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


class SequenceDraw:
    """Stands in for numpy's Generator: returns the given cluster draws in turn."""

    def __init__(self, draws):
        self.draws = iter(draws)

    def choice(self, unique, size, replace):
        return np.array(next(self.draws))


def contrast_fixture():
    # Absolute errors (SBP and DBP alike). Model M: A rows 2 and 4 (MAE_A 3),
    # B row 10 (MAE_B 10). Reference R: A rows 1 and 1, B row 4.
    ref = np.tile([120.0, 80.0], (3, 1))
    m = ref + np.array([[2, 2], [4, 4], [10, 10]])
    r = ref + np.array([[1, 1], [-1, -1], [4, 4]])
    return ref, {"M": m, "R": r}, ["A", "A", "B"]


def test_contrast_is_the_difference_within_each_draw(monkeypatch):
    ref, models, ids = contrast_fixture()
    draws = [["A", "B"], ["B", "B"], ["A", "A"]]
    config = BootstrapConfig(repetitions=3, confidence=0.5)
    monkeypatch.setattr("software.evaluation.subject_bootstrap.np.random.default_rng",
                        lambda seed: SequenceDraw(draws))
    result = bootstrap_bp(ref, models, ids, config, contrasts=[("M", "R")])
    (contrast,) = result["contrasts"]
    assert (contrast["model"], contrast["reference"]) == ("M", "R")
    for target in ("SBP", "DBP"):
        # Point: subject-balanced (3 + 10) / 2 - (1 + 4) / 2; sample (16 - 6) / 3.
        point = contrast["point"][target]
        assert point["subject_balanced_mae"] == pytest.approx(4)
        assert point["sample_weighted_mae"] == pytest.approx(10 / 3)
        # Draws [A,B], [B,B], [A,A] give 4, 6, 2 (subject-balanced) and 10/3, 6, 2
        # (sample-weighted); quartiles by linear interpolation.
        ci = contrast["ci"][target]
        assert ci["subject_balanced_mae"]["bounds"] == pytest.approx([3, 5])
        assert ci["sample_weighted_mae"]["bounds"] == pytest.approx(
            [2 + (10 / 3 - 2) / 2, 10 / 3 + (6 - 10 / 3) / 2])
        assert ci["subject_balanced_mae"]["valid_repetitions"] == 3
    # The per-model results are those of a call without contrasts.
    monkeypatch.setattr("software.evaluation.subject_bootstrap.np.random.default_rng",
                        lambda seed: SequenceDraw(draws))
    plain = bootstrap_bp(ref, models, ids, config)
    assert "contrasts" not in plain and plain["models"] == result["models"]


def test_contrast_sign_identity_and_insufficient_subjects():
    ref, models, ids = contrast_fixture()
    config = BootstrapConfig(seed=3, repetitions=200)
    both = bootstrap_bp(ref, {**models, "M2": models["M"]}, ids, config,
                        contrasts=[("M", "R"), ("R", "M"), ("M", "M2")])
    forward, backward, same = both["contrasts"]
    low, high = forward["ci"]["SBP"]["subject_balanced_mae"]["bounds"]
    assert backward["ci"]["SBP"]["subject_balanced_mae"]["bounds"] == pytest.approx(
        [-high, -low])
    assert same["point"]["SBP"]["subject_balanced_mae"] == 0
    assert same["ci"]["SBP"]["subject_balanced_mae"]["bounds"] == [0, 0]
    assert same["ci"]["SBP"]["subject_balanced_mae"]["status"] == "degenerate"
    assert both == bootstrap_bp(ref, {**models, "M2": models["M"]}, ids, config,
                                contrasts=[("M", "R"), ("R", "M"), ("M", "M2")])
    one = bootstrap_bp(ref[:1], {"M": models["M"][:1], "R": models["R"][:1]}, ["A"],
                       config, contrasts=[("M", "R")])
    assert one["status"] == "insufficient_subjects"
    assert one["contrasts"][0]["ci"] is None
    assert one["contrasts"][0]["point"]["SBP"]["subject_balanced_mae"] == 1


ALL_METHODS = ("percentile", "bca", "bootstrap_t", "student_t", "t_envelope")


def test_contrast_ci_methods_known_answers(monkeypatch):
    # d_s = MAE_s(M) - MAE_s(R): A 3 - 1 = 2, B 10 - 4 = 6; mean 4, SD 2.828, SE 2.
    ref, models, ids = contrast_fixture()
    draws = [["A", "B"], ["B", "B"], ["A", "A"]]
    monkeypatch.setattr("software.evaluation.subject_bootstrap.np.random.default_rng",
                        lambda seed: SequenceDraw(draws))
    result = bootstrap_bp(ref, models, ids, BootstrapConfig(repetitions=3, confidence=0.5),
                          contrasts=[("M", "R")], contrast_ci_methods=ALL_METHODS)
    assert result["contrast_ci_methods"] == list(ALL_METHODS)
    (contrast,) = result["contrasts"]
    for target in ("SBP", "DBP"):
        got = contrast["ci_methods"][target]["subject_balanced_mae"]
        # Percentile: draw means 4, 6, 2, the same draws as the existing CI.
        assert got["percentile"]["bounds"] == pytest.approx(
            contrast["ci"][target]["subject_balanced_mae"]["bounds"])
        assert got["percentile"]["bounds"] == pytest.approx([3, 5])
        # Student t, 50 %: t(1; 0.75) = 1, so 4 -/+ 1 * 2.
        assert got["student_t"]["bounds"] == pytest.approx([2, 6])
        # Bootstrap-t: each draw's t is 0 ([A,B] is centred; [B,B] and [A,A] have
        # SE 0), so the interval collapses on the mean.
        assert got["bootstrap_t"]["bounds"] == pytest.approx([4, 4])
        assert got["bootstrap_t"]["status"] == "degenerate"
        # The envelope takes the wider limit on each side.
        assert got["t_envelope"]["bounds"] == pytest.approx([2, 6])
        assert got["bca"]["status"] == "ok"
    # Without the methods, the result is exactly that of earlier versions.
    monkeypatch.setattr("software.evaluation.subject_bootstrap.np.random.default_rng",
                        lambda seed: SequenceDraw(draws))
    plain = bootstrap_bp(ref, models, ids, BootstrapConfig(repetitions=3, confidence=0.5),
                         contrasts=[("M", "R")])
    assert "contrast_ci_methods" not in plain and "ci_methods" not in plain["contrasts"][0]
    assert plain["contrasts"][0]["ci"] == contrast["ci"]
    assert plain["models"] == result["models"]


def test_contrast_ci_methods_follow_the_shared_formulas_with_real_draws():
    from scipy import stats

    rng = np.random.default_rng(11)
    ids = np.repeat([f"SYN_{i}" for i in range(12)], 3)
    ref = np.tile([120.0, 80.0], (len(ids), 1))
    m = ref + rng.normal(0, 4, ref.shape)
    r = ref + rng.normal(0, 4, ref.shape)
    config = BootstrapConfig(seed=5, repetitions=400)
    result = bootstrap_bp(ref, {"M": m, "R": r}, ids, config, contrasts=[("M", "R")],
                          contrast_ci_methods=ALL_METHODS)
    (contrast,) = result["contrasts"]
    for index, target in enumerate(("SBP", "DBP")):
        got = contrast["ci_methods"][target]["subject_balanced_mae"]
        assert got["percentile"]["bounds"] == pytest.approx(
            contrast["ci"][target]["subject_balanced_mae"]["bounds"])
        d = np.array([np.abs(m[ids == s, index] - ref[ids == s, index]).mean()
                      - np.abs(r[ids == s, index] - ref[ids == s, index]).mean()
                      for s in np.unique(ids)])
        assert d.mean() == pytest.approx(contrast["point"][target]["subject_balanced_mae"])
        half = stats.t.ppf(0.975, len(d) - 1) * d.std(ddof=1) / np.sqrt(len(d))
        assert got["student_t"]["bounds"] == pytest.approx([d.mean() - half, d.mean() + half])
        low_b, high_b = got["bootstrap_t"]["bounds"]
        low_t, high_t = got["student_t"]["bounds"]
        assert got["t_envelope"]["bounds"] == pytest.approx(
            [min(low_b, low_t), max(high_b, high_t)])
        for method in ALL_METHODS:
            low, high = got[method]["bounds"]
            assert low < d.mean() < high and got[method]["status"] == "ok"
    # Same seed: the extra CIs do not change the draws of the existing ones.
    plain = bootstrap_bp(ref, {"M": m, "R": r}, ids, config, contrasts=[("M", "R")])
    assert plain["contrasts"][0]["ci"] == contrast["ci"]


@pytest.mark.parametrize("methods,contrasts", [
    (("unknown",), [("M", "R")]), (("student_t", "student_t"), [("M", "R")]),
    (("student_t",), None), ((1,), [("M", "R")])])
def test_bad_contrast_ci_methods_are_rejected(methods, contrasts):
    ref, models, ids = contrast_fixture()
    with pytest.raises(ValueError):
        bootstrap_bp(ref, models, ids, BootstrapConfig(repetitions=10),
                     contrasts=contrasts, contrast_ci_methods=methods)


def test_contrast_ci_methods_with_too_few_subjects_and_through_the_table():
    ref, models, ids = contrast_fixture()
    one = bootstrap_bp(ref[:1], {"M": models["M"][:1], "R": models["R"][:1]}, ["A"],
                       BootstrapConfig(repetitions=10), contrasts=[("M", "R")],
                       contrast_ci_methods=("student_t",))
    assert one["status"] == "insufficient_subjects"
    assert one["contrasts"][0]["ci_methods"] is None
    manifest, inventory, predictions = table_fixture()
    other = predictions.assign(model="B1", pred_sbp=125.0)
    result = evaluate_prediction_table(
        manifest, inventory, pd.concat([predictions, other]),
        config=BootstrapConfig(repetitions=20), contrasts=[("B1", "B0")],
        contrast_ci_methods=("t_envelope",))
    # Every subject has errors 5 (B1) and 2 (B0) on SBP: d_s = 3 for all.
    got = result["contrasts"][0]["ci_methods"]["SBP"]["subject_balanced_mae"]
    assert got["t_envelope"]["bounds"] == pytest.approx([3, 3])


@pytest.mark.parametrize("contrasts", [[("M", "M")], [("M", "X")], [("M",)],
                                       [("M", "R"), ("M", "R")], "M-R", [["M"]]])
def test_bad_contrasts_are_rejected(contrasts):
    ref, models, ids = contrast_fixture()
    with pytest.raises(ValueError):
        bootstrap_bp(ref, models, ids, BootstrapConfig(repetitions=10),
                     contrasts=contrasts)


@pytest.mark.parametrize("n,status", [(1, "insufficient_subjects"),
                                      (2, "few_subjects"), (9, "few_subjects"),
                                      (10, "ok")])
def test_status_flags_few_subjects(n, status):
    ids = [f"S{i}" for i in range(n)]
    ref = np.tile([120.0, 80.0], (n, 1))
    pred = ref + np.arange(n)[:, None]
    result = bootstrap_bp(ref, {"M": pred}, ids, BootstrapConfig(repetitions=20))
    assert result["status"] == status
    # The CI is computed from 2 subjects on, flagged or not.
    assert (result["models"]["M"]["ci"] is None) == (n < 2)
    with pytest.raises(ValueError):
        BootstrapConfig(min_subjects=5, few_subjects=4)


def test_test_split_is_refused():
    manifest, inventory, predictions = table_fixture()
    with pytest.raises(ValueError, match="val"):
        evaluate_prediction_table(manifest, inventory, predictions.assign(split="test"),
                                  split="test", config=BootstrapConfig(repetitions=10))


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