
import numpy as np


def extract_features(segment):
    """Extract 12 simple features from ECG and PPG signals."""
    features = {}

    for name in ("ecg", "ppg"):
        signal = np.asarray(getattr(segment, name), dtype=float)

        if signal.size == 0:
            raise ValueError(f"{name} signal is empty")

        if not np.all(np.isfinite(signal)):
            raise ValueError(f"{name} signal contains NaN or infinity")

        features[f"{name}_mean"] = float(np.mean(signal))
        features[f"{name}_std"] = float(np.std(signal))
        features[f"{name}_min"] = float(np.min(signal))
        features[f"{name}_max"] = float(np.max(signal))
        features[f"{name}_range"] = float(np.ptp(signal))
        features[f"{name}_rms"] = float(np.sqrt(np.mean(signal ** 2)))

    return features

