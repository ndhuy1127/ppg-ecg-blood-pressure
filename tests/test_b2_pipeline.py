"""SYNTHETIC checks of B2 (demographics + HR) and its two panels.

Answers come from docs/protocol/b2_pulsedb_definition.md: five demographic
features (F = 0, M = 1, nothing imputed), an ECG peak-rate HR (derivative
energy, refractory 0.25 s, at least 4 peaks, [30, 220] bpm), panels ``full``
(B0, B2a, B3 on every QC row) and ``hr_available`` (B0, B2a, B2b, B3 refitted on
the rows with a HR), val only. They verify code, not BP or HR accuracy.
"""

import dataclasses
import json
import math
from pathlib import Path

import numpy as np
import pytest

from software.data_io.split_manifest import build_inventory, make_manifest
from software.pulsedb import features, features_b2, pipeline_b2
from software.pulsedb.pipeline_b2 import APPROVED, featurize, load_config, run_b2
from software.pulsedb.reader import PulseSegment

REPO = Path(__file__).resolve().parents[1]
CONFIG_PATH = REPO / "configs/models/b2_pulsedb_v0.json"
FS = 125.0
T = np.arange(1250) / FS


def ecg(rate_bpm, t_wave=False, phase_s=0.3):
    """Narrow R spikes at ``rate_bpm``; optional broad T wave 0.28 s after R."""
    return ecg_at(np.arange(phase_s, 10, 60 / rate_bpm), t_wave)


def ecg_at(r_times, t_wave=False):
    """Narrow R spikes at the given times (s)."""
    values = np.zeros_like(T)
    for r in r_times:
        values += np.exp(-0.5 * ((T - r) / 0.008) ** 2)
        if t_wave:
            values += 0.35 * np.exp(-0.5 * ((T - r - 0.28) / 0.04) ** 2)
    return values


def segment(subject, sbp, rate, age=40.0, sex="F", flat=False):
    return PulseSegment(
        subject_id=f"SYN_{subject:02d}", gender=sex, age=age, height_cm=165.0,
        weight_kg=60.0 + subject, bmi_kg_m2=(60.0 + subject) / 1.65 ** 2,
        sbp=sbp, dbp=0.6 * sbp, ecg=np.zeros_like(T) if flat else ecg(rate),
        ppg=np.sin(2 * np.pi * rate / 60 * T), abp=np.full(T.size, sbp),
    )


def make_data(n_subjects=24, per_subject=3):
    segments = []
    for subject in range(n_subjects):
        for k in range(per_subject):
            # Weight encodes SBP; the first segment of every third subject has a
            # flat ECG (no HR); subject 5 has no HR at all.
            segments.append(segment(subject, 100.0 + 2 * subject + k, 60 + subject,
                                    age=8.0 if subject % 4 == 0 else 40.0,
                                    sex="M" if subject % 2 else "F",
                                    flat=subject == 5 or (subject % 3 == 0 and k == 0)))
    inventory = build_inventory(segments, "SYN_SOURCE.mat", "0" * 64)
    return segments, make_manifest(inventory, seed=72), inventory


def small_config():
    config = load_config(CONFIG_PATH.read_bytes())
    config["bootstrap"]["repetitions"] = 20
    return config


# --- HR -----------------------------------------------------------------------

@pytest.mark.parametrize("rate", [45, 72, 150, 180])
def test_hr_is_the_median_r_r_rate_including_fast_child_rates(rate):
    assert features_b2.hr_bpm(ecg(rate)) == pytest.approx(rate, rel=0.02)


def test_hr_is_the_median_not_the_mean_of_irregular_r_r():
    # Two missed beats (1.6 s gaps) among 0.8 s intervals: the median gives
    # 75 bpm, the mean about 61 bpm.
    gaps = [0.8, 0.8, 1.6, 0.8, 0.8, 0.8, 1.6, 0.8, 0.8]
    r_times = 0.3 + np.concatenate([[0.0], np.cumsum(gaps)])
    assert 60 / np.mean(gaps) < 62
    assert features_b2.hr_bpm(ecg_at(r_times)) == pytest.approx(75, rel=0.02)


def test_hr_ignores_a_t_wave_that_prominence_would_count():
    # Section 3: at 0.25 s prominence takes the T wave too and doubles the rate.
    assert features_b2.hr_bpm(ecg(60, t_wave=True)) == pytest.approx(60, rel=0.02)


def test_hr_is_missing_when_not_measurable():
    assert features_b2.hr_bpm(np.zeros(1250)) is None  # flat
    assert features_b2.hr_bpm(ecg(20)) is None  # 3 to 4 beats, 20 bpm < 30
    few = np.zeros_like(T)
    few[[200, 400, 600]] = 1.0
    assert features_b2.hr_bpm(few) is None  # 3 peaks


def test_hr_config_is_the_frozen_definition():
    c = features_b2.HR_CONFIG
    assert (c.r_method, c.refractory_s, c.r_energy_window_s, c.r_energy_threshold,
            c.prominence_fraction, c.filter_mode, c.edge_s) == (
        "derivative_energy", 0.25, 0.1, "quantile", 0.2, "none", 0.1)
    assert (features_b2.HR_MIN_PEAKS, features_b2.HR_RANGE_BPM) == (4, (30.0, 220.0))


# --- demographics -------------------------------------------------------------

def test_demographics_encode_sex_and_refuse_anything_missing():
    assert features_b2.demographics(segment(1, 100, 60, sex="M")) == (
        40.0, 1.0, 165.0, 61.0, pytest.approx(61 / 1.65 ** 2))
    assert features_b2.demographics(segment(1, 100, 60, sex="F"))[1] == 0.0
    for change in ({"gender": "Unknown"}, {"age": math.nan}, {"height_cm": True}):
        bad = segment(1, 100, 60).__class__(**{**segment(1, 100, 60).__dict__, **change})
        with pytest.raises(ValueError):
            features_b2.demographics(bad)


def test_demographics_must_be_constant_within_a_subject():
    features_b2.check_constant_by_subject(["a", "a", "b"], [(1,), (1,), (2,)])
    with pytest.raises(ValueError, match="differ"):
        features_b2.check_constant_by_subject(["a", "a"], [(1,), (2,)])


# --- pipeline -----------------------------------------------------------------

def test_config_keeps_the_b3_v1_learner_and_rejects_other_fields():
    config = load_config(CONFIG_PATH.read_bytes())
    b3 = json.loads((REPO / "configs/models/b3_pulsedb_v1.json").read_bytes())
    assert config["xgboost"] == b3["b3"] and config["bootstrap"] == b3["bootstrap"]
    for field, value in (("evaluation_split", "test"), ("extra", 1),
                         ("train_weighting", "equal_rows")):
        payload = {**config, field: value}
        with pytest.raises(ValueError):
            load_config(json.dumps(payload).encode())


@pytest.mark.parametrize("status", ["", None, "APPROVED", "approved_not_test_evaluated",
                                    "APPROVED_SYNTHETIC_TEST"])
def test_config_accepts_only_the_two_documented_statuses(status):
    config = load_config(CONFIG_PATH.read_bytes())
    assert load_config(json.dumps({**config, "status": APPROVED}).encode())
    with pytest.raises(ValueError, match="status"):
        load_config(json.dumps({**config, "status": status}).encode())


def test_config_pins_the_split_of_the_b3_v1_run():
    config = load_config(CONFIG_PATH.read_bytes())
    report = json.loads(
        (REPO / "reports/weekly/week_05/pulsedb_b3_v1/split_report.json").read_bytes())
    assert config["split_sha256"] == {
        "raw": report["raw_sha256"], "inventory": report["inventory_sha256"],
        "manifest": report["manifest_sha256"], "config": report["config_sha256"]}
    for pins in ({**config["split_sha256"], "raw": "A" * 64},
                 {k: v for k, v in config["split_sha256"].items() if k != "config"},
                 "0" * 64):
        with pytest.raises(ValueError, match="split_sha256"):
            load_config(json.dumps({**config, "split_sha256": pins}).encode())


def test_two_panels_score_their_own_rows_and_never_featurize_test():
    segments, manifest, inventory = make_data()
    test_rows = set(manifest[manifest.split == "test"].raw_index)

    # verify_inputs iterates every row, test included, to rebuild the inventory
    # hashes (as B3 does); featurize indexes rows one by one, so an index of a
    # test row here would be a test segment turned into features.
    class Guard(list):
        def __getitem__(self, index):
            assert index not in test_rows, "a test segment was featurized"
            return list.__getitem__(self, index)

    result = run_b2(Guard(segments), manifest, inventory, small_config())
    full, hr = result["panels"]["full"], result["panels"]["hr_available"]
    assert set(full["predictions"].model) == {"B0", "B2a", "B3"}
    assert set(hr["predictions"].model) == {"B0", "B2a", "B2b", "B3"}
    val = manifest[manifest.split == "val"]
    flat = {i for i, s in enumerate(segments) if not s.ecg.any()}
    assert set(full["predictions"].sample_id) == set(val.sample_id)
    assert set(hr["predictions"].sample_id) == set(
        val[~val.raw_index.isin(flat)].sample_id)
    # Train rows of the HR panel lose the flat ECGs too (B0 refitted on them).
    train = manifest[(manifest.split == "train")]
    assert hr["counts"]["train"]["segments"] == int((~train.raw_index.isin(flat)).sum())
    assert hr["counts"]["test"] == full["counts"]["test"]
    coverage = result["hr_coverage"]
    assert coverage["train"]["all"]["rows_with_hr"] == hr["counts"]["train"]["segments"]
    lost = {"SYN_05"} & set(train.subject_id)
    assert coverage["train"]["all"]["subjects_lost"] == len(lost)
    assert coverage["train"]["age_lt_18"]["rows"] + coverage["train"]["age_ge_18"]["rows"] \
        == coverage["train"]["all"]["rows"]
    names = [c["model"] + "-" + c["reference"] for c in hr["evaluation"]["contrasts"]]
    assert names == ["B2b-B0", "B3-B2b", "B2b-B2a"]
    mask = result["hr_mask"]
    assert set(mask.split) == {"train", "val"} and len(mask) == int(
        manifest.split.isin(("train", "val")).sum())
    assert sorted(mask.sample_id[~mask.has_hr]) == result["rows_without_hr"]


def test_each_learner_gets_its_panel_rows_columns_and_subject_weights(monkeypatch):
    calls = []

    class SpyXGB(pipeline_b2.XGBoostBaseline):
        def fit(self, train_features, train_labels, sample_weight=None):
            calls.append((np.asarray(train_features), np.asarray(train_labels),
                          np.asarray(sample_weight)))
            return super().fit(train_features, train_labels, sample_weight=sample_weight)

    class SpyB0(pipeline_b2.PopulationMeanBaseline):
        def fit(self, train_labels, sample_weight=None):
            calls.append((None, np.asarray(train_labels), np.asarray(sample_weight)))
            return super().fit(train_labels, sample_weight=sample_weight)

    monkeypatch.setattr(pipeline_b2, "XGBoostBaseline", SpyXGB)
    monkeypatch.setattr(pipeline_b2, "PopulationMeanBaseline", SpyB0)
    segments, manifest, inventory = make_data()
    run_b2(segments, manifest, inventory, small_config())

    train = manifest[manifest.split == "train"].sort_values("raw_index")
    hr_rows = [i for i in train.raw_index if segments[i].ecg.any()]
    panels = {"full": list(train.raw_index), "hr_available": hr_rows}
    expected = []
    for name, models in (("full", ("B0", "B2a", "B3")),
                         ("hr_available", ("B0", "B2a", "B2b", "B3"))):
        rows = panels[name]
        ids = [segments[i].subject_id for i in rows]
        weights = np.array([1 / ids.count(s) for s in ids])
        weights *= len(ids) / weights.sum()
        labels = np.array([[segments[i].sbp, segments[i].dbp] for i in rows])
        demo = np.array([features_b2.demographics(segments[i]) for i in rows])
        x = {"B0": None, "B2a": demo,
             "B2b": None if name == "full" else np.column_stack(
                 [demo, [features_b2.hr_bpm(segments[i].ecg) for i in rows]]),
             "B3": np.array([[features.extract_features(segments[i].ecg, segments[i].ppg)[f]
                              for f in features.FEATURE_NAMES] for i in rows])}
        expected += [(x[model], labels, weights) for model in models]
    assert len(calls) == len(expected) == 7
    for (x, labels, weights), (want_x, want_labels, want_weights) in zip(calls, expected):
        assert (x is None) == (want_x is None)
        if x is not None:
            np.testing.assert_allclose(x, want_x)
        np.testing.assert_allclose(labels, want_labels)
        np.testing.assert_allclose(weights, want_weights)
    # The HR panel drops rows, so its weights differ from 1 for some subjects.
    assert not np.allclose(expected[3][2], 1.0)


def test_featurize_reads_no_label_abp_or_subject():
    class OnlyInputs:
        def __init__(self, s):
            self.ecg, self.ppg, self.gender, self.age = s.ecg, s.ppg, s.gender, s.age
            self.height_cm, self.weight_kg, self.bmi_kg_m2 = (
                s.height_cm, s.weight_kg, s.bmi_kg_m2)

        def __getattr__(self, name):
            raise AssertionError(f"B2 features read {name}")

    out = featurize([OnlyInputs(segment(1, 100, 72))], [0])
    assert out[0][2] == pytest.approx(72, rel=0.02)


def test_val_and_test_labels_and_test_ecg_do_not_change_predictions():
    segments, manifest, inventory = make_data()
    before = run_b2(segments, manifest, inventory, small_config())
    changed = list(segments)
    for index, split in zip(manifest.raw_index, manifest.split):
        if split != "train":
            update = {"sbp": 190.0, "dbp": 110.0}
            if split == "test":  # a test ECG with no HR must not move anything
                update["ecg"] = np.zeros_like(T)
            changed[index] = dataclasses.replace(changed[index], **update)
    inventory2 = build_inventory(changed, "SYN_SOURCE.mat", "0" * 64)
    manifest2 = make_manifest(inventory2, seed=72)
    assert manifest2.split.tolist() == manifest.split.tolist()
    after = run_b2(changed, manifest2, inventory2, small_config())
    for panel in before["panels"]:
        assert before["panels"][panel]["predictions"].equals(
            after["panels"][panel]["predictions"])
        assert before["panels"][panel]["evaluation"] != after["panels"][panel][
            "evaluation"]  # val labels still matter


# --- runner -------------------------------------------------------------------

def pool_rows(n_subjects=30, per_subject=3):
    rows = []
    for subject in range(n_subjects):
        for k in range(per_subject):
            s = segment(subject, 100.0 + 2 * subject + k, 60 + subject,
                        sex="M" if subject % 2 else "F", flat=subject % 3 == 0 and k == 0)
            wave = (np.sin(2 * np.pi * 3 * T) + 1) / 2
            rows.append(dataclasses.replace(s, abp=s.dbp + (s.sbp - s.dbp) * wave))
    return rows


def approved_config(tmp_path, split_dir=None, **pins):
    """The approved config, pinned to the split in ``split_dir`` (or to the B3 v1
    split of the repo config when None); ``pins`` overrides single hashes."""
    config = small_config()
    config["status"] = APPROVED
    if split_dir is not None:
        report = json.loads((split_dir / "report.json").read_bytes())
        config["split_sha256"] = {
            "raw": report["raw_sha256"], "inventory": report["inventory_sha256"],
            "manifest": report["manifest_sha256"], "config": report["config_sha256"]}
    config["split_sha256"].update(pins)
    path = tmp_path / "b2.json"
    path.write_text(json.dumps(config), encoding="utf-8")
    return path


def built_split(tmp_path):
    from scripts.build_pulsedb_split import run as build_split
    from tests.pulsedb_h5_fixture import subsample_split_config

    split_config, raw = subsample_split_config(tmp_path, rows=pool_rows(), n_subjects=24)
    build_split(split_config, tmp_path / "split")
    return raw, tmp_path / "split"


def committed(monkeypatch, definition=True):
    """Stand in for Git: SYNTHETIC configs live outside the repository, so the
    approval commit is simulated here; the runner has no bypass of its own."""
    import scripts.run_b2_pulsedb as runner

    def fake(repo, path):
        return definition or not str(path).endswith("b2_pulsedb_definition.md")

    monkeypatch.setattr(runner, "committed_unchanged", fake)


def test_runner_refuses_until_the_definition_is_approved(tmp_path):
    from scripts.run_b2_pulsedb import run
    with pytest.raises(ValueError, match="not approved"):
        run(tmp_path / "none.mat", tmp_path / "none", CONFIG_PATH, tmp_path / "out", REPO)
    assert not (tmp_path / "out").exists()


def test_runner_refuses_an_approved_config_that_is_not_committed(tmp_path):
    # Section 8: the approval is a commit. A config outside the repository (or
    # changed since HEAD) is refused before any file is read.
    from scripts.run_b2_pulsedb import run
    with pytest.raises(ValueError, match="committed"):
        run(tmp_path / "none.mat", tmp_path / "none", approved_config(tmp_path),
            tmp_path / "out", REPO)
    assert not (tmp_path / "out").exists()


def test_runner_refuses_when_only_the_definition_is_not_committed(tmp_path, monkeypatch):
    from scripts.run_b2_pulsedb import run
    committed(monkeypatch, definition=False)
    with pytest.raises(ValueError, match="committed.*'definition': False"):
        run(tmp_path / "none.mat", tmp_path / "none", approved_config(tmp_path),
            tmp_path / "out", REPO)
    assert not (tmp_path / "out").exists()


def git_repo(path):
    """A temporary Git repository with a.json, sub/c.json and s[1].json committed."""
    import subprocess

    def git(*args):
        subprocess.run(["git", "-c", "user.name=SYN", "-c", "user.email=syn@example.org",
                        *args], cwd=path, check=True, capture_output=True)

    git("init", "-q")
    (path / "sub").mkdir()
    for name in ("a.json", "sub/c.json", "s[1].json"):
        (path / name).write_text("{}\n", encoding="utf-8")
    git("add", "a.json", "sub/c.json", "s[1].json")
    git("commit", "-q", "-m", "SYN")
    return git


def test_committed_unchanged_needs_a_tracked_file_equal_to_head(tmp_path):
    from scripts.run_b2_pulsedb import committed_unchanged

    git = git_repo(tmp_path)
    assert committed_unchanged(tmp_path, tmp_path / "a.json")
    assert committed_unchanged(tmp_path, tmp_path / "sub" / "c.json")
    assert committed_unchanged(tmp_path, tmp_path / "s[1].json")  # literal, not a glob
    (tmp_path / "b.json").write_text("{}\n", encoding="utf-8")
    assert not committed_unchanged(tmp_path, tmp_path / "b.json")  # untracked
    (tmp_path / "s1.json").write_text("{}\n", encoding="utf-8")
    assert not committed_unchanged(tmp_path, tmp_path / "s1.json")  # untracked
    (tmp_path / "a.json").write_text('{"status": 1}\n', encoding="utf-8")
    assert not committed_unchanged(tmp_path, tmp_path / "a.json")  # changed
    git("add", "a.json")
    assert not committed_unchanged(tmp_path, tmp_path / "a.json")  # staged only
    assert not committed_unchanged(tmp_path, tmp_path.parent / "elsewhere.json")
    assert not committed_unchanged(tmp_path, tmp_path)


def test_committed_unchanged_refuses_symlinks(tmp_path):
    # An untracked link to a clean tracked file must not pass for that file.
    import os

    from scripts.run_b2_pulsedb import committed_unchanged

    git_repo(tmp_path)
    try:
        os.symlink(tmp_path / "sub" / "c.json", tmp_path / "link.json")
        os.symlink(tmp_path / "sub", tmp_path / "linkdir", target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("creating symlinks needs a privilege here (Windows)")
    assert not committed_unchanged(tmp_path, tmp_path / "link.json")
    assert not committed_unchanged(tmp_path, tmp_path / "linkdir" / "c.json")


def test_runner_refuses_a_split_other_than_the_pinned_one(tmp_path, monkeypatch):
    import software.pulsedb.h5_reader as h5_reader
    from scripts.run_b2_pulsedb import run

    class NoRead:
        def __init__(self, *args, **kwargs):
            raise AssertionError("a segment reader was opened before the pin check")

    committed(monkeypatch)
    raw, split_dir = built_split(tmp_path)  # building the split reads the file
    config = approved_config(tmp_path, split_dir, manifest="0" * 64)
    monkeypatch.setattr(h5_reader, "PulseDBH5Reader", NoRead)
    with pytest.raises(ValueError, match=r"pinned.*\['manifest'\]"):
        run(raw, split_dir, config, tmp_path / "out", REPO)
    assert not (tmp_path / "out").exists()


def test_runner_end_to_end_writes_both_panels_and_the_hr_mask_without_ids(
    tmp_path, monkeypatch
):
    import hashlib

    from scripts.run_b2_pulsedb import run
    from software.data_io.split_manifest import read_manifest_bytes

    committed(monkeypatch)
    raw, split_dir = built_split(tmp_path)
    config = approved_config(tmp_path, split_dir)
    report, table = run(raw, split_dir, config, tmp_path / "out", REPO)
    assert set(report["panels"]) == {"full", "hr_available"}
    assert report["approval_committed"] == {"config": True, "definition": True}
    assert report["hr_mask"]["rows_without_hr"] > 0
    assert "B2b@hr_available" in table and "B2a@full" in table
    saved = (tmp_path / "out" / "report.json").read_text(encoding="utf-8")
    assert "SYN_" not in saved and "SYN_" not in table
    mask_path = tmp_path / "out" / "hr_mask.csv"
    mask_text = mask_path.read_text(encoding="utf-8")
    assert mask_text.splitlines()[0] == "sample_id,split,has_hr" and "SYN_" not in mask_text
    # Every train/val row of the split with the HR status its ECG gives, no other row.
    rows = pool_rows()
    manifest = read_manifest_bytes((split_dir / "manifest.csv").read_bytes())
    labelled = manifest[manifest.split.isin(("train", "val"))]
    expected = {(sample_id, split, str(features_b2.hr_bpm(rows[index].ecg) is not None))
                for sample_id, split, index in zip(labelled.sample_id, labelled.split,
                                                   labelled.raw_index)}
    written = [tuple(line.split(",")) for line in mask_text.splitlines()[1:]]
    assert len(written) == len(expected) and set(written) == expected
    assert sum(has == "False" for _, _, has in written) == report["hr_mask"][
        "rows_without_hr"]
    assert report["outputs_sha256"]["hr_mask.csv"] == hashlib.sha256(
        mask_path.read_bytes()).hexdigest()
    with pytest.raises(FileExistsError):
        run(raw, split_dir, config, tmp_path / "out", REPO)
