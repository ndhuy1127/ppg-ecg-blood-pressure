"""Compile the ECG rate check (firmware/app/ecg_rate.c) and check its rule.

The rule comes from hardware/test_reports/sync_10min_test_plan.md section 11.3
(decided 2026-11-21): over each window of at least 10 s of reliable FIFO-read
anchors, the samples counted from the index must match the esp_timer time within
512 sps +- 1 000 ppm; a reset forgets the window. SYNTHETIC only. Without a host
C compiler the test is skipped.
"""

import os
import subprocess
from pathlib import Path

import pytest

from tests.test_firmware_c_encoder import _compiler

ROOT = Path(__file__).resolve().parents[1]
FS_MHZ, TOL_PPM, WINDOW_US = 512_000, 1000, 10_000_000
PERIOD_US = 1e9 / FS_MHZ

HARNESS = r"""
#include <stdio.h>

#include "ecg_rate.h"

/* P k t: packet, prints fault last_ppm*1000 windows faults;  R: reset */
int main(void)
{
    ecg_rate_t r;
    ecg_rate_init(&r);
    char op;
    while (scanf(" %c", &op) == 1) {
        if (op == 'R') {
            ecg_rate_reset(&r);
            printf("ok\n");
        } else if (op == 'P') {
            unsigned long k;
            long long t;
            if (scanf("%lu %lld", &k, &t) != 2) {
                return 2;
            }
            int fault = ecg_rate_packet(&r, (uint32_t)k, t, 512000u, 1000u, 10000000LL);
            printf("%d %lld %u %u\n", fault, (long long)(r.last_ppm * 1000.0), r.windows,
                   r.faults);
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
    work = tmp_path_factory.mktemp("ecg_rate")
    (work / "harness.c").write_text(HARNESS, encoding="utf-8")
    exe = work / ("harness.exe" if os.name == "nt" else "harness")
    build = subprocess.run(
        [*compiler, "-std=c99", "-Wall", "-Wextra", "-Werror", "-Wno-unused-result",
         "-I", str(ROOT / "firmware/include"), str(ROOT / "firmware/app/ecg_rate.c"),
         str(work / "harness.c"), "-o", str(exe)],
        capture_output=True, text=True,
    )
    assert build.returncode == 0, build.stderr
    return exe


class Rate:
    def __init__(self, exe):
        self.proc = subprocess.Popen([str(exe)], stdin=subprocess.PIPE,
                                     stdout=subprocess.PIPE, text=True)

    def packet(self, k, t):
        self.proc.stdin.write(f"P {k % 2**32} {round(t)}\n")
        self.proc.stdin.flush()
        fault, milli_ppm, windows, faults = map(int, self.proc.stdout.readline().split())
        return bool(fault), milli_ppm / 1000, windows, faults

    def reset(self):
        self.proc.stdin.write("R\n")
        self.proc.stdin.flush()
        assert self.proc.stdout.readline().strip() == "ok"

    def close(self):
        self.proc.stdin.close()
        assert self.proc.wait(timeout=30) == 0


@pytest.fixture
def rate(harness):
    r = Rate(harness)
    yield r
    r.close()


def run(rate, seconds, ppm=0.0, k0=15, t0=1_000_000.0, jitter=(0, 120, 37, 200)):
    """Packets of 16 samples from a chip whose sampling FREQUENCY is off by ``ppm``
    (positive = faster: shorter period), with small anchor jitter."""
    out = []
    for n in range(int(seconds * 32)):
        k = k0 + 16 * n
        t = t0 + (k - k0) * PERIOD_US / (1 + ppm * 1e-6) + jitter[n % len(jitter)]
        out.append(rate.packet(k, t))
    return out


def test_nominal_rate_passes_one_window_every_10_s(rate):
    out = run(rate, 35)
    assert not any(fault for fault, *_ in out)
    assert out[-1][2] == 3  # windows completed at 10, 20, 30 s
    assert abs(out[-1][1]) < 50  # jitter of 0.2 ms over 10 s is 20 ppm


@pytest.mark.parametrize("ppm, faults", [(900, 0), (-900, 0), (999, 0), (-999, 0),
                                         (1001, 1), (-1001, 1), (1100, 1), (-1100, 1),
                                         (5000, 1)])
def test_rate_outside_1000_ppm_is_a_fault(rate, ppm, faults):
    out = run(rate, 11, ppm=ppm, jitter=(0,))
    assert out[-1][3] == faults
    # Sign: positive when the chip samples faster than 512 sps.
    assert out[-1][1] == pytest.approx(ppm, abs=0.5)


def test_index_wraps_modulo_2_32(rate):
    out = run(rate, 11, k0=2**32 - 1000)
    assert out[-1][2] == 1 and out[-1][3] == 0


def test_reset_forgets_the_window(rate):
    run(rate, 6)
    rate.reset()
    # A jump of time after the reset (re-anchor): no fault, a fresh window.
    out = run(rate, 11, t0=50_000_000.0)
    assert out[-1][2] == 1 and out[-1][3] == 0


def test_time_not_advancing_is_a_fault(rate):
    rate.packet(15, 1_000_000)
    fault, _, windows, faults = rate.packet(31, 1_000_000)
    assert fault and windows == 1 and faults == 1
