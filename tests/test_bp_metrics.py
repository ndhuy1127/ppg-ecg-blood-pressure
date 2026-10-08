"""Known-answer, validation and aggregation tests for descriptive BP metrics."""

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from scripts.demo_week_03_baselines import run_demo
from software.evaluation.bp_metrics import evaluate_bp


def test_metrics_match_hand_calculation_and_error_direction():
    reference = [[120, 80], [120, 80], [120, 80]]
    predictions = [[118, 81], [120, 79], [122, 83]]
    result = evaluate_bp(reference, predictions, ["A", "A", "A"])
    sbp, dbp = result.sample_weighted["SBP"], result.sample_weighted["DBP"]
    assert sbp.n == dbp.n == 3
    assert sbp.mae == pytest.approx(4 / 3)
    assert sbp.bias == 0
    assert sbp.sd == 2
    assert dbp.mae == pytest.approx(5 / 3)
    assert dbp.bias == 1
    assert dbp.sd == 2
    reversed_result = evaluate_bp(predictions, reference, ["A", "A", "A"])
    assert reversed_result.sample_weighted["DBP"].bias == -1


def test_subject_balanced_averages_differ_from_sample_weighted():
    reference = np.tile([120, 80], (4, 1))
    predictions = [[120, 80], [120, 80], [120, 80], [128, 76]]
    result = evaluate_bp(reference, predictions, ["A", "A", "A", "B"])
    assert result.sample_weighted["SBP"].mae == 2
    assert result.sample_weighted["SBP"].bias == 2
    assert result.sample_weighted["SBP"].sd == 4
    assert result.subject_balanced["SBP"].mae == 4
    assert result.subject_balanced["SBP"].bias == 4
    assert result.subject_balanced["SBP"].n_subjects == 2
    assert result.sample_weighted["DBP"].mae == 1
    assert result.sample_weighted["DBP"].bias == -1
    assert result.subject_balanced["DBP"].mae == 2
    assert result.subject_balanced["DBP"].bias == -2
    assert result.by_subject["A"]["SBP"].sd == 0
    assert result.by_subject["B"]["SBP"].sd is None


def test_single_row_retains_mae_bias_but_has_no_sample_sd():
    result = evaluate_bp([[120, 80]], [[118, 81]], ["A"])
    for target in ("SBP", "DBP"):
        assert result.sample_weighted[target].n == 1
        assert result.sample_weighted[target].sd is None
        assert result.by_subject["A"][target].sd is None
    assert result.sample_weighted["SBP"].mae == 2
    assert result.sample_weighted["SBP"].bias == -2


@pytest.mark.parametrize(
    "bad", [[], [120, 80], [[120]], [[120, 80, 40]], [[None, 80]],
            [[np.nan, 80]], [[120, np.inf]], [["120", "80"]], [[120, True]],
            np.ma.array([[120, 80]], mask=[[True, False]])]
)
def test_metrics_reject_invalid_arrays_in_either_argument(bad):
    with pytest.raises(ValueError):
        evaluate_bp(bad, [[120, 80]], ["A"])
    with pytest.raises(ValueError):
        evaluate_bp([[120, 80]], bad, ["A"])


def test_metrics_reject_broadcastable_shape_mismatch():
    with pytest.raises(ValueError, match="identical shapes"):
        evaluate_bp([[120, 80], [130, 90]], [[120, 80]], ["A", "A"])


@pytest.mark.parametrize("ids", [[], ["A", "B"], [["A"]], [None], [1], [""]])
def test_metrics_reject_missing_invalid_or_mismatched_ids(ids):
    with pytest.raises(ValueError):
        evaluate_bp([[120, 80]], [[120, 80]], ids)


def test_metrics_reject_arithmetic_overflow():
    with pytest.raises(ValueError, match="overflow"):
        evaluate_bp([[-1e308, 80]], [[1e308, 80]], ["A"])


def test_demo_is_reproducible_and_marks_results_as_synthetic():
    first = run_demo()
    assert first == run_demo()
    assert first["source_type"] == "SYNTHETIC"
    assert first["seed"] == 20261003
    for baseline in ("B0", "B1"):
        assert first[baseline]["sample_weighted"]["SBP"]["n"] == 3
        assert first[baseline]["subject_balanced"]["DBP"]["n_subjects"] == 2


def test_demo_runs_directly_without_cwd_or_pythonpath_import_help():
    script = Path(__file__).resolve().parents[1] / "scripts/demo_week_03_baselines.py"
    result = subprocess.run(
        [sys.executable, "-I", str(script)],
        cwd=script.parent,
        capture_output=True,
        text=True,
        check=True,
    )
    assert json.loads(result.stdout) == run_demo()
