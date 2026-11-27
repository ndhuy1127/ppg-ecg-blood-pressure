"""The ledger of one study session (visit) in the session app (``session-app-v0``).

Pure code: the app calls these methods with the time ``now`` (monotonic seconds
of the PC) when the operator presses a button or the logger stream shows a device
event; nothing here opens a port or a file or draws anything. Every accepted step
and every refused or odd one goes to ``journal`` (``session-app-journal-v0``), the
session journal of spec section 7. A refused operation raises ``VisitError`` and
changes nothing.

Rules (spec sections 4-7 and 10, decided 2026-11-27; values in
``configs/session_app/session_app_v0.json``):

- one attempt open at a time; an attempt is a cuff inflation of a slot (M0 x2,
  M1, M2) or a screening inflation (session 1, two, both arms);
- a repeat only at M0, of a closed attempt that had no result or whose motion
  the operator marked before its t0; at most 2 per session; never after a
  device error;
- the "Motion" mark locks at t0: a later mark is only a deviation;
- inflations count across recordings and MCU restarts, screening included,
  against the cap (6, or 4 with only M0, plus 2 in session 1);
- at least 2 minutes from the end of one inflation to the next;
- safety (any reading, screening included): SBP >= 180 or DBP >= 110 asks to
  stop the session; a mean of the M0 readings >= 140/90 takes M1 and M2 out.
  The app shows the rule; the operator decides (``stop_visit``);
- device events: t0 (code 1) goes to the open attempt; cuff_end (code 2) to the
  latest attempt with a t0 in the same recording and MCU session and no end yet;
  an operator mark (code 4) is matched, in order, to the code-4 commands this
  visit queued (phase start, motion, event), so a motion or event mark is never
  taken for a phase mark.

Limits: a code-4 event lost after its command was acknowledged shifts the later
marks of the queue; the cross-check against ``decode.json`` after the session
(spec section 7) catches it. The phase of a mark is the one the app sent, not
read from the packet (code-4 packets carry no text).
"""

from dataclasses import asdict, dataclass

VERSION = "session-app-v0"
JOURNAL_VERSION = "session-app-journal-v0"
PHASES = ("M0", "M1", "M2")
SCREEN = "SCREEN"
STATUSES = ("valid", "no_result", "device_error")
REPEAT_REASONS = ("no_result", "observed_motion")
MARK_KINDS = ("phase_M1", "phase_M2", "motion", "event")
EVENT_T0, EVENT_CUFF_END, EVENT_MARK = 1, 2, 4
SESSIONS = {"S001": 1, "S002": 2}


class VisitError(ValueError):
    """An operation the rules refuse; the visit is unchanged."""


class NeedsConfirmation(VisitError):
    """A label outside the usual range: confirm it to keep it (never refused)."""

    def __init__(self, fields):
        super().__init__(f"Outside the usual range, confirm: {', '.join(fields)}")
        self.fields = fields


@dataclass
class Attempt:
    key: str                      # E01... for M0-M2, SCR1/SCR2 for screening
    phase: str
    opened_s: float
    planned_t0_s: float | None = None
    repeat_of: str | None = None
    repeat_reason: str | None = None
    motion: bool = False          # operator saw motion and marked it before t0
    recording: str | None = None
    device_session_id: int | None = None
    t0_ordinal: int | None = None
    t0_s: float | None = None
    phase_mark_ordinal: int | None = None
    cuff_end_ordinal: int | None = None
    cuff_end_s: float | None = None
    result_shown_s: float | None = None
    needs_deviation_reason: bool = False
    deviation_reason: str | None = None
    status: str | None = None
    sbp_mmhg: int | None = None
    dbp_mmhg: int | None = None
    pulse_rate_bpm: int | None = None
    note: str = ""
    safety_stop: bool = False
    aborted: str | None = None    # reason, for an attempt closed without a label
    closed: bool = False

    @property
    def inflated(self):
        """A real inflation: screening, a t0 from the board, or a cuff result."""
        return (self.phase == SCREEN or self.t0_s is not None
                or self.status is not None)


class Visit:
    def __init__(self, subject_id, session_id, config, m0_only=False):
        if config.get("version") != VERSION:
            raise VisitError(f"Config version must be {VERSION}")
        if session_id not in SESSIONS:
            raise VisitError("session_id must be S001 or S002 (protocol section 3)")
        self.subject_id, self.session_id, self.config = subject_id, session_id, config
        self.session_number = SESSIONS[session_id]
        self.m0_only = m0_only
        self.attempts, self.journal = [], []
        self.recording = self.device_session_id = None
        self.pending_marks = []       # kinds of the code-4 commands sent, in order
        self.phase_marks = {}         # phase -> (recording, device session, ordinal)
        self.started_s = self.stopped = self.last_inflation_end_s = None
        self.stopped_phases, self._stop_trigger = set(), None
        self._log("visit_created", None, subject_id=subject_id, session_id=session_id,
                  m0_only=m0_only, version=JOURNAL_VERSION)

    # -- journal and state ---------------------------------------------------
    def _log(self, entry_type, now, /, **fields):
        entry = {"t_s": now, "type": entry_type, **fields}
        self.journal.append(entry)
        return entry

    def _refuse(self, now, why, **fields):
        self._log("refused", now, reason=why, **fields)
        raise VisitError(why)

    @property
    def open_attempt(self):
        return next((a for a in self.attempts if not a.closed), None)

    def attempt(self, key):
        return next((a for a in self.attempts if a.key == key), None)

    def inflations(self):
        return sum(a.inflated for a in self.attempts)

    def m0_readings(self):
        return [(a.sbp_mmhg, a.dbp_mmhg) for a in self.attempts
                if a.phase == "M0" and a.status == "valid"]

    def maneuvers_skipped(self):
        """Safety rule (b): mean of the M0 readings >= 140/90 (every valid M0
        reading of the session)."""
        readings = self.m0_readings()
        if not readings:
            return False
        rule = self.config["safety"]
        sbp = sum(r[0] for r in readings) / len(readings)
        dbp = sum(r[1] for r in readings) / len(readings)
        return (sbp >= rule["skip_maneuvers_m0_mean_sbp"]
                or dbp >= rule["skip_maneuvers_m0_mean_dbp"])

    def cap(self):
        caps = self.config["inflation_cap"]
        base = caps["m0_only" if self.m0_only or self.maneuvers_skipped() else "full"]
        return base + (self.config["screening_inflations_session1"]
                       if self.session_number == 1 else 0)

    # -- recording and device session -----------------------------------------
    def start(self, now):
        self.started_s = now
        self._log("visit_started", now)

    def recording_started(self, recording, now):
        self.recording, self.device_session_id = recording, None
        self.pending_marks.clear()
        self._log("recording_started", now, recording=recording)

    def device_session(self, device_session_id, now):
        """A SESSION_ID seen in the stream. A new one after another is an MCU
        restart: marks still waiting for their event are dropped (spec 6.6)."""
        if device_session_id == self.device_session_id:
            return
        restart = self.device_session_id is not None
        dropped = list(self.pending_marks) if restart else []
        if restart:
            self.pending_marks.clear()
        self.device_session_id = device_session_id
        self._log("mcu_restart" if restart else "device_session", now,
                  device_session_id=device_session_id, dropped_marks=dropped)

    # -- attempts ------------------------------------------------------------
    def open(self, phase, now, planned_t0_s=None, repeat_of=None, repeat_reason=None):
        """Open an attempt of ``phase`` (M0, M1, M2 or SCREEN)."""
        if self.stopped:
            self._refuse(now, "the session was stopped")
        if self.open_attempt is not None:
            self._refuse(now, f"attempt {self.open_attempt.key} is still open")
        if phase not in (*PHASES, SCREEN):
            self._refuse(now, f"phase must be one of {(*PHASES, SCREEN)}")
        if phase in self.stopped_phases:
            self._refuse(now, f"{phase} was stopped")
        if phase in ("M1", "M2") and (self.m0_only or self.maneuvers_skipped()):
            self._refuse(now, f"{phase} is not done in this session (M0 only, or the "
                              "mean of the M0 readings reached 140/90)")
        rest = self.config["rest_between_inflations_s"]
        if (self.last_inflation_end_s is not None
                and now - self.last_inflation_end_s < rest):
            self._refuse(now, f"rest at least {rest} s between inflations "
                              f"({now - self.last_inflation_end_s:.0f} s so far)")
        if self.inflations() >= self.cap():
            self._refuse(now, f"inflation cap {self.cap()} reached")
        same = [a for a in self.attempts if a.phase == phase]
        if phase == SCREEN:
            if self.session_number != 1:
                self._refuse(now, "screening inflations only in session 1")
            if len(same) >= self.config["screening_inflations_session1"]:
                self._refuse(now, "both screening inflations are done")
            if repeat_of is not None:
                self._refuse(now, "screening inflations are not repeated")
        elif repeat_of is None:
            # An attempt closed before any inflation does not take a slot.
            taken = sum(a.repeat_of is None and (a.inflated or not a.closed) for a in same)
            if taken >= self.config["slots_per_phase"][phase]:
                self._refuse(now, f"every {phase} slot has its scheduled attempt; a "
                                  "repeat needs repeat_of")
        else:
            self._check_repeat(phase, repeat_of, repeat_reason, now)
        if phase == SCREEN:
            key = f"SCR{len(same) + 1}"
        else:
            key = f"E{sum(a.phase != SCREEN for a in self.attempts) + 1:02d}"
        attempt = Attempt(key=key, phase=phase, opened_s=now, planned_t0_s=planned_t0_s,
                          repeat_of=repeat_of, repeat_reason=repeat_reason)
        self.attempts.append(attempt)
        self._log("attempt_opened", now, key=key, phase=phase, planned_t0_s=planned_t0_s,
                  repeat_of=repeat_of, repeat_reason=repeat_reason)
        return attempt

    def _check_repeat(self, phase, repeat_of, reason, now):
        if phase not in self.config["repeat_phases"]:
            self._refuse(now, f"repeats only at {self.config['repeat_phases']} "
                              "(SAP section 2)")
        if reason not in REPEAT_REASONS:
            self._refuse(now, f"repeat reason must be one of {REPEAT_REASONS}")
        parent = self.attempt(repeat_of)
        if (parent is None or parent.phase != phase or not parent.closed
                or parent.status is None):
            self._refuse(now, f"{repeat_of} is not a labelled {phase} attempt")
        if parent.status == "device_error":
            self._refuse(now, "a device error stops the session; no repeat")
        if any(a.repeat_of == repeat_of for a in self.attempts):
            self._refuse(now, f"{repeat_of} is already repeated")
        if reason == "no_result" and parent.status != "no_result":
            self._refuse(now, f"{repeat_of} has a result ({parent.status})")
        if reason == "observed_motion" and not parent.motion:
            self._refuse(now, f"no motion was marked before the t0 of {repeat_of}")
        if sum(a.repeat_of is not None for a in self.attempts) >= self.config["max_repeats"]:
            self._refuse(now, f"at most {self.config['max_repeats']} repeats per session")

    def mark_motion(self, now, note=""):
        """The operator saw motion in the window before the cuff. Only before t0
        does it count (and allow a repeat); later it is a deviation. Returns True
        when the mark counts; the app then sends the code-4 command."""
        attempt = self.open_attempt
        if attempt is None:
            self._refuse(now, "no open attempt")
        if attempt.t0_s is not None:
            self._log("deviation", now, key=attempt.key, kind="motion_after_t0",
                      note=note)
            return False
        attempt.motion = True
        self.pending_marks.append("motion")
        self._log("motion_marked", now, key=attempt.key, note=note)
        return True

    def send_mark(self, kind, now, **fields):
        """A code-4 command queued by the app: ``phase_M1`` (paced breathing
        starts), ``phase_M2`` (starting number read out) or ``event``."""
        if kind not in MARK_KINDS or kind == "motion":
            self._refuse(now, "use mark_motion for motion")
        phase = kind.split("_", 1)[1] if kind.startswith("phase_") else None
        if phase is not None and (self.m0_only or self.maneuvers_skipped()
                                  or phase in self.stopped_phases or self.stopped):
            self._refuse(now, f"{phase} is not done in this session")
        self.pending_marks.append(kind)
        self._log("mark_sent", now, kind=kind, **fields)

    def command_failed(self, kind, now):
        """The command of a mark failed or ended unknown: no event to wait for."""
        if kind in self.pending_marks:
            self.pending_marks.remove(kind)
        self._log("mark_command_failed", now, kind=kind)

    def device_event(self, code, ordinal, now):
        """An event packet (0xC1) of the stream, in the current recording and
        device session."""
        where = {"recording": self.recording, "device_session_id": self.device_session_id,
                 "ordinal": ordinal}
        if code == EVENT_T0:
            attempt = self.open_attempt
            if attempt is None or attempt.phase == SCREEN or attempt.t0_s is not None:
                self._log("t0_outside_attempt", now, **where)
                return None
            attempt.recording, attempt.device_session_id = (self.recording,
                                                            self.device_session_id)
            attempt.t0_ordinal, attempt.t0_s = ordinal, now
            mark = self.phase_marks.get(attempt.phase)
            if mark is not None and mark[:2] == (self.recording, self.device_session_id):
                attempt.phase_mark_ordinal = mark[2]
            late = self.config["reminders_s"]["t0_late_vs_plan"]
            if (attempt.planned_t0_s is not None
                    and abs(now - attempt.planned_t0_s) > late):
                attempt.needs_deviation_reason = True
            self._log("t0", now, key=attempt.key, **where,
                      planned_t0_s=attempt.planned_t0_s)
            return attempt.key
        if code == EVENT_CUFF_END:
            with_t0 = [a for a in self.attempts if a.t0_s is not None]
            last = with_t0[-1] if with_t0 else None
            if (last is None or last.cuff_end_ordinal is not None
                    or (last.recording, last.device_session_id)
                    != (self.recording, self.device_session_id)):
                self._log("cuff_end_outside_attempt", now, **where)
                return None
            last.cuff_end_ordinal, last.cuff_end_s = ordinal, now
            self.last_inflation_end_s = now
            self._log("cuff_end", now, key=last.key, **where)
            return last.key
        if code == EVENT_MARK:
            if not self.pending_marks:
                self._log("unmatched_mark", now, **where)
                return None
            kind = self.pending_marks.pop(0)
            if kind.startswith("phase_"):
                self.phase_marks[kind.split("_", 1)[1]] = (self.recording,
                                                           self.device_session_id, ordinal)
            self._log("mark_event", now, kind=kind, **where)
            return kind
        self._log("other_event", now, code=code, **where)
        return None

    def false_t0(self, now, reason):
        """The t0 of the open attempt was pressed by mistake (no inflation)."""
        attempt = self.open_attempt
        if attempt is None or attempt.t0_s is None or attempt.cuff_end_s is not None:
            self._refuse(now, "no t0 to withdraw")
        if not reason:
            self._refuse(now, "a reason is needed")
        self._log("false_t0", now, key=attempt.key, ordinal=attempt.t0_ordinal,
                  reason=reason)
        attempt.t0_ordinal = attempt.t0_s = attempt.phase_mark_ordinal = None
        attempt.recording = attempt.device_session_id = None
        attempt.needs_deviation_reason = False

    def result_shown(self, now):
        attempt = self.open_attempt
        if attempt is None:
            self._refuse(now, "no open attempt")
        attempt.result_shown_s = now
        self._log("result_shown", now, key=attempt.key)

    def label(self, status, now, sbp=None, dbp=None, pulse=None, note="", confirm=False,
              deviation_reason=None):
        """The cuff result of the open attempt; closes it. Returns the safety
        actions the app must show: ``stop_visit`` (a reading >= 180/110, or a
        device error) and ``skip_maneuvers`` (mean of the M0 readings now
        >= 140/90)."""
        attempt = self.open_attempt
        if attempt is None:
            self._refuse(now, "no open attempt")
        if status not in STATUSES:
            self._refuse(now, f"status must be one of {STATUSES}")
        values = {"sbp_mmhg": sbp, "dbp_mmhg": dbp, "pulse_rate_bpm": pulse}
        if status == "valid":
            for name in ("sbp_mmhg", "dbp_mmhg"):
                if not isinstance(values[name], int) or isinstance(values[name], bool):
                    self._refuse(now, f"{name} must be an integer")
            if not dbp < sbp:
                self._refuse(now, "DBP must be below SBP")
        elif sbp is not None or dbp is not None:
            self._refuse(now, "only a valid result carries SBP/DBP")
        if pulse is not None and (not isinstance(pulse, int) or isinstance(pulse, bool)):
            self._refuse(now, "pulse_rate_bpm must be an integer")
        if attempt.needs_deviation_reason and not deviation_reason:
            self._refuse(now, "t0 was more than "
                              f"{self.config['reminders_s']['t0_late_vs_plan']} s off the "
                              "plan: give the reason")
        ranges = self.config["label_ranges"]
        outside = [name for name, value in values.items()
                   if value is not None and not ranges[name][0] <= value <= ranges[name][1]]
        if outside and not confirm:
            self._log("label_needs_confirmation", now, key=attempt.key, fields=outside)
            raise NeedsConfirmation(outside)
        skipped_before = self.maneuvers_skipped()
        attempt.status, attempt.note = status, note
        attempt.sbp_mmhg, attempt.dbp_mmhg, attempt.pulse_rate_bpm = sbp, dbp, pulse
        attempt.deviation_reason = deviation_reason
        attempt.closed = True
        end = attempt.cuff_end_s or now
        self.last_inflation_end_s = max(end, self.last_inflation_end_s or end)
        actions = []
        rule = self.config["safety"]
        if status == "valid" and (sbp >= rule["stop_sbp"] or dbp >= rule["stop_dbp"]):
            actions.append("stop_visit")
            self._stop_trigger = attempt.key
        if status == "device_error":
            actions.append("stop_visit")
        if not skipped_before and self.maneuvers_skipped():
            actions.append("skip_maneuvers")
        self._log("labelled", now, key=attempt.key, status=status, sbp=sbp, dbp=dbp,
                  pulse=pulse, outside_confirmed=outside, deviation_reason=deviation_reason,
                  actions=actions, note=note)
        return actions

    def abort(self, now, reason):
        """Close the open attempt without a label (spec 4: never "no_result")."""
        attempt = self.open_attempt
        if attempt is None:
            self._refuse(now, "no open attempt")
        if not reason:
            self._refuse(now, "a reason is needed")
        attempt.aborted, attempt.closed = reason, True
        if attempt.inflated:
            self.last_inflation_end_s = attempt.cuff_end_s or now
        self._log("attempt_aborted", now, key=attempt.key, reason=reason,
                  inflated=attempt.inflated)

    # -- stops -------------------------------------------------------------
    def stop_maneuver(self, phase, now, reason):
        if phase not in ("M1", "M2"):
            self._refuse(now, "only M1 or M2 can be stopped on its own")
        self.stopped_phases.add(phase)
        attempt = self.open_attempt
        if attempt is not None and attempt.phase == phase:
            attempt.safety_stop = True
        self._log("maneuver_stopped", now, phase=phase, reason=reason)

    def stop_visit(self, now, reason):
        """Stop the session (safety document section 4). The open attempt and the
        attempt whose reading asked for the stop carry ``safety_stop``."""
        self.stopped = reason
        for attempt in (self.open_attempt, self.attempt(self._stop_trigger or "")):
            if attempt is not None:
                attempt.safety_stop = True
        self._log("visit_stopped", now, reason=reason)

    # -- reminders and outputs -----------------------------------------------
    def reminders(self, now):
        """What the app should show now: overdue cuff end, rest still needed,
        session time."""
        out, times = [], self.config["reminders_s"]
        attempt = self.open_attempt
        if (attempt is not None and attempt.t0_s is not None and attempt.cuff_end_s is None
                and now - attempt.t0_s >= times["cuff_end_after_t0"]):
            out.append(("press_cuff_end", attempt.key))
        rest = self.config["rest_between_inflations_s"]
        if self.last_inflation_end_s is not None and now - self.last_inflation_end_s < rest:
            out.append(("rest_s_left", round(rest - (now - self.last_inflation_end_s))))
        if self.started_s is not None:
            if now - self.started_s >= times["visit_cap"]:
                out.append(("visit_cap_reached", None))
            elif now - self.started_s >= times["visit_warn"]:
                out.append(("visit_time_warning", None))
        return out

    def exceptions(self):
        """M0-M2 inflations that cannot go into the cuff log (spec section 7):
        no t0 from the board, or closed without a label."""
        out = []
        for a in self.attempts:
            if a.phase == SCREEN or not a.inflated:
                continue
            if a.t0_s is None:
                out.append({"key": a.key, "why": "no_t0", "status": a.status})
            elif a.status is None:
                out.append({"key": a.key, "why": "no_label", "aborted": a.aborted})
        return out

    def cuff_log_rows(self, led_readjusted, pilot):
        """Rows of ``cuff-log-v2`` (docs/data_convention.md 4.4), in attempt order:
        every closed M0-M2 attempt with a t0 and a label. Screening stays out."""
        rows, keys = [], set()
        for a in self.attempts:
            if a.phase == SCREEN or a.t0_s is None or a.status is None:
                continue
            if a.repeat_of is not None and a.repeat_of not in keys:
                raise VisitError(f"{a.key} repeats {a.repeat_of}, which has no row "
                                 "(no t0 or no label); resolve it in the journal first")
            keys.add(a.key)

            def text(value):
                return "" if value is None else str(value)

            rows.append({
                "recording": a.recording, "event_id": a.key, "phase": a.phase,
                "device_session_id": text(a.device_session_id),
                "t0_event_ordinal": text(a.t0_ordinal),
                "phase_mark_event_ordinal": text(a.phase_mark_ordinal),
                "cuff_end_event_ordinal": text(a.cuff_end_ordinal),
                "sbp_mmhg": text(a.sbp_mmhg), "dbp_mmhg": text(a.dbp_mmhg),
                "pulse_rate_bpm": text(a.pulse_rate_bpm), "status": a.status,
                "safety_stop": str(int(a.safety_stop)),
                "led_readjusted": str(int(led_readjusted)), "pilot": str(int(pilot)),
                "note": a.note, "repeat_of_event_id": text(a.repeat_of),
                "repeat_reason": text(a.repeat_reason)})
        return rows

    def snapshot(self):
        """The attempts as plain dicts, for the report and the printed form."""
        return [asdict(a) for a in self.attempts]
