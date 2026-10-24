"""Versioned, inventory-backed subject splits; no learned preprocessing."""

import csv
import hashlib
from fractions import Fraction
import io
import json
import math
import random
import re

import numpy as np
import pandas as pd

VERSION = "pulsedb-split-v2"
SPLITS = ("train", "val", "test")
COLUMNS = (
    "sample_id", "subject_id", "source", "source_sha256", "raw_index",
    "sample_hash", "waveform_hash", "sbp", "dbp",
)
OPTIONAL_COLUMNS = ("record_id", "window_id")
# Subject IDs that mean "missing"; also used by software/pulsedb/validator.py.
MISSING_SUBJECT_TOKENS = frozenset({"nan", "none", "null", "unknown"})
# Splits whose BP labels may be summarised; test labels stay unread.
LABEL_SUMMARY_SPLITS = ("train", "val")


def canonical_json(value):
    return json.dumps(
        value, sort_keys=True, ensure_ascii=False, allow_nan=False,
        separators=(",", ":"),
    ).encode("utf-8")


def file_sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _text(value, field):
    if not isinstance(value, str) or not value or value.strip() != value:
        raise ValueError(f"{field} must be nonempty text without edge spaces")
    if field == "subject_id" and value.lower() in MISSING_SUBJECT_TOKENS:
        raise ValueError("subject_id is missing")
    return value


def _checksum(value):
    if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{64}", value) is None:
        raise ValueError("Expected lowercase SHA256")
    return value


def sample_hash(segment):
    """Hash labels/identity and finite waveforms in fixed little-endian float64.

    Optional demographic metadata is deliberately not invented or hashed.
    Source/raw row identity is stored separately from content identity.
    """
    metadata = {
        "version": VERSION, "subject_id": _text(segment.subject_id, "subject_id"),
        "sbp": float(segment.sbp), "dbp": float(segment.dbp),
    }
    if not all(math.isfinite(metadata[k]) for k in ("sbp", "dbp")):
        raise ValueError("BP must be finite")
    h = hashlib.sha256(canonical_json(metadata))
    return _hash_waveforms(segment, h)


def waveform_hash(segment):
    """Content fingerprint independent of subject IDs, BP labels and source.

    An exact match across splits requires review, not automatic deletion or
    merging of subjects. This cannot detect partial overlaps/near duplicates.
    """
    h = hashlib.sha256(canonical_json({"version": VERSION, "kind": "waveform"}))
    return _hash_waveforms(segment, h)


def predictor_hash(segment):
    """ECG + PPG fingerprint: what a model sees, without ABP, labels or IDs.

    ``waveform_hash`` includes ABP, so two rows with identical ECG/PPG but a
    different ABP are not matched by it. Not stored in the split-v2 manifest;
    the split builder uses it to refuse identical predictors across splits.
    """
    h = hashlib.sha256(canonical_json({"version": VERSION, "kind": "predictors"}))
    return _hash_waveforms(segment, h, ("ecg", "ppg"))


def predictor_overlap(manifest, segments):
    """Counts of identical ECG/PPG (``predictor_hash``) within and across splits.

    ``segments`` is indexed by ``raw_index``. Returns ``{"across_splits": n,
    "within_split": n}``: groups of identical predictors spanning more than one
    split, and extra copies inside one split.
    """
    groups = {}
    for raw_index, split in zip(manifest.raw_index, manifest.split):
        key = predictor_hash(segments[int(raw_index)])
        groups.setdefault(key, []).append(split)
    across = sum(len(set(splits)) > 1 for splits in groups.values())
    within = sum(len(splits) - len(set(splits)) for splits in groups.values())
    return {"across_splits": across, "within_split": within}


def _hash_waveforms(segment, h, channels=("ecg", "ppg", "abp")):
    lengths = []
    for channel in channels:
        values = np.asarray(getattr(segment, channel))
        if values.dtype.kind not in "iuf" or values.ndim != 1 or not values.size:
            raise ValueError("Waveforms must be nonempty numeric vectors")
        if values.dtype.kind in "iu" and (
            int(values.min()) < -(2 ** 53) or int(values.max()) > 2 ** 53
        ) and any(int(value) != int(float(value)) for value in values):
            raise ValueError("Integer waveform cannot be represented exactly in float64")
        values = np.array(values, dtype="<f8", order="C", copy=True)
        if not np.isfinite(values).all():
            raise ValueError("Waveforms must be finite")
        values[values == 0] = 0  # Normalize negative zero.
        h.update(canonical_json({"channel": channel, "shape": list(values.shape)}))
        h.update(values.tobytes(order="C"))
        lengths.append(values.size)
    if len(set(lengths)) != 1:
        raise ValueError("Channel lengths must agree")
    return h.hexdigest()


def build_inventory(segments, source, source_sha256, record_ids=None):
    """Keep every reader row. raw_index is zero-based, not a session/record ID."""
    _text(source, "source")
    _checksum(source_sha256)
    if record_ids is not None and len(record_ids) != len(segments):
        raise ValueError("record_ids must cover every raw row")
    rows = []
    for index, segment in enumerate(segments):
        row = {
            "sample_id": f"{source_sha256}:{index}",
            "subject_id": _text(segment.subject_id, "subject_id"),
            "source": source, "source_sha256": source_sha256,
            "raw_index": index, "sample_hash": sample_hash(segment),
            "waveform_hash": waveform_hash(segment),
            "sbp": float(segment.sbp), "dbp": float(segment.dbp),
        }
        if record_ids is not None:
            row["record_id"] = _text(record_ids[index], "record_id")
        rows.append(row)
    inventory = pd.DataFrame(rows)
    _check_rows(inventory)
    return inventory


def _check_rows(frame):
    if not isinstance(frame, pd.DataFrame) or frame.empty:
        raise ValueError("Inventory/manifest must be nonempty")
    if not frame.columns.is_unique or not set(COLUMNS).issubset(frame.columns):
        raise ValueError("Missing or duplicate manifest columns")
    if set(frame.columns) - set(COLUMNS) - set(OPTIONAL_COLUMNS) - {"split"}:
        raise ValueError("Unsupported metadata columns; extend versioned schema first")
    for field in ("sample_id", "subject_id", "source"):
        for value in frame[field]:
            _text(value, field)
    for field in ("source_sha256", "sample_hash", "waveform_hash"):
        for value in frame[field]:
            _checksum(value)
    for value in frame.raw_index:
        if isinstance(value, (bool, np.bool_)) or not isinstance(
            value, (int, np.integer)
        ) or value < 0:
            raise ValueError("raw_index must be a nonnegative integer")
    if frame.sample_id.duplicated().any() or frame.duplicated(
        ["source_sha256", "raw_index"]
    ).any():
        raise ValueError("Duplicate sample/raw row")
    for field in ("sbp", "dbp"):
        if frame[field].dtype.kind not in "iuf" or not np.isfinite(
            frame[field].to_numpy()
        ).all():
            raise ValueError("BP must be numeric and finite")
    for field in OPTIONAL_COLUMNS:
        if field in frame:
            for value in frame[field]:
                _text(value, field)


def validate_manifest(manifest, inventory):
    """Raise on leakage or any missing, added, duplicated or altered input row.

    inventory is mandatory; an internally consistent manifest alone cannot
    prove conservation. This version has no implicit exclusion rule.
    """
    _check_rows(inventory)
    _check_rows(manifest)
    if "split" not in manifest or not manifest.split.isin(SPLITS).all():
        raise ValueError("Invalid/missing split")
    if set(manifest.split) != set(SPLITS):
        raise ValueError("All three splits must be nonempty")
    expected_columns = set(inventory.columns) | {"split"}
    if set(manifest.columns) != expected_columns:
        raise ValueError("Manifest/inventory schema mismatch")
    if set(manifest.sample_id) != set(inventory.sample_id):
        raise ValueError("Missing or added sample relative to inventory")
    left = manifest.set_index("sample_id").sort_index()
    right = inventory.set_index("sample_id").sort_index()
    for column in right:
        if not np.array_equal(left[column].to_numpy(), right[column].to_numpy()):
            raise ValueError(f"Altered inventory field: {column}")
    for group in ("subject_id", "sample_hash", "waveform_hash"):
        if (manifest.groupby(group).split.nunique() > 1).any():
            raise ValueError(f"Cross-split leakage: {group}")
    if "record_id" in manifest and (
        manifest.groupby(["source", "record_id"]).split.nunique() > 1
    ).any():
        raise ValueError("Cross-split leakage: record_id")
    if "window_id" in manifest:
        keys = ["source", "window_id"]
        if "record_id" in manifest:
            keys.insert(1, "record_id")
        if (manifest.groupby(keys).split.nunique() > 1).any():
            raise ValueError("Cross-split leakage: window_id")
    return True


def make_manifest(inventory, seed=72, ratios=(0.8, 0.1, 0.1)):
    _check_rows(inventory)
    if inventory.source.nunique() != 1 or inventory.source_sha256.nunique() != 1:
        raise ValueError("Multi-source pools require an approved identity mapping")
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise ValueError("seed must be an integer")
    if not isinstance(ratios, (tuple, list)) or len(ratios) != 3 or any(
        isinstance(r, bool) or not isinstance(r, (int, float))
        or not math.isfinite(r) or r <= 0 for r in ratios
    ) or not math.isclose(sum(ratios), 1.0, rel_tol=0, abs_tol=1e-12):
        raise ValueError("Three positive ratios must sum to one")
    subjects = sorted(inventory.subject_id.unique())
    random.Random(seed).shuffle(subjects)
    # Exact decimal floor: int(90 * 0.7) is 62 in float arithmetic. Identical to
    # the float result for 0.8/0.1/0.1. The remainder always goes to test.
    n_train, n_val = (
        math.floor(len(subjects) * Fraction(str(ratio))) for ratio in ratios[:2]
    )
    if min(n_train, n_val, len(subjects) - n_train - n_val) < 1:
        raise ValueError("Too few subjects for requested split ratios")
    groups = (subjects[:n_train], subjects[n_train:n_train + n_val],
              subjects[n_train + n_val:])
    assignment = {subject: split for split, group in zip(SPLITS, groups)
                  for subject in group}
    result = inventory.copy()
    result["split"] = result.subject_id.map(assignment)
    result = result.sort_values(["source_sha256", "raw_index"]).reset_index(drop=True)
    validate_manifest(result, inventory)
    return result


def manifest_bytes(frame):
    """Stable CSV ordering, newline, column order and round-trip float format."""
    _check_rows(frame)
    if "split" in frame and not frame.split.isin(SPLITS).all():
        raise ValueError("Invalid/missing split")
    columns = list(COLUMNS) + [c for c in OPTIONAL_COLUMNS if c in frame]
    if "split" in frame:
        columns.append("split")
    return frame.sort_values(["source_sha256", "raw_index"])[columns].to_csv(
        index=False, lineterminator="\n", float_format="%.17g",
    ).encode("utf-8")


def read_manifest_bytes(payload):
    """Read version-2 CSV without inferring ID types or NA-like ID tokens.

    Parsing checks row/schema validity only; callers must still use
    validate_manifest(manifest, inventory) for conservation and leakage.
    """
    text = payload.decode("utf-8-sig")
    rows = csv.reader(io.StringIO(text, newline=""), strict=True)
    try:
        header = next(rows, [])
        if not header or len(header) != len(set(header)):
            raise ValueError("Missing or duplicate CSV headers")
        for row in rows:
            if len(row) != len(header):
                raise ValueError("CSV row has the wrong number of fields")
    except csv.Error as exc:
        raise ValueError("Malformed manifest CSV") from exc
    types = {field: str for field in header if field not in {"raw_index", "sbp", "dbp"}}
    types.update({"raw_index": np.int64, "sbp": np.float64, "dbp": np.float64})
    frame = pd.read_csv(
        io.StringIO(text), dtype=types, keep_default_na=False, na_filter=False,
        float_precision="round_trip",
    )
    _check_rows(frame)
    if "split" in frame and not frame.split.isin(SPLITS).all():
        raise ValueError("Invalid/missing split")
    return frame


def summarize_manifest(manifest, inventory):
    """Counts for every split; BP statistics only for LABEL_SUMMARY_SPLITS.

    Test-label statistics are omitted (``bp`` is None) so that a handover report
    cannot inform choices made before a locked test evaluation.
    """
    validate_manifest(manifest, inventory)
    report = {}
    for split in SPLITS:
        rows = manifest[manifest.split == split]
        report[split] = {
            "subjects": int(rows.subject_id.nunique()), "segments": len(rows),
            "bp": {} if split in LABEL_SUMMARY_SPLITS else None,
        }
        if split not in LABEL_SUMMARY_SPLITS:
            continue
        for target in ("sbp", "dbp"):
            values = rows[target]
            report[split]["bp"][target] = {
                "mean": float(values.mean()),
                "std_ddof1": float(values.std()) if len(values) > 1 else None,
                "min": float(values.min()), "max": float(values.max()),
            }
    return report