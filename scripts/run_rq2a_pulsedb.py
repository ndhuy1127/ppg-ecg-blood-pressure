"""RQ2a: window-level versus subject-level split on PulseDB train + val.

Same model, features and metric as the locked B3 v1; only the training windows
differ (see docs/protocol/rq2a_pulsedb_definition.md). A = random split by window,
B = split by subject (RQ section 5.B). Test rows are verified (hash/leakage) but
never featurized, fitted or scored.

Runs only with the config status APPROVED_NOT_RUN and a config file, definition
and code that are tracked by Git and unchanged (``committed_unchanged``, as B2/B5),
on the split pinned in the config (``split_sha256``).
"""

import argparse
import hashlib
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path

APPROVED = "APPROVED_NOT_RUN"
DEFINITION = "docs/protocol/rq2a_pulsedb_definition.md"
CONFIG = "configs/models/rq2a_pulsedb_v0.json"
CODE_FILES = (
    "scripts/run_rq2a_pulsedb.py", "scripts/run_b3_pulsedb.py",
    "software/pulsedb/rq2a.py", "software/pulsedb/pipeline.py",
    "software/pulsedb/features.py", "software/pulsedb/h5_reader.py",
    "software/models/xgboost_baseline.py", "software/models/constant_baselines.py",
    "software/evaluation/subject_bootstrap.py", "software/evaluation/bp_metrics.py",
    "software/data_io/split_manifest.py", "software/_bp_validation.py",
    "software/_provenance.py", "scripts/run_b2_pulsedb.py",
)


def _git(repo, *args):
    try:
        return subprocess.check_output(["git", *args], cwd=repo, text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def check_approval(config, config_path, repo):
    """Require the approved status, and the config file actually passed, the
    definition and every code file tracked and unchanged against HEAD."""
    from scripts.run_b2_pulsedb import committed_unchanged

    if config["status"] != APPROVED:
        raise ValueError(f"Config status must be {APPROVED} before the run")
    committed = {"config": committed_unchanged(repo, config_path),
                 "definition": committed_unchanged(repo, Path(repo) / DEFINITION),
                 **{name: committed_unchanged(repo, Path(repo) / name)
                    for name in CODE_FILES}}
    bad = sorted(name for name, ok in committed.items() if not ok)
    if bad:
        raise ValueError("Config, definition and code must be committed and unchanged "
                         f"before a run; not: {bad}")
    return committed


def table_text(result) -> str:
    """Markdown summary; no subject IDs."""
    boot = result["bootstrap"]
    pct = round(100 * boot["confidence"])

    def cell(value):
        return f"{value['point']:.2f} [{value['ci'][0]:.2f}; {value['ci'][1]:.2f}]"

    lines = [
        f"RQ2a, pool {result['n_pool_subjects']} subjects, "
        f"{result['n_pool_windows']} windows, {len(result['replicates'])} replicates, "
        f"{result['n_pairs']} (replicate, subject) pairs. A = random by window, "
        "B = by subject.", "",
        f"| Model | Target | MAE A [{pct}% CI] | MAE B [{pct}% CI] | "
        f"Delta B - A [{pct}% CI] | Degradation % [{pct}% CI] | RMSE A / B | "
        "ME ± SD A | ME ± SD B |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for model in ("B0", "B3"):
        for target in ("SBP", "DBP"):
            row = result["summary"][model][target]
            lines.append(
                f"| {model} | {target} | {cell(row['mae']['A_window'])} | "
                f"{cell(row['mae']['B_subject'])} | {cell(row['delta_mae_b_minus_a'])} | "
                f"{cell(row['relative_degradation_pct'])} | "
                f"{row['rmse']['A_window']:.2f} / {row['rmse']['B_subject']:.2f} | "
                f"{row['me']['A_window']:.2f} ± {row['sd']['A_window']:.2f} | "
                f"{row['me']['B_subject']:.2f} ± {row['sd']['B_subject']:.2f} |")
    lines += ["", "MAE: subject-balanced on the shared evaluation windows; CI: "
              f"{boot['method']}, seed {boot['seed']}, {boot['repetitions']} draws. "
              "RMSE, ME, SD: over windows, mean of replicates, no CI. "
              "Error = prediction - reference (mmHg)."]
    return "\n".join(lines) + "\n"


def run(raw_path, split_dir, config_path, output, repo):
    """Validate every input before fitting; write a new output directory only."""
    from scripts.run_b3_pulsedb import load_split
    from software._provenance import text_file_sha256, text_sha256
    from software.data_io.split_manifest import file_sha256
    from software.pulsedb import features
    from software.pulsedb import pipeline as b3_pipeline
    from software.pulsedb import rq2a
    from software.pulsedb.h5_reader import PulseDBH5Reader

    output = Path(output)
    if output.exists():
        raise FileExistsError("Output directory already exists; refusing overwrite")
    config_bytes = Path(config_path).read_bytes()
    config = rq2a.load_config(config_bytes)
    committed = check_approval(config, config_path, repo)
    baseline_path = repo / config["baseline_config"]
    baseline_bytes = baseline_path.read_bytes()
    if text_sha256(baseline_bytes) != config["baseline_config_sha256"]:
        raise ValueError("Baseline config differs from the hash in the RQ2a config")
    baseline = b3_pipeline.load_config(baseline_bytes)
    if baseline["schema_version"] != b3_pipeline.VERSION_V1:
        raise ValueError("RQ2a reuses the locked B3 v1 recipe")
    payloads, split_report, raw_sha256, inventory, manifest, pool_decision = (
        load_split(raw_path, split_dir))
    found = {"raw": raw_sha256, "inventory": split_report["inventory_sha256"],
             "manifest": split_report["manifest_sha256"],
             "config": split_report["config_sha256"]}
    wrong = sorted(name for name, value in found.items()
                   if value != config["split_sha256"][name])
    if wrong:
        raise ValueError(f"Split differs from the one pinned in the config: {wrong}")

    reader = PulseDBH5Reader(str(raw_path))
    with reader.lazy(inventory.raw_index.tolist()) as segments:
        b3_pipeline.verify_inputs(manifest, inventory, segments)
        manifest, inventory, qc = b3_pipeline.label_qc(manifest, inventory)
        pool = manifest[manifest.split.isin(rq2a.POOL_SPLITS)].sort_values("raw_index")
        # Generator in raw_index order; test rows are never passed in.
        matrix = features.feature_matrix(segments[i] for i in pool.raw_index)
        result = rq2a.run_rq2a(
            matrix, pool[["sbp", "dbp"]].to_numpy(), pool.subject_id.to_numpy(),
            pool.sample_id.to_numpy(), pool.split.to_numpy(), config,
            baseline["b3"])
    if file_sha256(raw_path) != raw_sha256:
        raise ValueError("Raw file changed during reading")

    commit = _git(repo, "rev-parse", "HEAD")
    status = _git(repo, "status", "--porcelain")
    report = {
        "schema_version": rq2a.VERSION,
        "source_type": "PUBLIC_ABP",
        "scope": ("RQ2a leakage check on train + val; test and CalFree not used; "
                  "not a BP performance claim"),
        "config": config,
        "baseline_config": baseline,
        "inputs_sha256": {
            "config": text_sha256(config_bytes),
            "baseline_config": text_sha256(baseline_bytes),
            "definition": text_file_sha256(repo / DEFINITION),
            "raw": raw_sha256,
            "split_inventory": split_report["inventory_sha256"],
            "split_manifest": split_report["manifest_sha256"],
            "split_config": split_report["config_sha256"],
            "split_report": hashlib.sha256(payloads["report.json"]).hexdigest(),
        },
        "split_pool_decision": pool_decision,
        "approval_committed": committed,
        "label_qc": qc,
        "feature_names": list(features.FEATURE_NAMES),
        "result": result,
        "validation_log": [
            "Split inventory/manifest/config SHA256 match the split report",
            "validate_manifest and inventory rebuilt from raw before fitting",
            "Split SHA256 (raw, inventory, manifest, config) match split_sha256",
            "Pool = train and val rows only; make_designs rejects any other split",
            "Test rows not featurized, fitted or scored",
            "Evaluation windows identical for both designs; none in a training set",
            "Both training sets have the same number of windows per replicate",
        ],
        "code_provenance": {
            "git_commit": commit,
            "workspace_has_changes": None if status is None else bool(status),
            "sha256_lf": {name: text_file_sha256(repo / name) for name in CODE_FILES},
        },
        "environment": {
            "python": platform.python_version(),
            **{name: version(name)
               for name in ("numpy", "pandas", "xgboost", "h5py")},
        },
        "run_time_utc": datetime.now(timezone.utc).isoformat(),
    }
    table = table_text(result)
    output.mkdir(parents=True, exist_ok=False)
    with (output / "rq2a_table.md").open("x", encoding="utf-8", newline="\n") as s:
        s.write(table)
    report["outputs_sha256"] = {
        "rq2a_table.md": file_sha256(output / "rq2a_table.md")}
    serialized = json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False)
    # report.json is written last: its presence means every output exists.
    with (output / "report.json").open("x", encoding="utf-8", newline="\n") as s:
        s.write(serialized + "\n")
    return report, table


def main():
    repo = Path(__file__).resolve().parents[1]
    if not __package__:
        sys.path.insert(0, str(repo))
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, required=True, help="PulseDB .mat file")
    parser.add_argument("--split-dir", type=Path, required=True,
                        help="Directory written by scripts/build_pulsedb_split.py")
    parser.add_argument("--config", type=Path, default=repo / CONFIG)
    parser.add_argument("--output", type=Path, help="New directory; default runs/")
    args = parser.parse_args()
    output = args.output or (
        repo / "runs" / "rq2a_pulsedb"
        / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ"))
    try:
        report, table = run(args.raw, args.split_dir, args.config, output, repo)
    except (ValueError, OSError, KeyError) as exc:
        parser.exit(1, f"RQ2a stopped: {exc}\n")
    print(table, end="")
    print("Saved:", output)


if __name__ == "__main__":
    main()
