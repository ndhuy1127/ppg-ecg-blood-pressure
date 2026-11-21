"""Load schedule of criterion A11 (sync_10min_test_plan.md section 11.7).

Answers come from the written plan: 12 blocks of 120 s, normal first; a
``cuff_end`` mark at every block start and at the end of the last block (13
boundaries); in high blocks ``ping`` every 1 s and an ``operator`` mark every 5 s,
with nothing in the 2 s before or the 0.5 s after a boundary; one CPU burner on
during high blocks only. The runner is driven by a fake clock: no device, no real
time.
"""

import json

import pytest

from scripts import sync_load_schedule as sls


def test_plan_has_13_boundaries_and_alternating_loads():
    actions = sls.plan()
    boundaries = [a for a in actions if a["action"] == "boundary"]
    assert [a["t_s"] for a in boundaries] == [120.0 * k for k in range(13)]
    assert [a["load"] for a in boundaries] == ["normal", "high"] * 6 + ["end"]
    assert [a["t_s"] for a in actions] == sorted(a["t_s"] for a in actions)


def test_commands_only_in_high_blocks_and_never_near_a_boundary():
    actions = sls.plan()
    commands = [a for a in actions if a["action"] in ("ping", "mark")]
    assert all(a["load"] == "high" for a in commands)
    boundaries = [a["t_s"] for a in actions if a["action"] == "boundary"]
    assert all(not (b - 2.0 < a["t_s"] < b + 0.5) for a in commands for b in boundaries)
    per_block = {}
    for a in commands:
        per_block.setdefault((a["block"], a["action"]), []).append(a["t_s"])
    for block in range(1, 12, 2):
        pings, marks = per_block[(block, "ping")], per_block[(block, "mark")]
        assert len(pings) == 118 and len(marks) == 24  # 120.5 .. 237.5, 122.5 .. 237.5
        assert all(abs(b - a - 1.0) < 1e-9 for a, b in zip(pings, pings[1:]))
        assert all(abs(b - a - 5.0) < 1e-9 for a, b in zip(marks, marks[1:]))


def test_cpu_on_and_off_frame_each_high_block():
    actions = sls.plan()
    cpu = [(a["action"], a["t_s"]) for a in actions if a["action"].startswith("cpu")]
    expected = []
    for block in range(1, 12, 2):
        expected += [("cpu_on", 120.0 * block), ("cpu_off", 120.0 * (block + 1))]
    assert cpu == expected
    # At a shared time the CPU load stops before the boundary of the next block.
    at_240 = [a["action"] for a in actions if a["t_s"] == 240.0]
    assert at_240.index("cpu_off") < at_240.index("boundary")


def test_bad_parameters_are_refused():
    with pytest.raises(ValueError):
        sls.plan(blocks=0)
    with pytest.raises(ValueError):
        sls.plan(block_s=2.0)


class FakeClock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now

    def sleep(self, seconds):
        self.now += seconds


class LateClock(FakeClock):
    """Wakes up 2.5 s late once, on the first sleep that ends at or after
    ``late_at`` s from the start, as a busy PC."""

    def __init__(self, late_at):
        super().__init__()
        self.start, self.late_at, self.late = self.now, late_at, True

    def sleep(self, seconds):
        self.now += seconds
        if self.late and self.now - self.start >= self.late_at:
            self.now += 2.5
            self.late = False


class FakeBurner:
    def __init__(self, log):
        self.log = log
        log.append("start")

    def terminate(self):
        self.log.append("terminate")

    def wait(self, timeout=None):
        return 0

    def kill(self):
        self.log.append("kill")


class StuckBurner(FakeBurner):
    def wait(self, timeout=None):
        if "kill" not in self.log:
            raise sls.subprocess.TimeoutExpired("burner", timeout)
        return 0


def _recording(tmp_path):
    recording = tmp_path / "rec"
    recording.mkdir()
    (recording / "command_inbox.jsonl").write_text("", encoding="utf-8")
    return recording


def _lines(log):
    return [json.loads(x) for x in log.read_text(encoding="utf-8").splitlines()]


def test_runner_sends_in_order_logs_every_action_and_stops_the_burner(tmp_path):
    recording = _recording(tmp_path)
    sent, cpu, clock = [], [], FakeClock()
    log = sls.run(recording, tmp_path / "out" / "load.jsonl", blocks=2, block_s=10.0,
                  send=lambda rec, entry: sent.append(entry),
                  start_cpu=lambda: FakeBurner(cpu), clock=clock, sleep=clock.sleep,
                  raw_root=tmp_path / "raw")
    lines = _lines(log)
    assert lines[0]["version"] == sls.VERSION
    assert (lines[0]["blocks"], lines[0]["block_s"]) == (2, 10.0)  # real parameters
    actions = sls.plan(blocks=2, block_s=10.0)
    assert [x["action"] for x in lines[1:]] == [a["action"] for a in actions]
    assert {x["result"] for x in lines[1:]} == {"queued", "started", "stopped"}
    assert all(abs(x["t_pc_monotonic_s"] - x["t_s"]) < 1e-9 for x in lines[1:])
    assert sent[0] == sls.BOUNDARY and sent[-1] == sls.BOUNDARY
    assert sum(e == sls.BOUNDARY for e in sent) == 3
    assert cpu == ["start", "terminate"]


def test_runner_logs_a_failed_queue_and_goes_on(tmp_path):
    recording = _recording(tmp_path)
    clock = FakeClock()

    def send(rec, entry):
        if entry["cmd"] == "ping":
            raise OSError("inbox busy")

    log = sls.run(recording, tmp_path / "load.jsonl", blocks=2, block_s=10.0, send=send,
                  start_cpu=lambda: FakeBurner([]), clock=clock, sleep=clock.sleep,
                  raw_root=tmp_path / "raw")
    lines = _lines(log)[1:]
    assert {x["result"] for x in lines if x["action"] == "ping"} == {"error: inbox busy"}
    assert lines[-1]["action"] == "boundary" and lines[-1]["result"] == "queued"


def test_runner_stops_the_burner_when_interrupted_and_logs_it(tmp_path):
    recording = _recording(tmp_path)
    cpu, clock = [], FakeClock()

    def send(rec, entry):
        if entry["cmd"] == "ping":
            raise KeyboardInterrupt

    log = tmp_path / "load.jsonl"
    with pytest.raises(KeyboardInterrupt):
        sls.run(recording, log, blocks=2, block_s=10.0, send=send,
                start_cpu=lambda: FakeBurner(cpu), clock=clock, sleep=clock.sleep,
                raw_root=tmp_path / "raw")
    assert cpu == ["start", "terminate"]
    assert _lines(log)[-1]["action"] == "cpu_off_on_exit"


def test_a_burner_that_does_not_stop_is_killed_and_logged(tmp_path):
    recording = _recording(tmp_path)
    cpu, clock = [], FakeClock()
    log = sls.run(recording, tmp_path / "load.jsonl", blocks=2, block_s=10.0,
                  send=lambda rec, entry: None, start_cpu=lambda: StuckBurner(cpu),
                  clock=clock, sleep=clock.sleep, raw_root=tmp_path / "raw")
    assert [x["result"] for x in _lines(log)[1:] if x["action"] == "cpu_off"] == ["killed"]
    assert cpu == ["start", "terminate", "kill"]


def test_a_command_done_late_inside_the_quiet_window_is_skipped(tmp_path):
    recording = _recording(tmp_path)
    # The ping planned at 17.5 s runs at 20.0 s, inside the window of the end
    # boundary (18 .. 20.5 s), and so does the one planned at 18.0 s.
    clock = LateClock(late_at=17.5)
    sent = []
    log = sls.run(recording, tmp_path / "load.jsonl", blocks=2, block_s=10.0,
                  send=lambda rec, entry: sent.append(entry),
                  start_cpu=lambda: FakeBurner([]), clock=clock, sleep=clock.sleep,
                  raw_root=tmp_path / "raw")
    lines = _lines(log)[1:]
    commands = [x for x in lines if x["action"] in ("ping", "mark")]
    for x in commands:
        near = any(b - 2.0 < x["t_pc_monotonic_s"] < b + 0.5 for b in (0.0, 10.0, 20.0))
        assert (x["result"] == "skipped_late") == near
    assert any(x["result"] == "skipped_late" for x in commands)
    # Boundaries are always sent, late or not.
    assert sum(e == sls.BOUNDARY for e in sent) == 3


def test_runner_refuses_raw_paths_existing_log_and_missing_inbox(tmp_path):
    raw = tmp_path / "data" / "raw"
    raw.mkdir(parents=True)
    with pytest.raises(ValueError, match="data/raw"):
        sls.check_log(raw / "x.jsonl", raw_root=raw)
    existing = tmp_path / "old.jsonl"
    existing.write_text("", encoding="utf-8")
    with pytest.raises(ValueError, match="exists"):
        sls.check_log(existing, raw_root=raw)
    with pytest.raises(FileNotFoundError, match="record --commands"):
        sls.run(tmp_path / "no_rec", tmp_path / "new.jsonl", raw_root=raw)
    # A recording inside data/raw (a session with a person) is refused before any
    # command is queued.
    person = raw / "SUB001" / "S001" / "rec"
    person.mkdir(parents=True)
    (person / "command_inbox.jsonl").write_text("", encoding="utf-8")
    with pytest.raises(ValueError, match="data/raw"):
        sls.run(person, tmp_path / "new.jsonl", raw_root=raw)
    assert (person / "command_inbox.jsonl").read_text(encoding="utf-8") == ""
