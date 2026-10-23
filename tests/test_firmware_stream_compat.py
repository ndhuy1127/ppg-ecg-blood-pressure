"""The logger accepts a byte stream built with the firmware skeleton's conventions.

SYNTHETIC only. The stream mirrors firmware/app/main.c and
firmware/drivers/fake_afe.c (change both together): fake ECG every 1953 us read
16 at a time, fake PPG with three slots every 10000 us read 4 at a time and
sharing one anchor, t0 event packets, SEQ assigned at send per channel, STATUS
bit 4 on data packets, bit 1 after an MCU queue drop and carried to the next
packet sent when the marked packet is lost on USB, ROM text before the first
packet. It checks the conventions, not the C code, and no MCU is involved.
"""

import json
import random
from collections import Counter
from pathlib import Path

from software.data_io.packet_receiver import analyze_stream
from software.data_io.packet_wire import Packet, StreamDecoder, encode_packet

ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / "configs/hardware/packet_logger.json").read_bytes())
ROM_TEXT = b"ESP-ROM:esp32s3-20210327\r\nrst:0x1 (POWERON),boot:0x8\r\n"
BIT1, BIT4 = 1 << 1, 1 << 4
ECG, PPG, EVENT = 0xE1, (0xF1, 0xF2, 0xF3), 0xC1
SOURCES = ((ECG,), 1953, 16, 512000), (PPG, 10000, 4, 100000)


def ecg_word(index):
    return (((index % 2048) - 1024) & 0x3FFFF) << 6


def ppg_count(index, slot):
    return index % 4096 + 32768 * (slot + 1)


def produced(duration_us, seed=7):
    """Packets in send order as header fields without SEQ (firmware producers)."""
    rng = random.Random(seed)
    items = []
    for channels, period, batch, fs in SOURCES:
        first, t = 0, 0
        while t < duration_us:
            t = (first + batch) * period  # the sample that crosses the threshold
            latency = rng.randint(20, 400)
            count = batch + latency // period
            anchor = t + latency
            offset = ((count - 1) * 10**9 + fs // 2) // fs
            for slot, channel in enumerate(channels):
                data = [ecg_word(first + i) if channel == ECG
                        else ppg_count(first + i, slot) for i in range(count)]
                items.append((anchor + slot, dict(
                    channel_id=channel, first_sample_index=first, t_anchor_us=anchor,
                    t_first_us=anchor - offset, fs_nominal_mhz=fs, status=BIT4,
                    data=tuple(data))))
            first += count
    for ordinal, t in enumerate(range(5_000_000, duration_us, 97_000_000)):
        items.append((t, dict(channel_id=EVENT, first_sample_index=ordinal,
                              t_anchor_us=t, t_first_us=t, fs_nominal_mhz=0,
                              status=0, data=(1,))))
    return [fields for _, fields in sorted(items, key=lambda item: item[0])]


def stream(items, queue_drops=(), usb_losses=(), carry_bit1=True):
    """Bytes as the TX task sends them; drops are positions in ``items``."""
    seq, pending, carry = Counter(), Counter(), Counter()
    out = bytearray(ROM_TEXT)
    for position, fields in enumerate(items):
        channel, status = fields["channel_id"], fields["status"]
        if pending[channel]:
            status |= BIT1
        if position in queue_drops:
            pending[channel] = 1
            continue
        pending[channel] = 0
        if carry[channel]:
            status |= BIT1
        packet = Packet(version=1, session_id=0x5EED1234, seq=seq[channel],
                        **dict(fields, status=status))
        seq[channel] += 1
        if position in usb_losses:
            carry[channel] = bool(carry_bit1 and status & BIT1)
            continue
        carry[channel] = False
        out += encode_packet(packet)
    return bytes(out)


def metadata():
    channels, reasons = {}, {}
    for channel, fs in ((ECG, 512000), *((c, 100000) for c in PPG), (EVENT, None)):
        key = f"0x{channel:02X}"
        channels[key] = {"sensor": "SYN_fake_afe", "fs_nominal_mhz": fs,
                         "latency_l_us": None, "latency_source": None,
                         "unit_conversion": None, "afe_config": None}
        for name, value in channels[key].items():
            if value is None:
                reasons[f"channels.{key}.{name}"] = "SYNTHETIC firmware emulation"
    text = ("firmware_commit", "device_id", "operator", "electrode_type",
            "electrode_placement")
    reasons.update({name: "SYNTHETIC firmware emulation" for name in text})
    return {"schema_version": "packet-session-metadata-v0", "source_type": "SYNTHETIC",
            "clock_id": "ESP32_ESP_TIMER_US", "firmware_version": "SYN_emulation",
            **dict.fromkeys(text), "channels": channels, "simulation": None,
            "null_reasons": reasons}


def analyze(payload):
    decoder = StreamDecoder()
    decoded = []
    for start in range(0, len(payload), 4096):
        decoded += decoder.feed(payload[start:start + 4096])
    decoded += decoder.finish()
    return analyze_stream(decoded, decoder, CONFIG, metadata())


def positions(items, channel):
    return [i for i, fields in enumerate(items) if fields["channel_id"] == channel]


def test_ten_minutes_with_queue_drop_and_usb_losses():
    items = produced(600_000_000)
    ecg, ppg2 = positions(items, ECG), positions(items, 0xF2)
    payload = stream(items, queue_drops={ecg[5000]},
                     usb_losses={ecg[5001], ppg2[3000]})
    result, _, samples = analyze(payload)
    assert result["issue_counts"] == {"missing_packets": 2, "skipped_bytes": 1}
    skipped = [i for i in result["issues"] if i["code"] == "skipped_bytes"]
    assert skipped == [{"code": "skipped_bytes", "offset": 0,
                        "length": len(ROM_TEXT)}]
    channels = result["sessions"][0]["channels"]
    assert [g["lost_samples"] for g in channels["0xE1"]["gaps"]] == [32]
    assert channels["0xE1"]["status_bit_counts"]["mcu_buffer_overflow"] == 1
    assert [g["lost_samples"] for g in channels["0xF2"]["gaps"]] == [4]
    assert channels["0xC1"]["events"] == 7
    assert all(not c.get("packets_quarantined") for c in channels.values())
    for _, key, _, _, index, value in samples:
        slot = int(key[-1]) - 1
        assert value == (ecg_word(index) if key == "0xE1" else ppg_count(index, slot))


def test_carried_bit1_explains_a_gap_longer_than_one_packet():
    items = produced(20_000_000)
    ecg = positions(items, ECG)
    drops, lost = {ecg[100], ecg[101]}, {ecg[102]}
    with_carry, _, _ = analyze(stream(items, drops, lost))
    without_carry, _, _ = analyze(stream(items, drops, lost, carry_bit1=False))
    gap = with_carry["sessions"][0]["channels"]["0xE1"]["gaps"]
    assert [g["lost_samples"] for g in gap] == [48]
    assert "sample_index_inconsistent" not in with_carry["issue_counts"]
    assert without_carry["issue_counts"]["sample_index_inconsistent"] == 1
