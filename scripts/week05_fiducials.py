"""Week 5 fiducial review: SYNTHETIC records, train export, plots, detection,
agreement.

Subcommands (each refuses to overwrite its output and writes provenance):

  synth     SYNTHETIC records with known R/foot times (code check only)
  export    review segments of a raw PulseDB file + split v2 (train only, by the
            config's review_plan): main/ for marking, repeat/ for a second session
  plot      PNG per record for manual review; detections hidden by default
  annotate  interactive window: Huy clicks R (ECG axis) and foot (PPG axis)
  detect    run every candidate R/foot method; CSV with one row per fiducial
  compare   sensitivity/PPV/bias/MAE of each method against manual marks
  repeat    annotator repeatability: second vs first marking of repeat/ segments
  gate      pre-registered acceptance: select on one subject group, confirm once

Manual marks are made by a person with ``annotate``. This script never
generates them; the SYNTHETIC truth file is labelled as such and ``compare``
refuses it unless ``--allow-synthetic-truth`` is given.
"""

import argparse
import csv
import hashlib
import json
import platform
import subprocess
import sys
from dataclasses import asdict, replace
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from software._provenance import text_file_sha256, text_sha256  # noqa: E402
from software.evaluation.fiducial_agreement import (  # noqa: E402
    ANNOTATION_COLUMNS, DETECTION_COLUMNS, SYNTHETIC_ANNOTATOR, agreement,
    is_synthetic_annotator,
)
from software.evaluation.fiducial_gate import (  # noqa: E402
    GROUPS, check_acceptance, gate, repeatability,
)
from software.signal_processing.fiducials import (  # noqa: E402
    FOOT_METHODS, R_METHODS, Channel, SignalConfig, detect,
)

# v3 (2026-10-25): export follows review_plan (train only, two subject groups,
# repeat segments); new repeat and gate commands.
# v4 (2026-10-29): compare refuses manual marks on val unless detect verified the
# records as unchanged synth output (records_from_synth); gate refuses non-train
# compared rows; export.json records must be on the plan's train split.
SCRIPT_VERSION = "week05-fiducials-v4"
# v1 (2026-10-25): T apex at 0.28 * sqrt(RR) s after R instead of a fixed 0.25 s,
# which sat on the 0.25 s refractory boundary; SYN_T_EDGE_HR60 keeps the old
# position as a boundary case. v0 results stay as history.
SYNTHETIC_VERSION = "week05-synthetic-records-v1"
RECORD_COLUMNS = ("record_id", "subject_id", "split", "source_type", "origin",
                  "ecg_fs_hz", "ppg_fs_hz", "file", "file_sha256")
CODE_FILES = ("scripts/week05_fiducials.py", "software/signal_processing/fiducials.py",
              "software/signal_processing/pat_validity.py",
              "software/evaluation/fiducial_agreement.py",
              "software/evaluation/fiducial_gate.py", "software/_provenance.py",
              # Used by export to read raw PulseDB and check the split handover.
              "software/pulsedb/reader.py", "software/pulsedb/h5_reader.py",
              "software/data_io/split_manifest.py", "software/pulsedb/pipeline.py")
LIBRARIES = ("numpy", "scipy", "pandas", "matplotlib", "mat73", "h5py")


def _git(*args):
    try:
        return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def _library_version(name):
    try:
        return version(name)
    except PackageNotFoundError:
        return None


def provenance(command, inputs, source_types):
    status = _git("status", "--porcelain")
    return {
        "script_version": SCRIPT_VERSION,
        "command": command,
        "source_types": sorted(set(source_types)),
        "git_commit": _git("rev-parse", "HEAD"),
        "workspace_has_changes": None if status is None else bool(status),
        "code_sha256_lf": {name: text_file_sha256(ROOT / name) for name in CODE_FILES},
        "inputs_sha256": inputs,
        "environment": {"python": platform.python_version(),
                        **{name: _library_version(name) for name in LIBRARIES}},
    }


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _synth_records(records, records_sha256):
    """True only for an unchanged ``synth`` output: its synth.provenance.json
    lists this records.csv hash and SYNTHETIC as the only source type."""
    try:
        info = json.loads((Path(records) / "synth.provenance.json").read_text(
            encoding="utf-8"))
        return (info["outputs_sha256"]["records.csv"] == records_sha256
                and info["provenance"]["source_types"] == ["SYNTHETIC"])
    except (OSError, KeyError, TypeError, json.JSONDecodeError):
        return False


def _sidecar(path):
    """``det.csv`` -> ``det.provenance.json`` next to it."""
    path = Path(path)
    return path.with_name(path.stem + ".provenance.json")


def _refuse_existing(*paths):
    for path in paths:
        if Path(path).exists():
            raise FileExistsError(f"{path} exists; refusing to overwrite")


def _new_dir(path):
    path = Path(path)
    _refuse_existing(path)
    path.mkdir(parents=True)
    return path


def _new_file(path):
    path = Path(path)
    _refuse_existing(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path.open("x", encoding="utf-8", newline="")


def _write_csv(path, columns, rows):
    with _new_file(path) as stream:
        writer = csv.DictWriter(stream, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _write_json(path, payload):
    with _new_file(path) as stream:
        stream.write(json.dumps(payload, indent=2, allow_nan=False) + "\n")


# --- SYNTHETIC records -------------------------------------------------------

def t_apex_s(rr_s):
    """R to T-apex delay: 0.28 * sqrt(RR / 1 s) s (about 280 ms at 60 bpm, 177 ms
    at 150 bpm). Rate scaling in the spirit of ECGSYN
    (https://physionet.org/content/ecgsyn/1.0.0/); an engineering nominal for
    SYNTHETIC records, not a validated physiological model."""
    return 0.28 * float(np.sqrt(rr_s))


def synthetic_record(rr_s=1.0, duration_s=10.0, pat_s=0.2, rise_s=0.15, ecg_fs=500,
                     ppg_fs=125, noise_sd=0.0, wander=0.0, drop_beats=(),
                     drop_ppg_beats=(), seed=0, t_delay_s=None):
    """Gaussian QRS with a T wave; PPG pulse = half-cosine rise then exponential
    decay.

    Truth: R at the Gaussian centre; foot at pulse onset (start of the rise).
    The T apex is ``t_delay_s`` after R (default ``t_apex_s(rr_s)``).
    ``drop_beats`` removes beat k from both channels (pause); ``drop_ppg_beats``
    removes only its PPG pulse. Shapes are not physiological models.
    """
    t_delay = t_apex_s(rr_s) if t_delay_s is None else t_delay_s
    rng = np.random.default_rng(seed)
    beats = np.arange(1.0, duration_s - 0.6, rr_s)
    kept = np.array([t for k, t in enumerate(beats) if k not in drop_beats])
    pulses = np.array([t for k, t in enumerate(beats) if k not in drop_beats
                       and k not in drop_ppg_beats]) + pat_s
    et = np.arange(int(duration_s * ecg_fs)) / ecg_fs
    pt = np.arange(int(duration_s * ppg_fs)) / ppg_fs
    ecg = np.zeros_like(et)
    for r in kept:
        ecg += (np.exp(-0.5 * ((et - r) / 0.01) ** 2)
                - 0.15 * np.exp(-0.5 * ((et - r + 0.03) / 0.008) ** 2)
                - 0.2 * np.exp(-0.5 * ((et - r - 0.03) / 0.008) ** 2)
                + 0.3 * np.exp(-0.5 * ((et - r - t_delay) / 0.04) ** 2))
    ppg = np.zeros_like(pt)
    for onset in pulses:
        x = pt - onset
        ppg += np.where((x >= 0) & (x < rise_s), 0.5 * (1 - np.cos(np.pi * x / rise_s)),
                        np.where(x >= rise_s, np.exp(-(x - rise_s) / 0.12), 0.0))
    if noise_sd or wander:
        ecg = (ecg + noise_sd * rng.standard_normal(len(et))
               + wander * np.sin(2 * np.pi * 0.25 * et))
        ppg = (ppg + noise_sd * rng.standard_normal(len(pt))
               + wander * np.sin(2 * np.pi * 0.25 * pt + 1))
    return ecg, ppg, ecg_fs, ppg_fs, kept, pulses


SYNTHETIC_CASES = {
    "SYN_CLEAN_HR60": {},
    "SYN_NOISY_HR60": {"noise_sd": 0.03, "wander": 0.2, "seed": 5},
    "SYN_PAUSE_HR60": {"drop_beats": (4,)},
    "SYN_PPG_DROPOUT_HR60": {"drop_ppg_beats": (3,)},
    "SYN_HIGH_HR143": {"rr_s": 0.42, "pat_s": 0.16, "rise_s": 0.1},
    # Boundary case: T apex exactly on the 0.25 s ECG refractory period.
    "SYN_T_EDGE_HR60": {"t_delay_s": 0.25},
}


def run_synth(out):
    out = _new_dir(out)
    records, truth = [], []
    for record_id, kwargs in SYNTHETIC_CASES.items():
        ecg, ppg, ecg_fs, ppg_fs, r_true, foot_true = synthetic_record(**kwargs)
        path = out / f"{record_id}.npz"
        np.savez(path, ecg=ecg, ppg=ppg)
        records.append({"record_id": record_id, "subject_id": "SYN_S01", "split": "val",
                        "source_type": "SYNTHETIC",
                        "origin": json.dumps(kwargs, sort_keys=True),
                        "ecg_fs_hz": ecg_fs, "ppg_fs_hz": ppg_fs, "file": path.name,
                        "file_sha256": _sha256(path)})
        end = len(ecg) / ecg_fs
        for fiducial, times in (("ecg_r", r_true), ("ppg_foot", foot_true)):
            # Region excludes the edges where detectors trim candidates.
            region = (0.5, end - 0.5)
            base = {"record_id": record_id, "split": "val", "fiducial": fiducial,
                    "review_start_s": region[0], "review_end_s": region[1],
                    "annotator": SYNTHETIC_ANNOTATOR, "annotated_on": ""}
            rows = [{**base, "time_s": f"{t:.6f}",
                     "note": "generated truth, not a manual mark"}
                    for t in times if region[0] <= t <= region[1]]
            truth += rows or [{**base, "time_s": "", "note": "no beat in region"}]
    _write_csv(out / "records.csv", RECORD_COLUMNS, records)
    _write_csv(out / "truth_synthetic.csv", ANNOTATION_COLUMNS, truth)
    _write_json(out / "synth.provenance.json", {
        "generator_version": SYNTHETIC_VERSION,
        "cases": {k: {"defaults_overridden": v} for k, v in SYNTHETIC_CASES.items()},
        "outputs_sha256": {name: _sha256(out / name)
                           for name in ("records.csv", "truth_synthetic.csv")},
        "provenance": provenance("synth", {}, ["SYNTHETIC"]),
    })
    return out


# --- PulseDB train export ----------------------------------------------------

def export_record_id(raw_sha256, split, raw_index):
    """``PDB_<first 12 hex of the raw SHA-256>_<split>_<raw_index>``.

    The prefix keeps rows of two raw files (two pools) apart; it is a label
    only, and export.json keeps the full SHA-256.
    """
    return f"PDB_{raw_sha256[:12]}_{split}_{raw_index}"


PLAN_FIELDS = {"split", "n_subjects", "per_subject", "selection_subjects", "seed",
               "repeat_segments", "foot_definition", "r_definition"}


def _check_plan(plan):
    if set(plan) != PLAN_FIELDS:
        raise ValueError(f"review_plan needs exactly {sorted(PLAN_FIELDS)}")
    numbers = ("n_subjects", "per_subject", "selection_subjects", "seed",
               "repeat_segments")
    if any(isinstance(plan[k], bool) or not isinstance(plan[k], int) for k in numbers):
        raise ValueError("review_plan counts and seed must be integers")
    if plan["split"] != "train":
        raise ValueError("Fiducial methods are selected on train subjects only")
    if not 1 <= plan["selection_subjects"] < plan["n_subjects"]:
        raise ValueError("Both subject groups must be nonempty")
    smallest = min(plan["selection_subjects"],
                   plan["n_subjects"] - plan["selection_subjects"])
    if plan["per_subject"] < 1 or plan["repeat_segments"] % 2 or not (
            0 <= plan["repeat_segments"] // 2 <= smallest):
        raise ValueError("per_subject >= 1; repeat_segments even, one per subject "
                         "and at most the smaller group per group")


def select_review_plan(manifest, plan):
    """Subjects, groups, segments and repeat subset for manual review.

    Uses only subject_id, split and raw_index of the plan's split (train): no
    BP column and no signal value; val and test rows are never candidates.
    Subjects come from a seeded permutation (the first ``selection_subjects``
    form the selection group); each subject's sorted raw_index is cut into
    ``per_subject`` parts and one row is drawn from each part (raw_index is a
    file row, not time). ``repeat_segments`` segments, half per group and one
    per subject, are marked again later. Both lists are in a shuffled order.
    Returns {"groups": {group: subjects}, "main": [raw_index], "repeat": [...]}.
    """
    _check_plan(plan)
    rng = np.random.default_rng(plan["seed"])
    rows = manifest[manifest.split == plan["split"]]
    subjects = sorted(rows.subject_id.unique())
    if plan["n_subjects"] > len(subjects):
        raise ValueError("review_plan asks for more subjects than the split has")
    chosen = [subjects[i] for i in rng.permutation(len(subjects))[:plan["n_subjects"]]]
    k = plan["selection_subjects"]
    groups = {"selection": sorted(chosen[:k]), "confirmation": sorted(chosen[k:])}
    picks = {}
    for subject in chosen:
        indices = np.sort(rows.raw_index[rows.subject_id == subject].to_numpy())
        parts = np.array_split(indices, plan["per_subject"])
        if any(len(part) == 0 for part in parts):
            raise ValueError("A subject has fewer segments than per_subject")
        picks[subject] = [int(part[rng.integers(len(part))]) for part in parts]
    repeat = []
    for name in GROUPS:
        members = rng.choice(groups[name], plan["repeat_segments"] // 2,
                             replace=False)
        repeat += [picks[s][rng.integers(len(picks[s]))] for s in sorted(members)]
    main = sorted(i for indices in picks.values() for i in indices)
    return {"groups": groups,
            "main": [int(i) for i in rng.permutation(main)],
            "repeat": [int(i) for i in rng.permutation(sorted(repeat))]}


def _write_records(directory, rows, raw_sha256, fs_hz, segments):
    directory = _new_dir(directory)
    records = []
    for row in rows:
        segment = segments[int(row.raw_index)]
        record_id = export_record_id(raw_sha256, row.split, int(row.raw_index))
        path = directory / f"{record_id}.npz"
        # Only ECG and PPG are exported; ABP and labels stay in the raw file.
        np.savez(path, ecg=np.asarray(segment.ecg, float),
                 ppg=np.asarray(segment.ppg, float))
        records.append({"record_id": record_id, "subject_id": row.subject_id,
                        "split": row.split, "source_type": "PUBLIC_PULSEDB",
                        "origin": row.sample_id, "ecg_fs_hz": fs_hz,
                        "ppg_fs_hz": fs_hz, "file": path.name,
                        "file_sha256": _sha256(path)})
    _write_csv(directory / "records.csv", RECORD_COLUMNS, records)
    return _sha256(directory / "records.csv")


def run_export(raw, split_dir, fs_hz, config_path, out):
    """Every inventory row (test included) is read block by block with the h5py
    reader and re-hashed against the inventory, as in b3-pipeline-v1; only the
    review_plan's train rows are written, ECG/PPG only, to ``out/main`` (first
    marking session) and ``out/repeat`` (second session). ``out/export.json``
    keeps the subject groups and both records.csv hashes."""
    from software.data_io.split_manifest import file_sha256, read_manifest_bytes
    from software.pulsedb.h5_reader import PulseDBH5Reader
    from software.pulsedb.pipeline import verify_inputs

    _refuse_existing(out)
    config_bytes = Path(config_path).read_bytes()
    plan = json.loads(config_bytes)["review_plan"]
    split_dir = Path(split_dir)
    payloads = {n: (split_dir / n).read_bytes()
                for n in ("inventory.csv", "manifest.csv", "report.json")}
    report = json.loads(payloads["report.json"])
    raw_sha256 = file_sha256(raw)
    for field, actual in (
        ("raw_sha256", raw_sha256),
        ("inventory_sha256", hashlib.sha256(payloads["inventory.csv"]).hexdigest()),
        ("manifest_sha256", hashlib.sha256(payloads["manifest.csv"]).hexdigest()),
    ):
        if report.get(field) != actual:
            raise ValueError(f"{field} differs from the split handover report")
    inventory = read_manifest_bytes(payloads["inventory.csv"])
    manifest = read_manifest_bytes(payloads["manifest.csv"])
    selected = select_review_plan(manifest, plan)
    by_index = manifest.set_index("raw_index", drop=False)
    with PulseDBH5Reader(str(raw)).lazy(inventory.raw_index.tolist()) as segments:
        verify_inputs(manifest, inventory, segments)
        out = _new_dir(out)
        hashes = {name: _write_records(
            out / name, [by_index.loc[i] for i in selected[name]], raw_sha256,
            fs_hz, segments) for name in ("main", "repeat")}
    if file_sha256(raw) != raw_sha256:
        raise ValueError("Raw file changed during reading")
    _write_json(out / "export.json", {
        "review_plan": plan, "fs_hz_declared_by_caller": fs_hz,
        # Subject IDs: export.json stays next to the records, outside Git.
        "groups": selected["groups"],
        "records_csv_sha256": hashes,
        "provenance": provenance("export", {
            "raw": raw_sha256, "config": text_sha256(config_bytes),
            **{k: report[k] for k in ("inventory_sha256", "manifest_sha256")}},
            ["PUBLIC_PULSEDB"]),
    })
    return out


# --- records, plotting, annotation -------------------------------------------

def _record_index(directory):
    import pandas as pd

    directory = Path(directory)
    index = pd.read_csv(directory / "records.csv",
                        dtype={"record_id": str, "split": str, "source_type": str})
    if list(index.columns) != list(RECORD_COLUMNS):
        raise ValueError("records.csv has unexpected columns")
    if not set(index.split) <= {"train", "val"}:
        raise ValueError("Review records must come from train/val only")
    return index


def load_records(directory):
    directory = Path(directory)
    for row in _record_index(directory).itertuples():
        path = directory / row.file
        if _sha256(path) != row.file_sha256:
            raise ValueError(f"{row.file} does not match records.csv")
        with np.load(path) as data:
            yield row, data["ecg"], data["ppg"]


def _records_inputs(directory):
    """records.csv hash and source types; records.csv lists every file hash."""
    directory = Path(directory)
    index = _record_index(directory)
    return {"records_csv": _sha256(directory / "records.csv")}, list(index.source_type)


def _channels(row, ecg, ppg):
    return (Channel(ecg, float(row.ecg_fs_hz), "record_unit", None),
            Channel(ppg, float(row.ppg_fs_hz), "record_unit", None))


def _figure(row, ecg, ppg, detections=None):
    import matplotlib.pyplot as plt

    et = np.arange(len(ecg)) / row.ecg_fs_hz
    pt = np.arange(len(ppg)) / row.ppg_fs_hz
    fig, axes = plt.subplots(2, 1, figsize=(max(10, 2 * et[-1]), 6), sharex=True)
    axes[0].plot(et, ecg, lw=0.8)
    axes[1].plot(pt, ppg, lw=0.8, marker=".", ms=2)
    axes[0].set_ylabel("ECG (record unit)")
    axes[1].set_ylabel("PPG (record unit)")
    axes[1].set_xlabel("time (s)")
    for ax in axes:
        ax.set_xticks(np.arange(0, et[-1] + 1e-9, 0.5))
        ax.set_xticks(np.arange(0, et[-1] + 1e-9, 0.1), minor=True)
        ax.grid(which="major", lw=0.6)
        ax.grid(which="minor", lw=0.2)
    if detections is not None:
        for ax, fiducial in zip(axes, ("ecg_r", "ppg_foot")):
            rows = detections[(detections.record_id == row.record_id)
                              & (detections.fiducial == fiducial)
                              ].dropna(subset=["time_s"])
            for method, group in rows.groupby("method"):
                ax.vlines(group.time_s, *ax.get_ylim(), lw=0.6, label=method,
                          alpha=0.6)
            ax.legend(loc="upper right", fontsize=7)
    label = "detections shown" if detections is not None else "blind: no detections"
    fig.suptitle(f"{row.record_id} [{row.source_type}, {row.split}] - {label}")
    return fig, axes


def run_plot(records, out, detections_csv=None):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import pandas as pd

    inputs, source_types = _records_inputs(records)
    if detections_csv is not None:
        inputs["detections"] = _sha256(detections_csv)
    detections = None if detections_csv is None else pd.read_csv(detections_csv)
    out = _new_dir(out)
    for row, ecg, ppg in load_records(records):
        fig, _ = _figure(row, ecg, ppg, detections)
        fig.savefig(out / f"{row.record_id}.png", dpi=100)
        plt.close(fig)
    _write_json(out / "plot.provenance.json", {
        "detections_shown": detections_csv is not None,
        "provenance": provenance("plot", inputs, source_types),
    })
    return out


def clicks_to_rows(record, clicks, region, annotator, annotated_on):
    """Turn clicked (fiducial, time) pairs into annotation rows; no snapping.

    An empty fiducial still gets one row so the reviewed region is recorded.
    """
    rows = []
    for fiducial in ("ecg_r", "ppg_foot"):
        times = sorted(t for f, t in clicks if f == fiducial)
        base = {"record_id": record.record_id, "split": record.split,
                "fiducial": fiducial, "review_start_s": region[0],
                "review_end_s": region[1], "annotator": annotator,
                "annotated_on": annotated_on, "note": ""}
        rows += [{**base, "time_s": f"{t:.6f}"} for t in times] or [
            {**base, "time_s": ""}]
    return rows


def _progress_path(out):
    """``manual.csv`` -> ``manual.progress.json``: state of an unfinished session."""
    out = Path(out)
    return out.with_name(out.stem + ".progress.json")


def _write_progress(path, progress):
    temporary = Path(str(path) + ".tmp")
    temporary.write_text(json.dumps(progress, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def _checkpoint(out):
    """Byte length and SHA-256 of the CSV as committed so far."""
    data = Path(out).read_bytes()
    return {"csv_bytes": len(data), "csv_sha256": hashlib.sha256(data).hexdigest()}


def _resume_state(out, records_sha, annotator, edge_s):
    """Check a partial session against its last checkpoint.

    The CSV must start with exactly the committed bytes (any edit is refused).
    Bytes after the checkpoint are a record written before a crash and not yet
    committed: they are cut off and that record is marked again; the cut is
    recorded in the sittings.
    """
    try:
        progress = json.loads(_progress_path(out).read_text(encoding="utf-8"))
        committed = (progress["records_csv"], progress["annotator"],
                     progress["edge_s"])
        size, digest = progress["csv_bytes"], progress["csv_sha256"]
    except (OSError, KeyError, TypeError, json.JSONDecodeError) as exc:
        raise ValueError(f"Unreadable progress file: {exc}") from exc
    if committed != (records_sha, annotator, edge_s):
        raise ValueError("--resume needs the same records, annotator and edge_s")
    data = Path(out).read_bytes()
    if len(data) < size or hashlib.sha256(data[:size]).hexdigest() != digest:
        raise ValueError(f"{out} differs from its last checkpoint; mark again into "
                         "a new file")
    progress["discarded_uncommitted_bytes"] = len(data) - size
    if len(data) > size:
        with Path(out).open("r+b") as stream:
            stream.truncate(size)
    return progress


def run_annotate(records, out, annotator, annotated_on, edge_s, resume=False):
    """Left click adds a mark at the clicked time (ECG axis = R, PPG axis = foot);
    right click removes the nearest mark on that axis. Close the window to go on.

    Each record is written as soon as its window closes, and
    ``<out>.progress.json`` records which are done, so an interrupted session
    goes on with ``resume=True`` (the same records, annotator and edge_s; the
    date may differ). The provenance sidecar is written once every record is
    marked; an existing sidecar is never appended to.
    """
    import matplotlib.pyplot as plt

    if not annotator.strip() or is_synthetic_annotator(annotator):
        raise ValueError("annotator must be the person who marks")
    sidecar, progress_path = _sidecar(out), _progress_path(out)
    inputs, source_types = _records_inputs(records)
    if resume:
        _refuse_existing(sidecar)
        progress = _resume_state(out, inputs["records_csv"], annotator, edge_s)
        stream = Path(out).open("a", encoding="utf-8", newline="")
    else:
        _refuse_existing(out, sidecar, progress_path)
        progress = {"records_csv": inputs["records_csv"], "annotator": annotator,
                    "edge_s": edge_s, "records_done": [], "sittings": [],
                    "clicks_outside_region_dropped": {},
                    "discarded_uncommitted_bytes": 0}
        stream = _new_file(out)
    progress["sittings"].append({
        "date": annotated_on, "first_record": len(progress["records_done"]),
        "discarded_uncommitted_bytes": progress.pop("discarded_uncommitted_bytes")})
    done = set(progress["records_done"])
    with stream:
        writer = csv.DictWriter(stream, fieldnames=ANNOTATION_COLUMNS,
                                lineterminator="\n")
        if not resume:
            writer.writeheader()
        stream.flush()
        _write_progress(progress_path, {**progress, **_checkpoint(out)})
        for row, ecg, ppg in load_records(records):
            if row.record_id in done:
                continue
            fig, axes = _figure(row, ecg, ppg)
            clicks, artists = [], []

            def on_click(event, fig=fig, axes=axes, clicks=clicks, artists=artists):
                toolbar = getattr(fig.canvas, "toolbar", None)
                if (event.inaxes not in axes or event.xdata is None
                        or (toolbar is not None and toolbar.mode)):
                    return
                fiducial = "ecg_r" if event.inaxes is axes[0] else "ppg_foot"
                if event.button == 1:
                    clicks.append((fiducial, float(event.xdata)))
                    artists.append(event.inaxes.axvline(event.xdata, color="r", lw=0.8))
                elif event.button == 3:
                    same = [i for i, (f, _) in enumerate(clicks) if f == fiducial]
                    if same:
                        i = min(same, key=lambda k: abs(clicks[k][1] - event.xdata))
                        clicks.pop(i)
                        artists.pop(i).remove()
                fig.canvas.draw_idle()

            fig.canvas.mpl_connect("button_press_event", on_click)
            plt.show()
            plt.close(fig)
            end = len(ecg) / row.ecg_fs_hz
            region = (edge_s, end - edge_s)
            inside = [(f, t) for f, t in clicks if region[0] <= t <= region[1]]
            writer.writerows(clicks_to_rows(row, inside, region, annotator,
                                            annotated_on))
            stream.flush()
            progress["records_done"].append(row.record_id)
            progress["clicks_outside_region_dropped"][row.record_id] = (
                len(clicks) - len(inside))
            # The record counts as committed only once this checkpoint is written.
            _write_progress(progress_path, {**progress, **_checkpoint(out)})
    if len(progress["records_done"]) < len(_record_index(records)):
        return None  # Unfinished: continue later with resume.
    _write_json(sidecar, {
        "annotator": annotator, "annotated_on": annotated_on, "edge_s": edge_s,
        "sittings": progress["sittings"],
        "clicks_outside_region_dropped": progress["clicks_outside_region_dropped"],
        "output_sha256": _sha256(out),
        "provenance": provenance("annotate", inputs, source_types),
    })
    return out


# --- detection and comparison ------------------------------------------------

def detection_rows(row, ecg, ppg, base_config):
    """One marker row per (method, fiducial) plus one row per detected time.

    Returns (rows, channel issues per method) so a rejected channel is not
    mistaken for "ran and found nothing".
    """
    ecg_channel, ppg_channel = _channels(row, ecg, ppg)
    rows, issues = [], {}
    for kind, fiducial, methods, field in (
        ("ecg", "ecg_r", R_METHODS, "r_method"),
        ("ppg", "ppg_foot", FOOT_METHODS, "foot_method"),
    ):
        channel = ecg_channel if kind == "ecg" else ppg_channel
        for method in methods:
            config = replace(base_config, **{field: method})
            times, found_issues = detect(channel, config, kind)
            base = {"record_id": row.record_id, "split": row.split, "method": method,
                    "fiducial": fiducial}
            rows.append({**base, "time_s": ""})
            rows += [{**base, "time_s": f"{t:.6f}"} for t in times]
            if found_issues:
                issues[f"{fiducial}/{method}"] = list(found_issues)
    return rows, issues


def run_detect(records, config_path, out):
    sidecar = _sidecar(out)
    _refuse_existing(out, sidecar)
    config_bytes = Path(config_path).read_bytes()
    config = json.loads(config_bytes)
    base = SignalConfig(**config["signal"])
    inputs, source_types = _records_inputs(records)
    rows, issues = [], {}
    for row, ecg, ppg in load_records(records):
        record_rows, record_issues = detection_rows(row, ecg, ppg, base)
        rows += record_rows
        if record_issues:
            issues[row.record_id] = record_issues
    _write_csv(out, DETECTION_COLUMNS, rows)
    _write_json(sidecar, {
        "config_version": config.get("version"), "config_status": config.get("status"),
        "signal_config": asdict(base),
        # Checked against synth.provenance.json, not taken from records.csv.
        "records_from_synth": _synth_records(records, inputs["records_csv"]),
        "channel_issues": issues,
        "output_sha256": _sha256(out),
        "provenance": provenance(
            "detect", {**inputs, "config": text_sha256(config_bytes)}, source_types),
    })
    return out


def _annotation_provenance(annotations_csv, records_sha256, allow_missing):
    """Tie the annotations to the records.csv that ``detect`` used.

    Sources, in order: the ``annotate`` sidecar (<name>.provenance.json), or for
    generated truth the ``synth.provenance.json`` next to truth_synthetic.csv.
    A sidecar that exists but does not match (other file, other records, broken
    structure) is always refused. Only a missing provenance (a hand-filled
    template CSV) can be allowed, and that is recorded in the output.
    """
    annotations_csv = Path(annotations_csv)
    sidecar = _sidecar(annotations_csv)
    synth = annotations_csv.with_name("synth.provenance.json")
    try:
        if sidecar.exists():
            info = json.loads(sidecar.read_text(encoding="utf-8"))
            kind, source = "annotate", sidecar
            output = info["output_sha256"]
            records = info["provenance"]["inputs_sha256"]["records_csv"]
        elif annotations_csv.name == "truth_synthetic.csv" and synth.exists():
            info = json.loads(synth.read_text(encoding="utf-8"))
            kind, source = "synth", synth
            output = info["outputs_sha256"]["truth_synthetic.csv"]
            records = info["outputs_sha256"]["records.csv"]
        elif allow_missing:
            return {"kind": "none", "file": None, "sha256": None, "records_csv": None}
        else:
            raise ValueError(
                "Annotations have no provenance (annotate sidecar or "
                "synth.provenance.json); pass --annotations-without-provenance "
                "to compare a hand-filled CSV")
    except (KeyError, TypeError, json.JSONDecodeError) as exc:
        raise ValueError(f"Unreadable annotation provenance: {exc}") from exc
    if output != _sha256(annotations_csv):
        raise ValueError("Annotations differ from the file recorded by their "
                         "provenance")
    if records != records_sha256:
        raise ValueError("Annotations were made on other records than the detections")
    return {"kind": kind, "file": source.name, "sha256": _sha256(source),
            "records_csv": records}


def run_compare(annotations_csv, detections_csv, config_path, out,
                allow_synthetic_truth=False,
                allow_annotations_without_provenance=False):
    """The config must be the one ``detect`` used: its tolerances are read here
    and its signal settings produced the detections. The annotations must come
    from the same records as the detections (``_annotation_provenance``)."""
    import pandas as pd

    _refuse_existing(out)
    config_bytes = Path(config_path).read_bytes()
    config = json.loads(config_bytes)
    detect_sidecar = _sidecar(detections_csv)
    if not detect_sidecar.exists():
        raise ValueError(f"{detect_sidecar} is missing; run detect with this script")
    detect_info = json.loads(detect_sidecar.read_text(encoding="utf-8"))
    if detect_info["output_sha256"] != _sha256(detections_csv):
        raise ValueError("Detections differ from the file recorded by detect")
    detect_config = detect_info["provenance"]["inputs_sha256"]["config"]
    if detect_config != text_sha256(config_bytes):
        raise ValueError("Config differs from the one detect used; compare with the "
                         "same config so tolerances and detections match")
    annotation_source = _annotation_provenance(
        annotations_csv, detect_info["provenance"]["inputs_sha256"]["records_csv"],
        allow_annotations_without_provenance)
    read = {"dtype": {"record_id": str, "split": str, "fiducial": str},
            "keep_default_na": False, "na_values": [""]}
    annotations = pd.read_csv(annotations_csv, **read)
    detections = pd.read_csv(detections_csv, dtype={"record_id": str, "split": str,
                                                     "method": str, "fiducial": str})
    # Manual marks on val pass only for records verified as synth output at detect;
    # a source_type typed into records.csv is not enough (None fails closed).
    synth = detect_info.get("records_from_synth") is True
    result = agreement(annotations, detections, config["agreement"]["tolerance_s"],
                       allow_synthetic_truth=allow_synthetic_truth,
                       source_types=(detect_info["provenance"]["source_types"]
                                     if synth else None))
    result["provenance"] = provenance("compare", {
        "annotations": _sha256(annotations_csv),
        "annotations_provenance": annotation_source["sha256"],
        "detections": _sha256(detections_csv),
        "detections_provenance": _sha256(detect_sidecar),
        "config": text_sha256(config_bytes)},
        detect_info["provenance"]["source_types"])
    result["annotation_provenance"] = annotation_source
    result["detect_provenance"] = detect_info["provenance"]
    _write_json(out, result)
    return result


def _export_info(export_json, config_bytes):
    """export.json, the subject of each main/ record and the repeat/ record IDs,
    after checking both records.csv hashes, that both are on the plan's train
    split and that the export used this config (so the plan, groups and gates
    belong together)."""
    import pandas as pd

    export_json = Path(export_json)
    info = json.loads(export_json.read_text(encoding="utf-8"))
    if info["provenance"]["inputs_sha256"].get("config") != text_sha256(config_bytes):
        raise ValueError("export.json was made with another config")
    if info["review_plan"] != json.loads(config_bytes)["review_plan"]:
        raise ValueError("export.json review_plan differs from the config")
    index = {}
    for name in ("main", "repeat"):
        path = export_json.parent / name / "records.csv"
        if _sha256(path) != info["records_csv_sha256"][name]:
            raise ValueError(f"{name}/records.csv differs from export.json")
        index[name] = pd.read_csv(path, dtype=str)
    plan, groups = info["review_plan"], info["groups"]
    _check_plan(plan)  # Train only, among others.
    main, repeat = index["main"], index["repeat"]
    per_subject = main.groupby("subject_id").size()
    selection = set(groups["selection"])
    repeat_groups = [s in selection for s in repeat.subject_id]
    if (main.record_id.duplicated().any() or repeat.record_id.duplicated().any()
            or set(main.split) != {plan["split"]}
            or set(repeat.split) != {plan["split"]}
            or len(per_subject) != plan["n_subjects"]
            or set(per_subject) != {plan["per_subject"]}
            or len(groups["selection"]) != plan["selection_subjects"]
            or set(groups["selection"]) | set(groups["confirmation"])
            != set(per_subject.index)
            or len(repeat) != plan["repeat_segments"]
            or repeat.subject_id.duplicated().any()
            or not set(repeat.record_id) <= set(main.record_id)
            or sum(repeat_groups) != plan["repeat_segments"] // 2):
        raise ValueError("export.json records do not match its review_plan")
    return (info, dict(zip(index["main"].record_id, index["main"].subject_id)),
            list(index["repeat"].record_id))


def run_repeat(first_csv, second_csv, export_json, config_path, out):
    """Annotator repeatability on the repeat/ segments: the first session must be
    marked on main/ and the second on repeat/ (checked through their provenance),
    at least ``repeat_min_days`` apart."""
    import pandas as pd

    _refuse_existing(out)
    config_bytes = Path(config_path).read_bytes()
    config = json.loads(config_bytes)
    acceptance = config["acceptance"]
    check_acceptance(acceptance)
    info, _, repeat_records = _export_info(export_json, config_bytes)
    sources = {
        "first": _annotation_provenance(first_csv, info["records_csv_sha256"]["main"],
                                        False),
        "second": _annotation_provenance(second_csv,
                                         info["records_csv_sha256"]["repeat"], False),
    }
    read = {"dtype": {"record_id": str, "split": str, "fiducial": str,
                      "annotated_on": str},
            "keep_default_na": False, "na_values": [""]}
    result = repeatability(pd.read_csv(first_csv, **read),
                           pd.read_csv(second_csv, **read),
                           config["agreement"]["tolerance_s"],
                           acceptance["repeatability_max_mae_ms"],
                           acceptance["repeat_min_days"], repeat_records)
    result["annotation_provenance"] = sources
    result["provenance"] = provenance("repeat", {
        "first": _sha256(first_csv), "second": _sha256(second_csv),
        "export": _sha256(export_json), "config": text_sha256(config_bytes)},
        ["PUBLIC_PULSEDB"])
    _write_json(out, result)
    return result


def run_gate(agreement_json, export_json, config_path, out, repeatability_json=None,
             allow_synthetic_truth=False):
    """Apply the config's acceptance block to a ``compare`` output made with
    verified marks of every main/ record of ``export_json``. B4 is allowed only
    when both winners are confirmed and a repeatability result made from the same
    first-session marks, config and export has ``passed`` true."""
    from software.evaluation.fiducial_gate import VERSION as GATE_VERSION

    _refuse_existing(out)
    config_bytes = Path(config_path).read_bytes()
    config = json.loads(config_bytes)
    compared = json.loads(Path(agreement_json).read_text(encoding="utf-8"))
    if compared.get("version") != "fiducial-agreement-v1":
        raise ValueError("gate needs a compare output with per-record errors (v1)")
    if compared["provenance"]["inputs_sha256"]["config"] != text_sha256(config_bytes):
        raise ValueError("compare used another config")
    if compared["reference_type"] != "MANUAL" and not allow_synthetic_truth:
        raise ValueError("gate needs manual marks; SYNTHETIC truth is a code check")
    info, record_subject, _ = _export_info(export_json, config_bytes)
    main_sha = info["records_csv_sha256"]["main"]
    if compared["detect_provenance"]["inputs_sha256"]["records_csv"] != main_sha:
        raise ValueError("compare was not run on main/ of this export")
    source = compared["annotation_provenance"]
    kinds = {"annotate", "synth"} if allow_synthetic_truth else {"annotate"}
    if source["kind"] not in kinds or source["records_csv"] != main_sha:
        raise ValueError("gate needs marks with verified provenance on main/")
    if {row["split"] for row in compared["per_record"]} != {"train"}:
        raise ValueError("gate selects fiducial methods on train rows only")
    result = gate(compared["per_record"], record_subject, info["groups"],
                  config["acceptance"])
    inputs = {"agreement": _sha256(agreement_json), "export": _sha256(export_json),
              "config": text_sha256(config_bytes)}
    repeat = None
    if repeatability_json is not None:
        repeat = json.loads(Path(repeatability_json).read_text(encoding="utf-8"))
        used = repeat["provenance"]["inputs_sha256"]
        if (repeat.get("version") != GATE_VERSION
                or repeat["provenance"]["command"] != "repeat"):
            raise ValueError("--repeatability must be an output of repeat")
        if used["config"] != inputs["config"] or used["export"] != inputs["export"]:
            raise ValueError("repeatability used another config or export")
        if used["first"] != compared["provenance"]["inputs_sha256"]["annotations"]:
            raise ValueError("repeatability used other first-session marks")
        inputs["repeatability"] = _sha256(repeatability_json)
    result["repeatability_passed"] = (None if repeat is None
                                      else repeat["passed"] is True)
    if not result["detectors_confirmed"] or result["repeatability_passed"] is False:
        result["verdict"] = "B4_NOT_ALLOWED"
    elif repeat is None:
        result["verdict"] = "PENDING_REPEATABILITY"
    else:
        result["verdict"] = "B4_ALLOWED"
    result["reference_type"] = compared["reference_type"]
    result["provenance"] = provenance("gate", inputs,
                                      compared["provenance"]["source_types"])
    _write_json(out, result)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("synth")
    p.add_argument("--out", type=Path, required=True)
    p = sub.add_parser("export")
    p.add_argument("--raw", type=Path, required=True)
    p.add_argument("--split-dir", type=Path, required=True)
    p.add_argument("--fs-hz", type=float, required=True)
    p.add_argument("--config", type=Path, default=ROOT / "configs/data/week05_huy.json")
    p.add_argument("--out", type=Path, required=True)
    p = sub.add_parser("plot")
    p.add_argument("--records", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--detections", type=Path)
    p = sub.add_parser("annotate")
    p.add_argument("--records", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--annotator", required=True)
    p.add_argument("--date", required=True, help="YYYY-MM-DD of the marking session")
    p.add_argument("--edge-s", type=float, default=0.5)
    p.add_argument("--resume", action="store_true",
                   help="go on with an unfinished --out (see <out>.progress.json)")
    p = sub.add_parser("detect")
    p.add_argument("--records", type=Path, required=True)
    p.add_argument("--config", type=Path, default=ROOT / "configs/data/week05_huy.json")
    p.add_argument("--out", type=Path, required=True)
    p = sub.add_parser("compare")
    p.add_argument("--annotations", type=Path, required=True)
    p.add_argument("--detections", type=Path, required=True)
    p.add_argument("--config", type=Path, default=ROOT / "configs/data/week05_huy.json")
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--allow-synthetic-truth", action="store_true")
    p.add_argument("--annotations-without-provenance", action="store_true",
                   help="allow a hand-filled annotation CSV with no provenance "
                        "file; recorded in the output")
    p = sub.add_parser("repeat")
    p.add_argument("--first", type=Path, required=True, help="marks on main/")
    p.add_argument("--second", type=Path, required=True, help="marks on repeat/")
    p.add_argument("--export", type=Path, required=True, help="export.json")
    p.add_argument("--config", type=Path, default=ROOT / "configs/data/week05_huy.json")
    p.add_argument("--out", type=Path, required=True)
    p = sub.add_parser("gate")
    p.add_argument("--agreement", type=Path, required=True, help="compare output")
    p.add_argument("--export", type=Path, required=True, help="export.json")
    p.add_argument("--config", type=Path, default=ROOT / "configs/data/week05_huy.json")
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--repeatability", type=Path, help="repeat output")
    p.add_argument("--allow-synthetic-truth", action="store_true")
    args = parser.parse_args(argv)
    if args.command == "synth":
        print(run_synth(args.out))
    elif args.command == "export":
        print(run_export(args.raw, args.split_dir, args.fs_hz, args.config, args.out))
    elif args.command == "plot":
        print(run_plot(args.records, args.out, args.detections))
    elif args.command == "annotate":
        out = run_annotate(args.records, args.out, args.annotator, args.date,
                           args.edge_s, args.resume)
        print(out if out is not None else "Unfinished: run again with --resume")
    elif args.command == "detect":
        print(run_detect(args.records, args.config, args.out))
    elif args.command == "repeat":
        result = run_repeat(args.first, args.second, args.export, args.config,
                            args.out)
        print(json.dumps({"passed": result["passed"], **{
            f: {k: v[k] for k in ("matched", "mae_ms", "passed")}
            for f, v in result["fiducials"].items()}}, indent=2))
    elif args.command == "gate":
        result = run_gate(args.agreement, args.export, args.config, args.out,
                          args.repeatability, args.allow_synthetic_truth)
        print(json.dumps({"verdict": result["verdict"], **{
            f: {"winner": v["winner"], "confirmed": v["confirmed"]}
            for f, v in result["fiducials"].items()}}, indent=2))
    else:
        result = run_compare(args.annotations, args.detections, args.config, args.out,
                             args.allow_synthetic_truth,
                             args.annotations_without_provenance)
        print(json.dumps(result["summary"], indent=2))


if __name__ == "__main__":
    main()
