"""Check criterion A10 (per-packet ECG anchor residual) on one logger recording.

Reads a ``packet-logger-v3`` recording directory (verified against its manifest)
and writes ONE new JSON file outside ``data/raw/`` with the result of
``software/device/ecg_anchor_residual.py`` (method ``ecg-anchor-residual-v1``,
window 10 s, limit 0.5 ms; hardware/test_reports/sync_10min_test_plan.md section
11.2) and its provenance. Refuses to overwrite. Raw data are never changed.
Results on SYNTHETIC recordings only verify code.

    python scripts/check_ecg_anchor_residual.py --recording runs/bringup_v1/<dir> \
        --output runs/ecg_anchor_residual/<name>.json
"""

import argparse
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from software._provenance import text_file_sha256  # noqa: E402
from software.device import ecg_anchor_residual as a10  # noqa: E402
from software.device import session_ingest as si  # noqa: E402

CODE = ("scripts/check_ecg_anchor_residual.py", "software/__init__.py",
        "software/device/__init__.py", "software/device/ecg_anchor_residual.py",
        "software/device/session_ingest.py", "software/_provenance.py")


def _git(*args):
    try:
        return subprocess.check_output(["git", *args], cwd=REPO, text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def check_output(output, raw_root=None):
    output = Path(output).resolve()
    raw_root = Path(raw_root or REPO / "data" / "raw").resolve()
    if output == raw_root or raw_root in output.parents:
        raise ValueError("Derived output never goes inside data/raw/")
    if output.exists():
        raise ValueError(f"Output {output} exists; choose a new file")
    return output


def run(recording_dir, output, raw_root=None):
    output = check_output(output, raw_root)
    recording = si.load_recording(recording_dir)
    manifest = recording["manifest"]
    result = a10.check(recording["packets"])
    result["provenance"] = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "recording": str(Path(recording_dir)),
        "raw_sha256": manifest["raw"]["sha256"],
        "manifest_sha256": si.sha256_file(Path(recording_dir) / "session_manifest.json"),
        "packets_csv_sha256": manifest["outputs_sha256"]["packets.csv"],
        "firmware_version": manifest.get("firmware_version"),
        "code_sha256": {c: text_file_sha256(REPO / c) for c in CODE},
        "git_commit": _git("rev-parse", "HEAD"),
        "git_dirty": bool(_git("status", "--porcelain")),
        "python": platform.python_version(),
        "source_type": manifest["source_type"],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    with open(output, "x", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2, sort_keys=True)
        handle.write("\n")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--recording", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path, help="New JSON file")
    args = parser.parse_args()
    result = run(args.recording, args.output)
    print(json.dumps({"output": str(args.output), "passed": result["passed"],
                      "sessions": [{k: s[k] for k in (
                          "session_id", "packets_scored", "packets_not_yet_scored",
                          "packets_not_scored", "packets_flagged",
                          "max_abs_residual_us", "p99_abs_residual_us")}
                          for s in result["sessions"]]}, indent=2))


if __name__ == "__main__":
    main()
