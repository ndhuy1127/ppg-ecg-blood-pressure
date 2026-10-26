"""Compile the die temperature state machine (firmware/app/die_temp.c); run it on the host.

Answers come from Packet Schema V0.2 section 11.1: tick k at t0 + k s, index = k,
a start within 50 ms of the tick (a later tick gets no value, no error bit), no
overlapping conversions, a readout by tick + 100 ms (a later one is dropped),
bit 3 after a failed start or read, a missed deadline or a chip reset, never
bit 4 or 5. SYNTHETIC only. Without a host C compiler the test is
skipped.
"""

import os
import subprocess
from pathlib import Path

import pytest

from tests.test_firmware_c_encoder import _compiler

ROOT = Path(__file__).resolve().parents[1]
WAIT, START, POLL = "WAIT", "START", "POLL"
OK, BUSY, ERROR = range(3)
BIT3 = 1 << 3
T0 = 5_000_000
S = 1_000_000

HARNESS = r"""
#include <stdio.h>

#include "die_temp.h"

int main(void)
{
    static const char *const NAMES[] = {"WAIT", "START", "POLL"};
    die_temp_t t;
    die_temp_init(&t, 0);
    char cmd[2];
    while (scanf("%1s", cmd) == 1) {
        long long a = 0, b = 0;
        if (cmd[0] == 'I') {
            scanf("%lld", &a);
            die_temp_init(&t, a);
            printf("ok\n");
        } else if (cmd[0] == 'N') {
            scanf("%lld", &a);
            die_temp_action_t act = die_temp_next(&t, a);
            printf("%s %lu\n", NAMES[act], (unsigned long)t.tick);
        } else if (cmd[0] == 'S') {
            scanf("%lld", &a);
            die_temp_started(&t, a != 0);
            printf("ok\n");
        } else if (cmd[0] == 'P') {
            scanf("%lld %lld", &a, &b);
            die_temp_packet_t p = die_temp_polled(&t, (die_temp_read_t)a, b);
            printf("%d %lu %u\n", p.send, (unsigned long)p.index, p.status);
        } else if (cmd[0] == 'A') {
            die_temp_abort(&t);
            printf("ok\n");
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
    work = tmp_path_factory.mktemp("die_temp")
    (work / "harness.c").write_text(HARNESS, encoding="utf-8")
    exe = work / ("harness.exe" if os.name == "nt" else "harness")
    build = subprocess.run(
        [*compiler, "-std=c99", "-Wall", "-Wextra", "-Werror", "-Wno-unused-result",
         "-I", str(ROOT / "firmware/include"), str(ROOT / "firmware/app/die_temp.c"),
         str(work / "harness.c"), "-o", str(exe)],
        capture_output=True, text=True,
    )
    assert build.returncode == 0, build.stderr
    return exe


class Temp:
    def __init__(self, exe):
        self.proc = subprocess.Popen([str(exe)], stdin=subprocess.PIPE,
                                     stdout=subprocess.PIPE, text=True)
        self(f"I {T0}")

    def __call__(self, line):
        self.proc.stdin.write(line + "\n")
        self.proc.stdin.flush()
        return self.proc.stdout.readline().strip()

    def next(self, now):
        action, tick = self(f"N {now}").split()
        return action, int(tick)

    def started(self, ok=True):
        self(f"S {int(ok)}")

    def polled(self, result, now):
        send, index, status = map(int, self(f"P {result} {now}").split())
        return (index, status) if send else None

    def read(self, start, done):
        """A whole reading started at ``start`` and read out at ``done``."""
        tick = (start - T0) // S
        assert self.next(start) == (START, tick)
        self.started()
        assert self.next(done) == (POLL, tick)
        return self.polled(OK, done)

    def close(self):
        self.proc.stdin.close()
        assert self.proc.wait(timeout=30) == 0


@pytest.fixture
def temp(harness):
    t = Temp(harness)
    yield t
    t.close()


def test_one_reading_per_tick_on_the_esp_timer_grid(temp):
    assert temp.next(T0 - 1)[0] == WAIT
    assert temp.next(T0) == (START, 0)
    temp.started()
    assert temp.next(T0 + 10_000) == (POLL, 0)
    assert temp.polled(BUSY, T0 + 10_100) is None
    assert temp.next(T0 + 30_000) == (POLL, 0)
    assert temp.polled(OK, T0 + 30_100) == (0, 0)
    assert temp.next(T0 + 40_000)[0] == WAIT
    assert temp.next(T0 + S - 1)[0] == WAIT
    # Started 7 ms late: still tick 1, the grid does not drift with the delays.
    assert temp.read(T0 + S + 7_000, T0 + S + 40_000) == (1, 0)
    assert temp.read(T0 + 2 * S + 3_000, T0 + 2 * S + 35_000) == (2, 0)


@pytest.mark.parametrize("late,starts", [(50_000, True), (50_001, False)])
def test_a_tick_reached_too_late_gets_no_value_and_no_error(temp, late, starts):
    assert temp.read(T0, T0 + 30_000) == (0, 0)
    if starts:
        assert temp.read(T0 + S + late, T0 + S + late + 30_000) == (1, 0)
    else:
        assert temp.next(T0 + S + late)[0] == WAIT
        assert temp.next(T0 + S + 60_000)[0] == WAIT  # tick 1 is skipped for good
    assert temp.read(T0 + 2 * S, T0 + 2 * S + 30_000) == (2, 0)


def test_recovery_late_in_a_tick_waits_for_the_next_one(temp):
    assert temp.read(T0, T0 + 30_000) == (0, 0)
    # The task was 2.5 s late: ticks 1-3 get no value, no error bit.
    assert temp.next(T0 + 3 * S + 500_000)[0] == WAIT
    assert temp.read(T0 + 4 * S, T0 + 4 * S + 30_000) == (4, 0)


def test_no_second_conversion_while_one_runs(temp):
    assert temp.next(T0) == (START, 0)
    temp.started()
    for now in (T0 + 1, T0 + 50_000, T0 + 100_000):
        assert temp.next(now) == (POLL, 0)


@pytest.mark.parametrize("start", [0, 40_000])
def test_deadline_counts_from_the_tick_and_drops_the_reading(temp, start):
    assert temp.next(T0 + start) == (START, 0)
    temp.started()
    assert temp.next(T0 + 100_000) == (POLL, 0)  # at the deadline: still polled
    assert temp.next(T0 + 100_001)[0] == WAIT     # past it: given up
    assert temp.polled(OK, T0 + 100_002) is None  # a result now is not used
    assert temp.read(T0 + S, T0 + S + 30_000) == (1, BIT3)
    assert temp.read(T0 + 2 * S, T0 + 2 * S + 30_000) == (2, 0)


@pytest.mark.parametrize("readout,sent", [(100_000, True), (100_001, False)])
def test_a_readout_that_ends_past_the_deadline_is_dropped(temp, readout, sent):
    assert temp.next(T0) == (START, 0)
    temp.started()
    assert temp.next(T0 + 99_000) == (POLL, 0)
    # The I2C reads took the readout past tick + 100 ms.
    assert temp.polled(OK, T0 + readout) == ((0, 0) if sent else None)
    assert temp.read(T0 + S, T0 + S + 30_000) == (1, 0 if sent else BIT3)


def test_stall_inside_a_conversion_skips_to_a_tick_in_time(temp):
    assert temp.next(T0) == (START, 0)
    temp.started()
    # The task stalled 1.2 s inside the conversion: tick 0 is given up (bit 3),
    # tick 1 is 200 ms old (no value), tick 2 is measured.
    assert temp.next(T0 + S + 200_000)[0] == WAIT
    assert temp.read(T0 + 2 * S, T0 + 2 * S + 30_000) == (2, BIT3)


@pytest.mark.parametrize("fail", ["start", "read"])
def test_failed_start_or_read_sets_bit3_on_the_next_packet(temp, fail):
    assert temp.next(T0) == (START, 0)
    if fail == "start":
        temp.started(ok=False)
    else:
        temp.started()
        assert temp.next(T0 + 30_000) == (POLL, 0)
        assert temp.polled(ERROR, T0 + 30_100) is None
    assert temp.next(T0 + 40_000)[0] == WAIT  # no retry within the tick
    assert temp.read(T0 + S, T0 + S + 30_000) == (1, BIT3)
    assert temp.read(T0 + 2 * S, T0 + 2 * S + 30_000) == (2, 0)


def test_chip_reset_drops_the_running_conversion(temp):
    assert temp.read(T0, T0 + 30_000) == (0, 0)
    assert temp.next(T0 + S) == (START, 1)
    temp.started()
    temp("A")  # brownout: the chip is configured again
    # After RESET, TEMP_EN reads 0: polling now would take zeros as a result.
    assert temp.next(T0 + S + 30_000)[0] == WAIT
    assert temp.polled(OK, T0 + S + 30_100) is None
    assert temp.read(T0 + 2 * S, T0 + 2 * S + 30_000) == (2, BIT3)


def test_reset_while_idle_still_marks_the_next_packet(temp):
    assert temp.read(T0, T0 + 30_000) == (0, 0)
    temp("A")
    temp("A")  # called on every loop while the chip waits for reconfiguration
    assert temp.read(T0 + 4 * S, T0 + 4 * S + 30_000) == (4, BIT3)
