"""Known-answer SYNTHETIC waveform checks; never a public baseline table."""

import argparse
import csv
import hashlib
import json
import platform
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from software._provenance import text_file_sha256, text_sha256  # noqa: E402
from software.evaluation.subject_bootstrap import BootstrapConfig, bootstrap_bp  # noqa: E402
from software.feature_extraction.week04 import SignalWindow, extract_windows  # noqa: E402
from software.signal_processing.fiducials import Channel, SignalConfig  # noqa: E402


def fixture_provenance(window):
    """Versioned hashes separate waveform content from timing/alignment evidence."""
    digest = hashlib.sha256()
    channel_metadata = {}
    for name in ("ecg", "ppg"):
        channel = getattr(window, name)
        values = np.asarray(channel.values, dtype="<f8")
        digest.update(json.dumps({"channel": name, "shape": list(values.shape)}, sort_keys=True).encode())
        digest.update(values.tobytes())
        timestamps = None if channel.timestamps is None else np.asarray(channel.timestamps, dtype="<f8")
        channel_metadata[name] = {
            "fs_hz": channel.fs_hz, "unit": channel.unit, "clock_id": channel.clock_id,
            "start_s": channel.start_s, "timestamp_unit": channel.timestamp_unit,
            "processing_delay_s": channel.processing_delay_s,
            "timestamps_shape": None if timestamps is None else list(timestamps.shape),
            "timestamps_sha256": None if timestamps is None else hashlib.sha256(timestamps.tobytes()).hexdigest(),
        }
    metadata = {"version": "analytic-fixture-input-v2", "channels": channel_metadata,
        "alignment_verified": window.alignment_verified, "alignment_basis": window.alignment_basis}
    encoded = json.dumps(metadata, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    waveform_hash = digest.hexdigest()
    metadata_hash = hashlib.sha256(encoded).hexdigest()
    return {"waveform_sha256": waveform_hash, "metadata_sha256": metadata_hash,
            "input_sha256": hashlib.sha256((waveform_hash + metadata_hash).encode()).hexdigest(),
            "hash_kind": "analytic fixture content, NOT raw file SHA256", "input_metadata": metadata}


def fixture(ecg_fs=250, ppg_fs=125, pat_s=0.2):
    """Gaussian R peaks at 1..8 s; piecewise-linear PPG feet R+0.2 s.

    Analytic pulse: rise 0.16 s, fall 0.24 s, amplitude 1; no simulated physiology.
    """
    r = np.arange(1, 9, dtype=float)
    et, pt = np.arange(10 * ecg_fs) / ecg_fs, np.arange(10 * ppg_fs) / ppg_fs
    ecg = sum(np.exp(-0.5 * ((et - t) / 0.015) ** 2) for t in r)
    ppg = np.zeros_like(pt)
    for foot in r + pat_s:
        x = pt - foot
        ppg += np.where((x >= 0) & (x <= 0.16), x / 0.16,
                        np.where((x > 0.16) & (x < 0.4), (0.4 - x) / 0.24, 0))
    digest = hashlib.sha256(ecg.tobytes() + ppg.tobytes()).hexdigest()
    metadata = {"sample_id": "SYN_WAVEFORM_001", "subject_id": "SYN_001", "split": "val",
                "source": "analytic_fixture_v1", "source_type": "SYNTHETIC",
                "source_sha256": digest, "raw_index": 0}
    window = SignalWindow(metadata,
        Channel(ecg, ecg_fs, "synthetic_unit", "SYN_CLOCK", processing_delay_s=0),
        Channel(ppg, ppg_fs, "synthetic_unit", "SYN_CLOCK", processing_delay_s=0),
        True, "Analytic common seconds axis; no upstream processing")
    return replace(window, metadata={**metadata, "source_sha256": fixture_provenance(window)["input_sha256"]}), r


def run(config_path, output, figure):
    # Like the other runners: never overwrite, so the Week 4 record in reports/
    # (fixture_checks.json, not reproducible from Git blobs) stays as it was.
    table = output.with_name("fixture_features.csv")
    existing = [str(path) for path in (output, table, figure) if path.exists()]
    if existing:
        raise FileExistsError(f"Output already exists; refusing overwrite: {existing}")
    config_bytes = config_path.read_bytes()
    config = json.loads(config_bytes)
    signal = SignalConfig(**config["signal"])
    window, expected_r = fixture()
    missing = replace(window, ppg=replace(window.ppg, values=np.array([], dtype=float)))
    flat = replace(window, ppg=replace(window.ppg, values=np.zeros_like(window.ppg.values)))
    nonfinite_values = window.ppg.values.copy()
    nonfinite_values[10] = np.nan
    nonfinite = replace(window, ppg=replace(window.ppg, values=nonfinite_values))
    unverified = replace(window, alignment_verified=False, alignment_basis="")
    windows = [window, missing, flat, nonfinite, unverified]
    provenance = [fixture_provenance(w) for w in windows]
    windows = [replace(w, metadata={**w.metadata, "sample_id": f"SYN_CASE_{i}",
        "source_sha256": provenance[i]["input_sha256"]})
        for i, w in enumerate(windows)]
    rows, summary = extract_windows(windows, signal)
    reference = np.tile([120., 80.], (6, 1))
    predictions = reference + np.array([[1, 2], [-1, 0], [3, -2], [2, 1], [0, 0], [-2, -1]])
    statistics = bootstrap_bp(reference, {"SYNTHETIC_KNOWN_ERRORS": predictions},
                              ["SYN_A", "SYN_A", "SYN_B", "SYN_B", "SYN_C", "SYN_C"],
                              BootstrapConfig(**config["bootstrap"]))
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(2, 1, figsize=(10, 5), sharex=True)
    et = np.arange(len(window.ecg.values)) / window.ecg.fs_hz
    pt = np.arange(len(window.ppg.values)) / window.ppg.fs_hz
    axes[0].plot(et, window.ecg.values, label="SYNTHETIC ECG")
    axes[1].plot(pt, window.ppg.values, label="SYNTHETIC PPG")
    marks = rows[0]["fiducials"]
    axes[0].scatter(marks["r_times_s"], np.interp(marks["r_times_s"], et, window.ecg.values), label="R candidates")
    axes[1].scatter(marks["foot_times_s"], np.interp(marks["foot_times_s"], pt, window.ppg.values), label="Tangent feet")
    for ri, fi, pat in marks["pairs"]:
        axes[1].annotate(f"{pat:.0f} ms", xy=(marks["foot_times_s"][fi], 0),
                         xytext=(marks["r_times_s"][ri], -0.22), arrowprops={"arrowstyle": "->"}, fontsize=7)
    for ax in axes:
        ax.legend(loc="upper right")
        ax.set_ylabel("synthetic unit")
    axes[1].set_xlabel("Common acquisition time (s)")
    axes[1].set_xlim(0.5, 4)
    fig.suptitle("SYNTHETIC analytic fixture — not public data or device validation")
    fig.tight_layout()
    figure.parent.mkdir(parents=True, exist_ok=True)
    # Fixed salt and no date keep the SVG bytes, and so figure_sha256, reproducible.
    with plt.rc_context({"svg.hashsalt": "week04-fixture"}):
        fig.savefig(figure, metadata={"Description": "Analytic fixture v1", "Date": None})
    plt.close(fig)
    report = {"source_type": "SYNTHETIC", "config_sha256": text_sha256(config_bytes),
        "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "dirty": bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip()),
        "environment": {"python": platform.python_version(), "numpy": np.__version__},
        "expected": {"r_times_s": expected_r.tolist(), "foot_times_s": (expected_r + 0.2).tolist(),
                     "pat_ms": 200, "rise_ms": 160, "width50_ms": 200, "hr_bpm": 60},
        "summary": summary, "rows": rows, "fixture_input_provenance": provenance,
        "synthetic_statistics_not_public_baselines": statistics,
        "figure_sha256": hashlib.sha256(figure.read_bytes()).hexdigest(),
        "public_results": "N/A: no raw waveform/alignment evidence or B3 predictions handed over"}
    output.parent.mkdir(parents=True, exist_ok=True)
    with table.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["source_type", "case", *rows[0]["features"], "flags"],
                                lineterminator="\n")
        writer.writeheader()
        for i, row in enumerate(rows):
            writer.writerow({"source_type": "SYNTHETIC", "case": i, **row["features"],
                             "flags": ";".join(row["flags"])})
    report["code_sha256"] = {str(path.relative_to(ROOT)).replace("\\", "/"):
        text_file_sha256(path) for path in (
            Path(__file__), ROOT / "software/signal_processing/fiducials.py",
            ROOT / "software/feature_extraction/week04.py", ROOT / "software/evaluation/subject_bootstrap.py",
            ROOT / "software/evaluation/bp_metrics.py", ROOT / "software/_bp_validation.py",
            ROOT / "software/data_io/split_manifest.py", ROOT / "software/_provenance.py")}
    report["fixture_table_sha256"] = hashlib.sha256(table.read_bytes()).hexdigest()
    output.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(summary))
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "configs/data/week04_huy.json")
    parser.add_argument("--output", type=Path, default=ROOT / "runs/demo_week04_huy/fixture_checks.json")
    parser.add_argument("--figure", type=Path,
                        default=ROOT / "runs/demo_week04_huy/week04_synthetic_fiducials.svg")
    args = parser.parse_args()
    run(args.config, args.output, args.figure)