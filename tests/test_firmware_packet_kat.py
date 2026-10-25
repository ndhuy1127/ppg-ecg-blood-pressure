"""The firmware packet known answers must match an independent derivation and the
logger codec.

firmware/include/packet_kat.h is what the firmware checks its C encoder
against at boot (Packet Schema V0.2). No C compiler runs here: the expected
bytes are rebuilt with struct and binascii.crc_hqx, as the header says they
were made, and compared with the header and with software/data_io/packet_wire.py.
The V0.1 known answer stays in tests/fixtures/packet_v3_expected.json (checked
in test_packet_logger.py).
"""

import binascii
import json
import re
import struct
from pathlib import Path

from software.data_io.packet_wire import (
    STATUS_BITS, Packet, crc16_ccitt_false, device_info_data, encode_packet,
)

ROOT = Path(__file__).resolve().parents[1]
HEADER = (ROOT / "firmware/include/packet_kat.h").read_text(encoding="utf-8")
PACKET_HEADER = (ROOT / "firmware/include/packet_wire.h").read_text(encoding="utf-8")
EXPECTED = json.loads((ROOT / "tests/fixtures/packet_v3_expected.json").read_bytes())


def _defines(text):
    return dict(re.findall(r"^#define (\w+) (\S+)$", text, flags=re.MULTILINE))


def _int(value):
    return int(value.rstrip("uU"), 0)


def _array(name):
    body = re.search(rf"{name}\[\d*\] = \{{(.*?)\}};", HEADER, flags=re.DOTALL)
    return bytes(int(b, 16) for b in re.findall(r"0x([0-9a-fA-F]{2})", body.group(1)))


def _derive(version, channel, session, seq, first, anchor, t_first, fs, status, data):
    """Schema V0.1 section 6 layout, built without the codec under test."""
    body = struct.pack("<BBIIIQQIHH", version, channel, session, seq, first, anchor,
                       t_first, fs, len(data), status)
    body += b"".join(struct.pack("<I", value & 0xFFFFFFFF) for value in data)
    return b"\xa5\x5a" + body + struct.pack("<H", binascii.crc_hqx(body, 0xFFFF))


def test_kat_crc_matches_fixture_and_codec():
    defines = _defines(HEADER)
    text = defines["KAT_CRC_INPUT"].strip('"')
    expected = next(
        item["crc"] for item in EXPECTED["crc16_ccitt_false"] if item["ascii"] == text
    )
    assert _int(defines["KAT_CRC_EXPECTED"]) == expected
    assert crc16_ccitt_false(text.encode("ascii")) == expected


def test_kat_ecg_packet_is_v02_with_samp_bit():
    d = {k: _int(v) for k, v in _defines(HEADER).items()
         if k.startswith("KAT_") and not k.startswith(("KAT_INFO", "KAT_CRC"))}
    assert d["KAT_VERSION"] == 2
    assert d["KAT_STATUS"] == (1 << 4) | (1 << 8)  # latency unmeasured, SAMP anchor
    fields = dict(version=d["KAT_VERSION"], channel_id=d["KAT_CHANNEL_ID"],
                  session_id=d["KAT_SESSION_ID"], seq=d["KAT_SEQ"],
                  first_sample_index=d["KAT_FIRST_SAMPLE_INDEX"],
                  t_anchor_us=d["KAT_T_ANCHOR_US"], t_first_us=d["KAT_T_FIRST_US"],
                  fs_nominal_mhz=d["KAT_FS_NOMINAL_MHZ"], status=d["KAT_STATUS"],
                  data=(d["KAT_DATA_0"], d["KAT_DATA_1"]))
    payload = _array("KAT_PACKET")
    assert payload == _derive(*fields.values())
    assert encode_packet(Packet(**fields)) == payload
    # Same fields as the V0.1 example except VERSION, STATUS and so the CRC.
    v01 = EXPECTED["example_packet"]["fields"]
    assert {k: v for k, v in v01.items() if k not in ("version", "status")} == {
        k: list(v) if k == "data" else v for k, v in fields.items()
        if k not in ("version", "status")}


def test_kat_device_info_packet():
    defines = _defines(HEADER)
    digest = _array("KAT_INFO_SHA256")
    app = defines["KAT_INFO_APP_VERSION"].strip('"')
    idf = defines["KAT_INFO_IDF_VERSION"].strip('"')
    t = _int(defines["KAT_INFO_T_US"])
    raw = digest + app.encode("ascii").ljust(32, b"\0") + idf.encode("ascii").ljust(
        32, b"\0")
    words = [1, *struct.unpack(">24i", raw)]
    assert any(w < 0 for w in words[1:9])  # hash words with bit 31 set
    payload = _array("KAT_INFO_PACKET")
    assert len(payload) == 142
    assert payload == _derive(2, 0xD1, _int(defines["KAT_INFO_SESSION_ID"]), 0, 0, t,
                              t, 0, 0, words)
    assert tuple(words) == device_info_data(digest.hex(), app, idf)
    assert encode_packet(Packet(2, 0xD1, _int(defines["KAT_INFO_SESSION_ID"]), 0, 0,
                                t, t, 0, 0, tuple(words))) == payload


def test_firmware_header_constants_match_codec():
    defines = _defines(PACKET_HEADER)
    sync = bytes([_int(defines["PKT_SYNC0"]), _int(defines["PKT_SYNC1"])])
    assert sync == b"\xa5\x5a"
    assert _int(defines["PKT_VERSION"]) == 2
    assert _int(defines["PKT_MAX_SAMPLES"]) == 32
    channels = {
        "PKT_CH_ECG": 0xE1, "PKT_CH_PPG_SLOT1": 0xF1, "PKT_CH_PPG_SLOT2": 0xF2,
        "PKT_CH_PPG_SLOT3": 0xF3, "PKT_CH_PPG_SLOT4": 0xF4, "PKT_CH_EVENT": 0xC1,
        "PKT_CH_ACC_X": 0xA1, "PKT_CH_ACC_Y": 0xA2, "PKT_CH_ACC_Z": 0xA3,
        "PKT_CH_GYR_X": 0xA4, "PKT_CH_GYR_Y": 0xA5, "PKT_CH_GYR_Z": 0xA6,
        "PKT_CH_DEVICE_INFO": 0xD1, "PKT_CH_DIE_TEMP": 0xB1,
    }
    for name, value in channels.items():
        assert _int(defines[name]) == value, name
    bits = {int(m.group(2)): m.group(1) for m in re.finditer(
        r"^#define PKT_STATUS_(\w+) \(1u << (\d+)\)$", PACKET_HEADER, re.MULTILINE)}
    assert {bit: name.lower() for bit, name in bits.items()} == STATUS_BITS
    assert _int(defines["PKT_DEVICE_INFO_LAYOUT"]) == 1
    assert _int(defines["PKT_DEVICE_INFO_COUNT"]) == 25
