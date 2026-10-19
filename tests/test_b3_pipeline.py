"""SYNTHETIC checks for Linh's B0/B3 pipeline: features, leakage, train-only fit."""

import dataclasses
import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pytest

from scripts.run_b3_pulsedb import run
from software.data_io.split_manifest import (
    build_inventory, file_sha256, make_manifest, manifest_bytes,
)
from software.models.xgboost_baseline import XGBoostBaseline
from software.pulsedb import features
from software.pulsedb.pipeline import (
    baseline_table, load_config, run_baselines, verify_inputs,
)
from software.pulsedb.reader import PulseDBReader, PulseSegment

REPO = Path(__file__).resolve().parents[1]
CONFIG_PATH = REPO / "configs/models/b3_pulsedb_v0.json"
SOURCE_SHA = "0" * 64


def make_segments(n_subjects=20, per_subject=3, seed=0):
    """PPG amplitude encodes SBP, so B3 can learn what constant B0 cannot."""
    rng = np.random.default_rng(seed)
    t = np.arange(250) / 125
    segments = []
    for subject in range(n_subjects):
        for k in range(per_subject):
            sbp = 100.0 + 3 * subject + k
            dbp = 0.6 * sbp
            wave = np.sin(2 * np.pi * 1.2 * t)
            segments.append(PulseSegment(
                subject_id=f"SYN_{subject:02d}", gender="Unknown", age=math.nan,
                height_cm=math.nan, weight_kg=math.nan, bmi_kg_m2=math.nan,
                sbp=sbp, dbp=dbp,
                ecg=np.sin(2 * np.pi * 1.2 * t + subject) + rng.normal(0, 0.01, t.size),
                ppg=sbp / 100 * wave + rng.normal(0, 0.01, t.size),
                abp=dbp + (sbp - dbp) * (wave + 1) / 2,
            ))
    return segments


def make_split(segments, sha=SOURCE_SHA):
    inventory = build_inventory(segments, "SYN_SOURCE.mat", sha)
    return make_manifest(inventory, seed=72), inventory


def small_config(repetitions=20):
    config = load_config(CONFIG_PATH.read_bytes())
    config["bootstrap"]["repetitions"] = repetitions
    return config


# --- features -----------------------------------------------------------------

def test_features_known_answer():
    values = features.extract_features([1, -1, 1, -1], [0, 2])
    assert list(values) == list(features.FEATURE_NAMES)
    assert values["ecg_mean"] == 0 and values["ecg_std"] == 1
    assert values["ecg_range"] == 2 and values["ecg_rms"] == 1
    assert values["ppg_min"] == 0 and values["ppg_max"] == 2
    assert values["ppg_rms"] == pytest.approx(math.sqrt(2))


@pytest.mark.parametrize("bad", [[], [np.nan, 1.0], [[1.0, 2.0]], [True, False], ["1"]])
def test_features_reject_invalid_signal(bad):
    with pytest.raises(ValueError):
        features.extract_features(bad, [1.0, 2.0])


def test_feature_matrix_reads_only_ecg_and_ppg():
    class OnlyWaveforms:
        def __init__(self, segment):
            self.ecg, self.ppg = segment.ecg, segment.ppg

        def __getattr__(self, name):
            raise AssertionError(f"feature code read {name}")

    segments = make_segments(n_subjects=2, per_subject=1)
    values = features.feature_matrix([OnlyWaveforms(s) for s in segments])
    assert values.shape == (2, len(features.FEATURE_NAMES))
    forbidden = ("abp", "sbp", "dbp", "subject", "hash")
    assert not any(word in name for name in features.FEATURE_NAMES for word in forbidden)


# --- B3 model -------------------------------------------------------------------

def test_b3_is_deterministic_and_predicts_pairs():
    rng = np.random.default_rng(1)
    x = rng.normal(size=(40, 3))
    y = np.column_stack([120 + 10 * x[:, 0], 80 + 5 * x[:, 1]])
    first = XGBoostBaseline(seed=7).fit(x, y).predict(x[:5])
    second = XGBoostBaseline(seed=7).fit(x, y).predict(x[:5])
    assert first.shape == (5, 2)
    np.testing.assert_array_equal(first, second)


@pytest.mark.parametrize("kwargs", [
    {"seed": True}, {"seed": -1}, {"seed": 1, "params": {"random_state": 3}},
    {"seed": 1, "params": {"n_jobs": -1}},
])
def test_b3_rejects_unrecorded_or_nondeterministic_settings(kwargs):
    with pytest.raises(ValueError):
        XGBoostBaseline(**kwargs)


def test_b3_requires_fit_finite_features_and_no_overwrite(tmp_path):
    model = XGBoostBaseline(seed=1)
    with pytest.raises(RuntimeError):
        model.predict([[1.0]])
    with pytest.raises(ValueError, match="finite"):
        model.fit([[np.nan], [1.0]], [[120, 80], [121, 81]])
    model.fit([[0.0], [1.0]], [[120, 80], [121, 81]])
    model.save(tmp_path)
    with pytest.raises(FileExistsError):
        model.save(tmp_path)


# --- pipeline ---------------------------------------------------------------------

def test_config_rejects_test_evaluation_and_unknown_fields():
    config = json.loads(CONFIG_PATH.read_bytes())
    for change in ({"evaluation_split": "test"}, {"fit_split": "val"}, {"extra": 1}):
        with pytest.raises(ValueError):
            load_config(json.dumps({**config, **change}).encode())


def test_pipeline_scores_b0_and_b3_on_same_val_rows():
    segments = make_segments()
    manifest, inventory = make_split(segments)
    result = run_baselines(segments, manifest, inventory, small_config())
    val_ids = set(manifest[manifest.split == "val"].sample_id)
    table = result["predictions"]
    assert set(table.model) == {"B0", "B3"}
    for _, group in table.groupby("model"):
        assert set(group.sample_id) == val_ids
    assert result["counts"]["val"]["segments"] == len(val_ids)
    models = result["evaluation"]["models"]
    assert (models["B3"]["point"]["SBP"]["subject_balanced_mae"]
            < models["B0"]["point"]["SBP"]["subject_balanced_mae"])
    markdown = baseline_table(result["evaluation"], result["counts"])
    assert "SYN_" not in markdown and markdown.count("| B3 |") == 2


def test_val_and_test_labels_and_test_waveforms_do_not_change_predictions():
    segments = make_segments()
    manifest, inventory = make_split(segments)
    before = run_baselines(segments, manifest, inventory, small_config())
    held_out = manifest[manifest.split != "train"]
    changed = list(segments)
    for index, split in zip(held_out.raw_index, held_out.split):
        update = {"sbp": 200.0, "dbp": 120.0}
        if split == "test":
            update["ppg"] = changed[index].ppg * 5
        changed[index] = dataclasses.replace(changed[index], **update)
    new_manifest, new_inventory = make_split(changed)
    assert new_manifest.split.tolist() == manifest.split.tolist()
    after = run_baselines(changed, new_manifest, new_inventory, small_config())
    assert before["predictions"].equals(after["predictions"])
    assert before["b0_constant"] == after["b0_constant"]
    assert before["evaluation"] != after["evaluation"]  # Val labels still matter.


def test_rejects_subject_leakage_altered_hash_and_missing_row():
    segments = make_segments()
    manifest, inventory = make_split(segments)
    val_row = manifest.index[manifest.split == "val"][0]
    leaked = manifest.copy()
    leaked.loc[val_row, "split"] = "train"
    altered = manifest.copy()
    altered.loc[val_row, "sample_hash"] = "f" * 64
    for bad in (leaked, altered, manifest.drop(index=val_row)):
        with pytest.raises(ValueError):
            verify_inputs(bad, inventory, segments)


def test_rejects_raw_segments_that_differ_from_inventory():
    segments = make_segments()
    manifest, inventory = make_split(segments)
    changed = list(segments)
    changed[0] = dataclasses.replace(changed[0], ecg=changed[0].ecg + 1)
    with pytest.raises(ValueError, match="do not reproduce"):
        verify_inputs(manifest, inventory, changed)


# --- runner -----------------------------------------------------------------------

def write_inputs(tmp_path, monkeypatch):
    raw = tmp_path / "SYN_raw.mat"
    raw.write_bytes(b"SYNTHETIC placeholder; reader is monkeypatched")
    segments = make_segments()
    manifest, inventory = make_split(segments, file_sha256(raw))
    monkeypatch.setattr(PulseDBReader, "read", lambda self, limit=None: segments)
    split_dir = tmp_path / "split"
    split_dir.mkdir()
    payloads = {"inventory.csv": manifest_bytes(inventory),
                "manifest.csv": manifest_bytes(manifest)}
    for name, payload in payloads.items():
        (split_dir / name).write_bytes(payload)
    (split_dir / "report.json").write_text(json.dumps({
        "schema_version": "pulsedb-split-v2", "raw_sha256": file_sha256(raw),
        "inventory_sha256": hashlib.sha256(payloads["inventory.csv"]).hexdigest(),
        "manifest_sha256": hashlib.sha256(payloads["manifest.csv"]).hexdigest(),
    }))
    config = tmp_path / "config.json"
    config.write_text(json.dumps(small_config()))
    return raw, split_dir, config


def test_runner_writes_traceable_outputs_reproducibly(tmp_path, monkeypatch):
    raw, split_dir, config = write_inputs(tmp_path, monkeypatch)
    first, table = run(raw, split_dir, config, tmp_path / "out1", REPO)
    second, _ = run(raw, split_dir, config, tmp_path / "out2", REPO)
    assert first["evaluation"] == second["evaluation"]
    names = ("predictions_val.csv", "xgboost_sbp.json", "xgboost_dbp.json")
    for name in names:
        assert (tmp_path / "out1" / name).read_bytes() == (
            tmp_path / "out2" / name).read_bytes()
    saved = (tmp_path / "out1" / "report.json").read_text(encoding="utf-8")
    assert "SYN_" not in saved and "SYN_" not in table
    assert json.loads(saved)["inputs_sha256"]["raw"] == file_sha256(raw)
    with pytest.raises(FileExistsError):
        run(raw, split_dir, config, tmp_path / "out1", REPO)


def test_runner_rejects_raw_that_differs_from_split_report(tmp_path, monkeypatch):
    raw, split_dir, config = write_inputs(tmp_path, monkeypatch)
    raw.write_bytes(b"different raw bytes")
    with pytest.raises(ValueError, match="raw_sha256"):
        run(raw, split_dir, config, tmp_path / "out", REPO)
    assert not (tmp_path / "out").exists()
