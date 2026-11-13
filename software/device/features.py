"""Fiducials, PAT and SQI flags of device windows (ECG 512 sps, PPG 200 sps).

Input is the output of ``session_ingest``: each channel keeps its own sample
times on the MCU clock (latency removed, PPG slot offset added). The two time
axes are joined by passing those times to ``fiducials.Channel(timestamps=...)``:
R and foot times come out on the one MCU clock and PAT = foot - R, with no
resampling and no shift of one channel onto the other.

Expected quantization (no interpolation): an R peak is a sample maximum, so its
time error is within half an ECG period (0.98 ms at 512 sps); a PPG foot picked
on a sample (valley_min) within half a PPG period (2.5 ms at 200 sps). The
tangent foot of features-sqi-v1 is sub-sample. PAT error from sampling is thus
within 0.98 + 2.5 = 3.5 ms in the worst case, before anchor jitter and the error
of the latency L.

The features and flags are those of ``features-sqi-v2`` (week04.py) and
``pat-validity-v1``, plus the hardware flags of SQI v1 section 3.3. Thresholds are
not locked (SQI v1: locked on G2). BP is never read here.
"""

import numpy as np

from software.data_io.live_monitor import adc_ceiling
from software.feature_extraction.week04 import VERSION_V2, SignalWindow, extract_window
from software.signal_processing.fiducials import Channel, SignalConfig
from software.signal_processing.pat_validity import (
    PatRules, detectable_foot_span, pat_beats,
)

VERSION = "device-features-v1"
PPG_KEYS = ("0xF1", "0xF2", "0xF3", "0xF4")


def ecg_codes(words):
    """Signed 18-bit ECG samples and ETAG of MAX30001 FIFO words (schema 8)."""
    words = np.asarray(words, dtype=np.int64)
    codes = (words >> 6) & 0x3FFFF
    codes = np.where(codes >= 1 << 17, codes - (1 << 18), codes)
    return codes, (words >> 3) & 7


def load_config(config):
    """(SignalConfig, PatRules) from ``configs/data/device_session_v1.json``."""
    return SignalConfig(**config["signal"]), PatRules(**config["pat_validity"])


def _slice(series, start_us, end_us):
    t = series.t_us
    keep = np.isfinite(t) & (t >= start_us) & (t < end_us)
    return np.flatnonzero(keep)


def _channel(series, rows, values, clock_id):
    return Channel(values=values, fs_hz=series.fs_nominal_hz, unit="adc_code",
                   clock_id=clock_id, timestamps=series.t_us[rows] / 1e6,
                   timestamp_unit="s",
                   processing_delay_s=0.0 if series.latency_applied else None)


def _packets_in(packets, key, chain, low, high):
    """Packets of ``key`` whose samples overlap index [low, high] of ``chain``."""
    return [p for p in packets if p["channel_id"] == key and p["chain_id"] == chain
            and p["sample_index_ext"] <= high
            and p["sample_index_ext"] + p["sample_count"] - 1 >= low]


def hardware_flags(series, rows_by_key, packets, session, colors, sqi, lock_applied_us,
                   start_us):
    """SQI v1 section 3.3 flags and continuous indices for one window."""
    flags, quality = [], {}
    states = [s for s in ((session.get("afe_config") or {}).get("MAX30101") or [])
              if s["source"] == "chip" and s["configured"]]
    ceiling = adc_ceiling(states[-1]["registers"]) if states else None
    bits = {0: "afe:fifo_overflow", 2: "ecg:lead_off", 6: "ppg:alc_overflow"}
    for key, rows in rows_by_key.items():
        s = series[key]
        if not len(rows):
            flags.append("stream:gap")
            continue
        for chain in np.unique(s.chain[rows]):
            idx = s.index[rows][s.chain[rows] == chain]
            for p in _packets_in(packets, key, int(chain), idx.min(), idx.max()):
                for bit, name in bits.items():
                    if p["status"] >> bit & 1 and (bit != 2 or key == "0xE1") and (
                            bit != 6 or key in PPG_KEYS):
                        flags.append(name)
            if len(np.setdiff1d(np.arange(idx.min(), idx.max() + 1), idx)):
                flags.append("stream:gap")
        if len(np.unique(s.chain[rows])) > 1:
            flags.append("stream:gap")
        if key in PPG_KEYS:
            if ceiling is None:
                quality[f"{colors.get(key, key)}_saturation_fraction"] = None
            else:
                fraction = float(np.mean(s.value[rows] >= ceiling))
                quality[f"{colors.get(key, key)}_saturation_fraction"] = fraction
                if fraction > sqi["adc_saturation_max_fraction"]:
                    flags.append("ppg:adc_saturation")
    if lock_applied_us is not None and lock_applied_us > start_us:
        flags.append("ppg:led_not_locked")
    return sorted(set(flags)), quality


def window_features(cuff, series, packets, session, config, identity):
    """Features and flags of one cuff in its primary window ``[t0 - L, t0)``.

    ``identity``: subject_id, session_id, recording, raw_sha256, source_type,
    clock_id. Every PPG colour is processed; ``pat_ppg_color`` names the one
    reported as the cuff's PAT."""
    signal, rules = load_config(config)
    t0 = cuff["t0_us"]
    pre = config["window"]["primary_pre_s"]
    start = t0 - pre * 1e6
    colors = {key: s.name for key, s in series.items() if key in PPG_KEYS}
    rows = {key: _slice(s, start, t0) for key, s in series.items()}
    lock = session.get("ppg_led_lock") or {}
    applied = (lock.get("applied") or {}).get("t_anchor_us") if lock else None
    hw_flags, hw_quality = hardware_flags(series, rows, packets, session, colors,
                                          config["sqi_hardware"], applied, start)
    out = {"version": VERSION, "event_id": cuff["event_id"], "phase": cuff["phase"],
           "window_pre_s": pre, "hardware_flags": hw_flags,
           "hardware_quality": hw_quality, "by_color": {}}
    if "0xE1" not in series:
        out["missing"] = "ecg"
        return out
    codes, _ = ecg_codes(series["0xE1"].value[rows["0xE1"]])
    ecg = _channel(series["0xE1"], rows["0xE1"], codes, identity["clock_id"])
    for key in [k for k in PPG_KEYS if k in series]:
        ppg = _channel(series[key], rows[key], series[key].value[rows[key]],
                       identity["clock_id"])
        verified = all(series[k].latency_applied for k in ("0xE1", key))
        metadata = {"sample_id": f"{identity['recording']}:{cuff['event_id']}:{key}",
                    "subject_id": identity["subject_id"] or "SYN_NONE",
                    "source": f"device:{identity['recording']}",
                    "source_sha256": identity["raw_sha256"],
                    "raw_index": int(cuff["t0_event_ordinal"]), "split": "device",
                    "event_id": cuff["event_id"],
                    "source_type": identity["source_type"]}
        if identity.get("session_id"):
            metadata["session_id"] = identity["session_id"]
        window = SignalWindow(metadata, ecg, ppg, alignment_verified=verified,
                              alignment_basis=("MCU esp_timer anchors, per-chain line "
                                               "fit, latency L from session metadata")
                              if verified else "")
        result = extract_window(window, signal, VERSION_V2)
        validity = None
        r = np.asarray(result["fiducials"]["r_times_s"])
        feet = np.asarray(result["fiducials"]["foot_times_s"])
        if verified and len(rows[key]) > 1 and len(r):
            span = detectable_foot_span(ppg.timestamps, signal.edge_s,
                                        signal.foot_lookback_s)
            validity = pat_beats(r, feet, rules, foot_span=span)
        out["by_color"][series[key].name] = {
            "channel": key, "features": result["features"], "flags": result["flags"],
            "quality": result["quality"], "fiducials": result["fiducials"],
            "pat_validity": None if validity is None else {
                k: validity[k] for k in ("version", "n_pairs", "n_valid",
                                         "n_out_of_range", "n_outlier", "n_unpaired_r",
                                         "n_no_foot", "n_edge", "median_valid_ms",
                                         "iqr_valid_ms", "flags", "pairs",
                                         "r_status")}}
    return out


def ecg_rmssd_ms(r_times_s, min_beats):
    """RMSSD of RR intervals (ms); proposal for the ablation's HRV, not locked."""
    rr = np.diff(np.asarray(r_times_s, dtype=float)) * 1000
    if len(rr) < max(2, min_beats - 1):
        return None
    return float(np.sqrt(np.mean(np.diff(rr) ** 2)))


def cuff_row(cuff, result, identity, color):
    """One row of the per-cuff feature table (docs/data_convention.md 4.6)."""
    chosen = result["by_color"].get(color) or {}
    features = chosen.get("features") or {}
    validity = chosen.get("pat_validity") or {}
    flags = sorted(set(result["hardware_flags"]) | set(chosen.get("flags") or []))
    r_times = (chosen.get("fiducials") or {}).get("r_times_s") or []
    return {
        "subject_id": identity["subject_id"], "session_id": identity["session_id"],
        "recording": identity["recording"], "event_id": cuff["event_id"],
        "phase": cuff["phase"], "status": cuff["status"],
        "safety_stop": int(cuff["safety_stop"]),
        "led_readjusted": int(cuff["led_readjusted"]), "pilot": int(cuff["pilot"]),
        "sbp_mmhg": cuff["sbp_mmhg"],
        "dbp_mmhg": cuff["dbp_mmhg"], "window_pre_s": result["window_pre_s"],
        "ppg_color": color,
        "ppg_rise_time_ms": features.get("ppg_rise_time_median_ms"),
        "ppg_width50_ms": features.get("ppg_width50_median_ms"),
        "ppg_amplitude": features.get("ppg_amplitude_median"),
        "ppg_hr_bpm": features.get("ppg_hr_bpm"),
        "ecg_hr_bpm": features.get("ecg_hr_bpm"),
        "ecg_rmssd_ms": ecg_rmssd_ms(r_times, 3) if r_times else None,
        "pat_ms": validity.get("median_valid_ms"),
        "pat_sqi_v2_median_ms": features.get("pat_median_ms"),
        "pat_n_valid": validity.get("n_valid"),
        "flags": ";".join(flags + list(cuff.get("flags") or [])),
        "source_type": identity["source_type"],
    }
