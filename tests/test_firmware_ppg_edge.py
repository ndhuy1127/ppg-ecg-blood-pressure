"""Compile the PPG_RDY edge anchoring (firmware/include/ppg_edge.h) on the host.

Bench diagnostic of the MAX30101 sample clock (bring-up report 12.7): the ISR
stores the time of each PPG_RDY edge; for each FIFO read the newest edge before
the pointer read anchors the packet when the edges counted since the previous
read equal the samples read, and no edge fell during the pointer read. Expected
values are worked out by hand from the edge times fed in. SYNTHETIC only.
Without a host C compiler the test is skipped.
"""

import os
import subprocess
from pathlib import Path

import pytest

from tests.test_firmware_c_encoder import _compiler

ROOT = Path(__file__).resolve().parents[1]

HARNESS = r"""
#include <inttypes.h>
#include <stdio.h>

#include "ppg_edge.h"

static ppg_edge_ring_t ring;
static ppg_edge_t e;

/* E t: edge;  R n t: read of n samples, pointer read from t - 60 to t;
 * A n p t: the same with the pointer read from p to t (both print the anchor
 * and 1 when it is an edge);  B: break;  Z: reset the statistics;
 * S: print the statistics */
int main(void)
{
    ppg_edge_init(&e);
    char op;
    while (scanf(" %c", &op) == 1) {
        unsigned long long t, pre;
        unsigned n;
        if (op == 'E') {
            if (scanf("%llu", &t) != 1) {
                return 2;
            }
            ppg_edge_push(&ring, t);
        } else if (op == 'R' || op == 'A') {
            if (op == 'R') {
                if (scanf("%u %llu", &n, &t) != 2) {
                    return 2;
                }
                pre = t - 60u;
            } else if (scanf("%u %llu %llu", &n, &pre, &t) != 3) {
                return 2;
            }
            bool from_edge;
            uint64_t a = ppg_edge_anchor(&e, &ring, (uint16_t)n, pre, t, &from_edge);
            printf("%llu %d\n", (unsigned long long)a, from_edge ? 1 : 0);
        } else if (op == 'B') {
            ppg_edge_break(&e);
        } else if (op == 'Z') {
            ppg_edge_stats_reset(&e);
        } else if (op == 'S') {
            const ppg_edge_stats_t *s = &e.stats;
            printf("%u %u %u %u %u %lld %lld %lld\n", s->reads, s->anchored, s->mismatch,
                   s->no_edge, s->ambiguous, (long long)s->lat_min_us,
                   (long long)s->lat_max_us, (long long)s->lat_sum_us);
        } else {
            return 2;
        }
        fflush(stdout);
    }
    return 0;
}
"""


@pytest.fixture(scope="module")
def harness(tmp_path_factory):
    compiler = _compiler()
    if compiler is None:
        pytest.skip("no host C compiler ($CC, cc, gcc or clang)")
    work = tmp_path_factory.mktemp("ppg_edge")
    (work / "harness.c").write_text(HARNESS, encoding="utf-8")
    exe = work / ("harness.exe" if os.name == "nt" else "harness")
    build = subprocess.run(
        [*compiler, "-std=c99", "-Wall", "-Wextra", "-Werror", "-Wno-unused-result",
         "-I", str(ROOT / "firmware/include"), str(work / "harness.c"), "-o", str(exe)],
        capture_output=True, text=True,
    )
    assert build.returncode == 0, build.stderr
    return exe


def run(exe, script):
    out = subprocess.run([str(exe)], input=script, capture_output=True, text=True,
                         check=True)
    return out.stdout.split("\n")[:-1]


def edges(start, n, period=5000):
    return "".join(f"E {start + i * period}\n" for i in range(n))


def test_first_read_keeps_read_time_then_edges_anchor(harness):
    # 8 edges, read 300 us after the 8th: no previous read, so the count is not
    # verified and the read time is kept; the next 8 are anchored on the edge.
    script = edges(1000, 8) + "R 8 36300\n" + edges(41000, 8) + "R 8 76250\nS\n"
    out = run(harness, script)
    assert out[0] == "36300 0"
    assert out[1] == "76000 1"  # 41000 + 7 * 5000
    assert out[2] == "2 1 0 0 0 250 250 250"


def test_edges_after_the_read_time_are_not_used(harness):
    # The ISR stored an edge (sample 17) after the read time while the ring was
    # copied: it belongs to the next read.
    script = edges(1000, 8) + "R 8 36100\n" + edges(41000, 9) + "R 8 76400\nS\n"
    out = run(harness, script)
    assert out[1] == "76000 1"
    assert out[2] == "2 1 0 0 0 400 400 400"


def test_edge_during_the_pointer_read_is_ambiguous(harness):
    # The 9th sample's edge (81000) falls between the times taken before and
    # after the pointer read: the pointers may or may not include that sample.
    script = (edges(1000, 8) + "R 8 36100\n" + edges(41000, 9) + "A 8 80900 81100\n"
              + edges(86000, 7) + "R 8 116200\n" + edges(121000, 8) + "R 8 156300\nS\n")
    out = run(harness, script)
    assert out[1] == "81100 0"
    assert out[2] == "116200 0"  # count restarted: not verified
    assert out[3] == "156000 1"
    assert out[4] == "4 1 0 0 1 300 300 300"


def test_lost_edge_is_a_mismatch_and_keeps_read_time(harness):
    # 7 edges for 8 samples (one edge lost while the flag was still set).
    script = edges(1000, 8) + "R 8 36100\n" + edges(41000, 7) + "R 8 76300\nS\n"
    out = run(harness, script)
    assert out[1] == "76300 0"
    assert out[2] == "2 0 1 0 0 0 0 0"
    # The count restarts from this read: the next 8 edges anchor again.
    out = run(harness, script + edges(81000, 8) + "R 8 116200\nS\n")
    assert out[3] == "116000 1"
    assert out[4] == "3 1 1 0 0 200 200 200"


def test_late_read_of_more_samples_matches(harness):
    script = edges(1000, 8) + "R 8 36100\n" + edges(41000, 10) + "R 10 86900\nS\n"
    out = run(harness, script)
    assert out[1] == "86000 1"  # 41000 + 9 * 5000
    assert out[2] == "2 1 0 0 0 900 900 900"


def test_break_skips_the_count_check_once(harness):
    script = (edges(1000, 8) + "R 8 36100\nB\n" + edges(41000, 3) + edges(60000, 8)
              + "R 8 95500\n" + edges(100000, 8) + "R 8 135300\nS\n")
    out = run(harness, script)
    assert out[1] == "95500 0"  # after a break: read time, no mismatch counted
    assert out[2] == "135000 1"
    assert out[3] == "3 1 0 0 0 300 300 300"


def test_no_edge_and_zero_samples(harness):
    out = run(harness, "R 0 100\nR 8 5000\nS\n")
    assert out[:2] == ["100 0", "5000 0"]
    assert out[2] == "1 0 0 1 0 0 0 0"


def test_statistics_over_reads_and_reset(harness):
    script = edges(1000, 8) + "R 8 36100\n"
    t = 41000
    for lat in (100, 700, 400):
        script += edges(t, 8) + f"R 8 {t + 35000 + lat}\n"
        t += 40000
    out = run(harness, script + "S\nZ\nS\n")
    assert out[4] == "4 3 0 0 0 100 700 1200"
    assert out[5] == "0 0 0 0 0 0 0 0"


def test_ring_wrap_keeps_the_newest_edges(harness):
    # 200 edges without a read (more than the 64-entry ring), then reads resume.
    script = edges(1000, 200) + "R 8 996100\n" + edges(1001000, 8) + "R 8 1036300\nS\n"
    out = run(harness, script)
    assert out[0] == "996100 0"  # first read after start: read time
    assert out[1] == "1036000 1"
    assert out[2] == "2 1 0 0 0 300 300 300"
