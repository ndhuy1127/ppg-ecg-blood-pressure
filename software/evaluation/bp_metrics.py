"""Descriptive absolute BP errors; no independence claims or inference."""

from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike, NDArray

from software._bp_validation import bp_pairs, finite_result, subjects

TARGETS = ("SBP", "DBP")


@dataclass(frozen=True)
class ErrorMetrics:
    """Errors in mmHg; sample SD is undefined (None) when n < 2."""

    n: int
    mae: float
    bias: float
    sd: float | None


@dataclass(frozen=True)
class SubjectBalancedMetrics:
    """Equal mean of each subject's MAE/bias; no macro SD is defined."""

    n_subjects: int
    mae: float
    bias: float


@dataclass(frozen=True)
class BPEvaluation:
    sample_weighted: dict[str, ErrorMetrics]
    by_subject: dict[str, dict[str, ErrorMetrics]]
    subject_balanced: dict[str, SubjectBalancedMetrics]


def _summarize(errors: NDArray[np.float64]) -> dict[str, ErrorMetrics]:
    result = {}
    with np.errstate(over="ignore", invalid="ignore"):
        for index, target in enumerate(TARGETS):
            column = errors[:, index]
            mae = float(finite_result(np.asarray(np.abs(column).mean())))
            bias = float(finite_result(np.asarray(column.mean())))
            sd = (
                float(finite_result(np.asarray(column.std(ddof=1))))
                if len(column) >= 2
                else None
            )
            result[target] = ErrorMetrics(len(column), mae, bias, sd)
    return result


def evaluate_bp(
    reference: ArrayLike, predictions: ArrayLike, subject_ids: ArrayLike
) -> BPEvaluation:
    """Summarize prediction-reference separately for SBP/DBP.

    Input rows must already represent the agreed observation unit, without
    duplicate cuff windows. This function cannot validate event IDs or splits.
    Every row is retained; invalid input raises ValueError instead of being dropped.
    """
    reference = bp_pairs(reference, "reference")
    predictions = bp_pairs(predictions, "predictions")
    if reference.shape != predictions.shape:
        raise ValueError("reference and predictions must have identical shapes")
    ids = subjects(subject_ids, len(reference))
    with np.errstate(over="ignore", invalid="ignore"):
        errors = finite_result(predictions - reference)
    by_subject = {
        str(subject): _summarize(errors[ids == subject]) for subject in np.unique(ids)
    }
    balanced = {
        target: SubjectBalancedMetrics(
            n_subjects=len(by_subject),
            mae=float(np.mean([row[target].mae for row in by_subject.values()])),
            bias=float(np.mean([row[target].bias for row in by_subject.values()])),
        )
        for target in TARGETS
    }
    return BPEvaluation(_summarize(errors), by_subject, balanced)
