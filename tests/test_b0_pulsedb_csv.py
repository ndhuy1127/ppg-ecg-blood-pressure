"""Known-answer CSV integration and leakage checks using synthetic labels only."""

import argparse
import json
from pathlib import Path

import pytest

from scripts.run_b0_pulsedb_csv import apply_default_config, evaluate_manifest

HEADER = "sample_id,subject_id,source,split,sbp,dbp,sample_hash\n"
ROWS = [
    "0,SYN_TRAIN_A,synthetic,train,110,70,h0",
    "1,SYN_TRAIN_B,synthetic,train,130,90,h1",
    "2,SYN_VAL_A,synthetic,val,118,81,h2",
    "3,SYN_VAL_A,synthetic,val,122,79,h3",
    # Deliberately nonnumeric test labels: evaluation must leave them unused.
    "4,SYN_TEST_A,synthetic,test,UNUSED,UNUSED,h4",
]


def payload(rows=ROWS):
    return (HEADER + "\n".join(rows) + "\n").encode()


def test_csv_train_only_fit_and_known_validation_metrics():
    result = evaluate_manifest(payload())
    assert result["B0_constant"] == {"SBP": 120, "DBP": 80}
    assert result["split_counts"] == {"train": 2, "val": 2, "test": 1}
    assert result["subjects_per_split"] == {"train": 2, "val": 1, "test": 1}
    assert result["sample_weighted"]["SBP"]["mae"] == 2
    assert result["sample_weighted"]["SBP"]["bias"] == 0
    assert result["sample_weighted"]["SBP"]["sd"] == pytest.approx(8 ** 0.5)
    assert result["subject_balanced"]["DBP"]["mae"] == 1
    assert "by_subject" not in result  # No individual IDs in saved report.
    assert len(result["manifest_sha256"]) == 64


def test_changing_validation_labels_changes_metrics_not_constant():
    changed = ROWS.copy()
    changed[2] = changed[2].replace(",118,81,", ",148,101,")
    before, after = evaluate_manifest(payload()), evaluate_manifest(payload(changed))
    assert before["B0_constant"] == after["B0_constant"]
    assert before["sample_weighted"] != after["sample_weighted"]


@pytest.mark.parametrize("index", [2, 4])
def test_subject_overlap_with_validation_or_test_is_rejected(index):
    changed = ROWS.copy()
    changed[index] = changed[index].replace(
        "SYN_VAL_A" if index == 2 else "SYN_TEST_A", "SYN_TRAIN_A"
    )
    with pytest.raises(ValueError, match="Subject leakage"):
        evaluate_manifest(payload(changed))


def test_duplicate_sample_key_is_rejected():
    with pytest.raises(ValueError, match="Duplicate"):
        evaluate_manifest(payload(ROWS + [ROWS[0]]))


def test_cross_split_hash_is_rejected():
    changed = ROWS.copy()
    changed[2] = changed[2].replace("h2", "h0")
    with pytest.raises(ValueError, match="sample_hash"):
        evaluate_manifest(payload(changed))


@pytest.mark.parametrize("label", ["NaN", "inf", "", "text"])
def test_bad_validation_label_is_rejected(label):
    changed = ROWS.copy()
    changed[2] = changed[2].replace(",118,81,", f",{label},81,")
    with pytest.raises(ValueError):
        evaluate_manifest(payload(changed))


@pytest.mark.parametrize("missing_split", ["train", "val"])
def test_missing_required_split_is_rejected(missing_split):
    with pytest.raises(ValueError, match="Both train and val"):
        evaluate_manifest(payload([r for r in ROWS if f",{missing_split}," not in r]))


def test_missing_or_duplicate_header_is_rejected():
    with pytest.raises(ValueError, match="headers"):
        evaluate_manifest(b"sbp,dbp\n120,80\n")
    with pytest.raises(ValueError, match="headers"):
        evaluate_manifest(payload().replace(b"sample_hash\n", b"sample_hash,split\n"))


def test_no_csv_uses_recorded_config_relative_to_repo(monkeypatch):
    config = {
        "csv_path": "data/processed/synthetic.csv", "unit": "mmHg",
        "split_seed": 72, "manifest_ref": "SYN_REF", "manifest_sha256": "a" * 64,
    }
    monkeypatch.setattr(Path, "read_bytes", lambda _: json.dumps(config).encode())
    args = argparse.Namespace(
        csv_path=None, unit=None, split_seed=None, manifest_ref=None
    )
    repo = Path(__file__).resolve().parents[1]
    result = apply_default_config(args, repo)
    assert args.csv_path == repo / "data/processed/synthetic.csv"
    assert (args.unit, args.split_seed, args.manifest_ref) == ("mmHg", 72, "SYN_REF")
    assert result["expected_manifest_sha256"] == "a" * 64


def test_explicit_csv_does_not_inherit_default_seed_or_ref():
    args = argparse.Namespace(
        csv_path=Path("different.csv"), unit="mmHg", split_seed=None, manifest_ref=None
    )
    assert apply_default_config(args, Path.cwd()) is None
    assert args.split_seed is None and args.manifest_ref is None


def test_explicit_csv_still_requires_confirmed_units():
    args = argparse.Namespace(csv_path=Path("different.csv"), unit=None)
    with pytest.raises(ValueError, match="requires --unit"):
        apply_default_config(args, Path.cwd())
