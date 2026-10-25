"""Die temperature channel 0xB1 (Packet Schema V0.2 section 11), SYNTHETIC only.

Answers are derived from configs/hardware/Packet_Schema_V0.2.md section 11: one
value per packet at 1 Hz, FIRST_SAMPLE_INDEX = 1 s tick, every index gap of
known length (no bit 5), only STATUS bits 1 and 3, an absolute anchor tolerance
of temp_anchor_tolerance_us, no channel offset. They verify code, not a device.
"""

import copy
import json
from dataclasses import replace
from pathlib import Path

import pytest

from software.data_io.packet_receiver import analyze_stream
from software.data_io.packet_simulation_v3 import (
    generate_stream, session_metadata, validate_config,
)
from software.data_io.packet_wire import Packet, decode_bytes, encode_packet

ROOT = Path(__file__).resolve().parents[1]
SIM_TEMP = ROOT / "configs/hardware/packet_simulation_v3_v02_temp.json"
SIM_V01 = ROOT / "configs/hardware/packet_simulation_v3.json"
LOGGER_CONFIG = ROOT / "configs/hardware/packet_logger.json"
BIT0, BIT1, BIT3, BIT4, BIT5 = 1, 2, 8, 16, 32


@pytest.fixture
def sim():
    return json.loads(SIM_TEMP.read_bytes())


@pytest.fixture
def logger():
    return json.loads(LOGGER_CONFIG.read_bytes())


def temp(seq, tick, late_us=50_000, status=0, value=400, **fields):
    """0xB1 of tick ``tick`` read out ``late_us`` after the tick (grid at 1 s)."""
    anchor = 1_000_000 + tick * 1_000_000 + late_us
    packet = Packet(2, 0xB1, 1, seq, tick, anchor, anchor, 1000, status, (value,))
    return replace(packet, **fields)


def only_temp(sim):
    metadata = copy.deepcopy(session_metadata(sim, "valid", "0" * 64))
    metadata["channels"] = {"0xB1": metadata["channels"]["0xB1"]}
    metadata["null_reasons"] = {
        name: reason for name, reason in metadata["null_reasons"].items()
        if not name.startswith("channels.") or name.split(".")[1] == "0xB1"
    }
    return metadata


def analyze(packets, sim, logger, metadata=None):
    stream = b"".join(encode_packet(p) for p in packets)
    decoded, decoder = decode_bytes(stream, 4096, (1, 2))
    return analyze_stream(decoded, decoder, logger, metadata or only_temp(sim))


def channel(result):
    return result["sessions"][0]["channels"]["0xB1"]


def test_temp_channel_exists_in_v02_only(sim, logger):
    packet = temp(0, 0)
    stream = encode_packet(replace(packet, version=1)) + encode_packet(packet)
    decoded, decoder = decode_bytes(stream, 4096, (1, 2))
    assert [e.code for e in decoder.errors] == ["unknown_channel"]
    assert [p.packet.version for p in decoded] == [2]


def test_simulated_temp_stream_is_clean_and_kept_out_of_channel_offset(sim, logger):
    stream, _ = generate_stream(sim)
    decoded = [p.packet for p in decode_bytes(stream, 4096, (1, 2))[0]]
    temps = [p for p in decoded if p.channel_id == 0xB1]
    assert [p.first_sample_index for p in temps] == list(range(8))
    assert {(len(p.data), p.fs_nominal_mhz, p.status) for p in temps} == {(1, 1000, 0)}
    assert all(-2048 <= p.data[0] <= 2047 and p.t_first_us == p.t_anchor_us
               for p in temps)
    # A readout 100 ms after the tick, as on the chip: no channel_offset issue.
    late = [replace(p, t_anchor_us=p.t_anchor_us + 100_000,
                    t_first_us=p.t_anchor_us + 100_000) if p.channel_id == 0xB1 else p
            for p in decoded]
    metadata = session_metadata(sim, "valid", "0" * 64)
    for packets in (decoded, late):
        result, _, samples = analyze(packets, sim, logger, metadata)
        assert result["issue_counts"] == {}
        assert channel(result)["chains"] == 1
        offsets = result["sessions"][0]["channel_offset"]["offset_vs_ecg_us"]
        assert set(offsets) == {"0xF1"}
        assert len([s for s in samples if s[1] == "0xB1"]) == 8


def test_missed_ticks_are_a_counted_gap_that_keeps_the_chain(sim, logger):
    packets = [temp(0, 0), temp(1, 1), temp(2, 3, status=BIT3), temp(3, 4)]
    result, rows, _ = analyze(packets, sim, logger)
    assert result["issue_counts"] == {"sample_gap_counted": 1}
    gap = [i for i in result["issues"] if i["code"] == "sample_gap_counted"][0]
    assert (gap["absent_packets"], gap["lost_samples"]) == (0, 1)
    summary = channel(result)
    assert (summary["chains"], summary["packets_accepted"]) == (1, 4)
    assert summary["status_bit_counts"] == {"afe_error": 1}
    assert [(g["index_from"], g["index_to"], g["lost_samples"], g["reasons"])
            for g in summary["gaps"]] == [(2, 3, 1, ["counted_gap"])]
    # The chain goes on across the gap, so its timing is still checked.
    packets[2] = temp(2, 3, late_us=50_000 + 200_000)
    result, _, _ = analyze(packets, sim, logger)
    assert result["issue_counts"]["timestamp_anomaly"] == 1


def test_counted_gap_with_lost_packets_and_index_checks(sim, logger):
    # SEQ 2 lost on USB and ticks 3, 4 missed: 1 absent packet, 3 lost ticks.
    result, _, _ = analyze([temp(0, 0), temp(1, 1), temp(3, 5)], sim, logger)
    assert result["issue_counts"] == {"missing_packets": 1, "sample_gap_counted": 1}
    assert channel(result)["chains"] == 1
    # A lost packet whose tick is not missing from the index: inconsistent.
    result, _, _ = analyze([temp(0, 0), temp(1, 1), temp(3, 2)], sim, logger)
    assert result["issue_counts"] == {"missing_packets": 1,
                                      "sample_index_inconsistent": 1}
    # An index going back overlaps, as on any channel.
    result, _, _ = analyze([temp(0, 0), temp(1, 1), temp(2, 1)], sim, logger)
    assert result["issue_counts"]["sample_index_overlap"] == 1


@pytest.mark.parametrize("change,also", [
    ({"data": (400, 401)}, None),
    ({"fs_nominal_mhz": 1001}, "fs_metadata_mismatch"),  # seen on any packet
    ({"t_first_us": 1_000_000}, None),
    ({"status": BIT4}, "status_reserved_bits"),
    ({"status": BIT0}, "status_reserved_bits"),
    ({"status": BIT5}, "status_reserved_bits"),
    ({"status": 1 << 8}, "status_reserved_bits"),
])
def test_header_outside_the_contract_is_quarantined(sim, logger, change, also):
    packets = [temp(0, 0), temp(1, 1, **change), temp(2, 2)]
    result, rows, samples = analyze(packets, sim, logger)
    expected = {"temp_header_invalid": 1}
    if also:
        expected[also] = 1
    assert result["issue_counts"] == expected
    assert [r["disposition"] for r in rows if r["channel_id"] == "0xB1"] == [
        "accepted", "temp_header_invalid", "accepted"]
    assert [s[4] for s in samples] == [0, 2]
    # Its STATUS is not carried: bit 5 on it does not re-anchor the next packet.
    assert channel(result)["chains"] == 1


@pytest.mark.parametrize("late_us,anomaly", [
    (50_000 + 150_000, False), (50_000 + 150_001, True),
    (50_000 - 150_000, False), (50_000 - 150_001, True),
])
def test_anchor_tolerance_is_absolute(sim, logger, late_us, anomaly):
    packets = [temp(0, 0), temp(1, 1, late_us=late_us), temp(2, 2), temp(3, 3)]
    result, _, _ = analyze(packets, sim, logger)
    assert ("timestamp_anomaly" in result["issue_counts"]) is anomaly


def test_phase_may_not_drift_along_the_chain(sim, logger):
    # Readout delays 30, 130, ..., 830 ms: each step is within 150 ms of the one
    # before, but the delay after the tick is bounded for the whole chain.
    packets = [temp(k, k, late_us=30_000 + 100_000 * k) for k in range(9)]
    result, rows, _ = analyze(packets, sim, logger)
    assert result["issue_counts"] == {"timestamp_anomaly": 7}
    kinds = {i["kind"] for i in result["issues"]}
    assert kinds == {"phase"}
    assert [r["disposition"] for r in rows][:3] == [
        "accepted", "accepted", "timestamp_anomaly"]


def test_phase_window_keeps_the_most_packets(sim, logger):
    # Two early readouts against three on time: the three are kept.
    late = (50_000, 50_000, 260_000, 260_000, 260_000)
    packets = [temp(k, k, late_us=d) for k, d in enumerate(late)]
    result, rows, _ = analyze(packets, sim, logger)
    assert result["issue_counts"] == {"timestamp_anomaly": 2}
    assert [r["disposition"] for r in rows] == [
        "timestamp_anomaly", "timestamp_anomaly", "accepted", "accepted", "accepted"]


def test_anchors_one_millisecond_apart_are_not_accepted(sim, logger):
    # With the sample-based tolerance of other channels (1 sample + 500 us at
    # 30 000 ppm) any interval in (0, 2.03 s] would pass at 1 Hz.
    packets = [temp(0, 0), temp(1, 1, late_us=50_000 - 999_000), temp(2, 2)]
    result, _, _ = analyze(packets, sim, logger)
    assert result["issue_counts"] == {"timestamp_anomaly": 1}


@pytest.mark.parametrize("value,flagged", [(-2048, False), (2047, False),
                                           (-1, False), (2048, True),
                                           (-2049, True)])
def test_temp_data_range_is_signed_sixteenths(sim, logger, value, flagged):
    result, _, samples = analyze([temp(0, 0), temp(1, 1, value=value)], sim, logger)
    assert ("data_out_of_range" in result["issue_counts"]) is flagged


def test_simulator_temp_rules(sim):
    validate_config(sim)
    for spec in ({"fs_nominal_mhz": 2000, "sample_count": 1},
                 {"fs_nominal_mhz": 1000, "sample_count": 2}):
        bad = copy.deepcopy(sim)
        bad["channels"]["0xB1"] = spec
        with pytest.raises(ValueError):
            validate_config(bad)
    bad = copy.deepcopy(sim)
    bad["fault_channel"] = "0xB1"
    with pytest.raises(ValueError):
        validate_config(bad)
    v01 = json.loads(SIM_V01.read_bytes())
    v01["channels"]["0xB1"] = {"fs_nominal_mhz": 1000, "sample_count": 1}
    with pytest.raises(ValueError):
        validate_config(v01)
