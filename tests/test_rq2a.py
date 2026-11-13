"""RQ2a: window split (A) versus subject split (B), on SYNTHETIC data only."""

import hashlib
import json
from pathlib import Path

import numpy as np
import pytest

from software.evaluation.subject_bootstrap import BootstrapConfig
from software.pulsedb import rq2a

REPO = Path(__file__).resolve().parents[1]
B3 = {"seed": 42, "params": {
    "n_estimators": 60, "max_depth": 4, "learning_rate": 0.1,
    "objective": "reg:squarederror", "tree_method": "hist", "n_jobs": 1}}
CONFIG = {
    "schema_version": rq2a.VERSION, "status": "PROPOSED_NOT_RUN", "unit": "mmHg",
    "pool_splits": ["train", "val"],
    "split_sha256": {name: "0" * 64 for name in rq2a.SPLIT_PINS},
    "baseline_config": "x", "baseline_config_sha256": "0" * 64,
    "design": {"seeds": [1, 2, 3, 4], "eval_subject_fraction": 0.3,
               "eval_window_fraction": 0.25},
    "bootstrap": {"seed": 7, "repetitions": 300, "confidence": 0.95,
                  "min_subjects": 2},
}


def synthetic(person_effect, n_subjects=30, n_windows=40, seed=0):
    """BP = base + noise (+ per-subject offset); one feature identifies the subject."""
    rng = np.random.default_rng(seed)
    ids, feats, labels = [], [], []
    for s in range(n_subjects):
        offset = rng.normal(0, 10) if person_effect else 0.0
        mark = rng.normal(0, 5) if person_effect else 0.0
        for _ in range(n_windows):
            ids.append(f"SYN_{s:03d}")
            feats.append([mark + rng.normal(0, 0.1), rng.normal(), rng.normal()])
            labels.append([120 + offset + rng.normal(0, 3),
                           75 + offset / 2 + rng.normal(0, 2)])
    ids = np.array(ids)
    samples = np.array([f"SYN_ROW_{i}" for i in range(len(ids))])
    splits = np.where(np.arange(len(ids)) % 10 == 0, "val", "train")
    return np.array(feats), np.array(labels), ids, samples, splits


def draw(seed=3, **overrides):
    _, _, ids, samples, splits = synthetic(True)
    args = {"eval_subject_fraction": 0.3, "eval_window_fraction": 0.25, "seed": seed}
    return ids, make(ids, samples, splits, {**args, **overrides})


def make(ids, samples, splits, args):
    return rq2a.make_designs(ids, samples, splits, **args)


def delta(result, target, model="B3"):
    return result["summary"][model][target]["delta_mae_b_minus_a"]


def test_designs_have_equal_size_and_disjoint_eval():
    ids, d = draw()
    assert len(d["train_A"]) == len(d["train_B"])
    assert not np.intersect1d(d["eval"], d["train_A"]).size
    assert not np.intersect1d(d["eval"], d["train_B"]).size
    assert len(d["eval"]) > 0


def test_subject_split_b_shares_no_subject_but_window_split_a_does():
    ids, d = draw()
    eval_subjects = set(ids[d["eval"]])
    assert eval_subjects == set(d["eval_subjects"])
    assert not eval_subjects & set(ids[d["train_B"]])
    assert eval_subjects & set(ids[d["train_A"]])


def test_designs_are_deterministic_by_seed():
    _, a = draw(seed=5)
    _, b = draw(seed=5)
    _, c = draw(seed=6)
    for key in ("eval", "train_A", "train_B"):
        assert np.array_equal(a[key], b[key])
    assert not np.array_equal(a["eval"], c["eval"])


def test_test_rows_and_duplicate_ids_are_rejected():
    _, _, ids, samples, splits = synthetic(True)
    bad = splits.copy()
    bad[0] = "test"
    args = {"eval_subject_fraction": 0.3, "eval_window_fraction": 0.25, "seed": 1}
    with pytest.raises(ValueError, match="train and val"):
        make(ids, samples, bad, args)
    dup = samples.copy()
    dup[1] = dup[0]
    with pytest.raises(ValueError, match="unique"):
        make(ids, dup, splits, args)


def test_person_specific_signal_makes_window_split_look_better():
    f, y, ids, samples, splits = synthetic(True)
    result = rq2a.run_rq2a(f, y, ids, samples, splits, CONFIG, B3)
    for target in ("SBP", "DBP"):
        row = result["summary"]["B3"][target]
        assert delta(result, target)["point"] > 0
        assert delta(result, target)["ci"][0] > 0
        # Every reported metric of RQ section 5.D is there, per design.
        for metric in ("rmse", "me", "sd"):
            assert set(row[metric]) == set(rq2a.DESIGNS)
        for design in rq2a.DESIGNS:
            low, high = row["mae"][design]["ci"]
            assert low <= row["mae"][design]["point"] <= high
        assert row["relative_degradation_pct"]["point"] == pytest.approx(
            100 * delta(result, target)["point"] / row["mae"]["A_window"]["point"])
        assert delta(result, target)["between_replicate_se"] > 0
        assert result["summary"]["B0"][target]["delta_mae_b_minus_a"]["ci"]
    assert all(r["n_eval_subjects"] == 9 for r in result["replicates"])


def test_no_person_specific_signal_gives_delta_near_zero():
    f, y, ids, samples, splits = synthetic(False, seed=0)
    result = rq2a.run_rq2a(f, y, ids, samples, splits, CONFIG, B3)
    for target in ("SBP", "DBP"):
        low, high = delta(result, target)["ci"]
        assert low <= 0 <= high
        assert abs(delta(result, target)["point"]) < 0.2


def test_run_is_deterministic():
    f, y, ids, samples, splits = synthetic(True, n_subjects=12, n_windows=20)
    a = rq2a.run_rq2a(f, y, ids, samples, splits, CONFIG, B3)
    b = rq2a.run_rq2a(f, y, ids, samples, splits, CONFIG, B3)
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


def test_fit_predict_refuses_overlap():
    f, y, ids, _, _ = synthetic(True, n_subjects=6, n_windows=10)
    with pytest.raises(ValueError, match="training set"):
        rq2a.fit_predict(f, y, ids, np.arange(20), np.arange(10, 30), B3)


def test_weights_are_recomputed_on_each_training_set(monkeypatch):
    # Unequal windows per subject, so weights over the pool and over a training
    # set differ.
    f, y, ids, samples, splits = synthetic(True, n_subjects=10, n_windows=12)
    keep = np.array([i % 12 < 4 + int(ids[i][-1]) % 6 for i in range(len(ids))])
    f, y, ids, samples, splits = (a[keep] for a in (f, y, ids, samples, splits))
    calls, fits = [], []
    real_weights = rq2a.subject_weights
    real_fit = rq2a.XGBoostBaseline.fit

    def spy_weights(train_ids):
        calls.append(np.asarray(train_ids))
        return real_weights(train_ids)

    def spy_fit(self, x, labels, sample_weight=None):
        fits.append(np.asarray(sample_weight))
        return real_fit(self, x, labels, sample_weight=sample_weight)

    monkeypatch.setattr(rq2a, "subject_weights", spy_weights)
    monkeypatch.setattr(rq2a.XGBoostBaseline, "fit", spy_fit)
    config = {**CONFIG, "design": {**CONFIG["design"], "seeds": [3]}}
    rq2a.run_rq2a(f, y, ids, samples, splits, config, B3)
    d = make(ids, samples, splits, {"eval_subject_fraction": 0.3,
                                    "eval_window_fraction": 0.25, "seed": 3})
    assert len(calls) == len(fits) == 2
    for train_ids, weights, key in zip(calls, fits, ("train_A", "train_B")):
        assert np.array_equal(train_ids, ids[d[key]])
        assert weights.mean() == pytest.approx(1.0)
        totals = [weights[train_ids == s].sum() for s in np.unique(train_ids)]
        assert max(totals) == pytest.approx(min(totals))


def test_mae_is_subject_balanced_and_the_bootstrap_is_paired(monkeypatch):
    """Known errors: subject s has |error| = 1 + s on every window in A and
    exactly 0.5 more in B. Evaluated subjects have different window counts, so
    a window-pooled MAE would differ from the mean of MAE_s. B - A is 0.5 for
    every pair, so a paired bootstrap gives a zero-width CI at 0.5."""
    f, y, ids, samples, splits = synthetic(False, n_subjects=12, n_windows=14)
    keep = np.array([i % 14 < 2 + int(ids[i][-2:]) for i in range(len(ids))])
    f, y, ids, samples, splits = (a[keep] for a in (f, y, ids, samples, splits))
    level = np.array([1.0 + int(s[-2:]) for s in ids])
    calls = []

    def fake(features, labels, subject_ids, train_idx, eval_idx, b3):
        extra = 0.5 * (len(calls) % 2)  # A first, then B, in every replicate
        calls.append(1)
        error = (level[eval_idx] + extra)[:, None]
        return {"B0": labels[eval_idx] + error, "B3": labels[eval_idx] - error}

    monkeypatch.setattr(rq2a, "fit_predict", fake)
    design = {"seeds": [1, 2], "eval_subject_fraction": 0.3, "eval_window_fraction": 0.5}
    result = rq2a.run_rq2a(f, y, ids, samples, splits, {**CONFIG, "design": design}, B3)
    expected = []
    for seed in (1, 2):
        d = make(ids, samples, splits, {"eval_subject_fraction": 0.3,
                                        "eval_window_fraction": 0.5, "seed": seed})
        expected += [1.0 + int(s[-2:]) for s in d["eval_subjects"]]
        pooled = level[d["eval"]].mean()
        balanced = np.mean([1.0 + int(s[-2:]) for s in d["eval_subjects"]])
        assert pooled != pytest.approx(balanced)
    row = result["summary"]["B3"]["SBP"]
    assert row["mae"]["A_window"]["point"] == pytest.approx(np.mean(expected))
    assert row["mae"]["B_subject"]["point"] == pytest.approx(np.mean(expected) + 0.5)
    assert row["delta_mae_b_minus_a"]["ci"] == pytest.approx([0.5, 0.5])
    low, high = row["mae"]["A_window"]["ci"]
    assert high - low > 1  # the MAEs themselves vary between subjects
    assert row["me"]["A_window"] < 0 and result["summary"]["B0"]["SBP"]["me"][
        "A_window"] > 0


def test_summarize_pairs_point_values():
    pairs = np.array(["SYN_A", "SYN_B", "SYN_A", "SYN_C"])
    values = {(m, d, t): np.array([1.0, 2.0, 3.0, 4.0]) + (d == "B_subject")
              for m in rq2a.MODELS for d in rq2a.DESIGNS for t in rq2a.TARGETS}
    out = rq2a.summarize_pairs(pairs, values, BootstrapConfig(seed=1, repetitions=200))
    assert out["B3"]["SBP"]["mae"]["A_window"]["point"] == pytest.approx(2.5)
    assert out["B3"]["SBP"]["relative_degradation_pct"]["point"] == pytest.approx(40.0)


def test_shipped_config_loads_and_pins_the_split():
    payload = (REPO / "configs/models/rq2a_pulsedb_v0.json").read_bytes()
    config = rq2a.load_config(payload)
    assert config["pool_splits"] == ["train", "val"]
    assert config["status"] == "PROPOSED_NOT_RUN"
    # Same split as B5 (the B3 v1 split v2 run01).
    b5 = json.loads((REPO / "configs/models/b5_pulsedb_v0.json").read_bytes())
    assert config["split_sha256"] == b5["split_sha256"]
    bad = json.loads(payload)
    bad["pool_splits"] = ["train", "val", "test"]
    with pytest.raises(ValueError, match="test"):
        rq2a.load_config(json.dumps(bad).encode())
    bad = json.loads(payload)
    del bad["split_sha256"]["raw"]
    with pytest.raises(ValueError, match="split_sha256"):
        rq2a.load_config(json.dumps(bad).encode())


# --- runner -------------------------------------------------------------------------

def committed(monkeypatch, ok=lambda path: True):
    """Stand in for Git: SYNTHETIC configs live outside the repository, so the
    approval commit is simulated; the runner has no bypass of its own."""
    import scripts.run_b2_pulsedb as b2

    monkeypatch.setattr(b2, "committed_unchanged", lambda repo, path: ok(Path(path)))


def approved_copy(tmp_path, **changes):
    payload = json.loads((REPO / "configs/models/rq2a_pulsedb_v0.json").read_bytes())
    payload.update(status="APPROVED_NOT_RUN", **changes)
    path = tmp_path / "approved.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_script_refuses_overwrite_and_unapproved_config(tmp_path):
    from scripts.run_rq2a_pulsedb import run
    config = REPO / "configs/models/rq2a_pulsedb_v0.json"
    existing = tmp_path / "out"
    existing.mkdir()
    with pytest.raises(FileExistsError):
        run(tmp_path / "x.mat", tmp_path, config, existing, REPO)
    payload = json.loads(config.read_text(encoding="utf-8"))
    payload["status"] = "PROPOSED_NOT_RUN"
    proposed = tmp_path / "proposed.json"
    proposed.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="status"):
        run(tmp_path / "x.mat", tmp_path, proposed, tmp_path / "new", REPO)
    assert not (tmp_path / "new").exists()


def test_script_checks_git_on_the_config_actually_passed(tmp_path):
    # An approved copy outside the repository is never the committed config,
    # whatever the state of configs/models/rq2a_pulsedb_v0.json.
    from scripts.run_rq2a_pulsedb import run
    with pytest.raises(ValueError, match="'config'"):
        run(tmp_path / "x.mat", tmp_path, approved_copy(tmp_path), tmp_path / "new",
            REPO)
    assert not (tmp_path / "new").exists()


def test_script_refuses_a_changed_code_file(tmp_path, monkeypatch):
    from scripts.run_rq2a_pulsedb import run
    committed(monkeypatch, lambda path: path.name != "rq2a.py")
    with pytest.raises(ValueError, match="software/pulsedb/rq2a.py"):
        run(tmp_path / "x.mat", tmp_path, approved_copy(tmp_path), tmp_path / "new",
            REPO)
    assert not (tmp_path / "new").exists()


def built_split(tmp_path):
    from scripts.build_pulsedb_split import run as build_split
    from tests.pulsedb_h5_fixture import subsample_split_config, synthetic_rows

    rows = synthetic_rows(n_subjects=24, per_subject=6)
    split_config, raw = subsample_split_config(tmp_path, rows=rows, n_subjects=20)
    build_split(split_config, tmp_path / "split")
    report = json.loads((tmp_path / "split" / "report.json").read_text(encoding="utf-8"))
    pins = {name: report[f"{name}_sha256"] for name in rq2a.SPLIT_PINS}
    return raw, tmp_path / "split", pins


def test_runner_runs_end_to_end_on_a_small_synthetic_raw_file(tmp_path, monkeypatch):
    from scripts.run_rq2a_pulsedb import run
    raw, split_dir, pins = built_split(tmp_path)
    committed(monkeypatch)
    design = {"seeds": [1, 2], "eval_subject_fraction": 0.2, "eval_window_fraction": 0.4}
    config = approved_copy(tmp_path, split_sha256=pins, design=design,
                           bootstrap={"seed": 3, "repetitions": 50, "confidence": 0.95,
                                      "min_subjects": 2})
    report, table = run(raw, split_dir, config, tmp_path / "out", REPO)
    assert set(report["approval_committed"].values()) == {True}
    assert "workspace_has_changes" in report["code_provenance"]
    assert report["inputs_sha256"]["raw"] == pins["raw"]
    saved = (tmp_path / "out" / "report.json").read_text(encoding="utf-8")
    assert "SYN_" not in saved and "SYN_" not in table
    digest = hashlib.sha256((tmp_path / "out" / "rq2a_table.md").read_bytes()).hexdigest()
    assert json.loads(saved)["outputs_sha256"]["rq2a_table.md"] == digest
    assert "A = random by window" in table and "Delta B - A" in table
    # The pool is train + val of the split: 18 of the 20 sampled subjects.
    assert report["result"]["n_pool_subjects"] == 18
    with pytest.raises(FileExistsError):
        run(raw, split_dir, config, tmp_path / "out", REPO)


def test_runner_refuses_a_split_other_than_the_pinned_one(tmp_path, monkeypatch):
    from scripts.run_rq2a_pulsedb import run
    raw, split_dir, pins = built_split(tmp_path)
    committed(monkeypatch)
    config = approved_copy(tmp_path, split_sha256={**pins, "manifest": "e" * 64})
    with pytest.raises(ValueError, match="manifest"):
        run(raw, split_dir, config, tmp_path / "out", REPO)
    assert not (tmp_path / "out").exists()
