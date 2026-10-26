"""B0/B3 on a split-v2 PulseDB manifest: fit on train, evaluate on val only.

Pure functions: the caller reads raw/manifest files and writes outputs. Test
rows are checked for conservation/leakage but never featurized, fitted or
scored; test evaluation needs a locked model and is not supported here.
v1 (planned 2026-10-24, docs/protocol/run_b3_pulsedb.md) adds a label QC rule
and subject-balanced train weights; v0 keeps its behaviour.
"""

import json

import numpy as np
import pandas as pd

from software._bp_validation import subjects
from software.data_io.split_manifest import (
    COLUMNS, LABEL_SUMMARY_SPLITS, build_inventory, manifest_bytes, validate_manifest,
)
from software.evaluation.subject_bootstrap import (
    BootstrapConfig, evaluate_prediction_table,
)
from software.models.constant_baselines import PopulationMeanBaseline
from software.models.xgboost_baseline import XGBoostBaseline
from software.pulsedb import features

VERSION = "b3-pipeline-v0"
VERSION_V1 = "b3-pipeline-v1"
CONFIG_FIELDS = {
    "schema_version", "status", "unit", "fit_split", "evaluation_split",
    "feature_set", "b3", "bootstrap",
}
# Extra v1 fields; each names the only rule implemented for it.
V1_FIELDS = {"label_qc": "exclude_dbp_ge_sbp", "train_weighting": "inverse_subject_rows"}
PULSE_PRESSURE_QUANTILES = {
    "min": 0, "p01": 0.01, "p05": 0.05, "p50": 0.5, "p95": 0.95, "p99": 0.99, "max": 1,
}
MODELS = ("B0", "B3")
TARGETS = ("SBP", "DBP")


def load_config(payload: bytes) -> dict:
    """Parse and check the run config; unknown or missing fields are rejected."""
    config = json.loads(payload)
    v1 = isinstance(config, dict) and config.get("schema_version") == VERSION_V1
    expected = CONFIG_FIELDS | (set(V1_FIELDS) if v1 else set())
    if not isinstance(config, dict) or set(config) != expected:
        raise ValueError("Config must contain exactly the documented fields")
    if config["schema_version"] not in (VERSION, VERSION_V1) or config["unit"] != "mmHg":
        raise ValueError("Unsupported schema_version or BP unit")
    if v1 and any(config[field] != rule for field, rule in V1_FIELDS.items()):
        raise ValueError("Unsupported label_qc or train_weighting")
    if config["fit_split"] != "train":
        raise ValueError("Models are fitted on train only")
    if config["evaluation_split"] != "val":
        raise ValueError("v0 evaluates val only; test needs a locked model first")
    if config["feature_set"] != features.VERSION:
        raise ValueError("Unsupported feature_set")
    b3 = config["b3"]
    if not isinstance(b3, dict) or set(b3) != {"seed", "params"} or not isinstance(
        b3["params"], dict
    ):
        raise ValueError("b3 needs exactly seed and params")
    XGBoostBaseline(b3["seed"], b3["params"])  # Validate before any data is read.
    if not isinstance(config["bootstrap"], dict):
        raise ValueError("bootstrap must be an object")
    try:
        BootstrapConfig(**config["bootstrap"])
    except TypeError as exc:
        raise ValueError("Unsupported bootstrap field") from exc
    return config


def verify_inputs(manifest, inventory, segments) -> None:
    """Require a valid split and raw segments that reproduce the inventory hashes."""
    validate_manifest(manifest, inventory)
    if set(inventory.columns) != set(COLUMNS):
        raise ValueError("record_id/window_id columns are not supported in v0")
    if inventory.source.nunique() != 1 or inventory.source_sha256.nunique() != 1:
        raise ValueError("v0 supports exactly one raw source file")
    rebuilt = build_inventory(
        segments, inventory.source.iloc[0], inventory.source_sha256.iloc[0]
    )
    if manifest_bytes(rebuilt) != manifest_bytes(inventory):
        raise ValueError("Raw segments do not reproduce the handed-over inventory")


def _rows(manifest, split):
    return manifest[manifest.split == split].sort_values("raw_index")


def label_qc(manifest, inventory):
    """v1 rule: drop train/val rows with DBP >= SBP (pulse pressure <= 0).

    Returns the reduced manifest and inventory (so validate_manifest still checks
    conservation between them) and the excluded row counts. The rule is not
    applied to test rows (count None): they stay, unscored; a locked test
    evaluation applies it. Test labels are only hashed by ``verify_inputs``.
    """
    labelled = manifest[manifest.split.isin(LABEL_SUMMARY_SPLITS)]
    bad = labelled[labelled.dbp >= labelled.sbp]
    keep_manifest = ~manifest.sample_id.isin(bad.sample_id)
    keep_inventory = ~inventory.sample_id.isin(bad.sample_id)
    excluded = {split: int((bad.split == split).sum()) for split in LABEL_SUMMARY_SPLITS}
    report = {"rule": V1_FIELDS["label_qc"], "excluded_rows": {**excluded, "test": None}}
    return (manifest[keep_manifest].reset_index(drop=True),
            inventory[keep_inventory].reset_index(drop=True), report)


def pulse_pressure_summary(rows) -> dict:
    """SBP - DBP distribution of the given rows (call it on train only)."""
    pressure = (rows.sbp - rows.dbp).to_numpy()
    return {
        "rows": len(pressure), "rows_le_0": int((pressure <= 0).sum()),
        **{name: float(np.quantile(pressure, q))
           for name, q in PULSE_PRESSURE_QUANTILES.items()},
    }


def subject_weights(subject_ids):
    """v1 train weights: 1/n_s per row (n_s = that subject's rows), mean 1.

    Every subject carries the same total weight. Rescaling to mean 1 keeps the
    total hessian of the squared loss equal to the row count, as with unweighted
    rows, so XGBoost's absolute settings (the min_child_weight threshold, the
    reg_lambda penalty) act on the same global scale as in v0; B0's weighted
    mean (the mean of subject means) does not depend on it.
    """
    ids = subjects(subject_ids)
    _, inverse, counts = np.unique(ids, return_inverse=True, return_counts=True)
    weights = 1.0 / counts[inverse]
    return weights * (len(ids) / weights.sum())


def run_baselines(segments, manifest, inventory, config) -> dict:
    """Fit B0/B3 on train rows and score both on the same val rows and draws.

    ``segments`` is indexed by raw_index (a list of every file row, or a
    ``{raw_index: segment}`` mapping of the inventory rows). v1 first applies
    ``label_qc`` and weights train rows with ``subject_weights``.
    """
    verify_inputs(manifest, inventory, segments)
    v1 = config["schema_version"] == VERSION_V1
    qc, weights = None, None
    if v1:
        train_pressure = pulse_pressure_summary(_rows(manifest, "train"))
        manifest, inventory, qc = label_qc(manifest, inventory)
        qc["train_pulse_pressure_before_qc"] = train_pressure
    train, val = _rows(manifest, "train"), _rows(manifest, "val")
    if v1:
        weights = subject_weights(train.subject_id.to_numpy())
    train_labels = train[["sbp", "dbp"]].to_numpy()
    # Generators in raw_index order: a lazy reader holds one block at a time.
    train_features = features.feature_matrix(segments[i] for i in train.raw_index)
    val_features = features.feature_matrix(segments[i] for i in val.raw_index)

    b0 = PopulationMeanBaseline().fit(train_labels, sample_weight=weights)
    b3 = XGBoostBaseline(config["b3"]["seed"], config["b3"]["params"]).fit(
        train_features, train_labels, sample_weight=weights
    )
    predictions = {"B0": b0.predict(len(val)), "B3": b3.predict(val_features)}
    table = pd.concat([
        pd.DataFrame({
            "sample_id": val.sample_id.to_numpy(),
            "subject_id": val.subject_id.to_numpy(),
            "split": "val", "model": name,
            "pred_sbp": values[:, 0], "pred_dbp": values[:, 1],
        })
        for name, values in predictions.items()
    ], ignore_index=True)
    evaluation = evaluate_prediction_table(
        manifest, inventory, table, split="val",
        config=BootstrapConfig(**config["bootstrap"]), contrasts=[("B3", "B0")],
    )
    counts = {
        split: {
            "subjects": int(manifest[manifest.split == split].subject_id.nunique()),
            "segments": int((manifest.split == split).sum()),
        }
        for split in ("train", "val", "test")
    }
    return {
        "predictions": table, "evaluation": evaluation, "counts": counts,
        "label_qc": qc,
        "train_weighting": V1_FIELDS["train_weighting"] if v1 else "equal_rows",
        "b0_constant": dict(zip(TARGETS, b0.predict(1)[0].tolist())),
        "b3": b3, "feature_names": list(features.FEATURE_NAMES),
        # Normalized PulseDB channels may make some statistics constant.
        "constant_train_features": [
            name for i, name in enumerate(features.FEATURE_NAMES)
            if np.ptp(train_features[:, i]) == 0
        ],
    }


def _number(value):
    return "n/a" if value is None else f"{value:.2f}"


def _interval(model, target, metric):
    ci = model["ci"]
    if ci is None or ci[target][metric]["bounds"] is None:
        return "n/a"
    low, high = ci[target][metric]["bounds"]
    return f"[{low:.2f}, {high:.2f}]"


def baseline_table(evaluation, counts) -> str:
    """Markdown B0/B3 table without subject IDs; CI keeps whole-subject clusters."""
    confidence = round(100 * evaluation["confidence"])
    lines = [
        f"| Model | Target | Split | Subjects | Rows | MAE subject-balanced "
        f"[{confidence}% CI] | Bias subject-balanced [{confidence}% CI] | "
        "MAE sample | Bias sample | SD sample (ddof=1) |",
        "| --- | --- | --- | ---: | ---: | --- | --- | ---: | ---: | ---: |",
    ]
    for name in MODELS:
        model = evaluation["models"][name]
        for target in TARGETS:
            point = model["point"][target]
            lines.append(
                f"| {name} | {target} | val | {counts['val']['subjects']} | "
                f"{counts['val']['segments']} | "
                f"{_number(point['subject_balanced_mae'])} "
                f"{_interval(model, target, 'subject_balanced_mae')} | "
                f"{_number(point['subject_balanced_bias'])} "
                f"{_interval(model, target, 'subject_balanced_bias')} | "
                f"{_number(point['sample_weighted_mae'])} | "
                f"{_number(point['sample_weighted_bias'])} | "
                f"{_number(point['sample_sd'])} |"
            )
    lines.append("")
    for contrast in evaluation.get("contrasts", []):
        name = f"{contrast['model']} - {contrast['reference']}"
        for target in TARGETS:
            lines.append(
                f"{name}, {target}, subject-balanced MAE difference (same draws): "
                f"{_number(contrast['point'][target]['subject_balanced_mae'])} "
                f"{_interval(contrast, target, 'subject_balanced_mae')} mmHg; "
                "negative means lower error than the reference."
            )
    lines.append(
        f"Error = prediction - reference (mmHg). Bootstrap: {evaluation['method']}, "
        f"seed {evaluation['seed']}, {evaluation['repetitions']} repetitions, "
        f"status {evaluation['status']}."
    )
    return "\n".join(lines) + "\n"
