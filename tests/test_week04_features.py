"""Known-answer analytic fixtures, not PulseDB/device performance evidence."""

from dataclasses import replace

import numpy as np
import pytest

from scripts.demo_week04_huy import fixture, fixture_provenance, run
from software.feature_extraction.week04 import extract_window, from_pulse_segment
from software.signal_processing.fiducials import Channel, SignalConfig, pair_pat


@pytest.mark.parametrize("ecg_fs,ppg_fs", [(250, 125), (512, 128), (125, 125)])
def test_known_fiducials_different_sampling_rates(ecg_fs, ppg_fs):
    window, expected = fixture(ecg_fs, ppg_fs)
    ecg, ppg = window.ecg.values.copy(), window.ppg.values.copy()
    result = extract_window(window, SignalConfig())
    tolerance = 1000 / ppg_fs
    assert result["fiducials"]["r_times_s"] == pytest.approx(expected, abs=1 / ecg_fs)
    assert result["fiducials"]["foot_times_s"] == pytest.approx(expected + 0.2, abs=1 / ppg_fs)
    f = result["features"]
    assert f["pat_median_ms"] == pytest.approx(200, abs=tolerance)
    assert f["ppg_hr_bpm"] == pytest.approx(60, abs=0.1)
    assert f["ecg_hr_bpm"] == pytest.approx(60, abs=0.1)
    assert f["ppg_rise_time_median_ms"] == pytest.approx(160, abs=tolerance)
    assert f["ppg_width50_median_ms"] == pytest.approx(200, abs=tolerance)
    assert not result["flagged"]
    np.testing.assert_array_equal(ecg, window.ecg.values)
    np.testing.assert_array_equal(ppg, window.ppg.values)


@pytest.mark.parametrize("case,flag", [("empty", "missing"), ("flat", "flat"), ("nan", "nonfinite"), ("inf", "nonfinite")])
def test_bad_channels_flagged_not_imputed(case, flag):
    w, _ = fixture()
    values = w.ppg.values.copy()
    if case == "empty":
        values = np.array([], dtype=float)
    elif case == "flat":
        values[:] = 1
    else:
        values[12] = np.nan if case == "nan" else np.inf
    result = extract_window(replace(w, ppg=replace(w.ppg, values=values)), SignalConfig())
    assert f"ppg:{flag}" in result["flags"]
    assert result["features"]["pat_median_ms"] is None
    assert result["features"]["ppg_hr_bpm"] is None


def test_timestamps_units_delays_and_gaps():
    w, _ = fixture()
    t = np.arange(len(w.ppg.values)) / w.ppg.fs_hz
    delayed = replace(w.ppg, timestamps=(t + 0.03) * 1e6, timestamp_unit="us", processing_delay_s=0.03)
    assert extract_window(replace(w, ppg=delayed), SignalConfig())["features"]["pat_median_ms"] == pytest.approx(200)
    t[500:] += 0.1
    result = extract_window(replace(w, ppg=replace(w.ppg, timestamps=t)), SignalConfig())
    assert "ppg:time_gap" in result["flags"]
    assert result["features"]["pat_median_ms"] is None
    t[1] = t[0]
    result = extract_window(replace(w, ppg=replace(w.ppg, timestamps=t)), SignalConfig())
    assert "ppg:invalid_timestamps" in result["flags"]


@pytest.mark.parametrize("case", ["alignment", "clock", "delay"])
def test_pat_requires_verified_timing(case):
    w, _ = fixture()
    if case == "alignment":
        w = replace(w, alignment_verified=False)
    else:
        w = replace(w, ppg=replace(w.ppg, **({"clock_id": None} if case == "clock" else {"processing_delay_s": None})))
    result = extract_window(w, SignalConfig())
    assert result["features"]["pat_median_ms"] is None
    assert result["features"]["ppg_hr_bpm"] is not None


def test_missing_beats_and_ambiguous_or_invalid_pat():
    cfg = SignalConfig()
    pairs, missing = pair_pat([1, 2, 3], [1.2, 3.2], cfg)
    assert len(pairs) == 2 and missing == 1
    assert pairs[1][:2] == (2, 1)
    assert pair_pat([1], [1.2, 1.3], cfg) == ([], 1)
    assert pair_pat([1], [0.9], cfg) == ([], 1)
    assert pair_pat([1], [1.6], cfg) == ([], 1)
    with pytest.raises(ValueError):
        pair_pat([1, 1], [1.2], cfg)
    w, _ = fixture(pat_s=0.6)
    assert extract_window(w, cfg)["features"]["pat_median_ms"] is None


def test_missing_pulse_does_not_pair_to_next_beat():
    w, _ = fixture()
    values = w.ppg.values.copy()
    times = np.arange(len(values)) / w.ppg.fs_hz
    values[(times >= 3.2) & (times < 3.6)] = 0
    result = extract_window(replace(w, ppg=replace(w.ppg, values=values)), SignalConfig())
    assert result["quality"]["pat_pair_count"] == 7
    assert result["quality"]["pat_unmatched_r_count"] == 1
    assert "pat:unmatched_beats" in result["flags"]
    assert result["features"]["pat_median_ms"] == pytest.approx(200)


def test_high_heart_rate_valley_stays_after_previous_peak():
    # RR 0.42 s < foot_lookback_s 0.5 s: the lowest sample of the lookback window
    # lies on the previous upstroke, before the previous peak.
    from software.feature_extraction.week04 import SignalWindow
    from software.signal_processing.fiducials import Channel, peaks, ppg_fiducials, prepare

    cfg, fs = SignalConfig(), 64
    r = 0.5 + 0.42 * np.arange(22)
    et, pt = np.arange(2500) / 250, np.arange(10 * fs) / fs
    ecg = sum(np.exp(-0.5 * ((et - t) / 0.015) ** 2) for t in r)
    ppg = np.zeros_like(pt)
    for foot in r + 0.2:
        x = pt - foot
        ppg = ppg + np.where((x >= 0) & (x <= 0.1), x / 0.1,
                             np.where(x > 0.1, np.exp(-(x - 0.1) / 0.3), 0))
    w, _ = fixture()
    window = SignalWindow(w.metadata, Channel(ecg, 250, "u", "SYN_CLOCK", processing_delay_s=0),
                          Channel(ppg, fs, "u", "SYN_CLOCK", processing_delay_s=0),
                          True, "Analytic common seconds axis; no upstream processing")
    values, times, _, _ = prepare(window.ppg, cfg, "ppg")
    peak_idx = peaks(values, times, fs, cfg)
    beats = ppg_fiducials(values, times, peak_idx, cfg)
    feet = np.array([b[0] for b in beats])
    assert (np.diff(feet) > 0).all()
    for foot, peak, valley, *_ in beats:
        earlier = peak_idx[peak_idx < peak]
        assert not len(earlier) or valley > earlier[-1]
    result = extract_window(window, cfg)
    assert result["features"]["pat_median_ms"] == pytest.approx(200, abs=1000 / fs)


def test_shape_flag_and_insufficient_beats():
    w, _ = fixture()
    values = w.ppg.values.copy()
    times = np.arange(len(values)) / w.ppg.fs_hz
    # Three pulses produce two dissimilar cycles: median correlation is not
    # expected to detect minority outliers in a majority-identical template.
    values[times >= 4] = 0
    for r in (2,):
        mask = (times >= r + 0.2) & (times < r + 0.6)
        x = times[mask] - (r + 0.2)
        values[mask] = np.where(x <= 0.08, x / 0.08, np.maximum(0, (0.16 - x) / 0.08))
    result = extract_window(replace(w, ppg=replace(w.ppg, values=values)), SignalConfig(shape_min_correlation=0.99))
    assert "ppg:shape_inconsistent" in result["flags"]
    short = replace(w, ecg=replace(w.ecg, values=w.ecg.values[:500]), ppg=replace(w.ppg, values=w.ppg.values[:250]))
    assert extract_window(short, SignalConfig())["features"]["pat_median_ms"] is None


def test_reader_adapter_never_uses_labels_or_abp():
    from software.pulsedb.reader import PulseSegment
    w, _ = fixture()
    seg = PulseSegment("SYN_001", "unknown", 0, 0, 0, 0, np.nan, np.nan,
                       w.ecg.values, w.ppg.values, np.full(1, np.nan))
    ecg = dict(fs_hz=250, unit="synthetic_unit", clock_id="SYN_CLOCK", processing_delay_s=0)
    ppg = dict(ecg, fs_hz=125)
    adapted = from_pulse_segment(seg, w.metadata, ecg, ppg, alignment_verified=True, alignment_basis="Fixture")
    assert extract_window(adapted, SignalConfig())["features"]["pat_median_ms"] == pytest.approx(200)
    with pytest.raises(ValueError, match="subject mismatch"):
        from_pulse_segment(seg, {**w.metadata, "subject_id": "OTHER"}, ecg, ppg)


def test_zero_phase_filter_and_config_validation():
    w, _ = fixture()
    result = extract_window(w, SignalConfig(filter_mode="zero_phase"))
    assert result["processing"]["filter_mode"] == "zero_phase"
    assert result["quality"]["ecg_peak_count"] >= 3
    with pytest.raises(ValueError):
        SignalConfig(pat_min_s=0.5, pat_max_s=0.4)
    with pytest.raises(ValueError):
        extract_window(w, SignalConfig(filter_mode="zero_phase", ppg_band_hz=(0.5, 100)))


def test_explicit_polarity_and_provenance_errors():
    w, _ = fixture()
    inverted = replace(w, ecg=replace(w.ecg, values=-w.ecg.values), ppg=replace(w.ppg, values=-w.ppg.values))
    result = extract_window(inverted, SignalConfig(ecg_polarity=-1, ppg_polarity=-1))
    assert result["features"]["pat_median_ms"] == pytest.approx(200)
    for field, value in (("raw_index", -1), ("source_sha256", "bad"), ("split", "other")):
        with pytest.raises(ValueError):
            extract_window(replace(w, metadata={**w.metadata, field: value}), SignalConfig())
    from software.feature_extraction.week04 import extract_windows
    with pytest.raises(ValueError, match="Duplicate"):
        extract_windows([w, w], SignalConfig())


def test_demo_saves_synthetic_outputs(tmp_path):
    from pathlib import Path
    config = Path(__file__).resolve().parents[1] / "configs/data/week04_huy.json"
    report = run(config, tmp_path / "report.json", tmp_path / "figure.svg")
    assert report["source_type"] == "SYNTHETIC"
    assert report["summary"]["input_segments"] == 5
    assert report["summary"]["pat_segments"] == 1
    assert (tmp_path / "figure.svg").exists()


def test_one_beat_config_never_produces_nonfinite_hr():
    import json
    w, _ = fixture()
    w = replace(w, ecg=replace(w.ecg, values=w.ecg.values[:500]),
                ppg=replace(w.ppg, values=w.ppg.values[:250]))
    result = extract_window(w, SignalConfig(min_beats=1))
    assert result["quality"]["ecg_peak_count"] == 1
    assert result["features"]["ecg_hr_bpm"] is None
    assert result["features"]["ppg_hr_bpm"] is None
    assert "insufficient_rr_intervals" in result["missing_reasons"]["ecg_hr_bpm"]
    assert all(v is None or np.isfinite(v) for v in result["features"].values())
    json.dumps(result, allow_nan=False)


def test_missing_reasons_are_feature_specific():
    w, _ = fixture()
    bad = replace(w, ppg=replace(w.ppg, values=np.zeros_like(w.ppg.values)),
                  alignment_verified=False)
    result = extract_window(bad, SignalConfig())
    assert "pat:" not in result["missing_reasons"]["ppg_std"]
    assert "alignment_unverified" in result["missing_reasons"]["pat_median_ms"]
    # A rising pulse that never drops below half height: no valid width.
    w = replace(w, ecg=replace(w.ecg, values=w.ecg.values[:375]),
                ppg=replace(w.ppg, values=w.ppg.values[:185]))
    result = extract_window(w, SignalConfig(min_beats=1))
    assert result["features"]["ppg_amplitude_median"] is not None
    assert result["features"]["ppg_width50_median_ms"] is None
    assert result["missing_reasons"]["ppg_width50_median_ms"] == "ppg:no_complete_half_height_pulse"
    assert "ppg:no_complete_half_height_pulse" in result["flags"]


@pytest.mark.parametrize("field,value", [
    ("ecg_polarity", True), ("ppg_polarity", "1"), ("sampling_rtol", True),
    ("edge_s", None), ("shape_min_correlation", "0.8"), ("flat_std", [1]),
    ("ecg_band_hz", None), ("ppg_band_hz", [False, 8]),
])
def test_config_types_rejected_with_value_error(field, value):
    with pytest.raises(ValueError):
        SignalConfig(**{field: value})


@pytest.mark.parametrize("field,value", [("fs_hz", "125"), ("start_s", True),
                                         ("processing_delay_s", "0"), ("clock_id", " SYN_CLOCK")])
def test_channel_metadata_types_rejected(field, value):
    w, _ = fixture()
    with pytest.raises(ValueError):
        extract_window(replace(w, ppg=replace(w.ppg, **{field: value})), SignalConfig())


def test_alignment_and_id_validation():
    w, _ = fixture()
    with pytest.raises(ValueError):
        extract_window(replace(w, alignment_basis=None), SignalConfig())
    for key in ("sample_id", "subject_id", "source"):
        with pytest.raises(ValueError):
            extract_window(replace(w, metadata={**w.metadata, key: " spaced "}), SignalConfig())


@pytest.mark.parametrize("change", ["fs", "timestamp", "delay", "clock", "alignment", "basis"])
def test_fixture_provenance_hashes_timing_and_alignment(change):
    w, _ = fixture()
    if change == "alignment":
        changed = replace(w, alignment_verified=False)
    elif change == "basis":
        changed = replace(w, alignment_basis="Different evidence")
    else:
        field, value = {"fs": ("fs_hz", 100), "timestamp": ("timestamps", np.arange(len(w.ppg.values)) / 125),
                        "delay": ("processing_delay_s", 0.01), "clock": ("clock_id", "OTHER")}[change]
        changed = replace(w, ppg=replace(w.ppg, **{field: value}))
    first, second = fixture_provenance(w), fixture_provenance(changed)
    assert first["waveform_sha256"] == second["waveform_sha256"]
    assert first["metadata_sha256"] != second["metadata_sha256"]
    assert first["input_sha256"] != second["input_sha256"]
    assert first == fixture_provenance(w)


def test_zero_phase_fixture_timing_with_declared_sample_tolerance():
    # Regression tolerance: two PPG samples, fixed for this analytic fixture.
    # Not a clinical timing limit and not used to tune filter/SQI parameters.
    w, expected_r = fixture()
    result = extract_window(w, SignalConfig(filter_mode="zero_phase"))
    assert result["fiducials"]["r_times_s"] == pytest.approx(expected_r, abs=1 / w.ecg.fs_hz)
    assert result["fiducials"]["foot_times_s"] == pytest.approx(expected_r + 0.2, abs=2 / w.ppg.fs_hz)
    assert result["features"]["pat_median_ms"] == pytest.approx(200, abs=2000 / w.ppg.fs_hz)
    assert all(v is None or np.isfinite(v) for v in result["features"].values())


def test_filter_short_window_and_edge_exclusion():
    w, _ = fixture()
    short = replace(w, ecg=replace(w.ecg, values=w.ecg.values[247:252]),
                    ppg=replace(w.ppg, values=w.ppg.values[165:170]))
    result = extract_window(short, SignalConfig(filter_mode="zero_phase", min_beats=1))
    assert "ecg:too_short_for_filter" in result["flags"]
    assert "ppg:too_short_for_filter" in result["flags"]
    assert result["features"]["pat_median_ms"] is None
    # Put the first R at 20 ms from the start of a cropped input.
    cropped = replace(w, ecg=replace(w.ecg, values=w.ecg.values[245:], start_s=0.98))
    result = extract_window(cropped, SignalConfig())
    assert 1.0 not in result["fiducials"]["r_times_s"]


def beat_window(r_times, fs=125, duration_s=10.0, pat_s=0.2):
    """Analytic beats anywhere in a PulseDB-like 10 s window, edges included."""
    base, _ = fixture()
    t = np.arange(int(duration_s * fs)) / fs
    r_times = np.asarray(r_times, dtype=float)
    ecg = sum(np.exp(-0.5 * ((t - r) / 0.015) ** 2) for r in r_times)
    ppg = np.zeros_like(t)
    for foot in r_times + pat_s:
        x = t - foot
        ppg += np.where((x >= 0) & (x <= 0.16), x / 0.16,
                        np.where((x > 0.16) & (x < 0.4), (0.4 - x) / 0.24, 0))
    return replace(base, ecg=Channel(ecg, fs, "synthetic_unit", "SYN_CLOCK", processing_delay_s=0),
                   ppg=Channel(ppg, fs, "synthetic_unit", "SYN_CLOCK", processing_delay_s=0))


def test_clean_beats_cut_by_window_edges_are_not_unmatched():
    # Regression: peaks() trims edge_s per channel, so an R near an edge could
    # lose its foot (or vice versa) although nothing is wrong with the signal.
    edge_total = 0
    for offset in (0.02, 0.05, 0.3, 0.6, 0.75):
        result = extract_window(beat_window(np.arange(offset, 10, 0.8)), SignalConfig())
        quality = result["quality"]
        assert "pat:unmatched_beats" not in result["flags"], offset
        assert quality["pat_unmatched_r_count"] == quality["pat_unmatched_foot_count"] == 0
        edge_total += quality["pat_edge_unpaired_r_count"] + quality["pat_edge_unpaired_foot_count"]
    assert edge_total > 0  # The exemption was actually exercised.


def test_interior_missing_pulse_is_still_unmatched_in_edge_spanning_window():
    window = beat_window(np.arange(0.05, 10, 0.8))
    values = window.ppg.values.copy()
    times = np.arange(len(values)) / window.ppg.fs_hz
    values[(times >= 4.2) & (times < 4.7)] = 0  # Remove the pulse after R = 4.05 s.
    result = extract_window(replace(window, ppg=replace(window.ppg, values=values)), SignalConfig())
    assert result["quality"]["pat_unmatched_r_count"] == 1
    assert "pat:unmatched_beats" in result["flags"]


def test_zero_phase_foot_bias_is_morphological_not_sampling():
    # Characterisation, not a tolerance: on this analytic pulse the band-pass
    # filter moves the tangent foot later by about +5.7 ms (documented in
    # docs/protocol/week04_features_sqi_bootstrap.md). R timing is unchanged.
    pat = {}
    for fs in (125, 500):
        window, _ = fixture(ecg_fs=fs, ppg_fs=fs)
        pat[fs] = {mode: extract_window(window, SignalConfig(filter_mode=mode))["features"]["pat_median_ms"]
                   for mode in ("none", "zero_phase")}
        assert pat[fs]["none"] == pytest.approx(200, abs=1e-6)
        assert 3 < pat[fs]["zero_phase"] - 200 < 8
    # The same shift at 125 and 500 Hz: a filter/morphology effect, not quantisation.
    assert pat[125]["zero_phase"] == pytest.approx(pat[500]["zero_phase"], abs=0.5)


def test_masked_timestamps_are_rejected():
    window, _ = fixture()
    stamps = np.ma.masked_array(np.arange(len(window.ppg.values)) / window.ppg.fs_hz)
    stamps[3] = np.ma.masked
    with pytest.raises(ValueError, match="Masked"):
        extract_window(replace(window, ppg=replace(window.ppg, timestamps=stamps)),
                       SignalConfig())
