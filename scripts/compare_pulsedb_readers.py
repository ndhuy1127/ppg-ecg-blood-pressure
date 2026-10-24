"""Check that the h5py reader returns the mat73 reader's rows for one PulseDB file.

Reads the whole file with both readers (mat73 needs it in RAM), so use a file
that fits in memory. Prints counts and mismatch totals only: no subject IDs,
labels or signal values.
"""

import argparse
import json
import math
import platform
import subprocess
import sys
from importlib.metadata import version
from pathlib import Path

SCALARS = ("subject_id", "gender", "age", "height_cm", "weight_kg", "bmi_kg_m2",
           "sbp", "dbp")
WAVEFORMS = ("ecg", "ppg", "abp")


def _same(left, right):
    if isinstance(left, float) and isinstance(right, float):
        return (math.isnan(left) and math.isnan(right)) or left == right
    return type(left) is type(right) and left == right


def compare(raw_path):
    import numpy as np

    from software.data_io.split_manifest import file_sha256
    from software.pulsedb.h5_reader import PulseDBH5Reader
    from software.pulsedb.reader import PulseDBReader

    checksum = file_sha256(raw_path)
    reference = PulseDBReader(str(raw_path)).read()
    h5 = PulseDBH5Reader(str(raw_path))
    candidate = h5.read()
    mismatches = {field: 0 for field in SCALARS + WAVEFORMS}
    if list(candidate) != list(range(len(reference))):
        raise ValueError("Row keys differ between readers")
    for i, expected in enumerate(reference):
        actual = candidate[i]
        for field in SCALARS:
            mismatches[field] += not _same(getattr(expected, field), getattr(actual, field))
        for field in WAVEFORMS:
            left, right = getattr(expected, field), getattr(actual, field)
            mismatches[field] += not (
                left.dtype == right.dtype and left.shape == right.shape
                and np.ascontiguousarray(left).tobytes() == right.tobytes()
            )
    ids = h5.subject_ids()
    id_mismatches = sum(a != b.subject_id for a, b in zip(ids, reference))
    if file_sha256(raw_path) != checksum:
        raise ValueError("Raw file changed during reading")
    return {
        "raw_sha256": checksum, "rows": len(reference),
        "subjects": len({segment.subject_id for segment in reference}),
        "row_mismatches": mismatches,
        "subject_ids_mismatches": id_mismatches + abs(len(ids) - len(reference)),
        "pass": not any(mismatches.values()) and not id_mismatches
        and len(ids) == len(reference),
    }


def main():
    repo = Path(__file__).resolve().parents[1]
    if not __package__:
        sys.path.insert(0, str(repo))
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, required=True, help="PulseDB .mat file")
    args = parser.parse_args()
    try:
        result = compare(args.raw)
    except (ValueError, OSError, KeyError) as exc:
        parser.exit(1, f"Comparison failed: {exc}\n")
    try:
        commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        commit = None
    result.update({
        "commit": commit, "python": platform.python_version(),
        "dependencies": {name: version(name) for name in ("numpy", "h5py", "mat73")},
    })
    print(json.dumps(result, indent=2))
    if not result["pass"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
