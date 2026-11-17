"""Run records of the PulseDB baselines: one flat row per run, panel, model and target.

A row carries what the Week 6 plan asks every result to be traced to: the
experiment and run directory, the git commit (and whether the workspace had
uncommitted changes), the SHA-256 of the config, the raw file and the split
inventory/manifest, the model and bootstrap seeds, the evaluation split, and the
subject-balanced metrics with their subject-bootstrap CI. Reports are the
``report.json`` files the runners write last (``scripts/run_b3_pulsedb.py``,
``scripts/run_b2_pulsedb.py``); nothing is recomputed here.

Pure functions, no file I/O: ``scripts/collect_runs.py`` and
``scripts/run_b3_multiseed.py`` read the files and write the tables. A report
that lacks a traced field, or that was scored on anything but val, raises
``ValueError``; callers list it as skipped, never drop it silently.
"""

import math
from statistics import stdev

VERSION = "run-record-v1"
# Model run reports this module reads (schema_version of report.json).
MODEL_SCHEMAS = ("b3-pipeline-v0", "b3-pipeline-v1", "b2-pipeline-v0", "b2-pipeline-v1",
                 "b5-pipeline-v0")
TARGETS = ("SBP", "DBP")
METRICS = ("subject_balanced_mae", "subject_balanced_bias", "sample_sd")
TRACE_FIELDS = (
    "experiment", "run_id", "schema_version", "git_commit", "workspace_has_changes",
    "config_sha256", "raw_sha256", "split_inventory_sha256", "split_manifest_sha256",
    "model_seeds", "bootstrap_seed", "evaluation_split", "run_time_utc",
)
ROW_FIELDS = TRACE_FIELDS + (
    "panel", "model", "target", "n_subjects", "n_rows",
    *(f"{m}{suffix}" for m in METRICS for suffix in ("", "_ci_low", "_ci_high")),
)
# Metrics compared by seed_spread (the point values; CIs follow from them).
SPREAD_METRICS = METRICS


def _require(mapping, key, where):
    if not isinstance(mapping, dict) or key not in mapping:
        raise ValueError(f"report has no {where}{key}")
    return mapping[key]


def _sha(value, name):
    if not isinstance(value, str) or len(value) != 64 or any(
        c not in "0123456789abcdef" for c in value
    ):
        raise ValueError(f"{name} is not a SHA-256 hex digest")
    return value


def model_seeds(config):
    """``{section: seed}`` of every model section of a config (not ``bootstrap``),
    as a string ``b3=42`` / ``xgboost=42;...`` so the row stays flat."""
    seeds = {}
    for key, value in config.items():
        if key != "bootstrap" and isinstance(value, dict) and "seed" in value:
            seed = value["seed"]
            if isinstance(seed, bool) or not isinstance(seed, int):
                raise ValueError(f"config {key}.seed must be an integer")
            seeds[key] = seed
    if not seeds:
        raise ValueError("config has no model seed")
    return ";".join(f"{key}={seeds[key]}" for key in sorted(seeds))


def _number(value, name):
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not (
        math.isfinite(value)
    ):
        raise ValueError(f"{name} is not a finite number")
    return float(value)


def _panels(report):
    """``{panel: (evaluation, counts)}``; B3 reports have one panel, ``main``."""
    if "panels" in report:
        panels = report["panels"]
        if not isinstance(panels, dict) or not panels:
            raise ValueError("report panels must be a non-empty object")
        return {name: (_require(panel, "evaluation", f"panels.{name}."),
                       _require(panel, "counts", f"panels.{name}."))
                for name, panel in panels.items()}
    return {"main": (_require(report, "evaluation", ""),
                     _require(report, "split_counts", ""))}


def run_rows(report, experiment, run_id):
    """Rows of one runner ``report.json`` (a parsed dict)."""
    if not isinstance(report, dict):
        raise ValueError("report must be a JSON object")
    schema = report.get("schema_version")
    if schema not in MODEL_SCHEMAS:
        raise ValueError(f"not a model run report: schema_version {schema!r}")
    config = _require(report, "config", "")
    split = _require(config, "evaluation_split", "config.")
    if split != "val":
        raise ValueError(f"only val runs are registered, not {split!r}")
    provenance = _require(report, "code_provenance", "")
    commit = _require(provenance, "git_commit", "code_provenance.")
    if not isinstance(commit, str) or len(commit) != 40:
        raise ValueError("code_provenance.git_commit is not a full commit hash")
    dirty = _require(provenance, "workspace_has_changes", "code_provenance.")
    if not isinstance(dirty, bool):
        raise ValueError("code_provenance.workspace_has_changes must be true or false")
    inputs = _require(report, "inputs_sha256", "")
    bootstrap = _require(config, "bootstrap", "config.")
    boot_seed = _require(bootstrap, "seed", "config.bootstrap.")
    if isinstance(boot_seed, bool) or not isinstance(boot_seed, int):
        raise ValueError("config.bootstrap.seed must be an integer")
    run_time = _require(report, "run_time_utc", "")
    if not isinstance(run_time, str) or not run_time:
        raise ValueError("run_time_utc must be text")
    trace = {
        "experiment": experiment, "run_id": run_id, "schema_version": schema,
        "git_commit": commit, "workspace_has_changes": dirty,
        "config_sha256": _sha(_require(inputs, "config", "inputs_sha256."),
                              "inputs_sha256.config"),
        "raw_sha256": _sha(_require(inputs, "raw", "inputs_sha256."),
                           "inputs_sha256.raw"),
        "split_inventory_sha256": _sha(
            _require(inputs, "split_inventory", "inputs_sha256."),
            "inputs_sha256.split_inventory"),
        "split_manifest_sha256": _sha(
            _require(inputs, "split_manifest", "inputs_sha256."),
            "inputs_sha256.split_manifest"),
        "model_seeds": model_seeds(config), "bootstrap_seed": boot_seed,
        "evaluation_split": split, "run_time_utc": run_time,
    }
    rows = []
    for panel, (evaluation, counts) in _panels(report).items():
        models = _require(evaluation, "models", f"{panel} evaluation.")
        val = _require(counts, "val", f"{panel} counts.")
        if not isinstance(models, dict) or not models:
            raise ValueError(f"{panel}: evaluation.models must be a non-empty object")
        for model, result in models.items():
            point = _require(result, "point", f"{panel}.{model}.")
            ci = _require(result, "ci", f"{panel}.{model}.")
            for target in TARGETS:
                row = dict(trace, panel=panel, model=model, target=target,
                           n_subjects=_require(val, "subjects", f"{panel} counts.val."),
                           n_rows=_require(val, "segments", f"{panel} counts.val."))
                for metric in METRICS:
                    name = f"{panel}.{model}.{target}.{metric}"
                    row[metric] = _number(
                        _require(_require(point, target, f"{panel}.{model}.point."),
                                 metric, f"{panel}.{model}.point.{target}."), name)
                    interval = _require(_require(ci, target, f"{panel}.{model}.ci."),
                                        metric, f"{panel}.{model}.ci.{target}.")
                    bounds = interval.get("bounds") if isinstance(interval, dict) else None
                    if interval.get("status") == "ok" and (
                        isinstance(bounds, list) and len(bounds) == 2
                    ):
                        row[f"{metric}_ci_low"] = _number(bounds[0], name + " CI")
                        row[f"{metric}_ci_high"] = _number(bounds[1], name + " CI")
                    else:  # Kept with an empty CI, never dropped.
                        row[f"{metric}_ci_low"] = row[f"{metric}_ci_high"] = None
                rows.append(row)
    return rows


def seed_spread(rows):
    """Spread of each point metric across runs, per panel, model and target.

    Returns one dict per (panel, model, target, metric) with the number of runs,
    their model seeds, min, max, max − min and SD (``ddof=1``; ``None`` for one
    run). The runs must share everything traced except the run, the seeds and
    the config hash (which holds the seed), so that only the seed varies.
    """
    if not rows:
        raise ValueError("no rows to compare")
    fixed = ("schema_version", "git_commit", "raw_sha256", "split_inventory_sha256",
             "split_manifest_sha256", "bootstrap_seed", "evaluation_split")
    for field in fixed:
        values = {row[field] for row in rows}
        if len(values) != 1:
            raise ValueError(f"runs differ in {field}; only the seed may vary")
    groups = {}
    for row in rows:
        key = (row["panel"], row["model"], row["target"])
        groups.setdefault(key, []).append(row)
    runs = {row["run_id"] for row in rows}
    out = []
    for (panel, model, target), members in sorted(groups.items()):
        if {row["run_id"] for row in members} != runs or len(members) != len(runs):
            raise ValueError(f"{panel}/{model}/{target} is not in every run once")
        for metric in SPREAD_METRICS:
            values = [row[metric] for row in members]
            out.append({
                "panel": panel, "model": model, "target": target, "metric": metric,
                "n_runs": len(values),
                "model_seeds": [row["model_seeds"] for row in members],
                "min": min(values), "max": max(values),
                "max_minus_min": max(values) - min(values),
                "sd": stdev(values) if len(values) > 1 else None,
            })
    return out


def markdown_table(rows):
    """One line per run, panel and model: MAE and bias (subject-balanced) with CI."""
    def cell(row, metric):
        low, high = row[f"{metric}_ci_low"], row[f"{metric}_ci_high"]
        ci = "CI n/a" if low is None else f"[{low:.2f}; {high:.2f}]"
        return f"{row[metric]:.2f} {ci}"

    lines = ["| Experiment | Run | Commit | Seeds | Panel | Model | n subj. | "
             "SBP MAE | SBP bias | DBP MAE | DBP bias |",
             "| --- | --- | --- | --- | --- | --- | ---: | --- | --- | --- | --- |"]
    by_key = {}
    for row in rows:
        by_key.setdefault((row["experiment"], row["run_id"], row["panel"],
                           row["model"]), {})[row["target"]] = row
    for (experiment, run_id, panel, model), targets in by_key.items():
        sbp, dbp = targets["SBP"], targets["DBP"]
        commit = sbp["git_commit"][:7] + ("*" if sbp["workspace_has_changes"] else "")
        lines.append(
            f"| {experiment} | {run_id} | {commit} | {sbp['model_seeds']} | {panel} | "
            f"{model} | {sbp['n_subjects']} | {cell(sbp, 'subject_balanced_mae')} | "
            f"{cell(sbp, 'subject_balanced_bias')} | {cell(dbp, 'subject_balanced_mae')} | "
            f"{cell(dbp, 'subject_balanced_bias')} |")
    return "\n".join(lines) + "\n"
