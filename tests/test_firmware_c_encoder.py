"""Compile and run the firmware C encoder on the host.

firmware/app/packet_v01.c has no ESP-IDF dependency, so a host compiler can
build it with a small harness. The harness repeats the boot self-test against
firmware/include/packet_kat.h and encodes seeded random packets, whose bytes
must equal software/data_io/packet_wire.encode_packet. The compiler is taken
from $CC, else cc/gcc/clang; without one the test is skipped (CI on Ubuntu has
gcc). A build or run failure is a test failure, not a skip. This checks the
encoder only: not the ISR, tasks, USB or hardware.
"""

import os
import random
import shlex
import shutil
import subprocess
from dataclasses import replace
from pathlib import Path

import pytest

from software.data_io.packet_wire import Packet, encode_packet

ROOT = Path(__file__).resolve().parents[1]
CHANNELS = (0xE1, 0xF1, 0xF2, 0xF3, 0xF4, 0xC1)
INT32 = (-(1 << 31), (1 << 31) - 1)

HARNESS = r"""
#include <stdio.h>
#include <string.h>

#include "packet_kat.h"
#include "packet_v01.h"

static int kat(void)
{
    const char *text = KAT_CRC_INPUT;
    uint16_t crc = pkt_crc16_ccitt_false((const uint8_t *)text, strlen(text));
    if (crc != KAT_CRC_EXPECTED) {
        return 0;
    }
    if (pkt_t_first_us(KAT_T_ANCHOR_US, 2, KAT_FS_NOMINAL_MHZ) != KAT_T_FIRST_US) {
        return 0;
    }
    const pkt_t p = {
        .channel_id = KAT_CHANNEL_ID, .session_id = KAT_SESSION_ID, .seq = KAT_SEQ,
        .first_sample_index = KAT_FIRST_SAMPLE_INDEX, .t_anchor_us = KAT_T_ANCHOR_US,
        .t_first_us = KAT_T_FIRST_US, .fs_nominal_mhz = KAT_FS_NOMINAL_MHZ,
        .sample_count = 2, .status = KAT_STATUS, .data = {KAT_DATA_0, KAT_DATA_1},
    };
    uint8_t buf[PKT_MAX_SIZE];
    size_t n = pkt_encode(&p, buf, sizeof(buf));
    return n == sizeof(KAT_PACKET) && memcmp(buf, KAT_PACKET, n) == 0;
}

int main(void)
{
    printf("kat %d\n", kat());
    unsigned ch, n, status, cap;
    unsigned long session, seq, first, fs;
    unsigned long long anchor, t_first;
    while (scanf("%u %lu %lu %lu %llu %llu %lu %u %u %u", &ch, &session, &seq, &first,
                 &anchor, &t_first, &fs, &status, &cap, &n) == 10) {
        pkt_t p;
        memset(&p, 0, sizeof(p));
        p.channel_id = (uint8_t)ch;
        p.session_id = (uint32_t)session;
        p.seq = (uint32_t)seq;
        p.first_sample_index = (uint32_t)first;
        p.t_anchor_us = anchor;
        p.t_first_us = t_first;
        p.fs_nominal_mhz = (uint32_t)fs;
        p.status = (uint16_t)status;
        p.sample_count = (uint16_t)n;
        for (unsigned i = 0; i < n; i++) {
            long long value;
            if (scanf("%lld", &value) != 1) {
                return 2;
            }
            if (i < PKT_MAX_SAMPLES) {
                p.data[i] = (int32_t)value;
            }
        }
        uint8_t buf[PKT_MAX_SIZE + 8];
        memset(buf, 0xEE, sizeof(buf));
        size_t size = pkt_encode(&p, buf, cap);
        printf("%u ", (unsigned)size);
        for (size_t i = 0; i < sizeof(buf); i++) {
            printf("%02x", buf[i]);
        }
        printf(" %llu\n", (unsigned long long)pkt_t_first_us(anchor, (uint16_t)n,
                                                             (uint32_t)fs));
    }
    return 0;
}
"""


def _compiler():
    command = os.environ.get("CC")
    if command:
        # A bare path is used as is: POSIX splitting would eat the backslashes
        # of a Windows path. Otherwise split a command such as
        # '"C:\py\python.exe" -m ziglang cc', keeping Windows backslashes.
        if Path(command).is_file():
            return [command]
        parts = shlex.split(command, posix=os.name != "nt")
        return [p[1:-1] if len(p) > 1 and p[0] == p[-1] == '"' else p
                for p in parts]
    for name in ("cc", "gcc", "clang"):
        path = shutil.which(name)
        if path:
            return [path]
    return None


def test_cc_path_and_quoted_command_keep_backslashes(tmp_path, monkeypatch):
    exe = tmp_path / "bin dir" / "gcc.exe"
    exe.parent.mkdir()
    exe.write_bytes(b"")
    monkeypatch.setenv("CC", str(exe))
    assert _compiler() == [str(exe)]
    monkeypatch.setenv("CC", f'"{exe}" -m ziglang cc')
    assert _compiler() == [str(exe), "-m", "ziglang", "cc"]


@pytest.fixture(scope="module")
def harness(tmp_path_factory):
    compiler = _compiler()
    if compiler is None:
        pytest.skip("no host C compiler ($CC, cc, gcc or clang)")
    work = tmp_path_factory.mktemp("c_encoder")
    (work / "harness.c").write_text(HARNESS, encoding="utf-8")
    exe = work / ("harness.exe" if os.name == "nt" else "harness")
    build = subprocess.run(
        [*compiler, "-std=c99", "-Wall", "-Wextra", "-Werror",
         "-I", str(ROOT / "firmware/include"),
         str(ROOT / "firmware/app/packet_v01.c"), str(work / "harness.c"),
         "-o", str(exe)],
        capture_output=True, text=True,
    )
    assert build.returncode == 0, build.stderr
    return exe


def _run(exe, cases):
    lines = []
    for p, cap in cases:
        lines.append(" ".join(str(v) for v in (
            p.channel_id, p.session_id, p.seq, p.first_sample_index, p.t_anchor_us,
            p.t_first_us, p.fs_nominal_mhz, p.status, cap, len(p.data), *p.data)))
    run = subprocess.run([str(exe)], input="\n".join(lines) + "\n",
                         capture_output=True, text=True, timeout=60)
    assert run.returncode == 0, run.stderr
    out = run.stdout.splitlines()
    assert out[0] == "kat 1"
    rows = [line.split() for line in out[1:]]
    assert len(rows) == len(cases)
    return [(int(size), bytes.fromhex(buf), int(t_first))
            for size, buf, t_first in rows]


def _random_packet(rng, n):
    u32, u64 = (1 << 32) - 1, (1 << 64) - 1
    data = [rng.choice(INT32) if rng.random() < 0.2 else rng.randint(*INT32)
            for _ in range(n)]
    return Packet(
        version=1, channel_id=rng.choice(CHANNELS), session_id=rng.randint(0, u32),
        seq=rng.randint(0, u32), first_sample_index=rng.randint(0, u32),
        t_anchor_us=rng.randint(0, u64), t_first_us=rng.randint(0, u64),
        fs_nominal_mhz=rng.choice((0, 100000, 200000, 512000, rng.randint(1, u32))),
        status=rng.randint(0, 0x7F), data=tuple(data))


def _expected_t_first(anchor, n, fs):
    # firmware/include/packet_v01.h: offset (N - 1) * 1e9 / fs rounded half up.
    if fs == 0 or n == 0:
        return anchor
    offset = ((n - 1) * 10 ** 9 + fs // 2) // fs
    return 0 if offset > anchor else anchor - offset


def test_c_encoder_matches_python_codec(harness):
    rng = random.Random(20261023)
    counts = (1, 32, *rng.choices(range(1, 33), k=200))
    cases = [(_random_packet(rng, n), 512) for n in counts]
    for (packet, _), (size, buf, t_first) in zip(cases, _run(harness, cases)):
        expected = encode_packet(packet)
        assert size == len(expected) == 42 + 4 * len(packet.data)
        assert buf[:size] == expected
        assert set(buf[size:]) == {0xEE}  # Nothing written past the packet.
        assert t_first == _expected_t_first(packet.t_anchor_us, len(packet.data),
                                            packet.fs_nominal_mhz)


def test_c_encoder_refuses_bad_count_and_small_buffer(harness):
    rng = random.Random(7)
    good = _random_packet(rng, 4)
    cases = [
        (replace(good, data=()), 512),
        (replace(good, data=tuple(range(33))), 512),
        (good, 42 + 4 * 4 - 1),
        (good, 42 + 4 * 4),
    ]
    results = _run(harness, cases)
    for size, buf, _ in results[:3]:
        assert size == 0 and set(buf) == {0xEE}  # A packet is never partly written.
    assert results[3][0] == 42 + 16 and results[3][1][:58] == encode_packet(good)
