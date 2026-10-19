"""Synthetic-only regression tests for Linh's inventory-backed split."""

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from scripts.build_pulsedb_split import run
from software.data_io.split_manifest import (
    VERSION, build_inventory, file_sha256, make_manifest, manifest_bytes,
    read_manifest_bytes, sample_hash, summarize_manifest, validate_manifest, waveform_hash,
)


def segments():
    return [SimpleNamespace(
        subject_id=f"SYN_{i // 2}", sbp=120.0, dbp=80.0,
        ecg=np.array([i, i + 1.0]), ppg=np.array([i + 2.0, i + 3.0]),
        abp=np.array([i + 4.0, i + 5.0]),
    ) for i in range(20)]


@pytest.fixture
def inventory():
    return build_inventory(segments(), "SYNTHETIC", "a" * 64)


def test_seed_order_hash_and_statistics(inventory):
    first = make_manifest(inventory)
    second = make_manifest(inventory.iloc[::-1])
    assert manifest_bytes(first) == manifest_bytes(second)
    assert validate_manifest(first, inventory)
    summary = summarize_manifest(first, inventory)
    assert [summary[s]["subjects"] for s in ("train", "val", "test")] == [8, 1, 1]
    assert [summary[s]["segments"] for s in ("train", "val", "test")] == [16, 2, 2]
    assert summary["train"]["bp"]["sbp"]["mean"] == 120
    restored = read_manifest_bytes(manifest_bytes(first))
    assert validate_manifest(restored, inventory)


@pytest.mark.parametrize("case", [
    "missing", "added", "duplicate", "raw_duplicate", "subject_leak",
    "hash_leak", "altered_label", "empty_id", "missing_split", "bad_hash",
])
def test_validator_rejects_real_errors(inventory, case):
    bad = make_manifest(inventory)
    if case == "missing":
        bad = bad.iloc[:-1].copy()
    elif case == "added":
        extra = bad.iloc[[0]].assign(
            sample_id="new", raw_index=999, sample_hash="b" * 64,
        )
        bad = pd.concat([bad, extra], ignore_index=True)
    elif case == "duplicate":
        bad = pd.concat([bad, bad.iloc[[0]]], ignore_index=True)
    elif case == "raw_duplicate":
        bad.loc[1, "raw_index"] = bad.loc[0, "raw_index"]
    elif case == "subject_leak":
        bad.loc[0, "split"] = "test" if bad.loc[0, "split"] != "test" else "train"
    elif case == "hash_leak":
        # Inventory itself contains a shared hash across distinct subjects.
        other = bad.index[bad.split != bad.loc[0, "split"]][0]
        raw_index = int(bad.loc[other, "raw_index"])
        inventory.loc[raw_index, "sample_hash"] = bad.loc[0, "sample_hash"]
        bad.loc[other, "sample_hash"] = bad.loc[0, "sample_hash"]
    elif case == "altered_label":
        bad.loc[0, "sbp"] += 1
    elif case == "empty_id":
        bad.loc[0, "subject_id"] = " "
    elif case == "missing_split":
        bad.loc[0, "split"] = None
    else:
        bad.loc[0, "sample_hash"] = "not-a-hash"
    with pytest.raises(ValueError):
        validate_manifest(bad, inventory)


def test_record_leakage_is_rejected(inventory):
    inventory["record_id"] = "shared_record"
    with pytest.raises(ValueError, match="record_id"):
        make_manifest(inventory)


def test_same_labels_and_same_content_in_same_split_not_dropped():
    data = segments()
    data[1] = data[0]
    inv = build_inventory(data, "SYNTHETIC", "a" * 64)
    result = make_manifest(inv)
    assert len(result) == 20
    assert result.sample_hash.nunique() == 19
    assert validate_manifest(result, inv)


@pytest.mark.parametrize("subject", ["", " ", None, "nan", "unknown"])
def test_missing_subject_never_invented(subject):
    data = segments()
    data[0].subject_id = subject
    with pytest.raises(ValueError, match="subject_id"):
        build_inventory(data, "SYNTHETIC", "a" * 64)


def test_hash_canonical_dtype_byteorder_and_content():
    s = segments()[0]
    h = sample_hash(s)
    for channel in ("ecg", "ppg", "abp"):
        setattr(s, channel, getattr(s, channel).astype(">f4"))
    assert sample_hash(s) == h
    s.ecg[0] += 1
    assert sample_hash(s) != h


@pytest.mark.parametrize("ratios", [
    (1, 0, 0), (0.5, 0.5, 0.5), (float('nan'), .1, .1), None, "bad",
])
def test_bad_ratios_rejected(inventory, ratios):
    with pytest.raises(ValueError):
        make_manifest(inventory, ratios=ratios)


def test_too_few_subjects_rejected(inventory):
    with pytest.raises(ValueError, match="Too few"):
        make_manifest(inventory.iloc[:4])


def test_runner_reproducible_checksum_and_no_overwrite(tmp_path, monkeypatch):
    raw = tmp_path / "synthetic.mat"
    raw.write_bytes(b"SYNTHETIC reader input; no real waveform")
    config = {
        "schema_version": VERSION, "input_path": raw.name,
        "input_sha256": file_sha256(raw), "source": "SYNTHETIC",
        "source_version": "synthetic-v1", "license": "synthetic-test",
        "permission_basis": "synthetic-only", "pool_decision": "all synthetic rows",
        "subject_identity_review": "known synthetic IDs", "unit": "mmHg",
        "seed": 72, "ratios": [0.8, 0.1, 0.1],
    }
    path = tmp_path / "config.json"
    path.write_text(json.dumps(config), encoding="utf-8")
    # Exercise the actual repository reader; mock only the external MAT loader.
    data = segments()
    fake_mat = {
        "Signals": np.stack([np.stack([s.ecg, s.ppg, s.abp]) for s in data]),
        "Subject": np.array([s.subject_id for s in data]),
        "SBP": np.array([s.sbp for s in data]),
        "DBP": np.array([s.dbp for s in data]),
        "Age": np.full(len(data), 30.0), "Gender": np.full(len(data), "M"),
    }
    monkeypatch.setattr("software.pulsedb.reader.mat73.loadmat", lambda _: fake_mat)
    first, second = tmp_path / "first", tmp_path / "second"
    report = run(path, first)
    again = run(path, second)
    assert report["manifest_sha256"] == again["manifest_sha256"]
    assert report["manifest_sha256"] == hashlib.sha256(
        (first / "manifest.csv").read_bytes()
    ).hexdigest()
    assert report["excluded_segments"] == 0
    for name in ("inventory.csv", "manifest.csv", "config.json"):
        assert (first / name).read_bytes() == (second / name).read_bytes()
    with pytest.raises(FileExistsError):
        run(path, first)
    raw.write_bytes(b"changed")
    with pytest.raises(ValueError, match="SHA256 mismatch"):
        run(path, tmp_path / "bad")
    assert not (tmp_path / "bad").exists()


def test_multisource_pool_is_not_assumed_independent(inventory):
    inventory.loc[0, "source"] = "OTHER_SOURCE"
    with pytest.raises(ValueError, match="identity mapping"):
        make_manifest(inventory)


def test_csv_round_trip_preserves_fractional_labels(inventory):
    inventory["sbp"] = np.linspace(100.1234567890123, 150.9876543210987, 20)
    manifest = make_manifest(inventory)
    restored = read_manifest_bytes(manifest_bytes(manifest))
    assert validate_manifest(restored, inventory)


def test_cli_runs_directly_from_other_directory(tmp_path):
    script = Path(__file__).resolve().parents[1] / "scripts/build_pulsedb_split.py"
    result = subprocess.run(
        [sys.executable, "-B", str(script), "--help"], cwd=tmp_path,
        capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0
    assert "--config" in result.stdout and "--output" in result.stdout


def test_cli_invalid_config_returns_failure_without_output(tmp_path):
    path = tmp_path / "invalid.json"
    path.write_text("{}", encoding="utf-8")
    output = tmp_path / "output"
    script = Path(__file__).resolve().parents[1] / "scripts/build_pulsedb_split.py"
    result = subprocess.run(
        [sys.executable, "-B", str(script), "--config", str(path), "--output", str(output)],
        cwd=tmp_path, capture_output=True, text=True, check=False,
    )
    assert result.returncode == 1
    assert "Config must contain" in result.stderr
    assert not output.exists()


@pytest.mark.parametrize("change_labels", [False, True])
def test_identical_waveforms_different_subjects_rejected(change_labels):
    data = segments()
    baseline = make_manifest(build_inventory(data, "SYNTHETIC", "a" * 64))
    other = int(baseline.index[baseline.split != baseline.loc[0, "split"]][0])
    for channel in ("ecg", "ppg", "abp"):
        setattr(data[other], channel, getattr(data[0], channel).copy())
    if change_labels:
        data[other].sbp += 10
        data[other].dbp += 5
    assert data[other].subject_id != data[0].subject_id
    assert sample_hash(data[other]) != sample_hash(data[0])
    assert waveform_hash(data[other]) == waveform_hash(data[0])
    inv = build_inventory(data, "SYNTHETIC", "a" * 64)
    with pytest.raises(ValueError, match="waveform_hash"):
        make_manifest(inv)


def test_waveform_hash_ignores_metadata_and_canonicalizes_dtype():
    s = segments()[0]
    original = waveform_hash(s)
    s.subject_id = "OTHER_SYN"
    s.sbp = 140
    s.dbp = 90
    for channel in ("ecg", "ppg", "abp"):
        setattr(s, channel, getattr(s, channel).astype(">f4"))
    assert waveform_hash(s) == original
    s.ppg[0] += 1
    assert waveform_hash(s) != original


def test_trace_metadata_survives_csv_round_trip(inventory):
    inventory["record_id"] = inventory.subject_id.map(lambda s: "RECORD_" + s)
    inventory["window_id"] = inventory.raw_index.map(lambda i: f"WINDOW_{i}")
    manifest = make_manifest(inventory)
    # Even reordered input columns serialize in the same canonical order.
    payload = manifest_bytes(manifest)
    assert payload == manifest_bytes(manifest[manifest.columns[::-1]])
    restored = read_manifest_bytes(payload)
    assert restored.record_id.tolist() == manifest.record_id.tolist()
    assert restored.window_id.tolist() == manifest.window_id.tolist()
    assert validate_manifest(restored, inventory)


def test_unknown_metadata_is_rejected_not_silently_discarded(inventory):
    inventory["unreviewed_metadata"] = "SYN_VALUE"
    with pytest.raises(ValueError, match="Unsupported metadata"):
        make_manifest(inventory)
    with pytest.raises(ValueError, match="Unsupported metadata"):
        manifest_bytes(inventory)


def test_shared_window_across_splits_rejected(inventory):
    inventory["window_id"] = "SYN_SHARED_WINDOW"
    with pytest.raises(ValueError, match="window_id"):
        make_manifest(inventory)


@pytest.mark.parametrize("token", ["0001", "NA", "N/A", "NULL"])
def test_reader_preserves_text_identifiers(inventory, token):
    inventory["record_id"] = inventory.subject_id.map(lambda s: token + s)
    inventory["window_id"] = token
    # Preserve tokens in all identity columns, not just the optional columns.
    inventory["subject_id"] = inventory.subject_id.map(lambda s: s.replace("SYN_", "00"))
    inventory["source"] = token
    inventory["sample_id"] = [f"{i:04d}" for i in range(len(inventory))]
    manifest = make_manifest(inventory)
    restored = read_manifest_bytes(manifest_bytes(manifest))
    assert validate_manifest(restored, inventory)
    assert restored.window_id.tolist() == [token] * len(inventory)
    assert restored.sample_id.tolist() == manifest.sample_id.tolist()
    assert manifest_bytes(restored) == manifest_bytes(manifest)


@pytest.mark.parametrize("split", ["INVALID", "", None])
def test_serializer_rejects_invalid_split(inventory, split):
    manifest = make_manifest(inventory)
    manifest.loc[0, "split"] = split
    with pytest.raises(ValueError, match="split"):
        manifest_bytes(manifest)


@pytest.mark.parametrize("value,dtype", [
    (2 ** 53 + 1, "int64"), (-(2 ** 53 + 1), "int64"),
    (2 ** 64 - 1, "uint64"),
])
def test_hash_rejects_inexact_integer_waveforms(value, dtype):
    s = segments()[0]
    s.ecg = np.array([value, value], dtype=dtype)
    for hash_function in (sample_hash, waveform_hash):
        with pytest.raises(ValueError, match="represented exactly"):
            hash_function(s)


def test_hash_accepts_exact_integer_boundary():
    s = segments()[0]
    s.ecg = np.array([2 ** 53, 2 ** 53 + 2], dtype=np.int64)
    original = waveform_hash(s)
    s.ecg = s.ecg.astype(np.float64)
    assert waveform_hash(s) == original


@pytest.mark.parametrize("mutation", ["duplicate_header", "short_row", "extra_field", "bad_split"])
def test_reader_rejects_malformed_csv(inventory, mutation):
    payload = manifest_bytes(make_manifest(inventory))
    lines = payload.decode().splitlines()
    if mutation == "duplicate_header":
        lines[0] += ",sample_id"
    elif mutation == "short_row":
        lines[1] = lines[1].rsplit(",", 1)[0]
    elif mutation == "extra_field":
        lines[1] += ",extra"
    else:
        lines[1] = lines[1].rsplit(",", 1)[0] + ",INVALID"
    with pytest.raises(ValueError):
        read_manifest_bytes(("\n".join(lines) + "\n").encode())


def test_split_sizes_use_exact_decimal_floor():
    pool = [SimpleNamespace(subject_id=f"SYN_{i:03d}", sbp=120.0, dbp=80.0,
                            ecg=np.array([i, 1.0]), ppg=np.array([i, 2.0]),
                            abp=np.array([i, 3.0])) for i in range(90)]
    manifest = make_manifest(build_inventory(pool, "SYNTHETIC", "b" * 64),
                             ratios=(0.7, 0.2, 0.1))
    # float arithmetic gives int(90 * 0.7) == 62; the documented rule is 63.
    assert manifest.split.value_counts().to_dict() == {"train": 63, "val": 18, "test": 9}


def test_summary_omits_test_label_statistics(inventory):
    summary = summarize_manifest(make_manifest(inventory), inventory)
    assert summary["test"]["bp"] is None
    assert summary["test"]["segments"] == 2
    assert set(summary["val"]["bp"]) == {"sbp", "dbp"}
