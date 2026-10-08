"""B0 train-mean and B1 calibration-mean baselines for absolute BP (mmHg)."""

import numpy as np
from numpy.typing import ArrayLike, NDArray

from software._bp_validation import bp_pairs, finite_result, subjects


class PopulationMeanBaseline:
    """B0: fit only explicit train labels; predict without evaluation labels."""

    def __init__(self) -> None:
        self._constant: NDArray[np.float64] | None = None

    def fit(self, train_labels: ArrayLike) -> "PopulationMeanBaseline":
        """Use equally weighted train rows, with columns [SBP, DBP]."""
        labels = bp_pairs(train_labels, "train_labels")
        with np.errstate(over="ignore", invalid="ignore"):
            constant = finite_result(labels.mean(axis=0))
        self._constant = constant
        return self

    def predict(self, n_samples: int) -> NDArray[np.float64]:
        """Return n copies of the stored pair; never refit during prediction."""
        if self._constant is None:
            raise RuntimeError("B0 must be fitted on train_labels before prediction")
        if (
            isinstance(n_samples, (bool, np.bool_))
            or not isinstance(n_samples, (int, np.integer))
            or n_samples <= 0
        ):
            raise ValueError("n_samples must be a positive integer")
        return np.tile(self._constant, (n_samples, 1))


class UncalibratedSubjectError(ValueError):
    """B1 cannot predict for subjects absent from explicit calibration data."""


class PersonalMeanBaseline:
    """B1 for calibrated subjects only; the caller must verify chronology/split."""

    def __init__(self) -> None:
        self._constants: dict[str, NDArray[np.float64]] | None = None

    def fit(
        self, calibration_subject_ids: ArrayLike, calibration_labels: ArrayLike
    ) -> "PersonalMeanBaseline":
        """Replace state with per-subject means of explicit calibration rows."""
        labels = bp_pairs(calibration_labels, "calibration_labels")
        ids = subjects(calibration_subject_ids, len(labels))
        with np.errstate(over="ignore", invalid="ignore"):
            constants = {
                str(subject): finite_result(labels[ids == subject].mean(axis=0))
                for subject in np.unique(ids)
            }
        self._constants = constants
        return self

    def predict(self, subject_ids: ArrayLike) -> NDArray[np.float64]:
        """Return pairs in input order; reject the entire call if any ID is unknown."""
        if self._constants is None:
            raise RuntimeError("B1 must be fitted on calibration data before prediction")
        ids = subjects(subject_ids)
        if any(subject not in self._constants for subject in ids):
            # Do not expose subject identifiers in errors/logs.
            raise UncalibratedSubjectError(
                "B1 cannot predict: at least one subject has no calibration data"
            )
        return np.stack([self._constants[subject] for subject in ids])
