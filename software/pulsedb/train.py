
from pathlib import Path

import numpy as np
import pandas as pd
from xgboost import XGBRegressor
from sklearn.metrics import mean_absolute_error


def train_models(X, y_sbp, y_dbp, train_mask, random_state=42):
    """Train separate XGBoost models for SBP and DBP."""

    train_mask = np.asarray(train_mask, dtype=bool)
    y_sbp = np.asarray(y_sbp, dtype=float)
    y_dbp = np.asarray(y_dbp, dtype=float)

    if len(X) != len(y_sbp) or len(X) != len(y_dbp):
        raise ValueError("X and labels must have the same number of rows")

    if len(train_mask) != len(X):
        raise ValueError("train_mask length must match X")

    if not train_mask.any():
        raise ValueError("Training set is empty")

    if not np.isfinite(y_sbp).all() or not np.isfinite(y_dbp).all():
        raise ValueError("SBP/DBP labels contain NaN or infinity")

    model_sbp = XGBRegressor(
        n_estimators=300,
        max_depth=4,
        learning_rate=0.05,
        objective="reg:squarederror",
        random_state=random_state,
        n_jobs=-1,
    )

    model_dbp = XGBRegressor(
        n_estimators=300,
        max_depth=4,
        learning_rate=0.05,
        objective="reg:squarederror",
        random_state=random_state,
        n_jobs=-1,
    )

    model_sbp.fit(X.loc[train_mask], y_sbp[train_mask])
    model_dbp.fit(X.loc[train_mask], y_dbp[train_mask])

    return model_sbp, model_dbp


def save_models(model_sbp, model_dbp, output_dir):
    """Save trained models as JSON files."""

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    model_sbp.save_model(str(output_dir / "xgboost_sbp.json"))
    model_dbp.save_model(str(output_dir / "xgboost_dbp.json"))


if __name__ == "__main__":
    print("train.py đã nạp được.")
    print("Hãy gọi train_models() từ pipeline sau khi chuẩn bị X, nhãn và train_mask.")
