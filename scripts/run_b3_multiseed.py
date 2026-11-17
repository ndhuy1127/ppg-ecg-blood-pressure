"""Run B0/B3 with several XGBoost seeds on the same split: a determinism check.

Week 6 plan (corrected 2026-10-29): B0 has no seed, and B3 v1 draws no
subsample (no ``subsample``/``colsample_*`` in its params), so the model seed
should change nothing. This script runs ``scripts/run_b3_pulsedb.py`` once per
seed, with a config that differs from ``--config`` only in ``b3.seed``, and
checks that the predictions are byte-identical and every point metric has
SD = 0. Uncertainty is the subject bootstrap of each run, not the seed spread.
The split (seed 72) and the bootstrap seed are never changed. Only val is
scored, as in the B3 runner.

    python scripts/run_b3_multiseed.py --raw <VitalDB_Train_Subset.mat> \\
        --split-dir data/processed/pulsedb_train400_split_run01

Output (new directory, default ``runs/b3_multiseed/<UTC>/``): ``configs/``
(one config per seed), ``seed_<n>/`` (a normal B3 run each), ``seed_spread.csv``,
``multiseed_table.md`` and ``report.json`` (written last), with
``status`` ``DETERMINISTIC`` or ``DIFFERS``. A ``DIFFERS`` result is a finding to
report, not something to average away.
"""

import argparse
import copy
import csv
import hashlib
import io
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_VERSION = "b3-multiseed-v1"
DEFAULT_SEEDS = (42, 43, 44)
STOCHASTIC_PARAMS = ("subsample", "colsample_bytree", "colsample_bylevel",
                     "colsample_bynode")


def _git(repo, *args):
    try:
        return subprocess.check_output(["git", *args], cwd=repo, text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def seed_configs(config, seeds):
    """``{seed: config bytes}``: ``config`` with only ``b3.seed`` replaced."""
    if not isinstance(config, dict) or not isinstance(config.get("b3"), dict) or (
        "seed" not in config["b3"]
    ):
        raise ValueError("config needs b3.seed")
    if len(seeds) < 3 or len(set(seeds)) != len(seeds):
        raise ValueError("give at least three distinct seeds")
    out = {}
    for seed in seeds:
        if isinstance(seed, bool) or not isinstance(seed, int) or seed < 0:
            raise ValueError("seeds must be non-negative integers")
        derived = copy.deepcopy(config)
        derived["b3"]["seed"] = seed
        out[seed] = (json.dumps(derived, indent=2, ensure_ascii=False) + "\n").encode()
    return out


def determinism(rows, prediction_sha256):
    """``(status, spread)``: DETERMINISTIC when every seed gave byte-identical
    predictions and every point metric has max − min = 0."""
    from software.evaluation.run_registry import seed_spread

    spread = seed_spread(rows)
    same_predictions = len(set(prediction_sha256.values())) == 1
    same_metrics = all(item["max_minus_min"] == 0 for item in spread)
    status = "DETERMINISTIC" if same_predictions and same_metrics else "DIFFERS"
    return status, spread


def spread_csv(spread):
    buffer = io.StringIO()
    fields = ("panel", "model", "target", "metric", "n_runs", "min", "max",
              "max_minus_min", "sd")
    writer = csv.DictWriter(buffer, fieldnames=fields, lineterminator="\n",
                            extrasaction="ignore")
    writer.writeheader()
    for item in spread:
        writer.writerow({k: ("" if item[k] is None else item[k]) for k in fields})
    return buffer.getvalue()


def spread_table(status, seeds, spread):
    lines = [f"Status: **{status}** (seeds {', '.join(map(str, seeds))}; val only)", "",
             "| Model | Target | Metric | min | max | max − min | SD |",
             "| --- | --- | --- | ---: | ---: | ---: | ---: |"]
    for item in spread:
        sd = "n/a" if item["sd"] is None else f"{item['sd']:.3g}"
        lines.append(f"| {item['model']} | {item['target']} | {item['metric']} | "
                     f"{item['min']:.4f} | {item['max']:.4f} | "
                     f"{item['max_minus_min']:.3g} | {sd} |")
    return "\n".join(lines) + "\n"


def run(raw, split_dir, config_path, seeds, output, repo):
    from scripts.run_b3_pulsedb import run as run_b3
    from software.evaluation.run_registry import run_rows

    output = Path(output)
    if output.exists():
        raise FileExistsError("Output directory already exists; refusing overwrite")
    base_bytes = Path(config_path).read_bytes()
    base = json.loads(base_bytes)
    params = base.get("b3", {}).get("params", {})
    stochastic = sorted(set(params) & set(STOCHASTIC_PARAMS))
    configs = seed_configs(base, list(seeds))
    output.mkdir(parents=True)
    (output / "configs").mkdir()
    rows, runs, predictions = [], {}, {}
    for seed, payload in configs.items():
        path = output / "configs" / f"seed_{seed}.json"
        with path.open("xb") as handle:
            handle.write(payload)
        run_dir = output / f"seed_{seed}"
        report, _ = run_b3(raw, split_dir, path, run_dir, repo)
        rows += run_rows(report, "b3_multiseed", f"{output.name}/seed_{seed}")
        report_bytes = (run_dir / "report.json").read_bytes()
        predictions[seed] = report["outputs_sha256"]["predictions_val.csv"]
        runs[seed] = {"dir": run_dir.name,
                      "config_sha256": hashlib.sha256(payload).hexdigest(),
                      "report_sha256": hashlib.sha256(report_bytes).hexdigest(),
                      "predictions_val_sha256": predictions[seed]}
    status, spread = determinism(rows, predictions)
    files = {"seed_spread.csv": spread_csv(spread),
             "multiseed_table.md": spread_table(status, list(configs), spread)}
    for name, text in files.items():
        with (output / name).open("x", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
    summary = {
        "schema_version": SCRIPT_VERSION, "status": status,
        "purpose": ("determinism check of B3 over the model seed; not a variance "
                    "estimate (uncertainty = subject bootstrap CI of each run)"),
        "seeds": list(configs), "base_config_sha256": hashlib.sha256(
            base_bytes.replace(b"\r\n", b"\n")).hexdigest(),
        "stochastic_params_in_config": stochastic,
        "runs": runs, "evaluation_split": "val",
        "code_provenance": {
            "git_commit": _git(repo, "rev-parse", "HEAD"),
            "workspace_has_changes": (lambda s: None if s is None else bool(s))(
                _git(repo, "status", "--porcelain")),
        },
        "outputs_sha256": {name: hashlib.sha256(text.encode()).hexdigest()
                           for name, text in files.items()},
        "run_time_utc": datetime.now(timezone.utc).isoformat(),
    }
    with (output / "report.json").open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(summary, indent=2, ensure_ascii=False) + "\n")
    return summary, files["multiseed_table.md"]


def main(argv=None):
    repo = Path(__file__).resolve().parents[1]
    if str(repo) not in sys.path:
        sys.path.insert(0, str(repo))
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--raw", type=Path, required=True)
    parser.add_argument("--split-dir", type=Path, required=True)
    parser.add_argument("--config", type=Path,
                        default=repo / "configs/models/b3_pulsedb_v1.json")
    parser.add_argument("--seeds", type=int, nargs="+", default=list(DEFAULT_SEEDS))
    parser.add_argument("--output", type=Path,
                        help="New directory; default runs/b3_multiseed/<UTC>")
    args = parser.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        # The table has "−"; a Windows console (cp1252) cannot print it, which
        # failed the first run after every output was written (2026-11-07).
        sys.stdout.reconfigure(errors="replace")
    output = args.output or (repo / "runs" / "b3_multiseed"
                             / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ"))
    try:
        summary, table = run(args.raw, args.split_dir, args.config, args.seeds,
                             output, repo)
    except (ValueError, OSError, KeyError) as exc:
        parser.exit(1, f"Multi-seed run stopped: {exc}\n")
    print(table, end="")
    print("Saved:", output)


if __name__ == "__main__":
    main()
