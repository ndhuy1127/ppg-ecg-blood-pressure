"""Compile the MAX30001 driver core and run it against a simulated chip.

firmware/drivers/max30001.c has no ESP-IDF dependency. The harness models the
SPI side of the chip (datasheet 19-7590): 32-clock frames framed by CSB, the
command byte address << 1 | R/W, writes executed on the 32nd clock, the first
read after a reset returning no valid data, a latched PLLINT, and the ECG FIFO
burst read (0x20) one 24-bit word after another. Expected register words are
derived by hand from the register tables (pages 43-53) and the settings decided
for the V1-module (custom_board_proposal.md A.2, 2026-10-23..25), not from the
driver. SYNTHETIC only: no chip is involved, so this cannot catch a datasheet
detail the simulation also gets wrong; bring-up section 7 checks the real chip.
Without a host C compiler the test is skipped, like test_firmware_c_encoder.py.
"""

import os
import subprocess
from pathlib import Path

import pytest

from tests.test_firmware_c_encoder import _compiler

ROOT = Path(__file__).resolve().parents[1]
ERR_OK, ERR_BUS, ERR_INFO, ERR_READBACK, ERR_PLL = range(5)
VALID, FAST, VALID_EOF, FAST_EOF, EMPTY, OVERFLOW = 0, 1, 2, 3, 6, 7

HARNESS = r"""
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "max30001.h"

static uint32_t s_regs[128];
static uint32_t s_fifo[64];
static int s_fifo_n, s_fifo_pos;
static int s_pll_reads; /* STATUS reads that still show PLLINT */
static uint32_t s_info = 0x541000u;
static int s_after_reset;
static unsigned s_corrupt_reg = 0xFFu;
static uint32_t s_corrupt_bits;
static int s_in_frame, s_byte, s_cmd = -1, s_eof_given, s_overread, s_frames;
static uint32_t s_data, s_out;
static char s_log[16384];
static size_t s_log_len;

static void note(const char *fmt, ...)
{
    va_list ap;
    va_start(ap, fmt);
    s_log_len += (size_t)vsnprintf(s_log + s_log_len, sizeof(s_log) - s_log_len, fmt, ap);
    va_end(ap);
}

static void cs(void *ctx, bool active)
{
    (void)ctx;
    s_in_frame = active;
    if (active) {
        s_byte = 0;
        s_cmd = -1;
        s_data = 0;
        s_eof_given = 0;
        s_frames++;
    }
}

static void exec_write(unsigned reg, uint32_t value)
{
    note("W%02x:%06x;", reg, (unsigned)value);
    if (reg == MAX30001_SW_RST && value == 0) {
        memset(s_regs, 0, sizeof(s_regs));
        s_after_reset = 1;
    } else if (reg != MAX30001_SYNCH && reg != MAX30001_FIFO_RST) {
        s_regs[reg] = value;
    }
}

static uint32_t read_reg(unsigned reg)
{
    note("R%02x;", reg);
    if (s_after_reset) {
        s_after_reset = 0;
        return 0;
    }
    if (reg == MAX30001_INFO) {
        return s_info;
    }
    if (reg == MAX30001_STATUS) {
        if (s_pll_reads > 0) {
            s_pll_reads--;
            return MAX30001_ST_PLLINT;
        }
        return 0;
    }
    return s_regs[reg] ^ (reg == s_corrupt_reg ? s_corrupt_bits : 0u);
}

static int xfer(void *ctx, const uint8_t *tx, uint8_t *rx, size_t n)
{
    (void)ctx;
    for (size_t i = 0; i < n; i++, s_byte++) {
        if (!s_in_frame) {
            return -1; /* every byte must be inside a CS frame */
        }
        if (s_byte == 0) {
            s_cmd = tx[i];
            rx[i] = 0;
            unsigned reg = (unsigned)s_cmd >> 1;
            if ((s_cmd & 1) && reg == MAX30001_ECG_FIFO_BURST) {
                note("B;");
            } else if (s_cmd & 1) {
                s_out = read_reg(reg);
            }
            continue;
        }
        unsigned reg = (unsigned)s_cmd >> 1;
        if ((s_cmd & 1) && reg == MAX30001_ECG_FIFO_BURST) {
            int pos = (s_byte - 1) % 3;
            if (pos == 0) {
                if (s_eof_given) {
                    s_overread++;
                }
                s_out = s_fifo_pos < s_fifo_n ? s_fifo[s_fifo_pos++] : 0x000030u;
                unsigned tag = (s_out >> 3) & 7u;
                if (tag == 2 || tag == 3) {
                    s_eof_given = 1;
                }
            }
            rx[i] = (uint8_t)(s_out >> (8 * (2 - pos)));
        } else if (s_cmd & 1) {
            rx[i] = s_byte <= 3 ? (uint8_t)(s_out >> (8 * (3 - s_byte))) : 0;
        } else if (s_byte <= 3) {
            s_data = (s_data << 8) | tx[i];
            if (s_byte == 3) {
                exec_write(reg, s_data); /* executed on the 32nd clock */
            }
        }
    }
    return 0;
}

static void delay_ms(void *ctx, uint32_t ms)
{
    (void)ctx;
    note("D%u;", (unsigned)ms);
}

static void between(void *arg)
{
    (void)arg;
    note("CB;");
}

static void flush_log(void)
{
    printf("%s\n", s_log_len ? s_log : "-");
    s_log_len = 0;
    s_log[0] = 0;
}

int main(void)
{
    max30001_bus_t bus = {NULL, cs, xfer, delay_ms};
    max30001_regs_t v1, cal;
    max30001_v1_regs(&v1);
    max30001_cal_regs(&v1, &cal);
    char cmd[2];
    while (scanf("%1s", cmd) == 1) {
        unsigned a = 0, b = 0;
        if (cmd[0] == 'I') {
            scanf("%x", &a);
            s_info = a;
            printf("ok\n");
        } else if (cmd[0] == 'P') {
            scanf("%u", &a);
            s_pll_reads = (int)a;
            printf("ok\n");
        } else if (cmd[0] == 'C') {
            scanf("%x %x", &a, &b);
            s_corrupt_reg = a;
            s_corrupt_bits = b;
            printf("ok\n");
        } else if (cmd[0] == 'F') {
            scanf("%x", &a);
            s_fifo[s_fifo_n++] = a;
            printf("ok\n");
        } else if (cmd[0] == 'H') { /* max30001_check */
            int err = max30001_check(&bus, &v1);
            printf("%d\n", err);
            flush_log();
        } else if (cmd[0] == 'Z') { /* power-on reset, not commanded */
            memset(s_regs, 0, sizeof(s_regs));
            printf("ok\n");
        } else if (cmd[0] == 'S') {
            scanf("%u", &a);
            uint32_t info = 0;
            s_frames = 0;
            int err = max30001_start(&bus, &v1, a, &info);
            printf("%d %06x %d\n", err, (unsigned)info, s_frames);
            flush_log();
        } else if (cmd[0] == 'R') {
            max30001_fifo_t f;
            s_frames = 0;
            s_overread = 0;
            int err = max30001_read_fifo(&bus, &f);
            printf("%d %u %u %d %d %d %d %u %d %d %d", err, f.n, f.samples, f.eof, f.empty,
                   f.overflow, f.bad_tag, f.fast, s_overread, s_frames, s_fifo_pos);
            for (unsigned i = 0; i < f.samples; i++) {
                printf(" %ld:%u:%06x", (long)f.value[i], f.etag[i], (unsigned)f.word[i]);
            }
            printf("\n");
            flush_log();
        } else if (cmd[0] == 'T') {
            int err = max30001_restart(&bus, &v1, between, NULL);
            printf("%d\n", err);
            flush_log();
        } else if (cmd[0] == 'V') {
            const uint32_t *r[2] = {&v1.cnfg_gen, &cal.cnfg_gen};
            for (int k = 0; k < 2; k++) {
                for (int i = 0; i < 8; i++) {
                    printf("%06x%s", (unsigned)r[k][i], i < 7 ? " " : "\n");
                }
            }
        } else if (cmd[0] == 'X') {
            scanf("%x", &a);
            int32_t value;
            uint8_t tag;
            max30001_parse_word(a, &value, &tag);
            printf("%ld %u\n", (long)value, tag);
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
    work = tmp_path_factory.mktemp("max30001")
    (work / "harness.c").write_text(HARNESS, encoding="utf-8")
    exe = work / ("harness.exe" if os.name == "nt" else "harness")
    build = subprocess.run(
        [*compiler, "-std=c99", "-Wall", "-Wextra", "-Werror", "-Wno-unused-result",
         "-I", str(ROOT / "firmware/include"), str(ROOT / "firmware/drivers/max30001.c"),
         str(work / "harness.c"), "-o", str(exe)],
        capture_output=True, text=True,
    )
    assert build.returncode == 0, build.stderr
    return exe


class Chip:
    """One harness process (one simulated chip); each command answers lines."""

    def __init__(self, exe):
        self.proc = subprocess.Popen([str(exe)], stdin=subprocess.PIPE,
                                     stdout=subprocess.PIPE, text=True)

    def __call__(self, line, lines=1):
        self.proc.stdin.write(line + "\n")
        self.proc.stdin.flush()
        return [self.proc.stdout.readline().strip() for _ in range(lines)]

    def start(self, timeout_ms=100):
        result, log = self(f"S {timeout_ms}", 2)
        err, info, frames = result.split()
        return int(err), int(info, 16), int(frames), log.rstrip(";").split(";")

    def read_fifo(self):
        result, log = self("R", 2)
        err, n, samples, eof, empty, overflow, bad, fast, overread, frames, pos = map(
            int, result.split()[:11])
        values = [(int(v), int(t)) for v, t, _ in
                  (p.split(":") for p in result.split()[11:])]
        words = [int(p.split(":")[2], 16) for p in result.split()[11:]]
        return {"err": err, "n": n, "samples": samples, "eof": eof, "empty": empty,
                "overflow": overflow, "bad": bad, "fast": fast, "overread": overread,
                "frames": frames, "popped": pos, "values": values, "words": words,
                "log": log}

    def push(self, value, tag):
        self(f"F {((value & 0x3FFFF) << 6) | (tag << 3):06x}")

    def close(self):
        self.proc.stdin.close()
        assert self.proc.wait(timeout=30) == 0


@pytest.fixture
def chip(harness):
    c = Chip(harness)
    yield c
    c.close()


def test_v1_register_words_match_the_datasheet_tables(chip):
    v1, cal = (line.split() for line in chip("V", 2))
    # Order: CNFG_GEN, CNFG_CAL, CNFG_EMUX, CNFG_ECG, MNGR_INT, MNGR_DYN, EN_INT,
    # EN_INT2. Each word by hand from the decided settings:
    # CNFG_GEN p. 47-49: EN_ECG D19, EN_DCLOFF 01 D13:12, IMAG 010 (10 nA)
    #   D10:8, VTH 01 (400 mV) D7:6, RBIASV default 01 D3:2 -> 0x081244.
    # CNFG_CAL p. 50: FCAL default 100 D14:12, FIFTY D11 -> 0x004800.
    # CNFG_EMUX p. 51: inputs connected (OPENP = OPENN = 0) -> 0x000000.
    # CNFG_ECG p. 52-53: 512 sps 00, gain 20 V/V 00, DHPF 0, DLPF 01 -> 0x001000.
    # MNGR_INT p. 44: EFIT 15 D23:19, BFIT default 011, CLR_SAMP D2 -> 0x7B0004.
    # MNGR_DYN p. 45: FAST 10, FAST_TH 0x3F, BioZ thresholds 0xFF -> 0xBFFFFF.
    # EN_INT p. 43: EN_EINT D23, CMOS 01 -> 0x800001; EN_INT2: EN_SAMP D9 -> 0x000201.
    assert v1 == ["081244", "004800", "000000", "001000", "7b0004", "bfffff",
                  "800001", "000201"]
    # Self test: no lead-off detection or current (EN_DCLOFF 00, IMAG 000; VTH
    # left at 01, unused then), VCAL on/bipolar/0.5 mV/1 Hz/50 % (D22, D21, D20,
    # FCAL 100, FIFTY) and both inputs open on VCALP/VCALN.
    assert cal[:3] == ["080044", "704800", "3b0000"] and cal[3:] == v1[3:]


@pytest.mark.parametrize("word,value,tag", [
    (0x000000, 0, 0), (0x7FFFC0, 131071, 0), (0x800000, -131072, 0),
    (0xFFFFC0, -1, 0), (0x000050, 1, 2), (0x000030, 0, 6), (0x000038, 0, 7),
])
def test_fifo_word_is_18_bit_twos_complement_with_etag(chip, word, value, tag):
    assert chip(f"X {word:06x}") == [f"{value} {tag}"]


def test_start_resets_checks_info_configures_and_waits_for_the_pll(chip):
    chip("P 3")
    err, info, frames, log = chip.start()
    assert (err, info) == (ERR_OK, 0x541000)
    writes = ["W10:081244", "W12:004800", "W14:000000", "W15:001000", "W04:7b0004",
              "W05:bfffff", "W02:800001", "W03:000201"]
    reads = [w[:3].replace("W", "R") for w in writes]
    # Reset, settle, a discarded first read, INFO, writes, read-backs, then
    # STATUS until two reads in a row show no PLLINT (3 latched + 2 clear).
    assert log == (["W08:000000", "D10", "R0f", "R0f"] + writes + reads
                   + ["R01", "D5", "R01", "D5", "R01", "D5", "R01", "D5", "R01"])
    assert frames == len(log) - log.count("D10") - log.count("D5")


@pytest.mark.parametrize("info", ["000000", "641000", "540000"])
def test_start_refuses_a_chip_without_the_max30001_info_pattern(chip, info):
    chip(f"I {info}")
    err, _, _, log = chip.start()
    assert err == ERR_INFO and not any(e.startswith("W1") for e in log)


def test_start_detects_a_wrong_read_back_but_ignores_dont_care_bits(chip, harness):
    chip("C 15 001000")  # DLPF bit of CNFG_ECG reads back flipped.
    assert chip.start()[0] == ERR_READBACK
    other = Chip(harness)
    other("C 15 000100")  # D8 of CNFG_ECG is a don't-care bit.
    assert other.start()[0] == ERR_OK
    other.close()


def test_check_reads_info_and_every_register_back(chip, harness):
    assert chip.start()[0] == ERR_OK
    result, log = chip("H", 2)
    assert result == str(ERR_OK)
    # INFO, then the eight registers in write order; nothing is written.
    assert log.rstrip(";").split(";") == ["R0f", "R10", "R12", "R14", "R15", "R04",
                                          "R05", "R02", "R03"]
    chip("C 03 000200")  # EN_SAMP of EN_INT2 reads back flipped
    assert chip("H", 2)[0] == str(ERR_READBACK)
    other = Chip(harness)
    assert other.start()[0] == ERR_OK
    other("Z")  # a brownout: registers back to 0, the chip silent
    assert other("H", 2)[0] == str(ERR_READBACK)
    other("I 000000")
    assert other("H", 2)[0] == str(ERR_INFO)
    other.close()


def test_start_times_out_when_the_pll_never_locks(chip):
    chip("P 1000")
    err, _, _, log = chip.start(timeout_ms=20)
    assert err == ERR_PLL and log.count("R01") == 5  # at 0, 5, 10, 15 and 20 ms


def test_fifo_burst_stops_on_the_eof_word_and_never_reads_beyond(chip):
    values = [0, 1, -1, 131071, -131072] + list(range(10, 20))
    for v in values:
        chip.push(v, VALID)
    chip.push(-5, VALID_EOF)
    for v in range(3):  # samples that arrive later: not to be read now
        chip.push(100 + v, VALID)
    r = chip.read_fifo()
    assert (r["err"], r["n"], r["samples"], r["eof"], r["overread"], r["frames"]) == (
        ERR_OK, 16, 16, 1, 0, 1)
    assert r["popped"] == 16 and r["log"] == "B;"
    assert r["values"] == [(v, VALID) for v in values] + [(-5, VALID_EOF)]
    # The packet keeps the raw word, tags included (schema V0.1 section 8).
    assert r["words"][-1] == ((-5 & 0x3FFFF) << 6) | (VALID_EOF << 3)


def test_fifo_empty_overflow_fast_and_unused_tags(harness):
    cases = [
        ([(0, EMPTY)], {"samples": 0, "empty": 1, "n": 1}),
        ([(1, VALID), (2, VALID), (3, OVERFLOW)], {"samples": 2, "overflow": 1, "n": 3}),
        ([(1, FAST), (2, VALID), (3, FAST_EOF), (4, VALID)],
         {"samples": 3, "fast": 2, "eof": 1, "n": 3}),
        ([(1, VALID), (2, 4)], {"samples": 1, "bad": 1, "n": 2}),
        ([(k, VALID) for k in range(40)], {"samples": 32, "eof": 0, "n": 32}),
    ]
    for words, expected in cases:
        c = Chip(harness)
        for value, tag in words:
            c.push(value, tag)
        r = c.read_fifo()
        assert r["err"] == ERR_OK and r["overread"] == 0
        assert {k: r[k] for k in expected} == expected, words
        c.close()


def test_restart_masks_samp_around_the_callback_and_synch(chip):
    assert chip("T", 2) == ["0", "W03:000001;CB;W09:000000;W03:000201;"]
