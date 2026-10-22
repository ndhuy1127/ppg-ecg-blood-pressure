"""Week 5 fiducial review: SYNTHETIC records, train/val export, plots, detection,
agreement.

Subcommands (each refuses to overwrite its output and writes provenance):

  synth     SYNTHETIC records with known R/foot times (code check only)
  export    small train/val subset of a raw PulseDB file + split v2 (never test)
  plot      PNG per record for manual review; detections hidden by default
  annotate  interactive window: Huy clicks R (ECG axis) and foot (PPG axis)
  detect    run every candidate R/foot method; CSV with one row per fiducial
  compare   sensitivity/PPV/bias/MAE of each method against manual marks

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
from software.signal_processing.fiducials import (  # noqa: E402
    FOOT_METHODS, R_METHODS, Channel, SignalConfig, detect,
)

SCRIPT_VERSION = "week05-fiducials-v1"
SYNTHETIC_VERSION = "week05-synthetic-records-v0"
RECORD_COLUMNS = ("record_id", "subject_id", "split", "source_type", "origin",
                  "ecg_fs_hz", "ppg_fs_hz", "file", "file_sha256")
CODE_FILES = ("scripts/week05_fiducials.py", "software/signal_processing/fiducials.py",
              "software/signal_processing/pat_validity.py",
              "software/evaluation/fiducial_agreement.py", "software/_provenance.py")
LIBRARIES = ("numpy", "scipy", "pandas", "matplotlib")


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

def synthetic_record(rr_s=1.0, duration_s=10.0, pat_s=0.2, rise_s=0.15, ecg_fs=500,
                     ppg_fs=125, noise_sd=0.0, wander=0.0, drop_beats=(),
                     drop_ppg_beats=(), seed=0):
    """Gaussian QRS with a T wave; PPG pulse = half-cosine rise then exponential
    decay.

    Truth: R at the Gaussian centre; foot at pulse onset (start of the rise).
    ``drop_beats`` removes beat k from both channels (pause); ``drop_ppg_beats``
    removes only its PPG pulse. Shapes are not physiological models.
    """
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
                + 0.3 * np.exp(-0.5 * ((et - r - 0.25) / 0.04) ** 2))
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


# --- PulseDB train/val export ------------------------------------------------

def select_review_rows(manifest, n_subjects, per_subject, seed):
    """Pick subjects of train/val by a seeded permutation, then their first rows.

    Uses only subject_id, split and raw_index: no BP column, no signal value.
    Test rows are dropped before the selection.
    """
    rows = manifest[manifest.split.isin(["train", "val"])]
    subjects = sorted(rows.subject_id.unique())
    order = np.random.default_rng(seed).permutation(len(subjects))
    chosen = [subjects[i] for i in order[:n_subjects]]
    picked = (rows[rows.subject_id.isin(chosen)].sort_values("raw_index")
              .groupby("subject_id", sort=True).head(per_subject))
    return picked.sort_values("raw_index")


def run_export(raw, split_dir, fs_hz, n_subjects, per_subject, seed, out):
    """The whole raw file is read and every row (test included) is re-hashed
    against the inventory, as in the B3 pipeline; only selected train/val rows
    are written, ECG/PPG only."""
    from software.data_io.split_manifest import file_sha256, read_manifest_bytes
    from software.pulsedb.pipeline import verify_inputs
    from software.pulsedb.reader import PulseDBReader

    _refuse_existing(out)
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
    segments = PulseDBReader(str(raw)).read()
    verify_inputs(manifest, inventory, segments)
    picked = select_review_rows(manifest, n_subjects, per_subject, seed)
    out = _new_dir(out)
    records = []
    for row in picked.itertuples():
        segment = segments[int(row.raw_index)]
        record_id = f"PDB_{row.split}_{int(row.raw_index)}"
        path = out / f"{record_id}.npz"
        # Only ECG and PPG are exported; ABP and labels stay in the raw file.
        np.savez(path, ecg=np.asarray(segment.ecg, float),
                 ppg=np.asarray(segment.ppg, float))
        records.append({"record_id": record_id, "subject_id": row.subject_id,
                        "split": row.split, "source_type": "PUBLIC_PULSEDB",
                        "origin": row.sample_id, "ecg_fs_hz": fs_hz, "ppg_fs_hz": fs_hz,
                        "file": path.name, "file_sha256": _sha256(path)})
    _write_csv(out / "records.csv", RECORD_COLUMNS, records)
    _write_json(out / "export.json", {
        "selection": {"n_subjects": n_subjects, "per_subject": per_subject,
                      "seed": seed, "splits": ["train", "val"],
                      "fs_hz_declared_by_caller": fs_hz},
        "provenance": provenance("export", {"raw": raw_sha256, **{
            k: report[k] for k in ("inventory_sha256", "manifest_sha256")}},
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


def run_annotate(records, out, annotator, annotated_on, edge_s):
    """Left click adds a mark at the clicked time (ECG axis = R, PPG axis = foot);
    right click removes the nearest mark on that axis. Close the window to go on.

    The output is created before the first window and each record is written
    as soon as its window closes, so a crash or an existing ``--out`` never
    costs a finished marking session.
    """
    import matplotlib.pyplot as plt

    if not annotator.strip() or is_synthetic_annotator(annotator):
        raise ValueError("annotator must be the person who marks")
    sidecar = _sidecar(out)
    _refuse_existing(out, sidecar)
    inputs, source_types = _records_inputs(records)
    outside = {}
    with _new_file(out) as stream:
        writer = csv.DictWriter(stream, fieldnames=ANNOTATION_COLUMNS,
                                lineterminator="\n")
        writer.writeheader()
        stream.flush()
        for row, ecg, ppg in load_records(records):
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
            outside[row.record_id] = len(clicks) - len(inside)
            writer.writerows(clicks_to_rows(row, inside, region, annotator,
                                            annotated_on))
            stream.flush()
    _write_json(sidecar, {
        "annotator": annotator, "annotated_on": annotated_on, "edge_s": edge_s,
        "clicks_outside_region_dropped": outside,
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
        "channel_issues": issues,
        "output_sha256": _sha256(out),
        "provenance": provenance(
            "detect", {**inputs, "config": text_sha256(config_bytes)}, source_types),
    })
    return out


def run_compare(annotations_csv, detections_csv, config_path, out,
                allow_synthetic_truth=False):
    """The config must be the one ``detect`` used: its tolerances are read here
    and its signal settings produced the detections."""
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
    read = {"dtype": {"record_id": str, "split": str, "fiducial": str},
            "keep_default_na": False, "na_values": [""]}
    annotations = pd.read_csv(annotations_csv, **read)
    detections = pd.read_csv(detections_csv, dtype={"record_id": str, "split": str,
                                                     "method": str, "fiducial": str})
    result = agreement(annotations, detections, config["agreement"]["tolerance_s"],
                       allow_synthetic_truth=allow_synthetic_truth)
    result["provenance"] = provenance("compare", {
        "annotations": _sha256(annotations_csv),
        "detections": _sha256(detections_csv),
        "detections_provenance": _sha256(detect_sidecar),
        "config": text_sha256(config_bytes)},
        detect_info["provenance"]["source_types"])
    result["detect_provenance"] = detect_info["provenance"]
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
    p.add_argument("--subjects", type=int, default=5)
    p.add_argument("--per-subject", type=int, default=2)
    p.add_argument("--seed", type=int, default=20261021)
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
    args = parser.parse_args(argv)
    if args.command == "synth":
        print(run_synth(args.out))
    elif args.command == "export":
        print(run_export(args.raw, args.split_dir, args.fs_hz, args.subjects,
                         args.per_subject, args.seed, args.out))
    elif args.command == "plot":
        print(run_plot(args.records, args.out, args.detections))
    elif args.command == "annotate":
        print(run_annotate(args.records, args.out, args.annotator, args.date,
                           args.edge_s))
    elif args.command == "detect":
        print(run_detect(args.records, args.config, args.out))
    else:
        result = run_compare(args.annotations, args.detections, args.config, args.out,
                             args.allow_synthetic_truth)
        print(json.dumps(result["summary"], indent=2))


if __name__ == "__main__":
    main()
