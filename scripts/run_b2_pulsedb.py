"""B2 (demographics + HR) beside B0/B3 on val, from a raw PulseDB file + split v2.

Definition: docs/protocol/b2_pulsedb_definition.md (section 8). Before anything is
read the runner requires the status APPROVED_NOT_TEST_EVALUATED, a config and a
definition that are committed and unchanged (so Git shows the definition before
the numbers), and the split pinned in the config (the B3 v1 split).
"""

import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path

CODE_FILES = (
    "scripts/run_b2_pulsedb.py", "scripts/run_b3_pulsedb.py",
    "software/pulsedb/pipeline_b2.py", "software/pulsedb/pipeline.py",
    "software/pulsedb/features_b2.py", "software/pulsedb/features.py",
    "software/pulsedb/reader.py", "software/pulsedb/h5_reader.py",
    "software/models/xgboost_baseline.py", "software/models/constant_baselines.py",
    "software/evaluation/subject_bootstrap.py", "software/evaluation/bp_metrics.py",
    "software/signal_processing/fiducials.py", "software/data_io/split_manifest.py",
    "software/_bp_validation.py", "software/_provenance.py",
)
DEFINITION = "docs/protocol/b2_pulsedb_definition.md"


def _git(repo, *args):
    try:
        return subprocess.check_output(["git", *args], cwd=repo, text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def committed_unchanged(repo, path) -> bool:
    """Whether ``path`` itself lies in ``repo``, is tracked by Git and equals HEAD
    (no staged or unstaged change).

    Symlinks are refused, in the file and in every directory below ``repo``:
    resolving one would check its target, not the path the approval names.
    """
    root = os.path.abspath(repo)
    full = os.path.abspath(path)
    try:
        name = Path(os.path.relpath(full, root))
    except ValueError:  # another drive
        return False
    if name.parts[:1] == ("..",) or name == Path("."):
        return False
    if any((Path(root) / Path(*name.parts[:k])).is_symlink()
           for k in range(1, len(name.parts) + 1)):
        return False
    spec = f":(literal){name.as_posix()}"
    for args in (("ls-files", "--error-unmatch", "--", spec),
                 ("diff", "--quiet", "HEAD", "--", spec)):
        try:
            done = subprocess.run(["git", *args], cwd=repo, stdout=subprocess.DEVNULL,
                                  stderr=subprocess.DEVNULL)
        except OSError:
            return False
        if done.returncode != 0:
            return False
    return True


def panel_table(name, panel) -> str:
    """Markdown rows of one panel; model names carry the panel (e.g. B3@full)."""
    evaluation, counts = panel["evaluation"], panel["counts"]
    confidence = round(100 * evaluation["confidence"])
    lines = [f"### Panel `{name}` (val: {counts['val']['subjects']} subjects, "
             f"{counts['val']['segments']} rows; train: {counts['train']['segments']} rows)",
             "",
             f"| Model | Target | MAE subject-balanced [{confidence}% CI] | "
             f"Bias subject-balanced [{confidence}% CI] |",
             "| --- | --- | --- | --- |"]

    def cell(block, target, metric):
        point = block["point"][target][metric]
        ci = block["ci"]
        bounds = None if ci is None else ci[target][metric]["bounds"]
        text = "n/a" if point is None else f"{point:.2f}"
        return text + ("" if bounds is None else f" [{bounds[0]:.2f}, {bounds[1]:.2f}]")

    for model, block in evaluation["models"].items():
        for target in ("SBP", "DBP"):
            lines.append(f"| {model}@{name} | {target} | "
                         f"{cell(block, target, 'subject_balanced_mae')} | "
                         f"{cell(block, target, 'subject_balanced_bias')} |")
    lines.append("")
    for contrast in evaluation.get("contrasts", []):
        for target in ("SBP", "DBP"):
            lines.append(f"- {contrast['model']} - {contrast['reference']} @{name}, "
                         f"{target}: {cell(contrast, target, 'subject_balanced_mae')} "
                         "mmHg (negative: lower error than the reference)")
    return "\n".join(lines) + "\n"


def run(raw_path, split_dir, config_path, output, repo):
    """Validate every input before fitting; write a new output directory only."""
    from scripts.run_b3_pulsedb import load_split
    from software._provenance import text_file_sha256, text_sha256
    from software.data_io.split_manifest import file_sha256
    from software.pulsedb.h5_reader import PulseDBH5Reader
    from software.pulsedb.pipeline_b2 import APPROVED, load_config, run_b2

    output = Path(output)
    if output.exists():
        raise FileExistsError("Output directory already exists; refusing overwrite")
    config_bytes = Path(config_path).read_bytes()
    config = load_config(config_bytes)
    if config["status"] != APPROVED:
        raise ValueError(f"B2 definition not approved yet (config status "
                         f"{config['status']}); no B2 number may be computed")
    committed = {"config": committed_unchanged(repo, config_path),
                 "definition": committed_unchanged(repo, Path(repo) / DEFINITION)}
    if not all(committed.values()):
        raise ValueError("The approved config and the B2 definition must be committed "
                         f"and unchanged before a run (Git: {committed})")
    payloads, split_report, raw_sha256, inventory, manifest, pool_decision = (
        load_split(raw_path, split_dir))
    found = {"raw": raw_sha256, "inventory": split_report["inventory_sha256"],
             "manifest": split_report["manifest_sha256"],
             "config": split_report["config_sha256"]}
    wrong = sorted(name for name, value in found.items()
                   if value != config["split_sha256"][name])
    if wrong:
        raise ValueError(f"Split differs from the one pinned in the config (the B3 v1 "
                         f"split): {wrong}")
    reader = PulseDBH5Reader(str(raw_path))
    with reader.lazy(inventory.raw_index.tolist()) as segments:
        result = run_b2(segments, manifest, inventory, config)
    if file_sha256(raw_path) != raw_sha256:
        raise ValueError("Raw file changed during reading")

    status = _git(repo, "status", "--porcelain")
    mask = "\n".join(result["rows_without_hr"]).encode()
    report = {
        "schema_version": config["schema_version"],
        "source_type": "PUBLIC_ABP",
        "scope": ("B0/B2/B3 absolute BP on validation, two panels fixed in advance; "
                  "not test, prototype cuff or cross-session BP"),
        "config": config,
        "inputs_sha256": {
            "config": text_sha256(config_bytes), "raw": raw_sha256,
            "split_inventory": split_report["inventory_sha256"],
            "split_manifest": split_report["manifest_sha256"],
            "split_config": split_report["config_sha256"],
            "split_report": hashlib.sha256(payloads["report.json"]).hexdigest(),
        },
        "split_pool_decision": pool_decision,
        "label_qc": result["label_qc"],
        "approval_committed": committed,
        "hr_mask": {"rows_without_hr": len(result["rows_without_hr"]),
                    "sha256_of_sorted_sample_ids": hashlib.sha256(mask).hexdigest(),
                    "file": "hr_mask.csv"},
        "hr_coverage": result["hr_coverage"],
        "feature_names": result["feature_names"],
        "panels": {name: {"counts": panel["counts"], "b0_constant": panel["b0_constant"],
                          "evaluation": panel["evaluation"]}
                   for name, panel in result["panels"].items()},
        "limitations": [
            "PUBLIC_ABP labels of anaesthetised surgical patients; not cuff or prototype",
            "hr_bpm is an unvalidated ECG peak-rate estimate (R detector not gated)",
            "Demographics are per-subject constants: between-subject information",
            "B3 - B2b compares two feature sets; it is not the waveform gain over "
            "demographics",
            "Hyperparameters are B3 v1's, not tuned; no model selection has been done",
        ],
        "code_provenance": {
            "git_commit": _git(repo, "rev-parse", "HEAD"),
            "workspace_has_changes": None if status is None else bool(status),
            "sha256_lf": {name: text_file_sha256(repo / name) for name in CODE_FILES},
        },
        "environment": {
            "python": platform.python_version(),
            **{name: version(name) for name in ("numpy", "pandas", "xgboost", "h5py",
                                               "scipy")},
        },
        "run_time_utc": datetime.now(timezone.utc).isoformat(),
    }
    table = "".join(panel_table(name, panel) + "\n"
                    for name, panel in result["panels"].items())

    output.mkdir(parents=True, exist_ok=False)
    with (output / "b2_table.md").open("x", encoding="utf-8", newline="\n") as s:
        s.write(table)
    written = ["b2_table.md", "hr_mask.csv"]
    # Every train/val row after label QC with its HR status (section 4).
    with (output / "hr_mask.csv").open("x", encoding="utf-8", newline="") as s:
        result["hr_mask"].to_csv(s, index=False, lineterminator="\n")
    # Row-level predictions contain subject IDs; runs/ stays outside Git.
    for name, panel in result["panels"].items():
        path = f"predictions_val_{name}.csv"
        with (output / path).open("x", encoding="utf-8", newline="") as s:
            panel["predictions"].to_csv(s, index=False, lineterminator="\n",
                                        float_format="%.17g")
        written.append(path)
    report["outputs_sha256"] = {name: file_sha256(output / name) for name in sorted(written)}
    with (output / "report.json").open("x", encoding="utf-8", newline="\n") as s:
        s.write(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + "\n")
    return report, table


def main():
    repo = Path(__file__).resolve().parents[1]
    if not __package__:
        sys.path.insert(0, str(repo))
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, required=True, help="PulseDB .mat file")
    parser.add_argument("--split-dir", type=Path, required=True,
                        help="Directory written by scripts/build_pulsedb_split.py")
    parser.add_argument("--config", type=Path,
                        default=repo / "configs/models/b2_pulsedb_v0.json")
    parser.add_argument("--output", type=Path, help="New directory; default runs/")
    args = parser.parse_args()
    output = args.output or (repo / "runs" / "b2_pulsedb"
                             / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ"))
    try:
        report, table = run(args.raw, args.split_dir, args.config, output, repo)
    except (ValueError, OSError, KeyError) as exc:
        # Validation messages contain no raw rows or subject identifiers.
        parser.exit(1, f"B2 stopped: {exc}\n")
    print("HR coverage (val, all):", report["hr_coverage"]["val"]["all"])
    print(table, end="")
    print("Saved:", output)


if __name__ == "__main__":
    main()
