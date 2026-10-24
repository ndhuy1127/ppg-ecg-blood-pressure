"""Fit B0/B3 on train and evaluate on val from a raw PulseDB file + split v2."""

import argparse
import hashlib
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path

CODE_FILES = (
    "scripts/run_b3_pulsedb.py", "software/pulsedb/pipeline.py",
    "software/pulsedb/features.py", "software/pulsedb/reader.py",
    "software/pulsedb/h5_reader.py",
    "software/models/xgboost_baseline.py", "software/models/constant_baselines.py",
    "software/evaluation/subject_bootstrap.py", "software/evaluation/bp_metrics.py",
    "software/signal_processing/fiducials.py", "software/data_io/split_manifest.py",
    "software/_bp_validation.py", "software/_provenance.py",
)
SPLIT_FILES = ("inventory.csv", "manifest.csv", "config.json", "report.json")


def _git(repo, *args):
    try:
        return subprocess.check_output(["git", *args], cwd=repo, text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def run(raw_path, split_dir, config_path, output, repo):
    """Validate every input before fitting; write a new output directory only."""
    from software._provenance import text_file_sha256, text_sha256
    from software.data_io.split_manifest import (
        VERSION as SPLIT_VERSION, file_sha256, read_manifest_bytes,
    )
    from software.pulsedb.h5_reader import PulseDBH5Reader
    from software.pulsedb.pipeline import (
        VERSION_V1, baseline_table, load_config, run_baselines,
    )
    from software.pulsedb.reader import PulseDBReader

    output = Path(output)
    if output.exists():
        raise FileExistsError("Output directory already exists; refusing overwrite")
    config_bytes = Path(config_path).read_bytes()
    config = load_config(config_bytes)

    split_dir = Path(split_dir)
    payloads = {name: (split_dir / name).read_bytes() for name in SPLIT_FILES}
    split_report = json.loads(payloads["report.json"])
    if not isinstance(split_report, dict):
        raise ValueError("Split report.json must be a JSON object")
    if split_report.get("schema_version") != SPLIT_VERSION:
        raise ValueError(f"Split report schema_version must be {SPLIT_VERSION}")
    raw_sha256 = file_sha256(raw_path)
    # config.json is checked byte-for-byte: it is the copy written with the split.
    for field, actual in (
        ("inventory_sha256", hashlib.sha256(payloads["inventory.csv"]).hexdigest()),
        ("manifest_sha256", hashlib.sha256(payloads["manifest.csv"]).hexdigest()),
        ("config_sha256", hashlib.sha256(payloads["config.json"]).hexdigest()),
        ("raw_sha256", raw_sha256),
    ):
        if split_report.get(field) != actual:
            raise ValueError(f"{field} differs from the split handover report")
    split_config = json.loads(payloads["config.json"])
    pool_decision = split_config.get("pool_decision") if isinstance(
        split_config, dict) else None
    if not isinstance(pool_decision, str) or not pool_decision.strip():
        raise ValueError("Split config.json has no pool_decision")
    inventory = read_manifest_bytes(payloads["inventory.csv"])
    manifest = read_manifest_bytes(payloads["manifest.csv"])
    if set(inventory.source_sha256) != {raw_sha256}:
        raise ValueError("Inventory source_sha256 differs from the raw file")

    v1 = config["schema_version"] == VERSION_V1
    if not v1 and split_report.get("subject_subsample") is not None:
        # v0 reads the whole file; the rebuilt inventory could never match.
        raise ValueError("Split has a subject subsample; use b3-pipeline-v1")
    if v1:
        # Only the inventory rows (e.g. a subject subsample), keyed by raw_index
        # and read block by block, so the pool never has to fit in RAM.
        reader = PulseDBH5Reader(str(raw_path))
        with reader.lazy(inventory.raw_index.tolist()) as segments:
            result = run_baselines(segments, manifest, inventory, config)
    else:
        segments = PulseDBReader(str(raw_path)).read()
        result = run_baselines(segments, manifest, inventory, config)
    # Detect replacement/modification of the raw file while it was being read.
    if file_sha256(raw_path) != raw_sha256:
        raise ValueError("Raw file changed during reading")

    now = datetime.now(timezone.utc)
    commit = _git(repo, "rev-parse", "HEAD")
    status = _git(repo, "status", "--porcelain")
    report = {
        "schema_version": config["schema_version"],
        "source_type": "PUBLIC_ABP",
        "scope": ("B0/B3 absolute BP on validation; not test, prototype cuff "
                  "or cross-session BP"),
        "config": config,
        "inputs_sha256": {
            # Tracked text: hashed with LF line endings, as stored in Git.
            "config": text_sha256(config_bytes),
            "raw": raw_sha256,
            "split_inventory": split_report["inventory_sha256"],
            "split_manifest": split_report["manifest_sha256"],
            "split_config": split_report["config_sha256"],
            "split_report": hashlib.sha256(payloads["report.json"]).hexdigest(),
        },
        "split_schema_version": split_report["schema_version"],
        "split_pool_decision": pool_decision,
        "reader": ("h5py, inventory rows only" if v1 else "mat73, whole file"),
        "split_counts": result["counts"],
        "label_qc": result["label_qc"],
        "train_weighting": result["train_weighting"],
        "feature_names": result["feature_names"],
        "constant_train_features": result["constant_train_features"],
        "B0_constant": result["b0_constant"],
        "evaluation": result["evaluation"],
        "validation_log": [
            "Raw SHA256 matches the split report before and after reading",
            "Split inventory/manifest/config SHA256 match the split report",
            "Inventory source_sha256 equals the raw SHA256; pool_decision present",
            "validate_manifest: conservation and no subject/hash leakage",
            "Inventory rebuilt from raw segments matches the handover byte-for-byte",
            "Features read only ECG/PPG; no ABP, BP label, subject ID or hash",
            "B0/B3 fitted on train rows only; no imputation/scaling/selection",
            "Val scored with the same rows and bootstrap draws for B0 and B3",
            "Test rows not featurized, predicted or scored",
            ("Train/val rows with DBP >= SBP excluded from fit and scoring "
             "(label_qc); rule not applied to unscored test rows, whose labels are "
             "only re-hashed; no SQI filter applied" if v1 else
             "No rows excluded; no SQI filter applied"),
        ],
        "limitations": [
            "PUBLIC_ABP labels from one PulseDB subset; not cuff or prototype data",
            ("Train rows weighted 1/n_s (mean 1): every subject weighs the same"
             if v1 else
             "Train rows weighted equally; subjects with more segments weigh more"),
            "ECG_F/PPG_F amplitude units and normalization are unverified",
            "Hyperparameters are not tuned; no model selection has been done",
            "B1 not run: no chronology/calibration metadata",
        ],
        "code_provenance": {
            "git_commit": commit,
            "workspace_has_changes": None if status is None else bool(status),
            "sha256_lf": {name: text_file_sha256(repo / name) for name in CODE_FILES},
        },
        "environment": {
            "python": platform.python_version(),
            **{name: version(name)
               for name in ("numpy", "pandas", "xgboost", "mat73", "h5py")},
        },
        "run_time_utc": now.isoformat(),
    }
    table = baseline_table(result["evaluation"], result["counts"])

    output.mkdir(parents=True, exist_ok=False)
    with (output / "baseline_table.md").open("x", encoding="utf-8", newline="\n") as s:
        s.write(table)
    # Row-level predictions contain subject IDs; runs/ stays outside Git.
    with (output / "predictions_val.csv").open("x", encoding="utf-8", newline="") as s:
        result["predictions"].to_csv(s, index=False, lineterminator="\n",
                                     float_format="%.17g")
    written = ["baseline_table.md", "predictions_val.csv"]
    written += [path.name for path in result["b3"].save(output).values()]
    # report.json is written last: its presence means every output above exists.
    report["outputs_sha256"] = {
        name: file_sha256(output / name) for name in sorted(written)
    }
    serialized = json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False)
    with (output / "report.json").open("x", encoding="utf-8", newline="\n") as s:
        s.write(serialized + "\n")
    return report, table


def main():
    repo = Path(__file__).resolve().parents[1]
    if not __package__:
        sys.path.insert(0, str(repo))
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, required=True, help="PulseDB .mat file")
    parser.add_argument(
        "--split-dir", type=Path, required=True,
        help="Directory written by scripts/build_pulsedb_split.py",
    )
    parser.add_argument(
        "--config", type=Path, default=repo / "configs/models/b3_pulsedb_v0.json",
    )
    parser.add_argument("--output", type=Path, help="New directory; default runs/")
    args = parser.parse_args()
    output = args.output or (
        repo / "runs" / "b3_pulsedb"
        / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    )
    try:
        report, table = run(args.raw, args.split_dir, args.config, output, repo)
    except (ValueError, OSError, KeyError) as exc:
        # Validation messages contain no raw rows or subject identifiers.
        parser.exit(1, f"B3 stopped: {exc}\n")
    print("Split counts:", report["split_counts"])
    if report["constant_train_features"]:
        print("Constant train features:", report["constant_train_features"])
    print(table, end="")
    print("Saved:", output)


if __name__ == "__main__":
    main()
