"""PAT feet anchored on R (fiducials.feet_after_r, rise-after-r-v1; draft device-foot-v1,
docs/protocol/device_ppg_foot_definition_v1.md section 3), on hand-built SYNTHETIC
PPG. A raised-cosine rise of 100 ms has zero slope at its onset, so the tangent foot
sits 18.2 ms after the set onset in every case: the tests check that offset stays
the same, not that it is zero.
"""

import sys
from pathlib import Path

import numpy as np
import pytest

from software.signal_processing.fiducials import SignalConfig, feet_after_r

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import demo_device_foot_cases as demo  # noqa: E402

CFG = SignalConfig(edge_s=0.0)
KW = dict(rise_min_fraction=0.3, ambiguous_fraction=0.15, search_s=0.9)
OFFSET = 0.0182  # tangent foot after a raised-cosine onset of 100 ms


def _rise(t, onset, width=0.10, height=1.0):
    x = np.clip((t - onset) / width, 0, 1)
    return height * 0.5 * (1 - np.cos(np.pi * x))


@pytest.mark.parametrize("index", range(4))
def test_hard_cases_keep_the_foot_on_the_first_rise(index):
    title, t, y = demo.cases()[index]
    feet, status, _ = feet_after_r(y, t, np.array([0.0]), CFG, **KW)
    assert status == ["ok"], title
    assert feet[0] == pytest.approx(demo.ONSET_S + OFFSET, abs=0.005), title
    assert feet[0] == pytest.approx(demo.draft_foot(t, y)[2], abs=1e-9), title


def test_beat_train_gives_one_foot_per_r_with_a_constant_offset():
    fs = 200.0
    t = np.arange(0, 12, 1 / fs)
    r = np.arange(0.5, 11.0, 0.8)
    pats = 0.15 + 0.05 * np.sin(np.arange(len(r)))  # 100-200 ms
    y = np.zeros_like(t)
    for ri, p in zip(r, pats):
        on = ri + p
        y += _rise(t, on) * (t < on + 0.1) + (t >= on + 0.1) * np.clip(
            1 - (t - on - 0.1) / 0.4, 0, 1)
    feet, status, _ = feet_after_r(y, t, r, CFG, **KW)
    assert status == ["ok"] * len(r)
    assert np.all(np.diff(feet) > 0)
    np.testing.assert_allclose(feet - (r + pats), OFFSET, atol=0.006)


def test_rise_too_early_is_out_of_range():
    t = np.arange(-0.5, 1.0, 1 / 200)
    y = _rise(t, 0.02) * (t < 0.12) + (t >= 0.12)  # foot about R + 38 ms
    assert feet_after_r(y, t, np.array([0.0]), CFG, **KW)[1] == ["out_of_range"]


def _train(fs=200.0, rr=0.8, n=10, pat=0.15, heights=None, widths=None):
    t = np.arange(0, rr * (n + 1), 1 / fs)
    r = rr * (np.arange(n) + 0.5)
    y = np.zeros_like(t)
    for k, ri in enumerate(r):
        h = 1.0 if heights is None else heights[k]
        w = 0.1 if widths is None else widths[k]
        on = ri + pat
        y += _rise(t, on, w, h) * (t < on + w) + (t >= on + w) * h * np.clip(
            1 - (t - on - w) / 0.4, 0, 1)
    return t, y, r


def test_small_rise_among_normal_beats_is_no_rise():
    heights = [1.0] * 10
    heights[4] = 0.1  # one beat climbs 10 % of the median pulse range
    t, y, r = _train(heights=heights)
    status = feet_after_r(y, t, r, CFG, **KW)[1]
    assert status[4] == "no_rise" and status.count("ok") == 9


def test_distant_artefact_does_not_change_the_scale():
    t, y, r = _train(n=10)
    clean = feet_after_r(y, t, r, CFG, **KW)
    spike = y.copy()
    spike[(t > 0.2) & (t < 0.3)] += 20.0  # before the first R, 20 times the pulse
    dirty = feet_after_r(spike, t, r, CFG, **KW)
    assert dirty[1] == clean[1] == ["ok"] * 10
    np.testing.assert_allclose(dirty[0], clean[0])


def test_flat_step_inside_the_upstroke_does_not_move_the_foot():
    fs = 200.0
    t = np.arange(-0.5, 1.2, 1 / fs)
    y = _rise(t, 0.15, 0.2) * (t < 0.35) + (t >= 0.35)
    base = feet_after_r(y, t, np.array([0.0]), CFG, **KW)
    k = int(np.searchsorted(t, 0.19))  # about 12 % of the height
    flat = y.copy()
    flat[k + 1] = flat[k]  # one flat 5 ms step
    stepped = feet_after_r(flat, t, np.array([0.0]), CFG, **KW)
    assert base[1] == stepped[1] == ["ok"]
    assert stepped[0][0] == pytest.approx(base[0][0], abs=0.002)


def test_real_notch_between_two_waves_is_not_bridged():
    # The taller later wave of demo case 4 starts after a 30 % dip lasting 60 ms.
    title, t, y = demo.cases()[3]
    feet, status, _ = feet_after_r(y, t, np.array([0.0]), CFG, **KW)
    assert status == ["ok"] and feet[0] < 0.25


def test_rise_cut_by_the_window_end_is_edge():
    t = np.arange(-0.5, 0.27, 1 / 200)  # the upstroke 0.20-0.30 s is not complete
    y = _rise(t, 0.20)
    assert feet_after_r(y, t, np.array([0.0]), CFG, **KW)[1] == ["edge"]


def test_no_rise_when_the_search_runs_past_the_window_end_is_edge():
    t = np.arange(-0.5, 0.3, 1 / 200)
    y = np.cos(t)  # falling after R, window ends before R + search_s
    assert feet_after_r(y, t, np.array([0.0]), CFG, **KW)[1] == ["edge"]


@pytest.mark.parametrize("width", [0.08, 0.10, 0.15, 0.20])
def test_tangent_offset_grows_with_the_rise_width(width):
    # Raised cosine of width w: steepest at w/2, so the foot is w (1/2 - 1/pi)
    # = 0.182 w after the onset. A change of upstroke shape between sessions moves
    # PAT by this much (device-foot-v1 section 6, limitation).
    t, y, r = _train(widths=[width] * 10)
    feet, status, _ = feet_after_r(y, t, r, CFG, **KW)
    assert status == ["ok"] * 10
    np.testing.assert_allclose(feet - (r + 0.15), width * (0.5 - 1 / np.pi), atol=0.004)


@pytest.mark.parametrize("first, expected", [(0.10, "second"), (0.20, "ambiguous"),
                                             (0.40, "first")])
def test_two_wave_outcome_follows_the_draft_thresholds(first, expected):
    # Two waves at fixed times (onsets R + 120 and R + 300 ms); only the earlier
    # wave's height changes. Below 15 % it is ignored, between 15 and 30 % it makes
    # the beat ambiguous, from 30 % it is the systolic rise. The thresholds are
    # drafts, locked on wrist recordings.
    t = np.arange(-0.5, 1.3, 1 / 200)
    w1 = _rise(t, 0.12, 0.08, first) * (t < 0.20) + (t >= 0.20) * first * np.clip(
        1 - (t - 0.20) / 0.05, 0, 1)
    w2 = _rise(t, 0.30) * (t < 0.40) + (t >= 0.40) * np.clip(1 - (t - 0.40) / 0.5, 0, 1)
    feet, status, per_r = feet_after_r(w1 + w2, t, np.array([0.0]), CFG, **KW)
    if expected == "ambiguous":
        assert status == ["ambiguous"]
    else:
        assert status == ["ok"]
        onset = 0.12 if expected == "first" else 0.30
        assert onset < feet[0] < onset + 0.03


def test_earlier_mid_sized_rise_in_range_makes_the_beat_ambiguous():
    t = np.arange(-0.5, 1.2, 1 / 200)
    small = _rise(t, 0.12, height=0.2) * (t < 0.22) + 0.2 * (t >= 0.22) * (t < 0.25) \
        + (t >= 0.25) * 0.2 * np.clip(1 - (t - 0.25) / 0.05, 0, 1)
    big = _rise(t, 0.32) * (t < 0.42) + (t >= 0.42)
    feet, status, _ = feet_after_r(small + big, t, np.array([0.0]), CFG, **KW)
    assert status == ["ambiguous"] and len(feet) == 0


def test_foot_near_the_window_start_is_edge():
    t = np.arange(0.0, 1.0, 1 / 200)
    y = _rise(t, 0.10) * (t < 0.2) + (t >= 0.2)
    status = feet_after_r(y, t, np.array([0.0]), SignalConfig(edge_s=0.15), **KW)[1]
    assert status == ["edge"]


@pytest.mark.parametrize("kw", [dict(KW, ambiguous_fraction=0.3), dict(KW, rise_min_fraction=1.0),
                                dict(KW, ambiguous_fraction=0.0), dict(KW, search_s=0.0)])
def test_parameters_are_checked(kw):
    t = np.arange(0, 1, 1 / 200)
    with pytest.raises(ValueError):
        feet_after_r(np.sin(t), t, np.array([0.1]), CFG, **kw)


def test_foot_after_the_next_r_is_ambiguous_not_assigned():
    # R at 0 and 0.3 s; the only rise starts at 0.28 s (inside the first R's
    # interval) but is slow, so its tangent foot (about 0.325 s) falls after the
    # second R: it cannot be told which R it belongs to.
    t = np.arange(-0.5, 1.5, 1 / 200)
    y = _rise(t, 0.28, 0.25) * (t < 0.53) + (t >= 0.53)
    feet, status, per_r = feet_after_r(y, t, np.array([0.0, 0.3]), CFG, **KW)
    assert status[0] == "ambiguous" and len(feet) == 0 and per_r[0] > 0.3


def test_r_before_the_ppg_starts_is_edge():
    t = np.arange(0.5, 2.0, 1 / 200)  # PPG starts after the first R's interval
    y = _rise(t, 1.15) * (t < 1.25) + (t >= 1.25)
    status = feet_after_r(y, t, np.array([-0.5, 1.0]), CFG, **KW)[1]
    assert status[0] == "edge" and status[1] == "ok"


def test_pat_exactly_on_the_lower_limit_is_kept():
    # Linear rise: the tangent foot is the onset itself, 80 ms after R.
    t = np.arange(-0.5, 1.0, 1 / 200)
    r = 0.025
    y = np.clip((t - (r + 0.08)) / 0.1, 0, 1)
    feet, status, _ = feet_after_r(y, t, np.array([r]), CFG, **KW)
    assert status == ["ok"] and feet[0] - r == pytest.approx(0.08, abs=1e-9)
