"""AFE configuration 0xD2 and command acknowledgement 0xD3 in the receiver.

Answers are derived from configs/hardware/Packet_Schema_V0.2.md sections 12-13:
exact register sets per AFE, a monotonic generation, per-AFE presence in DEVICE
sessions, result-dependent acknowledgement checks. SYNTHETIC only.
"""

import copy
import json
from dataclasses import replace
from pathlib import Path

import pytest

from software.data_io.packet_receiver import analyze_stream
from software.data_io.packet_simulation_v3 import session_metadata
from software.data_io.packet_wire import Packet, decode_bytes, encode_packet

ROOT = Path(__file__).resolve().parents[1]
SIM_V02 = ROOT / "configs/hardware/packet_simulation_v3_v02.json"
LOGGER_CONFIG = ROOT / "configs/hardware/packet_logger.json"
ECG_REGS = (0x10, 0x12, 0x14, 0x15, 0x04, 0x05, 0x02, 0x03)
PPG_REGS = (0x08, 0x0A, 0x0C, 0x0D, 0x0E, 0x0F, 0x11, 0x12, 0x02, 0x03, 0x09)
IMU_REGS = (0x40, 0x41, 0x42, 0x43, 0x45, 0x46, 0x47, 0x48, 0x49, 0x53, 0x55, 0x58,
            0x7C, 0x7D)


@pytest.fixture
def sim():
    return json.loads(SIM_V02.read_bytes())


@pytest.fixture
def logger():
    return json.loads(LOGGER_CONFIG.read_bytes())


def metadata(sim, *keys, device=False):
    m = copy.deepcopy(session_metadata(sim, "valid", "0" * 64))
    m["channels"] = {k: v for k, v in m["channels"].items() if k in keys}
    m["null_reasons"] = {n: r for n, r in m["null_reasons"].items()
                         if not n.startswith("channels.") or n.split(".")[1] in keys}
    if device:
        m.update(source_type="DEVICE", simulation=None)
    return m


def words(regs, value=0x24):
    return tuple((a << 24) | value for a in regs)


def afe(seq, ordinal, afe_id, source=1, state=1, gen=1, regs=None, **fields):
    if regs is None:
        regs = (() if not (source and state) else
                words({1: ECG_REGS, 2: PPG_REGS, 3: IMU_REGS}[afe_id]))
    t = 1_000_000 + 10_000 * seq
    packet = Packet(2, 0xD2, 1, seq, ordinal, t, t, 0, 0,
                    (1, afe_id, source, state, gen, *regs))
    return replace(packet, **fields)


def ack(seq, ordinal, cmd_id, cmd_seq, result=0, gen=0, **fields):
    t = 2_000_000 + 10_000 * seq
    packet = Packet(2, 0xD3, 1, seq, ordinal, t, t, 0, 0, (1, cmd_id, cmd_seq, result,
                                                          gen))
    return replace(packet, **fields)


def ppg(seq):
    anchor = 1_000_000 + (4 * seq + 3) * 10_000
    return Packet(2, 0xF1, 1, seq, 4 * seq, anchor, anchor - 30_000, 100000, 16, (7,) * 4)


def ecg(seq):
    period = 10 ** 9 / 512_000
    anchor = round(1_000_000 + (16 * seq + 15) * period)
    return Packet(2, 0xE1, 1, seq, 16 * seq, anchor, round(anchor - 15 * period),
                  512_000, 16, (7 << 6,) * 16)


def analyze(packets, sim, logger, meta):
    stream = b"".join(encode_packet(p) for p in packets)
    decoded, decoder = decode_bytes(stream, 4096, (1, 2))
    return analyze_stream(decoded, decoder, logger, meta)


def session(result):
    return result["sessions"][0]


def test_control_channels_exist_in_v02_only(sim, logger):
    stream = encode_packet(replace(afe(0, 0, 2), version=1)) + encode_packet(
        replace(ack(0, 0, 1, 5), version=1))
    _, decoder = decode_bytes(stream, 4096, (1, 2))
    assert [e.code for e in decoder.errors] == ["unknown_channel"] * 2


def test_configuration_epochs_per_afe(sim, logger):
    meta = metadata(sim, "0xF1", "0xE1")
    led = words(PPG_REGS)[:2] + ((0x0C << 24) | 0x30,) + words(PPG_REGS)[3:]
    packets = [ppg(0), ecg(0), afe(0, 0, 1, regs=(*words(ECG_REGS[:7]),
                                                  (0x03 << 24) | 0x000201)),
               afe(1, 1, 2), afe(2, 2, 2), afe(3, 3, 2, gen=2, regs=led),
               afe(4, 4, 3, source=0, gen=0)]
    result, rows, samples = analyze(packets, sim, logger, meta)
    assert result["issue_counts"] == {}
    configs = session(result)["afe_config"]
    assert [(e["generation"], e["packets"], e["first_seq"]) for e in configs["MAX30101"]] \
        == [(1, 2, 1), (2, 1, 3)]
    assert configs["MAX30101"][1]["registers"]["0x0C"] == "0x30"
    assert configs["MAX30001"][0]["registers"]["0x03"] == "0x000201"
    assert configs["BMI270"] == [{"first_seq": 4, "t_anchor_us": 1_040_000,
                                  "source": "fake", "configured": True,
                                  "generation": 0, "registers": {}, "packets": 1}]
    # No samples, no metadata entry needed, never channel_missing.
    assert {s[1] for s in samples} == {"0xF1", "0xE1"}
    assert {r["disposition"] for r in rows if r["channel_id"] == "0xD2"} == {"afe_config"}


@pytest.mark.parametrize("change,problem", [
    ({"fs_nominal_mhz": 1}, "header"),
    ({"t_first_us": 5}, "header"),
    ({"status": 16}, "status"),
    ({"data": (1, 2, 1, 1)}, "sample_count"),
    ({"data": (2, 2, 1, 0, 0)}, "layout"),
    ({"data": (1, 4, 1, 0, 0)}, "afe"),
    ({"data": (1, 2, 2, 0, 0)}, "source_or_state"),
    ({"data": (1, 2, 0, 1, 1)}, "generation"),           # fake source, generation 1
    ({"data": (1, 2, 1, 1, 0, *words(PPG_REGS))}, "generation"),
    ({"data": (1, 2, 1, 1, 1, *words(PPG_REGS)[:10])}, "registers"),  # one missing
    ({"data": (1, 2, 1, 1, 1, *words(PPG_REGS)[::-1])}, "registers"),  # order
    ({"data": (1, 2, 1, 1, 1, *words(PPG_REGS)[:10], (0x09 << 24) | 0x107)},
     "registers"),                                        # 9-bit value
    ({"data": (1, 2, 1, 0, 3, *words(PPG_REGS))}, "registers"),  # not configured
])
def test_invalid_configuration_is_reported_and_not_counted(sim, logger, change, problem):
    result, _, _ = analyze([ppg(0), afe(0, 0, 2, **change)], sim, logger,
                           metadata(sim, "0xF1"))
    invalid = [i for i in result["issues"] if i["code"] == "afe_config_invalid"]
    assert [i["problem"] for i in invalid] == [problem]
    assert session(result)["afe_config"]["MAX30101"] == []


def test_generation_rules(sim, logger):
    meta = metadata(sim, "0xF1")
    other = words(PPG_REGS)[:2] + ((0x0C << 24) | 0x30,) + words(PPG_REGS)[3:]
    result, _, _ = analyze([afe(0, 0, 2, gen=3), afe(1, 1, 2, gen=2), ppg(0)], sim,
                           logger, meta)
    assert result["issue_counts"] == {"afe_config_generation_backwards": 1}
    result, _, _ = analyze([afe(0, 0, 2), afe(1, 1, 2, regs=other), ppg(0)], sim,
                           logger, meta)
    assert result["issue_counts"] == {"afe_config_changed_in_generation": 1}
    # One generation, one register image, even across a down state.
    result, _, _ = analyze([afe(0, 0, 2), afe(1, 1, 2, state=0, gen=1),
                            afe(2, 2, 2, regs=other), ppg(0)], sim, logger, meta)
    assert result["issue_counts"] == {"afe_config_changed_in_generation": 1}
    # Not configured (waiting for reconfiguration), then configured again: the
    # generation keeps counting up.
    result, _, _ = analyze([afe(0, 0, 2), afe(1, 1, 2, state=0, gen=1),
                            afe(2, 2, 2, gen=2), ppg(0)], sim, logger, meta)
    assert result["issue_counts"] == {}
    assert [(e["configured"], e["generation"]) for e in
            session(result)["afe_config"]["MAX30101"]] == [(True, 1), (False, 1),
                                                            (True, 2)]


def test_device_sessions_need_each_declared_afe(sim, logger):
    meta = metadata(sim, "0xF1", "0xE1", "0xA1", device=True)
    imu = Packet(2, 0xA1, 1, 0, 0, 1_090_000, 1_000_000, 100000, 16, (1,) * 10)
    base = [ppg(0), ecg(0), imu]
    result, _, _ = analyze(base + [afe(0, 0, 2), afe(1, 1, 3, source=0, gen=0),
                                   afe(2, 2, 1, state=0, gen=0)], sim, logger, meta)
    counts = result["issue_counts"]
    assert counts["afe_fake_source"] == 1 and counts["afe_not_configured"] == 1
    assert "afe_config_missing" not in counts
    result, _, _ = analyze(base + [afe(0, 0, 2)], sim, logger, meta)
    missing = [i["afe"] for i in result["issues"] if i["code"] == "afe_config_missing"]
    assert missing == ["MAX30001", "BMI270"]
    # SYNTHETIC sessions are not held to it.
    result, _, _ = analyze(base, sim, logger, metadata(sim, "0xF1", "0xE1", "0xA1"))
    assert "afe_config_missing" not in result["issue_counts"]


def test_configuration_ordinal_against_seq(sim, logger):
    result, _, _ = analyze([ppg(0), afe(0, 0, 2), afe(1, 3, 2)], sim, logger,
                           metadata(sim, "0xF1"))
    lost = [i for i in result["issues"] if i["code"] == "afe_config_lost_before_send"]
    assert [i["lost"] for i in lost] == [2]


def test_bit1_is_per_afe_and_the_ordinal_counts_lost_packets(sim, logger):
    # MAX30001 ordinal 1 dropped in the queue; MAX30101 ordinal 2 sent; the next
    # MAX30001 (ordinal 3) carries bit 1 for its own lost state. One counted loss
    # (ordinals), one per-AFE transition flag, never a second loss report.
    packets = [ppg(0), ecg(0), afe(0, 0, 1), afe(1, 2, 2), afe(2, 3, 1, status=2)]
    result, _, _ = analyze(packets, sim, logger, metadata(sim, "0xF1", "0xE1"))
    lost = [i for i in result["issues"] if i["code"] == "afe_config_lost_before_send"]
    assert [i["lost"] for i in lost] == [1]
    flags = [i for i in result["issues"] if i["code"] == "afe_config_transition_lost"]
    assert [(i["seq"], i["afe"]) for i in flags] == [(2, "MAX30001")]


def test_acknowledgements(sim, logger):
    meta = metadata(sim, "0xF1")
    packets = [ppg(0), afe(0, 0, 2), afe(1, 1, 2, gen=2),
               ack(0, 0, 0x01, 100), ack(1, 1, 0x02, 101, gen=2),
               ack(2, 2, 0x02, 102, result=8), ack(3, 3, 0x07, 103, result=1),
               ack(4, 4, 0x02, 104, gen=5)]
    result, _, _ = analyze(packets, sim, logger, meta)
    assert result["issue_counts"] == {"command_failed": 2,
                                      "command_ack_without_config": 1}
    failed = [i["result"] for i in result["issues"] if i["code"] == "command_failed"]
    assert failed == ["out_of_range", "unknown_command"]
    commands = session(result)["commands"]
    assert [(c["cmd"], c["cmd_seq"], c["result"], c["generation"]) for c in commands] \
        == [("ping", 100, "ok", 0), ("set_ppg_led", 101, "ok", 2),
            ("set_ppg_led", 102, "out_of_range", 0), (None, 103, "unknown_command", 0),
            ("set_ppg_led", 104, "ok", 5)]


@pytest.mark.parametrize("data,problem", [
    ((1, 0x01, 5, 0, 1), "generation"),        # ping never has a generation
    ((1, 0x02, 5, 0, 0), "generation"),        # a done SET_PPG_LED always has one
    ((1, 0x02, 5, 5, 3), "generation"),        # a failed one never
    ((1, 0x02, 5, 9, 0), "range"),
    ((1, 0x02, 70000, 0, 1), "range"),
    ((1, 0x100, 5, 1, 0), "range"),
    ((2, 0x01, 5, 0, 0), "layout"),
    ((1, 0x01, 5, 0), "sample_count"),
])
def test_invalid_acknowledgement(sim, logger, data, problem):
    result, _, _ = analyze([ppg(0), ack(0, 0, 1, 5, data=data)], sim, logger,
                           metadata(sim, "0xF1"))
    invalid = [i for i in result["issues"] if i["code"] == "command_ack_invalid"]
    assert [i["problem"] for i in invalid] == [problem]
    assert session(result)["commands"] == []
