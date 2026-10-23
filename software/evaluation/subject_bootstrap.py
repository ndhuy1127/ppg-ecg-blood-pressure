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


# Paired contrasts: metric of model minus metric of the reference model, from
# the same draw (a negative MAE difference means the model has lower error).
CONTRAST_METRICS = ("subject_balanced_mae", "sample_weighted_mae")


def _contrast_pairs(contrasts, names):
    if contrasts is None:
        return None
    if not isinstance(contrasts, (list, tuple)):
        raise ValueError("contrasts must be a list of (model, reference) pairs")
    pairs = []
    for pair in contrasts:
        if (not isinstance(pair, (list, tuple)) or len(pair) != 2
                or pair[0] == pair[1] or any(name not in names for name in pair)):
            raise ValueError("Each contrast is two different model names")
        pairs.append((pair[0], pair[1]))
    if len(set(pairs)) != len(pairs):
        raise ValueError("Duplicate contrast")
    return pairs


def _difference(a, b):
    return None if a is None or b is None else a - b


def _interval(values, alpha):
    bounds = np.quantile(values, [alpha, 1 - alpha]).tolist() if values else None
    return {"bounds": bounds, "valid_repetitions": len(values),
            "status": "undefined" if not values
            else ("degenerate" if np.ptp(values) == 0 else "ok")}


def bootstrap_bp(reference, prediction_sets, subject_ids, config=BootstrapConfig(), *,
                 contrasts=None):
    """Same cluster draws for every model; no model fitting or selection here.

    ``contrasts``: optional (model, reference) pairs. For each, the difference
    model - reference of ``CONTRAST_METRICS`` per target is taken within every
    draw, and its percentile CI is reported under ``result["contrasts"]``. The
    point difference of subject-balanced MAE equals the mean over subjects of
    MAE_s(model) - MAE_s(reference). Without contrasts the result is unchanged.
    """
    reference = bp_pairs(reference, "reference")
    ids = subjects(subject_ids, len(reference))
    if not isinstance(prediction_sets, dict) or not prediction_sets:
        raise ValueError("Provide a nonempty model -> predictions mapping")
    predictions = {name: bp_pairs(values, "predictions") for name, values in prediction_sets.items()}
    if any(not isinstance(name, str) or not name.strip() for name in predictions):
        raise ValueError("Model names must be nonempty text")
    if any(values.shape != reference.shape for values in predictions.values()):
        raise ValueError("reference and predictions must have identical shapes")
    pairs = _contrast_pairs(contrasts, predictions)
    point = {name: _statistics(evaluate_bp(reference, values, ids)) for name, values in predictions.items()}
    n_subjects = len(np.unique(ids))
    result = {"n_rows": len(ids), "n_subjects": n_subjects, "seed": config.seed,
              "repetitions": config.repetitions, "confidence": config.confidence,
              "method": "subject cluster percentile; shared draws across models",
              "models": {}, "status": "ok"}
    contrast_point = [
        {target: {metric: _difference(point[a][target][metric],
                                      point[b][target][metric])
                  for metric in CONTRAST_METRICS} for target in point[a]}
        for a, b in pairs or ()
    ]
    if n_subjects < config.min_subjects:
        result["status"] = "insufficient_subjects"
        result["models"] = {name: {"point": stats, "ci": None} for name, stats in point.items()}
        if pairs is not None:
            result["contrasts"] = [{"model": a, "reference": b, "point": p, "ci": None}
                                   for (a, b), p in zip(pairs, contrast_point)]
        return result
    samples = {name: {target: {metric: [] for metric in stats[target]} for target in stats} for name, stats in point.items()}
    contrast_samples = [{target: {metric: [] for metric in CONTRAST_METRICS}
                         for target in point[a]} for a, _ in pairs or ()]
    rng = np.random.default_rng(config.seed)
    for _ in range(config.repetitions):
        indices, draw_ids = cluster_draw(ids, rng)
        draw = {}
        for name, values in predictions.items():
            stats = draw[name] = _statistics(
                evaluate_bp(reference[indices], values[indices], draw_ids))
            for target in stats:
                for metric, value in stats[target].items():
                    if value is not None:
                        samples[name][target][metric].append(value)
        for (a, b), store in zip(pairs or (), contrast_samples):
            for target, metrics in store.items():
                for metric, values in metrics.items():
                    value = _difference(draw[a][target][metric],
                                        draw[b][target][metric])
                    if value is not None:
                        values.append(value)
    alpha = (1 - config.confidence) / 2
    for name in point:
        intervals = {target: {metric: _interval(values, alpha)
                              for metric, values in samples[name][target].items()}
                     for target in point[name]}
        result["models"][name] = {"point": point[name], "ci": intervals}
    if pairs is not None:
        result["contrasts"] = [
            {"model": a, "reference": b, "point": p,
             "ci": {target: {metric: _interval(values, alpha)
                             for metric, values in metrics.items()}
                    for target, metrics in store.items()}}
            for (a, b), p, store in zip(pairs, contrast_point, contrast_samples)
        ]
    return result


def evaluate_prediction_table(manifest, inventory, predictions, *, split="val",
                              config=BootstrapConfig(), contrasts=None):
    """Validate v2 conservation/leakage and exact prediction keys before metrics.

    Table columns: sample_id, subject_id, split, model, pred_sbp, pred_dbp.
    Caller still owns raw/pool permissions and observation/calibration checks.
    Test evaluation requires caller's prior model/threshold lock; not enforced here.
    ``contrasts`` is passed to ``bootstrap_bp``.
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
                        rows.subject_id.to_numpy(), config, contrasts=contrasts)