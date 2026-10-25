"""Compile the ECG read decision (firmware/app/ecg_read.c) and check its rules.

ecg_read_plan decides, for one MAX30001 FIFO drain, the packet to send, its
index and STATUS, the FIFO reset and the SAMP mapping error. The answers come
from Packet Schema V0.1 sections 5.2, 8, 9 and V0.2 sections 5 and 7 (bits 0, 2,
3, 5; re-anchor FIRST_next = max(last_prev + 1, I_ref + q - (M - 1)) with
q = round_half_up(elapsed / T)), not from the code. SYNTHETIC only: no chip, no
SPI, no task. Without a host C compiler the test is skipped.
"""

import os
import subprocess
from pathlib import Path

import pytest

from tests.test_firmware_c_encoder import _compiler

ROOT = Path(__file__).resolve().parents[1]
BIT0, BIT2, BIT3, BIT4, BIT5 = 1 << 0, 1 << 2, 1 << 3, 1 << 4, 1 << 5
DCLOFFINT, EOVF, PLLINT = 1 << 20, 1 << 22, 1 << 8
# samp_result_t values (samp_map.h): SAMP_INDEX, SAMP_OVERFLOW, SAMP_AFE.
INDEX_CAUSE, OVERFLOW_CAUSE, AFE_CAUSE = 2, 6, 8

HARNESS = r"""
#include <stdio.h>
#include <string.h>

#include "ecg_read.h"

int main(void)
{
    ecg_read_t r = {0};
    char cmd[2];
    while (scanf("%1s", cmd) == 1) {
        if (cmd[0] == 'I') {
            int restarted = 0;
            scanf("%d", &restarted);
            ecg_read_init(&r, restarted != 0);
            printf("ok\n");
        } else if (cmd[0] == 'R') {
            unsigned samples, eof, empty, overflow, bad, bus_ok, status;
            unsigned long long t;
            scanf("%u %u %u %u %u %u %x %llu", &samples, &eof, &empty, &overflow, &bad,
                  &bus_ok, &status, &t);
            max30001_fifo_t f;
            memset(&f, 0, sizeof(f));
            f.samples = (uint16_t)samples;
            f.eof = eof;
            f.empty = empty;
            f.overflow = overflow;
            f.bad_tag = bad;
            ecg_read_plan_t p = ecg_read_plan(&r, &f, bus_ok != 0, status, t, 512000, 0x10);
            printf("%d %lu %u %u %d %d %d\n", p.send, (unsigned long)p.chunk.first_index,
                   p.chunk.count, p.chunk.status, p.fifo_reset, p.mapping_error,
                   p.mapping_error ? (int)p.cause : -1);
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
    work = tmp_path_factory.mktemp("ecg_read")
    (work / "harness.c").write_text(HARNESS, encoding="utf-8")
    exe = work / ("harness.exe" if os.name == "nt" else "harness")
    sources = [ROOT / "firmware/app" / name
               for name in ("ecg_read.c", "imu_plan.c", "packet_wire.c")]
    build = subprocess.run(
        [*compiler, "-std=c99", "-Wall", "-Wextra", "-Werror", "-Wno-unused-result",
         "-I", str(ROOT / "firmware/include"), *map(str, sources),
         str(work / "harness.c"), "-o", str(exe)],
        capture_output=True, text=True,
    )
    assert build.returncode == 0, build.stderr
    return exe


class Reader:
    def __init__(self, exe, restarted=False):
        self.proc = subprocess.Popen([str(exe)], stdin=subprocess.PIPE,
                                     stdout=subprocess.PIPE, text=True)
        self("I 0")  # boot
        if restarted:
            self("I 1")  # a later SYNCH, with nothing pending

    def __call__(self, line):
        self.proc.stdin.write(line + "\n")
        self.proc.stdin.flush()
        return self.proc.stdout.readline().split()

    def read(self, samples, t_us, eof=True, empty=False, overflow=False, bad=False,
             bus_ok=True, status=0):
        send, first, count, st, reset, err, cause = map(int, self(
            f"R {samples} {int(eof)} {int(empty)} {int(overflow)} {int(bad)} "
            f"{int(bus_ok)} {status:x} {t_us}"))
        return {"send": send, "first": first, "count": count, "status": st,
                "reset": reset, "error": err, "cause": cause}

    def close(self):
        self.proc.stdin.close()
        assert self.proc.wait(timeout=30) == 0


@pytest.fixture
def ecg(harness):
    r = Reader(harness)
    yield r
    r.close()


T_US = 1e6 / 512  # 1953.125 us


def test_clean_reads_continue_the_index_with_base_status_only(ecg):
    first = ecg.read(16, 1_000_000)
    second = ecg.read(16, 1_031_250)
    assert first == {"send": 1, "first": 0, "count": 16, "status": BIT4, "reset": 0,
                     "error": 0, "cause": -1}
    assert (second["first"], second["status"], second["error"]) == (16, BIT4, 0)


def test_lead_off_and_pll_flags_survive_an_empty_read(ecg):
    ecg.read(16, 1_000_000)
    empty = ecg.read(0, 1_010_000, eof=False, empty=True, status=DCLOFFINT | PLLINT)
    assert (empty["send"], empty["error"], empty["cause"]) == (0, 1, AFE_CAUSE)
    flagged = ecg.read(16, 1_031_250)
    assert flagged["status"] == BIT4 | BIT2 | BIT3 and flagged["first"] == 16
    assert ecg.read(16, 1_062_500)["status"] == BIT4  # sent once, then cleared


@pytest.mark.parametrize("how", ["tag", "eovf"])
def test_overflow_drops_the_drain_resets_and_reanchors_by_time(ecg, how):
    ecg.read(16, 1_000_000)  # reliable: last index 15 at 1.000000 s
    dropped = ecg.read(5, 1_040_000, overflow=how == "tag",
                       status=EOVF if how == "eovf" else 0)
    assert (dropped["send"], dropped["reset"], dropped["error"],
            dropped["cause"]) == (0, 1, 1, OVERFLOW_CAUSE)
    nxt = ecg.read(16, 1_100_000)
    # q = round_half_up(100000 / 1953.125) = round(51.2) = 51;
    # FIRST = max(16, 15 + 51 - 15) = 51 (V0.2 section 5).
    assert nxt["first"] == 51 and nxt["status"] == BIT4 | BIT0 | BIT5
    assert (nxt["error"], nxt["cause"]) == (1, INDEX_CAUSE)


def test_unused_tag_and_spi_failure_are_read_failures(ecg, harness):
    ecg.read(16, 1_000_000)
    bad = ecg.read(3, 1_031_250, eof=False, bad=True)
    assert (bad["send"], bad["reset"], bad["error"], bad["cause"]) == (0, 1, 1, AFE_CAUSE)
    assert ecg.read(16, 1_062_500)["status"] == BIT4 | BIT3 | BIT5
    other = Reader(harness)
    other.read(16, 1_000_000)
    failed = other.read(16, 1_031_250, bus_ok=False)
    assert (failed["send"], failed["reset"], failed["error"], failed["cause"]) == (
        0, 0, 1, AFE_CAUSE)
    assert other.read(16, 1_062_500)["status"] == BIT4 | BIT3 | BIT5
    other.close()


def test_drain_without_eof_is_a_full_read_and_the_next_reanchors(ecg):
    ecg.read(16, 1_000_000)
    full = ecg.read(32, 1_080_000, eof=False)
    # Valid samples, but the anchor has no bound: bit 0, index continues.
    assert (full["send"], full["first"], full["status"], full["error"]) == (
        1, 16, BIT4 | BIT0, 0)
    nxt = ecg.read(16, 1_120_000)
    # Re-anchor from the last reliable read (15 at 1.0 s): q = round(61.44) = 61,
    # FIRST = max(48, 15 + 61 - 15) = 61.
    assert nxt["first"] == 61 and nxt["status"] == BIT4 | BIT5
    assert nxt["cause"] == INDEX_CAUSE


def test_restarted_epoch_starts_at_zero_with_bit5_and_keeps_the_mapping(harness):
    r = Reader(harness, restarted=True)
    first = r.read(16, 5_000_000)
    assert (first["first"], first["status"], first["error"]) == (0, BIT4 | BIT5, 0)
    assert r.read(16, 5_031_250)["status"] == BIT4
    r.close()


def test_bad_tag_with_eovf_keeps_the_overflow_evidence(ecg):
    ecg.read(16, 1_000_000)
    both = ecg.read(3, 1_031_250, eof=False, bad=True, status=EOVF)
    assert (both["send"], both["reset"], both["cause"]) == (0, 1, OVERFLOW_CAUSE)
    assert ecg.read(16, 1_062_500)["status"] == BIT4 | BIT0 | BIT3 | BIT5


@pytest.mark.parametrize("fault,bits", [
    ({"samples": 5, "overflow": True}, BIT0),
    ({"samples": 0, "eof": False, "empty": True, "status": DCLOFFINT}, BIT2),
    ({"samples": 16, "bus_ok": False}, BIT3),
])
def test_a_restart_keeps_the_flags_not_sent_yet(ecg, fault, bits):
    ecg.read(16, 1_000_000)
    samples = fault.pop("samples")
    ecg.read(samples, 1_031_250, **fault)
    ecg("I 1")  # the SYNCH of a mapping restart succeeded
    first = ecg.read(16, 1_100_000)
    assert first["first"] == 0 and first["status"] == BIT4 | BIT5 | bits
    assert ecg.read(16, 1_131_250)["status"] == BIT4
