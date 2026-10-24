"""Compile and run the firmware IMU read planner on the host.

firmware/app/imu_plan.c (with packet_wire.c for T_FIRST_US) has no ESP-IDF
dependency. Its answers are checked against Packet Schema V0.2 sections 3-5:
the re-anchor formula and the backlog split against the reviewed simulator
functions (software/data_io/packet_simulation_v3.py), the STATUS and index
rules against hand-written scenarios, and a fake BMI270 timeline (100 Hz,
watermark 10, 170-frame FIFO that stops when full, deliberate read stalls)
against the logger. SYNTHETIC only; no MCU, task or BMI270 is involved. Without
a host C compiler the test is skipped, like test_firmware_c_encoder.py.
"""

import json
import os
import random
import subprocess
from fractions import Fraction
from pathlib import Path

import pytest

from software.data_io.packet_receiver import analyze_stream
from software.data_io.packet_simulation_v3 import backlog_chunks, reanchor_index
from software.data_io.packet_wire import Packet, decode_bytes, encode_packet
from tests.test_firmware_c_encoder import _compiler

ROOT = Path(__file__).resolve().parents[1]
IMU = (0xA1, 0xA2, 0xA3, 0xA4, 0xA5, 0xA6)
BIT0, BIT3, BIT4, BIT5, BIT7 = 1 << 0, 1 << 3, 1 << 4, 1 << 5, 1 << 7
FS = 100_000  # 100 Hz, T = 10 000 us

HARNESS = r"""
#include <stdio.h>

#include "imu_plan.h"

int main(void)
{
    imu_index_t s;
    imu_index_init(&s, 0);
    char cmd[2];
    while (scanf("%1s", cmd) == 1) {
        if (cmd[0] == 'N') {
            long long start;
            if (scanf("%lld", &start) != 1) {
                return 2;
            }
            imu_index_init(&s, start);
            printf("n\n");
        } else if (cmd[0] == 'X') {
            imu_index_read_failed(&s);
            printf("x\n");
        } else if (cmd[0] == 'Q') {
            long long last_prev, ref_last, ref_anchor, next_anchor;
            unsigned long fs, count;
            if (scanf("%lld %lld %lld %lld %lu %lu", &last_prev, &ref_last, &ref_anchor,
                      &next_anchor, &fs, &count) != 6) {
                return 2;
            }
            printf("%lld\n", (long long)imu_reanchor_index(last_prev, ref_last, ref_anchor,
                                                           next_anchor, (uint32_t)fs,
                                                           (uint32_t)count));
        } else if (cmd[0] == 'R') {
            unsigned long frames, fs, cap;
            unsigned long long anchor;
            unsigned full, base;
            if (scanf("%lu %llu %u %lu %u %lu", &frames, &anchor, &full, &fs, &base,
                      &cap) != 6) {
                return 2;
            }
            imu_chunk_t out[IMU_MAX_CHUNKS + 1];
            size_t n = imu_plan_read(&s, (uint32_t)frames, anchor, full != 0, (uint32_t)fs,
                                     (uint16_t)base, out, cap);
            printf("%u", (unsigned)n);
            for (size_t k = 0; k < n; k++) {
                printf(" %lu %u %u %llu %u", (unsigned long)out[k].first_index,
                       (unsigned)out[k].count, (unsigned)out[k].offset,
                       (unsigned long long)out[k].t_first_us, (unsigned)out[k].status);
            }
            printf("\n");
        } else {
            return 2;
        }
    }
    return 0;
}
"""


@pytest.fixture(scope="module")
def harness(tmp_path_factory):
    compiler = _compiler()
    if compiler is None:
        pytest.skip("no host C compiler ($CC, cc, gcc or clang)")
    work = tmp_path_factory.mktemp("imu_plan")
    (work / "harness.c").write_text(HARNESS, encoding="utf-8")
    exe = work / ("harness.exe" if os.name == "nt" else "harness")
    build = subprocess.run(
        [*compiler, "-std=c99", "-Wall", "-Wextra", "-Werror",
         "-I", str(ROOT / "firmware/include"),
         str(ROOT / "firmware/app/imu_plan.c"), str(ROOT / "firmware/app/packet_wire.c"),
         str(work / "harness.c"), "-o", str(exe)],
        capture_output=True, text=True,
    )
    assert build.returncode == 0, build.stderr
    return exe


def _call(exe, lines):
    run = subprocess.run([str(exe)], input="\n".join(lines) + "\n",
                         capture_output=True, text=True, timeout=60)
    assert run.returncode == 0, run.stderr
    out = run.stdout.splitlines()
    assert len(out) == len(lines)
    return out


def _read(frames, anchor, full=False, base=BIT4, cap=6, fs=FS):
    return f"R {frames} {anchor} {int(full)} {fs} {base} {cap}"


def _chunks(line):
    n, *values = map(int, line.split())
    rows = [tuple(values[5 * k:5 * k + 5]) for k in range(n)]
    return [dict(zip(("first", "count", "offset", "t_first", "status"), r))
            for r in rows]


@pytest.mark.parametrize("next_anchor,expected", [
    (1_400_000, 50), (1_404_999, 50), (1_405_000, 51), (1_150_000, 30),
    (1_000_000, 30), (999_000, 30),
])
def test_reanchor_formula_known_answers(harness, next_anchor, expected):
    # Same table as test_packet_v02.py: reference last index 19 at 1 000 000 us,
    # last sent 29, next read of 10 frames, T = 10 000 us.
    (out,) = _call(harness, [f"Q 29 19 1000000 {next_anchor} {FS} 10"])
    assert int(out) == expected


def test_reanchor_formula_matches_simulator(harness):
    rng = random.Random(24)
    cases = []
    for _ in range(400):
        fs = rng.choice((FS, 128_000, 512_000, rng.randint(1, (1 << 32) - 1)))
        ref_anchor = rng.randint(0, 1 << 40)
        elapsed = rng.choice((rng.randint(-10 ** 6, 10 ** 7), rng.randint(0, 10 ** 15)))
        last_prev = rng.randint(-1, 1 << 40)
        cases.append((last_prev, last_prev - rng.randint(0, 500), ref_anchor,
                      ref_anchor + elapsed, fs, rng.randint(1, 170)))
    out = _call(harness, [f"Q {' '.join(map(str, c))}" for c in cases])
    for (last_prev, ref_last, ref_anchor, next_anchor, fs, count), line in zip(cases, out):
        expected = reanchor_index(last_prev, ref_last, ref_anchor, next_anchor,
                                  Fraction(10 ** 9, fs), count)
        assert int(line) == expected


@pytest.mark.parametrize("frames", [1, 10, 31, 32, 33, 64, 65, 96, 169, 170])
def test_backlog_split_matches_simulator(harness, frames):
    anchor = 5_000_000 + frames
    (line,) = _call(harness, ["N 100", _read(frames, anchor)])[1:]
    chunks = _chunks(line)
    expected = backlog_chunks(100, frames, anchor, Fraction(10 ** 9, FS), BIT4)
    assert [(c["first"], c["count"], c["t_first"], c["status"]) for c in chunks] == (
        expected)
    assert [c["offset"] for c in chunks] == [32 * k for k in range(len(chunks))]


def test_full_failed_and_reanchor_rules(harness):
    lines = [
        "N 0",
        _read(10, 100_000),                 # 0-9, reliable reference (9, 100 000)
        _read(170, 2_000_000, full=True),   # 10-179, every packet bit 0
        _read(10, 2_100_000),               # re-anchors: q = 200, 9 + 200 - 9 = 200
        _read(170, 4_000_000, full=True),   # 210-379, full again
        _read(170, 5_800_000, full=True),   # full twice in a row: last + 1, bit 5
        _read(40, 6_000_000),               # from (209, 2 100 000): 209 + 390 - 39
        "X",                                # read failed: nothing sent
        _read(10, 6_200_000),               # bits 3 and 5: 599 + 20 - 9
        _read(5, 6_250_000),                # continues, no extra bits
        _read(0, 6_300_000),                # nothing planned, state unchanged
        _read(40, 6_300_000, cap=1),        # 2 chunks do not fit in 1: nothing
        _read(5, 6_300_000),                # continues after the refused reads
    ]
    out = [_chunks(line) for line in _call(harness, lines)[1:] if line != "x"]
    firsts = [[c["first"] for c in read] for read in out]
    statuses = [[c["status"] for c in read] for read in out]
    assert firsts == [[0], [10, 42, 74, 106, 138, 170], [200],
                      [210, 242, 274, 306, 338, 370], [380, 412, 444, 476, 508, 540],
                      [560, 592], [610], [620], [], [], [625]]
    full_chunks = [BIT4 | BIT0 | BIT7] * 5 + [BIT4 | BIT0]
    assert statuses == [
        [BIT4], full_chunks, [BIT4 | BIT5], full_chunks,
        [full_chunks[0] | BIT5] + full_chunks[1:], [BIT4 | BIT5 | BIT7, BIT4],
        [BIT4 | BIT3 | BIT5], [BIT4], [], [], [BIT4]]


def test_first_read_full_has_no_reference(harness):
    lines = ["N 7", _read(170, 1_700_000, full=True), _read(10, 1_900_000)]
    out = [_chunks(line) for line in _call(harness, lines)[1:]]
    assert out[0][0]["first"] == 7
    # No reliable read yet: last_sent + 1, still bit 5.
    assert (out[1][0]["first"], out[1][0]["status"]) == (7 + 170, BIT4 | BIT5)


def imu_value(index, slot):
    # firmware/drivers/fake_afe.c, IMU channels.
    return (index * 257 + slot * 8191) % 65536 - 32768


def fake_imu_reads(duration_us, stalls, seed=5, period=10_000, batch=10, depth=170):
    """Reads of the firmware fake BMI270: ``(true_first, count, anchor, full,
    lost)``. Frame k exists from (k + 1) * period; the reader wakes when
    ``batch`` frames wait, 20-400 us late, plus a stall from ``stalls``
    ({start_us: length_us}) the first time it wakes after the start."""
    rng, stalls = random.Random(seed), dict(stalls)
    reads, fifo_first = [], 0
    while True:
        t = (fifo_first + batch) * period + rng.randint(20, 400)
        for start in sorted(stalls):
            if t >= start:
                t += stalls.pop(start)
                break
        if t > duration_us:
            return reads
        available = t // period - fifo_first
        count = min(available, depth)
        reads.append((fifo_first, count, t, count == depth, available - count))
        fifo_first += available


def test_fake_imu_timeline_through_planner_and_logger(harness):
    stalls = {10_000_000: 500_000, 20_000_000: 2_500_000}
    reads = fake_imu_reads(40_000_000, stalls)
    out = _call(harness, ["N 0", *(_read(count, anchor, full)
                                   for _, count, anchor, full, _ in reads)])[1:]
    backlog = [r for r in reads if 32 < r[1] < 170]
    fulls = [i for i, r in enumerate(reads) if r[3]]
    assert len(backlog) == 1 and len(fulls) == 1 and reads[fulls[0]][4] > 0
    packets, seq = [], {channel: 0 for channel in IMU}
    for (true_first, count, anchor, full, _), line in zip(reads, out):
        chunks = _chunks(line)
        # The section 5 formula finds the true index after the lost frames.
        assert chunks[0]["first"] == true_first
        for c in chunks:
            for slot, channel in enumerate(IMU):
                data = tuple(imu_value(true_first + c["offset"] + i, slot)
                             for i in range(c["count"]))
                packets.append(Packet(2, channel, 1, seq[channel], c["first"], anchor,
                                      c["t_first"], FS, c["status"], data))
                seq[channel] += 1
    stream = b"".join(encode_packet(p) for p in packets)
    decoded, decoder = decode_bytes(stream, 4096, (1, 2))
    result, _, samples = analyze_stream(decoded, decoder, LOGGER, _metadata())
    # One re-anchor per axis after the full read; nothing else.
    assert result["issue_counts"] == {"sample_index_reanchored": 6}
    for key in ("0xA1", "0xA6"):
        channel = result["sessions"][0]["channels"][key]
        assert channel["chains"] == 2
        # The backlog chunk with bit 7 and the full packets with bit 0.
        assert channel["packets_anchor_unreliable"] == 1 + 6
        assert [g["lost_samples"] for g in channel["gaps"]] == [None]
    for _, key, _, _, index, value, _ in samples:
        assert value == imu_value(index, IMU.index(int(key, 16)))


LOGGER = json.loads((ROOT / "configs/hardware/packet_logger.json").read_bytes())


def _metadata():
    channels, reasons = {}, {}
    for channel in IMU:
        key = f"0x{channel:02X}"
        channels[key] = {"sensor": "SYN_fake_imu", "fs_nominal_mhz": FS,
                         "latency_l_us": None, "latency_source": None,
                         "unit_conversion": None, "afe_config": None}
        for name in ("latency_l_us", "latency_source", "unit_conversion",
                     "afe_config"):
            reasons[f"channels.{key}.{name}"] = "SYNTHETIC firmware emulation"
    text = ("firmware_version", "firmware_commit", "device_id", "operator",
            "electrode_type", "electrode_placement")
    reasons.update({name: "SYNTHETIC firmware emulation" for name in text})
    return {"schema_version": "packet-session-metadata-v0", "source_type": "SYNTHETIC",
            "clock_id": "ESP32_ESP_TIMER_US", **dict.fromkeys(text),
            "channels": channels, "simulation": None, "null_reasons": reasons}
