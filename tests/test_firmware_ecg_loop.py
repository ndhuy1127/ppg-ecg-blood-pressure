"""Compile the MAX30001 reader-loop timing (firmware/app/ecg_loop.c); run it on the host.

Answers come from the rule in firmware/README.md (ECG health, 2026-10-25): check
the chip every 1 s and as soon as no sample came for 2 s; once down, try a start
every 100 ms until it works; while up, read the FIFO on an INTB edge, while INTB
is low, after 40 ms without a sample (the FIFO holds 62.5 ms at 512 sps), and
right before a SYNCH, so the samples still in the FIFO are sent first.
SYNTHETIC only. Without a host C compiler the test is skipped.
"""

import os
import subprocess
from pathlib import Path

import pytest

from tests.test_firmware_c_encoder import _compiler

ROOT = Path(__file__).resolve().parents[1]

HARNESS = r"""
#include <stdio.h>

#include "ecg_loop.h"

/* One command per line, the time in us first:
 *   I t          init (chip started at t)
 *   S t          start due? (prints 0/1)  U t   start worked
 *   C t          check due? (prints due dead)  D t   down
 *   R t w l s    read due? woke, INTB low, SYNCH due (prints 0/1)
 *   P t          packet sent from a read at t */
int main(void)
{
    ecg_loop_t l;
    char op;
    long long t;
    while (scanf(" %c %lld", &op, &t) == 2) {
        unsigned w, lo, s;
        bool dead;
        if (op == 'I') {
            ecg_loop_init(&l, t);
        } else if (op == 'S') {
            printf("%d\n", ecg_loop_start_due(&l, t));
        } else if (op == 'U') {
            ecg_loop_up(&l, t);
        } else if (op == 'C') {
            int due = ecg_loop_check_due(&l, t, &dead);
            printf("%d %d\n", due, dead);
        } else if (op == 'D') {
            ecg_loop_down(&l, t);
        } else if (op == 'R' && scanf("%u %u %u", &w, &lo, &s) == 3) {
            printf("%d\n", ecg_loop_read_due(&l, t, w != 0, lo != 0, s != 0));
        } else if (op == 'P') {
            ecg_loop_samples(&l, t);
        } else {
            return 2;
        }
    }
    return 0;
}
"""


@pytest.fixture(scope="module")
def run(tmp_path_factory):
    compiler = _compiler()
    if compiler is None:
        pytest.skip("no host C compiler ($CC, cc, gcc or clang)")
    work = tmp_path_factory.mktemp("ecg_loop")
    (work / "harness.c").write_text(HARNESS, encoding="utf-8")
    exe = work / ("harness.exe" if os.name == "nt" else "harness")
    build = subprocess.run(
        [*compiler, "-std=c99", "-Wall", "-Wextra", "-Werror", "-Wno-unused-result",
         "-I", str(ROOT / "firmware/include"), str(ROOT / "firmware/app/ecg_loop.c"),
         str(work / "harness.c"), "-o", str(exe)],
        capture_output=True, text=True,
    )
    assert build.returncode == 0, build.stderr

    def steps(*lines):
        out = subprocess.run([str(exe)], input="\n".join(lines) + "\n",
                             capture_output=True, text=True, check=True).stdout
        return out.split("\n")[:-1]

    return steps


def test_the_fifo_is_read_on_an_edge_a_low_intb_a_stall_or_before_a_synch(run):
    assert run("I 0", "P 1000",
               "R 20000 0 0 0", "R 20000 1 0 0", "R 20000 0 1 0", "R 20000 0 0 1",
               "R 41000 0 0 0", "R 41001 0 0 0") == ["0", "1", "1", "1", "0", "1"]


def test_the_chip_is_checked_every_second_and_when_silent_for_two(run):
    out = run("I 0", "C 999999", "C 1000000", "C 1500000", "P 1900000",
              "C 2000000", "C 2999999", "C 3000000", "C 3900001")
    # Checks at 1 s and 2 s (every second); a packet at 1.9 s keeps it alive;
    # at 3.9 s plus 1 us no sample came for over 2 s: dead, checked at once.
    assert out == ["0 0", "1 0", "0 0", "1 0", "0 0", "1 0", "1 1"]


def test_a_down_chip_is_started_every_100_ms_until_it_works(run):
    out = run("I 0", "D 5000000", "C 5000001", "R 5000001 1 1 1",
              "S 5000000", "S 5050000", "S 5100000", "S 5150000", "S 5200000",
              "U 5210000", "S 5300000", "C 6209999", "C 6210000",
              "R 5230000 0 0 0", "R 5250001 0 0 0")
    # Down: no check and no read; starts at 5.0, 5.1, 5.2 s; once up, no more
    # starts, the clocks start over from the start time.
    assert out == ["0 0", "0", "1", "0", "1", "0", "1", "0", "0 0", "1 0", "0", "1"]


def test_a_check_after_a_start_waits_a_full_second(run):
    # The start itself counts as a sample time: no instant "silent" after it.
    out = run("I 0", "D 9000000", "S 9000000", "U 9100000", "C 9100001",
              "C 10099999", "C 10100000")
    assert out == ["1", "0 0", "0 0", "1 0"]
