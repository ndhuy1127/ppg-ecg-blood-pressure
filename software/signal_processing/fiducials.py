"""Preliminary offline fiducials; no BP/ABP inputs and no clock estimation."""

from dataclasses import dataclass
from numbers import Real

import numpy as np
from scipy.signal import butter, find_peaks, sosfiltfilt

# "prominence": local maxima (v0). "derivative_energy": maxima of a centred moving
# average of the squared first difference, refined to the signal maximum. This
# borrows the derivative/squaring idea but is NOT Pan-Tompkins: no fixed
# bandpass, no adaptive thresholds, no search-back.
R_METHODS = ("prominence", "derivative_energy")
# Prominence threshold of the derivative-energy envelope: "quantile" =
# prominence_fraction x (Q95 - Q05) of the energy (decided 2026-10-25), so that
# one large beat does not hide the others; "ptp" = x peak-to-peak (week 5 v0).
R_ENERGY_THRESHOLDS = ("quantile", "ptp")
# "tangent": max-upslope tangent meets valley level (v0). "d2_max": maximum of
# the second difference between valley and max upslope. "valley_min": last
# minimum before the upstroke. Both new ones may use parabolic sub-sample
# refinement (foot_interpolation, off by default since 2026-10-25).
FOOT_METHODS = ("tangent", "d2_max", "valley_min")
DEFAULT_METHODS = ("prominence", "tangent")


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
    # Week 5 candidate methods. Defaults reproduce features-sqi-v1 exactly.
    r_method: str = "prominence"
    foot_method: str = "tangent"
    r_energy_window_s: float = 0.1
    # Decided 2026-10-25 (docs/protocol/week05_fiducials_pat_validity.md section
    # 8). None: PPG peaks use refractory_s, as features-sqi-v1/v2 do.
    ppg_refractory_s: float | None = None
    foot_interpolation: bool = False
    r_energy_threshold: str = "quantile"

    def __post_init__(self):
        if self.r_method not in R_METHODS or self.foot_method not in FOOT_METHODS:
            raise ValueError(f"r_method must be one of {R_METHODS}, "
                             f"foot_method one of {FOOT_METHODS}")
        if finite_number(self.r_energy_window_s, "r_energy_window_s") <= 0:
            raise ValueError("r_energy_window_s must be finite and positive")
        if self.ppg_refractory_s is not None and finite_number(
                self.ppg_refractory_s, "ppg_refractory_s") <= 0:
            raise ValueError("ppg_refractory_s must be None or finite and positive")
        if not isinstance(self.foot_interpolation, bool):
            raise ValueError("foot_interpolation must be true or false")
        if self.r_energy_threshold not in R_ENERGY_THRESHOLDS:
            raise ValueError(f"r_energy_threshold must be one of {R_ENERGY_THRESHOLDS}")
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
        if np.ma.isMaskedArray(channel.timestamps):
            raise ValueError("Masked timestamps are not accepted; pass explicit values")
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
    if "invalid_timestamps" not in flags and (
        not np.isfinite(times).all() or (np.diff(times) <= 0).any()
    ):
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


def ppg_refractory(config):
    """Refractory period of PPG peaks: ppg_refractory_s, else refractory_s."""
    return config.refractory_s if config.ppg_refractory_s is None else config.ppg_refractory_s


def peaks(values, times, fs_hz, config, refractory_s=None):
    """Local maxima at least ``refractory_s`` apart (default config.refractory_s)."""
    refractory_s = config.refractory_s if refractory_s is None else refractory_s
    indices, _ = find_peaks(
        values, distance=max(1, int(np.ceil(refractory_s * fs_hz))),
        prominence=config.prominence_fraction * np.ptp(values),
    )
    return _inside_edges(indices, times, config)


def _inside_edges(indices, times, config):
    return indices[(times[indices] >= times[0] + config.edge_s)
                   & (times[indices] <= times[-1] - config.edge_s)]


def r_peaks(values, times, fs_hz, config):
    """R candidates by ``config.r_method`` on a prepared (oriented) ECG."""
    if config.r_method == "prominence":
        return peaks(values, times, fs_hz, config)
    if len(values) < 3:
        return np.array([], dtype=int)
    distance = max(1, int(np.ceil(config.refractory_s * fs_hz)))
    width = max(1, int(round(config.r_energy_window_s * fs_hz)))
    energy = np.convolve((np.diff(values, prepend=values[0]) * fs_hz) ** 2,
                         np.ones(width) / width, mode="same")
    if config.r_energy_threshold == "ptp":
        scale = np.ptp(energy)
    else:
        scale = np.quantile(energy, 0.95) - np.quantile(energy, 0.05)
    found, _ = find_peaks(energy, distance=distance,
                          prominence=config.prominence_fraction * scale)
    refined = []
    for index in found:
        low, high = max(0, index - width), min(len(values), index + width + 1)
        candidate = low + int(np.argmax(values[low:high]))
        # Refinement can pull two envelope peaks onto close samples; keep the
        # larger one so the refractory period still holds.
        if refined and candidate - refined[-1] < distance:
            if values[candidate] > values[refined[-1]]:
                refined[-1] = candidate
            continue
        refined.append(candidate)
    return _inside_edges(np.array(refined, dtype=int), times, config)


def _vertex_offset(y0, y1, y2, extremum):
    """Parabola vertex offset in samples from the middle point, clipped to ±0.5.

    ``extremum`` is "min" or "max". A parabola curved the wrong way has no
    vertex of that kind near the middle point, so the offset is 0 (no shift).
    """
    denominator = y0 - 2 * y1 + y2
    if (denominator <= 0) if extremum == "min" else (denominator >= 0):
        return 0.0
    return float(np.clip(0.5 * (y0 - y2) / denominator, -0.5, 0.5))


def _foot_time(values, times, valley, slope_index, tangent_foot, method, interpolate):
    """Foot time by ``method``; with ``interpolate``, a strict three-point extremum
    is refined by a parabola (at most half a sample). An asymmetric corner, as at
    a pulse onset, is still a strict extremum and refinement can ADD error
    (docs/protocol/week05_fiducials_pat_validity.md, sections 2 and 8)."""
    if method == "tangent":
        return tangent_foot
    offset = 0.0
    if method == "valley_min":
        index = valley
        # Never a plateau: only a strict local minimum.
        if (interpolate and 0 < index < len(values) - 1
                and values[index - 1] > values[index] < values[index + 1]):
            offset = _vertex_offset(*values[index - 1:index + 2], "min")
    else:
        low, high = max(valley, 1), min(slope_index, len(values) - 2)
        if high < low:
            return None
        d2 = values[low - 1:high] - 2 * values[low:high + 1] + values[low + 1:high + 2]
        index = low + int(np.argmax(d2))
        if interpolate and 1 < index < len(values) - 2:
            d2_here = [values[index + k - 1] - 2 * values[index + k] + values[index + k + 1]
                       for k in (-1, 0, 1)]
            # A strict maximum of the second difference, not only the curvature
            # sign: the argmax at the edge of the search is no extremum.
            if d2_here[0] < d2_here[1] > d2_here[2]:
                offset = _vertex_offset(*d2_here, "max")
    step = times[min(index + 1, len(times) - 1)] - times[max(index - 1, 0)]
    return float(times[index] + offset * step / 2)


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
        lowest = times[valley] - 1e-9
        if config.foot_method != "tangent" and config.foot_interpolation:
            # Parabolic refinement may move up to half a sample before the valley.
            lowest -= (times[valley] - times[max(valley - 1, 0)]) / 2
        foot = _foot_time(values, times, valley, slope_index, foot, config.foot_method,
                          config.foot_interpolation)
        if foot is None or not lowest <= foot < times[peak]:
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


def detect(channel: Channel, config: SignalConfig, kind: str):
    """Fiducial times (s) of one channel by the configured method, plus issues.

    ECG returns R times; PPG returns foot times. A channel with issues returns
    no fiducials, as in features-sqi-v1. Never reads BP/ABP.
    """
    if kind not in ("ecg", "ppg"):
        raise ValueError("kind must be ecg or ppg")
    values, times, issues, _ = prepare(channel, config, kind)
    if issues:
        return np.array([], dtype=float), issues
    if kind == "ecg":
        return times[r_peaks(values, times, channel.fs_hz, config)], []
    peak_indices = peaks(values, times, channel.fs_hz, config, ppg_refractory(config))
    beats = ppg_fiducials(values, times, peak_indices, config)
    return np.array([b[0] for b in beats], dtype=float), []


RISE_AFTER_R_V1 = "rise-after-r-v1"
# A rising run may be interrupted for at most this many forward steps (10 ms at
# 200 sps) by a flat or falling step that loses at most RUN_BRIDGE_DROP of the
# beat scale; quantization or residual noise then does not split one upstroke and
# raise B. A real notch between two waves is longer or deeper.
RUN_BRIDGE_STEPS = 2
RUN_BRIDGE_DROP = 0.02


def _rising_runs(values, times, bridge_steps=0, bridge_drop=0.0):
    """(start, stop, steepest) sample indices of every run where the forward slope
    stays positive: values rise from ``start`` to ``stop``; ``steepest`` is the
    middle of the equally steepest forward steps (as ``ppg_fiducials``). Runs
    separated by at most ``bridge_steps`` non-rising steps that lose at most
    ``bridge_drop`` (in signal units) are merged; the merged run keeps the start of
    the first part."""
    slopes = np.diff(values) / np.diff(times)
    raw, k = [], 0
    while k < len(slopes):
        if slopes[k] > 0:
            j = k
            while j < len(slopes) and slopes[j] > 0:
                j += 1
            raw.append([k, j])
            k = j
        else:
            k += 1
    merged = []
    for start, stop in raw:
        if merged:
            last = merged[-1]
            gap = start - last[1]
            drop = values[last[1]] - np.min(values[last[1]:start + 1])
            if gap <= bridge_steps and drop <= bridge_drop:
                last[1] = stop
                continue
        merged.append([start, stop])
    runs = []
    for start, stop in merged:
        part = slopes[start:stop]
        top = np.flatnonzero(np.isclose(part, part.max(), rtol=1e-6, atol=1e-12))
        runs.append((start, stop, start + int(top[len(top) // 2])))
    return runs, slopes


def feet_after_r(values, times, r_times, config, *, rise_min_fraction, ambiguous_fraction,
                 search_s):
    """PAT feet anchored on R (device-foot-v1 draft, rise-after-r-v1; docs/protocol/
    device_ppg_foot_definition_v1.md section 3) on a PREPARED (oriented, filtered)
    PPG window.

    Scale: the median over R of the local pulse range (max - min of the PPG in
    [R, min(next R, R + search_s))), so a distant artefact does not move it. For
    each R, rising runs (bridged as ``_rising_runs``) that start in that interval;
    a run qualifies when it climbs at least ``rise_min_fraction`` of the scale.
    The first qualifying run is the systolic rise: A is its steepest step, B the
    value at its start, and the foot is where the tangent at A meets B. Status per R:
    - "ok": that foot lies in [R + pat_min_s, R + pat_max_s];
    - "out_of_range": it does not (the limit applies to the extrapolated foot);
    - "no_rise": no qualifying run;
    - "ambiguous": an earlier run, climbing at least ``ambiguous_fraction`` of the
      scale but under the qualifying size, also has a foot in range (it may be the
      true onset), the foot is at or after the next R, or it is not after the
      previous beat's foot;
    - "edge": the foot is within ``config.edge_s`` of the window start, the chosen
      run reaches the window end (rise not complete), or no run qualifies while
      the interval starts before the PPG or runs past its end.
    A later qualifying run (a reflected wave, even a taller one) does not make the
    beat ambiguous. PPG-only features never use this: it needs R.

    Returns (feet of "ok" beats, strictly increasing; status per R; foot per R or
    None when no foot was extrapolated).
    """
    values = np.asarray(values, dtype=float)
    times = np.asarray(times, dtype=float)
    r_times = np.asarray(r_times, dtype=float)
    if not 0 < ambiguous_fraction < rise_min_fraction < 1 or search_s <= 0:
        raise ValueError("Need 0 < ambiguous_fraction < rise_min_fraction < 1, search_s > 0")
    n = len(r_times)
    if len(values) < 3 or not n:
        return np.array([], dtype=float), ["no_rise"] * n, [None] * n
    ends = [min(r + search_s, r_times[i + 1] if i + 1 < n else np.inf)
            for i, r in enumerate(r_times)]
    local = []
    for r, end in zip(r_times, ends):
        inside = values[(times >= r) & (times < end)]
        if len(inside) > 1:
            local.append(float(np.ptp(inside)))
    scale = float(np.median(local)) if local else 0.0
    runs, slopes = _rising_runs(values, times, RUN_BRIDGE_STEPS, RUN_BRIDGE_DROP * scale)
    last = len(values) - 1

    def foot_of(start, steep):
        return float(times[steep] - (values[steep] - values[start]) / slopes[steep])

    def in_range(r, foot):
        # Same 1e-6 ms boundary tolerance as pat_validity._in_range, so float
        # rounding never drops a PAT that sits on a limit.
        return r + config.pat_min_s - 1e-9 <= foot <= r + config.pat_max_s + 1e-9

    feet, status, per_r = [], [], []
    for i, (r, end) in enumerate(zip(r_times, ends)):
        next_r = r_times[i + 1] if i + 1 < n else np.inf
        chosen, earlier = None, []
        for start, stop, steep in runs:
            if not r <= times[start] < end:
                continue
            rise = values[stop] - values[start]
            if scale > 0 and rise >= rise_min_fraction * scale:
                chosen = (start, stop, steep)
                break
            if scale > 0 and rise >= ambiguous_fraction * scale:
                earlier.append((start, steep))
        if chosen is None:
            # No PPG over the whole interval (it starts before the window or runs
            # past its end) is an edge, not a missed beat.
            status.append("edge" if end > times[-1] or r < times[0] else "no_rise")
            per_r.append(None)
            continue
        start, stop, steep = chosen
        foot = foot_of(start, steep)
        per_r.append(foot)
        if stop >= last or foot < times[0] + config.edge_s:
            status.append("edge")
        elif not in_range(r, foot):
            status.append("out_of_range")
        elif (any(in_range(r, foot_of(*e)) for e in earlier) or foot >= next_r
              or (feet and foot <= feet[-1])):
            # An earlier candidate onset, a foot at or after the next R (it may
            # belong to that R), or a foot not after the previous beat's foot.
            status.append("ambiguous")
        else:
            feet.append(foot)
            status.append("ok")
    return np.array(feet, dtype=float), status, per_r


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