"""B3: separate XGBoost regressors for SBP and DBP, fitted on train rows only."""

from pathlib import Path

import numpy as np
from numpy.typing import ArrayLike, NDArray
from xgboost import XGBRegressor

from software._bp_validation import bp_pairs, sample_weights

VERSION = "b3-xgboost-v0"
DEFAULT_PARAMS = {
    "n_estimators": 300,
    "max_depth": 4,
    "learning_rate": 0.05,
    "objective": "reg:squarederror",
    "tree_method": "hist",
    "n_jobs": 1,
}
# Seed is passed separately so it is always recorded; add other keys explicitly.
ALLOWED_PARAMS = frozenset(DEFAULT_PARAMS) | {
    "subsample", "colsample_bytree", "min_child_weight", "reg_lambda", "reg_alpha",
}


def _features(values, name: str) -> NDArray[np.float64]:
    if np.ma.isMaskedArray(values):
        raise ValueError(f"{name} must not be a masked array; masks are not imputed")
    array = np.asarray(values)
    if array.ndim != 2 or 0 in array.shape or array.dtype.kind not in "iuf":
        raise ValueError(f"{name} must be a nonempty 2-D numeric array")
    array = array.astype(np.float64)
    if not np.isfinite(array).all():
        raise ValueError(f"{name} must be finite; missing values are not imputed")
    return array


class XGBoostBaseline:
    """Absolute [SBP, DBP] in mmHg; no imputation, scaling or feature selection."""

    def __init__(self, seed: int, params: dict | None = None) -> None:
        if isinstance(seed, bool) or not isinstance(seed, int) or seed < 0:
            raise ValueError("seed must be a nonnegative integer")
        params = dict(DEFAULT_PARAMS if params is None else params)
        if set(params) - ALLOWED_PARAMS:
            raise ValueError("Unsupported B3 parameter; extend ALLOWED_PARAMS first")
        n_jobs = params.get("n_jobs")
        if isinstance(n_jobs, bool) or not isinstance(n_jobs, int) or n_jobs < 1:
            raise ValueError("n_jobs must be a fixed positive integer for reproducibility")
        self.seed = seed
        self.params = params
        self._models: tuple[XGBRegressor, XGBRegressor] | None = None
        self._n_features: int | None = None

    def fit(
        self, train_features: ArrayLike, train_labels: ArrayLike,
        sample_weight: ArrayLike | None = None,
    ) -> "XGBoostBaseline":
        """Fit one model per column of train_labels [SBP, DBP]; replaces old state.

        ``sample_weight`` (one positive weight per row) is passed to both models.
        """
        features = _features(train_features, "train_features")
        labels = bp_pairs(train_labels, "train_labels")
        if len(features) != len(labels):
            raise ValueError("train_features and train_labels need the same row count")
        weights = None if sample_weight is None else sample_weights(
            sample_weight, len(labels))
        models = []
        for column in range(2):
            model = XGBRegressor(**self.params, random_state=self.seed)
            model.fit(features, labels[:, column], sample_weight=weights)
            models.append(model)
        self._models = (models[0], models[1])
        self._n_features = features.shape[1]
        return self

    def predict(self, features: ArrayLike) -> NDArray[np.float64]:
        """Return (n, 2) predictions in input row order; never refits."""
        if self._models is None:
            raise RuntimeError("B3 must be fitted on train data before prediction")
        array = _features(features, "features")
        if array.shape[1] != self._n_features:
            raise ValueError("Feature count differs from the fitted model")
        predictions = np.column_stack(
            [model.predict(array).astype(np.float64) for model in self._models]
        )
        if not np.isfinite(predictions).all():
            raise ValueError("B3 produced nonfinite predictions")
        return predictions

    def save(self, directory: Path) -> dict[str, Path]:
        """Write xgboost_sbp.json/xgboost_dbp.json; refuse to overwrite files."""
        if self._models is None:
            raise RuntimeError("B3 must be fitted before saving")
        paths = {}
        for target, model in zip(("sbp", "dbp"), self._models):
            path = Path(directory) / f"xgboost_{target}.json"
            with path.open("xb") as stream:
                stream.write(bytes(model.get_booster().save_raw(raw_format="json")))
            paths[target] = path
        return paths
