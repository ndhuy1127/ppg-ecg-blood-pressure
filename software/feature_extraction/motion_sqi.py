"""Motion SQI from the wrist IMU (``motion-sqi-v0``): a strong-motion flag.

Pure functions on uniformly sampled arrays; nothing here reads files, BP, ABP
or labels. The flag says that strong motion was seen; ``no_motion_detected``
does not certify a clean PPG/ECG window (gripping can corrupt PPG with little
acceleration, slow motion is damped by the 0.5 Hz high-pass, and a left-wrist
IMU says nothing about EMG on the right arm). Thresholds are engineering drafts
(``ENGINEERING_DRAFT_NOT_TEST_TUNED``), to be locked on the G2 pilot before
main collection. Definition: docs/protocol/protocol_outline_v0.2.md, SQI
criterion 5.

Inputs are (n, 3) arrays in sensor axes: acceleration in g, angular rate in
deg/s, already on one time base at ``fs_hz`` (time mapping is done upstream).
A missing sample is a row of NaN; samples are never interpolated.
"""

from dataclasses import asdict, dataclass

import numpy as np
from scipy.signal import butter, sosfiltfilt

from software.signal_processing.fiducials import finite_number

VERSION = "motion-sqi-v0"
# One LSB below full scale counts as clipped (int16 at +32767 or -32768).
CLIP_FRACTION = 32767 / 32768


@dataclass(frozen=True)
class MotionConfig:
    fs_hz: float = 100.0
    highpass_hz: float = 0.5
    lowpass_hz: float = 10.0
    filter_order: int = 2
    burst_s: float = 1.0
    step_s: float = 0.1
    percentile: float = 95.0
    acc_threshold_g: float = 0.15
    gyro_threshold_dps: float = 20.0
    acc_range_g: float = 4.0
    gyro_range_dps: float = 500.0
    calibration_min_s: float = 30.0
    status: str = "ENGINEERING_DRAFT_NOT_TEST_TUNED"

    def __post_init__(self):
        fs = finite_number(self.fs_hz, "fs_hz")
        if fs <= 0:
            raise ValueError("fs_hz must be positive")
        low = finite_number(self.highpass_hz, "highpass_hz")
        high = finite_number(self.lowpass_hz, "lowpass_hz")
        if not 0 < low < high < fs / 2:
            raise ValueError("Need 0 < highpass_hz < lowpass_hz < fs_hz / 2")
        order = self.filter_order
        if (isinstance(order, bool) or not isinstance(order, int)
                or not 1 <= order <= 8):
            raise ValueError("filter_order must be an integer in [1, 8]")
        burst = finite_number(self.burst_s, "burst_s")
        step = finite_number(self.step_s, "step_s")
        if not (0 < step <= burst and round(burst * fs) >= 2 and round(step * fs) >= 1):
            raise ValueError("Need 0 < step_s <= burst_s, both at least one sample")
        if not 0 < finite_number(self.percentile, "percentile") <= 100:
            raise ValueError("percentile must be in (0, 100]")
        for name in ("acc_threshold_g", "gyro_threshold_dps", "acc_range_g",
                     "gyro_range_dps", "calibration_min_s"):
            if finite_number(getattr(self, name), name) <= 0:
                raise ValueError(f"{name} must be positive")
        if not isinstance(self.status, str) or not self.status:
            raise ValueError("status must be nonempty text")


def _xyz(values, name):
    # Checked before np.asarray, which drops the mask.
    if np.ma.isMaskedArray(values):
        raise ValueError(f"{name} must not be a masked array; masks are not imputed")
    values = np.asarray(values, dtype=float)
    if values.ndim != 2 or values.shape[1] != 3:
        raise ValueError(f"{name} must be an (n, 3) array")
    return values


def _filters(config):
    def design(cutoff, kind):
        return butter(config.filter_order, cutoff, kind, fs=config.fs_hz, output="sos")
    return design(config.highpass_hz, "highpass"), design(config.lowpass_hz, "lowpass")


def _min_length(sos):
    # Shortest input that sosfiltfilt can pad with its default odd extension.
    return 3 * (2 * len(sos) + 1) + 1


def _burst(values, config):
    """Largest ``percentile`` over sliding ``burst_s`` sub-windows (``step_s``)."""
    size = int(round(config.burst_s * config.fs_hz))
    step = int(round(config.step_s * config.fs_hz))
    if len(values) < size:
        return None
    return float(max(np.percentile(values[i:i + size], config.percentile)
                     for i in range(0, len(values) - size + 1, step)))


def _summary(values, threshold, config):
    burst = _burst(values, config)
    return {
        "burst": burst,
        "window_percentile": float(np.percentile(values, config.percentile)),
        "fraction_above": float(np.mean(values > threshold)),
        "max": float(values.max()),
        "above": burst is not None and burst > threshold,
    }


def _branch_problems(values, window, full_range, sos_min):
    problems = []
    if not np.isfinite(values).all():
        problems.append("gap_in_context")
    elif (np.abs(values[window]) >= full_range * CLIP_FRACTION).any():
        problems.append("clipping")
    if len(values) < sos_min:
        problems.append("context_too_short")
    return problems


def gyro_bias(gyro_dps, config=MotionConfig()):
    """Gyro bias from a segment the operator confirmed as rest (M0, arm on table).

    Returns the per-axis median and, as checks, the spread (median absolute
    deviation of the speed after removing the median) and the difference
    between the medians of the two halves. The bias is None, with reasons,
    when the segment is shorter than ``calibration_min_s``, has gaps or
    clipping, or itself shows motion by the same burst rule as the windows.
    The segment is never searched for its stillest part.
    """
    gyro = _xyz(gyro_dps, "gyro_dps")
    reasons = []
    if len(gyro) < config.calibration_min_s * config.fs_hz:
        reasons.append("calibration_too_short")
    if not np.isfinite(gyro).all():
        reasons.append("gap")
    elif (np.abs(gyro) >= config.gyro_range_dps * CLIP_FRACTION).any():
        reasons.append("clipping")
    if reasons:
        return {"version": VERSION, "bias_dps": None, "reasons": reasons}
    median = np.median(gyro, axis=0)
    half = len(gyro) // 2
    halves = np.median(gyro[half:], axis=0) - np.median(gyro[:half], axis=0)
    _, low = _filters(config)
    speed = np.linalg.norm(sosfiltfilt(low, gyro - median, axis=0), axis=1)
    burst = _burst(speed, config)
    if burst is not None and burst > config.gyro_threshold_dps:
        reasons.append("calibration_motion")
    return {
        "version": VERSION,
        "bias_dps": None if reasons else median.tolist(),
        "median_dps": median.tolist(),
        "spread_dps": float(np.median(np.abs(speed - np.median(speed)))),
        "half_difference_dps": float(np.linalg.norm(halves)),
        "calibration_burst_dps": burst,
        "reasons": reasons,
    }


def motion_window(acc_g, gyro_dps, window, bias_dps, config=MotionConfig()):
    """Motion status of ``window`` = (start, stop) sample indices of the arrays.

    The whole arrays are the filtering context: pass enough samples around the
    window, but never past the start of cuff inflation (t0). Status:
    ``motion`` when an evaluable branch is above its threshold;
    ``no_motion_detected`` only when BOTH branches are evaluable and below;
    otherwise ``not_evaluable``. A missing bias makes the gyro branch not
    evaluable, so accelerometer alone can flag motion but never clear a window.
    """
    acc = _xyz(acc_g, "acc_g")
    gyro = _xyz(gyro_dps, "gyro_dps")
    if len(acc) != len(gyro):
        raise ValueError("acc_g and gyro_dps must have the same length")
    start, stop = window
    if (any(isinstance(v, bool) or not isinstance(v, (int, np.integer)) for v in window)
            or not 0 <= start < stop <= len(acc)):
        raise ValueError("window must be (start, stop) indices inside the arrays")
    span = slice(start, stop)
    high, low = _filters(config)
    sos_min = max(_min_length(high), _min_length(low))
    branches = {}

    acc_problems = _branch_problems(acc, span, config.acc_range_g, sos_min)
    if acc_problems:
        branches["acc"] = {"evaluable": False, "reasons": acc_problems}
    else:
        moving = np.linalg.norm(
            sosfiltfilt(low, sosfiltfilt(high, acc, axis=0), axis=0), axis=1)[span]
        branches["acc"] = {"evaluable": True, "reasons": [],
                           **_summary(moving, config.acc_threshold_g, config)}

    gyro_problems = _branch_problems(gyro, span, config.gyro_range_dps, sos_min)
    if bias_dps is None:
        gyro_problems.append("no_gyro_bias")
    if gyro_problems:
        branches["gyro"] = {"evaluable": False, "reasons": gyro_problems}
    else:
        bias = np.asarray(bias_dps, dtype=float)
        if np.ma.isMaskedArray(bias_dps) or bias.shape != (3,) or (
            not np.isfinite(bias).all()
        ):
            raise ValueError("bias_dps must be three finite values")
        speed = np.linalg.norm(sosfiltfilt(low, gyro - bias, axis=0), axis=1)[span]
        branches["gyro"] = {"evaluable": True, "reasons": [],
                            **_summary(speed, config.gyro_threshold_dps, config)}

    for branch in branches.values():
        if branch["evaluable"] and branch["burst"] is None:
            branch.update(evaluable=False, reasons=["window_shorter_than_burst"])
    if any(b["evaluable"] and b["above"] for b in branches.values()):
        status = "motion"
    elif all(b["evaluable"] for b in branches.values()):
        status = "no_motion_detected"
    else:
        status = "not_evaluable"
    return {"version": VERSION, "status": status, "window": [start, stop],
            "acc": branches["acc"], "gyro": branches["gyro"],
            "config": asdict(config)}
