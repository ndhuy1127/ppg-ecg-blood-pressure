
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error


def evaluate_model(y_true, y_pred):
    """Calculate MAE, bias and standard deviation of prediction errors."""

    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)

    if y_true.shape != y_pred.shape:
        raise ValueError("y_true and y_pred must have the same shape")

    if y_true.size == 0:
        raise ValueError("Cannot evaluate empty arrays")

    if not np.isfinite(y_true).all() or not np.isfinite(y_pred).all():
        raise ValueError("Values contain NaN or infinity")

    errors = y_pred - y_true

    return {
        "n_samples": len(y_true),
        "MAE_mmHg": float(mean_absolute_error(y_true, y_pred)),
        "bias_mmHg": float(np.mean(errors)),
        "SD_error_mmHg": (
            float(np.std(errors, ddof=1))
            if len(errors) > 1
            else 0.0
        ),
    }


def build_metrics_table(
    y_sbp, pred_sbp, y_dbp, pred_dbp, split_name
):
    """Create a metrics table for one data split."""

    rows = []

    for target, y_true, y_pred in [
        ("SBP", y_sbp, pred_sbp),
        ("DBP", y_dbp, pred_dbp),
    ]:
        metrics = evaluate_model(y_true, y_pred)
        rows.append({
            "split": split_name,
            "target": target,
            **metrics,
        })

    return pd.DataFrame(rows)
