"""Commands PC -> device during ``record`` (Packet Schema V0.2 section 13).

The operator appends JSON lines to the recording's own ``command_inbox.jsonl``
(``scripts/device_command.py``); the record loop calls ``service`` after every
read of the port, bytes or not, and ``observe`` with the packets it decoded. One
command is outstanding at a time: sent, then sent again with the same CMD_SEQ
and bytes after 500 ms without its 0xD3, at most 3 times; after that its outcome
is unknown, not a failure. SET_PPG_LED is called unknown only 2.5 s after its
first send, since the firmware may take up to 2 s to answer it (decided
2026-10-29). Any two sends, new or repeated, are at least 500 ms apart (at most 2
per second). A change of SESSION_ID (MCU restart) cancels the command in flight.
A 0xD3 that comes after its command was called unknown is still matched by
CMD_SEQ and journaled as ``late_ack``; the unknown entry stays as it was.
CMD_SEQ is never reused within a recording: after 65 536 commands the rest are
refused. Every step goes to the journal (``commands_sent.jsonl``) with the PC
time (``pc_monotonic_s``), never a device time. The raw stream and its decode
do not depend on any of this. Clock and port write are passed in, so the logic
runs without a device.
"""

import json
import secrets

from software.data_io.command_wire import COMMANDS, command_from_json, encode_command
from software.data_io.packet_receiver import decode_command_ack
from software.data_io.packet_wire import COMMAND_ACK_CHANNEL

RETRY_S = 0.5
ATTEMPTS = 3
# Shortest time from the first send to "unknown", per CMD_ID; others: after the
# last attempt's RETRY_S. SET_PPG_LED: the PPG reader may take the request up to
# 2 s after it came (then it is withdrawn with BUSY), plus margin.
ACK_WAIT_S = {COMMANDS["set_ppg_led"]: 2.5}
MAX_LINE = 1024


class CommandDesk:
    def __init__(self, inbox_path, journal, write, clock, first_seq=None):
        self.inbox_path, self.journal, self.write, self.clock = (
            inbox_path, journal, write, clock)
        self.seq = secrets.randbelow(1 << 16) if first_seq is None else first_seq
        self.issued = 0
        self.offset, self.partial, self.lines = 0, b"", 0
        self.skipping = False  # inside a line longer than MAX_LINE
        self.inbox_open = True
        self.queue, self.pending, self.session_id = [], None, None
        self.unknown = {}  # (session, CMD_SEQ) -> command given up, for late_ack
        self.next_send = float("-inf")

    def _log(self, event, **fields):
        entry = {"event": event, "pc_monotonic_s": round(self.clock(), 6), **fields}
        self.journal.write(json.dumps(entry, sort_keys=True) + "\n")
        self.journal.flush()

    def observe(self, packets):
        """Decoded packets of the last chunk, in stream order."""
        for packet in packets:
            if self.session_id is not None and packet.session_id != self.session_id:
                self._cancel_on_new_session(packet.session_id)
            self.session_id = packet.session_id
            if packet.channel_id != COMMAND_ACK_CHANNEL:
                continue
            ack, problem = decode_command_ack(packet)
            if problem is not None:
                continue
            p, key = self.pending, (packet.session_id, ack["cmd_seq"])
            if p is not None and ack["cmd_id"] == p["cmd_id"] and (
                key == (p["session"], p["cmd_seq"])
            ):
                self._log("acked", line=p["line"], cmd_seq=p["cmd_seq"],
                          result=ack["result"], generation=ack["generation"],
                          ack_seq=packet.seq)
                self.pending = None
            elif key in self.unknown and self.unknown[key]["cmd_id"] == ack["cmd_id"]:
                late = self.unknown.pop(key)
                self._log("late_ack", line=late["line"], cmd_seq=late["cmd_seq"],
                          result=ack["result"], generation=ack["generation"],
                          ack_seq=packet.seq,
                          after_first_send_s=round(self.clock() - late["first_sent"], 6))

    def _cancel_on_new_session(self, new_session):
        if self.pending is not None:
            p = self.pending
            self._log("session_changed", line=p["line"], cmd_seq=p["cmd_seq"],
                      old_session=p["session"], new_session=new_session)
            self.pending = None

    def _read_inbox(self):
        if not self.inbox_open:
            return
        with open(self.inbox_path, "rb") as inbox:
            inbox.seek(0, 2)
            size = inbox.tell()
            if size < self.offset:
                self._log("inbox_truncated", size=size, offset=self.offset)
                self.inbox_open = False
                return
            inbox.seek(self.offset)
            data = inbox.read()
        self.offset += len(data)
        data = self.partial + data
        *complete, rest = data.split(b"\n")
        for raw in complete:
            self.lines += 1
            try:
                if self.skipping or len(raw) > MAX_LINE:
                    self.skipping = False
                    raise ValueError("line longer than 1024 bytes")
                entry = json.loads(raw.decode("utf-8"))
                command_from_json(entry, 0)  # validates; the session comes later
            except (ValueError, UnicodeDecodeError) as error:
                self._log("rejected", line=self.lines, error=str(error))
                continue
            self.queue.append((self.lines, entry))
            self._log("queued", line=self.lines, command=entry)
        if self.skipping or len(rest) > MAX_LINE:
            # Dropped through its newline; it is rejected (and counted) there.
            self.skipping, rest = True, b""
        self.partial = rest

    def _send(self):
        p = self.pending
        p["attempt"] += 1
        p["sent_at"] = self.clock()
        if p["attempt"] == 1:
            p["first_sent"] = p["sent_at"]
        self.next_send = p["sent_at"] + RETRY_S
        try:
            written = self.write(p["frame"])
            error = None
        except Exception as exc:  # serial write timeout or a closed port
            written, error = 0, f"{type(exc).__name__}: {exc}"
        self._log("sent", line=p["line"], cmd_seq=p["cmd_seq"], session=p["session"],
                  attempt=p["attempt"], bytes_hex=p["frame"].hex(),
                  written=written, error=error)

    def service(self):
        self._read_inbox()
        now = self.clock()
        p = self.pending
        if p is not None and now >= self.next_send:
            if p["attempt"] < ATTEMPTS:
                self._send()
            elif now >= p["first_sent"] + ACK_WAIT_S.get(p["cmd_id"], 0.0):
                self._log("unknown", line=p["line"], cmd_seq=p["cmd_seq"],
                          attempts=p["attempt"])
                self.unknown[(p["session"], p["cmd_seq"])] = p
                self.pending = None
        while self.pending is None and self.queue and self.issued >= 1 << 16:
            line, _ = self.queue.pop(0)
            self._log("rejected", line=line, error="CMD_SEQ values used up in this "
                                                   "recording")
        if (self.pending is None and self.queue and self.session_id is not None
                and now >= self.next_send):
            line, entry = self.queue.pop(0)
            cmd_id, params = command_from_json(entry, self.session_id)
            self.issued += 1
            self.seq = (self.seq + 1) & 0xFFFF
            self.pending = {"line": line, "cmd_id": cmd_id, "cmd_seq": self.seq,
                            "session": self.session_id, "attempt": 0, "sent_at": 0.0,
                            "first_sent": 0.0,
                            "frame": encode_command(cmd_id, self.seq, params)}
            self._send()

    def close(self):
        """End of the recording: what is left is not known or not sent."""
        self._read_inbox()
        if self.pending is not None:
            p = self.pending
            self._log("unknown", line=p["line"], cmd_seq=p["cmd_seq"],
                      attempts=p["attempt"], reason="recording ended")
            self.pending = None
        for line, _ in self.queue:
            self._log("not_sent", line=line, reason="recording ended")
        self.queue = []
