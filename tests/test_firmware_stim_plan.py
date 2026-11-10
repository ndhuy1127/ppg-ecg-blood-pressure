"""Compile the sync stimulus schedule (firmware/app/stim_plan.c); run it on the host.

Answers come from hardware/test_reports/sync_10min_test_plan.md sections 3-4: a
rising edge every 1 s plus a uniform offset in [0, 1953) us, seeded with the
SESSION_ID, so that 600 edges (10 minutes) cover one ECG sample period
(1953.125 us at 512 sps) evenly. Section 5 (2026-11-11): because the offsets add
up from edge to edge, the same 600 edges also cover the PPG sample period
(5000 us at 200 sps per slot), even with the PPG rate off by 3 %. The expected
numbers come from an independent Python xorshift32. SYNTHETIC only. Without a
host C compiler the test is skipped.
"""

import os
import subprocess
from pathlib import Path

import pytest

from tests.test_firmware_c_encoder import _compiler

ROOT = Path(__file__).resolve().parents[1]
ECG_PERIOD_US = 10 ** 9 / 512_000  # 1953.125
PPG_PERIOD_US = 10 ** 6 / 200  # 5000, one slot at 200 sps

HARNESS = r"""
#include <stdio.h>

#include "stim_plan.h"

int main(void)
{
    unsigned long seed, n;
    while (scanf("%lu %lu", &seed, &n) == 2) {
        stim_plan_t s;
        stim_plan_init(&s, (uint32_t)seed);
        for (unsigned long i = 0; i < n; i++) {
            printf("%s%lu", i ? " " : "", (unsigned long)stim_next_interval_us(&s));
        }
        printf("\n");
        fflush(stdout);
    }
    return 0;
}
"""


def xorshift_intervals(seed, n):
    x = seed or 0x9E3779B9
    out = []
    for _ in range(n):
        x ^= (x << 13) & 0xFFFFFFFF
        x ^= x >> 17
        x ^= (x << 5) & 0xFFFFFFFF
        out.append(1_000_000 + x % 1953)
    return out


@pytest.fixture(scope="module")
def run(tmp_path_factory):
    compiler = _compiler()
    if compiler is None:
        pytest.skip("no host C compiler ($CC, cc, gcc or clang)")
    work = tmp_path_factory.mktemp("stim")
    (work / "harness.c").write_text(HARNESS, encoding="utf-8")
    exe = work / ("harness.exe" if os.name == "nt" else "harness")
    build = subprocess.run(
        [*compiler, "-std=c99", "-Wall", "-Wextra", "-Werror", "-Wno-unused-result",
         "-I", str(ROOT / "firmware/include"), str(ROOT / "firmware/app/stim_plan.c"),
         str(work / "harness.c"), "-o", str(exe)],
        capture_output=True, text=True,
    )
    assert build.returncode == 0, build.stderr

    def intervals(seed, n):
        out = subprocess.run([str(exe)], input=f"{seed} {n}\n", capture_output=True,
                             text=True, check=True).stdout
        return [int(v) for v in out.split()]

    return intervals


@pytest.mark.parametrize("seed", [1, 0x5EED1234, 0xFFFFFFFF, 0])
def test_intervals_follow_xorshift32_and_stay_in_one_ecg_period(run, seed):
    got = run(seed, 600)
    assert got == xorshift_intervals(seed, 600)
    assert all(1_000_000 <= v < 1_001_953 for v in got)
    assert run(seed, 600) == got  # the SESSION_ID regenerates the sequence


def test_known_answer_for_seed_one():
    # x = 1: x ^= x << 13 -> 8193; x ^= x >> 17 -> 8193; x ^= x << 5 -> 270369;
    # 270369 mod 1953 = 855.
    assert xorshift_intervals(1, 1) == [1_000_855]


@pytest.mark.parametrize("seed", [0x5EED1234, 0x0BADF00D, 7])
def test_ten_minutes_of_edges_cover_the_ecg_sample_phase(run, seed):
    # Section 4: the edge phase against the ECG sample grid must cover one sample
    # period evenly; 16 bins of 600 edges hold 37.5 each on average.
    t, phases = 0, []
    for v in run(seed, 600):
        t += v
        phases.append((t % ECG_PERIOD_US) / ECG_PERIOD_US)
    bins = [0] * 16
    for p in phases:
        bins[int(p * 16)] += 1
    assert min(bins) >= 15 and max(bins) <= 65, bins


@pytest.mark.parametrize("seed", [0x5EED1234, 0x0BADF00D, 7])
@pytest.mark.parametrize("rate_error", [0.0, 0.03, -0.03])
def test_ten_minutes_of_edges_cover_the_ppg_sample_phase(run, seed, rate_error):
    # Section 5 and criterion A9 (section 9): every one of 10 phase bins of the PPG
    # sample period holds at least 5 % of the edges (30 of 600; 60 on average).
    # Each offset is shorter than 5000 us, but the edge times are cumulative, so
    # the phase walks around the PPG period many times. The PPG rate may differ
    # from nominal by up to 3 % (interface_power_sampling_v0.md section 6).
    period = PPG_PERIOD_US * (1 + rate_error)
    t, bins = 0, [0] * 10
    for v in run(seed, 600):
        t += v
        bins[int((t % period) / period * 10)] += 1
    assert min(bins) >= 30, bins
