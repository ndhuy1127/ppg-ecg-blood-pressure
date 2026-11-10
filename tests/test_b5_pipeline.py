"""SYNTHETIC checks of B5 (1D ResNet-18 of the PulseDB paper, ECG + PPG).

Answers come from docs/protocol/b5_pulsedb_definition.md: two input channels,
one model per target, the inner validation drawn by subject from train only,
scaling fitted on the fit rows only, waveforms read for train (``inner``) or
train and val (``val``) rows and never for test, B0/B3 refitted as in B3 v1,
contrasts B5 - B0 and B5 - B3, and no val run before an approved, committed
definition. They verify code, not BP accuracy. Skipped without PyTorch.
"""

import json
from pathlib import Path

import numpy as np
import pytest

torch = pytest.importorskip("torch")

from scripts.run_b5_pulsedb import run as run_b5_cli  # noqa: E402
from software.data_io.split_manifest import build_inventory, make_manifest  # noqa: E402
from software.models.resnet1d import ResNet18_1d, parameter_count  # noqa: E402
from software.pulsedb import pipeline, pipeline_b5  # noqa: E402
from software.pulsedb.pipeline_b5 import (  # noqa: E402
    APPROVED, PENDING, channel_scaling, inner_split, load_config, run_b5, waveforms,
)
from software.pulsedb.reader import PulseSegment  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
CONFIG_PATH = REPO / "configs/models/b5_pulsedb_v0.json"
T = np.arange(1250) / 125.0


def segment(subject, k):
    rate = 1.0 + 0.05 * subject
    sbp = 100.0 + 3 * subject + k
    return PulseSegment(
        subject_id=f"SYN_{subject:02d}", gender="F", age=40.0, height_cm=165.0,
        weight_kg=60.0, bmi_kg_m2=22.0, sbp=sbp, dbp=0.6 * sbp,
        ecg=np.sin(2 * np.pi * rate * T) + 0.01 * k,
        ppg=np.cos(2 * np.pi * rate * T) * (1 + 0.01 * subject), abp=np.full(T.size, sbp))


def make_data(n_subjects=20, per_subject=3):
    segments = [segment(s, k) for s in range(n_subjects) for k in range(per_subject)]
    inventory = build_inventory(segments, "SYN_SOURCE.mat", "0" * 64)
    return segments, make_manifest(inventory, seed=72), inventory


def small_config():
    config = load_config(CONFIG_PATH.read_bytes())
    config["training"].update(max_epochs=2, patience=1, batch_size=8, eval_batch_size=16,
                              learning_rate=1e-3)
    config["bootstrap"]["repetitions"] = 20
    return config


class Recorder:
    """Records which raw rows have their waveforms read."""

    def __init__(self, monkeypatch):
        self.rows = []
        real = pipeline_b5.waveforms

        def record(segments, raw_indices, samples):
            self.rows += list(raw_indices)
            return real(segments, raw_indices, samples)

        monkeypatch.setattr(pipeline_b5, "waveforms", record)


def raw_indices(manifest, split):
    return set(manifest[manifest.split == split].raw_index)


# --- config and helpers -------------------------------------------------------------

def test_committed_config_matches_the_definition():
    config = load_config(CONFIG_PATH.read_bytes())
    # Pending until the definition is approved by its own commit; either is valid.
    assert config["status"] in (PENDING, APPROVED)
    assert config["model"] == {"architecture": "resnet18-1d",
                               "input_channels": ["ecg", "ppg"], "samples": 1250,
                               "separate_targets": True}
    training = config["training"]
    assert (training["optimizer"], training["learning_rate"], training["max_epochs"]) == (
        "adam", 1e-6, 100)  # as in the PulseDB paper
    assert (training["inner_val_fraction"], training["batch_size"],
            training["patience"]) == (0.1, 64, 15)
    b2 = json.loads((REPO / "configs/models/b2_pulsedb_v1.json").read_bytes())
    assert config["split_sha256"] == b2["split_sha256"]  # the B3 v1 split
    assert config["xgboost"] == b2["xgboost"]


@pytest.mark.parametrize("change", [
    lambda c: c.update(extra=1),
    lambda c: c.update(status="APPROVED"),
    lambda c: c.update(evaluation_split="test"),
    lambda c: c["model"].update(architecture="resnet34-1d"),
    lambda c: c["training"].update(optimizer="sgd"),
    lambda c: c["training"].update(inner_val_fraction=0.6),
    lambda c: c["training"].update(batch_size=0),
    lambda c: c.update(label_qc="none"),
])
def test_config_changes_are_refused(change):
    config = json.loads(CONFIG_PATH.read_bytes())
    change(config)
    with pytest.raises(ValueError):
        load_config(json.dumps(config).encode())


def test_resnet18_1d_shape_and_size():
    model = ResNet18_1d(in_channels=2, outputs=1).eval()
    assert model(torch.zeros(3, 2, 1250)).shape == (3,)
    # torchvision resnet18 has 11 689 512 parameters with 3x3 kernels and 1000
    # outputs; in 1D the 3-tap kernels hold a third of the weights.
    assert parameter_count(model) == 3_844_865


def test_inner_split_is_by_subject_seeded_and_never_empty():
    ids = np.repeat([f"SYN_{i:02d}" for i in range(30)], 4)
    held = inner_split(ids, 0.1, 7)
    assert len(held) == 3 and held == inner_split(ids, 0.1, 7)
    assert held != inner_split(ids, 0.1, 8)
    assert len(inner_split(ids[:8], 0.1, 7)) == 1  # at least one of two subjects
    with pytest.raises(ValueError):
        inner_split(ids[:4], 0.1, 7)  # one subject


def test_waveforms_and_scaling_refuse_bad_input():
    segments = {0: segment(0, 0)}
    assert waveforms(segments, [0], 1250).shape == (1, 2, 1250)
    with pytest.raises(ValueError):
        waveforms(segments, [0], 1000)
    bad = segment(0, 0)
    bad.ppg[5] = np.nan
    with pytest.raises(ValueError):
        waveforms({0: bad}, [0], 1250)
    flat = np.zeros((4, 2, 10), dtype=np.float32)
    flat[:, 0] = np.arange(10)
    with pytest.raises(ValueError):
        channel_scaling(flat)


# --- leakage ------------------------------------------------------------------------

def test_inner_mode_reads_train_waveforms_only_and_scores_nothing(monkeypatch):
    segments, manifest, inventory = make_data()
    recorder = Recorder(monkeypatch)
    monkeypatch.setattr(pipeline, "run_baselines",
                        lambda *a, **k: pytest.fail("inner mode must not fit B0/B3"))
    result = run_b5(segments, manifest, inventory, small_config(), "cpu", "inner")
    assert set(recorder.rows) == raw_indices(manifest, "train")
    assert set(result) == {"report", "models"}
    report = result["report"]
    split = report["inner_split"]
    assert split["fit_subjects"] + split["inner_subjects"] == manifest[
        manifest.split == "train"].subject_id.nunique()
    for target in ("SBP", "DBP"):
        history = report["targets"][target]["history"]
        assert 1 <= len(history) <= 2 and report["targets"][target]["best_epoch"] >= 1


def test_val_mode_scores_b0_b3_b5_on_val_and_never_reads_test(monkeypatch):
    segments, manifest, inventory = make_data()
    recorder = Recorder(monkeypatch)
    config = small_config()
    result = run_b5(segments, manifest, inventory, config, "cpu", "val")
    assert set(recorder.rows) == raw_indices(manifest, "train") | raw_indices(
        manifest, "val")
    table = result["predictions"]
    assert set(table.model) == {"B0", "B3", "B5"} and set(table.split) == {"val"}
    assert set(table.sample_id) == set(manifest[manifest.split == "val"].sample_id)
    names = [(c["model"], c["reference"]) for c in result["evaluation"]["contrasts"]]
    assert names == [("B5", "B0"), ("B5", "B3")]
    # B0/B3 are exactly those of a B3 v1 run on the same inputs.
    alone = pipeline.run_baselines(segments, manifest, inventory,
                                   pipeline_b5.b3_config(config))["predictions"]
    for model in ("B0", "B3"):
        a = table[table.model == model].sort_values("sample_id")
        b = alone[alone.model == model].sort_values("sample_id")
        assert np.array_equal(a[["pred_sbp", "pred_dbp"]].to_numpy(),
                              b[["pred_sbp", "pred_dbp"]].to_numpy())


def test_val_mode_is_deterministic_on_cpu():
    segments, manifest, inventory = make_data()
    config = small_config()
    first = run_b5(segments, manifest, inventory, config, "cpu", "val")["predictions"]
    second = run_b5(segments, manifest, inventory, config, "cpu", "val")["predictions"]
    assert first.equals(second)


# --- runner gate --------------------------------------------------------------------

def test_runner_refuses_val_before_an_approved_committed_definition(tmp_path):
    pending_config = json.loads(CONFIG_PATH.read_bytes())
    pending_config["status"] = PENDING
    pending = tmp_path / "pending.json"
    pending.write_text(json.dumps(pending_config), encoding="utf-8")
    with pytest.raises(ValueError, match="not approved"):
        run_b5_cli(tmp_path / "none.mat", tmp_path, pending, tmp_path / "out", REPO, "val")
    approved = json.loads(CONFIG_PATH.read_bytes())
    approved["status"] = APPROVED
    path = tmp_path / "approved.json"
    path.write_text(json.dumps(approved), encoding="utf-8")
    with pytest.raises(ValueError, match="committed and unchanged"):
        run_b5_cli(tmp_path / "none.mat", tmp_path, path, tmp_path / "out", REPO, "val")
    assert not (tmp_path / "out").exists()
