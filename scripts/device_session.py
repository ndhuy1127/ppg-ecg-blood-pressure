"""Ingest one logger recording and compute per-cuff features (device-session-v1).

Reads a ``packet-logger-v3`` recording directory (verified against its manifest),
the cuff log of the study session, and ``configs/data/device_session_v1.json``.
Writes, to a NEW directory outside ``data/raw/``:

- ``session_summary.json``: duration, real rate per channel, packet loss, cuffs,
  markers, hardware flags (docs/data_convention.md 4.5);
- ``timebase.csv``, ``events.csv``, ``cuffs.json``: sample-time fit per chain,
  device events, cuff windows (4.2-4.4);
- ``window_samples.csv``: samples of every stored cuff window with their time;
- ``cuff_features.csv`` / ``cuff_features.json``: one row per cuff for RQ1 (4.6)
  and the full fiducial/PAT/SQI output;
- ``provenance.json``.

Raw data are never changed. Results on SYNTHETIC recordings only verify code.
"""

import argparse
import csv
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from software._provenance import text_file_sha256  # noqa: E402
from software.device import features as fe  # noqa: E402
from software.device import session_ingest as si  # noqa: E402

FEATURE_COLUMNS = (
    "subject_id", "session_id", "recording", "event_id", "phase", "status",
    "safety_stop", "led_readjusted", "pilot", "sbp_mmhg", "dbp_mmhg", "window_pre_s", "ppg_color",
    "ppg_rise_time_ms", "ppg_width50_ms", "ppg_amplitude", "ppg_hr_bpm", "ecg_hr_bpm",
    "ecg_rmssd_ms", "pat_ms", "pat_sqi_v2_median_ms", "pat_n_valid", "flags",
    "source_type",
)
# Every local module the feature step imports (tests/test_rq1_analysis.py checks the
# list against the import graph); their hashes go to provenance.json.
CODE = ("scripts/device_session.py", "software/device/__init__.py",
        "software/device/session_ingest.py", "software/device/features.py",
        "software/device/synthetic_session.py", "software/feature_extraction/week04.py",
        "software/signal_processing/fiducials.py",
        "software/signal_processing/pat_validity.py", "software/data_io/live_monitor.py",
        "software/data_io/packet_receiver.py", "software/data_io/packet_wire.py",
        "software/data_io/command_wire.py", "software/_provenance.py")
CONFIG = "configs/data/device_session_v1.json"


def _git(*args):
    import subprocess

    try:
        return subprocess.check_output(["git", *args], cwd=REPO, text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def _csv(path, columns, rows):
    with open(path, "x", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n",
                                extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: "" if row.get(k) is None else row.get(k) for k in columns})


def _json(path, value):
    with open(path, "x", encoding="utf-8") as handle:
        json.dump(value, handle, indent=2, sort_keys=True, default=float)
        handle.write("\n")


def check_output(output, raw_root=None):
    output = Path(output).resolve()
    raw_root = Path(raw_root or REPO / "data" / "raw").resolve()
    if output == raw_root or raw_root in output.parents:
        raise ValueError("Derived output never goes inside data/raw/")
    if output.exists():
        raise ValueError(f"Output {output} exists; choose a new directory")
    return output


def run(recording_dir, cuff_log, config_path, output, session_index=0, raw_root=None):
    output = check_output(output, raw_root)
    config = json.loads(Path(config_path).read_text(encoding="utf-8"))
    if config.get("version") != si.VERSION:
        raise ValueError(f"Config version must be {si.VERSION}")
    recording = si.load_recording(recording_dir)
    manifest = recording["manifest"]
    series, timebase, flags = si.session_series(recording, session_index)
    events = si.session_events(recording, session_index)
    name = Path(recording_dir).resolve().name
    session = recording["decode"]["sessions"][session_index]
    cuffs = [c for c in si.read_cuff_log(cuff_log, name)
             if c["device_session_id"] == session["session_id"]]
    windows = si.cuff_windows(cuffs, events, config["window"])
    summary = si.summarize(recording, series, timebase, flags, events, windows,
                           session_index)
    identity = {"subject_id": manifest.get("subject_id"),
                "session_id": manifest.get("session_id"), "recording": name,
                "raw_sha256": manifest["raw"]["sha256"],
                "source_type": manifest["source_type"],
                "clock_id": recording["metadata"]["clock_id"]}
    packets = [p for p in recording["packets"] if p["session_id"] == session["session_id"]
               and p["chain_id"] is not None]
    results, rows = [], []
    for cuff in windows:
        result = fe.window_features(cuff, series, packets, session, config, identity)
        results.append(result)
        rows.append(fe.cuff_row(cuff, result, identity, config["pat_ppg_color"]))
    output.mkdir(parents=True)
    _json(output / "session_summary.json", summary)
    _csv(output / "timebase.csv", ("device_session_id", "channel", "chain_id", "n_anchors",
                                   "a_us", "b_us", "fs_hz", "residual_sd_us",
                                   "anchor_source", "nominal_rate", "latency_l_us"),
         timebase)
    _csv(output / "events.csv", ("device_session_id", "event_ordinal", "code", "name",
                                 "t_us"), events)
    _json(output / "cuffs.json", windows)
    with open(output / "window_samples.csv", "x", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(("event_id", "channel", "name", "chain_id", "sample_index",
                         "t_us", "value"))
        for cuff in windows:
            start, end = cuff["stored_window_us"]
            for key, s in series.items():
                for i in si.window_samples(s, start, end):
                    writer.writerow((cuff["event_id"], key, s.name, int(s.chain[i]),
                                     int(s.index[i]), f"{s.t_us[i]:.3f}", int(s.value[i])))
    _csv(output / "cuff_features.csv", FEATURE_COLUMNS, rows)
    _json(output / "cuff_features.json", results)
    _json(output / "provenance.json", {
        "version": si.VERSION, "features_version": fe.VERSION,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "recording": str(Path(recording_dir)), "raw_sha256": manifest["raw"]["sha256"],
        "manifest_sha256": si.sha256_file(Path(recording_dir) / "session_manifest.json"),
        "cuff_log_sha256": si.sha256_file(cuff_log),
        "config_sha256": text_file_sha256(config_path),
        "code_sha256": {c: text_file_sha256(REPO / c) for c in CODE},
        "git_commit": _git("rev-parse", "HEAD"),
        "git_dirty": bool(_git("status", "--porcelain")),
        "python": platform.python_version(), "source_type": manifest["source_type"],
        "session_index": session_index})
    return summary, rows


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--recording", required=True, type=Path)
    parser.add_argument("--cuff-log", required=True, type=Path)
    parser.add_argument("--config", type=Path,
                        default=REPO / "configs/data/device_session_v1.json")
    parser.add_argument("--output", required=True, type=Path, help="New directory")
    parser.add_argument("--session-index", type=int, default=0,
                        help="Position of the device session in decode.json")
    args = parser.parse_args()
    summary, rows = run(args.recording, args.cuff_log, args.config, args.output,
                        args.session_index)
    print(json.dumps({"output": str(args.output), "cuffs": len(rows),
                      "duration_s": summary["duration_s"],
                      "packets_missing_total": summary["packets_missing_total"]},
                     indent=2))


if __name__ == "__main__":
    main()
