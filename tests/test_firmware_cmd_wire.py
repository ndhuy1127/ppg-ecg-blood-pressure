"""Compile the command frame parser (firmware/app/cmd_wire.c); run it on the host.

Answers come from Packet Schema V0.2 section 13: SYNC 0xA5 0x5B, CMD_VERSION 1,
CMD_ID, CMD_SEQ, LEN <= 16, CRC-16/CCITT-FALSE over CMD_VERSION .. parameters;
bad frames are dropped silently and the search for SYNC resumes at the byte
after the bad frame's first SYNC byte. Frames come from the Python encoder the
logger uses (software/data_io/command_wire.py), so the two sides are checked
against each other. SYNTHETIC only. Without a host C compiler the test is skipped.
"""

import os
import random
import struct
import subprocess
from pathlib import Path

import pytest

from software.data_io.command_wire import command_from_json, encode_command
from software.data_io.packet_wire import crc16_ccitt_false
from tests.test_firmware_c_encoder import _compiler

ROOT = Path(__file__).resolve().parents[1]

HARNESS = r"""
#include <stdio.h>
#include <string.h>

#include "cmd_wire.h"

static void on_frame(void *ctx, const cmd_frame_t *f)
{
    (void)ctx;
    printf("F %u %u %u", f->id, f->seq, f->len);
    for (unsigned i = 0; i < f->len; i++) {
        printf(" %02x", f->params[i]);
    }
    printf(";");
}

int main(void)
{
    /* Lines: chunk sizes then hex bytes; "R" resets. */
    char line[16384];
    cmd_parser_t p;
    cmd_parser_init(&p);
    while (fgets(line, sizeof(line), stdin)) {
        if (line[0] == 'E') { /* encode: id seq len params... */
            unsigned id, seq, len, b;
            unsigned char params[32], out[64];
            int off = 0, k;
            sscanf(line + 1, "%u %u %u%n", &id, &seq, &len, &off);
            char *s = line + 1 + off;
            for (unsigned i = 0; i < len && i < sizeof(params); i++) {
                sscanf(s, "%x%n", &b, &k);
                params[i] = (unsigned char)b;
                s += k;
            }
            size_t n = cmd_encode((uint8_t)id, (uint16_t)seq, params, (uint8_t)len, out,
                                  sizeof(out));
            for (size_t i = 0; i < n; i++) {
                printf("%02x", out[i]);
            }
            printf("\n");
            fflush(stdout);
            continue;
        }
        unsigned chunk = 0;
        int off = 0;
        sscanf(line, "%u%n", &chunk, &off);
        unsigned char data[8192];
        size_t n = 0;
        for (char *s = line + off; s[0] && s[1] && n < sizeof(data); s++) {
            if (s[0] == ' ' || s[0] == '\n') {
                continue;
            }
            unsigned b;
            sscanf(s, "%2x", &b);
            data[n++] = (unsigned char)b;
            s++;
        }
        for (size_t i = 0; i < n; i += chunk) {
            size_t m = n - i < chunk ? n - i : chunk;
            cmd_parser_feed(&p, data + i, m, on_frame, NULL);
        }
        printf("D %lu\n", (unsigned long)p.dropped);
        fflush(stdout);
    }
    return 0;
}
"""


@pytest.fixture(scope="module")
def parser(tmp_path_factory):
    compiler = _compiler()
    if compiler is None:
        pytest.skip("no host C compiler ($CC, cc, gcc or clang)")
    work = tmp_path_factory.mktemp("cmd_wire")
    (work / "harness.c").write_text(HARNESS, encoding="utf-8")
    exe = work / ("harness.exe" if os.name == "nt" else "harness")
    sources = [ROOT / "firmware/app/cmd_wire.c", ROOT / "firmware/app/packet_wire.c"]
    build = subprocess.run(
        [*compiler, "-std=c99", "-Wall", "-Wextra", "-Werror", "-Wno-unused-result",
         "-I", str(ROOT / "firmware/include"), *map(str, sources),
         str(work / "harness.c"), "-o", str(exe)],
        capture_output=True, text=True,
    )
    assert build.returncode == 0, build.stderr

    def run(lines):
        out = subprocess.run([str(exe)], input="".join(f"{x}\n" for x in lines),
                             capture_output=True, text=True, check=True).stdout
        return out.splitlines()

    return run


def feed(parser, data, chunk=1):
    out = parser([f"{chunk} {data.hex()}"])[0]
    frames, dropped = out.rsplit("D ", 1)
    return [f for f in frames.split(";") if f], int(dropped)


PING = encode_command(0x01, 7)
LED = encode_command(0x02, 0xBEEF, bytes([0x12, 0x24, 0x24]))


def test_python_and_c_encoders_agree(parser):
    assert parser(["E 1 7 0"]) == [PING.hex()]
    assert parser(["E 2 48879 3 12 24 24"]) == [LED.hex()]
    full = bytes(range(16))
    assert parser(["E 9 65535 16 " + " ".join(f"{b:02x}" for b in full)]) == [
        encode_command(9, 0xFFFF, full).hex()]
    assert parser(["E 9 1 17 " + " ".join(["00"] * 17)]) == [""]  # LEN > 16


@pytest.mark.parametrize("chunk", [1, 2, 5, 64])
def test_frames_in_any_split_with_garbage_between(parser, chunk):
    data = b"\x00\xa5\x00" + PING + b"ESP-ROM text\r\n\xa5\xa5" + LED + PING
    frames, dropped = feed(parser, data, chunk)
    assert frames == ["F 1 7 0", "F 2 48879 3 12 24 24", "F 1 7 0"]
    assert dropped == 0


def test_bad_frames_are_dropped_and_the_search_resumes_inside_them(parser):
    bad_crc = bytearray(LED)
    bad_crc[-1] ^= 0x01
    bad_version = bytearray(PING)
    bad_version[2] = 2
    long_len = bytearray(PING)
    long_len[6] = 17
    # A false start whose bytes hide a whole real frame: the frame is found.
    hidden = b"\xa5\x5b\x01\x02\x03\x00\x10" + PING + b"\x00" * 9
    frames, dropped = feed(parser, bytes(bad_crc) + bytes(bad_version) + bytes(long_len)
                           + hidden + LED)
    assert frames == ["F 1 7 0", "F 2 48879 3 12 24 24"]
    assert dropped == 4


def test_wrong_version_with_a_good_crc_is_dropped(parser):
    body = b"\xa5\x5b\x02\x01\x07\x00\x00"  # CMD_VERSION 2, otherwise PING
    frame = body + struct.pack("<H", crc16_ccitt_false(body[2:]))
    frames, dropped = feed(parser, frame + PING)
    assert frames == ["F 1 7 0"] and dropped == 1


def test_random_noise_never_yields_a_frame_but_real_frames_survive(parser):
    rng = random.Random(20261025)
    noise = bytes(rng.randrange(256) for _ in range(4000))
    # A random frame needs SYNC, version, LEN <= 16 and a CRC match: about 1e-17
    # per position, so none in 4000 bytes.
    frames, _ = feed(parser, noise + PING, 7)
    assert frames == ["F 1 7 0"]


def test_inbox_lines_to_frames():
    assert command_from_json({"cmd": "ping"}) == (1, b"")
    assert command_from_json({"cmd": "set_ppg_led", "green": 18, "red": 36, "ir": 36},
                             0x5EED1234) == (2, bytes([0x34, 0x12, 0xED, 0x5E, 18, 36,
                                                       36]))
    with pytest.raises(ValueError):  # no target session
        command_from_json({"cmd": "set_ppg_led", "green": 18, "red": 36, "ir": 36})
    for bad in ({"cmd": "ping", "x": 1}, {"cmd": "set_ppg_led", "green": 18},
                {"cmd": "set_ppg_led", "green": 256, "red": 0, "ir": 0},
                {"cmd": "set_ppg_led", "green": True, "red": 0, "ir": 0},
                {"cmd": "reboot"}, ["ping"]):
        with pytest.raises(ValueError):
            command_from_json(bad, 1)
    with pytest.raises(ValueError):
        encode_command(1, 0, bytes(17))
