"""RQ2a leakage check: window-level split versus subject-level split.

Pure functions; the caller reads raw/manifest files and writes outputs. Labels
follow docs/research_questions_v0.1.md section 5.B: design A is the random split
by window (leaky control), design B the split by subject. Both designs share the
same evaluation windows. They differ only in the training windows: B trains on
windows of other subjects, A on a random draw of the remaining pool windows, which
includes other windows of the evaluated subjects. Model, features, label
weighting and metric are those of a locked baseline (B3 v1), unchanged. Rows
with ``split = test`` are rejected: the pool is train + val only.
"""

import json
import re

import numpy as np

from software._bp_validation import bp_pairs, subjects
from software.evaluation.bp_metrics import evaluate_bp
from software.evaluation.subject_bootstrap import BootstrapConfig, cluster_draw
from software.models.constant_baselines import PopulationMeanBaseline
from software.models.xgboost_baseline import XGBoostBaseline
from software.pulsedb.pipeline import subject_weights

VERSION = "rq2a-pipeline-v0"
POOL_SPLITS = ("train", "val")
TARGETS = ("SBP", "DBP")
MODELS = ("B0", "B3")
# RQ section 5.B: A = random by window (leaky control), B = by subject.
DESIGNS = ("A_window", "B_subject")
CONFIG_FIELDS = {
    "schema_version", "status", "unit", "pool_splits", "split_sha256",
    "baseline_config", "baseline_config_sha256", "design", "bootstrap",
}
SPLIT_PINS = ("raw", "inventory", "manifest", "config")
DESIGN_FIELDS = {"seeds", "eval_subject_fraction", "eval_window_fraction"}


def load_config(payload: bytes) -> dict:
    """Parse and check the run config; unknown or missing fields are rejected."""
    config = json.loads(payload)
    if not isinstance(config, dict) or set(config) != CONFIG_FIELDS:
        raise ValueError("Config must contain exactly the documented fields")
    if config["schema_version"] != VERSION or config["unit"] != "mmHg":
        raise ValueError("Unsupported schema_version or BP unit")
    if config["pool_splits"] != list(POOL_SPLITS):
        raise ValueError("The pool is train and val only; test is never used")
    pins = config["split_sha256"]
    if (not isinstance(pins, dict) or set(pins) != set(SPLIT_PINS)
            or not all(isinstance(v, str) and re.fullmatch(r"[0-9a-f]{64}", v)
                       for v in pins.values())):
        raise ValueError("split_sha256 needs raw, inventory, manifest and config "
                         "SHA-256 values")
    design = config["design"]
    if not isinstance(design, dict) or set(design) != DESIGN_FIELDS:
        raise ValueError("design needs exactly seeds and the two fractions")
    seeds = design["seeds"]
    if (not isinstance(seeds, list) or not seeds or len(set(seeds)) != len(seeds)
            or any(isinstance(s, bool) or not isinstance(s, int) or s < 0
                   for s in seeds)):
        raise ValueError("seeds must be a nonempty list of distinct integers >= 0")
    for name in ("eval_subject_fraction", "eval_window_fraction"):
        value = design[name]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not (
                0 < value < 1):
            raise ValueError(f"{name} must be in (0, 1)")
    if not isinstance(config["bootstrap"], dict):
        raise ValueError("bootstrap must be an object")
    try:
        BootstrapConfig(**config["bootstrap"])
    except TypeError as exc:
        raise ValueError("Unsupported bootstrap field") from exc
    return config


def make_designs(subject_ids, sample_ids, splits, *, eval_subject_fraction,
                 eval_window_fraction, seed) -> dict:
    """Draw one replicate: shared evaluation windows and two training sets.

    Returns index arrays into the given rows (sorted):

    - ``eval``: ``eval_window_fraction`` of the windows of each evaluated subject
      (at least 1, leaving at least 1 other window of that subject);
    - ``train_B``: every window of the non-evaluated subjects (by subject);
    - ``train_A``: a random draw, of exactly ``len(train_B)`` windows, from all
      pool windows outside ``eval`` (by window).

    Hence the two training sets have the same size, ``eval`` is in neither, B has
    no subject in common with ``eval``, and A contains other windows of them.
    """
    ids = subjects(subject_ids)
    sample = np.asarray(sample_ids)
    split = np.asarray(splits)
    if not (len(ids) == len(sample) == len(split)):
        raise ValueError("subject_ids, sample_ids and splits need the same length")
    if len(set(sample.tolist())) != len(sample):
        raise ValueError("sample_ids must be unique")
    if not np.isin(split, POOL_SPLITS).all():
        raise ValueError("Only train and val rows may enter the RQ2a pool")
    unique, counts = np.unique(ids, return_counts=True)
    if len(unique) < 3 or counts.min() < 2:
        raise ValueError("Need at least 3 subjects with at least 2 windows each")
    rng = np.random.default_rng(seed)
    n_eval = min(max(1, round(eval_subject_fraction * len(unique))), len(unique) - 2)
    eval_subjects = np.sort(rng.choice(unique, n_eval, replace=False))
    eval_parts = []
    for subject in eval_subjects:
        rows = np.flatnonzero(ids == subject)
        take = min(max(1, round(eval_window_fraction * len(rows))), len(rows) - 1)
        eval_parts.append(rng.choice(rows, take, replace=False))
    eval_idx = np.sort(np.concatenate(eval_parts))
    train_b = np.flatnonzero(~np.isin(ids, eval_subjects))
    outside_eval = np.setdiff1d(np.arange(len(ids)), eval_idx)
    train_a = np.sort(rng.choice(outside_eval, len(train_b), replace=False))
    return {"eval": eval_idx, "train_A": train_a, "train_B": train_b,
            "eval_subjects": eval_subjects.tolist()}


def fit_predict(features, labels, subject_ids, train_idx, eval_idx, b3) -> dict:
    """Fit B0 and B3 on ``train_idx`` (locked recipe) and predict ``eval_idx``.

    Train rows are weighted 1/n_s per subject as in B3 v1 (``subject_weights``,
    computed on the training rows themselves). No selection or tuning.
    """
    features = np.asarray(features, dtype=np.float64)
    labels = bp_pairs(labels, "labels")
    ids = subjects(subject_ids, len(labels))
    if len(features) != len(labels):
        raise ValueError("features and labels need the same row count")
    if np.intersect1d(train_idx, eval_idx).size:
        raise ValueError("An evaluation window is in the training set")
    weights = subject_weights(ids[train_idx])
    b0 = PopulationMeanBaseline().fit(labels[train_idx], sample_weight=weights)
    model = XGBoostBaseline(b3["seed"], b3["params"]).fit(
        features[train_idx], labels[train_idx], sample_weight=weights)
    return {"B0": b0.predict(len(eval_idx)), "B3": model.predict(features[eval_idx])}


def window_metrics(reference, prediction, ids):
    """Metrics of one model on E: subject-balanced MAE (main metric), and over
    the windows of E RMSE, ME and SD of the error (error = prediction - reference);
    plus MAE per evaluated subject."""
    evaluation = evaluate_bp(reference, prediction, ids)
    error = np.asarray(prediction, float) - np.asarray(reference, float)
    out = {t: {"mae": evaluation.subject_balanced[t].mae,
               "rmse": float(np.sqrt(np.mean(error[:, i] ** 2))),
               "me": evaluation.sample_weighted[t].bias,
               "sd": evaluation.sample_weighted[t].sd} for i, t in enumerate(TARGETS)}
    by_subject = {s: {t: row[t].mae for t in TARGETS}
                  for s, row in evaluation.by_subject.items()}
    return out, by_subject


def _percentile(values, confidence):
    alpha = (1 - confidence) / 2
    return [float(np.quantile(values, alpha)), float(np.quantile(values, 1 - alpha))]


def summarize_pairs(pair_subject, pair_mae, boot):
    """Point values and paired subject-cluster percentile CIs.

    ``pair_mae[model, design, target]`` holds MAE_s for every (replicate,
    evaluated subject) pair, in the same pair order for every key. Each draw
    resamples pool subjects as whole clusters (all their pairs) and recomputes,
    from the same rows, every mean MAE, the difference B - A and the relative
    degradation 100 (B - A) / A, so A and B stay paired.
    """
    rng = np.random.default_rng(boot.seed)
    keys = list(pair_mae)
    draws = {key: np.empty(boot.repetitions) for key in keys}
    for k in range(boot.repetitions):
        indices, _ = cluster_draw(pair_subject, rng)
        for key in keys:
            draws[key][k] = pair_mae[key][indices].mean()
    out = {}
    for model in MODELS:
        out[model] = {}
        for t in TARGETS:
            a, b = (pair_mae[model, d, t] for d in DESIGNS)
            da, db = (draws[model, d, t] for d in DESIGNS)
            delta = db - da
            out[model][t] = {
                "mae": {d: {"point": float(pair_mae[model, d, t].mean()),
                            "ci": _percentile(draws[model, d, t], boot.confidence)}
                        for d in DESIGNS},
                "delta_mae_b_minus_a": {"point": float(b.mean() - a.mean()),
                                        "ci": _percentile(delta, boot.confidence),
                                        "bootstrap_se": float(delta.std(ddof=1))},
                "relative_degradation_pct": {
                    "point": float(100 * (b.mean() - a.mean()) / a.mean()),
                    "ci": _percentile(100 * delta / da, boot.confidence)}}
    return out


def run_rq2a(features, labels, subject_ids, sample_ids, splits, config, b3) -> dict:
    """Run every replicate and the paired subject bootstrap.

    ``delta = MAE(B, by subject) - MAE(A, by window)`` (RQ section 5.D); positive
    means the window split looks better. Per model and target the statistic is
    the mean over all (replicate, evaluated subject) pairs of MAE_s; every
    replicate evaluates the same number of subjects, so it equals the mean of
    the replicate subject-balanced MAEs. The bootstrap resamples pool subjects as
    whole clusters (all their pairs), so a subject drawn in several replicates
    stays one cluster. RMSE, ME and SD are means over replicates, without CI.
    """
    labels = bp_pairs(labels, "labels")
    ids = subjects(subject_ids, len(labels))
    design = config["design"]
    boot = BootstrapConfig(**config["bootstrap"])
    replicates, pair_subject = [], []
    pair_mae = {(m, d, t): [] for m in MODELS for d in DESIGNS for t in TARGETS}
    for seed in design["seeds"]:
        split = make_designs(
            ids, sample_ids, splits, seed=seed,
            eval_subject_fraction=design["eval_subject_fraction"],
            eval_window_fraction=design["eval_window_fraction"])
        reference, eval_ids = labels[split["eval"]], ids[split["eval"]]
        entry = {"seed": seed, "n_eval_subjects": len(split["eval_subjects"]),
                 "n_eval_windows": len(split["eval"]),
                 "n_train": len(split["train_B"]), "metrics": {}}
        by_subject = {}
        for name in DESIGNS:
            key = "train_" + name[0]
            predicted = fit_predict(features, labels, ids, split[key], split["eval"], b3)
            for model, values in predicted.items():
                metrics, by_subject[model, name] = window_metrics(reference, values,
                                                                  eval_ids)
                entry["metrics"].setdefault(model, {})[name] = metrics
        entry["delta_mae_b_minus_a"] = {
            model: {t: entry["metrics"][model]["B_subject"][t]["mae"]
                    - entry["metrics"][model]["A_window"][t]["mae"] for t in TARGETS}
            for model in MODELS}
        replicates.append(entry)
        for subject in split["eval_subjects"]:
            pair_subject.append(subject)
            for (m, d, t), values in pair_mae.items():
                values.append(by_subject[m, d][subject][t])
    pair_mae = {key: np.array(values) for key, values in pair_mae.items()}
    summary = summarize_pairs(np.array(pair_subject), pair_mae, boot)
    n = len(replicates)
    for model in MODELS:
        for t in TARGETS:
            row = summary[model][t]
            for metric in ("rmse", "me", "sd"):
                row[metric] = {d: float(np.mean([r["metrics"][model][d][t][metric]
                                                 for r in replicates])) for d in DESIGNS}
            # Limitation check: one A and one B model serve every subject of a
            # replicate, so pairs within a replicate are not independent. The SE
            # from the spread of the replicate deltas includes that fit-to-fit
            # variability; compare it with the bootstrap SE (few replicates: rough).
            deltas = [r["delta_mae_b_minus_a"][model][t] for r in replicates]
            row["delta_mae_b_minus_a"]["between_replicate_se"] = (
                float(np.std(deltas, ddof=1) / np.sqrt(n)) if n > 1 else None)
    return {
        "designs": {"A_window": "random split by window (leaky control)",
                    "B_subject": "split by subject"},
        "replicates": replicates, "summary": summary,
        "bootstrap": {"confidence": boot.confidence, "seed": boot.seed,
                      "repetitions": boot.repetitions,
                      "method": "pool-subject cluster percentile; A and B paired"},
        "n_pairs": len(pair_subject),
        "n_pool_subjects": int(len(np.unique(ids))), "n_pool_windows": len(ids),
    }
