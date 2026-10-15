"""Preliminary offline fiducials; no BP/ABP inputs and no clock estimation."""

from dataclasses import dataclass
from numbers import Real

import numpy as np
from scipy.signal import butter, find_peaks, sosfiltfilt


def finite_number(value, name):
    """Reject bool/string/array scalars consistently with ValueError."""
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Real) or not np.isfinite(value):
        raise ValueError(f"{name} must be a finite real number")
    return float(value)


@dataclass(frozen=True)
class Channel:
    values: np.ndarray
    fs_hz: float
    unit: str
    clock_id: str | None
    start_s: float = 0.0
    timestamps: np.ndarray | None = None
    timestamp_unit: str = "s"
    processing_delay_s: float | None = None


@dataclass(frozen=True)
class SignalConfig:
    """All defaults are engineering proposals, NOT validated clinical thresholds."""

    flat_std: float = 1e-8
    min_beats: int = 3
    refractory_s: float = 0.4
    prominence_fraction: float = 0.2
    foot_lookback_s: float = 0.5
    pat_min_s: float = 0.08
    pat_max_s: float = 0.4
    gap_factor: float = 1.5
    sampling_rtol: float = 0.05
    sampling_atol_s: float = 1e-6
    shape_min_correlation: float = 0.8
    edge_s: float = 0.1
    ecg_polarity: int = 1
    ppg_polarity: int = 1
    filter_mode: str = "none"
    ecg_band_hz: tuple[float, float] = (0.5, 40.0)
    ppg_band_hz: tuple[float, float] = (0.5, 8.0)
    filter_order: int = 2

    def __post_init__(self):
        for name in ("flat_std", "refractory_s", "foot_lookback_s", "pat_min_s",
                     "pat_max_s", "gap_factor", "prominence_fraction"):
            value = finite_number(getattr(self, name), name)
            if value <= 0:
                raise ValueError(f"{name} must be finite and positive")
        if self.pat_min_s >= self.pat_max_s or self.gap_factor <= 1:
            raise ValueError("Invalid PAT bounds or gap_factor")
        for value in (self.sampling_rtol, self.sampling_atol_s):
            if finite_number(value, "sampling tolerance") < 0:
                raise ValueError("Sampling tolerances must be finite and nonnegative")
        if not 0 < self.prominence_fraction < 1:
            raise ValueError("prominence_fraction must be in (0, 1)")
        if not -1 <= finite_number(self.shape_min_correlation, "shape_min_correlation") <= 1:
            raise ValueError("Invalid shape correlation threshold")
        if finite_number(self.edge_s, "edge_s") < 0:
            raise ValueError("edge_s must be finite and nonnegative")
        for value in (self.min_beats, self.filter_order):
            if isinstance(value, bool) or not isinstance(value, int) or value < 1:
                raise ValueError("Beat count/filter order must be positive integers")
        if any(finite_number(v, "polarity") not in (-1, 1) for v in (self.ecg_polarity, self.ppg_polarity)):
            raise ValueError("Polarity must be explicitly +1 or -1")
        if self.filter_mode not in ("none", "zero_phase"):
            raise ValueError("Only none/zero_phase filtering is supported")
        for band in (self.ecg_band_hz, self.ppg_band_hz):
            if not isinstance(band, (tuple, list)) or len(band) != 2:
                raise ValueError("Invalid filter band")
            low, high = (finite_number(v, "filter band") for v in band)
            if not 0 < low < high:
                raise ValueError("Invalid filter band")


def prepare(channel: Channel, config: SignalConfig, kind: str):
    """Return copied, oriented waveform/time/flags. Reject whole broken channels.

    No interpolation across gaps or nonfinite samples. Zero-phase filtering adds
    no constant group delay, but can change morphology; edges are excluded below.
    Upstream known constant processing delay is subtracted from acquisition times.
    """
    if finite_number(channel.fs_hz, "fs_hz") <= 0:
        raise ValueError("Channel requires positive fs_hz and finite start_s")
    finite_number(channel.start_s, "start_s")
    if not isinstance(channel.unit, str) or not channel.unit.strip():
        raise ValueError("Channel requires an explicit signal unit")
    if channel.clock_id is not None and (
        not isinstance(channel.clock_id, str) or not channel.clock_id.strip()
        or channel.clock_id.strip() != channel.clock_id
    ):
        raise ValueError("clock_id must be nonempty or None")
    if channel.timestamp_unit not in ("s", "ms", "us"):
        raise ValueError("Unsupported timestamp unit")
    if channel.processing_delay_s is not None and finite_number(channel.processing_delay_s, "processing_delay_s") < 0:
        raise ValueError("Known processing delay must be finite and nonnegative")
    raw = np.asarray(channel.values)
    if np.ma.isMaskedArray(channel.values) or raw.ndim != 1 or raw.dtype.kind not in "iuf":
        raise ValueError("Signal must be a real numeric vector (possibly empty)")
    values = raw.astype(float, copy=True)
    times = channel.start_s + np.arange(len(values)) / channel.fs_hz
    flags = []
    if channel.timestamps is not None:
        given = np.asarray(channel.timestamps)
        if given.shape != values.shape or given.dtype.kind not in "iuf":
            raise ValueError("Timestamp vector must match signal shape")
        times = given.astype(float, copy=True) * {"s": 1, "ms": 1e-3, "us": 1e-6}[channel.timestamp_unit]
        if not np.isfinite(times).all() or (np.diff(times) <= 0).any():
            flags.append("invalid_timestamps")
        elif (np.diff(times) > config.gap_factor / channel.fs_hz).any():
            flags.append("time_gap")
        elif len(times) > 1 and not np.allclose(
            np.diff(times), 1 / channel.fs_hz, rtol=config.sampling_rtol, atol=config.sampling_atol_s
        ):
            flags.append("sampling_inconsistent")
    if channel.processing_delay_s is not None:
        times = times - channel.processing_delay_s
    if not np.isfinite(times).all() or (np.diff(times) <= 0).any():
        flags.append("invalid_timestamps")
    finite_fraction = float(np.isfinite(values).mean()) if len(values) else 0.0
    if not len(values):
        flags.append("missing")
    elif finite_fraction < 1:
        flags.append("nonfinite")
    elif not np.isfinite(np.std(values)):
        flags.append("arithmetic_overflow")
    elif np.std(values) <= config.flat_std:
        flags.append("flat")
    if flags:
        return values, times, flags, finite_fraction
    values *= config.ecg_polarity if kind == "ecg" else config.ppg_polarity
    if config.filter_mode == "zero_phase":
        band = config.ecg_band_hz if kind == "ecg" else config.ppg_band_hz
        if band[1] >= channel.fs_hz / 2:
            raise ValueError("Filter band exceeds this channel's Nyquist frequency")
        sos = butter(config.filter_order, band, btype="bandpass", fs=channel.fs_hz, output="sos")
        try:
            values = sosfiltfilt(sos, values)
            if not np.isfinite(values).all():
                flags.append("filter_nonfinite")
        except ValueError:
            flags.append("too_short_for_filter")
    return values, times, flags, finite_fraction


def peaks(values, times, fs_hz, config):
    indices, _ = find_peaks(
        values, distance=max(1, int(np.ceil(config.refractory_s * fs_hz))),
        prominence=config.prominence_fraction * np.ptp(values),
    )
    return indices[(times[indices] >= times[0] + config.edge_s)
                   & (times[indices] <= times[-1] - config.edge_s)]


def ppg_fiducials(values, times, peak_indices, config):
    """Intersect maximum-upslope tangent with preceding valley level.

    Returns (foot time, peak index, valley index, amplitude, half-height width).
    Foot is sub-sample; ambiguous/invalid tangent or incomplete pulse is skipped.
    """
    beats = []
    previous_peak = -1
    for peak in peak_indices:
        start = int(np.searchsorted(times, times[peak] - config.foot_lookback_s))
        # Valley must follow the previous peak; otherwise at high HR two beats
        # share one valley and their feet coincide or cross.
        start = max(start, previous_peak + 1)
        previous_peak = int(peak)
        before = values[start:peak]
        if len(before) < 3:
            continue
        valley = start + np.flatnonzero(before == before.min())[-1]
        if peak - valley < 2:
            continue
        slopes = np.diff(values[valley:peak + 1]) / np.diff(times[valley:peak + 1])
        maximum = slopes.max()
        if maximum <= 0:
            continue
        # Middle of equally steep ramp avoids choosing an arbitrary first edge.
        candidates = np.flatnonzero(np.isclose(slopes, maximum, rtol=1e-6, atol=1e-12))
        slope_index = valley + candidates[len(candidates) // 2]
        foot = times[slope_index] - (values[slope_index] - values[valley]) / maximum
        if not times[valley] - 1e-9 <= foot < times[peak]:
            continue
        if foot < times[0] + config.edge_s:
            continue
        amplitude = values[peak] - values[valley]
        half = values[valley] + amplitude / 2
        left = np.flatnonzero(values[valley:peak + 1] >= half)
        end = int(np.searchsorted(times, times[peak] + config.foot_lookback_s))
        right = np.flatnonzero(values[peak:end] <= half)
        width = None
        if len(left) and len(right):
            li = valley + left[0]
            ri = peak + right[0]
            if li > valley and ri > peak:
                lt = np.interp(half, values[li - 1:li + 1], times[li - 1:li + 1])
                rt = np.interp(half, values[ri:ri - 2:-1], times[ri:ri - 2:-1])
                width = float(rt - lt)
        beats.append((float(foot), int(peak), int(valley), float(amplitude), width))
    return beats


def pair_pat(r_times, foot_times, config):
    """One-to-one forward pairing; reject ambiguous candidates and crossed beats."""
    r_times, foot_times = np.asarray(r_times), np.asarray(foot_times)
    for times in (r_times, foot_times):
        if times.ndim != 1 or not np.isfinite(times).all() or (np.diff(times) <= 0).any():
            raise ValueError("Fiducial times must be finite and strictly increasing")
    pairs = []
    rejected = 0
    for i, r in enumerate(r_times):
        upper = min(r + config.pat_max_s, r_times[i + 1] if i + 1 < len(r_times) else np.inf)
        candidates = np.flatnonzero((foot_times >= r + config.pat_min_s) & (foot_times <= upper))
        if len(candidates) != 1:
            rejected += 1
            continue
        j = int(candidates[0])
        # A foot inside more than one eligible R interval is not identifiable.
        owners = (foot_times[j] - r_times >= config.pat_min_s) & (foot_times[j] - r_times <= config.pat_max_s)
        if owners.sum() != 1:
            rejected += 1
            continue
        pairs.append((int(i), j, float((foot_times[j] - r) * 1000)))
    return pairs, rejected