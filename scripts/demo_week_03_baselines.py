"""Run deterministic SYNTHETIC B0/B1 examples; never read research data."""

import json
import platform
import sys
from dataclasses import asdict
from pathlib import Path

import numpy as np

SEED = 20261003


def run_demo() -> dict:
    # Import after direct-file execution has made the repo package available.
    from software.evaluation.bp_metrics import evaluate_bp
    from software.models.constant_baselines import (
        PersonalMeanBaseline,
        PopulationMeanBaseline,
    )

    rng = np.random.default_rng(SEED)
    train_ids = np.array(["SYN_TRAIN_A", "SYN_TRAIN_A", "SYN_TRAIN_B"])
    evaluation_ids = np.array(["SYN_EVAL_A", "SYN_EVAL_A", "SYN_EVAL_B"])
    train = np.array([120.0, 80.0]) + rng.normal(0, 5, (3, 2))
    evaluation = np.array([125.0, 82.0]) + rng.normal(0, 5, (3, 2))
    calibration_ids = np.array(["SYN_EVAL_A", "SYN_EVAL_A", "SYN_EVAL_B"])
    calibration = np.array([122.0, 81.0]) + rng.normal(0, 3, (3, 2))
    # These clocks and row IDs are deliberately synthetic, not PulseDB metadata.
    calibration_times = np.array([0, 1, 0])
    evaluation_times = np.array([2, 3, 2])
    calibration_row_ids = {"SYN_CAL_0", "SYN_CAL_1", "SYN_CAL_2"}
    evaluation_row_ids = {"SYN_EVAL_0", "SYN_EVAL_1", "SYN_EVAL_2"}
    assert not set(train_ids) & set(evaluation_ids)
    assert not calibration_row_ids & evaluation_row_ids
    for subject in np.unique(evaluation_ids):
        assert calibration_times[calibration_ids == subject].max() < (
            evaluation_times[evaluation_ids == subject].min()
        )
    b0 = PopulationMeanBaseline().fit(train)
    b1 = PersonalMeanBaseline().fit(calibration_ids, calibration)
    return {
        "source_type": "SYNTHETIC",
        "purpose": "Code/formula demonstration only; no device or model evidence",
        "seed": SEED,
        "python": platform.python_version(),
        "numpy": np.__version__,
        "columns": ["SBP", "DBP"],
        "unit": "mmHg",
        "error": "prediction - reference",
        "sd_ddof": 1,
        "sd_if_n_lt_2": "null (undefined)",
        "B0": asdict(evaluate_bp(evaluation, b0.predict(3), evaluation_ids)),
        "B1": asdict(evaluate_bp(evaluation, b1.predict(evaluation_ids), evaluation_ids)),
    }


def main() -> None:
    print(json.dumps(run_demo(), indent=2, allow_nan=False))


if __name__ == "__main__":
    if not __package__:
        # Run Python File starts with scripts/ on sys.path, rather than repo root.
        sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    main()
