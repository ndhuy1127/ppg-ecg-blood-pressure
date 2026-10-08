"""Shared strict input validation for the Week 3 BP baselines and metrics."""

import numpy as np
from numpy.typing import ArrayLike, NDArray


def bp_pairs(values: ArrayLike, name: str) -> NDArray[np.float64]:
    """Require nonempty finite real (n, 2) arrays ordered [SBP, DBP]."""
    if np.ma.isMaskedArray(values):
        raise ValueError(f"{name} must not be a masked array")
    try:
        array = np.asarray(values)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be a rectangular numeric (n, 2) array") from exc
    if array.ndim != 2 or array.shape[1] != 2 or array.shape[0] == 0:
        raise ValueError(f"{name} must have nonempty shape (n, 2): [SBP, DBP]")
    if array.dtype.kind not in "iuf":
        raise ValueError(f"{name} must contain real numbers, without missing values")
    if any(
        isinstance(value, (bool, np.bool_))
        for value in np.asarray(values, dtype=object).flat
    ):
        raise ValueError(f"{name} must not contain booleans")
    with np.errstate(over="ignore", invalid="ignore"):
        array = array.astype(np.float64, copy=True)
    if not np.isfinite(array).all():
        raise ValueError(f"{name} must contain finite numbers; NaN/Inf are rejected")
    return array


def subjects(values: ArrayLike, n: int | None = None) -> NDArray[np.str_]:
    """Require 1-D pseudonymous string IDs, without implicit normalization."""
    if np.ma.isMaskedArray(values):
        raise ValueError("subject_ids must not be a masked array")
    array = np.asarray(values, dtype=object)
    if array.ndim != 1 or array.size == 0:
        raise ValueError("subject_ids must be a nonempty 1-D array")
    if n is not None and array.size != n:
        raise ValueError("subject_ids length must match the BP row count")
    if any(
        not isinstance(value, str) or not value or value.strip() != value
        for value in array
    ):
        raise ValueError("subject_ids must be nonempty strings without edge whitespace")
    return array.astype(str)


def finite_result(values: NDArray[np.float64]) -> NDArray[np.float64]:
    """Reject arithmetic overflow instead of returning invalid results."""
    if not np.isfinite(values).all():
        raise ValueError("BP arithmetic produced nonfinite values (overflow)")
    return values
