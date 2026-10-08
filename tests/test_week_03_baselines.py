"""Known-answer synthetic checks of B0/B1 without real data or split tuning."""

import numpy as np
import pytest

from software.evaluation.bp_metrics import evaluate_bp
from software.models.constant_baselines import (
    PersonalMeanBaseline,
    PopulationMeanBaseline,
    UncalibratedSubjectError,
)


def test_b0_uses_train_means_separately_for_sbp_dbp():
    model = PopulationMeanBaseline().fit([[110, 70], [130, 90], [120, 80]])
    np.testing.assert_array_equal(model.predict(2), [[120, 80], [120, 80]])


def test_b0_evaluation_labels_change_metrics_but_never_predictions():
    model = PopulationMeanBaseline().fit([[110, 70], [130, 90]])
    predicted = model.predict(2)
    first = evaluate_bp([[120, 80], [120, 80]], predicted, ["A", "B"])
    second = evaluate_bp([[130, 90], [130, 90]], predicted, ["A", "B"])
    assert first.sample_weighted["SBP"].mae == 0
    assert second.sample_weighted["SBP"].mae == 10
    np.testing.assert_array_equal(model.predict(2), predicted)


def test_b1_uses_only_calibration_means_and_preserves_prediction_order():
    model = PersonalMeanBaseline().fit(
        ["A", "B", "A"], [[110, 70], [140, 90], [130, 80]]
    )
    np.testing.assert_array_equal(
        model.predict(["B", "A", "B"]), [[140, 90], [120, 75], [140, 90]]
    )


def test_b1_evaluation_labels_change_metrics_but_never_predictions():
    model = PersonalMeanBaseline().fit(["A", "B"], [[120, 80], [140, 90]])
    predicted = model.predict(["A", "B"])
    first = evaluate_bp(predicted, predicted, ["A", "B"])
    second = evaluate_bp(predicted + 10, predicted, ["A", "B"])
    assert first.subject_balanced["DBP"].mae == 0
    assert second.subject_balanced["DBP"].mae == 10
    np.testing.assert_array_equal(model.predict(["A", "B"]), predicted)


def test_b1_rejects_unknown_subject_without_fallback_or_exposing_id():
    model = PersonalMeanBaseline().fit(["A"], [[120, 80]])
    with pytest.raises(UncalibratedSubjectError, match="no calibration") as caught:
        model.predict(["A", "UNKNOWN_ID"])
    assert "UNKNOWN_ID" not in str(caught.value)
    np.testing.assert_array_equal(model.predict(["A"]), [[120, 80]])


def test_models_do_not_alias_inputs_or_returned_predictions():
    labels = np.array([[110.0, 70], [130, 90]])
    b0 = PopulationMeanBaseline().fit(labels)
    b1 = PersonalMeanBaseline().fit(["A", "A"], labels)
    labels[:] = 0
    b0.predict(1)[:] = 0
    b1.predict(["A"])[:] = 0
    np.testing.assert_array_equal(b0.predict(1), [[120, 80]])
    np.testing.assert_array_equal(b1.predict(["A"]), [[120, 80]])


def test_refit_replaces_b1_state_and_invalid_refit_keeps_previous_state():
    model = PersonalMeanBaseline().fit(["A"], [[120, 80]])
    with pytest.raises(ValueError):
        model.fit(["B"], [[np.nan, 90]])
    np.testing.assert_array_equal(model.predict(["A"]), [[120, 80]])
    model.fit(["B"], [[140, 90]])
    with pytest.raises(UncalibratedSubjectError):
        model.predict(["A"])


def test_prediction_requires_fit():
    with pytest.raises(RuntimeError, match="fitted"):
        PopulationMeanBaseline().predict(1)
    with pytest.raises(RuntimeError, match="fitted"):
        PersonalMeanBaseline().predict(["A"])


@pytest.mark.parametrize("count", [0, -1, 1.5, True, np.bool_(True), "2", None])
def test_b0_rejects_invalid_prediction_count(count):
    with pytest.raises(ValueError, match="positive integer"):
        PopulationMeanBaseline().fit([[120, 80]]).predict(count)


@pytest.mark.parametrize(
    "labels",
    [
        [], [120, 80], [[120]], [[120, 80, 40]], [[[120, 80]]],
        [[120, 80], [130]], [[np.nan, 80]], [[120, np.inf]],
        [[-np.inf, 80]], [[None, 80]], [["120", "80"]],
        [[True, False]], [[True, 80]], [[120 + 1j, 80]],
        np.ma.array([[120, 80]], mask=[[True, False]]),
    ],
)
def test_baselines_reject_invalid_labels(labels):
    with pytest.raises(ValueError):
        PopulationMeanBaseline().fit(labels)
    with pytest.raises(ValueError):
        PersonalMeanBaseline().fit(["A"], labels)


@pytest.mark.parametrize(
    "ids", [[], [["A"]], [None], [np.nan], [1], [""], [" "], [" A"], ["A", "B"]]
)
def test_b1_rejects_invalid_calibration_ids(ids):
    with pytest.raises(ValueError):
        PersonalMeanBaseline().fit(ids, [[120, 80]])


@pytest.mark.parametrize("ids", [[], [["A"]], [None], [""], [1], [" A"]])
def test_b1_rejects_invalid_prediction_ids(ids):
    with pytest.raises(ValueError):
        PersonalMeanBaseline().fit(["A"], [[120, 80]]).predict(ids)
