"""The logger accepts a byte stream built with the firmware skeleton's conventions.

SYNTHETIC only. The stream mirrors firmware/app/main.c and
firmware/drivers/fake_afe.c (change both together): fake ECG every 1953 us read
16 at a time, fake PPG with three slots every 5000 us read 8 at a time and
sharing one anchor, t0 event packets, SEQ assigned at send per channel, STATUS
bit 4 on data packets, bit 1 after an MCU queue drop, bits 0 and 1 of a dropped
or USB-lost packet moved to the next packet of the channel, bit 1 on the next
event after a t0 edge the ISR queue dropped (no ordinal for it), ROM text
before the first packet. It checks the conventions, not the C code (see
test_firmware_c_encoder.py for the encoder), and no MCU is involved.
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
BIT0, BIT1, BIT4 = 1 << 0, 1 << 1, 1 << 4
GAP_BITS = BIT0 | BIT1
ECG, PPG, EVENT = 0xE1, (0xF1, 0xF2, 0xF3), 0xC1
SOURCES = ((ECG,), 1953, 16, 512000), (PPG, 5000, 8, 200000)


def ecg_word(index):
    return (((index % 2048) - 1024) & 0x3FFFF) << 6


def ppg_count(index, slot):
    return index % 4096 + 32768 * (slot + 1)


def produced(duration_us, seed=7, isr_losses=()):
    """Packets in send order as header fields without SEQ (firmware producers).

    ``isr_losses``: indices of t0 edges the ISR queue drops; they get no ordinal
    and the next event packet sets bit 1 (firmware event_task).
    """
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
    ordinal, edges_lost = 0, False
    for edge, t in enumerate(range(5_000_000, duration_us, 97_000_000)):
        if edge in isr_losses:
            edges_lost = True
            continue
        items.append((t, dict(channel_id=EVENT, first_sample_index=ordinal,
                              t_anchor_us=t, t_first_us=t, fs_nominal_mhz=0,
                              status=BIT1 if edges_lost else 0, data=(1,))))
        ordinal, edges_lost = ordinal + 1, False
    return [fields for _, fields in sorted(items, key=lambda item: item[0])]


def afe_overflow(items, position, lost):
    """The AFE FIFO overflowed after ``items[position]`` and lost ``lost`` samples:
    that packet sets bit 0 and the later packets of its channel move on."""
    channel, period = items[position]["channel_id"], 1953
    assert channel == ECG
    out = list(items)
    out[position] = dict(items[position], status=items[position]["status"] | BIT0)
    for i in range(position + 1, len(items)):
        if items[i]["channel_id"] == channel:
            first = items[i]["first_sample_index"] + lost
            out[i] = dict(items[i], first_sample_index=first,
                          t_anchor_us=items[i]["t_anchor_us"] + lost * period,
                          t_first_us=items[i]["t_first_us"] + lost * period,
                          data=tuple(ecg_word(first + k)
                                     for k in range(len(items[i]["data"]))))
    return out


def stream(items, queue_drops=(), usb_losses=(), carry_bits=GAP_BITS):
    """Bytes as the TX task sends them; drops are positions in ``items``.

    A queue drop sets bit 1 on the next packet of the channel; the bits in
    ``carry_bits`` of a packet dropped in the queue or not taken by the USB driver
    (``usb_losses``: send failures the firmware sees) move on too,
    as in firmware enqueue() and tx_task(). The firmware before 2026-10-23
    carried bit 1 only (``carry_bits=BIT1``).
    """
    seq, pending, carried = Counter(), Counter(), Counter()
    out = bytearray(ROM_TEXT)
    for position, fields in enumerate(items):
        channel = fields["channel_id"]
        status = fields["status"] | pending[channel]
        if position in queue_drops:
            pending[channel] = (status & carry_bits) | BIT1
            continue
        pending[channel] = 0
        status |= carried[channel]
        packet = Packet(version=1, session_id=0x5EED1234, seq=seq[channel],
                        **dict(fields, status=status))
        seq[channel] += 1
        if position in usb_losses:
            carried[channel] = status & carry_bits
            continue
        carried[channel] = 0
        out += encode_packet(packet)
    return bytes(out)


def metadata():
    channels, reasons = {}, {}
    for channel, fs in ((ECG, 512000), *((c, 200000) for c in PPG), (EVENT, None)):
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
    assert [g["lost_samples"] for g in channels["0xF2"]["gaps"]] == [8]
    assert channels["0xC1"]["events"] == 7
    assert all(not c.get("packets_quarantined") for c in channels.values())
    for _, key, _, _, index, value, _ in samples:
        slot = int(key[-1]) - 1
        assert value == (ecg_word(index) if key == "0xE1" else ppg_count(index, slot))


def test_carried_bit1_explains_a_gap_longer_than_one_packet():
    items = produced(20_000_000)
    ecg = positions(items, ECG)
    drops, lost = {ecg[100], ecg[101]}, {ecg[102]}
    with_carry, _, _ = analyze(stream(items, drops, lost))
    without_carry, _, _ = analyze(stream(items, drops, lost, carry_bits=0))
    gap = with_carry["sessions"][0]["channels"]["0xE1"]["gaps"]
    assert [g["lost_samples"] for g in gap] == [48]
    assert "sample_index_inconsistent" not in with_carry["issue_counts"]
    assert without_carry["issue_counts"]["sample_index_inconsistent"] == 1


def test_carried_bit0_explains_an_afe_overflow_lost_on_usb():
    # ECG packet 50 reports an AFE overflow of 40 samples and is then lost on
    # USB: the next packet's index moves 16 + 40 > 32 samples for one absent
    # packet, which only bit 0 (carried) can explain.
    items = produced(20_000_000)
    ecg = positions(items, ECG)
    items = afe_overflow(items, ecg[50], 40)
    carried, _, _ = analyze(stream(items, usb_losses={ecg[50]}))
    assert carried["issue_counts"] == {"missing_packets": 1, "skipped_bytes": 1}
    channels = carried["sessions"][0]["channels"]
    assert [g["lost_samples"] for g in channels["0xE1"]["gaps"]] == [56]
    assert channels["0xE1"]["status_bit_counts"]["afe_fifo_overflow"] == 1
    old, _, _ = analyze(stream(items, usb_losses={ecg[50]}, carry_bits=BIT1))
    assert old["issue_counts"]["sample_index_inconsistent"] == 1
    # Dropped in the MCU queue instead: bit 1 explains the jump, bit 0 still says
    # that AFE samples were lost too.
    dropped, _, _ = analyze(stream(items, queue_drops={ecg[50]}))
    assert dropped["issue_counts"] == {"sample_gap_status": 1, "skipped_bytes": 1}
    bits = dropped["sessions"][0]["channels"]["0xE1"]["status_bit_counts"]
    assert bits["afe_fifo_overflow"] == 1 and bits["mcu_buffer_overflow"] == 1


def test_t0_edge_dropped_by_isr_is_reported_on_the_next_event():
    items = produced(600_000_000, isr_losses={2})
    result, _, _ = analyze(stream(items))
    assert result["issue_counts"] == {"events_lost_before_send": 1,
                                      "skipped_bytes": 1}
    lost = [i for i in result["issues"] if i["code"] == "events_lost_before_send"]
    assert lost[0]["lost"] is None and lost[0]["ordinal"] == 2
    events = result["sessions"][0]["events"]
    assert [e["event_ordinal"] for e in events] == list(range(6))


def test_t0_event_dropped_in_mcu_queue_is_counted():
    items = produced(600_000_000)
    events = positions(items, EVENT)
    result, _, _ = analyze(stream(items, queue_drops={events[3]}))
    assert result["issue_counts"] == {"events_lost_before_send": 1,
                                      "skipped_bytes": 1}
    lost = [i for i in result["issues"] if i["code"] == "events_lost_before_send"]
    assert lost[0]["lost"] == 1 and lost[0]["ordinal"] == 4
