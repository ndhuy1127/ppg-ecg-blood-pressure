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

MARK_EVENT (proposed 2026-11-07, pending team review): the device times the
event when the command arrives, so a mark is (re)sent only while it is at most
``MARK_EVENT_MAX_AGE_S`` old, counted from when the record loop read it from
the inbox and checked on a fresh clock reading right before each port write.
One that cannot be sent in time (another command still outstanding, no
SESSION_ID yet) is journaled ``expired`` and never sent; one sent but not
answered whose next send would come too late is ``unknown`` with reason
``mark_event_age_limit``. A port write that takes fewer bytes than the frame is
an error in the journal (``short write``). An inbox that can no longer be read
(deleted, say) is journaled ``inbox_unreadable`` and no longer read; the
recording goes on. With ``notify`` set, each outcome (answered, unknown, late,
rejected, expired, cancelled, not sent, a failed port write, an inbox problem)
is also written as one line for the operator.
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
MARK_EVENT_MAX_AGE_S = 1.0
NAMES = {cmd_id: name for name, cmd_id in COMMANDS.items()}


class CommandDesk:
    def __init__(self, inbox_path, journal, write, clock, first_seq=None,
                 notify=None):
        self.inbox_path, self.journal, self.write, self.clock = (
            inbox_path, journal, write, clock)
        self.notify = notify
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
        if self.notify is not None:
            text = _operator_text(event, fields)
            if text is not None:
                self.notify(text)

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
                self._log("acked", line=p["line"], cmd=NAMES[p["cmd_id"]],
                          cmd_seq=p["cmd_seq"], result=ack["result"],
                          generation=ack["generation"], ack_seq=packet.seq)
                self.pending = None
            elif key in self.unknown and self.unknown[key]["cmd_id"] == ack["cmd_id"]:
                late = self.unknown.pop(key)
                self._log("late_ack", line=late["line"], cmd=NAMES[late["cmd_id"]],
                          cmd_seq=late["cmd_seq"], result=ack["result"],
                          generation=ack["generation"],
                          ack_seq=packet.seq,
                          after_first_send_s=round(self.clock() - late["first_sent"], 6))

    def _cancel_on_new_session(self, new_session):
        if self.pending is not None:
            p = self.pending
            self._log("session_changed", line=p["line"], cmd=NAMES[p["cmd_id"]],
                      cmd_seq=p["cmd_seq"], old_session=p["session"],
                      new_session=new_session)
            self.pending = None

    def _read_inbox(self):
        if not self.inbox_open:
            return
        try:
            with open(self.inbox_path, "rb") as inbox:
                inbox.seek(0, 2)
                size = inbox.tell()
                if size < self.offset:
                    self._log("inbox_truncated", size=size, offset=self.offset)
                    self.inbox_open = False
                    return
                inbox.seek(self.offset)
                data = inbox.read()
            # The age of a mark starts here, for every line of this read: journal
            # lines and messages about earlier lines must not make it look younger.
            read_at = self.clock()
        except OSError as exc:  # never stops the recording
            self._log("inbox_unreadable", error=f"{type(exc).__name__}: {exc}")
            self.inbox_open = False
            return
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
            self.queue.append((self.lines, entry, read_at))
            self._log("queued", line=self.lines, command=entry)
        if self.skipping or len(rest) > MAX_LINE:
            # Dropped through its newline; it is rejected (and counted) there.
            self.skipping, rest = True, b""
        self.partial = rest

    def _send(self):
        """Send the pending command (again). A mark past its age is not sent:
        the clock is read here, right before the write, since journal lines and
        operator messages before it take time too."""
        p = self.pending
        now = self.clock()
        if self._too_old(p["cmd_id"], p["queued_at"], now):
            if p["attempt"] == 0:
                self._log("expired", line=p["line"], cmd=NAMES[p["cmd_id"]],
                          waited_s=round(now - p["queued_at"], 6),
                          limit_s=MARK_EVENT_MAX_AGE_S)
            else:
                self._log("unknown", line=p["line"], cmd=NAMES[p["cmd_id"]],
                          cmd_seq=p["cmd_seq"], attempts=p["attempt"],
                          reason="mark_event_age_limit")
                self.unknown[(p["session"], p["cmd_seq"])] = p
            self.pending = None
            return
        p["attempt"] += 1
        p["sent_at"] = now
        if p["attempt"] == 1:
            p["first_sent"] = p["sent_at"]
        self.next_send = p["sent_at"] + RETRY_S
        try:
            written = self.write(p["frame"])
            error = None if written == len(p["frame"]) else (
                f"short write: {written} of {len(p['frame'])} bytes")
        except Exception as exc:  # serial write timeout or a closed port
            written, error = 0, f"{type(exc).__name__}: {exc}"
        self._log("sent", line=p["line"], cmd=NAMES[p["cmd_id"]], cmd_seq=p["cmd_seq"],
                  session=p["session"], attempt=p["attempt"],
                  bytes_hex=p["frame"].hex(), written=written, error=error)

    def _too_old(self, cmd_id, queued_at, now):
        return cmd_id == COMMANDS["mark_event"] and now - queued_at > MARK_EVENT_MAX_AGE_S

    def _expire_marks(self, now):
        """Drop queued marks that can no longer be sent in time."""
        kept = []
        for line, entry, queued_at in self.queue:
            if self._too_old(COMMANDS.get(entry["cmd"]), queued_at, now):
                self._log("expired", line=line, cmd=entry["cmd"],
                          waited_s=round(now - queued_at, 6),
                          limit_s=MARK_EVENT_MAX_AGE_S)
            else:
                kept.append((line, entry, queued_at))
        self.queue = kept

    def service(self):
        self._read_inbox()
        now = self.clock()
        p = self.pending
        if p is not None and now >= self.next_send:
            if p["attempt"] < ATTEMPTS:
                self._send()  # or, for a mark too old by then, unknown
            elif now >= p["first_sent"] + ACK_WAIT_S.get(p["cmd_id"], 0.0):
                self._log("unknown", line=p["line"], cmd=NAMES[p["cmd_id"]],
                          cmd_seq=p["cmd_seq"], attempts=p["attempt"])
                self.unknown[(p["session"], p["cmd_seq"])] = p
                self.pending = None
        self._expire_marks(now)
        while self.pending is None and self.queue and self.issued >= 1 << 16:
            line, _, _ = self.queue.pop(0)
            self._log("rejected", line=line, error="CMD_SEQ values used up in this "
                                                   "recording")
        if (self.pending is None and self.queue and self.session_id is not None
                and now >= self.next_send):
            line, entry, queued_at = self.queue.pop(0)
            cmd_id, params = command_from_json(entry, self.session_id)
            self.issued += 1
            self.seq = (self.seq + 1) & 0xFFFF
            self.pending = {"line": line, "cmd_id": cmd_id, "cmd_seq": self.seq,
                            "session": self.session_id, "attempt": 0, "sent_at": 0.0,
                            "first_sent": 0.0, "queued_at": queued_at,
                            "frame": encode_command(cmd_id, self.seq, params)}
            self._send()

    def close(self):
        """End of the recording: what is left is not known or not sent."""
        self._read_inbox()
        if self.pending is not None:
            p = self.pending
            self._log("unknown", line=p["line"], cmd=NAMES[p["cmd_id"]],
                      cmd_seq=p["cmd_seq"], attempts=p["attempt"],
                      reason="recording ended")
            self.pending = None
        for line, entry, _ in self.queue:
            self._log("not_sent", line=line, cmd=entry["cmd"], reason="recording ended")
        self.queue = []


def _operator_text(event, fields):
    """One line for the operator about a journal step; None for steps that are
    not an outcome (queued, a normal send)."""
    what = f"command line {fields.get('line')} ({fields.get('cmd', 'unparsed')})"
    if event == "acked":
        generation = (f", LED generation {fields['generation']}"
                      if fields["generation"] else "")
        text = f"{what}: device answered {fields['result']}{generation}"
        return text if fields["result"] == "ok" else "WARNING: " + text
    if event == "late_ack":
        return (f"WARNING: {what}: late answer {fields['result']} "
                f"{fields['after_first_send_s']:.1f} s after the first send; it was "
                "already logged unknown")
    if event == "unknown":
        reason = fields.get("reason")
        why = {"mark_event_age_limit": f"no answer within {MARK_EVENT_MAX_AGE_S:g} s, "
                                       "not sent again (the mark may be missing)",
               "recording ended": "recording ended before an answer"}.get(
                   reason, f"no answer after {fields['attempts']} sends")
        return f"WARNING: {what}: outcome unknown, {why}"
    if event == "expired":
        return (f"WARNING: {what}: NOT SENT, waited {fields['waited_s']:.1f} s (limit "
                f"{fields['limit_s']:g} s); write the time down by hand")
    if event == "rejected":
        return f"WARNING: inbox line {fields['line']} rejected: {fields['error']}"
    if event == "session_changed":
        return (f"WARNING: {what}: cancelled, SESSION_ID changed (MCU restart); send "
                "it again if still needed")
    if event == "not_sent":
        return f"WARNING: {what}: not sent, {fields['reason']}"
    if event == "inbox_truncated":
        return "WARNING: command inbox was truncated; no further commands are read"
    if event == "inbox_unreadable":
        return (f"WARNING: command inbox cannot be read ({fields['error']}); no further "
                "commands are read, the recording goes on")
    if event == "sent" and fields["error"] is not None:
        return f"WARNING: {what}: port write failed: {fields['error']}"
    return None
