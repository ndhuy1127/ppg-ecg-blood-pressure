"""Week 5 candidate fiducials, PAT validity and manual-agreement tooling.

Known-answer SYNTHETIC checks only; not evidence of accuracy on people or PulseDB.
"""

import hashlib
import json
from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from scripts.demo_week04_huy import fixture
from scripts.week05_fiducials import (
    SYNTHETIC_CASES, clicks_to_rows, detection_rows, export_record_id, load_records,
    main, run_annotate, run_compare, select_review_rows, synthetic_record, t_apex_s,
)
from software.evaluation.fiducial_agreement import (
    ANNOTATION_COLUMNS, DETECTION_COLUMNS, agreement, match_events,
)
from software.feature_extraction.week04 import extract_window
from software.signal_processing.fiducials import (
    Channel, SignalConfig, _foot_time, _vertex_offset, detect,
)
from software.signal_processing.pat_validity import (
    PatRules, classify_pat, detectable_foot_span, pair_between_r, pat_beats,
)

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "configs/data/week05_huy.json"
CONFIG = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
BASE = SignalConfig(**CONFIG["signal"])
RULES = PatRules(**CONFIG["pat_validity"])
TOLERANCE = CONFIG["agreement"]["tolerance_s"]


def _case(name, **override):
    ecg, ppg, ecg_fs, ppg_fs, r, feet = synthetic_record(
        **{**SYNTHETIC_CASES[name], **override})
    return Channel(ecg, ecg_fs, "u", None), Channel(ppg, ppg_fs, "u", None), r, feet


def _span(ppg):
    times = ppg.start_s + np.arange(len(ppg.values)) / ppg.fs_hz
    return detectable_foot_span(times, BASE.edge_s, BASE.foot_lookback_s)


def _inside(times, low=0.5, high=9.5):
    times = np.asarray(times)
    return times[(times >= low) & (times <= high)]


def _sinusoid_ppg(offset_samples, fs=125, rate_hz=1.25, decimals=None):
    """-cos PPG: smooth symmetric minima ``offset_samples`` after a sample.

    1.25 Hz = 100 samples per period, so every minimum has the same offset.
    """
    t = np.arange(10 * fs) / fs
    t0 = 1.0 + offset_samples / fs
    ppg = -np.cos(2 * np.pi * rate_hz * (t - t0))
    if decimals is not None:
        ppg = np.round(ppg, decimals)
    minima = t0 + np.arange(-1, 15) / rate_hz
    return Channel(ppg, fs, "u", None), minima


def test_config_matches_documented_values():
    """Locked before marking (docs section 3); a change must be deliberate."""
    assert CONFIG["status"] == "NOT_TEST_TUNED"
    assert CONFIG["pat_validity"] == {"min_ms": 80.0, "max_ms": 400.0, "mad_k": 3.0,
                                      "mad_floor_ms": 10.0, "min_pairs": 3}
    assert TOLERANCE == {"ecg_r": 0.05, "ppg_foot": 0.1}
    assert (BASE.r_method, BASE.foot_method) == ("prominence", "tangent")
    assert (BASE.pat_min_s, BASE.pat_max_s) == (0.08, 0.4)
    # Decided 2026-10-25 (docs section 8).
    assert CONFIG["version"] == "fiducials-week05-v1"
    assert (BASE.refractory_s, BASE.ppg_refractory_s) == (0.25, 0.35)
    assert BASE.foot_interpolation is False
    assert BASE.r_energy_threshold == "quantile"


def test_defaults_are_v1_methods_and_unknown_methods_rejected():
    assert (SignalConfig().r_method, SignalConfig().foot_method) == ("prominence",
                                                                      "tangent")
    for field in ("r_method", "foot_method"):
        with pytest.raises(ValueError):
            SignalConfig(**{field: "pan_tompkins"})
    with pytest.raises(ValueError):
        SignalConfig(r_energy_window_s=0)
    # New fields keep features-sqi-v1/v2 when left at their defaults.
    assert SignalConfig().ppg_refractory_s is None
    assert SignalConfig().foot_interpolation is False
    assert SignalConfig().r_energy_threshold == "quantile"
    for bad in ({"ppg_refractory_s": 0}, {"ppg_refractory_s": float("nan")},
                {"foot_interpolation": 1}, {"r_energy_threshold": "mad"}):
        with pytest.raises(ValueError):
            SignalConfig(**bad)


@pytest.mark.parametrize("field,method", [("r_method", "derivative_energy"),
                                          ("foot_method", "d2_max"),
                                          ("foot_method", "valley_min")])
def test_features_sqi_v1_refuses_candidate_methods(field, method):
    window, _ = fixture()
    with pytest.raises(ValueError, match="features-sqi-v1"):
        extract_window(window, replace(SignalConfig(), **{field: method}))


def test_features_sqi_refuses_a_separate_ppg_refractory():
    window, _ = fixture()
    with pytest.raises(ValueError, match="ppg_refractory_s"):
        extract_window(window, replace(SignalConfig(), ppg_refractory_s=0.35))


@pytest.mark.parametrize("ecg_fs", [125, 500])
@pytest.mark.parametrize("method", ["prominence", "derivative_energy"])
def test_clean_r_peaks_known_answer(method, ecg_fs):
    ecg, _, r, _ = _case("SYN_CLEAN_HR60", ecg_fs=ecg_fs)
    found, issues = detect(ecg, replace(BASE, r_method=method, refractory_s=0.4), "ecg")
    assert not issues
    assert _inside(found) == pytest.approx(_inside(r), abs=1 / ecg.fs_hz)


@pytest.mark.parametrize("name", ["SYN_CLEAN_HR60", "SYN_T_EDGE_HR60"])
def test_prominence_needs_long_refractory_to_skip_t_waves(name):
    """Documented limitation: with a 0.25 s refractory the local-maxima detector
    also returns T waves (at R + 0.28 s nominal, and at R + 0.25 s, exactly on the
    boundary at 500 Hz); the derivative-energy envelope does not."""
    ecg, _, r, _ = _case(name)
    prominence, _ = detect(ecg, replace(BASE, r_method="prominence"), "ecg")
    energy, _ = detect(ecg, replace(BASE, r_method="derivative_energy"), "ecg")
    matched, _ = match_events(_inside(r), _inside(prominence), 0.05)
    assert len(matched) == len(_inside(r))
    assert len(_inside(prominence)) == 2 * len(_inside(r))
    assert _inside(energy) == pytest.approx(_inside(r), abs=1 / ecg.fs_hz)


def test_clean_feet_known_answer_per_method():
    _, ppg, _, onsets = _case("SYN_CLEAN_HR60")
    rise, step = SYNTHETIC_CASES["SYN_CLEAN_HR60"].get("rise_s", 0.15), 1 / ppg.fs_hz
    expected = _inside(onsets)
    tangent, _ = detect(ppg, replace(BASE, foot_method="tangent"), "ppg")
    # Half-cosine rise: max-slope tangent meets baseline (1/2 - 1/pi) * rise after
    # onset.
    assert _inside(tangent) == pytest.approx(expected + (0.5 - 1 / np.pi) * rise,
                                             abs=step)
    valley, _ = detect(ppg, replace(BASE, foot_method="valley_min"), "ppg")
    assert _inside(valley) == pytest.approx(expected, abs=step)
    d2, _ = detect(ppg, replace(BASE, foot_method="d2_max"), "ppg")
    # Discrete second difference peaks on the first sample after the onset kink.
    assert _inside(d2) == pytest.approx(expected + step, abs=step)


@pytest.mark.parametrize("method", ["valley_min", "d2_max"])
@pytest.mark.parametrize("offset", [0.3, -0.3])
def test_parabolic_refinement_finds_sub_sample_minimum(method, offset):
    """A smooth symmetric minimum between samples: refinement (when enabled)
    must land within 0.1 sample; no refinement is 0.3 sample off, the wrong sign
    0.6."""
    ppg, minima = _sinusoid_ppg(offset)
    feet, issues = detect(ppg, replace(BASE, foot_method=method,
                                       foot_interpolation=True), "ppg")
    assert not issues and len(_inside(feet)) >= 10
    nearest = minima[np.abs(_inside(feet)[:, None] - minima).argmin(axis=1)]
    assert np.abs(_inside(feet) - nearest).max() <= 0.1 / ppg.fs_hz


@pytest.mark.parametrize("method", ["valley_min", "d2_max"])
def test_interpolation_is_off_by_default(method):
    """Decided 2026-10-25: without refinement a foot stays on the sample grid,
    0.3 sample from a minimum that lies 0.3 sample after a sample."""
    ppg, minima = _sinusoid_ppg(0.3)
    feet, issues = detect(ppg, replace(BASE, foot_method=method), "ppg")
    assert not issues and len(_inside(feet)) >= 10
    on_grid = _inside(feet) * ppg.fs_hz
    assert on_grid == pytest.approx(np.round(on_grid), abs=1e-6)
    nearest = minima[np.abs(_inside(feet)[:, None] - minima).argmin(axis=1)]
    assert np.abs(_inside(feet) - nearest) == pytest.approx(0.3 / ppg.fs_hz, abs=1e-6)


@pytest.mark.parametrize("d2_next,shift", [(2.5, 0.0), (1.5, 1 / 6)])
def test_d2_max_refines_only_a_strict_maximum(d2_next, shift):
    """The second-difference argmax at the end of the search (slope index) is no
    maximum when the next second difference is larger: curvature alone would
    shift it by half a sample. A strict maximum 1, 2, 1.5 shifts by 1/6 sample."""
    d2 = [0.0, 0.0, 1.0, 2.0, d2_next, -5.0, -5.0, 0.0]
    values = [0.0, 0.0]
    for k in range(1, len(d2) - 1):  # d2[k] = v[k-1] - 2 v[k] + v[k+1]
        values.append(2 * values[k] - values[k - 1] + d2[k])
    values = np.array(values)
    times = np.arange(len(values)) * 0.01
    foot = _foot_time(values, times, 1, 3, None, "d2_max", True)
    assert foot == pytest.approx(times[3] + shift * 0.01)
    assert _foot_time(values, times, 1, 3, None, "d2_max", False) == times[3]


def test_vertex_offset_needs_the_right_curvature():
    assert _vertex_offset(1.0, 0.0, 1.0, "min") == 0.0
    assert _vertex_offset(2.0, 0.0, 1.0, "min") == pytest.approx(1 / 6)
    # d2 = 3.0, 1.2, 0.2 at the edge of the d2_max search: curved like a
    # minimum, so no maximum vertex and no shift.
    assert _vertex_offset(3.0, 1.2, 0.2, "max") == 0.0
    assert _vertex_offset(-1.0, 0.0, -2.0, "max") == pytest.approx(-1 / 6)
    # An asymmetric corner is a strict minimum and is still refined (documented).
    assert _vertex_offset(1.0, 0.0, 10.0, "min") == pytest.approx(-0.409, abs=1e-3)


def test_valley_plateau_is_not_refined():
    """Two equal minimal samples: the last one is kept, no half-sample shift."""
    ppg, minima = _sinusoid_ppg(0.5, decimals=6)
    feet, _ = detect(ppg, replace(BASE, foot_method="valley_min",
                                  foot_interpolation=True), "ppg")
    nearest = minima[np.abs(_inside(feet)[:, None] - minima).argmin(axis=1)]
    assert _inside(feet) - nearest == pytest.approx(0.5 / ppg.fs_hz, abs=1e-9)


def test_noisy_record_r_found_and_tangent_feet_complete():
    ecg, ppg, r, onsets = _case("SYN_NOISY_HR60")
    for method in ("prominence", "derivative_energy"):
        found, _ = detect(ecg, replace(BASE, r_method=method, refractory_s=0.4), "ecg")
        matched, _ = match_events(_inside(r), _inside(found), 0.05)
        assert len(matched) == len(_inside(r))
    for method in ("tangent", "d2_max", "valley_min"):
        feet, _ = detect(ppg, replace(BASE, foot_method=method), "ppg")
        assert np.isfinite(feet).all() and (np.diff(feet) > 0).all()
    tangent, _ = detect(ppg, BASE, "ppg")
    matched, _ = match_events(_inside(onsets), _inside(tangent), 0.1)
    assert len(matched) == len(_inside(onsets))


def test_rejected_channel_returns_issues_and_no_fiducials():
    ppg, _ = _sinusoid_ppg(0.0)
    times = np.arange(len(ppg.values)) / ppg.fs_hz
    times[600:] += 0.5  # a 0.5 s gap in the timestamps
    gapped = replace(ppg, timestamps=times)
    found, issues = detect(gapped, BASE, "ppg")
    assert len(found) == 0 and issues == ["time_gap"]


@pytest.mark.parametrize("method", ["prominence", "derivative_energy"])
def test_pause_creates_no_beat_and_no_pat(method):
    ecg, ppg, r, _ = _case("SYN_PAUSE_HR60")
    config = replace(BASE, r_method=method, refractory_s=0.4)
    found, _ = detect(ecg, config, "ecg")
    gap = (found > r[3] + 0.1) & (found < r[4] - 0.1)
    assert not gap.any()
    feet, _ = detect(ppg, config, "ppg")
    result = pat_beats(found, feet, RULES, foot_span=_span(ppg))
    assert result["n_pairs"] == len(found) and result["n_unpaired_r"] == 0


def test_ppg_dropout_leaves_r_unpaired_not_mispaired():
    ecg, ppg, r, _ = _case("SYN_PPG_DROPOUT_HR60")
    found, _ = detect(ecg, replace(BASE, r_method="derivative_energy"), "ecg")
    feet, _ = detect(ppg, BASE, "ppg")
    result = pat_beats(found, feet, RULES, foot_span=_span(ppg))
    assert result["n_unpaired_r"] == result["n_no_foot"] == 1
    assert result["n_valid"] == result["n_pairs"] == len(found) - 1
    pats = np.array([p[2] for p in result["pairs"]])
    assert pats == pytest.approx(200 + (0.5 - 1 / np.pi) * 150, abs=1000 / ppg.fs_hz)


@pytest.mark.parametrize("refractory", [0.25, 0.4])
@pytest.mark.parametrize("r_method", ["prominence", "derivative_energy"])
@pytest.mark.parametrize("foot_method", ["tangent", "d2_max", "valley_min"])
def test_high_heart_rate_every_beat_once(r_method, foot_method, refractory):
    ecg, ppg, r, onsets = _case("SYN_HIGH_HR143")
    # SYNTHETIC v1: at RR 0.42 s the T apex is 0.28 * sqrt(0.42) = 0.18 s after R,
    # inside both R refractory periods, so neither detector returns it (with v0's
    # fixed R + 0.25 s, prominence at 0.25 s also returned the last T wave).
    config = replace(BASE, r_method=r_method, foot_method=foot_method,
                     refractory_s=refractory)
    found, _ = detect(ecg, config, "ecg")
    feet, _ = detect(ppg, config, "ppg")
    assert len(match_events(_inside(r), _inside(found), 0.05)[0]) == len(_inside(r))
    assert len(_inside(found)) == len(_inside(r))
    assert (len(match_events(_inside(onsets), _inside(feet), 0.05)[0])
            == len(_inside(onsets)))
    assert (np.diff(feet) > 0).all()
    assert pat_beats(found, feet, RULES, foot_span=_span(ppg))["n_unpaired_r"] == 0


def test_pat_beats_labels_out_of_range_instead_of_dropping():
    r = np.arange(1.0, 9.0)
    pat = np.full(8, 0.2)
    pat[2], pat[5] = 0.45, 0.06
    result = pat_beats(r, r + pat, RULES, foot_span=None)
    assert (result["n_pairs"], result["n_unpaired_r"]) == (8, 0)
    assert result["n_out_of_range"] == 2
    assert [result["status"][i] for i in (2, 5)] == ["out_of_range"] * 2
    assert result["median_valid_ms"] == pytest.approx(200)


def test_pair_between_r_no_foot_and_ambiguous_are_labelled():
    r = [1.0, 2.0, 3.0, 4.0]
    # R2: two feet, only 2.2 s in range -> paired. R3: 3.05 and 3.5 s are both
    # out of range -> ambiguous. R4 (last): nothing within one RR -> no_foot.
    feet = [1.2, 2.2, 2.6, 3.05, 3.5]
    pairs, status = pair_between_r(r, feet, RULES, foot_span=None)
    assert status == ["paired", "paired", "ambiguous", "no_foot"]
    assert [(i, j) for i, j, _ in pairs] == [(0, 0), (1, 1)]
    assert [p[2] for p in pairs] == pytest.approx([200, 200])
    # The last R only looks one RR ahead: a foot 1.5 s later is not its own.
    assert pair_between_r([1.0, 2.0, 3.0], [1.2, 2.2, 4.5], RULES,
                          foot_span=None)[1][-1] == "no_foot"
    with pytest.raises(ValueError):
        pair_between_r([1.0, 1.0], [1.2], RULES, foot_span=None)


def test_detectable_foot_span_trims_edges_and_lookback():
    times = np.arange(1000) / 100  # 0 .. 9.99 s
    assert detectable_foot_span(times, 0.1, 0.5) == pytest.approx((0.1, 9.39))
    with pytest.raises(ValueError):
        detectable_foot_span(np.arange(50) / 100, 0.1, 0.5)  # 0.49 s window
    with pytest.raises(ValueError):
        detectable_foot_span([0.0, 0.0, 1.0], 0.1, 0.5)


def test_missing_foot_near_window_edge_is_edge_not_no_foot():
    # Span (0.1, 9.4). R 0.01 s: its PAT window starts at 0.09 s, before the span.
    # R 9.1 s: the window ends at 9.5 s, after it. R 2.0 s misses a foot inside.
    r, feet, span = [0.01, 1.0, 2.0, 3.0, 9.1], [1.2, 3.2], (0.1, 9.4)
    result = pat_beats(r, feet, RULES, foot_span=span)
    assert result["r_status"] == ["edge", "paired", "no_foot", "paired", "edge"]
    assert (result["n_pairs"], result["n_unpaired_r"], result["n_edge"]) == (2, 1, 2)
    assert result["n_pairs"] + result["n_unpaired_r"] + result["n_edge"] == len(r)
    # Without span information nothing is exempted (the earlier behaviour).
    old = pat_beats(r, feet, RULES, foot_span=None)
    assert old["r_status"] == ["no_foot", "paired", "no_foot", "paired", "no_foot"]
    assert (old["n_unpaired_r"], old["n_edge"]) == (3, 0)
    # Shifting the span with the times gives the same labels.
    moved = pat_beats(np.add(r, 100), np.add(feet, 100), RULES,
                      foot_span=(100.1, 109.4))
    assert moved["r_status"] == result["r_status"]


def test_edge_bound_is_inclusive_and_only_changes_no_foot():
    span = (0.1, 9.4)
    # R + 400 ms exactly at the span end: the whole window is inside -> no_foot.
    assert pair_between_r([8.0, 9.0], [8.2], RULES, foot_span=span)[1] == [
        "paired", "no_foot"]
    assert pair_between_r([8.0, 9.001], [8.2], RULES, foot_span=span)[1] == [
        "paired", "edge"]
    # Near the end (windows reach past 9.4 s): a single foot 50 ms after R is
    # still paired (then out_of_range), and two out-of-range feet stay ambiguous.
    pairs, status = pair_between_r([8.0, 9.15], [8.2, 9.2], RULES, foot_span=span)
    assert status == ["paired", "paired"] and pairs[1][2] == pytest.approx(50)
    status = pair_between_r([8.0, 9.2], [8.2, 9.22, 9.25], RULES, foot_span=span)[1]
    assert status == ["paired", "ambiguous"]


@pytest.mark.parametrize("span", [(5.0, 1.0), (1.0, 1.0), (float("nan"), 2.0),
                                  (1.0, 2.0, 3.0), "0-9"])
def test_bad_foot_span_is_rejected(span):
    with pytest.raises(ValueError):
        pat_beats([1.0, 2.0], [1.2], RULES, foot_span=span)


def test_pat_limits_are_inclusive_despite_float_rounding():
    # (0.18 - 0.1) * 1000 = 79.99999999999999 and (1.1 - 0.7) * 1000 =
    # 400.0000000000001 in binary floating point; both are on the limits.
    result = pat_beats([0.1, 0.7, 1.7, 2.7], [0.18, 1.1, 1.9, 2.9], RULES,
                       foot_span=None)
    assert result["n_out_of_range"] == 0 and result["n_pairs"] == 4
    outside = classify_pat([79.9, 400.1, 200, 200, 200], RULES)
    assert outside["status"][:2] == ["out_of_range"] * 2


def test_classify_pat_range_outlier_and_summary():
    pats = [198, 200, 202, 199, 201, 200, 260, 90, 50, 450]
    result = classify_pat(pats, RULES)
    assert result["status"] == (["valid"] * 6 + ["outlier", "outlier"]
                                + ["out_of_range", "out_of_range"])
    counts = (result["n_valid"], result["n_outlier"], result["n_out_of_range"])
    assert counts == (6, 2, 2)
    assert result["median_valid_ms"] == pytest.approx(200)
    assert result["median_all_ms"] == pytest.approx(200)
    constant = classify_pat([200, 200, 200, 300], RULES)
    # MAD = 0: flagged, and only the absolute floor decides outliers.
    assert constant["status"] == ["valid"] * 3 + ["outlier"]
    assert "pat:mad_zero" in constant["flags"]
    # Quantization-sized spread is not an outlier because of the floor.
    near = classify_pat([200, 200, 200, 208, 192, 200], RULES)
    assert near["n_outlier"] == 0
    no_floor = replace(RULES, mad_floor_ms=0)
    assert classify_pat([200, 200, 200, 208, 192, 200], no_floor)["n_outlier"] == 2
    few = classify_pat([200, 500], RULES)
    assert few["median_valid_ms"] is None and "pat:too_few_valid" in few["flags"]
    two = classify_pat([200, 300], RULES)
    assert "pat:too_few_in_range_for_outlier_rule" in two["flags"]


def test_mad_rule_uses_k_and_normal_scale():
    """Median 240, MAD 20 -> limit 3 * 1.4826 * 20 = 88.96 ms (> the 10 ms floor).
    305 (65 ms away) stays valid, 330 (90 ms) is an outlier. Scale 1 or k = 1
    would flag 305; k = 10 would keep 330."""
    pats = [200, 210, 220, 230, 240, 250, 260, 305, 330]
    assert classify_pat(pats, RULES)["status"] == ["valid"] * 8 + ["outlier"]


def test_pat_rules_load_from_config_and_reject_bad_values():
    for bad in ({"min_ms": 400, "max_ms": 80}, {"mad_k": 0}, {"mad_floor_ms": -1},
                {"min_pairs": 1}, {"min_ms": True}):
        with pytest.raises(ValueError):
            PatRules(**bad)
    with pytest.raises(ValueError):
        classify_pat([200, np.nan], RULES)


def test_match_events_one_to_one_closest_first():
    matched, errors = match_events([1.0, 2.0, 3.0], [1.01, 1.02, 2.2, 3.04], 0.05)
    assert matched == [(0, 0), (2, 3)]
    assert errors * 1000 == pytest.approx([10, 40])


def test_match_events_maximises_pairs_and_never_reuses():
    # Closest-first greedy would pair 1.06/1.035 and then lose 1.00.
    matched, _ = match_events([1.00, 1.06], [1.035, 1.105], 0.05)
    assert matched == [(0, 0), (1, 1)]
    assert len(match_events([1.0, 1.04], [1.02], 0.05)[0]) == 1
    assert len(match_events([1.02], [1.0, 1.04], 0.05)[0]) == 1
    # Exactly one tolerance away matches whatever the binary rounding.
    assert len(match_events([1.0, 2.0], [1.05, 2.05], 0.05)[0]) == 2
    assert match_events([1.0], [1.0501], 0.05)[0] == []


def _tables(times_det, split="val", marks=(1.0, 2.0, 3.0), annotator="HUY",
            det_split=None):
    rows = [(f, t) for f, t in [("ecg_r", t) for t in marks] + [("ppg_foot", None)]]
    annotations = pd.DataFrame([
        {"record_id": "SYN_A", "split": split, "fiducial": f, "time_s": t,
         "review_start_s": 0.5, "review_end_s": 4.5, "annotator": annotator,
         "annotated_on": "2026-10-21", "note": ""}
        for f, t in rows
    ], columns=ANNOTATION_COLUMNS)
    det_split = det_split or split
    det = [{"record_id": "SYN_A", "split": det_split, "method": "m", "fiducial": f,
            "time_s": None} for f in ("ecg_r", "ppg_foot")]
    det += [{"record_id": "SYN_A", "split": det_split, "method": "m",
             "fiducial": "ecg_r", "time_s": t} for t in times_det]
    return annotations, pd.DataFrame(det, columns=DETECTION_COLUMNS)


def test_agreement_counts_bias_and_region():
    annotations, detections = _tables([0.2, 1.004, 2.002, 2.5, 4.9])
    result = agreement(annotations, detections, TOLERANCE)
    assert result["reference_type"] == "MANUAL"
    r = next(s for s in result["summary"] if s["fiducial"] == "ecg_r")
    # 0.2 and 4.9 are outside the reviewed region and do not count.
    assert (r["tp"], r["fp"], r["fn"]) == (2, 1, 1)
    assert r["sensitivity"] == pytest.approx(2 / 3) and r["ppv"] == pytest.approx(2 / 3)
    assert r["bias_ms"] == pytest.approx(3) and r["mae_ms"] == pytest.approx(3)
    assert r["sd_ms"] == pytest.approx(np.std([4, 2], ddof=1))
    foot = next(s for s in result["summary"] if s["fiducial"] == "ppg_foot")
    assert foot["n_reference"] == 0 and foot["sensitivity"] is None


def test_agreement_edge_match_is_tp_and_unmatched_margin_is_not_fp():
    # Mark 4.49 s inside the region, detection 4.51 s just outside: a TP.
    # Detection 0.47 s (outside, unmatched): not a false positive.
    annotations, detections = _tables([0.47, 4.51], marks=(4.49,))
    r = next(s for s in agreement(annotations, detections, TOLERANCE)["summary"]
             if s["fiducial"] == "ecg_r")
    assert (r["tp"], r["fp"], r["fn"], r["n_detected"]) == (1, 0, 0, 1)
    assert r["bias_ms"] == pytest.approx(20)


def test_agreement_rejects_test_split_mismatch_and_missing_run():
    annotations, detections = _tables([1.0], split="test")
    with pytest.raises(ValueError, match="train/val"):
        agreement(annotations, detections, TOLERANCE)
    annotations, detections = _tables([1.0], det_split="train")
    with pytest.raises(ValueError, match="split differs"):
        agreement(annotations, detections, TOLERANCE)
    annotations, detections = _tables([1.0])
    with pytest.raises(ValueError, match="No method was run"):
        agreement(annotations, detections[detections.fiducial == "ecg_r"], TOLERANCE)


@pytest.mark.parametrize("name", ["SYNTHETIC_GROUND_TRUTH_NOT_MANUAL",
                                  " synthetic_ground_truth_not_manual ",
                                  "Synthetic"])
def test_agreement_refuses_synthetic_truth_however_written(name):
    annotations, detections = _tables([1.0], annotator=name)
    with pytest.raises(ValueError, match="SYNTHETIC"):
        agreement(annotations, detections, TOLERANCE)
    result = agreement(annotations, detections, TOLERANCE, allow_synthetic_truth=True)
    assert result["reference_type"] == "SYNTHETIC_TRUTH"
    mixed = annotations.copy()
    mixed.loc[0, "annotator"] = "HUY"
    with pytest.raises(ValueError, match="mix"):
        agreement(mixed, detections, TOLERANCE, allow_synthetic_truth=True)


def test_select_review_rows_never_test_and_ignores_bp():
    manifest = pd.DataFrame({
        "subject_id": [f"S{i % 6}" for i in range(30)],
        "split": ["train", "val", "test"] * 10,
        "raw_index": range(30), "sbp": np.arange(30.0),
        "sample_id": [f"x:{i}" for i in range(30)],
    })
    picked = select_review_rows(manifest, 3, 2, seed=1)
    assert set(picked.split) <= {"train", "val"} and len(picked) <= 6
    shuffled = manifest.assign(sbp=np.random.default_rng(0).permutation(manifest.sbp))
    assert (picked.raw_index.tolist()
            == select_review_rows(shuffled, 3, 2, seed=1).raw_index.tolist())


def test_clicks_to_rows_keeps_empty_reviewed_region():
    class Record:
        record_id, split = "SYN_A", "val"
    rows = clicks_to_rows(Record, [("ecg_r", 2.0), ("ecg_r", 1.0)], (0.5, 9.5), "HUY",
                          "2026-10-21")
    assert [r["time_s"] for r in rows if r["fiducial"] == "ecg_r"] == ["1.000000",
                                                                      "2.000000"]
    assert [r["time_s"] for r in rows if r["fiducial"] == "ppg_foot"] == [""]


def test_load_records_refuses_test_split(tmp_path):
    records = tmp_path / "records"
    main(["synth", "--out", str(records)])
    index = records / "records.csv"
    index.write_text(index.read_text(encoding="utf-8").replace(",val,", ",test,"),
                     encoding="utf-8")
    with pytest.raises(ValueError, match="train/val"):
        list(load_records(records))


def test_synth_refuses_existing_directory_before_writing(tmp_path):
    out = tmp_path / "records"
    out.mkdir()
    (out / "keep.txt").write_text("mine", encoding="utf-8")
    with pytest.raises(FileExistsError):
        main(["synth", "--out", str(out)])
    assert sorted(p.name for p in out.iterdir()) == ["keep.txt"]


def test_detection_rows_mark_every_run_and_report_channel_issues():
    class Record:
        record_id, split, ecg_fs_hz, ppg_fs_hz = "SYN_FLAT", "val", 500, 125
    ecg, _, _, _, _, _ = synthetic_record()
    rows, issues = detection_rows(Record, ecg, np.zeros(1250), BASE)
    feet = [r for r in rows if r["fiducial"] == "ppg_foot"]
    assert sorted(r["method"] for r in feet) == ["d2_max", "tangent", "valley_min"]
    assert all(r["time_s"] == "" for r in feet)
    assert issues == {f"ppg_foot/{m}": ["flat"] for m in ("tangent", "d2_max",
                                                          "valley_min")}


def test_script_end_to_end_on_synthetic_and_refuses_overwrite(tmp_path):
    records = tmp_path / "records"
    det = tmp_path / "det.csv"
    main(["synth", "--out", str(records)])
    synth_info = json.loads((records / "synth.provenance.json").read_text("utf-8"))
    assert synth_info["provenance"]["source_types"] == ["SYNTHETIC"]
    main(["detect", "--records", str(records), "--out", str(det)])
    detect_info = json.loads((tmp_path / "det.provenance.json").read_text("utf-8"))
    assert detect_info["signal_config"]["refractory_s"] == BASE.refractory_s
    assert set(detect_info["provenance"]["environment"]) >= {"python", "numpy",
                                                             "scipy", "pandas"}
    truth = records / "truth_synthetic.csv"
    with pytest.raises(ValueError, match="SYNTHETIC"):
        run_compare(truth, det, CONFIG_PATH, tmp_path / "x.json")
    assert not (tmp_path / "x.json").exists()
    result = run_compare(truth, det, CONFIG_PATH, tmp_path / "cmp.json",
                         allow_synthetic_truth=True)
    assert result["reference_type"] == "SYNTHETIC_TRUTH"
    assert result["provenance"]["source_types"] == ["SYNTHETIC"]
    assert result["detect_provenance"] == detect_info["provenance"]
    energy = next(s for s in result["summary"]
                  if s["fiducial"] == "ecg_r" and s["method"] == "derivative_energy")
    assert energy["fn"] == 0
    with pytest.raises(FileExistsError):
        main(["synth", "--out", str(records)])
    with pytest.raises(FileExistsError):
        main(["detect", "--records", str(records), "--out", str(det)])


def test_compare_refuses_other_config_or_missing_detect_provenance(tmp_path):
    records = tmp_path / "records"
    det = tmp_path / "det.csv"
    main(["synth", "--out", str(records)])
    main(["detect", "--records", str(records), "--out", str(det)])
    other = tmp_path / "other.json"
    other.write_text(json.dumps({**CONFIG, "agreement": {
        "tolerance_s": {"ecg_r": 0.5, "ppg_foot": 0.1}}}), encoding="utf-8")
    truth = records / "truth_synthetic.csv"
    with pytest.raises(ValueError, match="Config differs"):
        run_compare(truth, det, other, tmp_path / "a.json", allow_synthetic_truth=True)
    original = det.read_bytes()
    det.write_bytes(original + b"SYN_CLEAN_HR60,val,tangent,ppg_foot,5.000000\n")
    with pytest.raises(ValueError, match="Detections differ"):
        run_compare(truth, det, CONFIG_PATH, tmp_path / "c.json",
                    allow_synthetic_truth=True)
    det.write_bytes(original)
    (tmp_path / "det.provenance.json").unlink()
    with pytest.raises(ValueError, match="missing"):
        run_compare(truth, det, CONFIG_PATH, tmp_path / "b.json",
                    allow_synthetic_truth=True)


def test_export_record_ids_keep_two_raw_files_apart():
    first = export_record_id("a" * 64, "val", 7)
    assert first == "PDB_aaaaaaaaaaaa_val_7"
    assert export_record_id("b" * 64, "val", 7) != first


def _synth_and_detect(tmp_path):
    records, det = tmp_path / "records", tmp_path / "det.csv"
    main(["synth", "--out", str(records)])
    main(["detect", "--records", str(records), "--out", str(det)])
    detect_info = json.loads((tmp_path / "det.provenance.json").read_text("utf-8"))
    return records, det, detect_info["provenance"]["inputs_sha256"]["records_csv"]


def test_compare_ties_annotations_to_the_detected_records(tmp_path):
    records, det, records_sha = _synth_and_detect(tmp_path)
    truth = records / "truth_synthetic.csv"
    result = run_compare(truth, det, CONFIG_PATH, tmp_path / "ok.json",
                         allow_synthetic_truth=True)
    assert result["annotation_provenance"]["kind"] == "synth"
    assert result["annotation_provenance"]["records_csv"] == records_sha
    # A hand-filled CSV (here a copy) has no provenance: refused unless allowed,
    # and the bypass is recorded.
    manual = tmp_path / "manual.csv"
    manual.write_bytes(truth.read_bytes())
    with pytest.raises(ValueError, match="no provenance"):
        run_compare(manual, det, CONFIG_PATH, tmp_path / "a.json",
                    allow_synthetic_truth=True)
    assert not (tmp_path / "a.json").exists()
    bypass = run_compare(manual, det, CONFIG_PATH, tmp_path / "b.json",
                         allow_synthetic_truth=True,
                         allow_annotations_without_provenance=True)
    assert bypass["annotation_provenance"] == {
        "kind": "none", "file": None, "sha256": None, "records_csv": None}
    assert bypass["provenance"]["inputs_sha256"]["annotations_provenance"] is None
    # A sidecar that exists must match, flag or not.
    sidecar = tmp_path / "manual.provenance.json"
    good = {"output_sha256": hashlib.sha256(manual.read_bytes()).hexdigest(),
            "provenance": {"inputs_sha256": {"records_csv": records_sha}}}
    for broken, message in (
        ({**good, "output_sha256": "0" * 64}, "differ from the file"),
        ({**good, "provenance": {"inputs_sha256": {"records_csv": "0" * 64}}},
         "other records"),
        ({"output_sha256": good["output_sha256"]}, "Unreadable"),
    ):
        sidecar.write_text(json.dumps(broken), encoding="utf-8")
        with pytest.raises(ValueError, match=message):
            run_compare(manual, det, CONFIG_PATH, tmp_path / "c.json",
                        allow_synthetic_truth=True,
                        allow_annotations_without_provenance=True)
    sidecar.write_text(json.dumps(good), encoding="utf-8")
    tied = run_compare(manual, det, CONFIG_PATH, tmp_path / "d.json",
                       allow_synthetic_truth=True)
    assert tied["annotation_provenance"]["kind"] == "annotate"
    # Edited truth no longer matches synth.provenance.json.
    truth.write_bytes(truth.read_bytes() + b"\n")
    with pytest.raises(ValueError, match="differ from the file"):
        run_compare(truth, det, CONFIG_PATH, tmp_path / "e.json",
                    allow_synthetic_truth=True)


def test_annotate_refuses_existing_output_before_any_window(tmp_path, monkeypatch):
    import matplotlib
    matplotlib.use("Agg", force=True)
    import matplotlib.pyplot as plt

    shown = []
    monkeypatch.setattr(plt, "show", lambda *a, **k: shown.append(1))
    records = tmp_path / "records"
    main(["synth", "--out", str(records)])
    existing = tmp_path / "manual.csv"
    existing.write_text("keep", encoding="utf-8")
    with pytest.raises(FileExistsError):
        run_annotate(records, existing, "HUY", "2026-10-22", 0.5)
    assert shown == [] and existing.read_text(encoding="utf-8") == "keep"
    (tmp_path / "late.provenance.json").write_text("{}", encoding="utf-8")
    with pytest.raises(FileExistsError):
        run_annotate(records, tmp_path / "late.csv", "HUY", "2026-10-22", 0.5)
    assert shown == [] and not (tmp_path / "late.csv").exists()
    with pytest.raises(ValueError, match="person"):
        run_annotate(records, tmp_path / "s.csv", " synthetic_x", "2026-10-22", 0.5)
    out = tmp_path / "new.csv"
    run_annotate(records, out, "HUY", "2026-10-22", 0.5)
    assert len(shown) == len(SYNTHETIC_CASES)
    table = pd.read_csv(out)
    assert len(table) == 2 * len(SYNTHETIC_CASES) and table.time_s.isna().all()
    assert (tmp_path / "new.provenance.json").exists()



def _ecg_beats(amplitudes, fs=512, rr_s=1.0):
    """Gaussian QRS (no T wave) of the given amplitudes, one per RR, from 1 s."""
    times = np.arange(int((len(amplitudes) + 2) * rr_s * fs)) / fs
    r = 1.0 + rr_s * np.arange(len(amplitudes))
    ecg = sum(a * np.exp(-0.5 * ((times - t) / 0.01) ** 2) for a, t in zip(amplitudes, r))
    return Channel(ecg, fs, "u", None), r


@pytest.mark.parametrize("threshold,found", [("quantile", 9), ("ptp", 1)])
def test_energy_threshold_survives_one_large_beat(threshold, found):
    """Docs section 7-8: with the peak-to-peak scale one beat x2.5 raises the
    threshold above every other beat (1/9 found); Q95 - Q05 ignores that tail."""
    ecg, r = _ecg_beats([1, 1, 1, 1, 2.5, 1, 1, 1, 1])
    config = replace(BASE, r_method="derivative_energy", refractory_s=0.4,
                     r_energy_threshold=threshold)
    detected, issues = detect(ecg, config, "ecg")
    assert not issues
    assert len(match_events(r, detected, 0.05)[0]) == found


def _ppg_with_secondary_wave(rr_s=0.8, delay_s=0.30, fs=200):
    """Half-cosine pulse (rise 0.15 s, decay 0.12 s) plus a secondary bump of
    half its height ``delay_s`` after the systolic peak."""
    times = np.arange(int(12 * fs)) / fs
    onsets = np.arange(1.0, 11.0, rr_s)
    ppg = np.zeros_like(times)
    for onset in onsets:
        x = times - onset
        ppg += np.where((x >= 0) & (x < 0.15), 0.5 * (1 - np.cos(np.pi * x / 0.15)),
                        np.where(x >= 0.15, np.exp(-(x - 0.15) / 0.12), 0.0))
        ppg += 0.5 * np.exp(-0.5 * ((x - 0.15 - delay_s) / 0.03) ** 2)
    return Channel(ppg, fs, "u", None), onsets


def test_separate_ppg_refractory_skips_a_secondary_wave():
    """Docs section 7-8: a secondary wave 0.30 s after the systolic peak gives a
    false PPG peak, hence a false foot, with the shared 0.25 s refractory; the PPG
    refractory 0.35 s keeps one foot per pulse while ECG R keep 0.25 s."""
    ppg, onsets = _ppg_with_secondary_wave()
    shared, _ = detect(ppg, replace(BASE, ppg_refractory_s=None), "ppg")
    separate, _ = detect(ppg, BASE, "ppg")
    assert len(_inside(shared, 1.5, 10.5)) > len(_inside(onsets, 1.5, 10.5))
    assert len(_inside(separate, 1.5, 10.5)) == len(_inside(onsets, 1.5, 10.5))
    assert (len(match_events(_inside(onsets, 1.5, 10.5), _inside(separate, 1.5, 10.5),
                             0.1)[0]) == len(_inside(onsets, 1.5, 10.5)))


@pytest.mark.parametrize("name,delay", [("SYN_CLEAN_HR60", 0.28),
                                        ("SYN_HIGH_HR143", 0.28 * np.sqrt(0.42)),
                                        ("SYN_T_EDGE_HR60", 0.25)])
def test_t_apex_follows_heart_rate_and_edge_case_stays(name, delay):
    """SYNTHETIC v1: T apex 0.28 * sqrt(RR) s after R; the edge case keeps 0.25 s."""
    assert t_apex_s(SYNTHETIC_CASES[name].get("rr_s", 1.0)) == pytest.approx(
        0.28 * np.sqrt(SYNTHETIC_CASES[name].get("rr_s", 1.0)))
    ecg, _, r, _ = _case(name)
    times = np.arange(len(ecg.values)) / ecg.fs_hz
    for beat in _inside(r, 1.0, 8.0):
        window = (times > beat + 0.1) & (times < beat + 0.36)
        apex = times[window][np.argmax(ecg.values[window])]
        assert apex == pytest.approx(beat + delay, abs=3 / ecg.fs_hz)
