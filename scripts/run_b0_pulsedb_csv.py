"""Evaluate existing B0 on public PulseDB CSV train/val labels only."""

import argparse
import csv
import hashlib
import io
import json
import platform
import subprocess
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np


def evaluate_manifest(payload: bytes) -> dict:
    """Validate metadata for all splits; read BP labels only for train and val.

    This does not verify raw waveforms, hash construction, source permissions,
    original PulseDB holdouts, or split generation. Those need upstream evidence.
    """
    from software.evaluation.bp_metrics import evaluate_bp
    from software.models.constant_baselines import PopulationMeanBaseline

    reader = csv.DictReader(io.StringIO(payload.decode("utf-8-sig"), newline=""))
    required = {
        "sample_id", "subject_id", "source", "split", "sbp", "dbp", "sample_hash"
    }
    fields = reader.fieldnames or []
    if len(fields) != len(set(fields)) or not required.issubset(fields):
        raise ValueError("CSV needs unique headers including all seven manifest columns")
    counts = dict.fromkeys(("train", "val", "test"), 0)
    split_subjects = {split: set() for split in counts}
    subject_split: dict[str, str] = {}
    hash_split: dict[str, str] = {}
    waveform_split: dict[str, str] = {}
    sample_keys: set[tuple[str, str]] = set()
    labels: dict[str, list[list[float]]] = {"train": [], "val": []}
    validation_ids: list[str] = []
    for row in reader:
        if None in row or any(row.get(field) is None for field in fields):
            raise ValueError("CSV contains a row with the wrong number of fields")
        for field in required - {"sbp", "dbp"}:
            value = row[field]
            if not value or value.strip() != value:
                raise ValueError("Manifest metadata must be nonempty without edge spaces")
        split = row["split"]
        if split not in counts:
            raise ValueError("split values must be exactly train, val, or test")
        subject = row["subject_id"]
        if subject in subject_split and subject_split[subject] != split:
            raise ValueError("Subject leakage detected between splits; review with Linh")
        subject_split[subject] = split
        sample_key = (row["source"], row["sample_id"])
        if sample_key in sample_keys:
            raise ValueError("Duplicate source/sample_id key; no rows were dropped")
        sample_keys.add(sample_key)
        sample_hash = row["sample_hash"]
        if sample_hash in hash_split and hash_split[sample_hash] != split:
            raise ValueError("Repeated sample_hash across splits; review hash definition")
        hash_split[sample_hash] = split
        if "waveform_hash" in fields:
            fingerprint = row["waveform_hash"]
            if len(fingerprint) != 64 or any(c not in "0123456789abcdef" for c in fingerprint):
                raise ValueError("waveform_hash must be a lowercase SHA256")
            if fingerprint in waveform_split and waveform_split[fingerprint] != split:
                raise ValueError("Repeated waveform_hash across splits; review with Linh")
            waveform_split[fingerprint] = split
        counts[split] += 1
        split_subjects[split].add(subject)
        if split in labels:
            try:
                pair = [float(row["sbp"]), float(row["dbp"])]
            except (TypeError, ValueError) as exc:
                raise ValueError("train/val BP labels must be numeric") from exc
            labels[split].append(pair)
            if split == "val":
                validation_ids.append(subject)
    if not counts["train"] or not counts["val"]:
        raise ValueError("Both train and val must contain rows")
    model = PopulationMeanBaseline().fit(labels["train"])
    predictions = model.predict(counts["val"])
    metrics = evaluate_bp(labels["val"], predictions, validation_ids)
    return {
        "source_type": "PUBLIC_ABP",
        "scope": "B0 absolute BP on validation; not prototype cuff or cross-session BP",
        "manifest_sha256": hashlib.sha256(payload).hexdigest(),
        "split_counts": counts,
        "subjects_per_split": {
            split: len(ids) for split, ids in split_subjects.items()
        },
        "config": {
            "model": "B0",
            "fit_split": "train",
            "evaluation_split": "val",
            "columns": ["SBP", "DBP"],
            "unit": "mmHg",
            "train_weighting": "equal weight per CSV row",
            "error": "prediction - reference",
            "sd_ddof": 1,
            "model_seed": None,
            "model_seed_reason": "deterministic mean; no random operations",
            "split_seed": None,
        },
        "validation_log": [
            "Required headers and metadata checked; no rows silently dropped",
            "No subject overlap between CSV splits",
            "Unique source/sample_id keys",
            "No sample_hash shared between splits; raw hash content not reverified",
            ("No waveform_hash shared between splits; raw hash content not reverified"
             if "waveform_hash" in fields else
             "waveform_hash absent: waveform-only leakage not checked by this runner"),
            "Train/val labels validated by baseline and metrics modules",
            "Test BP labels were not converted or used in fitting/evaluation",
        ],
        "pending_upstream_checks": [
            "CSV source/version, permissions, raw checksum and hash construction",
            "Split config/seed/commit, original holdouts and true subject mapping",
            "BP label derivation, units and observation weighting review",
        ],
        "B0_constant": dict(zip(("SBP", "DBP"), predictions[0].tolist())),
        "sample_weighted": {
            target: asdict(value) for target, value in metrics.sample_weighted.items()
        },
        "subject_balanced": {
            target: asdict(value) for target, value in metrics.subject_balanced.items()
        },
        "B1": "Not run: this manifest does not establish prior calibration",
    }


def apply_default_config(args: argparse.Namespace, repo: Path) -> dict | None:
    """Use the recorded local manifest only when no CSV was explicitly supplied."""
    if args.csv_path is not None:
        if args.unit is None:
            raise ValueError("An explicit CSV path requires --unit mmHg")
        return None
    config_path = repo / "configs/data/b0_pulsedb_validation.json"
    payload = config_path.read_bytes()
    config = json.loads(payload)
    if not isinstance(config, dict) or config.get("unit") != "mmHg":
        raise ValueError("Default B0 config must declare mmHg units")
    path = config.get("csv_path")
    if not isinstance(path, str) or not path:
        raise ValueError("Default B0 config needs a CSV path")
    checksum = config.get("manifest_sha256")
    if not isinstance(checksum, str) or len(checksum) != 64:
        raise ValueError("Default B0 config needs the recorded manifest SHA256")
    args.csv_path = repo / path
    args.unit = args.unit or config["unit"]
    if args.split_seed is None:
        args.split_seed = config.get("split_seed")
    if args.manifest_ref is None:
        args.manifest_ref = config.get("manifest_ref")
    return {
        "path": "configs/data/b0_pulsedb_validation.json",
        "sha256": hashlib.sha256(payload).hexdigest(),
        "expected_manifest_sha256": checksum,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "csv_path", type=Path, nargs="?",
        help="CSV path; omit to use configs/data/b0_pulsedb_validation.json",
    )
    parser.add_argument(
        "--unit", choices=["mmHg"],
        help="Required for an explicit CSV; otherwise use the recorded config units",
    )
    parser.add_argument("--split-seed", type=int, help="Record Linh's actual split seed")
    parser.add_argument("--manifest-ref", help="Record the supplied CSV source commit/ref")
    parser.add_argument("--output", type=Path, help="New JSON path; existing files refused")
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[1]
    if not __package__:
        sys.path.insert(0, str(repo))
    try:
        run_config = apply_default_config(args, repo)
        payload = args.csv_path.read_bytes()
        if run_config is not None and hashlib.sha256(payload).hexdigest() != (
            run_config["expected_manifest_sha256"]
        ):
            raise ValueError("Default CSV hash differs from the recorded manifest")
        report = evaluate_manifest(payload)
        report["run_config"] = run_config
        report["config"]["split_seed"] = args.split_seed
        report["manifest_source_ref"] = args.manifest_ref
        git_commit = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=repo,
            capture_output=True, text=True, check=True,
        ).stdout.strip()
        git_status = subprocess.run(
            ["git", "status", "--porcelain"], cwd=repo,
            capture_output=True, text=True, check=True,
        ).stdout
        report["code_provenance"] = {
            "git_commit": git_commit,
            "workspace_has_changes": bool(git_status.strip()),
            "sha256": {
                name: hashlib.sha256((repo / name).read_bytes()).hexdigest()
                for name in (
                    "scripts/run_b0_pulsedb_csv.py",
                    "software/models/constant_baselines.py",
                    "software/evaluation/bp_metrics.py",
                    "software/_bp_validation.py",
                )
            },
        }
        report["environment"] = {
            "python": platform.python_version(), "numpy": np.__version__
        }
        now = datetime.now(timezone.utc)
        report["run_time_utc"] = now.isoformat()
        output = args.output or (
            repo / "runs" / "b0_pulsedb" / now.strftime("%Y%m%dT%H%M%S%fZ")
            / "metrics.json"
        )
        serialized = json.dumps(report, indent=2, allow_nan=False)
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("x", encoding="utf-8") as stream:
            stream.write(serialized + "\n")
    except UnicodeError:
        parser.exit(1, "CSV must use UTF-8 encoding.\n")
    except ValueError as exc:
        # These validation messages contain no raw rows or subject identifiers.
        parser.exit(1, f"B0 stopped: {exc}\n")
    except ModuleNotFoundError:
        parser.exit(1, "Use a checkout containing Huy's baseline and metrics modules.\n")
    except FileNotFoundError:
        parser.exit(1, "B0 stopped: CSV/config file not found. Check "
                    "configs/data/b0_pulsedb_validation.json or supply a CSV path.\n")
    except (OSError, csv.Error, subprocess.SubprocessError):
        parser.exit(1, "B0 stopped: check input file, Git, or output permissions. "
                    "Existing output files are not overwritten.\n")
    print("Split sample counts:", report["split_counts"])
    print("B0 train mean (SBP/DBP, mmHg):", report["B0_constant"])
    print("Validation sample-weighted metrics:", report["sample_weighted"])
    print("Validation subject-balanced metrics:", report["subject_balanced"])
    print("Saved:", output)


if __name__ == "__main__":
    main()
