"""Known-answer simulation tests, not sensor/waveform or BP validation."""

import copy
import json
import random
import subprocess
import sys
from fractions import Fraction
from pathlib import Path

import pytest

from scripts.simulate_packets import run
from software.data_io.packet_simulation import (
    CASES, generate_packets, json_bytes, packet_sha256, replay_packets,
)

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs/hardware/packet_simulation.json"
EXPECTED = ROOT / "tests/fixtures/packet_simulation_expected.json"


@pytest.fixture
def config():
    return json.loads(CONFIG.read_bytes())


@pytest.mark.parametrize("case", CASES)
def test_six_known_answer_cases(config, case):
    expected = json.loads(EXPECTED.read_bytes())["cases"][case]
    packets = generate_packets(config, case)
    result = replay_packets(packets, config)
    assert result["source_type"] == "SYNTHETIC"
    assert result["issue_counts"] == expected["issue_counts"]
    assert Fraction(result["offset_ppg_minus_ecg_us"]) == expected["offset_us"]
    for channel in ("ECG", "PPG"):
        stream = result["channels"][channel]
        assert stream["accepted_packets"] == expected[channel + "_packets"]
        assert len(stream["samples"]) == expected[channel + "_packets"] * config["channels"][channel]["sample_count"]
        lookup = {p["sequence"]: p for p in packets if p["channel"] == channel}
        for sample in stream["samples"]:
            packet = lookup[sample["sequence"]]
            assert sample["value"] == packet["samples"][sample["sample_index"]]
            assert Fraction(sample["timestamp_us"]) == (
                packet["timestamp_us"] + Fraction(sample["sample_index"] * 1000000, packet["fs_hz"])
            )
    assert len(result["channels"]["PPG"]["gaps"]) == expected["PPG_gaps"]
    if case in {"missing", "timestamp"}:
        gap = result["channels"]["PPG"]["gaps"][0]
        assert gap["sequence"] == 101
        assert Fraction(gap["nominal_start_us"]) == 1031250
        assert Fraction(gap["nominal_end_us"]) == 1062500
        assert all(s["sequence"] != 101 for s in result["channels"]["PPG"]["samples"])


def test_reorder_and_duplicate_do_not_change_reconstructed_data(config):
    original = replay_packets(generate_packets(config), config)["channels"]
    for case in ("duplicate", "reordered"):
        assert replay_packets(generate_packets(config, case), config)["channels"] == original


def test_generation_and_replay_reproducible_without_global_rng_mutation(config):
    state = random.getstate()
    first = generate_packets(config, "timestamp")
    second = generate_packets(dict(reversed(list(config.items()))), "timestamp")
    assert json_bytes(first) == json_bytes(second)
    assert packet_sha256(first) == packet_sha256(second)
    assert json_bytes(replay_packets(first, config)) == json_bytes(replay_packets(second, config))
    assert random.getstate() == state
    config["seed"] += 1
    assert packet_sha256(generate_packets(config, "timestamp")) != packet_sha256(first)


def test_offset_preserves_channel_timestamps(config):
    result = replay_packets(generate_packets(config, "offset"), config)
    assert Fraction(result["channels"]["PPG"]["samples"][0]["timestamp_us"]) == 1020000
    assert Fraction(result["channels"]["ECG"]["samples"][0]["timestamp_us"]) == 1000000


@pytest.mark.parametrize("position", [0, 3])
def test_missing_edge_packets_detected(config, position):
    packets = generate_packets(config)
    packets = [p for p in packets if not (p["channel"] == "PPG" and p["sequence"] == 100 + position)]
    result = replay_packets(packets, config)
    assert result["issue_counts"] == {"missing": 1}
    assert result["channels"]["PPG"]["gaps"][0]["sequence"] == 100 + position


def test_conflicting_duplicate_is_quarantined(config):
    packets = generate_packets(config)
    extra = copy.deepcopy(next(p for p in packets if p["channel"] == "PPG" and p["sequence"] == 101))
    extra["samples"][0] += 1
    packets.append(extra)
    result = replay_packets(packets, config)
    assert result["issue_counts"] == {"conflicting_duplicate": 1}
    assert result["channels"]["PPG"]["accepted_packets"] == 3
    assert result["channels"]["PPG"]["gaps"][0]["reason"] == "conflicting_duplicate"


@pytest.mark.parametrize("value", [0, 999999, 1200000])
def test_nonmonotonic_and_large_timestamp_jumps(config, value):
    packets = generate_packets(config)
    packet = next(p for p in packets if p["channel"] == "PPG" and p["sequence"] == 101)
    packet["timestamp_us"] = value
    assert replay_packets(packets, config)["issue_counts"] == {"timestamp_anomaly": 1}


@pytest.mark.parametrize("field,value", [
    ("schema_version", "hardware-v1"), ("source_type", "REAL"),
    ("session_id", "OTHER"), ("clock_id", "PRIVATE_CLOCK"),
    ("channel", "ABP"), ("sequence", True), ("sequence", 999),
    ("timestamp_us", -1), ("timestamp_us", 1.5), ("timestamp_kind", "receive"),
    ("timestamp_unit", "ms"), ("sample_count", 1), ("fs_hz", 500),
    ("sample_unit", "mV"), ("samples", [0]),
])
def test_bad_packet_schema_rejected(config, field, value):
    packets = generate_packets(config)
    packets[0][field] = value
    with pytest.raises(ValueError):
        replay_packets(packets, config)


@pytest.mark.parametrize("field,value", [
    ("seed", True), ("packet_count", 2), ("fault_index", 0),
    ("offset_us", 0), ("source_type", "REAL"), ("channels", {}),
])
def test_invalid_configs_rejected(config, field, value):
    config[field] = value
    with pytest.raises(ValueError):
        generate_packets(config)


def test_empty_stream_preserves_all_gaps(config):
    result = replay_packets([], config)
    assert result["issue_counts"] == {"missing": 8}
    assert result["offset_ppg_minus_ecg_us"] is None
    assert all(len(result["channels"][c]["gaps"]) == 4 for c in ("ECG", "PPG"))


def test_different_rates_and_batch_durations_supported(config):
    config["channels"]["PPG"] = {"fs_hz": 125, "sample_count": 3}
    result = replay_packets(generate_packets(config), config)
    assert result["issue_counts"] == {}
    assert Fraction(result["channels"]["PPG"]["samples"][3]["timestamp_us"]) == 1024000


def test_runner_generate_replay_and_refuse_overwrite(tmp_path):
    first, second = tmp_path / "first", tmp_path / "second"
    report = run(CONFIG, "missing", first)
    replay = run(CONFIG, "valid", second, first / "packets.json")
    assert report["packets_sha256"] == replay["packets_sha256"]
    assert report["result_sha256"] == replay["result_sha256"]
    assert report["issue_counts"] == {"missing": 1}
    assert (first / "replay.json").read_bytes() == (second / "replay.json").read_bytes()
    with pytest.raises(FileExistsError):
        run(CONFIG, "valid", first)


def test_cli_runs_from_other_directory(tmp_path):
    output = tmp_path / "cli"
    result = subprocess.run([
        sys.executable, "-B", str(ROOT / "scripts/simulate_packets.py"),
        "--case", "offset", "--output", str(output),
    ], cwd=tmp_path, capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["issue_counts"] == {"channel_offset": 1}
    assert json.loads((output / "report.json").read_bytes())["source_type"] == "SYNTHETIC"


@pytest.mark.parametrize("fs_hz", [3, 7, 512])
def test_fractional_duration_missing_anchor_not_false_anomaly(config, fs_hz):
    config["channels"]["PPG"] = {"fs_hz": fs_hz, "sample_count": 1}
    config["timestamp_tolerance_us"] = 0
    packets = [p for p in generate_packets(config)
               if not (p["channel"] == "PPG" and p["sequence"] == 100)]
    result = replay_packets(packets, config)
    assert result["issue_counts"] == {"missing": 1}
    assert result["channels"]["PPG"]["accepted_packets"] == 3
    # A real injected fault must still be detected with fractional timing.
    faulty = next(p for p in packets if p["channel"] == "PPG" and p["sequence"] == 102)
    faulty["timestamp_us"] += config["offset_us"]
    assert replay_packets(packets, config)["issue_counts"] == {
        "missing": 1, "timestamp_anomaly": 1,
    }


@pytest.mark.parametrize("field", ["start_timestamp_us", "sequence_start"])
def test_counter_overflow_rejected_before_generation(config, field):
    config[field] = 2 ** 63 - 1
    with pytest.raises(ValueError, match="final_timestamp_us|sequence_end"):
        generate_packets(config)


def test_timestamp_bound_includes_injected_offset(config):
    final_elapsed = 93750  # Four 31,250-us batches, last starts at index 3.
    config["start_timestamp_us"] = 2 ** 63 - 1 - final_elapsed
    with pytest.raises(ValueError, match="final_timestamp_us"):
        generate_packets(config)
    config["start_timestamp_us"] -= config["offset_us"]
    config["sequence_start"] = 2 ** 63 - 4
    for case in CASES:
        packets = generate_packets(config, case)
        assert max(p["timestamp_us"] for p in packets) <= 2 ** 63 - 1
        assert max(p["sequence"] for p in packets) == 2 ** 63 - 1
        replay_packets(packets, config)  # No generator/receiver range mismatch.


def test_offset_must_exceed_quantization_budget(config):
    config["timestamp_tolerance_us"] = 0
    config["offset_us"] = 1
    with pytest.raises(ValueError, match="quantization"):
        generate_packets(config)


@pytest.mark.parametrize("fs_hz", [3, 512])
def test_large_epoch_sample_and_gap_times_are_exact(config, fs_hz):
    config["start_timestamp_us"] = 2 ** 63 - 4000000
    config["channels"]["PPG"] = {"fs_hz": fs_hz, "sample_count": 2}
    result = replay_packets(generate_packets(config, "missing"), config)
    assert result["issue_counts"] == {"missing": 1}
    assert result["time_encoding"] == "rational-string-us"
    # JSON round-trip must preserve every timestamp exactly.
    decoded = json.loads(json_bytes(result))
    for channel in ("ECG", "PPG"):
        samples = decoded["channels"][channel]["samples"]
        interval = Fraction(1000000, config["channels"][channel]["fs_hz"])
        assert Fraction(samples[0]["timestamp_us"]) == config["start_timestamp_us"]
        assert Fraction(samples[1]["timestamp_us"]) - Fraction(samples[0]["timestamp_us"]) == interval
    gap = decoded["channels"]["PPG"]["gaps"][0]
    duration = Fraction(2000000, fs_hz)
    assert Fraction(gap["nominal_start_us"]) == config["start_timestamp_us"] + duration
    assert Fraction(gap["nominal_end_us"]) - Fraction(gap["nominal_start_us"]) == duration


def test_v1_config_rejected(config):
    config["schema_version"] = "synthetic-packet-v1"
    with pytest.raises(ValueError):
        generate_packets(config)