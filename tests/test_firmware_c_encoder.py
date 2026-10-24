"""Compile and run the firmware C encoder on the host.

firmware/app/packet_wire.c has no ESP-IDF dependency, so a host compiler can
build it with a small harness. The harness runs the boot self-test
(pkt_self_test, against firmware/include/packet_kat.h), encodes seeded random
Packet Schema V0.2 packets, whose bytes must equal
software/data_io/packet_wire.encode_packet, and packs device info payloads,
which must equal packet_wire.device_info_data. The compiler is taken from $CC,
else cc/gcc/clang; without one the test is skipped (CI on Ubuntu has gcc). A
build or run failure is a test failure, not a skip. This checks the encoder
only: not the ISR, tasks, USB or hardware.
"""

import os
import random
import shlex
import shutil
import subprocess
from dataclasses import replace
from pathlib import Path

import pytest

from software.data_io.packet_wire import Packet, device_info_data, encode_packet

ROOT = Path(__file__).resolve().parents[1]
IMU = (0xA1, 0xA2, 0xA3, 0xA4, 0xA5, 0xA6)
CHANNELS = (0xE1, 0xF1, 0xF2, 0xF3, 0xF4, 0xC1, *IMU, 0xD1)
INT32 = (-(1 << 31), (1 << 31) - 1)
INT16 = (-(1 << 15), (1 << 15) - 1)
UNTOUCHED = 0x5A5A5A5A  # device info words the harness presets before a call

HARNESS = r"""
#include <stdio.h>
#include <string.h>

#include "packet_wire.h"

/* "-" is the empty string; otherwise two hex digits per byte. */
static int hex_bytes(const char *hex, uint8_t *out, size_t cap)
{
    if (strcmp(hex, "-") == 0) {
        return 0;
    }
    size_t n = strlen(hex) / 2;
    if (n > cap) {
        return -1;
    }
    for (size_t i = 0; i < n; i++) {
        unsigned v;
        if (sscanf(hex + 2 * i, "%2x", &v) != 1) {
            return -1;
        }
        out[i] = (uint8_t)v;
    }
    return (int)n;
}

static int encode_line(void)
{
    unsigned ch, n, status, cap;
    unsigned long session, seq, first, fs;
    unsigned long long anchor, t_first;
    if (scanf("%u %lu %lu %lu %llu %llu %lu %u %u %u", &ch, &session, &seq, &first,
              &anchor, &t_first, &fs, &status, &cap, &n) != 10) {
        return 2;
    }
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
    return 0;
}

static int info_line(void)
{
    char sha_hex[65], app_hex[129], idf_hex[129];
    if (scanf("%64s %128s %128s", sha_hex, app_hex, idf_hex) != 3) {
        return 2;
    }
    uint8_t sha[32];
    char app[65], idf[65];
    int na = hex_bytes(app_hex, (uint8_t *)app, 64);
    int ni = hex_bytes(idf_hex, (uint8_t *)idf, 64);
    if (hex_bytes(sha_hex, sha, 32) != 32 || na < 0 || ni < 0) {
        return 2;
    }
    app[na] = '\0';
    idf[ni] = '\0';
    int32_t words[PKT_DEVICE_INFO_COUNT];
    memset(words, 0x5A, sizeof(words));
    printf("%d", pkt_device_info_data(sha, app, idf, words) ? 1 : 0);
    for (unsigned i = 0; i < PKT_DEVICE_INFO_COUNT; i++) {
        printf(" %ld", (long)words[i]);
    }
    printf("\n");
    return 0;
}

int main(void)
{
    printf("kat %d\n", pkt_self_test() ? 1 : 0);
    char cmd[2];
    while (scanf("%1s", cmd) == 1) {
        int rc = cmd[0] == 'P' ? encode_line() : cmd[0] == 'D' ? info_line() : 2;
        if (rc != 0) {
            return rc;
        }
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
         str(ROOT / "firmware/app/packet_wire.c"), str(work / "harness.c"),
         "-o", str(exe)],
        capture_output=True, text=True,
    )
    assert build.returncode == 0, build.stderr
    return exe


def _call(exe, lines):
    run = subprocess.run([str(exe)], input="\n".join(lines) + "\n",
                         capture_output=True, text=True, timeout=60)
    assert run.returncode == 0, run.stderr
    out = run.stdout.splitlines()
    assert out[0] == "kat 1"  # the boot self-test passes
    assert len(out) == len(lines) + 1
    return out[1:]


def _run(exe, cases):
    lines = [" ".join(str(v) for v in (
        "P", p.channel_id, p.session_id, p.seq, p.first_sample_index, p.t_anchor_us,
        p.t_first_us, p.fs_nominal_mhz, p.status, cap, len(p.data), *p.data))
        for p, cap in cases]
    return [(int(size), bytes.fromhex(buf), int(t_first))
            for size, buf, t_first in (line.split() for line in _call(exe, lines))]


def _random_packet(rng, n):
    u32, u64 = (1 << 32) - 1, (1 << 64) - 1
    channel = rng.choice(CHANNELS)
    span = INT16 if channel in IMU else INT32
    data = [rng.choice(span) if rng.random() < 0.2 else rng.randint(*span)
            for _ in range(n)]
    return Packet(
        version=2, channel_id=channel, session_id=rng.randint(0, u32),
        seq=rng.randint(0, u32), first_sample_index=rng.randint(0, u32),
        t_anchor_us=rng.randint(0, u64), t_first_us=rng.randint(0, u64),
        fs_nominal_mhz=rng.choice((0, 100000, 200000, 512000, rng.randint(1, u32))),
        status=rng.randint(0, 0x1FF), data=tuple(data))


def _expected_t_first(anchor, n, fs):
    # firmware/include/packet_wire.h: offset (N - 1) * 1e9 / fs rounded half up.
    if fs == 0 or n == 0:
        return anchor
    offset = ((n - 1) * 10 ** 9 + fs // 2) // fs
    return 0 if offset > anchor else anchor - offset


def test_c_encoder_matches_python_codec(harness):
    rng = random.Random(20261024)
    counts = (1, 25, 32, *rng.choices(range(1, 33), k=300))
    cases = [(_random_packet(rng, n), 512) for n in counts]
    assert {p.channel_id for p, _ in cases} == set(CHANNELS)
    for (packet, _), (size, buf, t_first) in zip(cases, _run(harness, cases)):
        expected = encode_packet(packet)
        assert size == len(expected) == 42 + 4 * len(packet.data)
        assert buf[:size] == expected and buf[2] == 2  # VERSION 0x02
        assert set(buf[size:]) == {0xEE}  # Nothing written past the packet.
        assert t_first == _expected_t_first(packet.t_anchor_us, len(packet.data),
                                            packet.fs_nominal_mhz)


def test_c_encoder_header_extremes_and_t_first_underflow(harness):
    u32, u64 = (1 << 32) - 1, (1 << 64) - 1
    cases = [
        (Packet(2, 0xE1, 0, 0, 0, 0, 0, 0, 0, (0,)), 512),
        (Packet(2, 0xD1, u32, u32, u32, u64, u64, u32, 0xFFFF, INT32 * 16), 512),
        # Offset 31 * 1e9 / 512000 = 60 546.875 -> 60 547 us > T_ANCHOR_US.
        (Packet(2, 0xE1, 1, 1, 1, 60_546, 0, 512_000, 0, (7,) * 32), 512),
        # Offset 31 * 1e9 / 100000 = 310 000 us = T_ANCHOR_US.
        (Packet(2, 0xA1, 1, 1, 1, 310_000, 0, 100_000, 0, INT16 * 16), 512),
    ]
    results = _run(harness, cases)
    for (packet, _), (size, buf, t_first) in zip(cases, results):
        assert buf[:size] == encode_packet(packet)
        assert t_first == _expected_t_first(packet.t_anchor_us, len(packet.data),
                                            packet.fs_nominal_mhz)
    # fs 0 keeps the anchor; 31 * 1e9 / (2**32 - 1) rounds to 7 us; underflow
    # gives 0, not a wrapped value.
    assert [t_first for _, _, t_first in results] == [0, u64 - 7, 0, 0]


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


def _info_line(digest, app, idf):
    return f"D {digest.hex()} {app.hex() or '-'} {idf.hex() or '-'}"


def test_c_device_info_matches_python(harness):
    rng = random.Random(61)
    cases = []
    for k in range(200):
        digest = bytearray(rng.randbytes(32))
        digest[4 * (k % 8)] |= 0x80  # at least one hash word with bit 31 set
        # Any ASCII but NUL, 0 to 31 bytes; tab and other controls included.
        app, idf = (bytes(rng.randint(1, 127) for _ in range(
            rng.choice((0, 1, 31, rng.randint(0, 31))))) for _ in range(2))
        cases.append((bytes(digest), app, idf))
    out = _call(harness, [_info_line(*case) for case in cases])
    for (digest, app, idf), line in zip(cases, out):
        ok, *words = map(int, line.split())
        assert ok == 1
        assert tuple(words) == device_info_data(digest.hex(), app.decode("ascii"),
                                                idf.decode("ascii"))


@pytest.mark.parametrize("text", [b"x" * 32, b"0.2.0-\xe9", b"\x80"])
def test_c_device_info_refuses_long_or_non_ascii_text(harness, text):
    digest = bytes(range(32))
    for line in _call(harness, [_info_line(digest, text, b"v5.5.3"),
                                _info_line(digest, b"v5.5.3", text)]):
        ok, *words = map(int, line.split())
        assert ok == 0 and words == [UNTOUCHED] * 25  # out left untouched
    with pytest.raises(ValueError):
        device_info_data(digest.hex(), text.decode("latin-1"), "v5.5.3")
