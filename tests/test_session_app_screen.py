"""Recording screen of the session app without the window (SYNTHETIC demo device)."""

import json
from pathlib import Path

import pytest

from scripts import session_app
from software.device import session_ingest as si
from software.session_app.visit import Visit, VisitError

ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / "configs/session_app/session_app_v0.json").read_text(
    encoding="utf-8"))


class ClockedDemo(session_app.DemoLink):
    """The demo link with a clock the test sets."""

    def __init__(self, folder):
        super().__init__(folder, minutes=12)
        self.t = 0.0

    def now(self):
        return self.t


def run_to(core, t):
    core.link.t = t
    return core.tick()


@pytest.fixture
def core(tmp_path):
    link = ClockedDemo(tmp_path)
    visit = Visit("SYN_DEMO", "S002", CONFIG)
    visit.start(0.0)
    visit.recording_started(link.recording, 0.0)
    return session_app.SessionCore(link, visit, tmp_path)


def test_a_short_session_writes_journal_and_a_cuff_log_the_ingest_reads(core, tmp_path):
    run_to(core, 1.0)
    assert core.visit.device_session_id == 1
    # E01: motion seen before t0 (its mark comes back as code 4), t0, cuff end, label.
    core.act("open", "M0")
    assert core.mark("motion") is True
    run_to(core, 2.0)
    core.link.board_t0()
    run_to(core, 3.0)
    core.link.mark("cuff_end")
    run_to(core, 60.0)
    assert core.act("label", "valid", sbp=121, dbp=79) == []
    # E02: repeat for the observed motion after the 2-minute rest.
    run_to(core, 100.0)
    with pytest.raises(VisitError, match="rest at least"):
        core.act("open", "M0", repeat_of="E01", repeat_reason="observed_motion")
    run_to(core, 200.0)
    core.act("open", "M0", repeat_of="E01", repeat_reason="observed_motion")
    core.link.board_t0()
    run_to(core, 201.0)
    core.link.mark("cuff_end")
    run_to(core, 250.0)
    core.act("label", "valid", sbp=118, dbp=77)
    status, rows = core.finish()
    assert status == "demo stopped" and rows == 2
    cuffs = si.read_cuff_log(tmp_path / "cuff_log.csv", "demo")
    # Event ordinals of the demo device: 0 motion mark, 1 t0, 2 cuff_end, 3 t0, 4 end.
    assert [(c["event_id"], c["t0_event_ordinal"], c["cuff_end_event_ordinal"],
             c["repeat_of_event_id"]) for c in cuffs] == [
        ("E01", 1, 2, None), ("E02", 3, 4, "E01")]
    journal = [json.loads(line) for line in
               (tmp_path / "session_journal.jsonl").read_text(encoding="utf-8").splitlines()]
    assert len(journal) == len(core.visit.journal)
    assert journal[-1]["type"] == "recording_stopped"
    assert [e["type"] for e in journal if e["type"] == "refused"] == ["refused"]
    assert json.loads((tmp_path / "exceptions.json").read_text(encoding="utf-8")) == []
    assert (tmp_path / "raw_demo.bin").stat().st_size > 0
    # Nothing is overwritten.
    with pytest.raises(FileExistsError):
        session_app.SessionCore(ClockedDemo.__new__(ClockedDemo), core.visit, tmp_path)


def test_the_window_builds(core):
    tk = pytest.importorskip("tkinter")
    try:
        root = tk.Tk()
    except tk.TclError:
        pytest.skip("no display")
    root.withdraw()
    try:
        session_app.build_window(core, root)
        for _ in range(3):
            root.update()
    finally:
        root.destroy()


def test_start_session_checks_the_choices(tmp_path):
    with pytest.raises(ValueError, match="participant mode is not open"):
        session_app.start_session("participant", output=tmp_path / "a")
    with pytest.raises(ValueError, match="needs a serial port"):
        session_app.start_session("bringup", output=tmp_path / "b")
    with pytest.raises(ValueError, match="metadata file not found"):
        session_app.start_session("bringup", port="COM9", metadata=tmp_path / "none.json",
                                  output=tmp_path / "c")
    assert not any((tmp_path / n).exists() for n in "abc")  # nothing made on refusal
    core = session_app.start_session("demo", "S002", demo_minutes=1,
                                     output=tmp_path / "demo")
    assert core.visit.session_id == "S002" and core.link.demo
    assert (tmp_path / "demo" / "session_journal.jsonl").exists()
    core.finish()
    assert isinstance(session_app.serial_ports(), list)


def test_the_start_screen_builds_and_starts_a_demo(tmp_path, monkeypatch):
    tk = pytest.importorskip("tkinter")
    try:
        root = tk.Tk()
    except tk.TclError:
        pytest.skip("no display")
    root.withdraw()
    monkeypatch.setattr(session_app, "SETTINGS", tmp_path / "settings.json")
    chosen = []
    try:
        frame = session_app.build_start_screen(root, chosen.append)
        root.update()
        start = [w for w in frame.winfo_children()
                 if "text" in w.keys() and str(w.cget("text")) == "Bắt đầu"]
        start[0].invoke()
        assert chosen == [{"mode": "demo", "session": "S001", "m0_only": False}]
        assert json.loads((tmp_path / "settings.json").read_text())["mode"] == "demo"
    finally:
        root.destroy()


def test_rule_messages_have_operator_wording():
    v = Visit("SYN_DEMO", "S002", CONFIG)
    v.open("M0", 0.0)
    with pytest.raises(VisitError) as exc:
        v.open("M0", 1.0)
    assert session_app.vietnamese(str(exc.value)) == (
        "Lượt E01 vẫn đang mở: lưu nhãn hoặc hủy lượt đó trước khi bắt đầu lượt mới.")
    assert session_app.vietnamese("rest at least 120 s between inflations (40 s so far)") \
        == "Phải nghỉ ít nhất 120 s giữa hai lần bơm (mới được 40 s)."
    assert session_app.vietnamese("something new") == "something new"
    # Every refusal of the ledger has a Vietnamese wording.
    import re
    source = (ROOT / "software/session_app/visit.py").read_text(encoding="utf-8")
    # Messages in one literal; the split ones (rest, slots, t0 plan) are checked above
    # or by their first words in the table.
    refusals = re.findall(r'_refuse\(now, f?"([^"]+)"\)', source)
    assert refusals
    for text in refusals:
        sample = re.sub(r"\{[^}]+\}", "X", text)
        assert session_app.vietnamese(sample) != sample or "use mark_motion" in sample \
            or "must be one of" in sample, sample


def test_a_busy_port_is_reported_before_anything_starts(tmp_path, monkeypatch):
    import scripts.packet_logger as logger

    def busy(name, baudrate, **kw):
        raise logger.__builtins__["PermissionError"](13, "Access is denied.")

    monkeypatch.setattr(logger, "open_serial", busy)
    meta = tmp_path / "meta.json"
    meta.write_text("{}")
    with pytest.raises(ValueError, match="đang bị một chương trình khác giữ"):
        session_app.start_session("bringup", port="COM4", metadata=meta,
                                  output=tmp_path / "x")
    assert not (tmp_path / "x").exists()


def test_a_trial_can_be_dropped_but_only_under_runs_session_app(tmp_path):
    import uuid

    core = session_app.start_session("demo", demo_minutes=1, output=tmp_path / "t")
    with pytest.raises(ValueError, match="Chỉ bỏ được"):
        core.discard()                        # a folder outside runs/session_app/
    core.finish()
    folder = ROOT / "runs/session_app" / f"test_discard_{uuid.uuid4().hex}"
    core = session_app.start_session("demo", demo_minutes=1, output=folder)
    assert folder.exists()
    assert core.discard() == "demo stopped"
    assert not folder.exists()
