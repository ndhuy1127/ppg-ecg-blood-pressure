"""Collect the PulseDB baseline runs in runs/ into one generated table.

Every ``report.json`` under ``runs/<experiment>/`` (at any depth, so the seed
runs of ``b3_multiseed`` are found too) is read with
``software.evaluation.run_registry``. Rows go to ``runs.csv`` and a summary to
``runs.md``; a report that is not a model run, lacks a traced field, or was not
scored on val is listed under ``skipped`` with the reason, never dropped
silently. Directories without ``report.json`` (an interrupted run, or an older
runner such as ``run_b0_pulsedb_csv.py``) are listed too. Nothing is recomputed
and no raw data is read.

    python scripts/collect_runs.py
    python scripts/collect_runs.py --experiments b3_pulsedb b3_multiseed

Output: a new directory ``runs/registry/<UTC>/`` (refuses to overwrite). The
table is generated from the reports; do not edit numbers by hand.
"""

import argparse
import csv
import hashlib
import io
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_VERSION = "collect-runs-v1"
DEFAULT_EXPERIMENTS = ("b3_pulsedb", "b2_pulsedb", "b3_multiseed")
# Summaries written next to model runs (not model runs themselves); listed in
# sources with their status, e.g. the determinism check of run_b3_multiseed.py.
SUMMARY_SCHEMAS = ("b3-multiseed-v1",)


def _git(repo, *args):
    try:
        return subprocess.check_output(["git", *args], cwd=repo, text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def collect(runs_root, experiments):
    """``(rows, sources, skipped)`` for the given experiment folders."""
    from software.evaluation.run_registry import run_rows

    runs_root = Path(runs_root)
    rows, sources, skipped = [], [], []
    for experiment in experiments:
        folder = runs_root / experiment
        if not folder.is_dir():
            skipped.append({"path": experiment, "reason": "experiment folder missing"})
            continue
        reports = sorted(folder.rglob("report.json"))
        report_dirs = {path.parent for path in reports}
        for child in sorted(p for p in folder.iterdir() if p.is_dir()):
            if not any(d == child or child in d.parents for d in report_dirs):
                skipped.append({"path": child.relative_to(runs_root).as_posix(),
                                "reason": "no report.json (interrupted or other runner)"})
        for path in reports:
            run_id = path.parent.relative_to(folder).as_posix()
            payload = path.read_bytes()
            entry = {"path": path.relative_to(runs_root).as_posix(),
                     "sha256": hashlib.sha256(payload).hexdigest()}
            try:
                report = json.loads(payload)
                if isinstance(report, dict) and (
                    report.get("schema_version") in SUMMARY_SCHEMAS
                ):
                    entry["kind"] = "summary"
                    entry["status"] = report.get("status")
                    sources.append(entry)
                    continue
                new = run_rows(report, experiment, run_id)
            except (ValueError, json.JSONDecodeError) as exc:
                skipped.append({"path": entry["path"], "reason": str(exc)})
                continue
            rows += new
            entry["kind"] = "run"
            sources.append(entry)
    return rows, sources, skipped


def rows_csv(rows):
    from software.evaluation.run_registry import ROW_FIELDS

    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=ROW_FIELDS, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({key: ("" if row[key] is None else row[key])
                         for key in ROW_FIELDS})
    return buffer.getvalue()


def write(output, rows, sources, skipped, repo, experiments):
    from software.evaluation.run_registry import VERSION, markdown_table

    output = Path(output)
    if output.exists():
        raise FileExistsError("Output directory already exists; refusing overwrite")
    table = markdown_table(rows) if rows else "No model run found.\n"
    notes = ["", "Commit marked `*`: the workspace had uncommitted changes when the run "
             "started (code SHA-256 are in its report.json). Seeds: model seed per "
             "config section; the bootstrap seed and split are in runs.csv.", ""]
    summaries = [s for s in sources if s["kind"] == "summary"]
    if summaries:
        notes += ["Summaries:", ""] + [f"- `{s['path']}`: status {s['status']}"
                                       for s in summaries] + [""]
    if skipped:
        notes += ["Skipped:", ""] + [f"- `{s['path']}`: {s['reason']}" for s in skipped]
    files = {"runs.csv": rows_csv(rows), "runs.md": table + "\n".join(notes) + "\n"}
    output.mkdir(parents=True, exist_ok=False)
    for name, text in files.items():
        with (output / name).open("x", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
    report = {
        "script_version": SCRIPT_VERSION, "record_version": VERSION,
        "source_type": "RUN_REPORTS", "experiments": list(experiments),
        "n_runs": sum(s["kind"] == "run" for s in sources), "n_rows": len(rows),
        "sources": sources,
        "skipped": skipped,
        "code_provenance": {
            "git_commit": _git(repo, "rev-parse", "HEAD"),
            "workspace_has_changes": (lambda s: None if s is None else bool(s))(
                _git(repo, "status", "--porcelain")),
        },
        "outputs_sha256": {name: hashlib.sha256(text.encode("utf-8")).hexdigest()
                           for name, text in files.items()},
        "run_time_utc": datetime.now(timezone.utc).isoformat(),
    }
    with (output / "report.json").open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    return report


def main(argv=None):
    repo = Path(__file__).resolve().parents[1]
    if str(repo) not in sys.path:
        sys.path.insert(0, str(repo))
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--runs-root", type=Path, default=repo / "runs")
    parser.add_argument("--experiments", nargs="+", default=list(DEFAULT_EXPERIMENTS))
    parser.add_argument("--output", type=Path,
                        help="New directory; default <runs-root>/registry/<UTC>")
    args = parser.parse_args(argv)
    if "registry" in args.experiments:
        parser.error("registry holds collected tables, not runs")
    output = args.output or (args.runs_root / "registry"
                             / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ"))
    rows, sources, skipped = collect(args.runs_root, args.experiments)
    try:
        report = write(output, rows, sources, skipped, repo, args.experiments)
    except (OSError, ValueError) as exc:
        parser.exit(1, f"Not collected: {exc}\n")
    print(f"{report['n_runs']} runs, {report['n_rows']} rows, "
          f"{len(skipped)} skipped -> {output}")


if __name__ == "__main__":
    main()
