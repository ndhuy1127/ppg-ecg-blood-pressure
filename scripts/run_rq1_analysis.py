"""RQ1 analysis of SAP v1 from per-cuff feature tables: one command, one run.

Input: one or more ``cuff_features.csv`` (scripts/device_session.py,
docs/data_convention.md 4.6); ``led_readjusted`` and ``pilot`` are required on every
non-SYNTHETIC row. Output, to a NEW directory: ``report.json`` (every number) and
``summary.md`` (main table), plus the provenance inside ``report.json``.

For any non-SYNTHETIC row the run is refused unless the config status is
``LOCKED`` and docs/protocol/sap_v1.md, the config and every file of ``LOCKED`` are
tracked by Git and unchanged against HEAD (SAP section 12), so the outer LOSO loop
of G5 runs once on committed choices.
"""

import argparse
import csv
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from software._provenance import text_file_sha256  # noqa: E402
from software.device.session_ingest import sha256_file  # noqa: E402
from software.evaluation.rq1_analysis import TARGETS, analyze  # noqa: E402

LOCKED = ("docs/protocol/sap_v1.md", "software/evaluation/rq1_analysis.py",
          "software/evaluation/mean_intervals.py", "software/evaluation/rq1_holm_loso.py",
          "software/evaluation/rq1_sensitivity.py", "software/_provenance.py",
          "software/device/session_ingest.py", "software/device/features.py",
          "scripts/run_rq1_analysis.py", "scripts/run_b2_pulsedb.py")
# Config status set by the SAP locking commit (proposed 2026-11-13, pending review).
LOCKED_STATUS = "LOCKED"


def _git(*args):
    import subprocess

    try:
        return subprocess.check_output(["git", *args], cwd=REPO, text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def read_tables(paths):
    rows = []
    for path in paths:
        with open(path, newline="", encoding="utf-8") as handle:
            rows.extend(csv.DictReader(handle))
    if not rows:
        raise ValueError("No cuff rows in the feature tables")
    return rows


def check_committed(config, config_path):
    """Gate for non-SYNTHETIC data (SAP section 12): the config must be LOCKED and
    the config file itself, the SAP and the code must be tracked and equal HEAD
    (``committed_unchanged``: no symlink, no copy outside the repository)."""
    from scripts.run_b2_pulsedb import committed_unchanged

    if config.get("status") != LOCKED_STATUS:
        raise ValueError(f"Real data: the config status must be {LOCKED_STATUS} (SAP "
                         f"section 12), got {config.get('status')!r}")
    files = {"config": committed_unchanged(REPO, config_path),
             **{name: committed_unchanged(REPO, REPO / name) for name in LOCKED}}
    bad = sorted(name for name, ok in files.items() if not ok)
    if bad:
        raise ValueError("Real data: commit the SAP, the config and the analysis code "
                         f"first (SAP section 12); not committed or changed: {bad}")
    return files


def fmt(value):
    return "-" if value is None else f"{value:.2f}"


def summary_md(report):
    lines = [f"# RQ1 ({report['version']})", "",
             f"Subjects: {report['subjects']['eligible']} eligible of "
             f"{report['subjects']['total']}; main-set cuffs "
             f"{report['counts']['main_cuffs']}. Source: {report['source_types']}.", ""]
    for target in TARGETS:
        t = report["main"]["targets"][target]
        lines += [f"## {target}", "", "| Model | MAE (mmHg) | ME | SD |", "| --- | --- | --- | --- |"]
        for name, row in t["models"].items():
            if name == "reference_delta":
                continue
            lines.append(f"| {name} | {fmt(row['mae'])} | {fmt(row['all']['me'])} | "
                         f"{fmt(row['all']['sd'])} |")
        lines.append("")
        for name, c in t["contrasts"].items():
            lines.append(f"- {name} (vs {c['reference']}): mean {c['mean']:.2f}, "
                         f"CI 97.5 % [{c['ci_975'][0]:.2f}; {c['ci_975'][1]:.2f}], "
                         f"CI 95 % [{c['ci_95'][0]:.2f}; {c['ci_95'][1]:.2f}]")
        m = t["main_conclusion"]
        lines += [f"- Main conclusion (Holm, SAP 6): {'declared' if m['declared'] else 'not declared'}"
                  f" at {m['level_used'] * 100:.1f} %; reading: {m['reading']}", ""]
    changed = report["main"]["ci_sensitivity"]["changed"]
    lines += [("Main conclusion changes with the CI method: " + ", ".join(changed)
               + " (SAP 5: not robust)") if changed
              else "Main conclusion is the same with every sensitivity CI (SAP 5).", ""]
    lines += [f"WARNING: {w}" for w in report["warnings"]]
    if report["warnings"]:
        lines.append("")
    if any(s != "SYNTHETIC" for s in report["source_types"]):
        lines.append("Secondary endpoints are not confirmatory (SAP section 11).")
    else:
        lines.append("SYNTHETIC input: these numbers only verify code.")
    return "\n".join(lines) + "\n"


def run(tables, config_path, output):
    output = Path(output)
    if output.exists():
        raise ValueError(f"Output {output} exists; choose a new directory")
    config = json.loads(Path(config_path).read_text(encoding="utf-8"))
    rows = read_tables(tables)
    sources = sorted({r.get("source_type") or "UNKNOWN" for r in rows})
    committed = None
    if sources != ["SYNTHETIC"]:
        committed = check_committed(config, config_path)
    report = analyze(rows, config)
    report["source_types"] = sources
    report["provenance"] = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "tables_sha256": {str(p): sha256_file(p) for p in tables},
        "config_sha256": text_file_sha256(config_path),
        "code_sha256": {p: text_file_sha256(REPO / p) for p in LOCKED},
        "git_commit": _git("rev-parse", "HEAD"),
        "approval_committed": committed,
        "git_dirty": bool(_git("status", "--porcelain")),
        "python": platform.python_version()}
    output.mkdir(parents=True)
    with open(output / "report.json", "x", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
        handle.write("\n")
    with open(output / "summary.md", "x", encoding="utf-8") as handle:
        handle.write(summary_md(report))
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--features", required=True, nargs="+", type=Path)
    parser.add_argument("--config", type=Path,
                        default=REPO / "configs/analysis/rq1_analysis_v1.json")
    parser.add_argument("--output", required=True, type=Path, help="New directory")
    args = parser.parse_args()
    report = run(args.features, args.config, args.output)
    print(json.dumps({t: report["main"]["targets"][t]["main_conclusion"]
                      for t in TARGETS}, indent=2))


if __name__ == "__main__":
    main()
