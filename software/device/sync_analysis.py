"""ECG-PPG offset from the common stimulus (sync-analysis-v2).

Implements the analysis of hardware/test_reports/sync_10min_test_plan.md sections
5, 9 and 11 for the FIFO-anchor mode (ECG bit 8 off): per stimulus event (0xC1
code 3) the response centre on each channel, the effective latency L, the
ECG-PPG offset and the criteria A1-A4, A6, A7, A9-A11 of one run, and A5 over
runs. The edge rule is fixed in section 5 of the plan ("Quy tắc cạnh", decided
2026-11-21 before any measurement) and repeated in ``EDGE``. v2 (same day, before
any measurement): a time-axis model per run (line or segmented-60s, plan section
9), A11 on a time axis refitted to each block, offsets per minute (report only),
A5 over runs of one model.

Inputs come from ``session_ingest.load_recording`` (a verified logger
recording). Pure functions: no file access, no printing. SYNTHETIC tests only
verify code; no number here is a device result.
"""

import math
import re

import numpy as np

from software.device import ecg_anchor_residual as a10
from software.device import session_ingest as si
from software.device.features import ecg_codes

VERSION = "sync-analysis-v2"
ECG, PPG_SLOTS = "0xE1", ("0xF1", "0xF2", "0xF3")
STIM_CODE, BOUNDARY_CODE = 3, 2
WIDTH_US = 50_000  # firmware STIM_WIDTH_US (nominal; checked by oscilloscope)
# Edge rule (plan section 5, "Quy tắc cạnh"): windows in us from the event anchor.
EDGE = {
    "pre_us": (-250_000, -50_000),
    "post_us": (200_000, 400_000),
    "plateau_us": {ECG: (45_000, 75_000), "ppg": (10_000, 40_000)},
    "rise_us": (-20_000, None),        # until the plateau starts
    "fall_after_plateau_us": 60_000,   # fall searched until plateau end + this
    "noise_factor": 10.0,
    "amplitude_floor": 20.0,           # ADC codes
    "width_tolerance_us": 10_000,
}
STABILIZATION_S = 60.0
BOOT_B, BOOT_SEED, BLOCK_S = 2000, 20261121, 60.0
LIMITS = {"a2_ecg_ppm": 1000.0, "a2_ppg_fraction": 0.03, "a3_us": 200.0,
          "a4_half_ci_us": 150.0, "a5_range_us": 300.0, "a6_range_us": 400.0,
          "a9_bin_fraction": 0.05, "a11_diff_us": 300.0}
A6_BLOCK_S, A6_BLOCKS = 1200.0, 6
A11 = {"boundaries": 13, "block_s": 120.0, "spacing_tolerance_s": 2.0, "guard_s": 10.0}


class SyncError(ValueError):
    """The recording cannot be analysed by this method."""


def _window(t, lo, hi):
    return (t >= lo) & (t < hi)


def _crossings(t, x, thr, lo, hi):
    """Upward and downward crossings of ``thr`` with the later sample in
    [lo, hi); times by linear interpolation between the two samples."""
    ups, downs = [], []
    for i in np.nonzero(_window(t, lo, hi))[0]:
        if i == 0:
            continue
        a, b = x[i - 1], x[i]
        if a < thr <= b or a >= thr > b:
            when = t[i - 1] + (thr - a) / (b - a) * (t[i] - t[i - 1])
            (ups if b > a else downs).append(float(when))
    return ups, downs


def event_response(t, x, chain, index, t_event, kind, clip=None):
    """Response of one channel to one event: dict with ``status`` ("ok" or the
    reason it was rejected) and, when ok, ``rise_us``, ``fall_us``,
    ``center_us``, ``latency_us`` (centre minus the input centre), amplitude
    and noise. ``kind`` is "ecg" or "ppg"; ``clip`` (lo, hi) codes reject a
    window that touches them. ``t`` must be increasing; only the samples around
    the event are looked at (one sample before the window is kept, for the
    interpolation of a crossing at its start)."""
    lo_all = t_event + EDGE["pre_us"][0]
    hi_all = t_event + EDGE["post_us"][1]
    first = max(int(np.searchsorted(t, lo_all, side="left")) - 1, 0)
    last = int(np.searchsorted(t, hi_all, side="left"))
    t, x = t[first:last], x[first:last]
    chain, index = chain[first:last], index[first:last]
    span = _window(t, lo_all, hi_all)
    if not span.any():
        return {"status": "no_samples"}
    ch, ix = chain[span], index[span]
    if len(np.unique(ch)) > 1 or np.any(np.diff(ix) != 1):
        return {"status": "gap"}
    if clip is not None and (np.any(x[span] <= clip[0]) or np.any(x[span] >= clip[1])):
        return {"status": "clipped"}
    pre = x[_window(t, t_event + EDGE["pre_us"][0], t_event + EDGE["pre_us"][1])]
    post = x[_window(t, t_event + EDGE["post_us"][0], t_event + EDGE["post_us"][1])]
    p_lo, p_hi = EDGE["plateau_us"][ECG if kind == "ecg" else "ppg"]
    plateau = x[_window(t, t_event + p_lo, t_event + p_hi)]
    if len(pre) < 3 or len(post) < 3 or len(plateau) < 3:
        return {"status": "no_samples"}
    low = (float(np.median(pre)) + float(np.median(post))) / 2
    noise = float(np.std(pre, ddof=1))
    amplitude = float(np.median(plateau)) - low
    if amplitude < max(EDGE["noise_factor"] * noise, EDGE["amplitude_floor"]):
        return {"status": "not_detected", "amplitude": amplitude, "noise": noise}
    thr = low + amplitude / 2
    ups, downs = _crossings(t, x, thr, t_event + EDGE["rise_us"][0], t_event + p_lo)
    if len(ups) != 1 or downs:
        return {"status": "rise_not_unique"}
    f_ups, f_downs = _crossings(t, x, thr, t_event + p_hi,
                                t_event + p_hi + EDGE["fall_after_plateau_us"])
    if len(f_downs) != 1 or f_ups:
        return {"status": "fall_not_unique"}
    rise, fall = ups[0], f_downs[0]
    if abs(fall - rise - WIDTH_US) > EDGE["width_tolerance_us"]:
        return {"status": "bad_width", "width_us": fall - rise}
    center = (rise + fall) / 2
    return {"status": "ok", "rise_us": rise, "fall_us": fall, "center_us": center,
            "latency_us": center - (t_event + WIDTH_US / 2), "amplitude": amplitude,
            "noise": noise}


def _bootstrap_mean(values, groups=None, b=BOOT_B, seed=BOOT_SEED):
    """Percentile 95 % CI of the mean; resample ``groups`` (blocks) if given."""
    values = np.asarray(values, float)
    rng = np.random.default_rng(seed)
    if groups is None:
        draws = rng.integers(0, len(values), (b, len(values)))
        means = values[draws].mean(axis=1)
    else:
        groups = np.asarray(groups)
        labels = np.unique(groups)
        members = [values[groups == g] for g in labels]
        means = np.empty(b)
        for i in range(b):
            pick = rng.integers(0, len(labels), len(labels))
            means[i] = np.concatenate([members[j] for j in pick]).mean()
    lo, hi = np.percentile(means, [2.5, 97.5])
    return float(lo), float(hi)


def offset_summary(offsets, times_us):
    """Mean offset with event and 60 s block bootstrap CIs; the A4 half-width
    is the wider of the two (plan 11.2, the stricter reading)."""
    offsets = np.asarray(offsets, float)
    if len(offsets) < 2:
        return {"n_events": int(len(offsets)), "mean_us": None}
    times = np.asarray(times_us, float)
    blocks = np.floor((times - times.min()) / (BLOCK_S * 1e6)).astype(int)
    ev = _bootstrap_mean(offsets)
    bl = _bootstrap_mean(offsets, blocks) if len(np.unique(blocks)) > 1 else None
    # Both CIs are needed: with one 60 s block there is no block CI, so no A4.
    half = None if bl is None else max((ev[1] - ev[0]) / 2, (bl[1] - bl[0]) / 2)
    return {"n_events": int(len(offsets)), "mean_us": float(offsets.mean()),
            "median_us": float(np.median(offsets)), "sd_us": float(np.std(offsets, ddof=1)),
            "ci_event_us": ev, "ci_block_us": bl, "a4_half_ci_us": half}


def phase_coverage(phases, bins=10):
    """Fraction of events in each of ``bins`` phase cells; passes A9 when every
    cell holds at least 5 %."""
    if not len(phases):
        return {"fractions": None, "passed": None}
    counts = np.bincount(np.minimum((np.asarray(phases) * bins).astype(int), bins - 1),
                         minlength=bins)
    fractions = counts / counts.sum()
    return {"fractions": [round(float(f), 4) for f in fractions],
            "passed": bool(fractions.min() >= LIMITS["a9_bin_fraction"])}


def _phase(t_event, fit, offset_us=0.0):
    """Phase of ``t_event`` on the sample grid of a chain: the fractional part of
    the sample index at that time (inverse of the time axis, slot offset
    removed). A line keeps the v1 expression, so its bins do not move."""
    if not fit.get("knots_k"):
        return ((t_event - fit["a_us"] - offset_us) / fit["b_us"]) % 1.0
    return float(si.timebase_index_at(fit, t_event - offset_us)) % 1.0


def _nearest(t_us, t_event):
    """Index of the sample nearest ``t_event`` among samples with a time (a chain
    without a reliable anchor has NaN times)."""
    return int(np.nanargmin(np.abs(t_us - t_event)))


def _fit_at(timebase, key, chain_id):
    for row in timebase:
        if row["channel"] == key and row["chain_id"] == chain_id and "a_us" in row:
            return row
    return None


def _a1(decode, session):
    channels = session["channels"]
    # Every channel of the session, events included (a lost stimulus packet
    # would remove an event silently).
    missing = sum(c.get("missing_packets", 0) for c in channels.values())
    bit0 = sum(channels[k].get("status_bit_counts", {}).get("afe_fifo_overflow", 0)
               for k in (ECG, *PPG_SLOTS) if k in channels)
    crc = sum(decode["decode"]["errors"].values())
    return {"missing_packets": missing, "status_bit0_packets": bit0, "decode_errors": crc,
            "passed": missing == 0 and bit0 == 0 and crc == 0}


def analyze_run(recording, session_index=0, stabilization_s=STABILIZATION_S,
                timebase_model="line"):
    """One sync run of one device session; see the module docstring.
    ``timebase_model`` is chosen for the whole validation series (plan section
    9): "line", or "segmented-60s" for every run once one run fails A3 with the
    line; never from A4-A6 or A11."""
    decode = recording["decode"]
    session = decode["sessions"][session_index]
    sid = session["session_id"]
    version = int(session["packet_schema"].rsplit("v0.", 1)[1])
    packets = [p for p in recording["packets"]
               if (p["session_id"], p["version"]) == (sid, version)]
    if any(p["channel_id"] == ECG and p["status"] >> 8 & 1 for p in packets):
        raise SyncError("ECG packets carry SAMP anchors (bit 8): this is the FIFO-anchor "
                        "analysis (plan section 11)")
    series, timebase, _ = si.session_series(recording, session_index, timebase_model)
    for key in (ECG, *PPG_SLOTS):
        if key not in series:
            raise SyncError(f"No {key} samples in the session")
        if series[key].latency_applied:
            raise SyncError(f"{key}: latency_l_us is set in the metadata; the sync run "
                            "measures L, so it must be null")
        if key in PPG_SLOTS and series[key].slot_offset_us is None:
            raise SyncError(f"{key}: PPG slot spacing unknown (no 0xD2 LED_PW)")
    events = [e for e in si.session_events(recording, session_index)]
    stim = [e for e in events if e["code"] == STIM_CODE]
    if not stim:
        raise SyncError("No stimulus event (0xC1 code 3)")
    start = stim[0]["t_us"] + stabilization_s * 1e6
    stim = [e for e in stim if e["t_us"] >= start]
    ecg_values = ecg_codes(series[ECG].value)[0].astype(float)
    clip = {ECG: (-(1 << 17), (1 << 17) - 1)}
    for key in PPG_SLOTS:
        clip[key] = (0, (1 << 18) - 1)
    rows = []
    for e in stim:
        row = {"event_ordinal": e["event_ordinal"], "t_event_us": e["t_us"]}
        for key in (ECG, *PPG_SLOTS):
            s = series[key]
            values = ecg_values if key == ECG else s.value.astype(float)
            r = event_response(s.t_us, values, s.chain, s.index, e["t_us"],
                               "ecg" if key == ECG else "ppg", clip[key])
            row[f"{key}_status"] = r["status"]
            row[f"{key}_latency_us"] = r.get("latency_us")
            near = _nearest(s.t_us, e["t_us"])
            fit = _fit_at(timebase, key, int(s.chain[near]))
            row[f"{key}_phase"] = (None if fit is None else
                                   float(_phase(e["t_us"], fit, s.slot_offset_us or 0.0)))
        slots = [row[f"{k}_latency_us"] for k in PPG_SLOTS]
        ppg_ok = all(row[f"{k}_status"] == "ok" for k in PPG_SLOTS)
        row["ppg_latency_us"] = float(np.mean(slots)) if ppg_ok else None
        ok = ppg_ok and row[f"{ECG}_status"] == "ok"
        row["offset_us"] = row[f"{ECG}_latency_us"] - row["ppg_latency_us"] if ok else None
        rows.append(row)
    used = [r for r in rows if r["offset_us"] is not None]
    result = {"method": VERSION, "edge_rule": EDGE, "limits": LIMITS,
              "timebase_model": timebase_model, "session_id": sid, "events_total": len(rows), "events_used": len(used),
              "rejections": {key: _count(rows, key) for key in (ECG, *PPG_SLOTS)}}
    result["offset"] = offset_summary([r["offset_us"] for r in used],
                                      [r["t_event_us"] for r in used])
    result["offset_by_minute_us"] = _by_minute(used)
    # Each channel on its own accepted events (A7 jitter); the offset needs all four.
    result["latency"] = {
        key: _mean_sd([r[f"{key}_latency_us"] for r in rows]) for key in (ECG, *PPG_SLOTS)}
    result["latency"]["ppg"] = _mean_sd([r["ppg_latency_us"] for r in rows])
    # Slot residuals and pair differences (a swapped or mis-spaced slot shows here).
    ppg_rows = [r for r in rows if r["ppg_latency_us"] is not None]
    result["slot_residual_us"] = {
        k: _mean_sd([r[f"{k}_latency_us"] - r["ppg_latency_us"] for r in ppg_rows])
        for k in PPG_SLOTS}
    result["slot_pairs_us"] = {
        f"{a}-{b}": _ci([r[f"{a}_latency_us"] - r[f"{b}_latency_us"] for r in ppg_rows])
        for a, b in ((PPG_SLOTS[0], PPG_SLOTS[1]), (PPG_SLOTS[1], PPG_SLOTS[2]),
                     (PPG_SLOTS[0], PPG_SLOTS[2]))}
    result["a9"] = {key: phase_coverage([r[f"{key}_phase"] for r in used
                                         if r[f"{key}_phase"] is not None])
                    for key in (ECG, *PPG_SLOTS)}
    result["latency_by_phase_bin_us"] = {key: _by_phase(used, key)
                                         for key in (ECG, *PPG_SLOTS)}
    result["a1"] = _a1(decode, session)
    result["a2"] = _a2(timebase)
    result["a3"] = _a3(timebase, timebase_model)
    result["a10"] = a10.check(packets)
    result["a8"] = {"status": "not_evaluable",
                    "reason": "FIFO-read anchors: no independent prediction of L_ECG "
                              "(plan 11.2)",
                    "l_ecg_fifo_us": result["latency"][ECG]["mean_us"]}
    result["a6"] = _a6(used, [e["t_us"] for e in stim])
    values = {key: ecg_values if key == ECG else series[key].value.astype(float)
              for key in (ECG, *PPG_SLOTS)}
    result["a11"] = _a11(events, rows, _anchor_residuals(packets, timebase),
                         _block_refit(packets, series, values, clip, timebase_model))
    result["events"] = rows
    result["verdict"] = _verdict(result)
    return result


def _by_minute(used):
    """Mean offset per 60 s from the first analysed event (report only): with
    FIFO anchors a slow read-delay drift and a clock drift give the same
    anchors, and only the stimulus offset shows the difference."""
    if not used:
        return []
    t0 = min(r["t_event_us"] for r in used)
    cells = {}
    for r in used:
        cells.setdefault(int((r["t_event_us"] - t0) // 60e6), []).append(r["offset_us"])
    return [None if m not in cells else float(np.mean(cells[m]))
            for m in range(max(cells) + 1)]


def _count(rows, key):
    out = {}
    for r in rows:
        out[r[f"{key}_status"]] = out.get(r[f"{key}_status"], 0) + 1
    return dict(sorted(out.items()))


def _mean_sd(values):
    values = [v for v in values if v is not None]
    if not values:
        return {"n": 0, "mean_us": None, "sd_us": None}
    return {"n": len(values), "mean_us": float(np.mean(values)),
            "sd_us": float(np.std(values, ddof=1)) if len(values) > 1 else None}


def _ci(values):
    if len(values) < 2:
        return {"n": len(values), "mean_us": None, "ci_us": None}
    return {"n": len(values), "mean_us": float(np.mean(values)),
            "ci_us": _bootstrap_mean(values)}


def _by_phase(used, key, bins=10):
    cells = [[] for _ in range(bins)]
    for r in used:
        if r[f"{key}_phase"] is not None:
            cells[min(int(r[f"{key}_phase"] * bins), bins - 1)].append(r[f"{key}_latency_us"])
    return [round(float(np.mean(c)), 1) if c else None for c in cells]


def _combine(values):
    """False if any is False, else None if any is None or there is none, else True."""
    values = list(values)
    if False in values:
        return False
    return None if (None in values or not values) else True


def _a2(timebase):
    out = {}
    for row in timebase:
        if row["channel"] not in (ECG, *PPG_SLOTS):
            continue
        name = f"{row['channel']}:chain{row['chain_id']}"
        if "fs_hz" not in row or row.get("nominal_rate"):
            # Under two anchors the rate is the nominal one filled in: no evidence.
            out[name] = {"fs_hz": row.get("fs_hz"), "passed": None}
            continue
        nominal = 512.0 if row["channel"] == ECG else 200.0
        dev = row["fs_hz"] / nominal - 1
        ok = (abs(dev) * 1e6 <= LIMITS["a2_ecg_ppm"] if row["channel"] == ECG
              else abs(dev) <= LIMITS["a2_ppg_fraction"])
        out[name] = {"fs_hz": row["fs_hz"], "ppm": dev * 1e6, "passed": ok}
    return {"chains": out, "passed": _combine(c["passed"] for c in out.values())}


def _a3(timebase, model="line"):
    rows = [r for r in timebase if r["channel"] in (ECG, *PPG_SLOTS)]
    values = {f"{r['channel']}:chain{r['chain_id']}": r.get("residual_block_max_us")
              for r in rows}
    passed = _combine(None if v is None else v <= LIMITS["a3_us"] for v in values.values())
    out = {"model": model, "block_max_us": values, "passed": passed, "note": None}
    if model == "segmented-60s":
        out["line_block_max_us"] = {f"{r['channel']}:chain{r['chain_id']}":
                                    r.get("line_residual_block_max_us") for r in rows}
        out["segment_problems"] = {f"{r['channel']}:chain{r['chain_id']}":
                                   r.get("segment_problem") for r in rows
                                   if r.get("segment_problem")}
    if passed is False and model == "line":
        out["note"] = ("A3 fails with one line: analyse every run of the validation "
                       "series again with timebase_model segmented-60s (plan section 9)")
    elif passed is not True:
        out["note"] = "A4-A6 and A11 not evaluable"
    return out


def _slope(t, y):
    """Offset slope (us per minute) with a 95 % event-bootstrap CI."""
    if len(t) < 3:
        return None, None
    x = (t - t.min()) / 60e6
    rng = np.random.default_rng(BOOT_SEED)
    draws = [np.polyfit(x[i], y[i], 1)[0]
             for i in rng.integers(0, len(x), (BOOT_B, len(x)))]
    lo, hi = np.percentile(draws, [2.5, 97.5])
    return float(np.polyfit(x, y, 1)[0]), (float(lo), float(hi))


def _a6(used, stim_times):
    """Six fixed 20-min blocks from the first analysed stimulus (plan 9, A6),
    judged only when the stimulus spans all of them; a shorter run reports the
    offset slope with its CI (no threshold)."""
    t = np.array([r["t_event_us"] for r in used], float)
    y = np.array([r["offset_us"] for r in used], float)
    slope, ci = _slope(t, y) if len(used) else (None, None)
    if not stim_times:
        return {"status": "not_evaluable"}
    start = min(stim_times)
    span_s = (max(stim_times) - start) / 1e6
    if span_s < A6_BLOCKS * A6_BLOCK_S - 2.0:
        return {"status": "short_run", "span_s": span_s, "slope_us_per_min": slope,
                "slope_ci": ci}
    block = np.floor((t - start) / (A6_BLOCK_S * 1e6)).astype(int)
    means = [float(y[block == b].mean()) if np.any(block == b) else None
             for b in range(A6_BLOCKS)]
    if any(m is None for m in means):
        return {"status": "not_evaluable", "reason": "a 20-min block has no event",
                "block_means_us": means}
    spread = max(means) - min(means)
    return {"status": "evaluated", "block_means_us": means, "range_us": spread,
            "passed": spread <= LIMITS["a6_range_us"], "slope_us_per_min": slope,
            "slope_ci": ci}


def _anchor_residuals(packets, timebase):
    """(anchor time, anchor - fitted time axis) of the reliable ECG and PPG
    slot-1 packets (the three slots share their anchors), for A11."""
    out = {}
    for key in (ECG, PPG_SLOTS[0]):
        points = []
        for p in packets:
            if (p["channel_id"] != key or p["disposition"] != "accepted"
                    or p["chain_id"] is None or p["status"] >> 8 & 1):
                continue
            fit = _fit_at(timebase, key, p["chain_id"])
            if fit is None:
                continue
            k = p["sample_index_ext"] + p["sample_count"] - 1
            points.append((p["t_anchor_us"], p["t_anchor_us"] - float(si.timebase_at(fit, k))))
        out[key] = np.array(points, float).reshape(-1, 2)
    return out


def _block_refit(packets, series, values, clip, model):
    """Callable (lo, hi, rows) -> one dict per row with ``offset_us`` (None when an
    edge fails) and the ``phase`` of each channel, both on a time axis fitted, with
    ``model``, to the anchors of [lo, hi) only; None when a chain of the block has
    no valid fit. A11 judges each block as a session of its own (plan 11.7)."""
    by_chain = {}
    for p in packets:
        if (p["channel_id"] in (ECG, *PPG_SLOTS) and p["chain_id"] is not None
                and p["disposition"] == "accepted"):
            by_chain.setdefault((p["channel_id"], p["chain_id"]), []).append(p)

    def refit(lo, hi, rows):
        axes, out = {}, []
        for r in rows:
            latency, phase = {}, {}
            for key in (ECG, *PPG_SLOTS):
                s = series[key]
                chain = int(s.chain[_nearest(s.t_us, r["t_event_us"])])
                if (key, chain) not in axes:
                    inside = [p for p in by_chain.get((key, chain), [])
                              if lo <= p["t_anchor_us"] < hi]
                    fit = si.fit_timebase(inside, s.fs_nominal_hz, model)
                    if fit is None or fit["nominal_rate"] or fit.get("segment_problem"):
                        return None
                    mask = s.chain == chain
                    order = np.argsort(s.index[mask], kind="stable")
                    index = s.index[mask][order]
                    t = si.timebase_at(fit, index) + (s.slot_offset_us or 0.0)
                    axes[(key, chain)] = (fit, t, values[key][mask][order],
                                          s.chain[mask][order], index)
                fit, t, x, ch, ix = axes[(key, chain)]
                resp = event_response(t, x, ch, ix, r["t_event_us"],
                                      "ecg" if key == ECG else "ppg", clip[key])
                latency[key] = resp.get("latency_us") if resp["status"] == "ok" else None
                phase[key] = _phase(r["t_event_us"], fit, s.slot_offset_us or 0.0)
            ok = None not in latency.values()
            out.append({"offset_us": latency[ECG] - float(np.mean(
                [latency[k] for k in PPG_SLOTS])) if ok else None, "phase": phase})
        return out

    return refit


def _a11(events, rows, residuals, refit):
    """A11 when the run has block boundaries (code 2 events); plan 11.7.

    The time axis of a run is fitted to the whole run, so a read delay that
    changes with the load only moves the anchors around it, not the sample
    times. A study session has its own fit, which follows the mean read delay of
    that session. Each block is therefore judged as a session of its own: the
    time axis is refitted (same model) to the anchors of the block, and the
    events of the block are measured again on it (the gate). The earlier
    approximation, event offsets on the run axis corrected by the block's mean
    ECG anchor residual minus its mean PPG anchor residual, is reported as
    ``residual_corrected``; it only shifts the intercept.
    """
    marks = [e["t_us"] for e in events if e["code"] == BOUNDARY_CODE]
    if not marks:
        return {"status": "not_an_a11_run"}
    if len(marks) != A11["boundaries"]:
        return {"status": "not_evaluable", "reason": f"{len(marks)} boundaries, not 13"}
    gaps = np.diff(marks) / 1e6
    if np.any(np.abs(gaps - A11["block_s"]) > A11["spacing_tolerance_s"]):
        return {"status": "not_evaluable", "reason": "boundary spacing off",
                "spacing_s": gaps.tolist()}
    phases = {"normal": [], "high": []}
    refitted = {"normal": [], "high": []}
    corrected = {"normal": [], "high": []}
    per_block = []
    for b in range(A11["boundaries"] - 1):
        lo, hi = marks[b] + A11["guard_s"] * 1e6, marks[b + 1]
        load = "normal" if b % 2 == 0 else "high"
        # Every stimulus of the block whose response window ends before the next
        # mark; the refit decides which edges pass (not the run-axis result).
        last = hi - EDGE["post_us"][1]
        inside = [r for r in rows if lo <= r["t_event_us"] < last]
        on_run = [r for r in inside if r["offset_us"] is not None]
        shift = []
        for key in (ECG, PPG_SLOTS[0]):
            pts = residuals[key]
            sel = pts[(pts[:, 0] >= lo) & (pts[:, 0] < hi), 1] if len(pts) else pts
            shift.append(float(sel.mean()) if len(sel) else None)
        if on_run and None not in shift:
            corrected[load] += [r["offset_us"] + shift[0] - shift[1] for r in on_run]
        fresh = [f for f in (refit(lo, hi, inside) or []) if f["offset_us"] is not None]
        values = [f["offset_us"] for f in fresh]
        phases[load] += [f["phase"] for f in fresh]
        refitted[load] += values
        per_block.append({"block": b, "load": load, "n": len(inside), "n_refit": len(values),
                          "anchor_shift_ecg_us": shift[0], "anchor_shift_ppg_us": shift[1],
                          "offset_us": float(np.mean(values)) if values else None})
    # A9 per load on the events that give the A11 offsets, with block-fit phases.
    a9 = {load: {key: phase_coverage([f[key] for f in g]) for key in (ECG, *PPG_SLOTS)}
          for load, g in phases.items()}
    if any(c["passed"] is not True for load in a9.values() for c in load.values()):
        return {"status": "not_evaluable", "reason": "A9 failed for a load type",
                "a9": a9, "blocks": per_block}
    if any(b["offset_us"] is None for b in per_block):
        return {"status": "not_evaluable", "reason": "a block has no refitted offset",
                "blocks": per_block}
    means = {load: float(np.mean(v)) for load, v in refitted.items()}
    diff = means["high"] - means["normal"]
    pairs = [per_block[i + 1]["offset_us"] - per_block[i]["offset_us"]
             for i in range(0, len(per_block) - 1, 2)]
    side = {load: float(np.mean(v)) if v else None for load, v in corrected.items()}
    side_diff = (None if None in side.values() else side["high"] - side["normal"])
    return {"status": "evaluated", "offset_us": means, "diff_us": diff,
            "passed": abs(diff) <= LIMITS["a11_diff_us"], "pair_diffs_us": pairs,
            "residual_corrected": {"offset_us": side, "diff_us": side_diff},
            "blocks": per_block, "a9": a9}


def _verdict(result):
    """Plan 11.2: A1-A6, A9-A11 pass together; A8 not evaluable. Criteria that
    this single run cannot decide (A5; A6 on a short run; A11 off an A11 run)
    are listed, not counted."""
    a9_values = [c["passed"] for c in result["a9"].values()]
    a9_ok = (False if False in a9_values else None if None in a9_values else True)
    gates = {"a1": result["a1"]["passed"], "a2": result["a2"]["passed"],
             "a3": result["a3"]["passed"], "a9": a9_ok,
             "a10": result["a10"]["passed"]}
    half = result["offset"].get("a4_half_ci_us")
    gates["a4"] = (None if half is None or a9_ok is not True
                   or result["a3"]["passed"] is not True
                   else half <= LIMITS["a4_half_ci_us"])
    base_ok = a9_ok is True and result["a3"]["passed"] is True
    if result["a6"]["status"] in ("evaluated", "not_evaluable"):
        gates["a6"] = result["a6"].get("passed") if base_ok else None
    if result["a11"]["status"] in ("evaluated", "not_evaluable"):
        gates["a11"] = result["a11"].get("passed") if base_ok else None
    failed = [k for k, v in gates.items() if v is False]
    open_ = [k for k, v in gates.items() if v is None]
    return {"gates": gates, "failed": failed, "not_evaluable": open_,
            "run_passed": not failed and not open_, "a8": "not_evaluable",
            "needs_other_runs": ["a5"] + ([] if "a6" in gates else ["a6"])}


def a5(runs, dates, identities=None):
    """A5 over run results (``analyze_run`` outputs) with the UTC date
    (YYYY-MM-DD) of each run and an identity per run (raw SHA-256 and device
    session): 10 distinct runs, 5 on each of two dates, each run passing A1, A4
    and A9; range of the offsets <= 0.3 ms."""
    if len(runs) != 10 or len(dates) != 10:
        return {"status": "not_evaluable", "reason": "A5 needs 10 runs"}
    if not all(re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", d or "") for d in dates):
        return {"status": "not_evaluable", "reason": "a run has no UTC start date"}
    if identities is not None and len(set(identities)) != 10:
        return {"status": "not_evaluable", "reason": "the 10 runs are not distinct"}
    # v1 reports predate the model choice and always used the line.
    models = {r.get("timebase_model") or ("line" if r.get("method") == "sync-analysis-v1"
                                          else None) for r in runs}
    if len(models) != 1 or not models <= set(si.TIMEBASE_MODELS):
        return {"status": "not_evaluable",
                "reason": "the runs do not share one time-axis model (plan section 9)",
                "models": sorted(str(m) for m in models)}
    per_day = {}
    for d in dates:
        per_day[d] = per_day.get(d, 0) + 1
    if sorted(per_day.values()) != [5, 5]:
        return {"status": "not_evaluable", "reason": "need 5 runs on each of two dates",
                "per_day": per_day}
    bad = [i for i, r in enumerate(runs)
           if any(r["verdict"]["gates"].get(g) is not True for g in ("a1", "a4", "a9"))]
    if bad:
        return {"status": "not_evaluable", "reason": "A1, A4 or A9 not passed in runs",
                "runs": bad}
    offsets = [r["offset"]["mean_us"] for r in runs]
    spread = max(offsets) - min(offsets)
    return {"status": "evaluated", "timebase_model": models.pop(),
            "offsets_us": offsets, "range_us": spread,
            "passed": spread <= LIMITS["a5_range_us"]}


def round_floats(value, digits=3):
    """JSON-friendly copy with floats rounded (NaN becomes None)."""
    if isinstance(value, float):
        return None if math.isnan(value) else round(value, digits)
    if isinstance(value, dict):
        return {k: round_floats(v, digits) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [round_floats(v, digits) for v in value]
    return value
