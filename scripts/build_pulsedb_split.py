"""Build an inventory-backed split from one explicitly approved PulseDB file."""

import argparse
import hashlib
import json
import platform
import re
import subprocess
import sys
from collections import Counter
from contextlib import ExitStack
from importlib.metadata import version
from pathlib import Path

# PulseDB Subject: 7-character subject code + "_" + source (0 MIMIC-III,
# 1 VitalDB), per Generate_Subsets.m (docs/pulsedb_provenance.md section 7).
SUBJECT_ID_PATTERN = r"p\d{6}_([01])"


def subject_id_format(subject_ids):
    """Rows matching SUBJECT_ID_PATTERN and rows per source suffix; no IDs."""
    matches = [re.fullmatch(SUBJECT_ID_PATTERN, value) for value in subject_ids]
    suffixes = Counter(match.group(1) for match in matches if match)
    return {
        "pattern": SUBJECT_ID_PATTERN, "rows": len(matches),
        "matching_rows": sum(match is not None for match in matches),
        "rows_by_suffix": dict(sorted(suffixes.items())),
    }


def run(config_path, output):
    from software._provenance import text_file_sha256
    from software.data_io.split_manifest import (
        SUBSAMPLE_METHOD, VERSION, build_inventory, canonical_json, file_sha256,
        make_manifest, manifest_bytes, predictor_overlap, subject_list_sha256,
        subsample_subjects, summarize_manifest,
    )
    from software.pulsedb.h5_reader import PulseDBH5Reader
    from software.pulsedb.reader import PulseDBReader
    from software.pulsedb.validator import channel_order_check

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
    if not isinstance(config, dict) or not required <= set(config) <= (
        required | {"subject_subsample"}
    ):
        raise ValueError("Config must contain exactly the documented fields")
    subsample = config.get("subject_subsample")
    if subsample is not None and (
        not isinstance(subsample, dict) or set(subsample) != {"n_subjects", "seed"}
    ):
        raise ValueError("subject_subsample needs exactly n_subjects and seed")
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
    with ExitStack() as stack:
        if subsample is None:
            segments = PulseDBReader(str(path)).read()
            pool_ids = [segment.subject_id for segment in segments]
            subsample_report = None
        else:
            # Partial h5py reads: the Subject cells of every row, then only the
            # rows of the chosen subjects, block by block ({raw_index: segment},
            # file row numbers kept), so the pool never has to fit in RAM.
            reader = PulseDBH5Reader(str(path))
            pool_ids = reader.subject_ids()
            chosen = subsample_subjects(
                pool_ids, subsample["n_subjects"], subsample["seed"])
            keep = set(chosen)
            segments = stack.enter_context(
                reader.lazy([i for i, value in enumerate(pool_ids) if value in keep]))
            subsample_report = {
                "method": SUBSAMPLE_METHOD, **subsample,
                "pool_rows": len(pool_ids), "pool_subjects": len(set(pool_ids)),
                "selected_rows": len(segments),
                "selected_subjects_sha256": subject_list_sha256(chosen),
            }
        inventory = build_inventory(segments, config["source"], checksum)
        manifest = make_manifest(inventory, config["seed"], config["ratios"])
        # Identical ECG/PPG in two splits would leak through any model input.
        overlap = predictor_overlap(manifest, segments)
        if overlap["across_splits"]:
            raise ValueError(f"{overlap['across_splits']} identical ECG/PPG inputs "
                             "span splits; no output written")
        # Channel 2 must be ABP before any feature is computed: train labels only.
        train = manifest[manifest.split == "train"]
        channel_check = channel_order_check(
            (segments[int(i)] for i in train.raw_index), train.sbp, train.dbp)
    if not channel_check["pass"]:
        raise ValueError(f"Channel order check failed on train rows: {channel_check}")
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
        "software/pulsedb/reader.py", "software/pulsedb/h5_reader.py",
        "software/pulsedb/validator.py", "software/_provenance.py",
    )
    report = {
        "schema_version": VERSION, "source_type": "PUBLIC_ABP",
        "config_sha256": hashlib.sha256(config_bytes).hexdigest(),
        "raw_sha256": checksum,
        "inventory_sha256": hashlib.sha256(inventory_payload).hexdigest(),
        "manifest_sha256": hashlib.sha256(manifest_payload).hexdigest(),
        "commit": commit, "working_tree_dirty": dirty,
        # Tracked code hashed with LF endings (as in Git), not CRLF checkout bytes.
        "code_sha256_lf": {file: text_file_sha256(repo / file) for file in files},
        "python": platform.python_version(),
        "dependencies": {
            name: version(name) for name in ("numpy", "pandas", "mat73", "h5py")
        },
        "subject_subsample": subsample_report,
        "pool_subject_id_format": subject_id_format(pool_ids),
        "split_summary": summarize_manifest(manifest, inventory),
        "predictor_duplicates": overlap,
        "channel_order_check": channel_check,
        "validation": "PASS: exact inventory conservation and split isolation",
        "excluded_segments": 0,
        "limitations": [
            "raw_index identifies a file row, not an original record or timestamp",
            "No original record/window metadata or cross-source identity verified",
            "Config declarations (license, pool, identity) are not verified automatically",
            "No learned preprocessing, demographics, calibration or cuff inference",
            "split_summary gives counts only for test; test BP labels are not summarised",
            "All reader rows retained; no implicit subsampling or quality exclusion"
            if subsample is None else
            "Explicit subject subsample (subject_subsample): every row of the chosen "
            "subjects retained, raw_index is the file row; no quality exclusion",
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