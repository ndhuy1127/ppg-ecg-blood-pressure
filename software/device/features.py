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

from software.data_io.live_monitor import adc_ceiling, led_codes
from software.device import ecg_anchor_residual as a10
from software.feature_extraction.week04 import VERSION_V2, SignalWindow, extract_window
from software.signal_processing import fiducials as fd
from software.signal_processing.fiducials import Channel, SignalConfig
from software.signal_processing.pat_validity import (
    PatRules, classify_pat, detectable_foot_span,
)

# v2 (2026-11-21): ECG timing flags of sync_10min_test_plan.md section 11.4 (A10
# per-packet state, ECG STATUS bit 3) and no PAT for a window that has them.
# v3 (2026-11-24): ecg:lead_off from the ECG signal instead of STATUS bit 2 (on the
# breakout v2 the chip's DC lead-off flag is set with good contact too; bring-up
# report 9.10), and no PAT for a window that has it.
# v4 (2026-11-25): PAT feet anchored on R (fiducials.feet_after_r, rise-after-r-v1,
# draft device-foot-v1: docs/protocol/device_ppg_foot_definition_v1.md); the PPG-only
# features keep the feet of features-sqi-v2.
VERSION = "device-features-v4"
PPG_KEYS = ("0xF1", "0xF2", "0xF3", "0xF4")
# LED lock states of a window (led_lock_status) that set ppg:led_not_locked.
LOCK_NOT_HELD = ("no_lock_metadata", "not_applied", "applied_after_window_start",
                 "state_unverified", "codes_differ")
# A10 states of an ECG packet that leave its anchor unchecked or failed.
A10_NOT_OK = ("flagged", "not_yet_scored")
# Flags that stop PAT for a window (sync_10min_test_plan.md section 11.4).
ECG_TIMING_FLAGS = ("ecg:timing_unverified", "ecg:afe_error")
PAT_BLOCKING_FLAGS = (*ECG_TIMING_FLAGS, "ecg:lead_off")
# MAX30001 CNFG_ECG (0x15) ECG_GAIN, D17:D16 (p. 53): the full scale of
# sqi_hardware.ecg_full_scale_mv (50 mV = VREF 1 V / 20 V/V) holds for code 00 only.
ECG_GAIN_SHIFT, ECG_GAIN_20 = 16, 0
# ETAG of a valid ECG sample (000, 010 EOF; p. 65 Table 48): a fast-recovery word
# (001, 011) carries no valid voltage and stays out of the lead-off level.
ECG_VALID_ETAGS = (0, 2)
LEAD_OFF_KEYS = ("ecg_lead_off_abs_mv", "ecg_lead_off_hold_s", "ecg_full_scale_mv")
PAT_FOOT_KEYS = ("method", "rise_min_fraction", "ambiguous_fraction", "search_s")
FOOT_STATUSES = ("ok", "out_of_range", "no_rise", "ambiguous", "edge")
# features-sqi-v2 flags of its own R-foot pairing: kept apart as legacy diagnostics,
# since the cuff's PAT comes from the R-anchored feet (v4).
LEGACY_PAT_FLAGS = ("pat:unmatched_beats", "pat:too_few_pairs")


def pat_from_feet(r_times, feet, status, per_r, rules):
    """PAT validity of one window from ``fiducials.feet_after_r``: one record per R
    keeps its detector status; the PAT of "ok" beats goes through ``classify_pat``
    (range and MAD outlier rule). Counts: n_pairs ("ok" beats) = n_valid + n_outlier
    + ok beats outside the pat_validity range; n_out_of_range adds the detector's
    out_of_range; n_no_foot ("no_rise"), n_ambiguous, n_edge; n_unpaired_r =
    n_no_foot + n_ambiguous; R = ok + detector out_of_range + n_unpaired_r + n_edge."""
    ok = [i for i, st in enumerate(status) if st == "ok"]
    pats = [(feet[k] - r_times[i]) * 1000 for k, i in enumerate(ok)]
    result = classify_pat(pats, rules)
    result["pairs"] = [(int(i), k, float(p)) for k, (i, p) in enumerate(zip(ok, pats))]
    result["r_status"] = list(status)
    # Detector out_of_range plus any ok beat that classify_pat put out of range
    # (if pat_validity were narrower than signal.pat_*), so the counts add up.
    result["n_out_of_range"] += status.count("out_of_range")
    result["n_no_foot"] = status.count("no_rise")
    result["n_ambiguous"] = status.count("ambiguous")
    result["n_edge"] = status.count("edge")
    result["n_unpaired_r"] = result["n_no_foot"] + result["n_ambiguous"]
    result["foot_status"] = {k: status.count(k) for k in FOOT_STATUSES}
    result["pat_feet_s"] = [float(f) for f in feet]
    result["foot_per_r_s"] = [None if f is None else float(f) for f in per_r]
    if result["n_unpaired_r"]:
        result["flags"] = sorted({*result["flags"], "pat:unmatched_beats"})
    result["detector"] = fd.RISE_AFTER_R_V1
    return result


def annotate_ecg_timing(packets):
    """Add ``a10_state`` (ecg_anchor_residual.classify) to every ECG packet row,
    in place; ``hardware_flags`` refuses ECG packets without it, so the 11.4 rule
    cannot be skipped by mistake. Call once per recording, on all its packets."""
    for p, state in zip(packets, a10.classify(packets)):
        if p["channel_id"] == a10.ECG_KEY:
            p["a10_state"] = state
    return packets


def ecg_codes(words):
    """Signed 18-bit ECG samples and ETAG of MAX30001 FIFO words (schema 8)."""
    words = np.asarray(words, dtype=np.int64)
    codes = (words >> 6) & 0x3FFFF
    codes = np.where(codes >= 1 << 17, codes - (1 << 18), codes)
    return codes, (words >> 3) & 7


def _valid_codes(series, rows):
    codes, etag = ecg_codes(series.value[rows])
    return codes[np.isin(etag, ECG_VALID_ETAGS)]


def ecg_lead_off(series, start_us, end_us, sqi):
    """(flag, quality) of the window [start_us, end_us), sync test plan 11.4 and
    SQI v1 section 3.3 (decided 2026-11-24): set when a valid ECG sample of
    [start_us - hold, end_us) reaches sqi.ecg_lead_off_abs_mv, so the hold after
    the last such sample (an electrode put back) is covered. Quality:
    ``ecg_max_abs_mv``, the largest valid |ECG| of the window itself (None without
    samples; it can stay under the level while the hold flags the window), and
    ``ecg_lead_off_lookback_s``, the seconds of ECG samples seen in the hold before
    the window (under the hold after a gap or near the recording start, where an
    earlier lead-off cannot be seen)."""
    hold_us = sqi["ecg_lead_off_hold_s"] * 1e6
    scale = sqi["ecg_full_scale_mv"] / (1 << 17)
    limit = sqi["ecg_lead_off_abs_mv"] / scale
    codes = _valid_codes(series, _slice(series, start_us - hold_us, end_us))
    flag = bool(len(codes)) and bool(np.max(np.abs(codes)) >= limit)
    window = _valid_codes(series, _slice(series, start_us, end_us))
    lookback = len(_slice(series, start_us - hold_us, start_us)) / series.fs_nominal_hz
    return flag, {"ecg_max_abs_mv": float(np.max(np.abs(window)) * scale) if len(window)
                  else None, "ecg_lead_off_lookback_s": float(lookback)}


def check_ecg_gain(session, source_type):
    """Refuse a recording whose MAX30001 ran with another ECG gain than 20 V/V at
    any time of the session: the lead-off level in mV assumes it. A DEVICE
    recording must show at least one configured chip state with CNFG_ECG (0x15);
    SYNTHETIC recordings carry none and are not checked."""
    states = [s for s in (session.get("afe_config") or {}).get("MAX30001") or []
              if s.get("source") == "chip" and s.get("configured")
              and (s.get("registers") or {}).get("0x15") is not None]
    if source_type != "SYNTHETIC" and not states:
        raise ValueError("no configured MAX30001 chip state with CNFG_ECG (0x15) in the "
                         "session: the ECG gain behind the lead-off level is unverified")
    for state in states:
        value = state["registers"]["0x15"]
        gain = int(value, 16) >> ECG_GAIN_SHIFT & 3
        if gain != ECG_GAIN_20:
            raise ValueError(f"MAX30001 ECG_GAIN {gain} (CNFG_ECG {value}): the "
                             "lead-off level assumes 20 V/V (code 00)")


def load_config(config):
    """(SignalConfig, PatRules) from ``configs/data/device_session_v1.json``; refuses
    a config without the lead-off keys of device-features-v3."""
    missing = [k for k in LEAD_OFF_KEYS if k not in config.get("sqi_hardware", {})]
    if missing:
        raise ValueError(f"sqi_hardware lacks {missing} (device-features-v3, "
                         "configs/data/device_session_v1.json since 2026-11-24)")
    foot = config.get("pat_foot", {})
    missing = [k for k in PAT_FOOT_KEYS if k not in foot]
    if missing or foot.get("method") != fd.RISE_AFTER_R_V1:
        raise ValueError(f"pat_foot needs {list(PAT_FOOT_KEYS)} with method "
                         f"{fd.RISE_AFTER_R_V1} (device-features-v4, 2026-11-25)")
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


def led_lock_status(session, start_us, end_us, study):
    """State of the locked LED codes (protocol 6.1) in the window [start_us, end_us),
    from the decoded session (SQI v1 section 3.3; fixed 2026-11-15). ``study``: the
    recording belongs to a subject (``subject_id`` set).

    - ``not_checked``: no ``ppg_led_lock`` and no subject (bring-up, SYNTHETIC);
    - ``no_lock_metadata``: a subject's recording without a lock (the LED
      calibration recording of the first session, or a metadata error);
    - ``not_applied``: no MAX30101 state of this device session carried the locked
      codes (logger issue ``ppg_led_lock_not_applied``: an MCU restart with the
      codes not sent again, say);
    - ``applied_after_window_start``: the locked codes took effect after the start;
    - ``state_unverified``: the state where the lock took effect is not found by
      sequence and generation, or the MAX30101 state in effect at the start, or one
      that began inside the window, is not a configured chip state (a fake source
      or a chip that is down); an earlier state is never carried across it;
    - ``codes_differ``: such a state has other LED codes than the state where the
      lock took effect (logger issue ``ppg_led_lock_mismatch``);
    - ``locked`` otherwise.

    Every state in ``LOCK_NOT_HELD`` sets ``ppg:led_not_locked``. The lock is the one
    of this recording's metadata; that a subject keeps the same codes in every
    session is not checked here (open, docs/protocol/device_session_pipeline.md)."""
    lock = session.get("ppg_led_lock")
    if lock is None:
        return "no_lock_metadata" if study else "not_checked"
    applied = lock.get("applied")
    if applied is None:
        return "not_applied"
    if applied["t_anchor_us"] > start_us:
        return "applied_after_window_start"
    states = sorted(((session.get("afe_config") or {}).get("MAX30101") or []),
                    key=lambda s: (s["t_anchor_us"], s["first_seq"]))
    locked = [led_codes(s["registers"]) for s in states
              if s["first_seq"] == applied["seq"]
              and s["generation"] == applied["generation"]
              and s["source"] == "chip" and s["configured"]]
    if not locked:
        return "state_unverified"
    before = [s for s in states if s["t_anchor_us"] <= start_us]
    during = [s for s in states if start_us < s["t_anchor_us"] < end_us]
    for state in before[-1:] + during:
        if not (state["source"] == "chip" and state["configured"]):
            return "state_unverified"
        if led_codes(state["registers"]) != locked[0]:
            return "codes_differ"
    return "locked"


def hardware_flags(series, rows_by_key, packets, session, colors, sqi, lock_status):
    """SQI v1 section 3.3 flags and continuous indices for one window;
    ``lock_status`` comes from ``led_lock_status``."""
    flags, quality = [], {}
    states = [s for s in ((session.get("afe_config") or {}).get("MAX30101") or [])
              if s["source"] == "chip" and s["configured"]]
    ceiling = adc_ceiling(states[-1]["registers"]) if states else None
    # STATUS bit 2 (ECG lead-off) is no longer a flag (device-features-v3):
    # ecg:lead_off comes from the signal, see ecg_lead_off.
    bits = {0: "afe:fifo_overflow", 6: "ppg:alc_overflow"}
    for key, rows in rows_by_key.items():
        s = series[key]
        if not len(rows):
            flags.append("stream:gap")
            continue
        for chain in np.unique(s.chain[rows]):
            idx = s.index[rows][s.chain[rows] == chain]
            for p in _packets_in(packets, key, int(chain), idx.min(), idx.max()):
                if key == a10.ECG_KEY:
                    # Section 11.4 of the sync test plan: an ECG anchor that A10
                    # flagged or could not check yet, or an AFE error (bit 3, which
                    # includes the FIFO-mode rate check), stops PAT for the window.
                    if "a10_state" not in p:
                        raise ValueError("ECG packets lack a10_state: call "
                                         "annotate_ecg_timing on the recording first")
                    if p["a10_state"] in A10_NOT_OK:
                        flags.append("ecg:timing_unverified")
                    if p["status"] >> 3 & 1:
                        flags.append("ecg:afe_error")
                for bit, name in bits.items():
                    if p["status"] >> bit & 1 and (bit != 6 or key in PPG_KEYS):
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
    if lock_status in LOCK_NOT_HELD:
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
    lock_status = led_lock_status(session, start, t0, bool(identity.get("subject_id")))
    hw_flags, hw_quality = hardware_flags(series, rows, packets, session, colors,
                                          config["sqi_hardware"], lock_status)
    if "0xE1" in series:
        check_ecg_gain(session, identity["source_type"])
        lead_off, quality = ecg_lead_off(series["0xE1"], start, t0, config["sqi_hardware"])
        hw_quality.update(quality)
        if lead_off:
            hw_flags = sorted({*hw_flags, "ecg:lead_off"})
    out = {"version": VERSION, "event_id": cuff["event_id"], "phase": cuff["phase"],
           "window_pre_s": pre, "hardware_flags": hw_flags,
           "hardware_quality": hw_quality, "led_lock_status": lock_status,
           "by_color": {}}
    has_ecg = "0xE1" in series and len(rows["0xE1"]) > 0
    if has_ecg:
        codes, _ = ecg_codes(series["0xE1"].value[rows["0xE1"]])
        ecg = _channel(series["0xE1"], rows["0xE1"], codes, identity["clock_id"])
    else:
        # No ECG sample in the window: PPG features are still computed, so the
        # cuff can enter PPG-only on every cuff (SAP endpoint 3, section 10); PAT
        # and ECG features stay empty (added 2026-11-14). The empty channel only
        # carries the nominal ECG rate of the config as a label.
        out["missing"] = "ecg"
        out["hardware_flags"] = sorted({*hw_flags, "ecg:absent"})
        ecg = Channel(values=np.array([], dtype=np.int64),
                      fs_hz=config["expected_rates_hz"]["0xE1"], unit="adc_code", clock_id=identity["clock_id"],
                      timestamps=np.array([], dtype=float), timestamp_unit="s",
                      processing_delay_s=None)
    for key in [k for k in PPG_KEYS if k in series]:
        ppg = _channel(series[key], rows[key], series[key].value[rows[key]],
                       identity["clock_id"])
        timing_ok = not set(PAT_BLOCKING_FLAGS) & set(out["hardware_flags"])
        verified = has_ecg and timing_ok and all(series[k].latency_applied
                                                  for k in ("0xE1", key))
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
        color_flags = [f for f in result["flags"] if f not in LEGACY_PAT_FLAGS]
        legacy_flags = [f for f in result["flags"] if f in LEGACY_PAT_FLAGS]
        r = np.asarray(result["fiducials"]["r_times_s"])
        feet = np.asarray(result["fiducials"]["foot_times_s"])
        if verified and len(rows[key]) > 1 and len(r):
            try:
                detectable_foot_span(ppg.timestamps, signal.edge_s,
                                            signal.foot_lookback_s)
            except ValueError:
                # The PPG covers too little of the window for any foot (under
                # 2 x edge_s + foot_lookback_s, 0.7 s) or its times are not
                # strictly increasing: no PAT for this colour, and the session
                # goes on (fixed 2026-11-15; before, one such window stopped the
                # whole session).
                color_flags.append("pat:no_foot_span")
            else:
                # PAT feet anchored on R (v4); the PPG-only features above keep
                # their own feet, found without R.
                values, times, issues, _ = fd.prepare(ppg, signal, "ppg")
                if issues:
                    color_flags.append("pat:ppg_not_usable")
                else:
                    pf = config["pat_foot"]
                    feet, foot_status, per_r = fd.feet_after_r(
                        values, times, r, signal, rise_min_fraction=pf["rise_min_fraction"],
                        ambiguous_fraction=pf["ambiguous_fraction"], search_s=pf["search_s"])
                    validity = pat_from_feet(r, feet, foot_status, per_r, rules)
                    color_flags.extend(validity["flags"])
        out["by_color"][series[key].name] = {
            "channel": key, "features": result["features"],
            "flags": sorted(set(color_flags)), "legacy_pat_flags": legacy_flags,
            "quality": result["quality"], "fiducials": result["fiducials"],
            "pat_validity": None if validity is None else {
                k: validity[k] for k in ("version", "n_pairs", "n_valid",
                                         "n_out_of_range", "n_outlier", "n_unpaired_r",
                                         "n_no_foot", "n_edge", "median_valid_ms",
                                         "iqr_valid_ms", "flags", "pairs",
                                         "r_status", "foot_status", "pat_feet_s",
                                         "foot_per_r_s", "n_ambiguous", "detector")}}
    return out


def ecg_rmssd_ms(r_times_s, min_beats):
    """RMSSD of RR intervals (ms), the ablation's HRV (approved 2026-11-14): a rough
    estimate from as few as three R peaks, with no ectopic-beat correction."""
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
        "session_start_utc": identity.get("session_start_utc"),
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
