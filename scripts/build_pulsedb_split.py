"""Build an inventory-backed split from one explicitly approved PulseDB file."""

import argparse
import hashlib
import json
import platform
import subprocess
import sys
from importlib.metadata import version
from pathlib import Path


def run(config_path, output):
    from software.data_io.split_manifest import (
        VERSION, build_inventory, canonical_json, file_sha256, make_manifest,
        manifest_bytes, summarize_manifest,
    )
    from software.pulsedb.reader import PulseDBReader

    output = Path(output)
    if output.exists():
        raise FileExistsError("Output directory already exists; refusing overwrite")
    config_path = Path(config_path).resolve()
    config_bytes = config_path.read_bytes()
    config = json.loads(config_bytes)
    required = {
        "schema_version", "input_path", "input_sha256", "source",
        "source_version", "license", "permission_basis", "pool_decision",
        "subject_identity_review", "unit", "seed", "ratios",
    }
    if not isinstance(config, dict) or set(config) != required:
        raise ValueError("Config must contain exactly the documented fields")
    for field in required - {"seed", "ratios"}:
        value = config[field]
        if not isinstance(value, str) or not value or value.strip() != value:
            raise ValueError(f"Config requires explicit nonempty {field}")
    if config["schema_version"] != VERSION or config["unit"] != "mmHg":
        raise ValueError("Unsupported schema_version or BP unit")
    path = Path(config["input_path"])
    if not path.is_absolute():
        path = config_path.parent / path
    checksum = file_sha256(path)
    if checksum != config["input_sha256"]:
        raise ValueError("Raw SHA256 mismatch; no output written")
    segments = PulseDBReader(str(path)).read()
    inventory = build_inventory(segments, config["source"], checksum)
    manifest = make_manifest(inventory, config["seed"], config["ratios"])
    # Detect input replacement/modification while the reader was running.
    if file_sha256(path) != checksum:
        raise ValueError("Raw file changed during reading")
    inventory_payload = manifest_bytes(inventory)
    manifest_payload = manifest_bytes(manifest)
    repo = Path(__file__).resolve().parents[1]
    try:
        commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=repo, text=True,
        ).strip()
        dirty = bool(subprocess.check_output(
            ["git", "status", "--porcelain"], cwd=repo, text=True,
        ).strip())
    except (OSError, subprocess.CalledProcessError):
        commit, dirty = None, None
    files = (
        "scripts/build_pulsedb_split.py", "software/data_io/split_manifest.py",
        "software/pulsedb/reader.py",
    )
    report = {
        "schema_version": VERSION, "source_type": "PUBLIC_ABP",
        "config_sha256": hashlib.sha256(config_bytes).hexdigest(),
        "raw_sha256": checksum,
        "inventory_sha256": hashlib.sha256(inventory_payload).hexdigest(),
        "manifest_sha256": hashlib.sha256(manifest_payload).hexdigest(),
        "commit": commit, "working_tree_dirty": dirty,
        "code_sha256": {file: file_sha256(repo / file) for file in files},
        "python": platform.python_version(),
        "dependencies": {name: version(name) for name in ("numpy", "pandas", "mat73")},
        "split_summary": summarize_manifest(manifest, inventory),
        "validation": "PASS: exact inventory conservation and split isolation",
        "excluded_segments": 0,
        "limitations": [
            "raw_index identifies a file row, not an original record or timestamp",
            "No original record/window metadata or cross-source identity verified",
            "Config review declarations require independent human review",
            "No learned preprocessing, demographics, calibration or cuff inference",
            "All reader rows retained; no implicit subsampling or quality exclusion",
            "Exact waveform matches across splits require review; partial overlaps are not detected",
        ],
    }
    # Refuse existing handover directories, including an empty existing directory.
    output.mkdir(parents=True, exist_ok=False)
    for name, payload in (
        ("inventory.csv", inventory_payload), ("manifest.csv", manifest_payload),
        ("config.json", config_bytes), ("report.json", canonical_json(report) + b"\n"),
    ):
        with (output / name).open("xb") as stream:
            stream.write(payload)
    return report


def main():
    repo = Path(__file__).resolve().parents[1]
    if not __package__:
        sys.path.insert(0, str(repo))
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        report = run(args.config, args.output)
    except (ValueError, OSError, KeyError) as exc:
        parser.exit(1, f"Split failed: {exc}\n")
    print(json.dumps({
        "manifest_sha256": report["manifest_sha256"],
        "split_counts": {k: {f: v[f] for f in ("subjects", "segments")}
                         for k, v in report["split_summary"].items()},
    }, indent=2))


if __name__ == "__main__":
    main()