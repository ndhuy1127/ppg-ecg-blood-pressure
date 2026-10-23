"""The firmware packet known answer must match the fixture and the logger codec.

firmware/include/packet_kat.h is what the firmware checks its C encoder
against at boot. No C compiler runs here: this test only ties that header to
tests/fixtures/packet_v3_expected.json and software/data_io/packet_wire.py.
"""

import json
import re
from pathlib import Path

from software.data_io.packet_wire import Packet, crc16_ccitt_false, encode_packet

ROOT = Path(__file__).resolve().parents[1]
HEADER = (ROOT / "firmware/include/packet_kat.h").read_text(encoding="utf-8")
PACKET_HEADER = (ROOT / "firmware/include/packet_v01.h").read_text(encoding="utf-8")
EXPECTED = json.loads((ROOT / "tests/fixtures/packet_v3_expected.json").read_bytes())


def _defines(text):
    return dict(re.findall(r"^#define (\w+) (\S+)$", text, flags=re.MULTILINE))


def _int(value):
    return int(value.rstrip("uU"), 0)


def _kat_bytes():
    body = re.search(r"KAT_PACKET\[\] = \{(.*?)\};", HEADER, flags=re.DOTALL)
    return bytes(int(b, 16) for b in re.findall(r"0x([0-9a-fA-F]{2})", body.group(1)))


def test_kat_crc_matches_fixture_and_codec():
    defines = _defines(HEADER)
    text = defines["KAT_CRC_INPUT"].strip('"')
    expected = next(
        item["crc"] for item in EXPECTED["crc16_ccitt_false"] if item["ascii"] == text
    )
    assert _int(defines["KAT_CRC_EXPECTED"]) == expected
    assert crc16_ccitt_false(text.encode("ascii")) == expected


def test_kat_packet_matches_fixture_and_codec():
    defines = _defines(HEADER)
    fields = EXPECTED["example_packet"]["fields"]
    for name, value in fields.items():
        if name == "data":
            continue
        assert _int(defines[f"KAT_{name.upper()}"]) == value, name
    assert [_int(defines["KAT_DATA_0"]), _int(defines["KAT_DATA_1"])] == fields["data"]
    payload = _kat_bytes()
    assert payload.hex() == EXPECTED["example_packet"]["hex"]
    packet = Packet(**dict(fields, data=tuple(fields["data"])))
    assert encode_packet(packet) == payload


def test_firmware_header_constants_match_codec():
    defines = _defines(PACKET_HEADER)
    sync = bytes([_int(defines["PKT_SYNC0"]), _int(defines["PKT_SYNC1"])])
    assert sync == b"\xa5\x5a"
    assert _int(defines["PKT_VERSION"]) == 1
    assert _int(defines["PKT_MAX_SAMPLES"]) == 32
    channels = {
        "PKT_CH_ECG": 0xE1, "PKT_CH_PPG_SLOT1": 0xF1, "PKT_CH_PPG_SLOT2": 0xF2,
        "PKT_CH_PPG_SLOT3": 0xF3, "PKT_CH_PPG_SLOT4": 0xF4, "PKT_CH_EVENT": 0xC1,
    }
    for name, value in channels.items():
        assert _int(defines[name]) == value, name
