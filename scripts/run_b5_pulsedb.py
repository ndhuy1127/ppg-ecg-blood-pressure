"""B5 (1D ResNet-18 of the PulseDB paper, ECG + PPG) beside B0/B3 on val.

Definition: docs/protocol/b5_pulsedb_definition.md. Two modes:

- ``--mode inner``: fit on 90 % of the train subjects and write the
  inner-validation curve only. No val or test row is featurized, predicted or
  scored (they are only hashed by the split check, as in B3), so it may run
  while the definition is pending review. Output: runs/b5_pulsedb_inner/<UTC>/.
- ``--mode val`` (default): needs the config status APPROVED_NOT_TEST_EVALUATED
  and a config, definition and code that are committed and unchanged (as B2).
  Output: runs/b5_pulsedb/<UTC>/.

    python scripts/run_b5_pulsedb.py --raw data/raw/pulsedb/VitalDB_Train_Subset.mat \\
        --split-dir data/processed/pulsedb_train400_split_run01 --mode inner

Requires PyTorch (requirements-dl.txt); uses CUDA when available unless --device cpu.
"""

import argparse
import csv
import hashlib
import io
import json
import os
import platform
import sys
import time
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path

# Deterministic cuBLAS needs this before CUDA is first used (set before torch).
os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")

CODE_FILES = (
    "scripts/run_b5_pulsedb.py", "scripts/run_b3_pulsedb.py",
    "scripts/run_b2_pulsedb.py",
    "software/pulsedb/pipeline_b5.py", "software/pulsedb/pipeline.py",
    "software/pulsedb/features.py", "software/pulsedb/reader.py",
    "software/pulsedb/h5_reader.py", "software/models/resnet1d.py",
    "software/models/xgboost_baseline.py", "software/models/constant_baselines.py",
    "software/evaluation/subject_bootstrap.py", "software/evaluation/bp_metrics.py",
    "software/data_io/split_manifest.py", "software/_bp_validation.py",
    "software/_provenance.py",
)
DEFINITION = "docs/protocol/b5_pulsedb_definition.md"
INNER_SCHEMA = "b5-inner-v0"
HISTORY_COLUMNS = ("epoch", "train_weighted_mse_scaled", "inner_subject_balanced_mae",
                   "seconds")
LIMITATIONS = [
    "PUBLIC_ABP labels of anaesthetised surgical patients; not cuff or prototype",
    "Absolute BP of unseen subjects (calibration-free); not cross-session ΔBP",
    "Layer details beyond the paper's text follow torchvision ResNet-18 made 1D",
    "B5 fits on 90 % of the train subjects (10 % choose the epoch); B0/B3 on all",
    "Batch size, scaling and early stopping are not given in the paper; chosen "
    "in the definition before any val number",
    "GPU and CPU kernels may give slightly different weights; the device is recorded",
]


def _git(repo, *args):
    import subprocess

    try:
        return subprocess.check_output(["git", *args], cwd=repo, text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def _device(choice):
    import torch

    if choice == "auto":
        return "cuda" if torch.cuda.is_available() else "cpu"
    if choice == "cuda" and not torch.cuda.is_available():
        raise ValueError("CUDA requested but not available")
    return choice


def _history_csv(history):
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(HISTORY_COLUMNS)
    for row in history:
        writer.writerow([repr(row[name]) if isinstance(row[name], float) else row[name]
                         for name in HISTORY_COLUMNS])
    return buffer.getvalue().encode("utf-8")


def b5_table(evaluation, counts) -> str:
    """Markdown table of B0/B3/B5 on val and the paired contrasts; no subject IDs."""
    confidence = round(100 * evaluation["confidence"])
    lines = [f"Val: {counts['val']['subjects']} subjects, {counts['val']['segments']} rows; "
             f"train: {counts['train']['segments']} rows.", "",
             f"| Model | Target | MAE subject-balanced [{confidence}% CI] | "
             f"Bias subject-balanced [{confidence}% CI] | SD sample |",
             "| --- | --- | --- | --- | ---: |"]

    def cell(block, target, metric):
        point = block["point"][target][metric]
        ci = block["ci"]
        bounds = None if ci is None else ci[target][metric]["bounds"]
        text = "n/a" if point is None else f"{point:.2f}"
        return text + ("" if bounds is None else f" [{bounds[0]:.2f}, {bounds[1]:.2f}]")

    for model, block in evaluation["models"].items():
        for target in ("SBP", "DBP"):
            sd = block["point"][target]["sample_sd"]
            lines.append(f"| {model} | {target} | "
                         f"{cell(block, target, 'subject_balanced_mae')} | "
                         f"{cell(block, target, 'subject_balanced_bias')} | "
                         f"{'n/a' if sd is None else f'{sd:.2f}'} |")
    lines.append("")
    for contrast in evaluation.get("contrasts", []):
        for target in ("SBP", "DBP"):
            lines.append(f"- {contrast['model']} - {contrast['reference']}, {target}: "
                         f"{cell(contrast, target, 'subject_balanced_mae')} mmHg "
                         "(subject-balanced MAE difference on the same draws; negative: "
                         "lower error than the reference)")
    lines.append("")
    lines.append(f"Error = prediction - reference (mmHg). Bootstrap: {evaluation['method']}, "
                 f"seed {evaluation['seed']}, {evaluation['repetitions']} repetitions, "
                 f"status {evaluation['status']}.")
    return "\n".join(lines) + "\n"


def run(raw_path, split_dir, config_path, output, repo, mode="val", device="auto",
        log=None):
    """Validate every input before reading a segment; write a new directory only."""
    import torch

    from scripts.run_b2_pulsedb import committed_unchanged
    from scripts.run_b3_pulsedb import load_split
    from software._provenance import text_file_sha256, text_sha256
    from software.data_io.split_manifest import file_sha256
    from software.pulsedb.h5_reader import PulseDBH5Reader
    from software.pulsedb.pipeline_b5 import APPROVED, load_config, run_b5

    output = Path(output)
    if output.exists():
        raise FileExistsError("Output directory already exists; refusing overwrite")
    config_bytes = Path(config_path).read_bytes()
    config = load_config(config_bytes)
    committed = None
    if mode == "val":
        if config["status"] != APPROVED:
            raise ValueError(f"B5 definition not approved yet (config status "
                             f"{config['status']}); no B5 number may be computed on "
                             "val. --mode inner fits on train only")
        committed = {"config": committed_unchanged(repo, config_path),
                     "definition": committed_unchanged(repo, Path(repo) / DEFINITION),
                     "code": all(committed_unchanged(repo, Path(repo) / name)
                                 for name in CODE_FILES)}
        if not all(committed.values()):
            raise ValueError("The approved config, the B5 definition and the code must "
                             f"be committed and unchanged before a run (Git: {committed})")
    elif mode != "inner":
        raise ValueError("mode must be inner or val")
    device = _device(device)
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
    started = time.perf_counter()
    reader = PulseDBH5Reader(str(raw_path))
    with reader.lazy(inventory.raw_index.tolist()) as segments:
        result = run_b5(segments, manifest, inventory, config, device, mode, log)
    if file_sha256(raw_path) != raw_sha256:
        raise ValueError("Raw file changed during reading")

    status = _git(repo, "status", "--porcelain")
    files = {}
    for target, model in result["models"].items():
        buffer = io.BytesIO()
        torch.save(model.state_dict(), buffer)
        files[f"model_{target.lower()}.pt"] = buffer.getvalue()
        files[f"history_{target.lower()}.csv"] = _history_csv(
            result["report"]["targets"][target]["history"])
    b5 = result["report"]
    for target in b5["targets"].values():
        target.pop("history")  # in history_<target>.csv
    report = {
        "schema_version": config["schema_version"] if mode == "val" else INNER_SCHEMA,
        "mode": mode, "source_type": "PUBLIC_ABP",
        "scope": ("B0/B3/B5 absolute BP on validation" if mode == "val" else
                  "B5 training check on train subjects only; no val or test number"),
        "config": config,
        "inputs_sha256": {
            "config": text_sha256(config_bytes), "raw": raw_sha256,
            "split_inventory": split_report["inventory_sha256"],
            "split_manifest": split_report["manifest_sha256"],
            "split_config": split_report["config_sha256"],
            "split_report": hashlib.sha256(payloads["report.json"]).hexdigest(),
        },
        "split_pool_decision": pool_decision,
        "approval_committed": committed,
        "b5": b5,
        "footprint": {
            "parameters_per_model": b5["parameters_per_model"],
            "models": len(result["models"]),
            "state_dict_bytes": {name: len(payload) for name, payload in files.items()
                                 if name.endswith(".pt")},
            "train_seconds": {t: v["train_seconds"] for t, v in b5["targets"].items()},
            "run_seconds": time.perf_counter() - started,
        },
        "limitations": LIMITATIONS,
        "code_provenance": {
            "git_commit": _git(repo, "rev-parse", "HEAD"),
            "workspace_has_changes": None if status is None else bool(status),
            "sha256_lf": {name: text_file_sha256(repo / name) for name in CODE_FILES},
        },
        "environment": {
            "python": platform.python_version(), "device": device,
            "cuda_device": (torch.cuda.get_device_name(0) if device == "cuda" else None),
            "torch_cuda": torch.version.cuda,
            **{name: version(name) for name in ("numpy", "pandas", "xgboost", "h5py",
                                               "torch")},
        },
        "run_time_utc": datetime.now(timezone.utc).isoformat(),
    }
    table = None
    if mode == "val":
        rows = result["counts"]["val"]["segments"]
        report["footprint"]["val_inference_ms_per_segment"] = (
            1000 * b5["val_inference_seconds"] / rows)
        report["evaluation"] = result["evaluation"]
        report["split_counts"] = result["counts"]
        table = b5_table(result["evaluation"], result["counts"])
        files["b5_table.md"] = table.encode("utf-8")
        buffer = io.StringIO()
        # Row-level predictions contain subject IDs; runs/ stays outside Git.
        result["predictions"].to_csv(buffer, index=False, lineterminator="\n",
                                     float_format="%.17g")
        files["predictions_val.csv"] = buffer.getvalue().encode("utf-8")

    output.mkdir(parents=True, exist_ok=False)
    for name, payload in files.items():
        with (output / name).open("xb") as handle:
            handle.write(payload)
    report["outputs_sha256"] = {name: hashlib.sha256(payload).hexdigest()
                                for name, payload in sorted(files.items())}
    with (output / "report.json").open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False)
                     + "\n")
    return report, table


def main():
    repo = Path(__file__).resolve().parents[1]
    if not __package__:
        sys.path.insert(0, str(repo))
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--raw", type=Path, required=True, help="PulseDB .mat file")
    parser.add_argument("--split-dir", type=Path, required=True,
                        help="Directory written by scripts/build_pulsedb_split.py")
    parser.add_argument("--config", type=Path,
                        default=repo / "configs/models/b5_pulsedb_v0.json")
    parser.add_argument("--mode", choices=("inner", "val"), default="val")
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="auto")
    parser.add_argument("--output", type=Path, help="New directory; default runs/")
    args = parser.parse_args()
    folder = "b5_pulsedb" if args.mode == "val" else "b5_pulsedb_inner"
    output = args.output or (repo / "runs" / folder
                             / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ"))
    sys.stdout.reconfigure(errors="replace")

    def log(target, row):
        print(f"{target} epoch {row['epoch']}: train MSE (scaled) "
              f"{row['train_weighted_mse_scaled']:.4f}, inner MAE "
              f"{row['inner_subject_balanced_mae']:.2f} mmHg, {row['seconds']:.1f} s",
              flush=True)

    try:
        report, table = run(args.raw, args.split_dir, args.config, output, repo,
                            args.mode, args.device, log)
    except (ValueError, OSError, KeyError) as exc:
        # Validation messages contain no raw rows or subject identifiers.
        parser.exit(1, f"B5 stopped: {exc}\n")
    for target, info in report["b5"]["targets"].items():
        print(f"{target}: best epoch {info['best_epoch']} of {info['epochs_run']}, "
              f"inner MAE {info['best_inner_subject_balanced_mae']:.2f} mmHg")
    if table:
        print(table, end="")
    print("Saved:", output)


if __name__ == "__main__":
    main()
