"""Compile the 0xD2 data builders and the command decisions; run them on the host.

The 0xD2 DATA built in C from each driver's V1 registers is checked with the
receiver's own section 12 validator (decode_afe_config), and its values against
the register values of the driver tests and Packet Schema V0.2 section 3. The
command decisions (firmware/app/cmd_exec.c) follow section 13: a retry with the
same bytes gets the remembered answer, a reused CMD_SEQ with other bytes is
refused, BUSY is not remembered, the target SESSION_ID and the LED limit are
checked first. MARK_EVENT (amendment 2026-10-29) takes one byte, only codes 2 and
4, whatever the PPG chip does, and a retry never marks a second event. SYNTHETIC
only. Without a host C compiler the test is skipped.
"""

import os
import struct
import subprocess
from pathlib import Path

import pytest

from software.data_io.packet_receiver import decode_afe_config, decode_command_ack
from software.data_io.packet_wire import Packet
from tests.test_firmware_c_encoder import _compiler

ROOT = Path(__file__).resolve().parents[1]
OK, UNKNOWN, BAD_LENGTH, NO_CHIP, BUSY, CHIP_ERROR, REUSED, WRONG_SESSION, RANGE = \
    range(9)
NONE, PPG_BUSY, READY = range(3)

HARNESS = r"""
#include <stdio.h>
#include <string.h>

#include "bmi270.h"
#include "cmd_exec.h"
#include "max30001.h"
#include "max30101.h"
#include "packet_wire.h"

static void print_data(const int32_t *d, unsigned n)
{
    for (unsigned i = 0; i < n; i++) {
        printf("%s%ld", i ? " " : "", (long)d[i]);
    }
    printf("\n");
}

int main(void)
{
    cmd_exec_t e;
    cmd_exec_init(&e);
    char cmd[2];
    while (scanf("%1s", cmd) == 1) {
        if (cmd[0] == 'W') { /* 0xD2 DATA: afe source configured generation */
            unsigned afe, source, configured, gen;
            scanf("%u %u %u %u", &afe, &source, &configured, &gen);
            uint32_t words[32];
            unsigned n = 0;
            if (afe == 1) {
                max30001_regs_t r;
                max30001_v1_regs(&r);
                n = max30001_config_words(&r, words);
            } else if (afe == 2) {
                max30101_regs_t r;
                max30101_v1_regs(&r, 411);
                n = max30101_config_words(&r, words);
            } else {
                bmi270_regs_t r;
                bmi270_v1_regs(&r);
                n = bmi270_config_words(&r, words);
            }
            int32_t data[PKT_MAX_SAMPLES];
            uint16_t count = pkt_afe_config_data((uint8_t)afe, (uint8_t)source, configured != 0,
                                                 gen, words, (uint16_t)n, data);
            print_data(data, count);
        } else if (cmd[0] == 'A') { /* 0xD3 DATA */
            unsigned id, seq, result, gen;
            scanf("%u %u %u %u", &id, &seq, &result, &gen);
            int32_t data[PKT_COMMAND_ACK_COUNT];
            pkt_command_ack_data((uint8_t)id, (uint16_t)seq, (uint8_t)result, gen, data);
            print_data(data, PKT_COMMAND_ACK_COUNT);
        } else if (cmd[0] == 'X' || cmd[0] == 'D') {
            /* X session ppg id seq len params...;
             * D result gen ticket id seq len params... */
            unsigned long session = 0, ticket = 0;
            unsigned ppg = 0, result = 0, gen = 0, id, seq, len, b;
            if (cmd[0] == 'X') {
                scanf("%lu %u", &session, &ppg);
            } else {
                scanf("%u %u %lu", &result, &gen, &ticket);
            }
            scanf("%u %u %u", &id, &seq, &len);
            cmd_frame_t f = {.id = (uint8_t)id, .seq = (uint16_t)seq, .len = (uint8_t)len};
            for (unsigned i = 0; i < len; i++) {
                scanf("%x", &b);
                f.params[i] = (uint8_t)b;
            }
            if (cmd[0] == 'X') {
                cmd_action_t a = cmd_exec_decide(&e, &f, (uint32_t)session,
                                                 (cmd_ppg_state_t)ppg);
                printf("%d %u %u %u %u %lu %d %d %u %lu\n", a.apply_led, a.green, a.red,
                       a.ir, a.result, (unsigned long)a.generation, a.repeat,
                       a.mark_event, a.event_code, (unsigned long)a.ticket);
            } else {
                cmd_exec_done(&e, &f, (uint8_t)result, gen, (uint32_t)ticket);
                printf("ok\n");
            }
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
    work = tmp_path_factory.mktemp("control")
    (work / "harness.c").write_text(HARNESS, encoding="utf-8")
    exe = work / ("harness.exe" if os.name == "nt" else "harness")
    sources = ["firmware/app/cmd_exec.c", "firmware/app/packet_wire.c",
               "firmware/drivers/max30001.c", "firmware/drivers/max30101.c",
               "firmware/drivers/bmi270.c", "firmware/drivers/bmi270_config.c"]
    build = subprocess.run(
        [*compiler, "-std=c99", "-Wall", "-Wextra", "-Werror", "-Wno-unused-result",
         "-I", str(ROOT / "firmware/include"), *(str(ROOT / s) for s in sources),
         str(work / "harness.c"), "-o", str(exe)],
        capture_output=True, text=True,
    )
    assert build.returncode == 0, build.stderr
    return exe


class Run:
    def __init__(self, exe):
        self.proc = subprocess.Popen([str(exe)], stdin=subprocess.PIPE,
                                     stdout=subprocess.PIPE, text=True)

    def __call__(self, line):
        self.proc.stdin.write(line + "\n")
        self.proc.stdin.flush()
        return self.proc.stdout.readline().strip()

    def decide(self, session, ppg, cmd_id, seq, params=()):
        out = self(f"X {session} {ppg} {cmd_id} {seq} {len(params)} "
                   + " ".join(f"{b:02x}" for b in params))
        apply, g, r, i, result, gen, repeat, mark, code, ticket = map(int, out.split())
        self.ticket = ticket
        return {"apply": apply, "codes": (g, r, i), "result": result,
                "generation": gen, "repeat": repeat, "mark": mark, "event_code": code,
                "ticket": ticket}

    def done(self, result, gen, cmd_id, seq, params=(), ticket=None):
        """Answer sent; ``ticket`` defaults to that of the last decision."""
        ticket = self.ticket if ticket is None else ticket
        self(f"D {result} {gen} {ticket} {cmd_id} {seq} {len(params)} "
             + " ".join(f"{b:02x}" for b in params))

    def close(self):
        self.proc.stdin.close()
        assert self.proc.wait(timeout=30) == 0


@pytest.fixture
def run(harness):
    r = Run(harness)
    yield r
    r.close()


def packet(data, channel=0xD2):
    return Packet(2, channel, 1, 0, 0, 5, 5, 0, 0, tuple(int(x) for x in data.split()))


def test_afe_config_data_passes_the_receiver_check(run):
    expected = {
        1: {"0x10": "0x081244", "0x12": "0x004800", "0x14": "0x000000",
            "0x15": "0x001000", "0x04": "0x7B0004", "0x05": "0xBFFFFF",
            "0x02": "0x800001", "0x03": "0x000201"},
        2: {"0x08": "0x0F", "0x0A": "0x6B", "0x0C": "0x24", "0x0D": "0x24",
            "0x0E": "0x12", "0x0F": "0x12", "0x11": "0x13", "0x12": "0x02",
            "0x02": "0x60", "0x03": "0x00", "0x09": "0x07"},
        3: {"0x40": "0xA8", "0x41": "0x01", "0x42": "0xE8", "0x43": "0x02",
            "0x45": "0x88", "0x46": "0x78", "0x47": "0x00", "0x48": "0x01",
            "0x49": "0xC0", "0x53": "0x0A", "0x55": "0x00", "0x58": "0x02",
            "0x7C": "0x02", "0x7D": "0x06"},
    }
    for afe, registers in expected.items():
        config, problem = decode_afe_config(packet(run(f"W {afe} 1 1 3")))
        assert problem is None
        assert (config["source"], config["configured"], config["generation"]) == (
            "chip", True, 3)
        assert config["registers"] == registers
        for state in ("1 0 3", "0 1 0"):  # not configured; fake source
            config, problem = decode_afe_config(packet(run(f"W {afe} {state}")))
            assert problem is None and config["registers"] == {}
    assert run("A 2 65535 0 4") == "1 2 65535 0 4"
    ack, problem = decode_command_ack(packet(run("A 2 65535 0 4"), 0xD3))
    assert problem is None and ack["generation"] == 4


def led(session, g=0x12, r=0x24, i=0x24):
    return tuple(struct.pack("<I", session)) + (g, r, i)


def test_set_led_checks_come_before_the_chip(run):
    s = 0x5EED1234
    assert run.decide(s, READY, 2, 1, led(s))["apply"] == 1
    assert run.decide(s, READY, 2, 1, led(s))["codes"] == (0x12, 0x24, 0x24)
    for other in (s + 1, s - 1, 0, s ^ 0xFFFFFFFF, s ^ 0x80):
        assert run.decide(s, READY, 2, 2, led(other))["result"] == WRONG_SESSION
    assert run.decide(s, READY, 2, 3, led(s, g=0x80))["result"] == RANGE
    assert run.decide(s, READY, 2, 4, led(s, i=0x7F))["apply"] == 1
    assert run.decide(s, READY, 2, 5, led(s)[:6])["result"] == BAD_LENGTH
    assert run.decide(s, NONE, 2, 6, led(s))["result"] == NO_CHIP
    assert run.decide(s, PPG_BUSY, 2, 7, led(s))["result"] == BUSY
    assert run.decide(s, READY, 1, 8)["result"] == OK
    assert run.decide(s, READY, 1, 9, (1,))["result"] == BAD_LENGTH
    assert run.decide(s, READY, 0x42, 10)["result"] == UNKNOWN


def test_retries_get_the_remembered_answer(run):
    s = 7
    assert run.decide(s, READY, 2, 100, led(s))["apply"] == 1
    run.done(OK, 2, 2, 100, led(s))
    again = run.decide(s, READY, 2, 100, led(s))
    assert (again["apply"], again["result"], again["generation"], again["repeat"]) == (
        0, OK, 2, 1)
    # The same CMD_SEQ for other bytes or another command: refused, and the
    # remembered request is kept, so its own retry still gets its answer.
    assert run.decide(s, READY, 2, 100, led(s, g=1))["result"] == REUSED
    run.done(REUSED, 0, 2, 100, led(s, g=1))
    assert run.decide(s, READY, 1, 100)["result"] == REUSED
    run.done(REUSED, 0, 1, 100)
    assert run.decide(s, READY, 2, 100, led(s))["repeat"] == 1
    # BUSY is not remembered: the same CMD_SEQ is decided afresh.
    assert run.decide(s, PPG_BUSY, 2, 101, led(s))["result"] == BUSY
    run.done(BUSY, 0, 2, 101, led(s))
    assert run.decide(s, READY, 2, 101, led(s))["apply"] == 1
    # A failed one is remembered like a done one.
    run.done(CHIP_ERROR, 0, 2, 101, led(s))
    assert run.decide(s, READY, 2, 101, led(s))["result"] == CHIP_ERROR


def test_mark_event_takes_only_the_operator_codes(run):
    s = 7
    for code in (2, 4):
        for ppg in (NONE, PPG_BUSY, READY):  # independent of the PPG chip
            d = run.decide(s, ppg, 3, 10 * code + ppg, (code,))
            assert (d["mark"], d["event_code"], d["apply"]) == (1, code, 0)
    # t0 (1) stays the SW1 button and 3 the sync stimulus; other codes too.
    for seq, code in enumerate((0, 1, 3, 5, 0x7F, 0xFF), start=40):
        d = run.decide(s, READY, 3, seq, (code,))
        assert (d["mark"], d["result"]) == (0, RANGE)
    for seq, params in ((50, ()), (51, (2, 0)), (52, (2,) * 16)):
        d = run.decide(s, READY, 3, seq, params)
        assert (d["mark"], d["result"]) == (0, BAD_LENGTH)
    ack, problem = decode_command_ack(packet(run("A 3 52 0 0"), 0xD3))
    assert problem is None and (ack["cmd"], ack["result"], ack["generation"]) == (
        "mark_event", "ok", 0)


def test_a_mark_event_retry_never_marks_twice(run):
    s = 7
    assert run.decide(s, READY, 3, 200, (2,))["mark"] == 1
    run.done(OK, 0, 3, 200, (2,))
    again = run.decide(s, READY, 3, 200, (2,))
    assert (again["mark"], again["result"], again["repeat"]) == (0, OK, 1)
    # The same CMD_SEQ with the other code: refused, no event.
    other = run.decide(s, READY, 3, 200, (4,))
    assert (other["mark"], other["result"]) == (0, REUSED)
    # A full event queue answers BUSY, which is not remembered: the same CMD_SEQ
    # is decided afresh and marks then.
    assert run.decide(s, READY, 3, 201, (4,))["mark"] == 1
    run.done(BUSY, 0, 3, 201, (4,))
    assert run.decide(s, READY, 3, 201, (4,))["mark"] == 1


def test_a_late_led_answer_does_not_displace_a_later_mark(run):
    # The PC gave up on an LED change still in flight (unknown after 2.5 s) and
    # sent a MARK_EVENT, which was done; then the LED change finishes. A retry of
    # the mark (its answer was lost) must get the remembered answer, not a second
    # event: the later-received request stays remembered.
    s = 7
    change = run.decide(s, READY, 2, 300, led(s))
    assert change["apply"] == 1
    mark = run.decide(s, READY, 3, 301, (2,))
    assert mark["mark"] == 1 and mark["ticket"] > change["ticket"]
    run.done(OK, 0, 3, 301, (2,), ticket=mark["ticket"])
    run.done(OK, 5, 2, 300, led(s), ticket=change["ticket"])
    again = run.decide(s, READY, 3, 301, (2,))
    assert (again["mark"], again["result"], again["repeat"]) == (0, OK, 1)
    # In arrival order a later request still replaces the remembered one.
    assert run.decide(s, READY, 1, 302)["result"] == OK
    run.done(OK, 0, 1, 302)
    assert run.decide(s, READY, 3, 301, (2,))["mark"] == 1
