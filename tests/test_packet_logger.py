"""Known-answer tests of the Packet Schema V0.1 codec, receiver checks and logger.

SYNTHETIC only: they verify code against hand-derived answers, not a device.
"""

import binascii
import copy
import hashlib
import json
import random
import subprocess
import sys
from dataclasses import replace
from fractions import Fraction
from pathlib import Path

import pytest

from scripts import packet_logger
from scripts.packet_logger import record, replay
from scripts.simulate_packets import run as simulate
from software.data_io.packet_receiver import (
    analyze_stream, render_outputs, validate_config, validate_metadata,
)
from software.data_io.packet_simulation_v3 import (
    CASES, generate_stream, session_metadata,
)
from software.data_io.packet_wire import (
    SYNC, Packet, crc16_ccitt_false, decode_bytes, encode_packet,
)

ROOT = Path(__file__).resolve().parents[1]
SIM_CONFIG = ROOT / "configs/hardware/packet_simulation_v3.json"
LOGGER_CONFIG = ROOT / "configs/hardware/packet_logger.json"
EXPECTED = json.loads((ROOT / "tests/fixtures/packet_v3_expected.json").read_bytes())


@pytest.fixture
def sim():
    return json.loads(SIM_CONFIG.read_bytes())


@pytest.fixture
def logger():
    return json.loads(LOGGER_CONFIG.read_bytes())


def analyze(stream, sim_config, logger_config, case="valid", metadata=None,
            chunk=None):
    packets, decoder = decode_bytes(stream, chunk or logger_config["read_chunk_bytes"])
    metadata = metadata or session_metadata(sim_config, case, "0" * 64)
    return analyze_stream(packets, decoder, logger_config, metadata)


def decoded(stream):
    return [item.packet for item in decode_bytes(stream)[0]]


def restream(packets):
    return b"".join(encode_packet(packet) for packet in packets)


def channel(result, session=1, key="0xF1"):
    return next(s for s in result["sessions"] if s["session_id"] == session)[
        "channels"][key]


def device(sim_config):
    metadata = session_metadata(sim_config, "valid", "0" * 64)
    metadata.update(source_type="DEVICE", simulation=None)
    return metadata


def only(metadata, *keys):
    """Metadata that declares only the given channels (and their null reasons)."""
    metadata = copy.deepcopy(metadata)
    metadata["channels"] = {k: v for k, v in metadata["channels"].items() if k in keys}
    metadata["null_reasons"] = {
        name: reason for name, reason in metadata["null_reasons"].items()
        if not name.startswith("channels.") or name.split(".")[1] in keys
    }
    return metadata


def shifted(packet, microseconds):
    return replace(packet, t_anchor_us=packet.t_anchor_us + microseconds,
                   t_first_us=packet.t_first_us + microseconds)


def test_crc_known_answers_and_independent_oracle():
    for row in EXPECTED["crc16_ccitt_false"]:
        assert crc16_ccitt_false(row["ascii"].encode()) == row["crc"]
    rng = random.Random(7)
    for size in (1, 2, 46, 170):
        payload = bytes(rng.randrange(256) for _ in range(size))
        assert crc16_ccitt_false(payload) == binascii.crc_hqx(payload, 0xFFFF)


def test_encode_and_decode_match_hand_built_packet():
    example = EXPECTED["example_packet"]
    fields = dict(example["fields"], data=tuple(example["fields"]["data"]))
    payload = bytes.fromhex(example["hex"])
    assert len(payload) == example["size"] == 42 + 4 * len(fields["data"])
    assert encode_packet(Packet(**fields)) == payload
    assert int.from_bytes(payload[-2:], "little") == example["crc"]
    (item,), decoder = decode_bytes(payload)
    assert item.packet == Packet(**fields) and (item.offset, item.size) == (0, 50)
    assert decoder.errors == [] and decoder.skipped == []


@pytest.mark.parametrize("case", CASES)
def test_v3_cases_known_answers(sim, logger, case):
    expected = EXPECTED["cases"][case]
    stream, layout = generate_stream(sim, case)
    # Precondition for exact answers: no false SYNC inside any packet.
    assert stream.count(SYNC) == len(layout)
    result, _, _ = analyze(stream, sim, logger, case)
    assert result["source_type"] == "SYNTHETIC"
    assert result["issue_counts"] == expected["issue_counts"]
    accepted = {
        str(session["session_id"]): {
            key: data.get("packets_accepted", data.get("events"))
            for key, data in session["channels"].items()
        }
        for session in result["sessions"]
    }
    assert accepted == expected["accepted"]
    gaps = channel(result).get("gaps", [])
    assert [{k: g[k] for k in ("reasons", "lost_samples")} for g in gaps] == (
        expected["fault_gaps"]
    )
    if "skipped_bytes" in expected:
        assert result["decode"]["skipped_bytes"] == expected["skipped_bytes"]
    offsets = result["sessions"][0]["channel_offset"]["offset_vs_ecg_us"]
    shift = sim["time_fault_us"] if case == "offset" else 0
    assert abs(Fraction(offsets["0xF1"]) - shift) <= sim["anchor_jitter_us"] + 1
    assert abs(Fraction(offsets["0xF2"])) <= sim["anchor_jitter_us"] + 1


def test_valid_stream_has_expected_size_and_layout(sim):
    stream, layout = generate_stream(sim)
    assert len(layout) == EXPECTED["packets_in_valid_stream"]
    sizes = {key: 42 + 4 * spec["sample_count"]
             for key, spec in sim["channels"].items()}
    for offset, size, key, _, _, _ in layout:
        assert stream[offset:offset + 2] == SYNC
        assert size == sizes.get(key, 46)  # Event packets carry one DATA word.
        assert stream[offset + 2] == 0x01  # VERSION


@pytest.mark.parametrize("case", ["duplicate", "reordered"])
def test_duplicate_and_reorder_keep_valid_samples(sim, logger, case):
    valid = render_outputs(*analyze(generate_stream(sim)[0], sim, logger))
    other = render_outputs(*analyze(generate_stream(sim, case)[0], sim, logger, case))
    assert other["samples.csv"] == valid["samples.csv"]


@pytest.mark.parametrize("case", ["valid", "crc", "byte_loss", "version"])
def test_decoding_is_independent_of_chunking(sim, logger, case):
    stream = generate_stream(sim, case)[0]
    reference = render_outputs(*analyze(stream, sim, logger, case, chunk=len(stream)))
    for chunk in (1, 2, 41, 4096):
        assert render_outputs(*analyze(stream, sim, logger, case, chunk=chunk)) == (
            reference
        )


def test_leading_garbage_and_false_sync_are_skipped(sim, logger):
    stream = generate_stream(sim)[0]
    # False SYNC with a plausible header (VERSION 1, ECG, SAMPLE_COUNT 1), bad CRC.
    junk = (b"\x00" + SYNC + b"\x01\xe1" + bytes(32) + b"\x01\x00" + bytes(2)
            + bytes(4) + bytes(2) + bytes(5))
    result, _, _ = analyze(junk + stream, sim, logger)
    assert result["decode"]["packets_decoded"] == EXPECTED["packets_in_valid_stream"]
    assert result["issue_counts"] == {"crc_mismatch": 1, "skipped_bytes": 1}
    assert result["decode"]["skipped_bytes"] == len(junk)


def test_truncated_tail_is_reported_not_padded(sim, logger):
    stream = generate_stream(sim)[0]
    result, _, _ = analyze(stream[:-10], sim, logger)
    assert result["issue_counts"] == {"skipped_bytes": 1, "truncated_packet": 1}
    total = EXPECTED["packets_in_valid_stream"]
    assert result["decode"]["packets_decoded"] == total - 1


def test_implausible_headers_rejected_without_trusting_length(sim, logger):
    packets = decoded(generate_stream(sim)[0])
    too_long = replace(packets[0], data=tuple(range(33)))
    unknown = replace(packets[0], channel_id=0xD1)
    stream = encode_packet(too_long) + encode_packet(unknown) + restream(packets)
    result, _, _ = analyze(stream, sim, logger)
    assert result["issue_counts"] == {
        "bad_sample_count": 1, "skipped_bytes": 1, "unknown_channel": 1,
    }
    # The unknown channel passed CRC, so it is skipped whole; data still decodes.
    skipped = 42 + 4 * 33 + len(encode_packet(unknown))
    assert result["decode"]["skipped_bytes"] == skipped
    assert result["decode"]["packets_decoded"] == len(packets)


@pytest.mark.parametrize("channel_id", [0xE1, 0xB1])
def test_rejected_candidate_never_skips_by_declared_length(sim, logger, channel_id):
    stream = generate_stream(sim)[0]
    ecg = next(p for p in decoded(stream) if p.channel_id == 0xE1)
    # The first 50 bytes of a 106-byte packet: its declared length runs into the
    # first real packet and its CRC fails, also for a channel code that is unknown.
    false = encode_packet(replace(ecg, channel_id=channel_id))[:50]
    result, _, _ = analyze(false + stream, sim, logger)
    assert result["decode"]["errors"] == {"crc_mismatch": 1}
    assert result["decode"]["packets_decoded"] == EXPECTED["packets_in_valid_stream"]
    assert result["decode"]["skipped_bytes"] == len(false)


def test_one_damaged_packet_is_one_decode_error(sim, logger):
    packets = decoded(generate_stream(sim)[0])
    target = next(p for p in packets if p.channel_id == 0xE1 and p.seq == 1)
    # 0x5AA5 is sent as a5 5a 00 00: three false SYNC inside the damaged packet.
    damaged = bytearray(encode_packet(replace(target, data=(0x5AA5,) * 3
                                              + target.data[3:])))
    damaged[4] ^= 0x01  # SESSION_ID byte; CRC16 left unchanged.
    stream = b"".join(bytes(damaged) if p is target else encode_packet(p)
                      for p in packets)
    assert stream.count(SYNC) == len(packets) + 3
    for chunk in (1, 4096):
        result, _, _ = analyze(stream, sim, logger, chunk=chunk)
        assert result["decode"]["errors"] == {"crc_mismatch": 1}
        assert result["decode"]["sync_candidates_rejected"] == 3
        assert result["issue_counts"] == {
            "crc_mismatch": 1, "missing_packets": 1, "skipped_bytes": 1,
        }


def test_truncated_tail_is_one_error(sim, logger):
    stream = generate_stream(sim)[0]
    # A lone 0xA5 at the end is the first half of a SYNC that never arrived.
    result, _, _ = analyze(stream + SYNC[:1], sim, logger)
    assert result["issue_counts"] == {"skipped_bytes": 1, "truncated_packet": 1}
    assert result["decode"]["packets_decoded"] == EXPECTED["packets_in_valid_stream"]
    ecg = next(p for p in decoded(stream) if p.channel_id == 0xE1)
    tail = encode_packet(replace(ecg, data=(0x5AA5,) * 3 + ecg.data[3:]))[:60]
    assert tail.count(SYNC) == 4
    for chunk in (1, 4096):
        result, _, _ = analyze(stream + tail, sim, logger, chunk=chunk)
        assert result["decode"]["errors"] == {"truncated_packet": 1}
        assert result["decode"]["sync_candidates_rejected"] == 3
        assert result["decode"]["skipped_bytes"] == len(tail)


def test_conflicting_duplicate_is_quarantined(sim, logger):
    packets = decoded(generate_stream(sim)[0])
    target = next(p for p in packets if p.channel_id == 0xF1 and p.seq == 2)
    packets.append(replace(target, data=(target.data[0] ^ 1, *target.data[1:])))
    result, rows, _ = analyze(restream(packets), sim, logger)
    assert result["issue_counts"] == {"conflicting_duplicate": 1}
    assert channel(result)["packets_accepted"] == 7
    assert channel(result)["gaps"][0]["reasons"] == ["conflicting_duplicate"]
    assert sum(r["disposition"] == "conflicting_duplicate" for r in rows) == 2


def test_seq_and_index_wraparound_extend_counters(sim, logger):
    sim["seq_start"] = 2 ** 32 - 3
    sim["index_start"] = 2 ** 32 - 10
    result, rows, samples = analyze(generate_stream(sim)[0], sim, logger)
    assert result["issue_counts"] == {}
    ppg = channel(result)
    assert (ppg["first_seq"], ppg["last_seq"]) == (2 ** 32 - 3, 2 ** 32 + 4)
    indices = [s[4] for s in samples if s[1] == "0xF1"]
    assert indices == list(range(2 ** 32 - 10, 2 ** 32 - 10 + 32))


def test_index_jump_without_status_is_unexplained(sim, logger):
    packets = decoded(generate_stream(sim)[0])
    shifted = [
        replace(p, first_sample_index=p.first_sample_index + 5,
                t_anchor_us=p.t_anchor_us + 50000, t_first_us=p.t_first_us + 50000)
        if p.channel_id == 0xF1 and p.seq > 2 else p
        for p in packets
    ]
    result, _, _ = analyze(restream(shifted), sim, logger)
    assert result["issue_counts"] == {"sample_gap_unexplained": 1}
    assert channel(result)["gaps"][0]["lost_samples"] == 5


def test_index_overlap_quarantines_packet(sim, logger):
    packets = decoded(generate_stream(sim)[0])
    bad = [replace(p, first_sample_index=p.first_sample_index - 2)
           if p.channel_id == 0xF1 and p.seq == 3 else p for p in packets]
    result, _, _ = analyze(restream(bad), sim, logger)
    assert result["issue_counts"] == {"sample_index_overlap": 1}
    assert channel(result)["packets_quarantined"] == {"index_overlap": 1}


def test_anchor_not_increasing_is_flagged(sim, logger):
    packets = decoded(generate_stream(sim)[0])
    previous = next(p for p in packets if p.channel_id == 0xF1 and p.seq == 2)
    bad = [replace(p, t_anchor_us=previous.t_anchor_us)
           if p.channel_id == 0xF1 and p.seq == 3 else p for p in packets]
    result, _, _ = analyze(restream(bad), sim, logger)
    assert result["issue_counts"] == {"timestamp_anomaly": 1}
    assert result["issues"][0]["kind"] == "not_increasing"


@pytest.mark.parametrize("key,seq,shift", [
    ("0xF1", 0, 20000), ("0xF1", 0, -20000), ("0xE1", 0, 20000),
    ("0xE1", 0, -20000), ("0xF1", 7, 20000),
])
def test_bad_first_or_last_anchor_quarantines_only_that_packet(sim, logger, key, seq,
                                                               shift):
    channel_id = int(key, 16)
    packets = [shifted(p, shift) if (p.channel_id, p.seq) == (channel_id, seq) else p
               for p in decoded(generate_stream(sim)[0])]
    result, _, _ = analyze(restream(packets), sim, logger)
    assert result["issue_counts"] == {"timestamp_anomaly": 1}
    assert [(i["channel"], i["seq"]) for i in result["issues"]] == [(key, seq)]
    assert channel(result, key=key)["packets_accepted"] == 7
    # The channel offset comes from accepted packets, not from the bad one.
    offsets = result["sessions"][0]["channel_offset"]["offset_vs_ecg_us"]
    assert abs(Fraction(offsets["0xF1"])) <= sim["anchor_jitter_us"] + 1


@pytest.mark.parametrize("start,quarantined", [(5, [5, 6, 7]), (3, [0, 1, 2])])
def test_lasting_anchor_step_quarantines_shorter_side(sim, logger, start,
                                                      quarantined):
    packets = [shifted(p, 30000) if p.channel_id == 0xE1 and p.seq >= start else p
               for p in decoded(generate_stream(sim)[0])]
    result, _, _ = analyze(restream(packets), sim, logger, metadata=device(sim))
    assert {i["code"] for i in result["issues"]} == {"timestamp_anomaly"}
    assert [i["seq"] for i in result["issues"]] == quarantined


@pytest.mark.parametrize("rate", [Fraction(97, 100), Fraction(101, 100),
                                  Fraction(103, 100)])
@pytest.mark.parametrize("gap", [10, 50])
@pytest.mark.parametrize("shift", [0, 20000, -20000])
def test_rate_error_and_gap_keep_good_packets(sim, logger, rate, gap, shift):
    # PPG 0xF1, 100 Hz nominal, N = 4; the true sample RATE is ``rate`` times
    # the nominal one (period / rate). SEQ 10 .. 10 + gap - 1 are lost; ``shift``
    # hits the next one.
    lost, period = range(10, 10 + gap), Fraction(10 ** 9, 100000)
    packets = []
    for seq in range(120):
        if seq in lost:
            continue
        anchor = round(1_000_000 + (4 * seq + 3) * period / rate + 1000)
        anchor += shift if seq == lost.stop else 0
        packets.append(Packet(1, 0xF1, 1, seq, 4 * seq, anchor,
                              round(anchor - 3 * period), 100000, 16, (7,) * 4))
    result, _, _ = analyze(restream(packets), sim, logger,
                           metadata=only(device(sim), "0xF1"))
    bad = [i["seq"] for i in result["issues"] if i["code"] == "timestamp_anomaly"]
    assert bad == ([lost.stop] if shift else [])
    assert result["issue_counts"] == {"missing_packets": 1, **(
        {"timestamp_anomaly": 1} if shift else {})}
    assert channel(result)["packets_accepted"] == 120 - gap - len(bad)


def test_afe_overflow_packet_keeps_samples_but_not_its_late_anchor(sim, logger):
    # PPG 100 Hz, N = 4. The FIFO was full when SEQ 5 was read: its 4 samples
    # are old, the anchor is the read time, 10 samples (100 ms) late, and 10
    # samples were lost after it (bit 0; the next index jumps by 10).
    period, lost = 10_000, 10
    packets = []
    for seq in range(12):
        first = 4 * seq + (lost if seq > 5 else 0)
        anchor = 1_000_000 + (first + 3) * period + (lost * period if seq == 5 else 0)
        packets.append(Packet(1, 0xF1, 1, seq, first, anchor, anchor - 3 * period,
                              100000, 16 | (1 if seq == 5 else 0), (7,) * 4))
    result, rows, samples = analyze(restream(packets), sim, logger,
                                    metadata=only(device(sim), "0xF1"))
    assert result["issue_counts"] == {"sample_gap_status": 1}
    summary = channel(result)
    assert summary["packets_accepted"] == 12
    assert summary["packets_anchor_unreliable"] == 1
    assert summary["samples_accepted"] == 48
    assert {r["seq"]: r["disposition"] for r in rows}[5] == "accepted_anchor_unreliable"
    # Before 2026-10-23 the late anchor quarantined the whole packet.
    assert summary["packets_quarantined"] == {}


def test_late_anchor_of_overflow_packet_is_not_the_channel_offset_reference(sim,
                                                                            logger):
    packets = [replace(shifted(p, 50_000), status=p.status | 1)
               if (p.channel_id, p.seq) == (0xF1, 0) else p
               for p in decoded(generate_stream(sim)[0])]
    result, _, _ = analyze(restream(packets), sim, logger)
    assert result["issue_counts"] == {}
    assert channel(result)["packets_anchor_unreliable"] == 1


@pytest.mark.parametrize("steps,elapsed,flagged", [
    # r = 3 %, no fixed slack, T = 10 000 us. The true period lies in
    # [T/1.03, T/0.97]: 97 samples take at most 1 000 000 us (rate -3 %) and
    # 103 samples at least 1 000 000 us (rate +3 %), both exactly on the bound.
    (97, 1_000_000, False), (97, 1_000_001, True),
    (103, 1_000_000, False), (103, 999_999, True),
])
def test_rate_tolerance_is_on_the_rate_not_the_period(sim, logger, steps, elapsed,
                                                      flagged):
    # The old bound 3 % * steps * T rejected the first case (excess 30 000 us >
    # 29 100 us) although a rate exactly 3 % slow is inside the tolerance.
    config = dict(logger, anchor_tolerance_samples=0, anchor_tolerance_extra_us=0)
    first = Packet(1, 0xF1, 1, 0, 0, 1_000_000, 970_000, 100000, 16, (7,) * 4)
    # SEQ 25 after 24 lost packets keeps the index jump consistent with SEQ.
    second = Packet(1, 0xF1, 1, 25, steps, 1_000_000 + elapsed, 0, 100000, 16,
                    (7,) * 4)
    result, _, _ = analyze(restream([first, second]), sim, config,
                           metadata=only(device(sim), "0xF1"))
    assert ("timestamp_anomaly" in result["issue_counts"]) is flagged
    assert result["issue_counts"]["missing_packets"] == 1


def test_backward_reanchor_keeps_chains_apart(sim, logger):
    # After SYNCH (schema section 9) the ECG index restarts at 0 with bit 5.
    packets = [
        replace(p, first_sample_index=p.first_sample_index - 64,
                status=p.status | (1 << 5) | (1 << 0) if p.seq == 4 else p.status)
        if p.channel_id == 0xE1 and p.seq >= 4 else p
        for p in decoded(generate_stream(sim)[0])
    ]
    result, rows, samples = analyze(restream(packets), sim, logger,
                                    metadata=device(sim))
    assert result["issue_counts"] == {"sample_index_reanchored": 1}
    assert channel(result, key="0xE1")["chains"] == 2
    chain_ids = [r["chain_id"] for r in rows if r["channel_id"] == "0xE1"]
    assert chain_ids == [0] * 4 + [1] * 4
    lines = render_outputs(result, rows, samples)["samples.csv"].decode().splitlines()
    assert lines[0] == "session_id,channel_id,chain_id,seq_ext,sample_index_ext,value"
    ecg = [line.split(",") for line in lines[1:] if line.split(",")[1] == "0xE1"]
    keys = [(s[0], s[1], s[2], s[4]) for s in ecg]
    assert len(set(keys)) == len(keys) == 128
    assert [s[2] for s in ecg] == ["0"] * 64 + ["1"] * 64  # Chains not interleaved.
    for chain in ("0", "1"):
        assert [int(s[4]) for s in ecg if s[2] == chain] == list(range(64))


def test_fs_zero_is_quarantined_without_crash(sim, logger):
    packets = decoded(generate_stream(sim)[0])
    no_rate = [replace(p, fs_nominal_mhz=0) if p.channel_id == 0xE1 else p
               for p in packets]
    result, _, samples = analyze(restream(no_rate), sim, logger)
    assert result["issue_counts"] == {"fs_invalid": 8, "fs_metadata_mismatch": 1}
    assert channel(result, key="0xE1")["packets_quarantined"] == {"fs_invalid": 8}
    assert not [s for s in samples if s[1] == "0xE1"]
    assert result["sessions"][0]["channel_offset"] == {
        "offset_vs_ecg_us": None, "reason": "no accepted ECG packet",
    }
    one = [replace(p, fs_nominal_mhz=0) if p.channel_id == 0xF1 and p.seq == 3 else p
           for p in packets]
    result, _, _ = analyze(restream(one), sim, logger)
    # No fs_changed around it, and the chain is not split.
    assert result["issue_counts"] == {"fs_invalid": 1, "fs_metadata_mismatch": 1}
    assert channel(result)["gaps"][0]["reasons"] == ["fs_invalid"]
    assert channel(result)["chains"] == 1


@pytest.mark.parametrize("status,expected", [
    (16, {"missing_packets": 1, "sample_index_inconsistent": 1}),
    (17, {"missing_packets": 1}),  # Bit 0: the AFE lost samples as well.
])
def test_index_jump_beyond_what_absent_packets_carry(sim, logger, status, expected):
    # ECG SEQ 2 lost, yet the index moves 16 + 300 samples: more than 32 per
    # absent packet.
    shift = round(300 * Fraction(10 ** 9, 512000))
    packets = [
        replace(shifted(p, shift), first_sample_index=p.first_sample_index + 300,
                status=status if p.seq == 3 else p.status)
        if p.channel_id == 0xE1 and p.seq >= 3 else p
        for p in decoded(generate_stream(sim)[0])
        if (p.channel_id, p.seq) != (0xE1, 2)
    ]
    result, _, _ = analyze(restream(packets), sim, logger, metadata=device(sim))
    assert result["issue_counts"] == expected


def test_data_out_of_range_is_flagged_and_kept(sim, logger):
    values = {(0xE1, 1): 1 << 24, (0xF1, 1): 1 << 18, (0xF2, 1): -1}
    packets = [replace(p, data=(values[p.channel_id, p.seq], *p.data[1:]))
               if (p.channel_id, p.seq) in values else p
               for p in decoded(generate_stream(sim)[0])]
    result, _, samples = analyze(restream(packets), sim, logger)
    assert result["issue_counts"] == {"data_out_of_range": 3}
    assert set(values.values()) <= {s[5] for s in samples}


def test_reserved_status_bit_and_missing_run(sim, logger):
    packets = decoded(generate_stream(sim)[0])
    reserved = [replace(p, status=p.status | 1 << 9)
                if (p.channel_id, p.seq) == (0xE1, 1) else p for p in packets]
    result, _, _ = analyze(restream(reserved), sim, logger)
    assert result["issue_counts"] == {"status_reserved_bits": 1}
    two_lost = [p for p in packets if not (p.channel_id == 0xF1 and p.seq in (2, 3))]
    result, _, _ = analyze(restream(two_lost), sim, logger)
    assert result["issue_counts"] == {"missing_packets": 1}
    assert result["issues"][0]["count"] == channel(result)["missing_packets"] == 2


def test_t_first_is_anchor_minus_n_minus_1_periods(sim):
    # Schema section 5.3: T_FIRST_US = T_ANCHOR_US - (N - 1) * 10**6 / fs (Hz).
    for packet in decoded(generate_stream(sim)[0]):
        if packet.channel_id != 0xC1:
            period = Fraction(10 ** 9, packet.fs_nominal_mhz)
            assert packet.t_first_us == round(
                packet.t_anchor_us - (len(packet.data) - 1) * period)


def test_simulated_events_send_status_zero_like_the_firmware(sim):
    # Schema section 10: bit 4 (latency unmeasured) is off for event packets.
    packets = decoded(generate_stream(sim)[0])
    assert {p.status for p in packets if p.channel_id == 0xC1} == {0}
    assert {p.status for p in packets if p.channel_id != 0xC1} == {sim["status"]}


def test_event_packets_skip_anchor_check(sim, logger):
    packets = decoded(generate_stream(sim)[0])
    events = [p for p in packets if p.channel_id == 0xC1]
    odd = [
        replace(events[0], t_anchor_us=5, fs_nominal_mhz=7),
        replace(events[1], data=(9,)),
    ]
    others = [p for p in packets if p.channel_id != 0xC1]
    result, _, _ = analyze(restream(others + odd), sim, logger)
    assert result["issue_counts"] == {"unknown_event_code": 1}
    assert [e["event_ordinal"] for e in result["sessions"][0]["events"]] == [0, 1]
    two = replace(events[0], data=(1, 2))
    result, _, _ = analyze(restream(others + [two]), sim, logger)
    assert result["issue_counts"] == {"event_sample_count": 1}


def event(seq, ordinal, status=0):
    return Packet(1, 0xC1, 1, seq % (1 << 32), ordinal % (1 << 32),
                  2_000_000 + 1000 * ordinal, 2_000_000 + 1000 * ordinal, 0, status,
                  (1,))


@pytest.mark.parametrize("pairs,expected,lost", [
    # (SEQ, ordinal) of received events. SEQ is given at send time, so an event
    # dropped in the MCU queue moves the ordinal but not SEQ.
    ([(10, 0), (11, 2)], {"events_lost_before_send": 1}, [1]),
    ([(10, 0), (12, 2)], {"missing_packets": 1}, []),  # Lost on USB only.
    ([(10, 0), (12, 4)], {"missing_packets": 1, "events_lost_before_send": 1}, [2]),
    # Both counters wrap past 2**32 independently.
    ([((1 << 32) - 1, (1 << 32) - 2), (1 << 32, 1 << 32)],
     {"events_lost_before_send": 1}, [1]),
])
def test_event_ordinal_gap_is_a_lost_event(sim, logger, pairs, expected, lost):
    result, _, _ = analyze(restream([event(s, o) for s, o in pairs]), sim, logger,
                           metadata=only(device(sim), "0xC1"))
    assert result["issue_counts"] == expected
    assert [i["lost_events"] for i in result["issues"]
            if i["code"] == "events_lost_before_send"] == lost


def test_event_status_bit1_and_bad_ordinal(sim, logger):
    metadata = only(device(sim), "0xC1")
    # Bit 1 on the first event: something was dropped, count unknown.
    result, _, _ = analyze(restream([event(0, 0, status=2), event(1, 1)]), sim,
                           logger, metadata=metadata)
    assert [(i["code"], i["lost_events"]) for i in result["issues"]] == [
        ("events_lost_before_send", None)]
    # Bit 1 together with a counted gap is one issue, not two.
    result, _, _ = analyze(restream([event(0, 0), event(1, 2, status=2)]), sim,
                           logger, metadata=metadata)
    assert [(i["code"], i["lost_events"]) for i in result["issues"]] == [
        ("events_lost_before_send", 1)]
    # An ordinal going back is flagged once; the next events are checked from it.
    result, _, _ = analyze(restream([event(0, 5), event(1, 3), event(2, 4),
                                     event(3, 5)]), sim, logger, metadata=metadata)
    assert result["issue_counts"] == {"event_ordinal_inconsistent": 1}
    assert [e["event_ordinal"] for e in result["sessions"][0]["events"]] == [
        5, 3, 4, 5]


@pytest.mark.parametrize("dead", [("0xE1",), ("0xF2",), ("0xE1", "0xF1")])
def test_declared_channel_without_packets_is_missing(sim, logger, dead):
    keep = [p for p in decoded(generate_stream(sim)[0])
            if f"0x{p.channel_id:02X}" not in dead]
    result, _, _ = analyze(restream(keep), sim, logger)
    assert result["issue_counts"] == {"channel_missing": len(dead)}
    assert result["sessions"][0]["channels_missing"] == sorted(dead)
    # Events may be absent (a bench session without t0).
    no_events = [p for p in keep if p.channel_id != 0xC1]
    result, _, _ = analyze(restream(no_events), sim, logger)
    assert result["sessions"][0]["channels_missing"] == sorted(dead)


def test_channel_with_only_quarantined_packets_is_not_missing(sim, logger):
    packets = [replace(p, fs_nominal_mhz=0) if p.channel_id == 0xF2 else p
               for p in decoded(generate_stream(sim)[0])]
    result, _, _ = analyze(restream(packets), sim, logger)
    assert "channel_missing" not in result["issue_counts"]
    assert result["sessions"][0]["channels_missing"] == []


@pytest.mark.parametrize("at", [0, 3])
@pytest.mark.parametrize("offset", [400, -400, (1 << 32) - 7])
def test_fs_zero_packet_with_bad_index_does_not_move_the_reference(sim, logger, at,
                                                                    offset):
    # FS 0 marks an untrusted header: whatever its index, the packets after it
    # are still checked against the last trusted packet.
    packets = [
        replace(p, fs_nominal_mhz=0,
                first_sample_index=(p.first_sample_index + offset) % (1 << 32))
        if p.channel_id == 0xF1 and p.seq in (at, at + 1) else p
        for p in decoded(generate_stream(sim)[0])
    ]
    result, _, _ = analyze(restream(packets), sim, logger)
    assert result["issue_counts"] == {"fs_invalid": 2, "fs_metadata_mismatch": 1}
    assert channel(result)["packets_quarantined"] == {"fs_invalid": 2}
    assert channel(result)["packets_accepted"] == 6
    assert channel(result)["chains"] == 1


def test_device_source_never_reports_channel_offset(sim, logger):
    metadata = session_metadata(sim, "offset", "0" * 64)
    metadata.update(source_type="DEVICE", simulation=None)
    result, _, _ = analyze(generate_stream(sim, "offset")[0], sim, logger,
                           metadata=metadata)
    assert result["issue_counts"] == {}
    assert result["sessions"][0]["channel_offset"]["offset_vs_ecg_us"] is None


def test_metadata_needs_reason_for_each_null(sim):
    metadata = session_metadata(sim, "valid", "0" * 64)
    assert validate_metadata(metadata)
    for mutate in (
        lambda m: m["null_reasons"].pop("operator"),
        lambda m: m["null_reasons"].update(device_id="not null"),
        lambda m: m.update(source_type="DEVICE"),  # DEVICE with simulation block
        lambda m: m.update(source_type="REAL"),
        lambda m: m["channels"]["0xE1"].pop("sensor"),
    ):
        broken = copy.deepcopy(metadata)
        mutate(broken)
        with pytest.raises(ValueError):
            validate_metadata(broken)


@pytest.mark.parametrize("field,value", [
    ("wire_versions", [2]), ("anchor_tolerance_samples", -1),
    ("schema_version", "packet-logger-v0"), ("read_chunk_bytes", 0),
    ("anchor_rate_tolerance_ppm", 10 ** 5 + 1),
])
def test_logger_config_rejected(logger, field, value):
    logger[field] = value
    with pytest.raises(ValueError):
        validate_config(logger)


@pytest.mark.parametrize("field,value", [
    ("time_fault_us", 201), ("unsupported_version", 1), ("fault_index", 0),
    ("schema_version", "synthetic-packet-v2"), ("status", 1 << 7),
    ("events", [{"code": 1, "time_us": 5}, {"code": 2, "time_us": 5}]),
])
def test_v3_config_rejected(sim, field, value):
    sim[field] = value
    with pytest.raises(ValueError):
        generate_stream(sim)


def test_v3_config_rejects_ppg_slots_with_different_rates(sim):
    sim["channels"]["0xF2"]["fs_nominal_mhz"] = 200000
    with pytest.raises(ValueError):
        generate_stream(sim)


def test_record_replay_identical_and_no_overwrite(tmp_path):
    generated = tmp_path / "generated"
    report = simulate(SIM_CONFIG, "crc", generated)
    stream = (generated / "stream.bin").read_bytes()
    assert report["stream_sha256"] == hashlib.sha256(stream).hexdigest()
    metadata = generated / "session_metadata.json"
    session = tmp_path / "session"
    with (generated / "stream.bin").open("rb") as source:
        manifest = record(source, session, LOGGER_CONFIG, metadata, ROOT, "stream.bin")
    # Raw keeps every received byte, including the corrupt packet.
    assert (session / "raw.bin").read_bytes() == stream
    assert manifest["issue_counts"] == EXPECTED["cases"]["crc"]["issue_counts"]
    assert manifest["session_id"] == 1 and manifest["source_type"] == "SYNTHETIC"
    for name, digest in manifest["outputs_sha256"].items():
        assert hashlib.sha256((session / name).read_bytes()).hexdigest() == digest
    assert b"t_rx" not in (session / "decode.json").read_bytes()
    assert b"t_rx" not in (session / "packets.csv").read_bytes()
    replayed = tmp_path / "replay"
    result = replay(session / "raw.bin", replayed, LOGGER_CONFIG, metadata, ROOT,
                    session / "session_manifest.json")
    assert result["expected_manifest"]["mismatches"] == []
    assert manifest["logger_version"] == result["logger_version"] == "packet-logger-v1"
    # A manifest written by another logger version is named as a mismatch.
    older = tmp_path / "older_manifest.json"
    older.write_text(json.dumps({**manifest, "logger_version": "packet-logger-v0"}),
                     encoding="utf-8")
    result = replay(session / "raw.bin", tmp_path / "replay_old", LOGGER_CONFIG,
                    metadata, ROOT, older)
    assert result["expected_manifest"]["mismatches"] == ["logger_version"]
    for name in ("decode.json", "packets.csv", "samples.csv"):
        assert (replayed / name).read_bytes() == (session / name).read_bytes()
    with pytest.raises(FileExistsError), (generated / "stream.bin").open("rb") as s:
        record(s, session, LOGGER_CONFIG, metadata, ROOT, "stream.bin")
    with pytest.raises(FileExistsError):
        replay(session / "raw.bin", replayed, LOGGER_CONFIG, metadata, ROOT)


def test_manifest_is_written_last(tmp_path, monkeypatch):
    generated = tmp_path / "generated"
    simulate(SIM_CONFIG, "valid", generated)
    written, write = [], packet_logger._write

    def spy(directory, name, payload):
        written.append(name)
        write(directory, name, payload)

    monkeypatch.setattr(packet_logger, "_write", spy)
    with (generated / "stream.bin").open("rb") as source:
        record(source, tmp_path / "session", LOGGER_CONFIG,
               generated / "session_metadata.json", ROOT, "stream.bin")
    assert written[-1] == "session_manifest.json"
    assert "session_manifest.json" not in written[:-1]


def test_input_copies_exist_before_first_read_and_survive_interruption(tmp_path):
    generated = tmp_path / "generated"
    simulate(SIM_CONFIG, "valid", generated)
    metadata = generated / "session_metadata.json"
    stream = (generated / "stream.bin").read_bytes()
    session = tmp_path / "session"

    class Interrupted:
        reads = 0

        def read(self, n):
            # The copies are on disk before any byte is taken from the source.
            for name, source in (("logger_config.json", LOGGER_CONFIG),
                                 ("session_metadata.json", metadata)):
                assert (session / name).read_bytes() == source.read_bytes()
            self.reads += 1
            if self.reads > 1:
                raise KeyboardInterrupt
            return stream[:n]

    with pytest.raises(KeyboardInterrupt):
        record(Interrupted(), session, LOGGER_CONFIG, metadata, ROOT, "stream.bin")
    chunk = json.loads(LOGGER_CONFIG.read_bytes())["read_chunk_bytes"]
    assert (session / "raw.bin").read_bytes() == stream[:chunk]
    assert not (session / "session_manifest.json").exists()


def test_raw_and_outputs_are_opened_exclusively(tmp_path, monkeypatch):
    packet_logger._write(tmp_path, "out.json", b"first")
    with pytest.raises(FileExistsError):
        packet_logger._write(tmp_path, "out.json", b"second")
    assert (tmp_path / "out.json").read_bytes() == b"first"
    generated, session = tmp_path / "generated", tmp_path / "session"
    simulate(SIM_CONFIG, "valid", generated)
    session.mkdir()
    (session / "raw.bin").write_bytes(b"earlier session")
    # Defeat the directory guards so that only the exclusive open of raw.bin is left.
    exists, mkdir = Path.exists, Path.mkdir
    monkeypatch.setattr(Path, "exists", lambda self: self != session and exists(self))
    monkeypatch.setattr(Path, "mkdir", lambda self, *args, **kwargs: (
        None if self == session else mkdir(self, *args, **kwargs)))
    with pytest.raises(FileExistsError), (generated / "stream.bin").open("rb") as s:
        record(s, session, LOGGER_CONFIG, generated / "session_metadata.json", ROOT,
               "stream.bin")
    assert (session / "raw.bin").read_bytes() == b"earlier session"


def test_session_restart_manifest_lists_both_sessions(tmp_path):
    generated = tmp_path / "generated"
    simulate(SIM_CONFIG, "session_restart", generated)
    with (generated / "stream.bin").open("rb") as source:
        manifest = record(source, tmp_path / "session", LOGGER_CONFIG,
                          generated / "session_metadata.json", ROOT, "stream.bin")
    assert manifest["session_ids"] == [1, 2] and manifest["session_id"] is None
    assert "session_id" in manifest["null_reasons"]


def test_v2_and_v3_inputs_are_not_mixed(tmp_path):
    with pytest.raises(ValueError):
        simulate(ROOT / "configs/hardware/packet_simulation.json", "crc",
                 tmp_path / "v2")
    with pytest.raises(ValueError):
        simulate(SIM_CONFIG, "valid", tmp_path / "v3", tmp_path / "packets.json")


def test_cli_replay_detects_changed_input(tmp_path):
    python = [sys.executable, "-B"]
    generated, session = tmp_path / "generated", tmp_path / "session"
    metadata = str(generated / "session_metadata.json")
    for args in (
        [str(ROOT / "scripts/simulate_packets.py"), "--config", str(SIM_CONFIG),
         "--case", "valid", "--output", str(generated)],
        [str(ROOT / "scripts/packet_logger.py"), "record", "--source-file",
         str(generated / "stream.bin"), "--metadata", metadata,
         "--output", str(session)],
        [str(ROOT / "scripts/packet_logger.py"), "replay", "--raw",
         str(session / "raw.bin"), "--metadata", metadata, "--expect",
         str(session / "session_manifest.json"), "--output", str(tmp_path / "same")],
    ):
        done = subprocess.run(python + args, cwd=tmp_path, capture_output=True,
                              text=True, check=False)
        assert done.returncode == 0, done.stderr
    changed = tmp_path / "changed_metadata.json"
    edited = json.loads((generated / "session_metadata.json").read_bytes())
    edited["device_id"] = "SYN_DEVICE_002"
    changed.write_text(json.dumps(edited), encoding="utf-8")
    done = subprocess.run(python + [
        str(ROOT / "scripts/packet_logger.py"), "replay", "--raw",
        str(session / "raw.bin"), "--metadata", str(changed),
        "--expect", str(session / "session_manifest.json"),
        "--output", str(tmp_path / "different"),
    ], cwd=tmp_path, capture_output=True, text=True, check=False)
    assert done.returncode == 1
    assert "input:session_metadata" in done.stdout
