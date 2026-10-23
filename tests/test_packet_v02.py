"""Packet Schema V0.2 in the codec, receiver, logger and simulator (SYNTHETIC only).

Answers are derived from configs/hardware/Packet_Schema_V0.2.md, not from the
code under test; they verify code, not a device.
"""

import copy
import json
from dataclasses import replace
from fractions import Fraction
from pathlib import Path

import pytest

from scripts.packet_logger import record, replay
from scripts.simulate_packets import run as simulate
from software.data_io.packet_receiver import analyze_stream, decode_device_info
from software.data_io.packet_simulation_v3 import (
    V02_CASES, backlog_chunks, generate_stream, reanchor_index, session_metadata,
    validate_config,
)
from software.data_io.packet_wire import (
    Packet, decode_bytes, device_info_data, encode_packet,
)

ROOT = Path(__file__).resolve().parents[1]
SIM_V01 = ROOT / "configs/hardware/packet_simulation_v3.json"
SIM_V02 = ROOT / "configs/hardware/packet_simulation_v3_v02.json"
LOGGER_CONFIG = ROOT / "configs/hardware/packet_logger.json"
IMU = ("0xA1", "0xA2", "0xA3", "0xA4", "0xA5", "0xA6")
ELF = "f0e1d2c3b4a5968778695a4b3c2d1e0f00112233445566778899aabbccddeeff"


@pytest.fixture
def sim():
    return json.loads(SIM_V02.read_bytes())


@pytest.fixture
def logger():
    return json.loads(LOGGER_CONFIG.read_bytes())


def analyze(stream, sim, logger, case="valid", metadata=None):
    packets, decoder = decode_bytes(stream, logger["read_chunk_bytes"],
                                    logger["wire_versions"])
    metadata = metadata or session_metadata(sim, case, "0" * 64)
    return analyze_stream(packets, decoder, logger, metadata)


def decoded(stream):
    return [item.packet for item in decode_bytes(stream, 4096, (1, 2))[0]]


def restream(packets):
    return b"".join(encode_packet(p) for p in packets)


def only(metadata, *keys):
    metadata = copy.deepcopy(metadata)
    metadata["channels"] = {k: v for k, v in metadata["channels"].items() if k in keys}
    metadata["null_reasons"] = {
        name: reason for name, reason in metadata["null_reasons"].items()
        if not name.startswith("channels.") or name.split(".")[1] in keys
    }
    return metadata


def ppg(seq, first, status=16, version=2, n=4):
    """PPG slot 1, 100 Hz, anchors exactly on the index (no jitter)."""
    anchor = 1_000_000 + (first + n - 1) * 10_000
    return Packet(version, 0xF1, 1, seq, first, anchor, anchor - (n - 1) * 10_000,
                  100000, status, (7,) * n)


def info_packet(seq, ordinal, data=None, version=2, **fields):
    data = data or device_info_data(ELF, "0.2.0-sim", "v5.5.3")
    t = 1_000_000 + 300_000 * ordinal
    packet = Packet(version, 0xD1, 1, seq, ordinal, t, t, 0, 0, data)
    return replace(packet, **fields)


# --- codec ---------------------------------------------------------------------

def test_channel_registry_is_per_version():
    imu = Packet(1, 0xA1, 1, 0, 0, 1000, 1000, 100000, 0, (5,))
    packets, decoder = decode_bytes(restream([imu]), 4096, (1, 2))
    assert packets == [] and [e.code for e in decoder.errors] == ["unknown_channel"]
    packets, decoder = decode_bytes(restream([replace(imu, version=2)]), 4096, (1, 2))
    assert [p.packet.channel_id for p in packets] == [0xA1] and not decoder.errors
    packets, decoder = decode_bytes(restream([replace(imu, version=3)]), 4096, (1, 2))
    assert [e.code for e in decoder.errors] == ["unsupported_version"]


def test_device_info_words_keep_the_bit_pattern():
    data = device_info_data(ELF, "0.2.0-sim", "v5.5.3")
    assert len(data) == 25 and data[0] == 1
    assert data[1] == 0xF0E1D2C3 - (1 << 32)  # bit 31 set: negative int32
    packet = info_packet(0, 0, data)
    assert decode_bytes(restream([packet]), 4096, (2,))[0][0].packet == packet
    identity, problem = decode_device_info(packet)
    assert problem is None
    assert identity == {"elf_sha256": ELF, "app_version": "0.2.0-sim",
                        "idf_version": "v5.5.3"}
    for bad in ("x" * 32, "é"):
        with pytest.raises(ValueError):
            device_info_data(ELF, bad, "v5.5.3")
    with pytest.raises(ValueError):
        device_info_data(ELF[:-2], "a", "b")


# --- simulator cases -------------------------------------------------------------

@pytest.mark.parametrize("case,expected", [
    ("valid", {}),
    ("imu_backlog", {}),
    ("imu_fifo_full", {"sample_index_reanchored": 6}),
    ("mixed_version", {"version_mixed_in_session": 1, "missing_packets": 1,
                       "channel_missing": 8}),
    ("device_info_changed", {"device_info_changed": 2}),
])
def test_v02_cases_known_answers(sim, logger, case, expected):
    result, rows, samples = analyze(generate_stream(sim, case)[0], sim, logger, case)
    assert result["issue_counts"] == expected
    session = result["sessions"][0]
    assert session["packet_schema"] == "packet-v0.2"
    assert result["packet_schemas"] == (
        ["packet-v0.1", "packet-v0.2"] if case == "mixed_version" else ["packet-v0.2"])
    axes = [session["channels"][key] for key in IMU]
    if case == "imu_backlog":
        # Reads 2-5 (4 x 10 frames) are one late read of 40 frames: chunks of 32
        # (bit 7, anchor unused) and 8; 4 + 2 packets per axis, nothing lost.
        assert {a["packets_accepted"] for a in axes} == {6}
        assert {a["packets_anchor_unreliable"] for a in axes} == {1}
        assert {a["samples_accepted"] for a in axes} == {80}
        assert {a["chains"] for a in axes} == {1} and not any(a["gaps"] for a in axes)
    elif case == "imu_fifo_full":
        # Read 2 is full (bit 0, anchor unused), reads 3 and 4 are lost, read 5
        # re-anchors (bit 5): a new chain, lost samples unknown.
        assert {a["packets_accepted"] for a in axes} == {6}
        assert {a["packets_anchor_unreliable"] for a in axes} == {1}
        assert {a["chains"] for a in axes} == {2}
        assert {g["lost_samples"] for a in axes for g in a["gaps"]} == {None}
    else:
        assert {a["packets_accepted"] for a in axes} == {8}
    assert all(-(1 << 15) <= s[5] < 1 << 15 for s in samples if s[1] in IMU)
    assert not [s for s in samples if s[1] == "0xD1"]
    info = session["device_info"]
    assert info["identities"][0]["elf_sha256"] == ELF
    assert info["valid_packets"] == 3  # at 1.0, 1.3, 1.6 s


def test_imu_backlog_losing_the_newest_chunk_leaves_no_reference(sim, logger):
    stream, _ = generate_stream(sim, "imu_backlog")
    packets = decoded(stream)
    newest = {p.seq for p in packets if p.channel_id == 0xA1 and len(p.data) == 8}
    kept = [p for p in packets
            if not (0xA1 <= p.channel_id <= 0xA6 and p.seq in newest)]
    result, _, _ = analyze(restream(kept), sim, logger, "imu_backlog")
    assert result["issue_counts"] == {"missing_packets": 6}
    axis = result["sessions"][0]["channels"]["0xA1"]
    assert axis["packets_anchor_unreliable"] == 1
    assert "timestamp_anomaly" not in result["issue_counts"]


def test_imu_fifo_full_index_sequence(sim, logger):
    # Reads of 10 frames: 0, 10, 20 (FIFO full), reads 3-4 lost, then the read
    # whose true first index is 50 re-anchors to 50 (section 5 formula).
    packets = decoded(generate_stream(sim, "imu_fifo_full")[0])
    firsts = [p.first_sample_index for p in packets if p.channel_id == 0xA1]
    assert firsts == [0, 10, 20, 50, 60, 70]
    status = [p.status for p in packets if p.channel_id == 0xA1]
    assert [bool(s & 1) for s in status] == [False, False, True, False, False, False]
    assert [bool(s & 32) for s in status] == [False, False, False, True, False, False]


@pytest.mark.parametrize("next_anchor,expected", [
    (1_400_000, 50),   # 40 periods after the reference: true index
    (1_404_999, 50),   # 40.4999 periods: rounds down
    (1_405_000, 51),   # 40.5 periods: half up
    (1_150_000, 30),   # formula below last_prev + 1 (29): max branch
    (1_000_000, 30),   # no elapsed time: the index just continues
    (999_000, 30),     # negative elapsed: continues as well
])
def test_reanchor_index_formula(next_anchor, expected):
    # Reference: last index 19 at 1 000 000 us; full read ended at index 29;
    # next read of 10 frames; T = 10 000 us.
    assert reanchor_index(29, 19, 1_000_000, next_anchor, Fraction(10_000), 10) == (
        expected)


def test_v02_bit5_on_a_fs_zero_packet_is_kept(sim, logger):
    metadata = only(session_metadata(sim, "valid", "0" * 64), "0xF1")
    packets = [ppg(0, 100), replace(ppg(1, 0, status=16 | 32), fs_nominal_mhz=0),
               ppg(2, 4), ppg(3, 8)]
    result, _, _ = analyze(restream(packets), sim, logger, metadata=metadata)
    assert result["issue_counts"] == {"fs_invalid": 1, "fs_metadata_mismatch": 1,
                                      "sample_index_reanchored": 1}
    summary = result["sessions"][0]["channels"]["0xF1"]
    assert summary["packets_accepted"] == 3 and summary["chains"] == 2
    assert {g["lost_samples"] for g in summary["gaps"]} == {None}


def test_mixed_version_samples_and_issues_keep_the_version(sim, logger):
    result, rows, samples = analyze(generate_stream(sim, "mixed_version")[0], sim,
                                    logger, "mixed_version")
    keys = [(s[0], s[6], s[1], s[2], s[4]) for s in samples]
    assert len(set(keys)) == len(keys)
    assert {s[6] for s in samples if s[1] == "0xF1"} == {1, 2}
    missing = [i for i in result["issues"] if i["code"] == "channel_missing"]
    assert {i["version"] for i in missing} == {1}
    assert {r["version"] for r in rows if r["channel_id"] == "0xF1"} == {1, 2}


def test_simulate_cli_accepts_v02_cases(tmp_path):
    import subprocess
    import sys
    out = tmp_path / "out"
    run = subprocess.run(
        [sys.executable, "-B", str(ROOT / "scripts/simulate_packets.py"), "--config",
         str(SIM_V02), "--case", "imu_backlog", "--output", str(out)],
        capture_output=True, text=True)
    assert run.returncode == 0, run.stderr
    assert (out / "stream.bin").exists()


def test_device_info_accepts_any_ascii_but_not_bytes_after_nul():
    tab = device_info_data(ELF, "a\tb", "v5.5.3")
    assert decode_device_info(info_packet(0, 0, tab))[0]["app_version"] == "a\tb"
    with pytest.raises(ValueError):
        device_info_data(ELF, "a\0b", "v5.5.3")


def test_t_first_rounds_the_offset_half_up():
    # 128 Hz: T = 7812.5 us; 9 periods = 70312.5 us rounds to 70313.
    chunk = backlog_chunks(0, 10, 1_071_462, Fraction(10 ** 9, 128_000), 0)
    assert chunk[0][2] == 1_071_462 - 70_313


@pytest.mark.parametrize("frames", [32, 33, 64, 65])
def test_backlog_chunks_boundaries(frames):
    period = Fraction(10_000)
    chunks = backlog_chunks(100, frames, 5_000_000, period, 16)
    assert [c[1] for c in chunks] == [32] * (frames // 32) + (
        [frames % 32] if frames % 32 else [])
    assert [c[0] for c in chunks] == [100 + 32 * i for i in range(len(chunks))]
    assert [bool(c[3] & 1 << 7) for c in chunks] == [True] * (len(chunks) - 1) + [False]
    for first, _, t_first, _ in chunks:
        assert t_first == 5_000_000 - (frames - 1 - (first - 100)) * 10_000


def test_v02_simulator_reproducible_and_v01_rejects_v02_parts(sim):
    assert generate_stream(sim, "valid") == generate_stream(sim, "valid")
    v01 = json.loads(SIM_V01.read_bytes())
    for case in V02_CASES:
        with pytest.raises(ValueError):
            generate_stream(v01, case)
    with_imu = copy.deepcopy(v01)
    with_imu["channels"]["0xA1"] = {"fs_nominal_mhz": 100000, "sample_count": 10}
    with pytest.raises(ValueError):
        validate_config(with_imu)
    for broken in ({**sim, "device_info": None},
                   {k: v for k, v in sim.items() if k != "device_info"},
                   {**sim, "channels": {k: v for k, v in sim["channels"].items()
                                        if k != "0xA6"}},
                   {**sim, "unsupported_version": 2},
                   {**sim, "fault_channel": "0xA1"}):
        with pytest.raises(ValueError):
            validate_config(broken)


# --- receiver rules ----------------------------------------------------------------

def test_reserved_status_bits_are_per_version(sim, logger):
    metadata = only(session_metadata(sim, "valid", "0" * 64), "0xF1")
    # V0.1: bit 7 is reserved, and the anchor is still checked.
    late = [ppg(0, 0, version=1), replace(ppg(1, 4, version=1, status=16 | 128),
                                          t_anchor_us=2_000_000), ppg(2, 8, version=1)]
    result, _, _ = analyze(restream(late), sim, logger, metadata=metadata)
    assert result["issue_counts"] == {"status_reserved_bits": 1,
                                      "timestamp_anomaly": 1}
    # V0.2: bit 7 is a backlog chunk, its anchor is not checked; bit 8 is reserved.
    chunk = [ppg(0, 0), replace(ppg(1, 4, status=16 | 128), t_anchor_us=2_000_000),
             ppg(2, 8, status=16 | 256)]
    result, _, _ = analyze(restream(chunk), sim, logger, metadata=metadata)
    assert result["issue_counts"] == {"status_reserved_bits": 1}
    assert result["sessions"][0]["channels"]["0xF1"]["packets_anchor_unreliable"] == 1


def test_v02_bit5_always_reanchors_and_only_on_its_own_packet(sim, logger):
    metadata = only(session_metadata(sim, "valid", "0" * 64), "0xF1")
    # Bit 5 with a continuous index: still a new chain in V0.2, not in V0.1.
    for version, chains, issues in ((2, 2, {"sample_index_reanchored": 1}),
                                    (1, 1, {})):
        packets = [ppg(0, 0, version=version), ppg(1, 4, version=version),
                   ppg(2, 8, version=version, status=16 | 32),
                   ppg(3, 12, version=version)]
        result, _, _ = analyze(restream(packets), sim, logger, metadata=metadata)
        assert result["issue_counts"] == issues
        assert result["sessions"][0]["channels"]["0xF1"]["chains"] == chains
    # V0.2: bit 5 on the packet before a jump does not explain the jump.
    # (Anchors follow the index, so the jump itself is consistent in time.)
    packets = [ppg(0, 0), ppg(1, 4, status=16 | 32), ppg(2, 50)]
    result, _, _ = analyze(restream(packets), sim, logger, metadata=metadata)
    assert result["issue_counts"] == {"sample_index_reanchored": 1,
                                      "sample_gap_unexplained": 1}
    # A lost re-anchored packet whose bit 5 the firmware carried: one boundary.
    packets = [ppg(0, 0), ppg(1, 4), ppg(3, 60, status=16 | 32), ppg(4, 64)]
    result, _, _ = analyze(restream(packets), sim, logger, metadata=metadata)
    assert result["issue_counts"] == {"missing_packets": 1,
                                      "sample_index_reanchored": 1}
    assert result["sessions"][0]["channels"]["0xF1"]["chains"] == 2


@pytest.mark.parametrize("value,flagged", [(-32768, False), (32767, False),
                                           (-1, False), (32768, True),
                                           (-32769, True)])
def test_imu_data_range_is_signed(sim, logger, value, flagged):
    packets = [p if p.channel_id != 0xA1 or p.seq != 1
               else replace(p, data=(value, *p.data[1:]))
               for p in decoded(generate_stream(sim)[0])]
    result, _, _ = analyze(restream(packets), sim, logger)
    assert ("data_out_of_range" in result["issue_counts"]) is flagged


@pytest.mark.parametrize("change,problem", [
    ({"data": device_info_data(ELF, "a", "b")[:24]}, "sample_count"),
    ({"data": (2, *device_info_data(ELF, "a", "b")[1:])}, "layout"),
    ({"fs_nominal_mhz": 1}, "header"),
    ({"t_first_us": 5}, "header"),
    ({"status": 16}, "status"),
    ({"data": (*device_info_data(ELF, "a", "b")[:9], 0x41000042,
               *device_info_data(ELF, "a", "b")[10:])}, "text"),  # text after NUL
    ({"data": (*device_info_data(ELF, "a", "b")[:9], -1,
               *device_info_data(ELF, "a", "b")[10:])}, "text"),  # not ASCII
])
def test_invalid_device_info_is_reported_and_not_counted(sim, logger, change,
                                                          problem):
    metadata = only(session_metadata(sim, "valid", "0" * 64), "0xD1")
    metadata.update(source_type="DEVICE", simulation=None)
    result, _, _ = analyze(restream([info_packet(0, 0, **change)]), sim, logger,
                           metadata=metadata)
    invalid = [i for i in result["issues"] if i["code"] == "device_info_invalid"]
    assert [i["problem"] for i in invalid] == [problem]
    assert result["issue_counts"]["device_info_missing"] == 1
    assert result["sessions"][0]["device_info"]["valid_packets"] == 0


def test_device_info_missing_mismatch_and_ordinal(sim, logger):
    base = only(session_metadata(sim, "valid", "0" * 64), "0xF1", "0xD1")
    device = {**base, "source_type": "DEVICE", "simulation": None}
    # A V0.2 DEVICE session without device info, whatever the metadata says.
    result, _, _ = analyze(restream([ppg(0, 0), ppg(1, 4)]), sim, logger,
                           metadata=device)
    assert result["issue_counts"] == {"device_info_missing": 1}
    # V0.1 sessions have no device info at all.
    result, _, _ = analyze(restream([ppg(0, 0, version=1)]), sim, logger,
                           metadata=device)
    assert result["issue_counts"] == {}
    assert result["sessions"][0]["device_info"] is None
    # Metadata firmware_version must be the app version from the stream.
    stated = {**device, "firmware_version": "0.1.9",
              "null_reasons": {k: v for k, v in device["null_reasons"].items()
                               if k != "firmware_version"}}
    packets = [ppg(0, 0), info_packet(0, 0), info_packet(1, 1)]
    result, _, _ = analyze(restream(packets), sim, logger, metadata=stated)
    assert result["issue_counts"] == {"firmware_metadata_mismatch": 1}
    # An info packet dropped in the MCU queue: ordinal jumps, SEQ does not.
    packets = [ppg(0, 0), info_packet(0, 0), info_packet(1, 2)]
    result, _, _ = analyze(restream(packets), sim, logger, metadata=device)
    lost = [i for i in result["issues"] if i["code"] == "device_info_lost_before_send"]
    assert [i["lost"] for i in lost] == [1]


def test_session_restart_resends_device_info(sim, logger):
    result, _, _ = analyze(generate_stream(sim, "session_restart")[0], sim, logger,
                           "session_restart")
    assert result["issue_counts"] == {"session_change": 1}
    assert [s["device_info"]["valid_packets"] >= 1 for s in result["sessions"]] == [
        True, True]


# --- logger record/replay ------------------------------------------------------------

def test_record_replay_v02_manifest(tmp_path):
    generated = tmp_path / "generated"
    simulate(SIM_V02, "imu_backlog", generated)
    metadata = generated / "session_metadata.json"
    session = tmp_path / "session"
    with (generated / "stream.bin").open("rb") as source:
        manifest = record(source, session, LOGGER_CONFIG, metadata, ROOT, "stream.bin")
    assert manifest["packet_schemas"] == ["packet-v0.2"]
    assert manifest["issue_counts"] == {}
    (info,) = manifest["sessions"]
    assert info["packet_schema"] == "packet-v0.2"
    assert info["device_info"]["identities"][0]["elf_sha256"] == ELF
    result = replay(session / "raw.bin", tmp_path / "replay", LOGGER_CONFIG, metadata,
                    ROOT, session / "session_manifest.json")
    assert result["expected_manifest"]["mismatches"] == []
