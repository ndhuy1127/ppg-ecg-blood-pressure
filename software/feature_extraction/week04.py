"""Label-blind ECG/PPG features and diagnostic SQI flags, one output per input."""

from collections import Counter
from dataclasses import dataclass

import numpy as np

from software.signal_processing.fiducials import (
    Channel, SignalConfig, pair_pat, peaks, ppg_fiducials, prepare,
)

VERSION = "features-sqi-v1"
FEATURE_NAMES = (
    "ppg_std", "ppg_amplitude_median", "ppg_rise_time_median_ms",
    "ppg_width50_median_ms", "ppg_hr_bpm", "ecg_hr_bpm",
    "pat_median_ms", "pat_iqr_ms",
)


@dataclass(frozen=True)
class SignalWindow:
    metadata: dict
    ecg: Channel
    ppg: Channel
    alignment_verified: bool = False
    alignment_basis: str = ""


def _median(values):
    available = [v for v in values if v is not None and np.isfinite(v)]
    return float(np.median(available)) if available else None


def _heart_rate(times, minimum):
    if len(times) < max(2, minimum):
        return None
    intervals = np.diff(times)
    if not np.isfinite(intervals).all() or (intervals <= 0).any():
        return None
    with np.errstate(over="ignore", divide="ignore", invalid="ignore"):
        rate = 60 / np.median(intervals)
    return float(rate) if np.isfinite(rate) else None


def _shape_consistency(values, times, beats):
    waveforms = []
    for first, last in zip(beats[:-1], beats[1:]):
        grid = np.linspace(first[0], last[0], 64, endpoint=False)
        waveform = np.interp(grid, times, values)
        if np.std(waveform) > 0:
            waveforms.append((waveform - waveform.mean()) / waveform.std())
    if len(waveforms) < 2:
        return None
    template = np.median(waveforms, axis=0)
    if np.std(template) == 0:
        return None
    return _median([np.corrcoef(w, template)[0, 1] for w in waveforms])


def _partner_detectable(low, high, times, config, tail_s=0.0):
    """True where [low, high] lies inside the span where the other channel can
    yield fiducials (edge_s trimmed; tail_s extra at the end). An empty channel
    has no span, so nothing is exempted."""
    low, high = np.asarray(low, dtype=float), np.asarray(high, dtype=float)
    if not len(times):
        return np.ones(low.shape, dtype=bool)
    return (low >= times[0] + config.edge_s) & (high <= times[-1] - config.edge_s - tail_s)


def _unmatched(r_times, foot_times, pairs, ecg_times, ppg_times, config):
    """Split unpaired R/feet into interior (counted) and edge (exempt) beats.

    peaks() trims edge_s per channel, so a beat near a window edge can lose its
    partner without any signal problem. A foot is detectable only if its peak,
    at most foot_lookback_s later, is inside the PPG span.
    """
    paired_r = {p[0] for p in pairs}
    paired_foot = {p[1] for p in pairs}
    lone_r = np.array([t for i, t in enumerate(r_times) if i not in paired_r])
    lone_foot = np.array([t for j, t in enumerate(foot_times) if j not in paired_foot])
    r_inside = _partner_detectable(lone_r + config.pat_min_s, lone_r + config.pat_max_s,
                                   ppg_times, config, tail_s=config.foot_lookback_s)
    foot_inside = _partner_detectable(lone_foot - config.pat_max_s,
                                      lone_foot - config.pat_min_s, ecg_times, config)
    return (int(r_inside.sum()), int(len(lone_r) - r_inside.sum()),
            int(foot_inside.sum()), int(len(lone_foot) - foot_inside.sum()))


def extract_window(window: SignalWindow, config: SignalConfig) -> dict:
    """Only read ECG/PPG; never read ABP, BP labels, demographics or future data."""
    required = ("sample_id", "subject_id", "source", "source_sha256", "raw_index", "split")
    if not isinstance(window.metadata, dict) or any(k not in window.metadata for k in required):
        raise ValueError("Window needs manifest identity/provenance and split")
    for k in required[:-2]:
        if (not isinstance(window.metadata[k], str) or not window.metadata[k].strip()
                or window.metadata[k].strip() != window.metadata[k]):
            raise ValueError("Missing identity/provenance")
    if window.metadata["split"] not in ("train", "val", "test"):
        raise ValueError("Invalid split")
    checksum = window.metadata["source_sha256"]
    if len(checksum) != 64 or any(c not in "0123456789abcdef" for c in checksum):
        raise ValueError("source_sha256 must be lowercase SHA256")
    index = window.metadata["raw_index"]
    if isinstance(index, (bool, np.bool_)) or not isinstance(index, (int, np.integer)) or index < 0:
        raise ValueError("raw_index must be a nonnegative integer")
    if not isinstance(window.alignment_verified, bool):
        raise ValueError("alignment_verified must be explicit boolean")
    if not isinstance(window.alignment_basis, str):
        raise ValueError("alignment_basis must be text")
    for key in ("sample_hash", "waveform_hash", "record_id", "window_id", "session_id", "event_id", "source_type"):
        if key in window.metadata and (
            not isinstance(window.metadata[key], str) or not window.metadata[key]
            or window.metadata[key].strip() != window.metadata[key]
        ):
            raise ValueError(f"{key} must be nonempty text without edge whitespace")
    metadata = {k: window.metadata[k] for k in (
        *required, "sample_hash", "waveform_hash", "record_id", "window_id",
        "session_id", "event_id", "source_type",
    ) if k in window.metadata}
    features = dict.fromkeys(FEATURE_NAMES)
    flags, quality, prepared, detected, channel_issues = [], {}, {}, {}, {}
    for kind in ("ecg", "ppg"):
        channel = getattr(window, kind)
        values, times, issues, fraction = prepare(channel, config, kind)
        prepared[kind] = (values, times)
        channel_issues[kind] = [f"{kind}:{issue}" for issue in issues]
        quality[f"{kind}_finite_fraction"] = fraction
        quality[f"{kind}_std"] = float(np.std(values)) if len(values) and not issues else None
        flags.extend(f"{kind}:{issue}" for issue in issues)
        indices = peaks(values, times, channel.fs_hz, config) if not issues else np.array([], dtype=int)
        detected[kind] = indices
        quality[f"{kind}_peak_count"] = len(indices)
        if len(indices) < config.min_beats:
            flags.append(f"{kind}:too_few_peaks")
        if kind == "ecg":
            features["ecg_hr_bpm"] = _heart_rate(times[indices], config.min_beats)
            if features["ecg_hr_bpm"] is None:
                flags.append("ecg:insufficient_rr_intervals")
        if kind == "ppg" and not issues:
            features["ppg_std"] = float(np.std(values))
    pv, pt = prepared["ppg"]
    beats = ppg_fiducials(pv, pt, detected["ppg"], config) if len(detected["ppg"]) else []
    foot_times = np.array([b[0] for b in beats])
    quality["ppg_foot_count"] = len(beats)
    if len(beats) < config.min_beats:
        flags.append("ppg:too_few_feet")
    else:
        features["ppg_amplitude_median"] = _median([b[3] for b in beats])
        features["ppg_rise_time_median_ms"] = _median([(pt[b[1]] - b[0]) * 1000 for b in beats])
        features["ppg_width50_median_ms"] = _median([None if b[4] is None else b[4] * 1000 for b in beats])
        if features["ppg_width50_median_ms"] is None:
            flags.append("ppg:no_complete_half_height_pulse")
        features["ppg_hr_bpm"] = _heart_rate(foot_times, config.min_beats)
    if features["ppg_hr_bpm"] is None:
        flags.append("ppg:insufficient_foot_intervals")
    shape = _shape_consistency(pv, pt, beats)
    quality["ppg_shape_correlation"] = shape
    if shape is not None and shape < config.shape_min_correlation:
        flags.append("ppg:shape_inconsistent")
    r_times = prepared["ecg"][1][detected["ecg"]]
    timing_reasons = []
    if not window.alignment_verified or not window.alignment_basis.strip():
        timing_reasons.append("alignment_unverified")
    if window.ecg.clock_id is None or window.ecg.clock_id != window.ppg.clock_id:
        timing_reasons.append("clock_unverified")
    if any(c.processing_delay_s is None for c in (window.ecg, window.ppg)):
        timing_reasons.append("upstream_delay_unknown")
    pairs, _ = ([], len(r_times)) if timing_reasons else pair_pat(r_times, foot_times, config)
    flags.extend(f"pat:{r}" for r in timing_reasons)
    lone_r, edge_r, lone_foot, edge_foot = _unmatched(
        r_times, foot_times, pairs, prepared["ecg"][1], pt, config)
    quality["pat_pair_count"] = len(pairs)
    quality["pat_unmatched_r_count"] = lone_r
    quality["pat_unmatched_foot_count"] = lone_foot
    quality["pat_edge_unpaired_r_count"] = edge_r
    quality["pat_edge_unpaired_foot_count"] = edge_foot
    quality["pat_pair_fraction"] = len(pairs) / len(r_times) if len(r_times) else None
    if not timing_reasons and (lone_r or lone_foot):
        flags.append("pat:unmatched_beats")
    if len(pairs) < config.min_beats:
        flags.append("pat:too_few_pairs")
    else:
        pats = np.array([p[2] for p in pairs])
        features["pat_median_ms"] = float(np.median(pats))
        features["pat_iqr_ms"] = float(np.percentile(pats, 75) - np.percentile(pats, 25))
    missing_reasons = {}
    for name, value in features.items():
        if value is not None and not np.isfinite(value):
            features[name] = None
            missing_reasons[name] = "arithmetic_nonfinite"
            flags.append(f"feature:{name}:arithmetic_nonfinite")
        elif value is None:
            kind = "ecg" if name.startswith("ecg_") else "ppg"
            if name.startswith("pat_"):
                related = [f for f in flags if f.startswith("pat:")]
                related += channel_issues["ecg"] + channel_issues["ppg"]
            else:
                related = list(channel_issues[kind])
                if name == "ecg_hr_bpm":
                    related.append("ecg:insufficient_rr_intervals")
                elif name == "ppg_hr_bpm":
                    related.append("ppg:insufficient_foot_intervals")
                elif name != "ppg_std" and len(beats) < config.min_beats:
                    related.append("ppg:too_few_feet")
            if name == "ppg_width50_median_ms" and len(beats) >= config.min_beats:
                related = ["ppg:no_complete_half_height_pulse"]
            missing_reasons[name] = ";".join(sorted(set(related))) or "insufficient_valid_input"
    return {
        "version": VERSION, "metadata": metadata, "features": features,
        "missing_reasons": missing_reasons,
        "quality": quality, "flags": sorted(set(flags)), "flagged": bool(flags),
        "unavailable": {"motion": "No IMU", "saturation": "No ADC rails",
                        "ac_dc": "No physical DC/unit evidence"},
        "fiducials": {"r_times_s": r_times.tolist(), "foot_times_s": foot_times.tolist(),
                      "ppg_peak_times_s": pt[detected["ppg"]].tolist(), "pairs": pairs},
        "processing": {"filter_mode": config.filter_mode, "alignment_basis": window.alignment_basis,
                       "ecg_fs_hz": window.ecg.fs_hz, "ppg_fs_hz": window.ppg.fs_hz},
    }


def extract_windows(windows, config):
    rows = [extract_window(window, config) for window in windows]
    ids = [row["metadata"]["sample_id"] for row in rows]
    if len(set(ids)) != len(ids):
        raise ValueError("Duplicate sample_id in feature batch")
    return rows, {
        "input_segments": len(rows),
        "ppg_feature_segments": sum(r["features"]["ppg_hr_bpm"] is not None for r in rows),
        "pat_segments": sum(r["features"]["pat_median_ms"] is not None for r in rows),
        "flagged_segments": sum(r["flagged"] for r in rows),
        "flag_counts": dict(sorted(Counter(f for r in rows for f in r["flags"]).items())),
    }


def from_pulse_segment(segment, metadata, ecg_channel_metadata, ppg_channel_metadata,
                       *, alignment_verified=False, alignment_basis=""):
    """Adapter: explicit metadata required; never infer fs/clock from shape."""
    if segment.subject_id != metadata.get("subject_id"):
        raise ValueError("Reader/manifest subject mismatch")
    return SignalWindow(
        dict(metadata), Channel(segment.ecg, **ecg_channel_metadata),
        Channel(segment.ppg, **ppg_channel_metadata), alignment_verified, alignment_basis,
    )