"""SYNTHETIC checks of motion-sqi-v0: they verify code, not detection on people."""

from dataclasses import replace

import numpy as np
import pytest

from software.feature_extraction.motion_sqi import (
    MotionConfig, gyro_bias, motion_window,
)

CONFIG = MotionConfig()
FS = CONFIG.fs_hz
T = np.arange(int(30 * FS)) / FS
WINDOW = (int(10 * FS), int(20 * FS))  # 10 s inside 30 s of context
BIAS = [0.4, -0.3, 0.2]


def rest(seed=0):
    rng = np.random.default_rng(seed)
    acc = np.tile([0.0, 0.0, 1.0], (len(T), 1)) + rng.normal(0, 0.002, (len(T), 3))
    gyro = np.tile(BIAS, (len(T), 1)) + rng.normal(0, 0.1, (len(T), 3))
    return acc, gyro


def test_rest_is_no_motion_detected():
    acc, gyro = rest()
    result = motion_window(acc, gyro, WINDOW, BIAS)
    assert result["status"] == "no_motion_detected"
    assert result["acc"]["burst"] < 0.01 and result["gyro"]["burst"] < 1
    assert result["config"]["status"] == "ENGINEERING_DRAFT_NOT_TEST_TUNED"


@pytest.mark.parametrize("duration", [0.2, 0.3, 0.5])
def test_short_burst_is_caught_although_the_window_percentile_misses_it(duration):
    acc, gyro = rest()
    k = (T >= 15) & (T < 15 + duration)
    acc[k, 0] += 0.5 * np.sin(2 * np.pi * 5 * (T[k] - 15))
    result = motion_window(acc, gyro, WINDOW, BIAS)
    assert result["status"] == "motion"
    assert result["acc"]["burst"] > CONFIG.acc_threshold_g
    # A 95th percentile over the whole 10 s would have called it still.
    assert result["acc"]["window_percentile"] < CONFIG.acc_threshold_g


def test_single_spike_is_not_motion():
    acc, gyro = rest()
    acc[1500, 0] += 1.0
    result = motion_window(acc, gyro, WINDOW, BIAS)
    assert result["status"] == "no_motion_detected"
    assert result["acc"]["max"] > result["acc"]["burst"]


def test_slow_rotation_needs_the_gyro():
    # 90 degrees about x at 30 deg/s (12-15 s): gravity moves too slowly for the
    # 0.5 Hz high-pass, the gyro sees 30 deg/s.
    acc, gyro = rest()
    angle = np.clip((T - 12) * np.deg2rad(30), 0, np.pi / 2)
    acc[:, 1], acc[:, 2] = np.sin(angle), np.cos(angle)
    turning = (T >= 12) & (T < 15)
    gyro[turning, 0] += 30
    result = motion_window(acc, gyro, WINDOW, BIAS)
    assert not result["acc"]["above"] and result["gyro"]["above"]
    assert result["status"] == "motion"


def test_missing_bias_flags_motion_but_never_clears():
    acc, gyro = rest()
    quiet = motion_window(acc, gyro, WINDOW, None)
    assert quiet["status"] == "not_evaluable"
    assert quiet["gyro"]["reasons"] == ["no_gyro_bias"]
    k = (T >= 15) & (T < 15.5)
    acc[k, 0] += 0.5 * np.sin(2 * np.pi * 5 * (T[k] - 15))
    assert motion_window(acc, gyro, WINDOW, None)["status"] == "motion"


@pytest.mark.parametrize("where", ["window", "context"])
def test_gap_makes_both_branches_not_evaluable(where):
    acc, gyro = rest()
    row = 1500 if where == "window" else 200
    acc[row] = gyro[row] = np.nan  # a lost IMU sample is a row of NaN
    result = motion_window(acc, gyro, WINDOW, BIAS)
    assert result["status"] == "not_evaluable"
    assert result["acc"]["reasons"] == result["gyro"]["reasons"] == ["gap_in_context"]


def test_clipping_is_not_evaluable_not_motion():
    acc, gyro = rest()
    acc[1500, 2] = CONFIG.acc_range_g  # at full scale
    result = motion_window(acc, gyro, WINDOW, BIAS)
    assert result["acc"]["reasons"] == ["clipping"]
    assert result["status"] == "not_evaluable"
    gyro[1600, 0] = -CONFIG.gyro_range_dps
    assert motion_window(acc, gyro, WINDOW, BIAS)["gyro"]["reasons"] == ["clipping"]


def test_window_shorter_than_one_burst_is_not_evaluable():
    acc, gyro = rest()
    result = motion_window(acc, gyro, (1000, 1050), BIAS)  # 0.5 s
    assert result["status"] == "not_evaluable"
    assert result["acc"]["reasons"] == ["window_shorter_than_burst"]


def test_gyro_bias_from_confirmed_rest():
    _, gyro = rest()
    bias = gyro_bias(gyro)
    assert bias["reasons"] == []
    assert bias["bias_dps"] == pytest.approx(BIAS, abs=0.02)
    assert bias["half_difference_dps"] < 0.05


def test_gyro_bias_refuses_short_gappy_clipped_or_moving_segments():
    _, gyro = rest()
    assert gyro_bias(gyro[:2000])["reasons"] == ["calibration_too_short"]
    gappy = gyro.copy()
    gappy[10] = np.nan
    assert gyro_bias(gappy)["reasons"] == ["gap"]
    clipped = gyro.copy()
    clipped[10, 1] = CONFIG.gyro_range_dps
    assert gyro_bias(clipped)["reasons"] == ["clipping"]
    moving = gyro.copy()
    moving[(T >= 5) & (T < 6), 2] += 40
    result = gyro_bias(moving)
    assert result["bias_dps"] is None and result["reasons"] == ["calibration_motion"]


@pytest.mark.parametrize("field,value", [
    ("fs_hz", 0), ("highpass_hz", 0), ("lowpass_hz", 60), ("filter_order", True),
    ("filter_order", 9), ("burst_s", 0.005), ("step_s", 2.0), ("percentile", 0),
    ("acc_threshold_g", -1), ("gyro_range_dps", float("nan")), ("status", ""),
])
def test_bad_config_is_rejected(field, value):
    with pytest.raises(ValueError):
        replace(CONFIG, **{field: value})


def test_bad_inputs_are_rejected():
    acc, gyro = rest()
    with pytest.raises(ValueError):
        motion_window(acc[:, :2], gyro, WINDOW, BIAS)
    with pytest.raises(ValueError):
        motion_window(acc, gyro[:-1], WINDOW, BIAS)
    for window in [(0, 0), (-1, 10), (0, len(T) + 1), (True, 10)]:
        with pytest.raises(ValueError):
            motion_window(acc, gyro, window, BIAS)
    with pytest.raises(ValueError):
        motion_window(acc, gyro, WINDOW, [0.0, 0.0])
