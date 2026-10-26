"""B2 (demographics + HR) beside B0/B3 on a split-v2 PulseDB manifest, val only.

Definition: docs/protocol/b2_pulsedb_definition.md (proposed 2026-10-26, pending
Huy's approval; no B2 number may be computed on PulseDB before it is approved).
Two panels fixed in advance (section 4): ``full`` scores B0, B2a and B3 on every
row that passes label QC; ``hr_available`` refits B0, B2a, B2b and B3 on the
train rows with a measurable HR and scores them on the val rows with one. Test
rows are never featurized, fitted or scored; they stay in the reduced manifests
so conservation is still checked.
"""

import json

import numpy as np
import pandas as pd

from software.evaluation.subject_bootstrap import (
    BootstrapConfig, evaluate_prediction_table,
)
from software.models.constant_baselines import PopulationMeanBaseline
from software.models.xgboost_baseline import XGBoostBaseline
from software.pulsedb import features, features_b2
from software.pulsedb.pipeline import (
    V1_FIELDS, label_qc, pulse_pressure_summary, subject_weights, verify_inputs,
)

VERSION = "b2-pipeline-v0"
CONFIG_FIELDS = {
    "schema_version", "status", "unit", "split_sha256", "fit_split",
    "evaluation_split", "b3_feature_set", "b2_feature_set", "label_qc",
    "train_weighting", "xgboost", "bootstrap",
}
# Section 8: the only two statuses; the runner computes numbers only when approved.
PENDING = "PENDING_APPROVAL_NOT_RUN"
APPROVED = "APPROVED_NOT_TEST_EVALUATED"
# Section 1: the split of the B3 v1 run, pinned by the hashes its split report gives.
SPLIT_HASHES = ("raw", "inventory", "manifest", "config")
HEX = frozenset("0123456789abcdef")
PANELS = {
    "full": (("B0", "B2a", "B3"), [("B2a", "B0"), ("B3", "B2a")]),
    "hr_available": (("B0", "B2a", "B2b", "B3"),
                     [("B2b", "B0"), ("B3", "B2b"), ("B2b", "B2a")]),
}
TARGETS = ("SBP", "DBP")


def load_config(payload: bytes) -> dict:
    """Parse and check the B2 run config; unknown or missing fields are rejected."""
    config = json.loads(payload)
    if not isinstance(config, dict) or set(config) != CONFIG_FIELDS:
        raise ValueError("Config must contain exactly the documented fields")
    if config["schema_version"] != VERSION or config["unit"] != "mmHg":
        raise ValueError("Unsupported schema_version or BP unit")
    if config["status"] not in (PENDING, APPROVED):
        raise ValueError(f"status must be {PENDING} or {APPROVED}")
    pins = config["split_sha256"]
    if not isinstance(pins, dict) or set(pins) != set(SPLIT_HASHES) or not all(
        isinstance(value, str) and len(value) == 64 and set(value) <= HEX
        for value in pins.values()
    ):
        raise ValueError("split_sha256 needs raw, inventory, manifest and config "
                         "as lowercase SHA-256 hex")
    if any(config[field] != rule for field, rule in V1_FIELDS.items()):
        raise ValueError("Unsupported label_qc or train_weighting")
    if config["fit_split"] != "train" or config["evaluation_split"] != "val":
        raise ValueError("Models are fitted on train and scored on val only")
    if config["b3_feature_set"] != features.VERSION or (
        config["b2_feature_set"] != features_b2.VERSION
    ):
        raise ValueError("Unsupported feature set")
    xgb = config["xgboost"]
    if not isinstance(xgb, dict) or set(xgb) != {"seed", "params"} or not isinstance(
        xgb["params"], dict
    ):
        raise ValueError("xgboost needs exactly seed and params")
    XGBoostBaseline(xgb["seed"], xgb["params"])  # Validate before any data is read.
    if not isinstance(config["bootstrap"], dict):
        raise ValueError("bootstrap must be an object")
    try:
        BootstrapConfig(**config["bootstrap"])
    except TypeError as exc:
        raise ValueError("Unsupported bootstrap field") from exc
    return config


def featurize(segments, raw_indices):
    """One pass in raw_index order (a lazy reader holds one block at a time).

    Returns ``{raw_index: (b3 features, demographics, hr or None)}``; reads only
    ECG/PPG and the demographic fields of each segment.
    """
    out = {}
    for index in sorted(raw_indices):
        segment = segments[index]
        b3 = features.extract_features(segment.ecg, segment.ppg)
        out[index] = ([b3[name] for name in features.FEATURE_NAMES],
                      features_b2.demographics(segment),
                      features_b2.hr_bpm(segment.ecg))
    return out


def _matrices(rows, table):
    b3 = np.array([table[i][0] for i in rows.raw_index])
    b2a = np.array([table[i][1] for i in rows.raw_index])
    hr = np.array([[table[i][2]] for i in rows.raw_index], dtype=float)
    return {"B3": b3, "B2a": b2a, "B2b": np.hstack([b2a, hr])}


def _coverage(rows, table):
    """Row and subject counts of rows with a measurable HR, by age band and sex."""
    has_hr = np.array([table[i][2] is not None for i in rows.raw_index])
    age = np.array([table[i][1][0] for i in rows.raw_index])
    sex = np.array([table[i][1][1] for i in rows.raw_index])
    groups = {"all": np.ones(len(rows), bool), "age_lt_18": age < 18,
              "age_ge_18": age >= 18, "sex_F": sex == 0, "sex_M": sex == 1}
    ids = rows.subject_id.to_numpy()
    out = {}
    for name, mask in groups.items():
        subjects_all = set(ids[mask])
        subjects_hr = set(ids[mask & has_hr])
        out[name] = {"rows": int(mask.sum()), "rows_with_hr": int((mask & has_hr).sum()),
                     "subjects": len(subjects_all),
                     "subjects_with_hr": len(subjects_hr),
                     "subjects_lost": len(subjects_all - subjects_hr)}
    return out


def _panel(manifest, inventory, table, config, models, contrasts):
    train = manifest[manifest.split == "train"].sort_values("raw_index")
    val = manifest[manifest.split == "val"].sort_values("raw_index")
    weights = subject_weights(train.subject_id.to_numpy())
    labels = train[["sbp", "dbp"]].to_numpy()
    fit_x, val_x = _matrices(train, table), _matrices(val, table)
    seed, params = config["xgboost"]["seed"], config["xgboost"]["params"]
    predictions, fitted = {}, {}
    for name in models:
        if name == "B0":
            model = PopulationMeanBaseline().fit(labels, sample_weight=weights)
            predictions[name] = model.predict(len(val))
        else:
            model = XGBoostBaseline(seed, params).fit(fit_x[name], labels,
                                                      sample_weight=weights)
            predictions[name] = model.predict(val_x[name])
        fitted[name] = model
    frame = pd.concat([
        pd.DataFrame({
            "sample_id": val.sample_id.to_numpy(), "subject_id": val.subject_id.to_numpy(),
            "split": "val", "model": name,
            "pred_sbp": values[:, 0], "pred_dbp": values[:, 1],
        })
        for name, values in predictions.items()
    ], ignore_index=True)
    evaluation = evaluate_prediction_table(
        manifest, inventory, frame, split="val",
        config=BootstrapConfig(**config["bootstrap"]), contrasts=contrasts,
    )
    counts = {split: {"subjects": int(manifest[manifest.split == split].subject_id.nunique()),
                      "segments": int((manifest.split == split).sum())}
              for split in ("train", "val", "test")}
    return {"predictions": frame, "evaluation": evaluation, "counts": counts,
            "models": fitted,
            "b0_constant": dict(zip(TARGETS, fitted["B0"].predict(1)[0].tolist()))}


def run_b2(segments, manifest, inventory, config) -> dict:
    """Both panels of section 4, each fitted on train and scored on val."""
    verify_inputs(manifest, inventory, segments)
    train_pressure = pulse_pressure_summary(manifest[manifest.split == "train"])
    manifest, inventory, qc = label_qc(manifest, inventory)
    qc["train_pulse_pressure_before_qc"] = train_pressure
    labelled = manifest[manifest.split.isin(("train", "val"))]
    table = featurize(segments, labelled.raw_index.tolist())
    features_b2.check_constant_by_subject(
        labelled.subject_id.tolist(), [table[i][1] for i in labelled.raw_index])

    # The HR mask is decided by the ECG alone, before any model sees a label.
    has_hr = [table[i][2] is not None for i in labelled.raw_index]
    mask = pd.DataFrame({"sample_id": labelled.sample_id.to_numpy(),
                         "split": labelled.split.to_numpy(), "has_hr": has_hr})
    no_hr = mask.sample_id[~mask.has_hr]
    keep_manifest = ~manifest.sample_id.isin(no_hr)
    keep_inventory = ~inventory.sample_id.isin(no_hr)
    reduced = (manifest[keep_manifest].reset_index(drop=True),
               inventory[keep_inventory].reset_index(drop=True))
    panels = {
        "full": _panel(manifest, inventory, table, config, *PANELS["full"]),
        "hr_available": _panel(*reduced, table, config, *PANELS["hr_available"]),
    }
    coverage = {split: _coverage(labelled[labelled.split == split].sort_values("raw_index"),
                                 table)
                for split in ("train", "val")}
    return {"panels": panels, "label_qc": qc, "hr_coverage": coverage,
            "rows_without_hr": sorted(no_hr.tolist()), "hr_mask": mask,
            "feature_names": {"B3": list(features.FEATURE_NAMES),
                              "B2a": list(features_b2.DEMOGRAPHIC_NAMES),
                              "B2b": [*features_b2.DEMOGRAPHIC_NAMES, features_b2.HR_NAME]}}
