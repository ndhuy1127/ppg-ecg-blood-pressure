"""The logger accepts a byte stream built with the firmware skeleton's conventions.

SYNTHETIC only. The stream mirrors firmware/app/main.c and
firmware/drivers/fake_afe.c (change both together): Packet Schema V0.2 (VERSION
2 on every packet), fake ECG every 1953 us read 16 at a time, fake PPG with
three slots every 5000 us read 8 at a time and sharing one anchor, fake IMU
with six axes every 10 000 us read 10 at a time and sharing one anchor (no
read stalls: those are in test_firmware_imu_plan.py), fake die temperature 0xB1
once per 1 s tick (started at the next 5 ms PPG wake, 29 ms conversion, read
out at the wake after; V0.2 section 11, no bit 4), t0 event
packets, device info packets 0xD1 at start and every 10 s with an ordinal that
counts dropped ones, SEQ assigned at send per channel, STATUS bit 4 on data
packets, bit 1 after an MCU queue drop, bits 0, 1 and 5 of a dropped or
USB-lost packet moved to the next packet of the channel, bit 1 on the next
event after a t0 edge the ISR queue dropped (no ordinal for it), ROM text
before the first packet. It checks the conventions, not the C code (see
test_firmware_c_encoder.py for the encoder), and no MCU is involved.
"""

import json
import random
from collections import Counter
from pathlib import Path

from software.data_io.packet_receiver import analyze_stream
from software.data_io.packet_wire import (
    Packet, StreamDecoder, device_info_data, encode_packet,
)

ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / "configs/hardware/packet_logger.json").read_bytes())
ROM_TEXT = b"ESP-ROM:esp32s3-20210327\r\nrst:0x1 (POWERON),boot:0x8\r\n"
BIT0, BIT1, BIT4, BIT5 = 1 << 0, 1 << 1, 1 << 4, 1 << 5
CARRY_BITS = BIT0 | BIT1 | BIT5
ECG, PPG, EVENT, INFO, TEMP = 0xE1, (0xF1, 0xF2, 0xF3), 0xC1, 0xD1, 0xB1
BIT3 = 1 << 3
IMU = (0xA1, 0xA2, 0xA3, 0xA4, 0xA5, 0xA6)
SOURCES = (((ECG,), 1953, 16, 512000), (PPG, 5000, 8, 200000),
           (IMU, 10000, 10, 100000))
APP_VERSION = "SYN_emulation"
INFO_DATA = device_info_data("ab" * 32, APP_VERSION, "v5.5.3")
INFO_PERIOD_US = 10_000_000


def ecg_word(index):
    return (((index % 2048) - 1024) & 0x3FFFF) << 6


def imu_value(index, slot):
    return (index * 257 + slot * 8191) % 65536 - 32768


def value_of(channel, index):
    if channel == ECG:
        return ecg_word(index)
    if channel == TEMP:
        return 25 * 16 + index % 16  # firmware fake_temp_service
    if channel in IMU:
        return imu_value(index, IMU.index(channel))
    return ppg_count(index, PPG.index(channel))


def ppg_count(index, slot):
    return index % 4096 + 32768 * (slot + 1)


def produced(duration_us, seed=7, isr_losses=(), ppg_delay=False):
    """Packets in send order as header fields without SEQ (firmware producers).

    ``isr_losses``: indices of t0 edges the ISR queue drops; they get no ordinal
    and the next event packet sets bit 1 (firmware event_task). ``ppg_delay``:
    firmware FAKE_PPG_DELAY, the PPG reader latches 12 ms late every 10 s and
    drains every sample there (V0.2 section 7.6).
    """
    rng = random.Random(seed)
    items = []
    for channels, period, batch, fs in SOURCES:
        first, t, delay_at = 0, 0, 10_000_000
        while t < duration_us:
            t = (first + batch) * period  # the sample that crosses the threshold
            latency = rng.randint(20, 400)
            if ppg_delay and channels == PPG and t + latency >= delay_at:
                delay_at += 10_000_000
                latency += 12_000
            count = batch + latency // period
            anchor = t + latency
            offset = ((count - 1) * 10**9 + fs // 2) // fs
            for slot, channel in enumerate(channels):
                data = [value_of(channel, first + i) for i in range(count)]
                items.append((anchor + slot, dict(
                    channel_id=channel, first_sample_index=first, t_anchor_us=anchor,
                    t_first_us=anchor - offset, fs_nominal_mhz=fs, status=BIT4,
                    data=tuple(data))))
            first += count
    for tick in range(duration_us // 1_000_000):
        # Started at the first 5 ms PPG wake at or after the tick, read out at the
        # first wake 29 ms or more later (firmware fake_temp_service).
        start = tick * 1_000_000 + rng.randint(0, 4_999)
        anchor = start + 29_000 + rng.randint(0, 4_999)
        items.append((anchor, dict(
            channel_id=TEMP, first_sample_index=tick, t_anchor_us=anchor,
            t_first_us=anchor, fs_nominal_mhz=1000, status=0,
            data=(value_of(TEMP, tick),))))
    for ordinal, t in enumerate(range(0, duration_us, INFO_PERIOD_US)):
        # t = 0 sorts before every data packet: sent right after USB starts.
        items.append((t - 1, dict(channel_id=INFO, first_sample_index=ordinal,
                                  t_anchor_us=t, t_first_us=t, fs_nominal_mhz=0,
                                  status=0, data=INFO_DATA)))
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


def _shift_ecg(items, start, lost):
    """ECG packets from ``items[start]`` on come ``lost`` samples later."""
    period = 1953
    out = list(items)
    for i in range(start, len(items)):
        if items[i]["channel_id"] == ECG:
            first = items[i]["first_sample_index"] + lost
            out[i] = dict(items[i], first_sample_index=first,
                          t_anchor_us=items[i]["t_anchor_us"] + lost * period,
                          t_first_us=items[i]["t_first_us"] + lost * period,
                          data=tuple(ecg_word(first + k)
                                     for k in range(len(items[i]["data"]))))
    return out


def afe_overflow(items, position, lost):
    """The AFE FIFO overflowed after ``items[position]`` and lost ``lost`` samples:
    that packet sets bit 0 and the later packets of its channel move on."""
    assert items[position]["channel_id"] == ECG
    out = _shift_ecg(items, position + 1, lost)
    out[position] = dict(out[position], status=out[position]["status"] | BIT0)
    return out


def reanchor(items, position, lost):
    """``lost`` ECG samples, a count the firmware does not know, were lost before
    ``items[position]``: that packet re-anchors and sets bit 5 (V0.2 section 5)."""
    assert items[position]["channel_id"] == ECG
    out = _shift_ecg(items, position, lost)
    out[position] = dict(out[position], status=out[position]["status"] | BIT5)
    return out


def stream(items, queue_drops=(), usb_losses=(), carry_bits=CARRY_BITS):
    """Bytes as the TX task sends them; drops are positions in ``items``.

    A queue drop sets bit 1 on the next packet of the channel; the bits in
    ``carry_bits`` of a packet dropped in the queue or not taken by the USB driver
    (``usb_losses``: send failures the firmware sees) move on too,
    as in firmware enqueue() and tx_task(). The firmware before 2026-10-23
    carried bit 1 only (``carry_bits=BIT1``), before 2026-10-24 bits 0 and 1.
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
        packet = Packet(version=2, session_id=0x5EED1234, seq=seq[channel],
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
    for channel, fs in ((ECG, 512000), *((c, 200000) for c in PPG),
                        *((c, 100000) for c in IMU), (TEMP, 1000), (EVENT, None),
                        (INFO, None)):
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
            "clock_id": "ESP32_ESP_TIMER_US", "firmware_version": APP_VERSION,
            **dict.fromkeys(text), "channels": channels, "simulation": None,
            "null_reasons": reasons}


def analyze(payload):
    decoder = StreamDecoder(CONFIG["wire_versions"])
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
    # docs/protocol/packet_logger.md: 100 866 packets (60 of them 0xD1, 36 000
    # IMU, 600 0xB1), 1 027 792 samples.
    assert result["decode"]["packets_decoded"] == 100_866
    assert len(samples) == 1_027_792
    skipped = [i for i in result["issues"] if i["code"] == "skipped_bytes"]
    assert skipped == [{"code": "skipped_bytes", "offset": 0,
                        "length": len(ROM_TEXT)}]
    channels = result["sessions"][0]["channels"]
    assert [g["lost_samples"] for g in channels["0xE1"]["gaps"]] == [32]
    assert channels["0xE1"]["status_bit_counts"]["mcu_buffer_overflow"] == 1
    assert [g["lost_samples"] for g in channels["0xF2"]["gaps"]] == [8]
    assert channels["0xC1"]["events"] == 7
    for key in ("0xA1", "0xA6"):
        assert channels[key]["packets_accepted"] == 6000 and not channels[key]["gaps"]
    assert channels["0xB1"]["packets_accepted"] == 600 and not channels["0xB1"]["gaps"]
    assert channels["0xB1"]["status_bit_counts"] == {}
    assert all(not c.get("packets_quarantined") for c in channels.values())
    info = result["sessions"][0]["device_info"]
    assert info["valid_packets"] == 60  # at 0, 10, ..., 590 s
    assert [i["app_version"] for i in info["identities"]] == [APP_VERSION]
    for _, key, _, _, index, value, _ in samples:
        assert value == value_of(int(key, 16), index)


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


def test_carried_bit5_keeps_a_reanchor_dropped_in_the_queue():
    # ECG packet 80 re-anchors after an unknown loss (bit 5) and is dropped in
    # the MCU queue: the next packet carries bits 1 and 5, so the logger starts
    # a new chain with an unknown loss instead of a known count.
    items = produced(20_000_000)
    ecg = positions(items, ECG)
    items = reanchor(items, ecg[80], 300)
    carried, _, _ = analyze(stream(items, queue_drops={ecg[80]}))
    assert carried["issue_counts"] == {"sample_index_reanchored": 1,
                                       "skipped_bytes": 1}
    channel = carried["sessions"][0]["channels"]["0xE1"]
    assert channel["chains"] == 2
    assert [g["lost_samples"] for g in channel["gaps"]] == [None]
    old, _, _ = analyze(stream(items, queue_drops={ecg[80]},
                               carry_bits=BIT0 | BIT1))
    assert old["issue_counts"] == {"sample_gap_status": 1, "skipped_bytes": 1}
    gap = old["sessions"][0]["channels"]["0xE1"]["gaps"]
    assert [g["lost_samples"] for g in gap] == [16 + 300]  # a count claimed known


def test_device_info_dropped_in_mcu_queue_is_counted():
    items = produced(60_000_000)
    info = positions(items, INFO)
    result, _, _ = analyze(stream(items, queue_drops={info[2]}))
    assert result["issue_counts"] == {"device_info_lost_before_send": 1,
                                      "skipped_bytes": 1}
    lost = [i for i in result["issues"] if i["code"] == "device_info_lost_before_send"]
    assert lost[0]["lost"] == 1 and lost[0]["ordinal"] == 3
    assert result["sessions"][0]["device_info"]["valid_packets"] == 5


def test_late_ppg_reader_drains_more_than_eight():
    # Every 10 s the reader latches 12 ms after the 8th sample: 2 more samples
    # wait, and it reads all 10 (never a fixed 8, V0.2 section 7.6).
    items = produced(55_000_000, ppg_delay=True)  # late at 10, 20, 30, 40, 50 s
    counts = Counter(len(i["data"]) for i in items if i["channel_id"] == 0xF1)
    assert counts[10] == 5 and set(counts) == {8, 10}
    result, _, samples = analyze(stream(items))
    assert result["issue_counts"] == {"skipped_bytes": 1}
    ppg1 = result["sessions"][0]["channels"]["0xF1"]
    assert not ppg1["gaps"] and not ppg1.get("packets_quarantined")
    for _, key, _, _, index, value, _ in samples:
        assert value == value_of(int(key, 16), index)


def test_die_temperature_drops_and_losses_keep_known_gaps():
    items = produced(30_000_000)
    temp = positions(items, TEMP)
    # Tick 10 hits an I2C error (bit 3 on tick 11); tick 11 is then dropped in the
    # MCU queue: tick 12 has bit 1, a counted gap of 2 ticks, and bit 3 is gone
    # (not a carried bit, V0.2 section 11.1). Tick 19 is lost on USB.
    items = [fields for i, fields in enumerate(items) if i != temp[10]]
    temp = positions(items, TEMP)
    items[temp[10]] = dict(items[temp[10]], status=BIT3)
    result, _, samples = analyze(stream(items, queue_drops={temp[10]},
                                        usb_losses={temp[18]}))
    assert result["issue_counts"] == {"missing_packets": 1, "sample_gap_counted": 1,
                                      "skipped_bytes": 1}
    channel = result["sessions"][0]["channels"]["0xB1"]
    assert channel["chains"] == 1 and channel["packets_accepted"] == 27
    assert channel["status_bit_counts"] == {"mcu_buffer_overflow": 1}
    assert [(g["index_from"], g["index_to"], g["lost_samples"])
            for g in channel["gaps"]] == [(10, 12, 2), (19, 20, 1)]
    for _, key, _, _, index, value, _ in samples:
        assert value == value_of(int(key, 16), index)
