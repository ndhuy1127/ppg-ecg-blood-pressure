"""Compile the BMI270 driver core (firmware/drivers/bmi270.c); run it on the host.

The driver talks raw SPI to a simulated BMI270 (datasheet BST-BMI270-DS000-08,
rev 1.6): the interface starts in I2C mode and answers SPI only once a
transaction has ended (CSB rising edge) and 200 us have passed, again after a
soft reset (section 6.3); a read returns one dummy byte first; addresses
auto-increment except at FIFO_DATA, which pops whole frames; INIT_DATA takes
the microcode at INIT_ADDR * 2 (section 4.4, footnote 4); INIT_CTRL = 1 says
init_ok only if the whole Bosch array was written with advanced power save
off; EVENT.por_detected is set by a reset and cleared on read. Register values
are derived by hand from section 5.2 and Packet Schema V0.2 section 3, not from
the driver. SYNTHETIC only: the simulation shares my reading of the datasheet,
so the real chip is checked at bring-up. Without a host C compiler the test is
skipped.
"""

import hashlib
import os
import re
import subprocess
from pathlib import Path

import pytest

from tests.test_firmware_c_encoder import _compiler

ROOT = Path(__file__).resolve().parents[1]
OK, ERR_BUS, ERR_CHIP_ID, ERR_INIT, ERR_READBACK, ERR_STATE = range(6)
CONFIG_SHA256 = "2d75e68e343a13ff99be98261dfbd99d9e8c6f267da9e3c5aeb883276ad178db"

HARNESS = r"""
#include <stdarg.h>
#include <stdio.h>
#include <string.h>

#include "bmi270.h"
#include "bmi270_config.h"

static uint8_t s_reg[128];
static uint8_t s_chip_id = 0x24;
static int s_spi;                 /* the interface answers SPI */
static long s_since_edge_us = -1; /* delay since the switching edge; -1: none */
static uint8_t s_cfg[BMI270_CONFIG_SIZE];
static uint8_t s_cfg_set[BMI270_CONFIG_SIZE];
static int s_init_polls = 2, s_init_left = -1;
static int s_conf_error;          /* set EVENT.error_code on ACC_CONF writes */
static uint8_t s_fifo[4096];
static int s_fifo_n, s_fifo_pos;
static int s_len_lo = -1, s_len_hi = -1;
static unsigned s_corrupt_reg = 0xFFFu;
static uint8_t s_corrupt_bits;
static int s_fail_next; /* 1: fails at once; 2: after its side effects */
static char s_log[65536];
static size_t s_log_len;

static void note(const char *fmt, ...)
{
    va_list ap;
    va_start(ap, fmt);
    s_log_len += (size_t)vsnprintf(s_log + s_log_len, sizeof(s_log) - s_log_len, fmt, ap);
    va_end(ap);
}

static void reset_chip(void)
{
    memset(s_reg, 0, sizeof(s_reg));
    s_reg[0x00] = s_chip_id;
    s_reg[0x03] = 0x10;
    s_reg[0x1B] = 0x01; /* por_detected */
    s_reg[0x23] = 0x80;
    s_reg[0x40] = 0xA8;
    s_reg[0x41] = 0x02;
    s_reg[0x42] = 0xA9;
    s_reg[0x44] = 0x46;
    s_reg[0x45] = 0x88;
    s_reg[0x47] = 0x02;
    s_reg[0x48] = 0x02;
    s_reg[0x49] = 0x10;
    s_reg[0x7C] = 0x03;
    s_spi = 0;
    s_since_edge_us = -1;
    memset(s_cfg_set, 0, sizeof(s_cfg_set));
    s_init_left = -1;
    s_fifo_n = s_fifo_pos = 0;
}

static uint8_t read_reg(uint8_t r)
{
    if (r == 0x21 && s_init_left > 0 && --s_init_left == 0) {
        s_reg[0x21] = 0x01; /* init_ok on the s_init_polls-th read */
    }
    uint8_t v = s_reg[r];
    if (r == 0x26) {
        if (s_fifo_pos < s_fifo_n) {
            v = s_fifo[s_fifo_pos++];
        } else {
            v = (uint8_t)(s_fifo_pos++ % 2 ? 0x80 : 0x00); /* over-read: 0x8000 */
        }
    } else if (r == 0x24 || r == 0x25) {
        int left = s_fifo_n - s_fifo_pos;
        v = r == 0x24 ? (uint8_t)(s_len_lo >= 0 ? s_len_lo : left & 0xFF)
                      : (uint8_t)(s_len_hi >= 0 ? s_len_hi : left >> 8);
    } else if (r == 0x1B) {
        s_reg[r] &= (uint8_t)~0x01u;
    }
    return v ^ (r == s_corrupt_reg ? s_corrupt_bits : 0u);
}

static void write_reg(uint8_t r, uint8_t v)
{
    if (r == 0x7E) {
        if (v == 0xB6) {
            reset_chip();
        } else if (v == 0xB0) {
            s_fifo_n = s_fifo_pos = 0;
        }
        return;
    }
    if (r == 0x59 && v == 0x01) {
        int all = 1;
        for (unsigned i = 0; i < BMI270_CONFIG_SIZE; i++) {
            all &= s_cfg_set[i] && s_cfg[i] == bmi270_config_file[i];
        }
        /* Section 4.4: whole file, advanced power save off. */
        if (all && !(s_reg[0x7C] & 0x01)) {
            s_init_left = s_init_polls;
        } else {
            s_reg[0x21] = 0x02; /* init_err */
        }
    }
    if (r == 0x40 && s_conf_error) {
        s_reg[0x1B] |= 0x04; /* error_code 1: acc_err */
    }
    s_reg[r] = v;
}

static int xfer(void *ctx, const uint8_t *tx, uint8_t *rx, size_t n)
{
    (void)ctx;
    memset(rx, 0xFF, n);
    if (s_fail_next == 1) {
        s_fail_next = 0;
        note("F;");
        return -1;
    }
    if (!s_spi) {
        /* I2C mode: ignored; its CSB rising edge switches to SPI 200 us later. */
        if (s_since_edge_us >= 200) {
            s_spi = 1;
        } else {
            note("X%02x;", tx[0]);
            if (s_since_edge_us < 0) {
                s_since_edge_us = 0;
            }
            return 0;
        }
    }
    uint8_t addr = tx[0] & 0x7Fu;
    if (tx[0] & 0x80u) {
        note("R%02x:%u;", addr, (unsigned)(n - 2));
        rx[1] = 0x5A; /* dummy byte */
        int start = s_fifo_pos;
        for (size_t i = 2; i < n; i++) {
            uint8_t r = addr == 0x26 ? addr : (uint8_t)(addr + i - 2);
            rx[i] = read_reg(r);
        }
        if (addr == 0x26 && s_fifo_pos <= s_fifo_n) {
            /* A frame read in part is sent again whole next time (4.7.2). */
            s_fifo_pos = start + (s_fifo_pos - start) / 12 * 12;
        }
        if (s_fail_next == 2) {
            s_fail_next = 0;
            note("F;");
            return -1;
        }
        return 0;
    }
    if (addr == 0x5E) {
        unsigned base = 2u * ((unsigned)(s_reg[0x5B] & 0x0F) | ((unsigned)s_reg[0x5C] << 4));
        note("W5e:%uB@%u;", (unsigned)(n - 1), base);
        for (size_t i = 1; i < n && base + i - 1 < BMI270_CONFIG_SIZE; i++) {
            s_cfg[base + i - 1] = tx[i];
            s_cfg_set[base + i - 1] = 1;
        }
        return 0;
    }
    note("W%02x:", addr);
    for (size_t i = 1; i < n; i++) {
        note("%02x", tx[i]);
        write_reg((uint8_t)(addr + i - 1), tx[i]);
    }
    note(";");
    return 0;
}

static void delay_us(void *ctx, uint32_t us)
{
    (void)ctx;
    note("U%u;", (unsigned)us);
    if (s_since_edge_us >= 0) {
        s_since_edge_us += (long)us;
    }
}

static void flush_log(void)
{
    printf("%s\n", s_log_len ? s_log : "-");
    s_log_len = 0;
    s_log[0] = 0;
}

int main(void)
{
    bmi270_bus_t bus = {NULL, xfer, delay_us};
    bmi270_regs_t regs;
    bmi270_v1_regs(&regs);
    reset_chip();
    char cmd[2];
    while (scanf("%1s", cmd) == 1) {
        unsigned a = 0, b = 0;
        if (cmd[0] == 'V') {
            printf("%02x %02x %02x %02x %02x %02x%02x %02x %02x %02x %02x %02x %02x %02x\n",
                   regs.acc_conf, regs.acc_range, regs.gyr_conf, regs.gyr_range,
                   regs.fifo_downs, regs.fifo_wtm[0], regs.fifo_wtm[1], regs.fifo_config[0],
                   regs.fifo_config[1], regs.int1_io_ctrl, regs.int_latch, regs.int_map_data,
                   regs.pwr_conf, regs.pwr_ctrl);
        } else if (cmd[0] == 'I') {
            scanf("%x", &a);
            s_chip_id = (uint8_t)a;
            reset_chip();
            printf("ok\n");
        } else if (cmd[0] == 'K') {
            scanf("%u", &a);
            s_init_polls = (int)a;
            printf("ok\n");
        } else if (cmd[0] == 'Q') {
            s_conf_error = 1;
            printf("ok\n");
        } else if (cmd[0] == 'C') {
            scanf("%x %x", &a, &b);
            s_corrupt_reg = a;
            s_corrupt_bits = (uint8_t)b;
            printf("ok\n");
        } else if (cmd[0] == 'X') { /* set a register as the chip would */
            scanf("%x %x", &a, &b);
            s_reg[a & 0x7Fu] = (uint8_t)b;
            printf("ok\n");
        } else if (cmd[0] == 'P') { /* power-on reset, not commanded */
            reset_chip();
            printf("ok\n");
        } else if (cmd[0] == 'E') {
            scanf("%u", &a);
            s_fail_next = (int)a;
            printf("ok\n");
        } else if (cmd[0] == 'U') {
            int err = bmi270_flush(&bus);
            printf("%d %d\n", err, s_fifo_n - s_fifo_pos);
            flush_log();
        } else if (cmd[0] == 'S') {
            int err = bmi270_start(&bus, &regs, bmi270_config_file);
            int same = 1;
            for (unsigned i = 0; i < BMI270_CONFIG_SIZE; i++) {
                same &= s_cfg_set[i] && s_cfg[i] == bmi270_config_file[i];
            }
            printf("%d %d %02x\n", err, same, s_reg[0x21]);
            flush_log();
        } else if (cmd[0] == 'H') {
            int err = bmi270_check(&bus, &regs);
            printf("%d\n", err);
            flush_log();
        } else if (cmd[0] == 'L') { /* FIFO_LENGTH bytes as read, or -1 -1 */
            int lo, hi;
            scanf("%d %d", &lo, &hi);
            s_len_lo = lo;
            s_len_hi = hi;
            printf("ok\n");
        } else if (cmd[0] == 'A') {
            bmi270_latch_t l;
            int err = bmi270_latch(&bus, &l);
            printf("%d %u %u %d\n", err, l.length, l.frames, l.full);
            flush_log();
        } else if (cmd[0] == 'F') { /* one frame: gyr X Y Z, acc X Y Z words */
            unsigned w[6];
            scanf("%x %x %x %x %x %x", &w[0], &w[1], &w[2], &w[3], &w[4], &w[5]);
            for (int k = 0; k < 6; k++) {
                s_fifo[s_fifo_n++] = (uint8_t)w[k];
                s_fifo[s_fifo_n++] = (uint8_t)(w[k] >> 8);
            }
            printf("ok\n");
        } else if (cmd[0] == 'D') {
            scanf("%u", &a);
            static bmi270_frames_t fr;
            int err = bmi270_read_frames(&bus, (uint16_t)a, &fr);
            printf("%d %u", err, fr.count);
            for (unsigned f = 0; f < fr.count; f++) {
                printf(" ");
                for (int k = 0; k < 6; k++) {
                    printf("%s%d", k ? "," : "", fr.value[f][k]);
                }
            }
            printf("\n");
            flush_log();
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
    work = tmp_path_factory.mktemp("bmi270")
    (work / "harness.c").write_text(HARNESS, encoding="utf-8")
    exe = work / ("harness.exe" if os.name == "nt" else "harness")
    sources = [ROOT / "firmware/drivers/bmi270.c", ROOT / "firmware/drivers/bmi270_config.c"]
    build = subprocess.run(
        [*compiler, "-std=c99", "-Wall", "-Wextra", "-Werror", "-Wno-unused-result",
         "-I", str(ROOT / "firmware/include"), *map(str, sources),
         str(work / "harness.c"), "-o", str(exe)],
        capture_output=True, text=True,
    )
    assert build.returncode == 0, build.stderr
    return exe


class Chip:
    def __init__(self, exe):
        self.proc = subprocess.Popen([str(exe)], stdin=subprocess.PIPE,
                                     stdout=subprocess.PIPE, text=True)

    def __call__(self, line, lines=1):
        self.proc.stdin.write(line + "\n")
        self.proc.stdin.flush()
        out = [self.proc.stdout.readline().strip() for _ in range(lines)]
        return out if lines > 1 else out[0]

    def start(self):
        result, log = self("S", 2)
        err, same, status = result.split()
        return int(err), int(same), int(status, 16), log.rstrip(";").split(";")

    def check(self):
        result, log = self("H", 2)
        return int(result), log.rstrip(";").split(";")

    def latch(self, lo=-1, hi=-1):
        self(f"L {lo} {hi}")
        result, log = self("A", 2)
        err, length, frames, full = map(int, result.split())
        return (err, length, frames, full), log.rstrip(";").split(";")

    def close(self):
        self.proc.stdin.close()
        assert self.proc.wait(timeout=30) == 0


@pytest.fixture
def chip(harness):
    c = Chip(harness)
    yield c
    c.close()


def test_v1_register_bytes_match_the_datasheet_and_schema(chip):
    # ACC_CONF 5.2.41: filter_perf 1 | bwp 010 normal | odr 1000 (100 Hz) -> a8;
    # ACC_RANGE 01 = +-4 g. GYR_CONF 5.2.43: filter_perf 1 | noise_perf 1 | bwp 10
    # | odr 1000 -> e8; GYR_RANGE 010 = +-500 dps. FIFO_DOWNS 5.2.46: filtered acc
    # b7 and gyr b3 -> 88. FIFO_WTM 120 bytes = 10 frames -> 78 00. FIFO_CONFIG_0
    # stop_on_full -> 01; FIFO_CONFIG_1 gyr_en b7 | acc_en b6 -> c0. INT1_IO_CTRL
    # output_en b3 | lvl b1 (active high, push-pull) -> 0a; INT_LATCH 00;
    # INT_MAP_DATA fwm_int1 b1 -> 02. PWR_CONF adv_power_save 0, fifo_self_wake_up
    # 1 -> 02; PWR_CTRL gyr_en b1 | acc_en b2 -> 06.
    assert chip("V") == "a8 01 e8 02 88 7800 01 c0 0a 00 02 02 06"


def test_config_file_is_the_bosch_array_byte_for_byte():
    text = (ROOT / "firmware/drivers/bmi270_config.c").read_text(encoding="ascii")
    body = text.split("bmi270_config_file[BMI270_CONFIG_SIZE] = {", 1)[1]
    data = bytes(int(x, 16) for x in re.findall(r"0x([0-9a-f]{2})", body))
    assert len(data) == 8192
    assert hashlib.sha256(data).hexdigest() == CONFIG_SHA256
    assert "BSD-3-Clause" in text and "Copyright (c) 2023 Bosch Sensortec GmbH" in text
    assert CONFIG_SHA256 in (ROOT / "firmware/THIRD_PARTY_NOTICES.md").read_text(
        encoding="utf-8")


def test_start_switches_to_spi_resets_uploads_and_configures(chip):
    err, same, status, log = chip.start()
    assert (err, same, status) == (OK, 1, 0x01)
    # Section 6.3: the first read only switches to SPI (I2C mode answers nothing);
    # the soft reset puts it back to I2C, so once more after it.
    assert log[:9] == ["X80", "U2", "U1000", "W7e:b6", "U450", "U2000", "X80", "U2",
                       "U1000"]
    assert log[9:11] == ["R00:1", "U2"]
    # Section 4.4: advanced power save off, INIT_CTRL 0, 32 bursts of 256 bytes at
    # INIT_ADDR = offset / 2 split 3:0 / 11:4, INIT_CTRL 1, 20 ms, INTERNAL_STATUS.
    assert log[11:15] == ["W7c:00", "U450", "W59:00", "U450"]
    bursts = [e for e in log if e.startswith(("W5b", "W5e"))]
    expected = []
    for k in range(32):
        base = k * 128
        expected += [f"W5b:{base & 0x0F:02x}{base >> 4:02x}", f"W5e:256B@{2 * base}"]
    assert bursts == expected
    after = log[log.index("W59:01"):]
    assert after[:4] == ["W59:01", "U450", "U20000", "R21:1"]
    # init_ok on the second read, 1 ms later; then the configuration in order,
    # read back.
    assert after[4:7] == ["U2", "U1000", "R21:1"]
    tail = [e for e in after[7:] if not e.startswith("U")]
    assert tail == ["W40:a8", "W41:01", "W42:e8", "W43:02", "W45:88", "W46:78", "W47:00",
                    "W48:01", "W49:c0", "W53:0a", "W55:00", "W58:02", "W7c:02",
                    "R40:10", "R53:6", "R7c:2", "R1b:1",
                    "W7d:06", "W7e:b0", "R40:10", "R53:6", "R7c:2"]
    assert "U80000" in after[after.index("W7d:06"):after.index("W7e:b0")]
    # Every write is followed by 450 us and every read by 2 us (section 6.4).
    for entry, nxt in zip(log, log[1:]):
        if entry.startswith("W"):
            assert nxt == "U450", entry
        if entry.startswith("R"):
            assert nxt == "U2", entry


def test_start_refuses_wrong_chip_failed_init_and_bad_configuration(harness):
    c = Chip(harness)
    c("I 26")
    assert c.start()[0] == ERR_CHIP_ID
    c.close()
    c = Chip(harness)
    c("K 99")  # INTERNAL_STATUS never says init_ok
    err, _, _, log = c.start()
    assert err == ERR_INIT and log.count("R21:1") == 11
    c.close()
    c = Chip(harness)
    c("C 42 40")  # gyr_noise_perf reads back flipped
    assert c.start()[0] == ERR_READBACK
    c.close()
    c = Chip(harness)
    c("C 44 ff")  # AUX_CONF is not ours: no effect
    assert c.start()[0] == OK
    c.close()
    c = Chip(harness)
    c("Q")  # EVENT.error_code: ACC_CONF rejected
    assert c.start()[0] == ERR_READBACK
    c.close()


def test_check_sees_a_reset_a_fatal_error_and_a_lost_configuration(harness):
    for setup, expected in ((None, OK), ("X 1b 01", ERR_STATE), ("X 02 01", ERR_STATE),
                            ("X 1b 08", ERR_STATE), ("X 21 00", ERR_STATE),
                            ("X 41 03", ERR_READBACK), ("X 7d 00", ERR_READBACK)):
        c = Chip(harness)
        assert c.start()[0] == OK
        if setup:
            c(setup)
        err, log = c.check()
        assert err == expected, setup
        if setup is None:
            assert log[:8] == ["R00:1", "U2", "R02:1", "U2", "R1b:1", "U2", "R21:1", "U2"]
        c.close()
    # A power-on reset puts the interface back to I2C: the check fails, then a
    # new start brings the chip back.
    c = Chip(harness)
    assert c.start()[0] == OK
    c("P")
    assert c.check()[0] != OK
    assert c.start()[0] == OK and c.check()[0] == OK
    c.close()


@pytest.mark.parametrize("lo,hi,length,frames,full", [
    (0, 0, 0, 0, 0), (120, 0, 120, 10, 0),
    (0xE0, 0x07, 2016, 168, 0),   # 2016 + 21 <= 2048
    (0xEC, 0x07, 2028, 169, 1),   # fewer than 21 bytes free
    (0xF8, 0x07, 2040, 170, 1),
    (0x78, 0xC0, 120, 10, 0),     # FIFO_LENGTH_1 bits 7:6 are not length
])
def test_latch_reads_fifo_length_and_flags_full_conservatively(
        chip, lo, hi, length, frames, full):
    assert chip.start()[0] == OK
    result, log = chip.latch(lo, hi)
    assert result == (OK, length, frames, full)
    assert log == ["R24:2", "U2"]


def test_read_frames_maps_axes_and_leaves_later_frames(chip):
    assert chip.start()[0] == OK
    chip("F 0001 0002 0003 0004 0005 0006")
    chip("F ffff 8000 7fff fffe 0100 8001")
    chip("F 0011 0012 0013 0014 0015 0016")
    result, log = chip("D 2", 2)
    # Bytes 0-5 gyr X, Y, Z; 6-11 acc X, Y, Z; packets in channel order 0xA1-0xA6
    # (acc X, Y, Z, gyr X, Y, Z), little-endian signed words.
    assert result == "0 2 4,5,6,1,2,3 -2,256,-32767,-1,-32768,32767"
    assert log == "R26:24;U2;"
    assert chip("D 1", 2)[0] == "0 1 20,21,22,17,18,19"
    assert chip("D 0", 2)[0].split()[:2] == [str(ERR_BUS), "0"]
    assert chip("D 171", 2)[0].split()[:2] == [str(ERR_BUS), "0"]


@pytest.mark.parametrize("lo,hi", [(125, 0), (0x00, 0x08), (0x01, 0x08), (0x04, 0x08),
                                   (0xFF, 0x3F), (0xFF, 0xFF)])
def test_latch_refuses_a_length_that_is_not_whole_frames(chip, lo, hi):
    # 125 and 2048 are not multiples of 12; 2052 is past 170 frames; a
    # floating-high MISO reads 0x3FFF: none is a fill level (4.7.1, 5.2.36).
    assert chip.start()[0] == OK
    assert chip.latch(lo, hi)[0] == (ERR_STATE, 0, 0, 0)


def test_bus_failure_is_reported(chip):
    assert chip.start()[0] == OK
    chip("E 1")
    assert chip.latch()[0][0] == ERR_BUS


def test_failed_read_after_taking_frames_out_then_flush(chip):
    # The transfer clocked two whole frames out, then failed: they are gone
    # (only a frame read in part comes back, 4.7.2); the flush empties the rest.
    assert chip.start()[0] == OK
    for k in range(3):
        chip(f"F {k:04x} 0 0 0 0 0")
    chip("E 2")
    assert chip("D 2", 2)[0].split()[:2] == [str(ERR_BUS), "0"]
    assert chip.latch()[0] == (OK, 12, 1, 0)
    assert chip("U", 2) == ["0 0", "W7e:b0;U450;"]
    assert chip.latch()[0] == (OK, 0, 0, 0)
