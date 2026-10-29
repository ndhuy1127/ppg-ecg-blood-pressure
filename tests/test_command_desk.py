"""Commands during record (Packet Schema V0.2 section 13), SYNTHETIC only.

The desk is driven with a fake clock and port; the record test uses a fake
device that answers each command frame with a 0xD3 packet. Answers come from
section 13: one outstanding command, the same bytes again after 500 ms, three
attempts, then outcome unknown; a new SESSION_ID cancels; the inbox keeps a
partial line until its newline and rejects bad lines. Amendment 2026-10-29:
SET_PPG_LED is unknown only 2.5 s after its first send, an answer after
"unknown" is journaled as late_ack, MARK_EVENT, and the PC refuses LED codes
above 0x7F unless the bring-up flag is given.
"""

import io
import json
import struct
from pathlib import Path

import pytest

from scripts.device_command import main as device_command
from scripts.device_command import queue_command
from scripts.packet_logger import record
from software.data_io.command_desk import CommandDesk
from software.data_io.command_wire import COMMAND_SYNC
from software.data_io.packet_simulation_v3 import session_metadata
from software.data_io.packet_wire import Packet, crc16_ccitt_false, encode_packet

ROOT = Path(__file__).resolve().parents[1]
LOGGER_CONFIG = ROOT / "configs/hardware/packet_logger.json"
SIM_V02 = ROOT / "configs/hardware/packet_simulation_v3_v02.json"


def parse_frame(frame):
    """Independent reading of a command frame (section 13 table)."""
    assert frame[:2] == COMMAND_SYNC and frame[2] == 1
    cmd_id, seq, length = frame[3], struct.unpack_from("<H", frame, 4)[0], frame[6]
    params = frame[7:7 + length]
    assert struct.unpack_from("<H", frame, 7 + length)[0] == crc16_ccitt_false(
        frame[2:7 + length])
    return cmd_id, seq, params


def ack_packet(session, seq, cmd_id, cmd_seq, result=0, gen=0):
    t = 5_000_000 + seq
    return Packet(2, 0xD3, session, seq, seq, t, t, 0, 0, (1, cmd_id, cmd_seq, result, gen))


def info(session, seq=0):
    return Packet(2, 0xC1, session, seq, seq, 1000 + seq, 1000 + seq, 0, 0, (4,))


class Clock:
    def __init__(self):
        self.t = 100.0

    def __call__(self):
        return self.t


@pytest.fixture
def desk(tmp_path):
    inbox = tmp_path / "command_inbox.jsonl"
    inbox.write_bytes(b"")
    clock, sent, journal = Clock(), [], io.StringIO()
    d = CommandDesk(inbox, journal, lambda b: sent.append(b) or len(b), clock,
                    first_seq=99)
    d.inbox, d.sent, d.clk = inbox, sent, clock
    d.events = lambda: [json.loads(x)["event"] for x in journal.getvalue().splitlines()]
    return d


def append(path, text):
    with open(path, "ab") as f:
        f.write(text.encode())


def test_one_command_at_a_time_with_the_session_target(desk):
    append(desk.inbox, '{"cmd": "set_ppg_led", "green": 18, "red": 36, "ir": 36}\n'
                       '{"cmd": "ping"}\n')
    desk.service()
    assert desk.sent == []  # no packet yet: target session unknown
    desk.observe([info(0x5EED)])
    desk.service()
    cmd_id, seq, params = parse_frame(desk.sent[0])
    assert (cmd_id, seq, params) == (2, 100, struct.pack("<I", 0x5EED) + bytes([18, 36, 36]))
    desk.clk.t += 0.2
    desk.service()
    assert len(desk.sent) == 1  # waiting for its 0xD3
    desk.observe([ack_packet(0x5EED, 0, 2, 100, gen=2)])
    desk.service()
    assert len(desk.sent) == 1  # at most 2 sends per second, new ones included
    desk.clk.t += 0.3  # 0.5 s after the first send
    desk.service()
    assert parse_frame(desk.sent[1])[:2] == (1, 101)
    assert desk.events() == ["queued", "queued", "sent", "acked", "sent"]


def test_retries_same_bytes_then_unknown(desk):
    desk.observe([info(7)])
    append(desk.inbox, '{"cmd": "ping"}\n')
    desk.service()
    for _ in range(2):
        desk.clk.t += 0.49
        desk.service()
        desk.clk.t += 0.01
        desk.service()
    assert len(desk.sent) == 3 and len(set(desk.sent)) == 1
    # Same session, wrong CMD_SEQ or wrong CMD_ID: not this command's answer.
    desk.observe([ack_packet(7, 0, 1, 999), ack_packet(7, 1, 2, 100, gen=1)])
    desk.clk.t += 0.5
    desk.service()
    assert desk.events() == ["queued", "sent", "sent", "sent", "unknown"]
    assert desk.pending is None


def test_new_session_cancels_the_pending_command(desk):
    desk.observe([info(7)])
    append(desk.inbox, '{"cmd": "ping"}\n')
    desk.service()
    desk.observe([info(8)])  # MCU restarted
    assert desk.events()[-1] == "session_changed" and desk.pending is None


def test_a_long_line_is_dropped_through_its_newline(desk):
    desk.observe([info(7)])
    append(desk.inbox, "x" * 1025)
    desk.service()
    append(desk.inbox, '{"cmd": "set_ppg_led", "green": 1, "red": 1, "ir": 1}\n'
                       '{"cmd": "ping"}\n')
    desk.service()
    # The JSON after the junk belongs to the same long line: never executed.
    assert desk.events() == ["rejected", "queued", "sent"]
    assert parse_frame(desk.sent[0])[0] == 1


def test_odd_json_types_are_rejected_not_fatal(desk):
    append(desk.inbox, '{"cmd": []}\n{"cmd": {}}\n[1]\n7\n')
    desk.service()
    assert desk.events() == ["rejected"] * 4


def test_cmd_seq_is_never_reused_in_a_recording(desk):
    desk.observe([info(7)])
    desk.issued = 1 << 16  # every value used once already
    append(desk.inbox, '{"cmd": "ping"}\n')
    desk.service()
    assert desk.events() == ["queued", "rejected"] and desk.sent == []


def test_inbox_partial_bad_and_truncated_lines(desk):
    desk.observe([info(7)])
    append(desk.inbox, '{"cmd": "pi')
    desk.service()
    assert desk.events() == []
    append(desk.inbox, 'ng"}\nnot json\n{"cmd": "reboot"}\n'
                       '{"cmd": "set_ppg_led", "green": 300, "red": 1, "ir": 1}\n'
                       + "x" * 1100 + "\n")
    desk.service()
    assert desk.events() == ["queued", "rejected", "rejected", "rejected", "rejected",
                             "sent"]
    desk.inbox.write_bytes(b"")  # truncated by someone
    desk.service()
    assert desk.events()[-1] == "inbox_truncated"
    append(desk.inbox, '{"cmd": "ping"}\n')
    desk.service()
    assert desk.events()[-1] == "inbox_truncated"  # no longer read


def test_write_errors_are_journaled_and_close_reports_leftovers(tmp_path):
    inbox = tmp_path / "command_inbox.jsonl"
    inbox.write_bytes(b'{"cmd": "ping"}\n{"cmd": "ping"}\n')
    journal = io.StringIO()

    def broken(_):
        raise TimeoutError("write timeout")

    d = CommandDesk(inbox, journal, broken, Clock(), first_seq=0)
    d.observe([info(1)])
    d.service()
    d.close()
    entries = [json.loads(x) for x in journal.getvalue().splitlines()]
    assert [e["event"] for e in entries] == ["queued", "queued", "sent", "unknown",
                                             "not_sent"]
    assert entries[2]["written"] == 0 and "TimeoutError" in entries[2]["error"]


LED_DEFAULT = ({"cmd": "set_ppg_led", "green": 18, "red": 36, "ir": 36},
               {"cmd": "ping"})


class FakeDevice:
    """Sends filler packets; answers command frames with 0xD3 the way section 13
    says (LED code above 0x7F: result 8; MARK_EVENT: an event packet with the
    code, then the answer); 0.1 s per read."""

    def __init__(self, recording, reads=40, entries=LED_DEFAULT, filler_code=4):
        self.recording, self.reads, self.count = recording, reads, 0
        self.entries, self.filler_code = entries, filler_code
        self.now = 0.0
        self.out, self.session, self.seq = [], 0x5EED1234, {0xC1: 0, 0xD3: 0}
        self.on_idle = None

    def _emit(self, packet):
        self.out.append(encode_packet(packet))

    def _event(self, code):
        k = self.seq[0xC1]
        self.seq[0xC1] += 1
        self._emit(Packet(2, 0xC1, self.session, k, k, 1000 * k, 1000 * k, 0, 0, (code,)))

    def read(self, n):
        self.count += 1
        self.now += 0.1
        if self.count == 3:
            for entry in self.entries:
                queue_command(self.recording, entry)
        if self.count > self.reads:
            return b""
        if not self.out:
            self._event(self.filler_code)
        return self.out.pop(0)

    def write(self, frame):
        cmd_id, cmd_seq, params = parse_frame(frame)
        result, gen = 0, 1 if cmd_id == 2 else 0
        if cmd_id == 2:
            assert struct.unpack_from("<I", params)[0] == self.session
            if max(params[4:]) > 0x7F:
                result, gen = 8, 0
        if cmd_id == 3:
            assert len(params) == 1 and params[0] in (2, 4)
            self._event(params[0])
        k = self.seq[0xD3]
        self.seq[0xD3] += 1
        self._emit(ack_packet(self.session, k, cmd_id, cmd_seq, result, gen))
        return len(frame)


def test_record_with_commands_end_to_end(tmp_path):
    sim = json.loads(SIM_V02.read_bytes())
    meta = session_metadata(sim, "valid", "0" * 64)
    meta_path = tmp_path / "meta.json"
    meta_path.write_text(json.dumps(meta), encoding="utf-8")
    out = tmp_path / "rec"
    device = FakeDevice(out)
    manifest = record(device, out, LOGGER_CONFIG, meta_path, ROOT, "fake",
                      commands=True, clock=lambda: device.now)
    journal = [json.loads(x) for x in
               (out / "commands_sent.jsonl").read_text(encoding="utf-8").splitlines()]
    assert [e["event"] for e in journal] == ["queued", "queued", "sent", "acked", "sent",
                                             "acked"]
    assert [e["result"] for e in journal if e["event"] == "acked"] == ["ok", "ok"]
    assert manifest["commands"] == {"inbox": "command_inbox.jsonl",
                                    "journal": "commands_sent.jsonl"}
    for name in ("command_inbox.jsonl", "commands_sent.jsonl"):
        assert name in manifest["outputs_sha256"]
    decode = json.loads((out / "decode.json").read_bytes())
    acks = decode["sessions"][0]["commands"]
    assert [(a["cmd"], a["result"]) for a in acks] == [("set_ppg_led", "ok"),
                                                       ("ping", "ok")]
    # A SET_PPG_LED done without its 0xD2 is reported by the decode itself.
    assert decode["issue_counts"].get("command_ack_without_config") == 1


def test_queue_command_needs_a_running_recording(tmp_path):
    with pytest.raises(FileNotFoundError):
        queue_command(tmp_path, {"cmd": "ping"})
    (tmp_path / "command_inbox.jsonl").write_bytes(b"")
    with pytest.raises(ValueError):
        queue_command(tmp_path, {"cmd": "set_ppg_led", "green": 1})
    queue_command(tmp_path, {"cmd": "ping"})
    assert (tmp_path / "command_inbox.jsonl").read_bytes() == b'{"cmd": "ping"}\n'


def step(desk, seconds, dt=0.05):
    """Advance the fake clock in small steps, serving the desk each time."""
    for _ in range(round(seconds / dt)):
        desk.clk.t += dt
        desk.service()


def test_set_ppg_led_waits_2_5_s_before_unknown(desk):
    desk.observe([info(7)])
    append(desk.inbox, '{"cmd": "set_ppg_led", "green": 18, "red": 36, "ir": 36}\n'
                       '{"cmd": "ping"}\n')
    desk.service()
    step(desk, 2.4)
    # Three sends of the same bytes, 0.5 s apart, then still waiting: the
    # firmware may answer up to 2 s after it took the frame.
    assert len(desk.sent) == 3 and len(set(desk.sent)) == 1
    assert desk.events()[-1] == "sent" and desk.pending is not None
    step(desk, 0.15)
    assert desk.events()[-3:] == ["sent", "unknown", "sent"]
    unknown = [json.loads(x) for x in desk.journal.getvalue().splitlines()][-2]
    assert unknown["pc_monotonic_s"] - 100.0 >= 2.5
    assert parse_frame(desk.sent[3])[0] == 1  # the ping goes next


def test_other_commands_keep_the_1_5_s_window(desk):
    desk.observe([info(7)])
    append(desk.inbox, '{"cmd": "mark_event", "event": "cuff_end"}\n')
    desk.service()
    assert parse_frame(desk.sent[0]) == (3, 100, b"\x02")
    step(desk, 1.45)
    assert desk.events()[-1] == "sent" and len(desk.sent) == 3
    step(desk, 0.2)
    assert desk.events()[-1] == "unknown"


def test_an_answer_after_unknown_is_a_late_ack(desk):
    desk.observe([info(7)])
    append(desk.inbox, '{"cmd": "set_ppg_led", "green": 18, "red": 36, "ir": 36}\n'
                       '{"cmd": "ping"}\n')
    desk.service()
    step(desk, 2.55)
    assert desk.events()[-2:] == ["unknown", "sent"]
    # The ping is pending; the LED answer comes now. Wrong CMD_ID: not it. Then
    # the right one, then a repeat of it (journaled once).
    desk.observe([ack_packet(7, 0, 1, 100), ack_packet(7, 1, 2, 100, gen=2),
                  ack_packet(7, 2, 2, 100, gen=2)])
    entries = [json.loads(x) for x in desk.journal.getvalue().splitlines()]
    late = [e for e in entries if e["event"] == "late_ack"]
    assert len(late) == 1
    assert (late[0]["line"], late[0]["cmd_seq"], late[0]["result"],
            late[0]["generation"], late[0]["ack_seq"]) == (1, 100, "ok", 2, 1)
    assert late[0]["after_first_send_s"] >= 2.5
    # The ping is still pending, and the unknown entry stays in the journal.
    assert desk.pending["cmd_seq"] == 101 and "unknown" in desk.events()
    desk.observe([ack_packet(7, 3, 1, 101)])
    assert desk.events()[-1] == "acked" and desk.pending is None


def test_device_command_cli_lines(tmp_path, capsys):
    inbox = tmp_path / "command_inbox.jsonl"
    inbox.write_bytes(b"")
    base = ["--recording", str(tmp_path)]
    device_command([*base, "mark", "--event", "cuff_end"])
    device_command([*base, "mark", "--event", "operator"])
    device_command([*base, "set-ppg-led", "--green", "127", "--red", "36", "--ir", "36"])
    assert "queued (not yet sent)" in capsys.readouterr().out
    # Above the study ceiling: refused before anything is written.
    with pytest.raises(SystemExit) as refused:
        device_command([*base, "set-ppg-led", "--green", "18", "--red", "128",
                        "--ir", "36"])
    assert refused.value.code == 1 and "ceiling" in capsys.readouterr().err
    with pytest.raises(SystemExit):  # not an operator code
        device_command([*base, "mark", "--event", "t0"])
    device_command([*base, "set-ppg-led", "--green", "18", "--red", "128", "--ir", "36",
                    "--allow-over-firmware-limit"])
    lines = [json.loads(x) for x in inbox.read_text(encoding="utf-8").splitlines()]
    assert lines == [
        {"cmd": "mark_event", "event": "cuff_end"},
        {"cmd": "mark_event", "event": "operator"},
        {"cmd": "set_ppg_led", "green": 127, "red": 36, "ir": 36},
        {"cmd": "set_ppg_led", "green": 18, "red": 128, "ir": 36,
         "allow_over_firmware_limit": True},
    ]


def test_record_mark_event_and_over_limit_logger_integration(tmp_path):
    # Logger side only: FakeDevice stands in for the firmware (its result 8 is a
    # stand-in); the firmware's own refusal of 0x80 and above is checked on
    # the C code in tests/test_firmware_control.py.
    sim = json.loads(SIM_V02.read_bytes())
    meta = session_metadata(sim, "valid", "0" * 64)
    meta_path = tmp_path / "meta.json"
    meta_path.write_text(json.dumps(meta), encoding="utf-8")
    out = tmp_path / "rec"
    entries = ({"cmd": "mark_event", "event": "cuff_end"},
               {"cmd": "set_ppg_led", "green": 18, "red": 200, "ir": 36,
                "allow_over_firmware_limit": True},
               {"cmd": "mark_event", "event": "operator"})
    device = FakeDevice(out, entries=entries, filler_code=1)
    record(device, out, LOGGER_CONFIG, meta_path, ROOT, "fake", commands=True,
           clock=lambda: device.now)
    journal = [json.loads(x) for x in
               (out / "commands_sent.jsonl").read_text(encoding="utf-8").splitlines()]
    assert [e["event"] for e in journal] == ["queued"] * 3 + ["sent", "acked"] * 3
    assert journal[1]["command"]["allow_over_firmware_limit"] is True
    sent = [bytes.fromhex(e["bytes_hex"]) for e in journal if e["event"] == "sent"]
    assert [parse_frame(f)[2][-3:] for f in sent] == [b"\x02", bytes([18, 200, 36]),
                                                      b"\x04"]
    decode = json.loads((out / "decode.json").read_bytes())
    s = decode["sessions"][0]
    assert [(a["cmd"], a["result"]) for a in s["commands"]] == [
        ("mark_event", "ok"), ("set_ppg_led", "out_of_range"), ("mark_event", "ok")]
    # The marks reach the decode as events with codes 2 and 4 (the fillers are
    # code 1); the firmware's refusal is reported, the marks are not issues.
    assert [e["data"][0] for e in s["events"] if e["data"][0] != 1] == [2, 4]
    counts = decode["issue_counts"]
    assert counts.get("command_failed") == 1
    assert not {"command_ack_invalid", "unknown_event_code",
                "events_lost_before_send", "event_ordinal_inconsistent"} & set(counts)
