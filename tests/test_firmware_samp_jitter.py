"""Compile the SAMP interval statistics (firmware/include/samp_jitter.h) on the host.

Bench check of the MAX30001 sample clock (bring-up report 9.9): each interval
between captured SAMP edges against the nominal period (80 MHz capture ticks,
156 250 per 1/512 s), plus sums of the last 16 and 256 intervals. Expected
values are worked out by hand from the edge times fed in. SYNTHETIC only.
Without a host C compiler the test is skipped.
"""

import os
import subprocess
from pathlib import Path

import pytest

from tests.test_firmware_c_encoder import _compiler

ROOT = Path(__file__).resolve().parents[1]
NOMINAL, HZ = 156_250, 80_000_000

HARNESS = r"""
#include <inttypes.h>
#include <stdio.h>

#include "samp_jitter.h"

static samp_jitter_t j;

/* E t: edge;  B: break;  S: print the statistics */
int main(void)
{
    samp_jitter_init(&j, 156250u, 80000000u);
    char op;
    while (scanf(" %c", &op) == 1) {
        if (op == 'E') {
            unsigned long t;
            if (scanf("%lu", &t) != 1) {
                return 2;
            }
            samp_jitter_add(&j, (uint32_t)t);
        } else if (op == 'B') {
            samp_jitter_break(&j);
        } else if (op == 'S') {
            const samp_jitter_stats_t *s = &j.stats;
            printf("%u %u %d %d %lld %llu", s->n, s->gaps, s->min_dev, s->max_dev,
                   (long long)s->sum_dev, (unsigned long long)s->sum_sq);
            for (int i = 0; i < SAMP_JITTER_BINS; i++) {
                printf(" %u", s->bins[i]);
            }
            for (int i = 0; i < 2; i++) {
                printf(" %u %d %d", s->span_n[i], s->span_min[i], s->span_max[i]);
            }
            printf("\n");
            fflush(stdout);
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
    work = tmp_path_factory.mktemp("samp_jitter")
    (work / "harness.c").write_text(HARNESS, encoding="utf-8")
    exe = work / ("harness.exe" if os.name == "nt" else "harness")
    build = subprocess.run(
        [*compiler, "-std=c99", "-Wall", "-Wextra", "-Werror", "-Wno-unused-result",
         "-I", str(ROOT / "firmware/include"), str(work / "harness.c"), "-o", str(exe)],
        capture_output=True, text=True,
    )
    assert build.returncode == 0, build.stderr
    return exe


def stats(exe, ops):
    """Feed edge times (ints) and 'B' breaks; return the statistics."""
    text = "".join("B\n" if op == "B" else f"E {op % 2**32}\n" for op in ops) + "S\n"
    out = subprocess.run([str(exe)], input=text, capture_output=True, text=True, check=True)
    v = list(map(int, out.stdout.split()))
    return {"n": v[0], "gaps": v[1], "min": v[2], "max": v[3], "sum": v[4], "sq": v[5],
            "bins": v[6:13], "span16": tuple(v[13:16]), "span256": tuple(v[16:19])}


def edges(count, start=1000, devs=None):
    t, out = start, [start]
    for i in range(count - 1):
        t += NOMINAL + (devs(i) if devs else 0)
        out.append(t)
    return out


def test_bin_limits_follow_the_capture_resolution():
    # 0.125, 0.5, 1, 5, 20, 100 us at 80 MHz.
    assert [round(ns * HZ / 1e9) for ns in (125, 500, 1000, 5000, 20000, 100000)] == \
        [10, 40, 80, 400, 1600, 8000]


def test_nominal_edges_give_zero_deviation_and_span_counts(harness):
    s = stats(harness, edges(301))
    assert (s["n"], s["gaps"], s["min"], s["max"], s["sum"], s["sq"]) == (300, 0, 0, 0, 0, 0)
    assert s["bins"] == [300, 0, 0, 0, 0, 0, 0]
    # Sums exist from the 16th and the 256th interval of a series on.
    assert s["span16"] == (300 - 15, 0, 0) and s["span256"] == (300 - 255, 0, 0)


def test_one_late_edge_shows_as_plus_and_minus_and_cancels_in_the_spans(harness):
    times = edges(301)
    times[100] += 800  # 10 us late: interval 99 is +800 ticks, interval 100 is -800
    s = stats(harness, times)
    assert (s["min"], s["max"], s["sum"], s["sq"]) == (-800, 800, 0, 2 * 800**2)
    assert s["bins"] == [298, 0, 0, 0, 2, 0, 0]  # 10 us is in the <= 20 us bin
    # A 16-interval sum holding only one half: windows ending at 99 (+800) or
    # starting at 100 (-800); windows holding both sum to 0.
    assert s["span16"][1:] == (-800, 800)
    assert s["span256"][1:] == (0, 0)


def test_slow_phase_excursion_shows_in_the_spans_not_in_one_interval(harness):
    # +40 ticks (0.5 us) per interval for 64 intervals, then -40 for 64.
    def dev(i):
        return 40 if 100 <= i < 164 else -40 if 164 <= i < 228 else 0
    s = stats(harness, edges(400, devs=dev))
    assert (s["min"], s["max"]) == (-40, 40) and s["bins"][1] == 128
    assert s["span16"][1:] == (-640, 640)  # 16 x 40
    # The excursion returns to phase within 256 intervals: windows that hold all
    # of it sum to 0, windows that hold only part of it do not.
    assert s["span256"][0] == 399 - 255 and s["span256"][2] <= 64 * 40


def test_missed_edge_is_a_gap_and_starts_a_new_series(harness):
    times = edges(100)
    del times[50]  # one edge lost: an interval of two periods
    s = stats(harness, times)
    assert (s["n"], s["gaps"], s["min"], s["max"]) == (98 - 1, 1, 0, 0)
    # Each series of 49 and 48 intervals gives sums from its 16th on.
    assert s["span16"][0] == (49 - 15) + (48 - 15)


def test_break_drops_the_interval_across_a_restart(harness):
    first = edges(20)
    second = edges(20, start=first[-1] + 37_000)  # SYNCH: a new phase
    s = stats(harness, [*first, "B", *second])
    assert (s["n"], s["gaps"], s["max"], s["min"]) == (38, 0, 0, 0)


def test_counter_wrap_is_harmless(harness):
    s = stats(harness, edges(40, start=2**32 - 5 * NOMINAL))
    assert (s["n"], s["gaps"], s["min"], s["max"]) == (39, 0, 0, 0)


def test_half_a_period_off_is_counted_and_more_is_a_gap(harness):
    # Half a period off is still counted, more is a gap.
    times = [0, NOMINAL + NOMINAL // 2, 2 * NOMINAL + NOMINAL // 2 + NOMINAL // 2 + 1]
    s = stats(harness, times)
    assert (s["n"], s["gaps"], s["max"]) == (1, 1, NOMINAL // 2)
