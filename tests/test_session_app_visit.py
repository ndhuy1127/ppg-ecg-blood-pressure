"""Session app ledger (software/session_app/visit.py): SYNTHETIC known answers."""

import json
from pathlib import Path

import pytest

from software.device import session_ingest as si
from software.session_app.visit import NeedsConfirmation, Visit, VisitError
from tests.device_fixtures import write_cuff_log

ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / "configs/session_app/session_app_v0.json").read_text(
    encoding="utf-8"))


def visit(session="S001", **kw):
    v = Visit("SUB001", session, CONFIG, **kw)
    v.start(0.0)
    v.recording_started("rec1", 0.0)
    v.device_session(1, 0.0)
    return v


def cuff(v, phase, t, t0, end, status="valid", sbp=120, dbp=78, motion=False, **kw):
    """One attempt at time ``t``: open, (motion), t0 event, cuff_end event, label."""
    v.open(phase, t, **kw)
    if motion:
        assert v.mark_motion(t + 1)
        v.device_event(4, t0 - 1, t + 2)  # the motion mark comes back as code 4
    v.device_event(1, t0, t + 10)
    v.device_event(2, end, t + 60)
    labels = {"sbp": sbp, "dbp": dbp} if status == "valid" else {}
    return v.label(status, t + 70, **labels)


def test_full_first_session_gives_a_cuff_log_the_ingest_reads(tmp_path):
    v = visit()
    for n, t in enumerate((0.0, 200.0)):  # screening, both arms
        v.open("SCREEN", t)
        v.label("valid", t + 60, sbp=118, dbp=76)
    cuff(v, "M0", 400, 0, 1)
    cuff(v, "M0", 700, 2, 3)
    v.send_mark("phase_M1", 1000)
    assert v.device_event(4, 4, 1001) == "phase_M1"
    cuff(v, "M1", 1900, 5, 6, sbp=114, dbp=74)
    v.send_mark("phase_M2", 2200)
    v.device_event(4, 7, 2201)
    cuff(v, "M2", 2290, 8, 9, sbp=130, dbp=84)
    assert v.inflations() == 6 and v.cap() == 8
    rows = v.cuff_log_rows(led_readjusted=0, pilot=0)
    # Screening stays out of the cuff log; event ids number the M0-M2 attempts.
    assert [(r["event_id"], r["phase"], r["t0_event_ordinal"], r["cuff_end_event_ordinal"],
             r["phase_mark_event_ordinal"]) for r in rows] == [
        ("E01", "M0", "0", "1", ""), ("E02", "M0", "2", "3", ""),
        ("E03", "M1", "5", "6", "4"), ("E04", "M2", "8", "9", "7")]
    log = write_cuff_log(tmp_path / "cuff_log.csv", rows, v2=True)
    cuffs = si.read_cuff_log(log, "rec1")
    assert [c["event_id"] for c in cuffs] == ["E01", "E02", "E03", "E04"]
    assert cuffs[2]["phase_mark_event_ordinal"] == 4 and cuffs[3]["sbp_mmhg"] == 130
    assert v.exceptions() == []
    assert v.journal[0]["version"] == "session-app-journal-v0"


def test_motion_before_t0_allows_one_repeat_and_its_mark_is_not_a_phase_mark(tmp_path):
    v = visit("S002")
    cuff(v, "M0", 0, 1, 2, motion=True)          # mark event ordinal 0
    assert v.attempt("E01").motion
    # A repeat for observed motion of a valid original: allowed after the rest.
    with pytest.raises(VisitError, match="rest at least 120 s"):
        v.open("M0", 100, repeat_of="E01", repeat_reason="observed_motion")
    cuff(v, "M0", 300, 3, 4, repeat_of="E01", repeat_reason="observed_motion")
    cuff(v, "M0", 600, 5, 6)
    # Motion marked after t0 is a deviation and gives no repeat.
    v.open("M1", 900)
    v.device_event(1, 7, 905)
    assert v.mark_motion(906) is False
    assert v.journal[-1]["kind"] == "motion_after_t0"
    v.device_event(2, 8, 950)
    v.label("valid", 960, sbp=110, dbp=70)
    # The phase mark sent later is matched to M2, not to an earlier motion mark.
    v.send_mark("phase_M2", 1200)
    v.device_event(4, 9, 1201)
    cuff(v, "M2", 1290, 10, 11)
    rows = {r["event_id"]: r for r in v.cuff_log_rows(0, 0)}
    assert rows["E02"]["repeat_of_event_id"] == "E01"
    assert rows["E02"]["repeat_reason"] == "observed_motion"
    assert rows["E04"]["phase_mark_event_ordinal"] == ""   # no M1 mark was sent
    assert rows["E05"]["phase_mark_event_ordinal"] == "9"
    si.read_cuff_log(write_cuff_log(tmp_path / "log.csv", list(rows.values()), v2=True),
                     "rec1")


def test_repeat_rules():
    v = visit("S002")
    cuff(v, "M0", 0, 0, 1, status="no_result")
    # A valid original without a motion mark is not repeated.
    cuff(v, "M0", 300, 2, 3)
    with pytest.raises(VisitError, match="no motion was marked"):
        v.open("M0", 600, repeat_of="E02", repeat_reason="observed_motion")
    with pytest.raises(VisitError, match="has a result"):
        v.open("M0", 600, repeat_of="E02", repeat_reason="no_result")
    # Every M0 slot has its scheduled attempt: a third original is refused.
    with pytest.raises(VisitError, match="every M0 slot"):
        v.open("M0", 600)
    cuff(v, "M0", 600, 4, 5, status="no_result", repeat_of="E01",
         repeat_reason="no_result")
    with pytest.raises(VisitError, match="already repeated"):
        v.open("M0", 900, repeat_of="E01", repeat_reason="no_result")
    cuff(v, "M0", 900, 6, 7, repeat_of="E03", repeat_reason="no_result")
    # Two repeats used.
    v.attempt("E04").status = "no_result"
    with pytest.raises(VisitError, match="at most 2 repeats"):
        v.open("M0", 1200, repeat_of="E04", repeat_reason="no_result")
    # No repeat at M1.
    cuff(v, "M1", 1200, 8, 9, status="no_result")
    with pytest.raises(VisitError, match="repeats only at"):
        v.open("M1", 1500, repeat_of="E05", repeat_reason="no_result")
    refused = [e for e in v.journal if e["type"] == "refused"]
    assert len(refused) == 6


def test_caps_and_screening():
    assert visit("S001").cap() == 8 and visit("S002").cap() == 6
    assert visit("S002", m0_only=True).cap() == 4 and visit("S001", m0_only=True).cap() == 6
    v = visit("S002")
    with pytest.raises(VisitError, match="only in session 1"):
        v.open("SCREEN", 0)
    v = visit("S001")
    v.open("SCREEN", 0)
    v.label("valid", 30, sbp=120, dbp=80)
    v.open("SCREEN", 200)
    v.label("valid", 230, sbp=121, dbp=80)
    with pytest.raises(VisitError, match="both screening"):
        v.open("SCREEN", 400)
    with pytest.raises(VisitError, match="M1 is not done|only M0"):
        visit("S002", m0_only=True).open("M1", 0)


def test_safety_rules():
    # (a) any reading, screening included, >= 180/110 asks to stop the session.
    v = visit("S001")
    v.open("SCREEN", 0)
    assert v.label("valid", 30, sbp=181, dbp=100, confirm=True) == ["stop_visit"]
    v.stop_visit(40, "reading >= 180/110")
    assert v.attempt("SCR1").safety_stop
    with pytest.raises(VisitError, match="stopped"):
        v.open("SCREEN", 400)
    # (b) mean of the M0 readings >= 140/90 takes M1 and M2 out: (150 + 136) / 2 = 143.
    v = visit("S002")
    assert cuff(v, "M0", 0, 0, 1, sbp=150, dbp=85) == ["skip_maneuvers"]
    # One reading of 150 already reaches the mean; a second lower one keeps it above.
    cuff(v, "M0", 300, 2, 3, sbp=136, dbp=85)
    assert v.maneuvers_skipped() and v.cap() == 4
    with pytest.raises(VisitError, match="M1 is not done"):
        v.open("M1", 600)
    with pytest.raises(VisitError, match="M2 is not done"):
        v.send_mark("phase_M2", 600)
    # A device error asks to stop and is never repeated.
    v = visit("S002")
    assert cuff(v, "M0", 0, 0, 1, status="device_error") == ["stop_visit"]
    with pytest.raises(VisitError, match="device error"):
        v.open("M0", 300, repeat_of="E01", repeat_reason="observed_motion")
    # Stopping M1 flags the open M1 attempt and refuses another.
    v = visit("S002")
    cuff(v, "M0", 0, 0, 1)
    cuff(v, "M0", 300, 2, 3)
    v.open("M1", 600)
    v.stop_maneuver("M1", 610, "dizziness")
    assert v.open_attempt.safety_stop
    v.abort(620, "maneuver stopped before the cuff")
    with pytest.raises(VisitError, match="M1 was stopped"):
        v.open("M1", 900)


def test_labels_are_checked_and_extremes_confirmed():
    v = visit("S002")
    v.open("M0", 0, planned_t0_s=10)
    v.device_event(1, 0, 50)   # 40 s after the plan
    v.device_event(2, 1, 100)
    with pytest.raises(VisitError, match="DBP must be below SBP"):
        v.label("valid", 110, sbp=80, dbp=90)
    with pytest.raises(VisitError, match="only a valid result"):
        v.label("no_result", 110, sbp=120)
    with pytest.raises(VisitError, match="give the reason"):
        v.label("valid", 110, sbp=120, dbp=80)
    with pytest.raises(NeedsConfirmation) as exc:
        v.label("valid", 110, sbp=210, dbp=80, pulse=35, deviation_reason="needed rest")
    assert exc.value.fields == ["sbp_mmhg", "pulse_rate_bpm"]
    assert v.open_attempt is not None  # nothing kept yet
    actions = v.label("valid", 110, sbp=210, dbp=80, pulse=35, confirm=True,
                      deviation_reason="needed rest")
    assert actions == ["stop_visit", "skip_maneuvers"]
    assert v.attempt("E01").deviation_reason == "needed rest"


def test_mcu_restart_and_stray_events(tmp_path):
    v = visit("S002")
    v.device_event(1, 0, 0)                     # t0 with no attempt open
    assert v.journal[-1]["type"] == "t0_outside_attempt"
    v.open("M0", 10)
    v.device_event(1, 1, 20)
    v.false_t0(25, "pressed twice")             # no inflation yet
    assert v.inflations() == 0
    v.device_event(1, 2, 30)
    v.send_mark("event", 31, note="cough")
    v.device_session(2, 40)                     # MCU restart: the pending mark is dropped
    assert v.journal[-1]["type"] == "mcu_restart"
    assert v.journal[-1]["dropped_marks"] == ["event"]
    v.device_event(2, 0, 80)                    # cuff_end of the new session: not E01's
    assert v.journal[-1]["type"] == "cuff_end_outside_attempt"
    v.label("valid", 90, sbp=120, dbp=80)
    cuff(v, "M0", 300, 1, 2)
    rows = v.cuff_log_rows(0, 0)
    assert [(r["device_session_id"], r["t0_event_ordinal"], r["cuff_end_event_ordinal"])
            for r in rows] == [("1", "2", ""), ("2", "1", "2")]
    si.read_cuff_log(write_cuff_log(tmp_path / "log.csv", rows, v2=True), "rec1")


def test_exceptions_and_slots():
    v = visit("S002")
    v.open("M0", 0)
    v.abort(5, "opened by mistake")            # no inflation: the slot stays free
    v.open("M0", 10)
    v.label("valid", 60, sbp=120, dbp=80)      # inflated, but the board t0 was missed
    v.open("M0", 300)
    v.device_event(1, 0, 310)
    v.abort(320, "participant moved off the chair")
    assert v.exceptions() == [{"key": "E02", "why": "no_t0", "status": "valid"},
                              {"key": "E03", "why": "no_label",
                               "aborted": "participant moved off the chair"}]
    assert v.cuff_log_rows(0, 0) == []
    assert v.inflations() == 2


def test_reminders():
    v = visit("S002")
    v.open("M0", 0)
    v.device_event(1, 0, 10)
    assert v.reminders(100) == []
    assert v.reminders(130) == [("press_cuff_end", "E01")]
    v.device_event(2, 1, 140)
    v.label("valid", 150, sbp=120, dbp=80)
    assert v.reminders(200) == [("rest_s_left", 60)]
    assert ("visit_time_warning", None) in v.reminders(6000)
    assert ("visit_cap_reached", None) in v.reminders(7200)
