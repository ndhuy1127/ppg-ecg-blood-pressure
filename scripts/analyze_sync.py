"""Analyse sync-test runs (sync-analysis-v1, FIFO-anchor mode).

``run``: one logger recording (verified against its manifest) of the common
stimulus test, hardware/test_reports/sync_10min_test_plan.md sections 5, 9, 11:
per-event table (CSV) and a JSON with L per channel, the ECG-PPG offset, A1-A4,
A6, A7, A9-A11 and the run verdict. ``a5``: the A5 range over 10 run JSONs (5 on
each of two dates). Writes NEW files outside ``data/raw/``; refuses to
overwrite. Results on SYNTHETIC recordings only verify code.

    python scripts/analyze_sync.py run --recording runs/bringup_v1/<dir> \
        --output runs/sync_fifo/<name>
    python scripts/analyze_sync.py a5 --runs <10 run JSONs> --output runs/sync_fifo/a5
"""

import argparse
import csv
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from software._provenance import text_file_sha256  # noqa: E402
from software.device import session_ingest as si  # noqa: E402
from software.device import sync_analysis as sa  # noqa: E402

CODE = ("scripts/analyze_sync.py", "software/__init__.py", "software/device/__init__.py",
        "software/device/sync_analysis.py", "software/device/session_ingest.py",
        "software/device/ecg_anchor_residual.py", "software/device/features.py",
        "software/_provenance.py")


def _git(*args):
    try:
        return subprocess.check_output(["git", *args], cwd=REPO, text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def check_output(base, raw_root=None):
    """``base`` names two new files, ``base.json`` and ``base_events.csv``."""
    base = Path(base).resolve()
    raw_root = Path(raw_root or REPO / "data" / "raw").resolve()
    if base == raw_root or raw_root in base.parents:
        raise ValueError("Derived output never goes inside data/raw/")
    paths = (base.with_suffix(".json"), base.parent / f"{base.name}_events.csv")
    for path in paths:
        if path.exists():
            raise ValueError(f"Output {path} exists; choose a new name")
    return paths


def _provenance(extra):
    return {"created_utc": datetime.now(timezone.utc).isoformat(),
            "code_sha256": {c: text_file_sha256(REPO / c) for c in CODE},
            "git_commit": _git("rev-parse", "HEAD"),
            "git_dirty": bool(_git("status", "--porcelain")),
            "python": platform.python_version(), **extra}


def run(recording_dir, output, session_index=0, raw_root=None):
    json_path, csv_path = check_output(output, raw_root)
    recording = si.load_recording(recording_dir)
    manifest = recording["manifest"]
    result = sa.analyze_run(recording, session_index)
    events = result.pop("events")
    result["provenance"] = _provenance({
        "recording": str(Path(recording_dir)), "raw_sha256": manifest["raw"]["sha256"],
        "manifest_sha256": si.sha256_file(Path(recording_dir) / "session_manifest.json"),
        "pc_start_time_utc": manifest.get("pc_start_time_utc"),
        "firmware_version": manifest.get("firmware_version"),
        "source_type": manifest["source_type"], "session_index": session_index})
    json_path.parent.mkdir(parents=True, exist_ok=True)
    columns = list(events[0]) if events else ["event_ordinal"]
    with open(csv_path, "x", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        for row in events:
            writer.writerow({k: "" if v is None else v for k, v in row.items()})
    result["provenance"]["events_csv_sha256"] = si.sha256_file(csv_path)
    with open(json_path, "x", encoding="utf-8") as handle:
        json.dump(sa.round_floats(result), handle, indent=2, sort_keys=True)
        handle.write("\n")
    return result


def run_a5(run_paths, output, raw_root=None):
    json_path, _ = check_output(output, raw_root)
    runs = [json.loads(Path(p).read_text(encoding="utf-8")) for p in run_paths]
    dates = [(r["provenance"].get("pc_start_time_utc") or "")[:10] for r in runs]
    identities = [(r["provenance"].get("raw_sha256"), r.get("session_id")) for r in runs]
    result = sa.a5(runs, dates, identities)
    result["runs"] = [str(p) for p in run_paths]
    result["dates"] = dates
    result["provenance"] = _provenance({"run_sha256": [si.sha256_file(p)
                                                       for p in run_paths]})
    json_path.parent.mkdir(parents=True, exist_ok=True)
    with open(json_path, "x", encoding="utf-8") as handle:
        json.dump(sa.round_floats(result), handle, indent=2, sort_keys=True)
        handle.write("\n")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    one = sub.add_parser("run")
    one.add_argument("--recording", required=True, type=Path)
    one.add_argument("--output", required=True, type=Path,
                     help="Base name: writes <base>.json and <base>_events.csv")
    one.add_argument("--session-index", type=int, default=0)
    agg = sub.add_parser("a5")
    agg.add_argument("--runs", required=True, nargs="+", type=Path)
    agg.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.cmd == "run":
        result = run(args.recording, args.output, args.session_index)
        print(json.dumps(sa.round_floats({"events_used": result["events_used"],
                                          "offset": result["offset"],
                                          "verdict": result["verdict"]}), indent=2))
    else:
        result = run_a5(args.runs, args.output)
        print(json.dumps(sa.round_floats({k: result.get(k) for k in (
            "status", "range_us", "passed", "reason")}), indent=2))


if __name__ == "__main__":
    main()
