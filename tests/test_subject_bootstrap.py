"""Cluster multiplicity, aggregation and validated table integration tests."""

from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from software.data_io.split_manifest import build_inventory, make_manifest
from software.evaluation.subject_bootstrap import (
    BootstrapConfig, bootstrap_bp, cluster_draw, evaluate_prediction_table,
)


def test_duplicate_draw_keeps_all_rows_and_new_cluster_identity():
    class FixedDraw:
        def choice(self, unique, size, replace):
            return np.array(["A", "A", "B"])
    indices, ids = cluster_draw(["A", "A", "B", "C"], FixedDraw())
    assert indices.tolist() == [0, 1, 0, 1, 2]
    assert ids.tolist() == ["DRAW_0", "DRAW_0", "DRAW_1", "DRAW_1", "DRAW_2"]


def test_bootstrap_reproducible_shared_draws_and_point_metrics():
    ref = np.tile([120, 80], (4, 1))
    pred = ref + np.array([[0, 0], [0, 0], [0, 0], [8, -4]])
    config = BootstrapConfig(seed=4, repetitions=100)
    first = bootstrap_bp(ref, {"B0": pred, "B3": pred}, ["A", "A", "A", "B"], config)
    assert first == bootstrap_bp(ref, {"B0": pred, "B3": pred}, ["A", "A", "A", "B"], config)
    assert first["models"]["B0"] == first["models"]["B3"]
    point = first["models"]["B0"]["point"]["SBP"]
    assert point["subject_balanced_mae"] == 4
    assert point["sample_weighted_mae"] == 2
    assert point["sample_sd"] == 4
    assert first["models"]["B0"]["ci"]["SBP"]["subject_balanced_mae"]["bounds"] == [0, 8]


def test_insufficient_subjects_and_degenerate_results():
    ref = [[120, 80]]
    one = bootstrap_bp(ref, {"B0": ref}, ["A"], BootstrapConfig(repetitions=10))
    assert one["status"] == "insufficient_subjects"
    assert one["models"]["B0"]["ci"] is None
    two = bootstrap_bp(ref * 2, {"B0": ref * 2}, ["A", "B"], BootstrapConfig(repetitions=10))
    assert two["models"]["B0"]["ci"]["SBP"]["sample_sd"]["status"] == "degenerate"


def test_existing_b0_b1_and_metrics_are_reused():
    from software.models.constant_baselines import PopulationMeanBaseline, PersonalMeanBaseline
    reference = [[124, 84], [126, 86]]
    ids = ["SYN_A", "SYN_B"]
    b0 = PopulationMeanBaseline().fit([[110, 70], [130, 90]])
    b1 = PersonalMeanBaseline().fit(ids, [[120, 80], [122, 82]])
    result = bootstrap_bp(reference, {"B0": b0.predict(2), "B1": b1.predict(ids)}, ids,
                          BootstrapConfig(repetitions=10))
    assert result["models"]["B0"]["point"]["SBP"]["subject_balanced_mae"] == 5
    assert result["models"]["B1"]["point"]["SBP"]["subject_balanced_mae"] == 4


@pytest.mark.parametrize("ids", [[], [None], [1], [""], ["A", "B"]])
def test_invalid_ids(ids):
    with pytest.raises(ValueError):
        bootstrap_bp([[120, 80]], {"B0": [[120, 80]]}, ids)


def test_empty_input_and_bad_config():
    with pytest.raises(ValueError):
        bootstrap_bp([], {}, [])
    with pytest.raises(ValueError):
        BootstrapConfig(repetitions=1)
    with pytest.raises(ValueError):
        BootstrapConfig(seed=True)
    for confidence in (True, "0.95", None, [0.95]):
        with pytest.raises(ValueError):
            BootstrapConfig(confidence=confidence)


def table_fixture():
    segments = [SimpleNamespace(subject_id=f"SYN_{i}", sbp=120., dbp=80.,
        ecg=np.array([i, i + 1.]), ppg=np.array([i + 2., i + 3.]),
        abp=np.array([i + 4., i + 5.])) for i in range(10)]
    inventory = build_inventory(segments, "SYNTHETIC", "a" * 64)
    manifest = make_manifest(inventory, ratios=(0.6, 0.2, 0.2))
    rows = manifest[manifest.split == "val"]
    predictions = pd.DataFrame({"sample_id": rows.sample_id, "subject_id": rows.subject_id,
        "split": "val", "model": "B0", "pred_sbp": 122., "pred_dbp": 79.})
    return manifest, inventory, predictions


def test_manifest_predictions_join_by_id_not_order():
    manifest, inventory, predictions = table_fixture()
    result = evaluate_prediction_table(manifest, inventory, predictions.iloc[::-1], config=BootstrapConfig(repetitions=10))
    assert result["models"]["B0"]["point"]["SBP"]["subject_balanced_mae"] == 2


@pytest.mark.parametrize("case", ["missing", "duplicate", "subject", "split", "nan", "label"])
def test_prediction_mismatch_rejected(case):
    manifest, inventory, predictions = table_fixture()
    if case == "missing":
        predictions = predictions.iloc[:1]
    elif case == "duplicate":
        predictions = pd.concat([predictions, predictions.iloc[:1]])
    elif case == "label":
        manifest.loc[0, "sbp"] += 1
    else:
        field, value = {"subject": ("subject_id", "OTHER"), "split": ("split", "test"),
                        "nan": ("pred_sbp", np.nan)}[case]
        predictions.loc[predictions.index[0], field] = value
    with pytest.raises(ValueError):
        evaluate_prediction_table(manifest, inventory, predictions, config=BootstrapConfig(repetitions=10))