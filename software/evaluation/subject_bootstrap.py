"""Cluster percentile bootstrap, preserving every draw's multiplicity."""

from dataclasses import dataclass

import numpy as np
import pandas as pd

from software._bp_validation import bp_pairs, subjects
from software.data_io.split_manifest import validate_manifest
from software.evaluation.bp_metrics import evaluate_bp
from software.signal_processing.fiducials import finite_number


@dataclass(frozen=True)
class BootstrapConfig:
    seed: int = 20261013
    repetitions: int = 2000
    confidence: float = 0.95
    min_subjects: int = 2

    def __post_init__(self):
        for name, minimum in (("seed", 0), ("repetitions", 2), ("min_subjects", 2)):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
                raise ValueError(f"Invalid bootstrap {name}")
        if not 0 < finite_number(self.confidence, "confidence") < 1:
            raise ValueError("confidence must be in (0, 1)")


def cluster_draw(subject_ids, rng):
    """Return row indices AND fresh cluster IDs for each occurrence of a draw."""
    ids = subjects(subject_ids)
    unique = np.unique(ids)
    selected = rng.choice(unique, len(unique), replace=True)
    groups = [np.flatnonzero(ids == subject) for subject in selected]
    indices = np.concatenate(groups)
    draw_ids = np.concatenate([np.repeat(f"DRAW_{i}", len(g)) for i, g in enumerate(groups)])
    return indices, draw_ids


def _statistics(evaluation):
    return {target: {
        "subject_balanced_mae": evaluation.subject_balanced[target].mae,
        "subject_balanced_bias": evaluation.subject_balanced[target].bias,
        "sample_weighted_mae": evaluation.sample_weighted[target].mae,
        "sample_weighted_bias": evaluation.sample_weighted[target].bias,
        "sample_sd": evaluation.sample_weighted[target].sd,
    } for target in ("SBP", "DBP")}


def bootstrap_bp(reference, prediction_sets, subject_ids, config=BootstrapConfig()):
    """Same cluster draws for every model; no model fitting or selection here."""
    reference = bp_pairs(reference, "reference")
    ids = subjects(subject_ids, len(reference))
    if not isinstance(prediction_sets, dict) or not prediction_sets:
        raise ValueError("Provide a nonempty model -> predictions mapping")
    predictions = {name: bp_pairs(values, "predictions") for name, values in prediction_sets.items()}
    if any(not isinstance(name, str) or not name.strip() for name in predictions):
        raise ValueError("Model names must be nonempty text")
    if any(values.shape != reference.shape for values in predictions.values()):
        raise ValueError("reference and predictions must have identical shapes")
    point = {name: _statistics(evaluate_bp(reference, values, ids)) for name, values in predictions.items()}
    n_subjects = len(np.unique(ids))
    result = {"n_rows": len(ids), "n_subjects": n_subjects, "seed": config.seed,
              "repetitions": config.repetitions, "confidence": config.confidence,
              "method": "subject cluster percentile; shared draws across models",
              "models": {}, "status": "ok"}
    if n_subjects < config.min_subjects:
        result["status"] = "insufficient_subjects"
        result["models"] = {name: {"point": stats, "ci": None} for name, stats in point.items()}
        return result
    samples = {name: {target: {metric: [] for metric in stats[target]} for target in stats} for name, stats in point.items()}
    rng = np.random.default_rng(config.seed)
    for _ in range(config.repetitions):
        indices, draw_ids = cluster_draw(ids, rng)
        for name, values in predictions.items():
            stats = _statistics(evaluate_bp(reference[indices], values[indices], draw_ids))
            for target in stats:
                for metric, value in stats[target].items():
                    if value is not None:
                        samples[name][target][metric].append(value)
    alpha = (1 - config.confidence) / 2
    for name in point:
        intervals = {}
        for target in point[name]:
            intervals[target] = {}
            for metric, values in samples[name][target].items():
                bounds = np.quantile(values, [alpha, 1 - alpha]).tolist() if values else None
                intervals[target][metric] = {"bounds": bounds, "valid_repetitions": len(values),
                    "status": "undefined" if not values else ("degenerate" if np.ptp(values) == 0 else "ok")}
        result["models"][name] = {"point": point[name], "ci": intervals}
    return result


def evaluate_prediction_table(manifest, inventory, predictions, *, split="val", config=BootstrapConfig()):
    """Validate v2 conservation/leakage and exact prediction keys before metrics.

    Table columns: sample_id, subject_id, split, model, pred_sbp, pred_dbp.
    Caller still owns raw/pool permissions and observation/calibration checks.
    Test evaluation requires caller's prior model/threshold lock; not enforced here.
    """
    validate_manifest(manifest, inventory)
    if split not in ("val", "test"):
        raise ValueError("Evaluation split must be val/test")
    columns = {"sample_id", "subject_id", "split", "model", "pred_sbp", "pred_dbp"}
    if not isinstance(predictions, pd.DataFrame) or predictions.empty or not predictions.columns.is_unique or set(predictions.columns) != columns:
        raise ValueError("Prediction table needs exactly the documented columns")
    if not predictions.split.eq(split).all():
        raise ValueError("Prediction split mismatch")
    subjects(predictions.subject_id.to_numpy(), len(predictions))
    subjects(predictions.sample_id.to_numpy(), len(predictions))
    subjects(predictions.model.to_numpy(), len(predictions))
    if predictions.duplicated(["model", "sample_id"]).any():
        raise ValueError("Duplicate prediction keys")
    rows = manifest[manifest.split == split].sort_values("sample_id")
    prediction_sets = {}
    for name, group in predictions.groupby("model"):
        if set(group.sample_id) != set(rows.sample_id):
            raise ValueError("Missing/extra prediction IDs; all models need the same rows")
        group = group.set_index("sample_id").loc[rows.sample_id]
        if not np.array_equal(group.subject_id.to_numpy(), rows.subject_id.to_numpy()):
            raise ValueError("Prediction subject mismatch")
        prediction_sets[name] = group[["pred_sbp", "pred_dbp"]].to_numpy()
    return bootstrap_bp(rows[["sbp", "dbp"]].to_numpy(), prediction_sets,
                        rows.subject_id.to_numpy(), config)