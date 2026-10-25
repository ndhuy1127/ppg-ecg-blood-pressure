"""Command frames PC -> device (configs/hardware/Packet_Schema_V0.2.md section 13).

Pure code: builds the bytes the logger writes to the serial port. SYNC 0xA5 0x5B,
CMD_VERSION 1, CMD_ID, CMD_SEQ (uint16), LEN (0 .. 16), parameters, then
CRC-16/CCITT-FALSE over CMD_VERSION .. the last parameter, little-endian. The
device answers with a 0xD3 packet in the normal packet stream.
"""

import struct

from software.data_io.packet_wire import COMMAND_NAMES, crc16_ccitt_false

COMMAND_SYNC = b"\xa5\x5b"
COMMAND_VERSION = 0x01
MAX_PARAMS = 16
COMMANDS = {name: cmd_id for cmd_id, name in COMMAND_NAMES.items()}
LED_CODE_MAX = 0x7F  # firmware limit per code (section 13), 25.4 mA per sink
HEADER = struct.Struct("<2sBBHB")


def encode_command(cmd_id, seq, params=b""):
    """One frame; ``seq`` is taken modulo 2^16."""
    params = bytes(params)
    if not 0 <= cmd_id <= 0xFF or len(params) > MAX_PARAMS:
        raise ValueError("CMD_ID must be a byte and LEN at most 16")
    body = HEADER.pack(COMMAND_SYNC, COMMAND_VERSION, cmd_id, seq & 0xFFFF,
                       len(params)) + params
    return body + struct.pack("<H", crc16_ccitt_false(body[2:]))


def command_from_json(entry, session_id=None):
    """``(cmd_id, params)`` of one inbox line, e.g. ``{"cmd": "ping"}`` or
    ``{"cmd": "set_ppg_led", "green": 18, "red": 36, "ir": 36}`` (codes in 0.2 mA
    steps; green is the code of each of its two sinks). ``set_ppg_led`` targets
    ``session_id`` (the device session the command is meant for, section 13)."""
    if not isinstance(entry, dict) or not isinstance(entry.get("cmd"), str) or (
        entry["cmd"] not in COMMANDS
    ):
        raise ValueError("Unknown command")
    name = entry["cmd"]
    if name == "ping":
        if set(entry) != {"cmd"}:
            raise ValueError("ping takes no parameters")
        return COMMANDS[name], b""
    if set(entry) != {"cmd", "green", "red", "ir"}:
        raise ValueError("set_ppg_led needs green, red and ir")
    codes = [entry[k] for k in ("green", "red", "ir")]
    if any(isinstance(c, bool) or not isinstance(c, int) or not 0 <= c <= 255
           for c in codes):
        raise ValueError("LED codes must be integers 0 .. 255")
    if session_id is None or not 0 <= session_id <= 0xFFFFFFFF:
        raise ValueError("set_ppg_led needs the target SESSION_ID")
    return COMMANDS[name], struct.pack("<I", session_id) + bytes(codes)
