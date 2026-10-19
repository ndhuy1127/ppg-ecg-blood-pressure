"""Label-blind ECG/PPG summary statistics: Linh's first B3 feature set.

Inputs are only the ECG and PPG vectors of one segment. ABP, SBP/DBP, subject
IDs and hashes are never passed in, so they cannot become predictors. Values
keep the source amplitude units (PulseDB ECG_F/PPG_F units are unverified).
"""

import numpy as np

VERSION = "pulsedb-simple-stats-v0"
CHANNELS = ("ecg", "ppg")
STATISTICS = ("mean", "std", "min", "max", "range", "rms")
FEATURE_NAMES = tuple(
    f"{channel}_{statistic}" for channel in CHANNELS for statistic in STATISTICS
)


def _signal(values, name):
    array = np.asarray(values)
    if array.ndim != 1 or array.size == 0 or array.dtype.kind not in "iuf":
        raise ValueError(f"{name} must be a nonempty 1-D numeric vector")
    array = array.astype(np.float64)
    if not np.isfinite(array).all():
        raise ValueError(f"{name} contains NaN or infinity")
    return array


def extract_features(ecg, ppg) -> dict[str, float]:
    """Return the 12 features in FEATURE_NAMES order; population std (ddof=0)."""
    features = {}
    for channel, values in zip(CHANNELS, (ecg, ppg)):
        signal = _signal(values, channel)
        with np.errstate(over="ignore", invalid="ignore"):
            stats = {
                "mean": np.mean(signal), "std": np.std(signal),
                "min": np.min(signal), "max": np.max(signal),
                "range": np.ptp(signal), "rms": np.sqrt(np.mean(signal ** 2)),
            }
        for statistic in STATISTICS:
            value = float(stats[statistic])
            if not np.isfinite(value):
                raise ValueError(f"{channel}_{statistic} overflowed")
            features[f"{channel}_{statistic}"] = value
    return features


def feature_matrix(segments) -> np.ndarray:
    """Read only .ecg/.ppg of each segment; one row per segment, input order."""
    rows = [extract_features(segment.ecg, segment.ppg) for segment in segments]
    if not rows:
        raise ValueError("No segments to extract features from")
    return np.array([[row[name] for name in FEATURE_NAMES] for row in rows])
