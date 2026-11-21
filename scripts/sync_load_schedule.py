"""Load schedule for criterion A11 (sync-load-schedule-v1).

Runs next to ``packet_logger.py record --commands`` during the A11 run of
hardware/test_reports/sync_10min_test_plan.md section 11.7: 12 blocks of 2 min,
alternating normal and high load, normal first. At the start of every block and
at the end of the last one it queues ``mark --event cuff_end`` (event code 2) as
the block boundary on the device clock. In high-load blocks it queues ``ping``
every 1 s and ``mark --event operator`` (code 4) every 5 s, and runs one
background process that keeps one CPU core busy. No command is queued in the 2 s
before or the 0.5 s after a boundary, so a boundary mark is never held up by
another command (the record loop drops a ``MARK_EVENT`` that waits over 1 s); a
command that comes due late, inside that quiet window, is skipped and logged.

Writes ONE new JSONL log outside ``data/raw/`` (refuses to overwrite) and
refuses a recording inside ``data/raw/``: a header line (version, parameters,
git commit) and one line per action with its planned time, the PC monotonic time
and UTC at the moment it was done, and the result (``queued`` only means written
to the inbox; ``commands_sent.jsonl`` of the recording says what the device
answered). Bench use only: never during a session with a person.

    python scripts/sync_load_schedule.py --recording runs/bringup_v1/<record dir> \
        --log runs/sync_fifo/<name>_load.jsonl
"""

import argparse
import json
import platform
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from scripts.device_command import queue_command  # noqa: E402

VERSION = "sync-load-schedule-v1"
BLOCKS, BLOCK_S, PING_S, MARK_S = 12, 120.0, 1.0, 5.0
QUIET_BEFORE_S, QUIET_AFTER_S = 2.0, 0.5  # no command this close to a boundary
PING_PHASE_S, MARK_PHASE_S = 0.5, 2.5  # offsets inside a high-load block
STOP_WAIT_S = 5.0
BOUNDARY = {"cmd": "mark_event", "event": "cuff_end"}
COMMANDS = {"ping": {"cmd": "ping"},
            "mark": {"cmd": "mark_event", "event": "operator"}}
# One core kept busy, the same work on every run.
CPU_BURNER = ("import hashlib\nblock = bytes(4096)\n"
              "while True:\n    block = hashlib.sha256(block).digest() * 128\n")


def load_of(block):
    return "normal" if block % 2 == 0 else "high"


def plan(blocks=BLOCKS, block_s=BLOCK_S, ping_s=PING_S, mark_s=MARK_S):
    """Actions sorted by planned time (s from the start): boundary, cpu_on,
    cpu_off, ping, mark; each with its block and load."""
    if (blocks < 1 or block_s <= QUIET_BEFORE_S + QUIET_AFTER_S or ping_s <= 0
            or mark_s <= 0):
        raise ValueError("bad schedule parameters")
    actions = []
    for block in range(blocks):
        start, end = block * block_s, (block + 1) * block_s
        load = load_of(block)
        actions.append({"t_s": start, "action": "boundary", "block": block, "load": load})
        if load != "high":
            continue
        actions.append({"t_s": start, "action": "cpu_on", "block": block, "load": load})
        for name, period, phase in (("ping", ping_s, PING_PHASE_S),
                                    ("mark", mark_s, MARK_PHASE_S)):
            t = start + max(phase, QUIET_AFTER_S)
            while t <= end - QUIET_BEFORE_S:
                actions.append({"t_s": t, "action": name, "block": block, "load": load})
                t += period
        actions.append({"t_s": end, "action": "cpu_off", "block": block, "load": load})
    actions.append({"t_s": blocks * block_s, "action": "boundary", "block": blocks,
                    "load": "end"})
    order = {"cpu_off": 0, "boundary": 1, "cpu_on": 2, "ping": 3, "mark": 3}
    return sorted(actions, key=lambda a: (a["t_s"], order[a["action"]]))


def _outside_raw(path, raw_root, what):
    path = Path(path).resolve()
    raw_root = Path(raw_root or REPO / "data" / "raw").resolve()
    if path == raw_root or raw_root in path.parents:
        raise ValueError(f"The {what} never goes inside data/raw/ (bench use only)")
    return path


def check_log(path, raw_root=None):
    path = _outside_raw(path, raw_root, "load log")
    if path.exists():
        raise ValueError(f"Log {path} exists; choose a new file")
    return path


def _git(*args):
    try:
        return subprocess.check_output(["git", *args], cwd=REPO, text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def _start_cpu():
    return subprocess.Popen([sys.executable, "-I", "-c", CPU_BURNER],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def _stop_cpu(burner):
    """Terminate, kill if it does not stop; returns how it ended."""
    burner.terminate()
    try:
        burner.wait(timeout=STOP_WAIT_S)
        return "stopped"
    except subprocess.TimeoutExpired:
        burner.kill()
        burner.wait(timeout=STOP_WAIT_S)
        return "killed"


def _late(action, now_s, boundaries):
    """A command done inside the quiet window of a boundary (it came due late)."""
    return any(b - QUIET_BEFORE_S < now_s < b + QUIET_AFTER_S for b in boundaries)


def run(recording, log, blocks=BLOCKS, block_s=BLOCK_S, ping_s=PING_S, mark_s=MARK_S,
        send=queue_command, start_cpu=_start_cpu, clock=time.monotonic, sleep=time.sleep,
        raw_root=None):
    """Carry out ``plan(blocks, block_s, ping_s, mark_s)`` against the inbox of
    ``recording`` (``record --commands`` running). A failed queue is logged and
    the run goes on; the background process is always stopped and logged."""
    _outside_raw(recording, raw_root, "recording")
    path = check_log(log, raw_root)
    actions = plan(blocks, block_s, ping_s, mark_s)
    boundaries = [a["t_s"] for a in actions if a["action"] == "boundary"]
    inbox = Path(recording) / "command_inbox.jsonl"
    if not inbox.is_file():
        raise FileNotFoundError(f"{inbox} not found: is record --commands running?")
    path.parent.mkdir(parents=True, exist_ok=True)
    burner = None
    with open(path, "x", encoding="utf-8") as handle:
        def write(entry):
            handle.write(json.dumps(entry, sort_keys=True) + "\n")
            handle.flush()

        write({"version": VERSION, "recording": str(Path(recording)), "blocks": blocks,
               "block_s": block_s, "ping_s": ping_s, "mark_s": mark_s,
               "quiet_before_s": QUIET_BEFORE_S, "quiet_after_s": QUIET_AFTER_S,
               "git_commit": _git("rev-parse", "HEAD"),
               "python": platform.python_version(),
               "created_utc": datetime.now(timezone.utc).isoformat()})
        t0 = clock()
        try:
            for action in actions:
                delay = t0 + action["t_s"] - clock()
                if delay > 0:
                    sleep(delay)
                done = clock() - t0
                utc = datetime.now(timezone.utc).isoformat()
                name = action["action"]
                try:
                    if name == "boundary":
                        send(recording, dict(BOUNDARY))
                        result = "queued"
                    elif name in COMMANDS:
                        if _late(action, done, boundaries):
                            result = "skipped_late"
                        else:
                            send(recording, dict(COMMANDS[name]))
                            result = "queued"
                    elif name == "cpu_on":
                        burner = start_cpu() if burner is None else burner
                        result = "started"
                    else:  # cpu_off
                        result = _stop_cpu(burner) if burner is not None else "not_running"
                        burner = None
                except (OSError, ValueError, subprocess.SubprocessError) as exc:
                    result = f"error: {exc}"
                write({**action, "t_pc_monotonic_s": round(done, 6), "utc": utc,
                       "result": result})
        finally:
            if burner is not None:
                ended = _stop_cpu(burner)
                write({"action": "cpu_off_on_exit",
                       "t_pc_monotonic_s": round(clock() - t0, 6),
                       "utc": datetime.now(timezone.utc).isoformat(), "result": ended})
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--recording", required=True, type=Path,
                        help="Directory of the running record --commands")
    parser.add_argument("--log", required=True, type=Path, help="New JSONL file")
    args = parser.parse_args()
    print(f"{VERSION}: {BLOCKS} blocks of {BLOCK_S:.0f} s; log {args.log}")
    run(args.recording, args.log)


if __name__ == "__main__":
    main()
