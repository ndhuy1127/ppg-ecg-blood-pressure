"""Compile and run the firmware SAMP mapping on the host.

firmware/app/samp_map.c has no ESP-IDF dependency. A harness keeps an edge
table numbered like the capture callback (edge e = the e-th captured edge since
the last clear) and drives the mapping. The answers come from Packet Schema V0.2
sections 7.2-7.3 and the restart policy decided on 2026-10-24 (1 s after an
error, at most once per 10 s). The last test runs a fake ECG timeline with the
faults of the firmware's FAKE_SAMP_FAULTS mode through the mapping and the
logger; its reader loop is a Python copy of ecg_reader_task, so it checks the
mapping, bit 8 and bit 5 against the logger, not the C stop/restart sequence,
the polling wait or the 64-slot ring (those run only on the MCU). SYNTHETIC
only; no MCU, capture or MAX30001 is involved. Without a host C compiler the
test is skipped, like test_firmware_c_encoder.py.
"""

import json
import os
import random
import subprocess
from fractions import Fraction
from pathlib import Path

import pytest

from software.data_io.packet_receiver import analyze_stream
from software.data_io.packet_wire import Packet, decode_bytes, encode_packet
from tests.test_firmware_c_encoder import _compiler

ROOT = Path(__file__).resolve().parents[1]
LOGGER = json.loads((ROOT / "configs/hardware/packet_logger.json").read_bytes())
T = Fraction(10 ** 9, 512_000)  # 1953.125 us
OK, IN_ERROR, INDEX, EDGE_MISSING, SHORT, LONG, OVERFLOW, LATE = range(8)
NO_DEADLINE = 1 << 62
BIT0, BIT4, BIT5, BIT8 = 1 << 0, 1 << 4, 1 << 5, 1 << 8

HARNESS = r"""
#include <stdio.h>
#include <string.h>

#include "samp_map.h"

#define TABLE 8192
static long long s_t[TABLE];
static int s_have[TABLE];
static unsigned s_next;

static bool lookup(void *ctx, uint32_t e, int64_t *t_us)
{
    (void)ctx;
    if (e >= TABLE || !s_have[e]) {
        return false;
    }
    *t_us = s_t[e];
    return true;
}

int main(void)
{
    samp_map_t m;
    samp_map_init(&m, 512000, 22000, 1000000, 10000000);
    char cmd[2];
    while (scanf("%1s", cmd) == 1) {
        long long a = 0, b = 0, c = 0;
        if (cmd[0] == 'S') {          /* restart at time a; the ring is cleared */
            scanf("%lld", &a);
            memset(s_have, 0, sizeof(s_have));
            s_next = 0;
            samp_map_restart(&m, a);
            printf("s\n");
        } else if (cmd[0] == 'E') {   /* the next captured edge, at time a */
            scanf("%lld", &a);
            s_t[s_next] = a;
            s_have[s_next++] = 1;
            printf("e\n");
        } else if (cmd[0] == 'D') {   /* edge a left the ring */
            scanf("%lld", &a);
            s_have[a] = 0;
            printf("d\n");
        } else if (cmd[0] == 'P') {   /* packet k_first a, n b, deadline d, at time c */
            long long d = 0;
            scanf("%lld %lld %lld %lld", &a, &b, &d, &c);
            int64_t anchor = -1;
            samp_result_t r = samp_map_packet(&m, (uint32_t)a, (uint16_t)b, lookup, NULL, d,
                                              c, &anchor);
            printf("%d %lld %d\n", (int)r, (long long)anchor, (int)m.state);
        } else if (cmd[0] == 'O') {   /* FIFO overflow found at time a */
            scanf("%lld", &a);
            samp_map_error(&m, SAMP_OVERFLOW, a);
            printf("o\n");
        } else if (cmd[0] == 'Q') {   /* may the mapping restart at time a? */
            scanf("%lld", &a);
            printf("%d\n", samp_map_restart_due(&m, a) ? 1 : 0);
        } else if (cmd[0] == 'C') {
            printf("%lu %lu %lu %llu", (unsigned long)m.packets_samp,
                   (unsigned long)m.packets_fifo, (unsigned long)m.remaps,
                   (unsigned long long)m.period_ns);
            for (int i = 0; i < SAMP_RESULTS; i++) {
                printf(" %lu", (unsigned long)m.results[i]);
            }
            printf("\n");
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
    work = tmp_path_factory.mktemp("samp_map")
    (work / "harness.c").write_text(HARNESS, encoding="utf-8")
    exe = work / ("harness.exe" if os.name == "nt" else "harness")
    build = subprocess.run(
        [*compiler, "-std=c99", "-Wall", "-Wextra", "-Werror", "-Wno-unused-result",
         "-I", str(ROOT / "firmware/include"), str(ROOT / "firmware/app/samp_map.c"),
         str(work / "harness.c"), "-o", str(exe)],
        capture_output=True, text=True,
    )
    assert build.returncode == 0, build.stderr
    return exe


class Map:
    """One harness process; each command answers one line."""

    def __init__(self, exe):
        self.proc = subprocess.Popen([str(exe)], stdin=subprocess.PIPE,
                                     stdout=subprocess.PIPE, text=True)

    def __call__(self, line):
        self.proc.stdin.write(line + "\n")
        self.proc.stdin.flush()
        return self.proc.stdout.readline().strip()

    def edges(self, times):
        for t in times:
            self(f"E {t}")

    def packet(self, k, n, now=0, deadline=NO_DEADLINE):
        r, anchor, state = map(int, self(f"P {k} {n} {deadline} {now}").split())
        return r, anchor, state

    def counters(self):
        samp, fifo, remaps, period, *results = map(int, self("C").split())
        return samp, fifo, remaps, period, results

    def close(self):
        self.proc.stdin.close()
        assert self.proc.wait(timeout=30) == 0


@pytest.fixture
def m(harness):
    mapping = Map(harness)
    mapping("S 0")
    yield mapping
    mapping.close()


def sample_time(k, start=1_000_000, jitter=0):
    return round(start + k * T) + jitter


def test_period_and_valid_packets(m):
    times = [sample_time(k, jitter=k % 4) for k in range(64)]
    m.edges(times)
    for k in range(0, 64, 16):
        assert m.packet(k, 16) == (OK, times[k + 15], 1)
    samp, fifo, remaps, period, results = m.counters()
    assert (samp, fifo, remaps, period) == (4, 0, 0, 1_953_125)
    assert results == [0] * 9  # one counter per samp_result_t, SAMP_AFE included


@pytest.mark.parametrize("late,expected", [(0, OK), (1, LATE)])
def test_last_edge_after_the_bounded_wait_is_late(m, late, expected):
    # Section 7.3: wait at most two sample periods after the FIFO read for the
    # edge of the last sample; an edge 1 us after that deadline is not used.
    times = [sample_time(k) for k in range(16)]
    m.edges(times)
    r, anchor, state = m.packet(0, 16, deadline=times[15] - late)
    assert (r, state) == (expected, 1 if expected == OK else 2)
    assert m.counters()[4][LATE] == (expected == LATE)


def test_first_packet_needs_edge_zero(m):
    m.edges(sample_time(k) for k in range(16))
    m("D 0")
    assert m.packet(0, 16)[::2] == (EDGE_MISSING, 2)


def test_missed_edge_shifts_the_numbering(m):
    # Sample 20's edge is not captured: the callback gives edge 20 to sample 21,
    # so the interval from edge 19 to edge 20 is two periods.
    m.edges(sample_time(k) for k in range(48) if k != 20)
    assert m.packet(0, 16)[0] == OK
    assert m.packet(16, 16)[0] == LONG
    assert m.counters()[4][LONG] == 1


def test_extra_edge(m):
    times = [sample_time(k) for k in range(48)]
    m.edges(times[:21] + [times[20] + 976] + times[21:])
    assert m.packet(0, 16)[0] == OK
    assert m.packet(16, 16)[0] == SHORT


def test_missed_plus_extra_keep_the_count_but_not_the_intervals(m):
    times = [sample_time(k) for k in range(48)]
    edges = times[:20] + times[21:26] + [times[25] + 976] + times[26:]
    assert len(edges) == 48
    m.edges(edges)
    assert m.packet(0, 16)[0] == OK
    assert m.packet(16, 16)[0] == LONG  # the first odd interval in the span


def test_edge_not_yet_captured_or_left_the_ring(harness):
    for drop in (None, 20):
        mapping = Map(harness)
        mapping("S 0")
        mapping.edges(sample_time(k) for k in range(31 if drop is None else 32))
        assert mapping.packet(0, 16)[0] == OK
        if drop is not None:
            mapping(f"D {drop}")
        assert mapping.packet(16, 16)[0] == EDGE_MISSING
        mapping.close()


def test_packet_must_continue_the_previous_one(m):
    m.edges(sample_time(k) for k in range(64))
    assert m.packet(0, 16)[0] == OK
    assert m.packet(20, 16)[0] == INDEX


@pytest.mark.parametrize("interval,expected", [
    (1975, OK), (1976, LONG), (1932, OK), (1931, SHORT),
])
def test_interval_tolerance_bounds(m, interval, expected):
    # T = 1 953 125 ns, tolerance 22 000 ns: accepted 1 931 125 .. 1 975 125 ns.
    times = [1_000_000 + 1953 * k for k in range(9)]
    times += [times[-1] + interval + 1953 * k for k in range(7)]
    m.edges(times)
    assert m.packet(0, 16)[0] == expected


def test_error_state_sticks_and_counts_its_cause_once(m):
    m.edges(sample_time(k) for k in range(64) if k != 20)
    assert m.packet(0, 16)[0] == OK
    assert m.packet(16, 16)[0] == LONG
    assert m.packet(32, 16)[0] == IN_ERROR
    m("O 0")
    samp, fifo, _, _, results = m.counters()
    assert (samp, fifo) == (1, 2)
    assert results[LONG] == 1 and results[OVERFLOW] == 0  # already in error


def test_overflow_enters_the_error_state(m):
    m.edges(sample_time(k) for k in range(32))
    m("O 5")
    assert m.packet(0, 16)[0] == IN_ERROR
    assert m.counters()[4][OVERFLOW] == 1


def test_restart_policy(harness):
    mapping = Map(harness)
    assert mapping("Q 0") == "0"  # nothing started yet
    mapping("S 0")                # boot: does not count for the 10 s gap
    mapping.edges(sample_time(k) for k in range(16) if k != 3)
    assert mapping.packet(0, 16, now=500_000)[0] == LONG
    assert mapping("Q 1499999") == "0"
    assert mapping("Q 1500000") == "1"  # 1 s after the error
    mapping("S 1500000")
    assert mapping.counters()[2] == 1
    mapping.edges(sample_time(k, start=2_000_000) for k in range(16) if k != 3)
    assert mapping.packet(0, 16, now=3_000_000)[0] == LONG
    assert mapping("Q 4000000") == "0"   # 1 s after, but 2.5 s after a restart
    assert mapping("Q 11499999") == "0"
    assert mapping("Q 11500000") == "1"  # 10 s after the last restart
    mapping("S 11500000")
    mapping.edges(sample_time(k, start=12_000_000) for k in range(16))
    assert mapping.packet(0, 16, now=12_100_000)[0] == OK  # new epoch from edge 0
    assert mapping("Q 30000000") == "0"  # mapped: nothing to restart
    mapping.close()


def fake_ecg(harness, duration_us, drop_every=20_000_000, seed=9):
    """Packets of the firmware ECG reader with FAKE_SAMP_FAULTS, made in Python
    as in firmware/app/main.c (ecg_reader_task, fake_samp_edge) and
    firmware/drivers/fake_afe.c; the mapping is the C code."""
    rng = random.Random(seed)
    mapping = Map(harness)
    period = 1953
    start, k_read, made, restart_bits = 0, 0, 0, 0
    lcg, drop_at, extra_at = 1, 5_000_000, 15_000_000
    mapping(f"S {start}")
    packets, seq, restarts = [], 0, 0
    while True:
        # Sample k exists at start + (k + 1) * period; the reader wakes when 16
        # samples wait, 20..400 us late.
        t_read = start + (k_read + 16) * period + rng.randint(20, 400)
        if t_read > duration_us:
            break
        while start + (made + 1) * period <= t_read:  # edges of the new samples
            lcg = (lcg * 1664525 + 1013904223) % (1 << 32)
            t = start + (made + 1) * period + (lcg >> 30)
            made += 1
            if t >= drop_at:
                drop_at += drop_every
                continue
            if t >= extra_at:
                extra_at += drop_every
                mapping(f"E {t - period // 2}")
            mapping(f"E {t}")
        count = made - k_read
        r, edge, _ = mapping.packet(k_read, count, now=t_read,
                                    deadline=t_read + 2 * 1953)
        status = BIT4 | restart_bits | (BIT8 if r == OK else 0)
        restart_bits = 0
        anchor = edge if r == OK else t_read
        data = tuple((((k_read + i) % 2048 - 1024) & 0x3FFFF) << 6 for i in range(count))
        packets.append(Packet(2, 0xE1, 1, seq, k_read, anchor,
                              anchor - round((count - 1) * T), 512_000, status, data))
        seq, k_read = seq + 1, made
        if mapping(f"Q {t_read}") == "1":
            # Stop, clear the ring, SYNCH: index and edges from 0, time goes on.
            start, k_read, made, restart_bits = t_read, 0, 0, BIT5
            mapping(f"S {t_read}")
            restarts += 1
    counters = mapping.counters()
    mapping.close()
    return packets, restarts, counters


def test_fake_ecg_with_samp_faults_through_the_logger(harness):
    packets, restarts, (samp, fifo, remaps, _, results) = fake_ecg(harness, 40_000_000)
    # Faults at 5, 15, 25, 35 s; restarts 1 s later but at most once per 10 s.
    assert restarts == remaps == 4
    assert results[LONG] == 2 and results[SHORT] == 2
    assert samp + fifo == len(packets)
    stream = b"".join(encode_packet(p) for p in packets)
    decoded, decoder = decode_bytes(stream, 4096, (1, 2))
    result, _, samples = analyze_stream(decoded, decoder, LOGGER, _metadata())
    # Each restart is a new chain (bit 5, index from 0); no anchor is out of
    # line within either source, and SAMP never comes back without bit 5.
    assert result["issue_counts"] == {"sample_index_reanchored": 4}
    ecg = result["sessions"][0]["channels"]["0xE1"]
    assert ecg["chains"] == 5
    assert ecg["anchor_sources"]["samp"] == samp
    assert ecg["anchor_sources"]["fifo_read"] == fifo
    assert len(ecg["anchor_sources"]["switch_seqs"]) == 8
    for _, _, _, _, index, value, _ in samples:
        assert value == (((index % 2048) - 1024) & 0x3FFFF) << 6


def _metadata():
    spec = {"sensor": "SYN_fake_ecg", "fs_nominal_mhz": 512_000, "latency_l_us": None,
            "latency_source": None, "unit_conversion": None, "afe_config": None,
            "latency_samp_l_us": None, "latency_samp_source": None}
    reasons = {f"channels.0xE1.{name}": "SYNTHETIC firmware emulation"
               for name, value in spec.items() if value is None}
    text = ("firmware_version", "firmware_commit", "device_id", "operator",
            "electrode_type", "electrode_placement")
    reasons.update({name: "SYNTHETIC firmware emulation" for name in text})
    return {"schema_version": "packet-session-metadata-v0", "source_type": "SYNTHETIC",
            "clock_id": "ESP32_ESP_TIMER_US", **dict.fromkeys(text),
            "channels": {"0xE1": spec}, "simulation": None, "null_reasons": reasons}
