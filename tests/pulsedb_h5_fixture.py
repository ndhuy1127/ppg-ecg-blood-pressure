"""SYNTHETIC PulseDB Subset files in the MATLAB v7.3 layout, written with h5py.

Copies the layout seen in the real files (docs/pulsedb_provenance.md): a
``Subset`` struct group; numeric fields of shape (1, N) tagged ``MATLAB_class``;
Subject/Gender as cells of references to char (uint16) datasets in ``#refs#``,
an empty char tagged ``MATLAB_empty``; Signals stored as (samples, 3, N).
"""

import json
import math
from types import SimpleNamespace

import h5py
import numpy as np

from software.data_io.split_manifest import VERSION, file_sha256


def synthetic_rows(n_subjects=6, per_subject=3, samples=50, seed=0):
    """ABP spans DBP..SBP (channel order check passes); ECG/PPG are noise."""
    rng = np.random.default_rng(seed)
    t = np.linspace(0, 1, samples)
    rows = []
    for subject in range(n_subjects):
        for k in range(per_subject):
            sbp = 100.0 + 4 * subject + k + 0.123
            dbp = 60.0 + 2 * subject + 0.5 * k
            rows.append(SimpleNamespace(
                subject_id=f"SYN_{subject:03d}", gender=("M", "F", "")[(subject + k) % 3],
                age=30.0 + subject, height_cm=math.nan if k == 1 else 170.0 + subject,
                weight_kg=60.5 + k, bmi_kg_m2=21.25,
                sbp=sbp, dbp=dbp,
                ecg=rng.normal(0, 1, samples), ppg=rng.normal(0, 1, samples),
                abp=dbp + (sbp - dbp) * (np.sin(2 * np.pi * 3 * t) + 1) / 2,
            ))
    return rows


def _tag(node, matlab_class, empty=False):
    node.attrs["MATLAB_class"] = np.bytes_(matlab_class)
    if empty:
        node.attrs["MATLAB_empty"] = np.uint8(1)
    return node


def write_subset(path, rows, optional=True, chunk_rows=2):
    with h5py.File(path, "w") as handle:
        refs = handle.create_group("#refs#")
        group = _tag(handle.create_group("Subset"), "struct")

        def numeric(name, field):
            values = np.array([[getattr(row, field) for row in rows]], dtype=np.float64)
            _tag(group.create_dataset(name, data=values), "double")

        def cell(name, field):
            references = []
            for k, row in enumerate(rows):
                text = getattr(row, field)
                if text:
                    data = np.array([[ord(char)] for char in text], dtype=np.uint16)
                    item = _tag(refs.create_dataset(f"{name}_{k}", data=data), "char")
                else:
                    data = np.zeros(2, dtype=np.uint64)
                    item = _tag(refs.create_dataset(f"{name}_{k}", data=data), "char",
                                empty=True)
                references.append(item.ref)
            data = np.array([references], dtype=h5py.ref_dtype)
            _tag(group.create_dataset(name, data=data), "cell")

        signals = np.stack([np.stack([row.ecg, row.ppg, row.abp]) for row in rows])
        _tag(group.create_dataset(
            "Signals", data=signals.transpose(2, 1, 0), compression="gzip",
            chunks=(signals.shape[2], 3, min(chunk_rows, len(rows))),
        ), "double")
        numeric("SBP", "sbp")
        numeric("DBP", "dbp")
        numeric("Age", "age")
        if optional:
            numeric("Height", "height_cm")
            numeric("Weight", "weight_kg")
            numeric("BMI", "bmi_kg_m2")
        cell("Subject", "subject_id")
        cell("Gender", "gender")
    return path


def subsample_split_config(tmp_path, n_pool=30, per_subject=3, n_subjects=20, seed=5,
                           rows=None):
    """Pool file (``rows``, else synthetic_rows) + split-v2 config with an explicit
    subject subsample."""
    if rows is None:
        rows = synthetic_rows(n_subjects=n_pool, per_subject=per_subject)
    raw = write_subset(tmp_path / "SYN_pool.mat", rows)
    config = {
        "schema_version": VERSION, "input_path": raw.name,
        "input_sha256": file_sha256(raw), "source": "SYN_pool.mat",
        "source_version": "synthetic-v1", "license": "synthetic-test",
        "permission_basis": "synthetic-only",
        "pool_decision": "SYNTHETIC pool, subject subsample",
        "subject_identity_review": "known synthetic IDs", "unit": "mmHg",
        "seed": 72, "ratios": [0.8, 0.1, 0.1],
        "subject_subsample": {"n_subjects": n_subjects, "seed": seed},
    }
    path = tmp_path / "split_config.json"
    path.write_text(json.dumps(config), encoding="utf-8")
    return path, raw
