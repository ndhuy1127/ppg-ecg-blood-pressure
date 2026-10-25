"""Compile the 0xD2 send rules (firmware/app/afe_order.c); run them on the host.

Answers come from Packet Schema V0.2 section 12 (fixed 2026-10-25): per AFE,
never a state older than the newest one sent, the same state again only as the
periodic repeat or to carry STATUS bit 1, a repeat waits while the latest state
is still in the AFE queue, and a lost transition stays latched until a 0xD2
carries bit 1. The scenarios follow the control task (firmware/app/main.c,
ctl_task): lost transitions are noted, then the AFE queue is drained, then the
latest state goes out for an AFE whose loss nothing carried, then the repeat.
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

#include "afe_order.h"

int main(void)
{
    afe_order_t o;
    afe_order_init(&o);
    char op;
    while (scanf(" %c", &op) == 1) {
        unsigned afe, repeat, queued;
        unsigned long long order;
        if (op == 'L' && scanf("%u %llu", &afe, &order) == 2) {
            afe_order_lost(&o, (uint8_t)afe, order);
        } else if (op == 'P' && scanf("%u", &afe) == 1) {
            printf("%d\n", afe_order_pending(&o, (uint8_t)afe));
        } else if (op == 'D' && scanf("%u %llu %u %u", &afe, &order, &repeat, &queued) == 4) {
            bool bit1;
            if (afe_order_decide(&o, (uint8_t)afe, order, repeat != 0, &bit1)) {
                afe_order_sent(&o, (uint8_t)afe, order, queued != 0);
                printf("send %d\n", bit1);
            } else {
                printf("skip\n");
            }
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
    work = tmp_path_factory.mktemp("afe_order")
    (work / "harness.c").write_text(HARNESS, encoding="utf-8")
    exe = work / ("harness.exe" if os.name == "nt" else "harness")
    build = subprocess.run(
        [*compiler, "-std=c99", "-Wall", "-Wextra", "-Werror", "-Wno-unused-result",
         "-I", str(ROOT / "firmware/include"), str(ROOT / "firmware/app/afe_order.c"),
         str(work / "harness.c"), "-o", str(exe)],
        capture_output=True, text=True,
    )
    assert build.returncode == 0, build.stderr

    def steps(*lines):
        out = subprocess.run([str(exe)], input="\n".join(lines) + "\n",
                             capture_output=True, text=True, check=True).stdout
        return out.split("\n")[:-1]

    return steps


def queue(afe, order, queued=1):
    return f"D {afe} {order} 0 {queued}"


# ctl_send_latest for a lost transition: the same call as a state from the queue.
latest = queue


def repeat(afe, order, queued=1):
    return f"D {afe} {order} 1 {queued}"


def test_states_go_out_in_order_once_and_older_ones_are_dropped(run):
    assert run(queue(1, 1), queue(1, 2), queue(1, 2), queue(1, 1)) == [
        "send 0", "send 0", "skip", "skip"]


def test_a_repeat_waits_while_the_latest_state_is_still_queued(run):
    # State 2 is in the table but not yet drained: the repeat skips it; once it
    # went out, every repeat sends it again without bit 1.
    assert run(queue(1, 1), repeat(1, 2), queue(1, 2), repeat(1, 2), repeat(1, 2)) == [
        "send 0", "skip", "send 0", "send 0", "send 0"]


def test_a_lost_transition_sent_from_the_table_keeps_the_repeats(run):
    # Codex round 2, finding 1: 9 never reached the queue and went out from the
    # table; the repeats must not stop until a new transition.
    lines = [queue(1, k) for k in range(1, 9)]
    out = run(*lines, "L 1 9", latest(1, 9), repeat(1, 9), repeat(1, 9), "P 1")
    assert out == ["send 0"] * 8 + ["send 1", "send 0", "send 0", "0"]


def test_a_loss_noted_after_a_newer_state_went_out_is_still_carried(run):
    # Finding 2: 9 lost, 10 queued and drained before the control task saw the
    # loss. 10 goes out again with bit 1; then repeats without it.
    out = run(queue(1, 8), queue(1, 10), "L 1 9", "P 1", latest(1, 10), "P 1",
              repeat(1, 10))
    assert out == ["send 0", "send 0", "1", "send 1", "0", "send 0"]


def test_a_loss_seen_before_the_drain_flags_the_first_newer_state(run):
    # 9 lost; the queue still holds 8 (older: no bit 1) and 10 (bit 1). Nothing
    # is left to send from the table. The control task notes every AFE each
    # round (0: none); an older or empty note keeps the loss at 9.
    out = run("L 1 9", "L 1 5", "L 1 0", queue(1, 8), "P 1", queue(1, 10), "P 1",
              queue(1, 11))
    assert out == ["send 0", "1", "send 1", "0", "send 0"]


def test_a_state_sent_from_the_table_is_not_sent_again_from_the_queue(run):
    out = run(queue(1, 8), "L 1 9", latest(1, 10), queue(1, 10), repeat(1, 10))
    assert out == ["send 0", "send 1", "skip", "send 0"]


def test_a_0xd2_dropped_before_a_seq_sets_bit_1_on_the_next_one(run):
    assert run(queue(1, 5, queued=0), queue(1, 6), queue(1, 7)) == [
        "send 0", "send 1", "send 0"]
    # With no newer state, the repeat sends the dropped one again, with bit 1.
    assert run(queue(1, 5, queued=0), repeat(1, 5), repeat(1, 5)) == [
        "send 0", "send 1", "send 0"]


def test_a_flagged_0xd2_that_is_dropped_passes_bit_1_on(run):
    out = run("L 1 9", latest(1, 9, queued=0), "P 1", queue(1, 10), queue(1, 11))
    assert out == ["send 1", "0", "send 1", "send 0"]


def test_each_afe_has_its_own_order_and_losses(run):
    out = run(queue(1, 3), "L 2 1", queue(1, 4), queue(3, 1), queue(2, 1),
              queue(2, 1), "P 2", queue(3, 1))
    assert out == ["send 0", "send 0", "send 0", "send 1", "skip", "0", "skip"]


def test_orders_past_32_bits_do_not_wrap(run):
    # Finding 5: a 32-bit order would wrap to 0 and reject every later state.
    big = 2 ** 32
    out = run(queue(1, big - 1), queue(1, big), queue(1, big - 1), repeat(1, big),
              "L 1 " + str(big + 1), latest(1, big + 1), queue(1, 2 ** 64 - 1))
    assert out == ["send 0", "send 0", "skip", "send 0", "send 1", "send 0"]
