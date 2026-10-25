"""Compile the MAX30101 driver core and the PPG read decision; run them on the host.

firmware/drivers/max30101.c talks to a simulated chip (datasheet 19-8453 Rev 2):
register reads/writes auto-increment the address except FIFO_DATA (0x07), whose
reads pop 9 bytes per three-slot sample; RESET clears itself after a few reads;
Interrupt Status 1 clears on read; TEMP_EN clears itself after a conversion.
firmware/app/ppg_read.c is checked against Packet Schema V0.1 sections 5.1, 9
and V0.2 sections 5 and 7.6. Register values are derived by hand from the
register tables (p. 11-23) and the settings decided for the V1-module
(custom_board_proposal.md A.3, 2026-10-24/25), not from the driver. SYNTHETIC
only: the simulation shares my reading of the datasheet, so the real chip is
checked at bring-up section 8. Without a host C compiler the test is skipped.
"""

import os
import subprocess
from pathlib import Path

import pytest

from tests.test_firmware_c_encoder import _compiler

ROOT = Path(__file__).resolve().parents[1]
OK, ERR_BUS, ERR_PART_ID, ERR_RESET, ERR_READBACK, ERR_BUSY, ERR_MODE = range(7)
BIT0, BIT3, BIT4, BIT5, BIT6 = 1 << 0, 1 << 3, 1 << 4, 1 << 5, 1 << 6
PPG_RDY, ALC_OVF, PWR_RDY = 1 << 6, 1 << 5, 1 << 0

HARNESS = r"""
#include <stdarg.h>
#include <stdio.h>
#include <string.h>

#include "max30101.h"
#include "ppg_read.h"

static uint8_t s_reg[256];
static uint8_t s_fifo[64 * 9];
static int s_fifo_n, s_fifo_pos;
static int s_reset_polls = 2;  /* MODE_CONFIG reads that still show RESET */
static int s_temp_busy;        /* TEMP_CONFIG reads that still show TEMP_EN */
static unsigned s_corrupt_reg = 0xFFFu;
static uint8_t s_corrupt_bits;
static unsigned s_fail_reg = 0xFFFu; /* the next read starting here fails */
static char s_log[16384];
static size_t s_log_len;

static void note(const char *fmt, ...)
{
    va_list ap;
    va_start(ap, fmt);
    s_log_len += (size_t)vsnprintf(s_log + s_log_len, sizeof(s_log) - s_log_len, fmt, ap);
    va_end(ap);
}

static int bus_write(void *ctx, uint8_t reg, const uint8_t *data, size_t n)
{
    (void)ctx;
    note("W%02x:", reg);
    for (size_t i = 0; i < n; i++) {
        uint8_t r = (uint8_t)(reg + i);
        note("%02x", data[i]);
        if (r == MAX30101_MODE_CONFIG && (data[i] & MAX30101_MODE_RESET)) {
            memset(s_reg, 0, 0x22);
            s_reg[MAX30101_MODE_CONFIG] = MAX30101_MODE_RESET;
        } else if (r == MAX30101_TEMP_CONFIG) {
            s_reg[r] = data[i];
        } else {
            s_reg[r] = data[i];
        }
    }
    note(";");
    return 0;
}

static int bus_read(void *ctx, uint8_t reg, uint8_t *data, size_t n)
{
    (void)ctx;
    note("R%02x:%u;", reg, (unsigned)n);
    if (reg == s_fail_reg) { /* the chip saw the read, the MCU got an error */
        s_fail_reg = 0xFFFu;
        if (reg == MAX30101_FIFO_DATA) { /* part of the FIFO popped */
            s_fifo_pos += (int)n / 2;
        } else if (reg == MAX30101_INT_STATUS1) { /* cleared, flags lost */
            s_reg[MAX30101_INT_STATUS1] = 0;
        }
        return -1;
    }
    for (size_t i = 0; i < n; i++) {
        if (reg == MAX30101_FIFO_DATA) {
            data[i] = s_fifo_pos < s_fifo_n ? s_fifo[s_fifo_pos++] : 0;
            continue;
        }
        uint8_t r = (uint8_t)(reg + i);
        uint8_t v = s_reg[r];
        if (r == MAX30101_MODE_CONFIG && (v & MAX30101_MODE_RESET)) {
            if (--s_reset_polls <= 0) {
                s_reg[r] = 0; /* reset done */
            }
        }
        if (r == MAX30101_TEMP_CONFIG && (v & MAX30101_TEMP_EN) && --s_temp_busy <= 0) {
            s_reg[r] = 0;
        }
        if (r == MAX30101_INT_STATUS1 || r == MAX30101_INT_STATUS2) {
            s_reg[r] = 0; /* cleared on read */
        }
        data[i] = v ^ (r == s_corrupt_reg ? s_corrupt_bits : 0u);
    }
    return 0;
}

static void delay_ms(void *ctx, uint32_t ms)
{
    (void)ctx;
    note("D%u;", (unsigned)ms);
}

static void flush_log(void)
{
    printf("%s\n", s_log_len ? s_log : "-");
    s_log_len = 0;
    s_log[0] = 0;
}

int main(void)
{
    max30101_bus_t bus = {NULL, bus_write, bus_read, delay_ms};
    ppg_read_t pr;
    ppg_read_init(&pr);
    max30101_latch_t last = {0};
    char cmd[2];
    while (scanf("%1s", cmd) == 1) {
        unsigned a = 0, b = 0, c = 0, d = 0;
        if (cmd[0] == 'V') {
            max30101_regs_t r411, r215;
            max30101_v1_regs(&r411, 411);
            max30101_v1_regs(&r215, 215);
            max30101_set_currents(&r215, 0x30, 0x10, 0x20);
            const max30101_regs_t *rs[2] = {&r411, &r215};
            for (int k = 0; k < 2; k++) {
                const max30101_regs_t *r = rs[k];
                printf("%02x %02x %02x%02x%02x%02x %02x%02x %02x%02x\n", r->fifo_config,
                       r->spo2_config, r->led_pa[0], r->led_pa[1], r->led_pa[2], r->led_pa[3],
                       r->multi_led[0], r->multi_led[1], r->int_enable[0], r->int_enable[1]);
            }
        } else if (cmd[0] == 'I') {
            scanf("%x", &a);
            s_reg[MAX30101_PART_ID] = (uint8_t)a;
            s_reg[MAX30101_REV_ID] = 0x03;
            printf("ok\n");
        } else if (cmd[0] == 'Z') {
            scanf("%u", &a);
            s_reset_polls = (int)a;
            printf("ok\n");
        } else if (cmd[0] == 'C') {
            scanf("%x %x", &a, &b);
            s_corrupt_reg = a;
            s_corrupt_bits = (uint8_t)b;
            printf("ok\n");
        } else if (cmd[0] == 'E') {
            scanf("%x", &a);
            s_fail_reg = a;
            printf("ok\n");
        } else if (cmd[0] == 'R') {
            ppg_read_reconfigured(&pr);
            printf("ok\n");
        } else if (cmd[0] == 'S') {
            max30101_regs_t r;
            max30101_v1_regs(&r, 411);
            uint8_t rev = 0;
            int err = max30101_start(&bus, &r, &rev);
            printf("%d %02x\n", err, rev);
            flush_log();
        } else if (cmd[0] == 'P') { /* pointers and status1 */
            scanf("%u %u %u %x", &a, &b, &c, &d);
            s_reg[MAX30101_FIFO_WR_PTR] = (uint8_t)a;
            s_reg[MAX30101_OVF_COUNTER] = (uint8_t)b;
            s_reg[MAX30101_FIFO_RD_PTR] = (uint8_t)c;
            s_reg[MAX30101_INT_STATUS1] = (uint8_t)d;
            printf("ok\n");
        } else if (cmd[0] == 'L') {
            int err = max30101_latch(&bus, &last);
            printf("%d %d %d %u %d %u %02x\n", err, last.status_ok, last.pointers_ok,
                   last.waiting, last.full, last.overflow, last.status1);
            flush_log();
        } else if (cmd[0] == 'F') { /* one sample: three 24-bit slot words */
            scanf("%x %x %x", &a, &b, &c);
            unsigned w[3] = {a, b, c};
            for (int k = 0; k < 3; k++) {
                s_fifo[s_fifo_n++] = (uint8_t)(w[k] >> 16);
                s_fifo[s_fifo_n++] = (uint8_t)(w[k] >> 8);
                s_fifo[s_fifo_n++] = (uint8_t)w[k];
            }
            printf("ok\n");
        } else if (cmd[0] == 'D') {
            scanf("%u", &a);
            max30101_samples_t smp;
            int err = max30101_read_samples(&bus, (uint16_t)a, &smp);
            printf("%d %u", err, smp.count);
            for (unsigned s = 0; s < smp.count; s++) {
                printf(" %05x,%05x,%05x", (unsigned)smp.value[s][0], (unsigned)smp.value[s][1],
                       (unsigned)smp.value[s][2]);
            }
            printf("\n");
            flush_log();
        } else if (cmd[0] == 'T') { /* TINT TFRAC busy-reads */
            scanf("%x %x %u", &a, &b, &c);
            s_reg[MAX30101_TEMP_INT] = (uint8_t)a;
            s_reg[MAX30101_TEMP_FRAC] = (uint8_t)b;
            s_temp_busy = (int)c;
            printf("ok\n");
        } else if (cmd[0] == 'Q') {
            int err = max30101_temp_start(&bus);
            printf("%d\n", err);
            flush_log();
        } else if (cmd[0] == 'B') { /* brownout: registers back to reset values */
            memset(s_reg, 0, 0x22);
            printf("ok\n");
        } else if (cmd[0] == 'G') { /* the mode the chip must still be in */
            scanf("%x", &a);
            int32_t v = 0;
            int err = max30101_temp_read(&bus, (uint8_t)a, &v);
            printf("%d %ld\n", err, (long)v);
            flush_log();
        } else if (cmd[0] == 'N') { /* ppg_read_count of a latch: waiting full batch */
            scanf("%u %u %u", &a, &b, &c);
            max30101_latch_t l = {.waiting = (uint16_t)a, .full = b != 0};
            printf("%u\n", ppg_read_count(&l, (uint16_t)c));
        } else if (cmd[0] == 'X') {
            /* plan: status_ok pointers_ok waiting full status1 count ok anchor */
            unsigned long long anchor;
            unsigned e = 0, f = 0, g = 0;
            scanf("%u %u %u %u %x %u %u %llu", &a, &g, &b, &c, &d, &e, &f, &anchor);
            max30101_latch_t l = {.status_ok = a != 0, .pointers_ok = g != 0,
                                  .waiting = (uint16_t)b, .full = c != 0,
                                  .status1 = (uint8_t)d};
            ppg_read_plan_t p = ppg_read_plan(&pr, &l, (uint16_t)e, f != 0, anchor, 200000,
                                              0x10);
            printf("%d %lu %u %u %d\n", p.send, (unsigned long)p.chunk.first_index,
                   p.chunk.count, p.chunk.status, p.reconfigure);
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
    work = tmp_path_factory.mktemp("max30101")
    (work / "harness.c").write_text(HARNESS, encoding="utf-8")
    exe = work / ("harness.exe" if os.name == "nt" else "harness")
    sources = [ROOT / "firmware/drivers/max30101.c", ROOT / "firmware/app/ppg_read.c",
               ROOT / "firmware/app/imu_plan.c", ROOT / "firmware/app/packet_wire.c"]
    build = subprocess.run(
        [*compiler, "-std=c99", "-Wall", "-Wextra", "-Werror", "-Wno-unused-result",
         "-I", str(ROOT / "firmware/include"), *map(str, sources),
         str(work / "harness.c"), "-o", str(exe)],
        capture_output=True, text=True,
    )
    assert build.returncode == 0, build.stderr
    return exe


class Chip:
    def __init__(self, exe, part_id="15"):
        self.proc = subprocess.Popen([str(exe)], stdin=subprocess.PIPE,
                                     stdout=subprocess.PIPE, text=True)
        self(f"I {part_id}")

    def __call__(self, line, lines=1):
        self.proc.stdin.write(line + "\n")
        self.proc.stdin.flush()
        out = [self.proc.stdout.readline().strip() for _ in range(lines)]
        return out if lines > 1 else out[0]

    def start(self):
        result, log = self("S", 2)
        err, rev = result.split()
        return int(err), log.rstrip(";").split(";")

    def latch(self, wr, ovf, rd, status1=0):
        self(f"P {wr} {ovf} {rd} {status1:x}")
        result, log = self("L", 2)
        err, status_ok, pointers_ok, waiting, full, overflow, s1 = result.split()
        return {"err": int(err), "status_ok": int(status_ok),
                "pointers_ok": int(pointers_ok), "waiting": int(waiting),
                "full": int(full), "overflow": int(overflow), "status1": int(s1, 16),
                "log": log.rstrip(";").split(";")}

    def plan(self, waiting, count, anchor, full=False, status1=0, status_ok=True,
             pointers_ok=True, samples_ok=True):
        send, first, n, status, reconf = map(int, self(
            f"X {int(status_ok)} {int(pointers_ok)} {waiting} {int(full)} {status1:x} "
            f"{count} {int(samples_ok)} {anchor}").split())
        return {"send": send, "first": first, "count": n, "status": status,
                "reconfigure": reconf}

    def close(self):
        self.proc.stdin.close()
        assert self.proc.wait(timeout=30) == 0


@pytest.fixture
def chip(harness):
    c = Chip(harness)
    yield c
    c.close()


def test_v1_register_bytes_match_the_datasheet_tables(chip):
    r411, r215 = chip("V", 2)
    # FIFO Config p. 18: SMP_AVE 000, ROLLOVER 0, A_FULL 0xF -> 0x0F.
    # SpO2 Config p. 19-20: ADC_RGE 11 (16 384 nA) b6:5, SR 010 (200 sps) b4:2,
    #   LED_PW 11 (411 us) -> 0x6B; LED_PW 10 (215 us) -> 0x6A.
    # LED PA p. 21 (0.2 mA steps): LED1 red, LED2 IR 0x24 = 7.2 mA; SLOTx = 011
    #   drives LED3 and LED4 together (p. 22), so 0x12 = 3.6 mA each, 7.2 mA green.
    # Multi-LED p. 22: SLOT2 001 red b6:4 | SLOT1 011 green -> 0x13; SLOT3 010 IR -> 0x02.
    # Interrupt Enable 1 p. 14: PPG_RDY_EN b6 | ALC_OVF_EN b5 -> 0x60; Enable 2 -> 0x00.
    assert r411 == "0f 6b 24241212 1302 6000"
    # set_currents(green 0x30, red 0x10, IR 0x20): LED1 10, LED2 20, LED3/4 30.
    assert r215 == "0f 6a 10203030 1302 6000"


def test_start_resets_checks_part_id_configures_then_enters_multi_led_mode(chip):
    err, log = chip.start()
    assert err == OK
    writes = ["W08:0f", "W0a:6b", "W0c:24241212", "W11:1302", "W02:60", "W03:00"]
    reads = ["R08:1", "R0a:1", "R0c:4", "R11:2", "R02:1", "R03:1"]
    # The simulated RESET still reads as set twice, then clear (third read).
    assert log == (["W09:40", "D1", "R09:1", "D1", "R09:1", "D1", "R09:1", "Rff:1",
                    "Rfe:1", "R00:2"]
                   + writes + reads + ["W04:000000", "W09:07", "R09:1"])


def test_start_refuses_wrong_part_id_stuck_reset_and_bad_read_back(harness):
    c = Chip(harness, part_id="1e")
    assert c.start()[0] == ERR_PART_ID
    c.close()
    c = Chip(harness)
    c("Z 100")
    err, log = c.start()
    assert err == ERR_RESET and log.count("R09:1") == 20
    c.close()
    c = Chip(harness)
    c("C 0a 01")  # LED_PW bit reads back flipped
    assert c.start()[0] == ERR_READBACK
    c.close()
    c = Chip(harness)
    c("C 11 08")  # bit 3 of Multi-LED 1 is unused
    assert c.start()[0] == OK
    c.close()


@pytest.mark.parametrize("wr,ovf,rd,waiting,full", [
    (8, 0, 0, 8, 0), (3, 0, 30, 5, 0), (17, 0, 17, 0, 0), (17, 4, 17, 32, 1),
    (12, 0, 4, 8, 0),
])
def test_latch_reads_status_then_pointers_and_counts_with_wraparound(
        chip, wr, ovf, rd, waiting, full):
    got = chip.latch(wr, ovf, rd, PPG_RDY | ALC_OVF)
    assert got == {"err": OK, "status_ok": 1, "pointers_ok": 1, "waiting": waiting,
                   "full": full, "overflow": ovf, "status1": PPG_RDY | ALC_OVF,
                   "log": ["R00:1", "R04:3"]}  # Status 1 first, then one pointer burst


def test_latch_keeps_a_cleared_status_when_the_pointer_read_fails(chip):
    chip("E 04")
    got = chip.latch(8, 0, 0, PWR_RDY | ALC_OVF)
    assert (got["err"], got["status_ok"], got["pointers_ok"], got["status1"]) == (
        ERR_BUS, 1, 0, PWR_RDY | ALC_OVF)
    assert chip.latch(8, 0, 0)["pointers_ok"] == 1
    chip("E 00")  # nothing of the previous latch may survive
    got = chip.latch(8, 0, 0, PWR_RDY)
    assert (got["err"], got["status_ok"], got["pointers_ok"], got["log"]) == (
        ERR_BUS, 0, 0, ["R00:1"])
    # The failed read may still have cleared Status 1: PWR_RDY is gone for good.
    assert chip("L", 2)[0].split()[-1] == "00"


def test_read_samples_takes_one_burst_and_keeps_18_bits_per_slot(chip):
    chip("F 03ffff 000001 012345")
    chip("F fc0000 abcdef 000000")  # bits 23:18 are not data (p. 16)
    result, log = chip("D 2", 2)
    assert result == "0 2 3ffff,00001,12345 00000,3cdef,00000"
    assert log == "R07:18;"


@pytest.mark.parametrize("tint,tfrac,value", [("19", "3", 25 * 16 + 3),
                                              ("fe", "8", -2 * 16 + 8),
                                              ("80", "f", -128 * 16 + 15)])
def test_die_temperature_in_sixteenths_and_busy_while_converting(chip, tint, tfrac, value):
    chip(f"T {tint} {tfrac} 1")
    assert chip("Q", 2) == ["0", "W21:01;"]
    assert chip("G 0", 2)[0] == f"{ERR_BUSY} 0"  # TEMP_EN still set
    assert chip("G 0", 2)[0] == f"{OK} {value}"


def test_temperature_read_refuses_a_chip_reset_during_the_conversion(chip):
    # V0.2 section 11.1: after a brownout TEMP_EN and the temperature registers
    # read 0, which looks like a finished conversion at 0 degC; MODE_CONFIG,
    # read after them, tells.
    assert chip.start()[0] == OK
    chip("T 19 3 1")
    assert chip("Q", 2)[0] == "0"
    assert chip("G 7", 2)[0] == f"{ERR_BUSY} 0"
    assert chip("G 7", 2) == [f"{OK} {25 * 16 + 3}", "R21:1;R1f:2;R09:1;"]
    assert chip("Q", 2)[0] == "0"
    chip("B")
    assert chip("G 7", 2)[0] == f"{ERR_MODE} 0"

@pytest.mark.parametrize("waiting,full,batch,count", [
    (7, 0, 8, 0), (8, 0, 8, 8), (12, 0, 8, 12), (32, 1, 8, 32), (3, 0, 1, 3), (0, 0, 1, 0),
])
def test_read_count_is_everything_waiting_once_the_batch_is_reached(
        chip, waiting, full, batch, count):
    assert chip(f"N {waiting} {full} {batch}") == str(count)


def test_ppg_plan_index_flags_full_and_failures(harness):
    c = Chip(harness)
    first = c.plan(8, 8, 1_000_000)
    assert first == {"send": 1, "first": 0, "count": 8, "status": BIT4, "reconfigure": 0}
    assert c.plan(8, 8, 1_040_000)["first"] == 8
    # ALC_OVF seen on a latch with too few samples is kept for the next packet.
    assert c.plan(5, 0, 1_060_000, status1=ALC_OVF)["send"] == 0
    flagged = c.plan(8, 8, 1_080_000)
    assert (flagged["first"], flagged["status"]) == (16, BIT4 | BIT6)
    # A full FIFO: valid samples, bit 0, index continues (24..55).
    full = c.plan(32, 32, 1_240_000, full=True)
    assert (full["first"], full["status"]) == (24, BIT4 | BIT0)
    # The next read re-anchors by time from the last reliable read (23 at
    # 1.08 s): q = round(0.32 s * 200) = 64, FIRST = max(56, 23 + 64 - 7) = 80.
    after = c.plan(8, 8, 1_400_000)
    assert (after["first"], after["status"]) == (80, BIT4 | BIT5)
    c.close()


def test_ppg_plan_bus_failure_and_brownout(harness):
    c = Chip(harness)
    c.plan(8, 8, 1_000_000)
    ptr = c.plan(8, 0, 1_040_000, pointers_ok=False)  # no side effect: no reset
    assert (ptr["send"], ptr["reconfigure"]) == (0, 0)
    nxt = c.plan(8, 8, 1_080_000)
    # q = round(0.08 * 200) = 16 from (7, 1.0 s): 7 + 16 - 7 = 16.
    assert (nxt["first"], nxt["status"]) == (16, BIT4 | BIT3 | BIT5)
    brown = c.plan(8, 8, 1_120_000, status1=PWR_RDY)
    assert (brown["send"], brown["reconfigure"]) == (0, 1)
    c("R")  # max30101_start succeeded
    assert c.plan(8, 8, 1_160_000)["status"] == BIT4 | BIT3 | BIT5
    c.close()


def test_ppg_plan_keeps_status_flags_when_only_the_pointers_failed(harness):
    c = Chip(harness)
    c.plan(8, 8, 1_000_000)
    lost = c.plan(0, 0, 1_040_000, status1=ALC_OVF, pointers_ok=False)
    assert (lost["send"], lost["reconfigure"]) == (0, 0)
    assert c.plan(8, 8, 1_080_000)["status"] == BIT4 | BIT3 | BIT5 | BIT6
    # A brownout seen in a Status 1 whose pointer read failed still reconfigures.
    brown = c.plan(0, 0, 1_120_000, status1=PWR_RDY, pointers_ok=False)
    assert (brown["send"], brown["reconfigure"]) == (0, 1)
    c.close()


def test_ppg_plan_reconfigures_after_a_failed_status_read(harness):
    # The failed read may have cleared PWR_RDY: only a reset gives a known state.
    c = Chip(harness)
    c.plan(8, 8, 1_000_000)
    lost = c.plan(0, 0, 1_040_000, status_ok=False, pointers_ok=False)
    assert (lost["send"], lost["reconfigure"]) == (0, 1)
    assert c.plan(8, 8, 1_080_000)["reconfigure"] == 1
    c("R")
    assert c.plan(8, 8, 1_120_000)["status"] == BIT4 | BIT3 | BIT5
    c.close()


def test_ppg_plan_sends_nothing_until_a_reconfiguration_succeeds(harness):
    c = Chip(harness)
    c.plan(8, 8, 1_000_000)
    assert c.plan(8, 8, 1_040_000, status1=PWR_RDY)["reconfigure"] == 1
    # max30101_start failed: later looks, even good ones, only ask again.
    for t in (1_080_000, 1_120_000):
        again = c.plan(8, 8, t)
        assert (again["send"], again["reconfigure"]) == (0, 1)
    c("R")
    back = c.plan(8, 8, 1_160_000)
    assert (back["send"], back["reconfigure"], back["status"]) == (1, 0, BIT4 | BIT3 | BIT5)
    c.close()


def test_ppg_plan_reconfigures_after_a_failed_sample_read(harness):
    # Part of the FIFO was popped; clearing pointers mid-acquisition has no
    # datasheet guarantee, so the chip is reset and configured again.
    c = Chip(harness)
    c.plan(8, 8, 1_000_000)
    failed = c.plan(8, 8, 1_040_000, samples_ok=False)
    assert (failed["send"], failed["reconfigure"]) == (0, 1)
    c("R")
    assert c.plan(8, 8, 1_080_000)["status"] == BIT4 | BIT3 | BIT5
    # A failed read of a full FIFO: samples were lost, bit 0 goes on the next packet.
    full = c.plan(32, 32, 1_240_000, full=True, samples_ok=False)
    assert (full["send"], full["reconfigure"]) == (0, 1)
    c("R")
    assert c.plan(8, 8, 1_280_000)["status"] == BIT4 | BIT0 | BIT3 | BIT5
    # Nothing was read (too few waiting): no read, no failure.
    assert c.plan(5, 0, 1_300_000, samples_ok=False)["reconfigure"] == 0
    c.close()
