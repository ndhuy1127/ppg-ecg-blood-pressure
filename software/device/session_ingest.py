"""Ingest of one ``packet-logger-v3`` recording (``device-session-v1``).

Reads the logger output directory, checks it against its own manifest, and
builds per-channel sample times on the MCU clock. Raw data are never changed:
``raw.bin`` and the logger outputs are only read and hashed. The output format is
defined in docs/data_convention.md section 4 (proposal 2026-11-13, pending
review).

Sample time (Packet Schema V0.1 section 5.3), per (device session, version,
channel, chain): a least-squares line ``T_ANCHOR_US = a + b k`` over the packets
whose anchor the logger accepted (``disposition == "accepted"``), with k the
index of the last sample of the packet; then ``t_us(k) = a + b k - L`` with L the
effective latency of the channel from the session metadata. PPG slot j adds
(j - 1) x the LED spacing of ``LED_PW`` in the MAX30101 ``0xD2`` state (schema
section 7). ECG and PPG keep their own sample times on the same MCU clock; nothing
is resampled or shifted to align the channels.
"""

import csv
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from software.data_io.live_monitor import slot_colors
from software.device.max30101 import SLOT_SPACING_US

VERSION = "device-session-v1"
LOGGER_VERSION = "packet-logger-v3"
TIME_UNIT = "us"
DATA_CHANNELS = ("0xE1", "0xF1", "0xF2", "0xF3", "0xF4")
PPG_KEYS = ("0xF1", "0xF2", "0xF3", "0xF4")
EVENT_NAMES = {1: "cuff_t0", 2: "cuff_end", 3: "sync_pulse", 4: "operator_mark"}
STATUS_FLAGS = {0: "afe_fifo_overflow", 1: "mcu_buffer_overflow", 2: "ecg_lead_off",
                3: "afe_error", 6: "ppg_alc_overflow"}
CUFF_COLUMNS = ("recording", "event_id", "phase", "device_session_id",
                "t0_event_ordinal", "phase_mark_event_ordinal",
                "cuff_end_event_ordinal", "sbp_mmhg", "dbp_mmhg", "pulse_rate_bpm",
                "status", "safety_stop", "led_readjusted", "pilot", "note")
# cuff-log-v2 (docs/data_convention.md 4.4, decided 2026-11-27; SAP section 2): the v1
# columns plus the link of a repeat to the attempt it repeats. Repeats only at M0,
# at most 2 per log, for no_result or a motion the operator saw and logged before t0.
CUFF_COLUMNS_V2 = CUFF_COLUMNS + ("repeat_of_event_id", "repeat_reason")
CUFF_LOG_VERSIONS = {CUFF_COLUMNS: "cuff-log-v1", CUFF_COLUMNS_V2: "cuff-log-v2"}
REPEAT_REASONS = ("no_result", "observed_motion")
MAX_REPEATS = 2
SLOTS_PER_PHASE = {"M0": 2, "M1": 1, "M2": 1}
# Session- and subject-level 0/1 columns of the cuff log: one cuff log is one study
# session of one subject, so they must be the same on every row (data_convention 4.4).
LOG_CONSTANT_COLUMNS = ("led_readjusted", "pilot")
CUFF_STATUS = ("valid", "no_result", "device_error")
# Acceptance criterion A3 (hardware/test_reports/sync_10min_test_plan.md section 9):
# the median anchor residual of every 10 s block stays within +/- 0.2 ms. Checked on
# every recording and only flagged; sample times are not changed (added 2026-11-15).
A3_BLOCK_US = 10_000_000
A3_LIMIT_US = 200.0
# Time-axis models (sync_10min_test_plan.md section 9, "Mô hình theo đoạn", decided
# 2026-11-21): one line per chain, or a continuous piecewise-linear function of the
# sample index with knots every 60 s of nominal samples from the first anchor.
TIMEBASE_MODELS = ("line", "segmented-60s")
SEGMENT_S = 60.0
PHASES = ("M0", "M1", "M2")
REQUIRED_FILES = ("raw.bin", "decode.json", "packets.csv", "samples.csv",
                  "session_metadata.json", "logger_config.json")


class IngestError(ValueError):
    """The recording is incomplete, altered or inconsistent; nothing is repaired."""


@dataclass(frozen=True)
class ChannelSeries:
    """Samples of one channel in one device session, ordered by time."""

    key: str
    name: str
    chain: np.ndarray
    index: np.ndarray
    value: np.ndarray
    t_us: np.ndarray  # MCU clock, latency removed when known; NaN without timebase
    fs_nominal_hz: float
    latency_applied: bool
    slot_offset_us: float | None


def sha256_file(path, chunk=1 << 20):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        while block := handle.read(chunk):
            digest.update(block)
    return digest.hexdigest()


def _load_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise IngestError(f"Cannot read {Path(path).name}: {exc}") from exc


def verify_recording(directory):
    """Check a recording against its manifest; returns the manifest.

    Refuses a recording without ``session_manifest.json`` (interrupted), another
    logger version, a missing file, and any file whose SHA-256 differs from the
    manifest (raw, outputs and the input copies)."""
    directory = Path(directory)
    manifest_path = directory / "session_manifest.json"
    if not manifest_path.is_file():
        raise IngestError("No session_manifest.json: the recording is incomplete; "
                          "replay raw.bin first (docs/protocol/packet_logger.md)")
    manifest = _load_json(manifest_path)
    if manifest.get("logger_version") != LOGGER_VERSION:
        raise IngestError(f"Logger version {manifest.get('logger_version')!r} is not "
                          f"{LOGGER_VERSION}")
    hashes = manifest.get("outputs_sha256")
    if not isinstance(hashes, dict):
        raise IngestError("Manifest has no outputs_sha256")
    for name in REQUIRED_FILES:
        if name not in hashes:
            raise IngestError(f"Manifest does not hash {name}")
    for name, expected in sorted(hashes.items()):
        path = directory / name
        if not path.is_file():
            raise IngestError(f"Missing file {name}")
        if sha256_file(path) != expected:
            raise IngestError(f"SHA-256 of {name} differs from the manifest")
    if manifest["raw"]["sha256"] != hashes["raw.bin"] or (
            directory / "raw.bin").stat().st_size != manifest["raw"]["bytes"]:
        raise IngestError("raw.bin does not match the manifest raw entry")
    if manifest["inputs_sha256"]["session_metadata"] != hashes["session_metadata.json"]:
        raise IngestError("Session metadata copy differs from the hashed input")
    return manifest


def _read_packets(path):
    rows = []
    with open(path, newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            for name in ("session_id", "version", "seq_ext", "t_anchor_us",
                         "fs_nominal_mhz", "sample_count", "status"):
                row[name] = int(row[name])
            for name in ("sample_index_ext", "chain_id"):
                row[name] = int(row[name]) if row[name] != "" else None
            rows.append(row)
    return rows


def _read_samples(path):
    """{(session, version, channel): (chain, index, value)} as int64 arrays."""
    columns = {}
    with open(path, newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        header = next(reader)
        if header != ["session_id", "channel_id", "chain_id", "seq_ext",
                      "sample_index_ext", "value", "version"]:
            raise IngestError("Unexpected samples.csv columns")
        for session, channel, chain, _, index, value, version in reader:
            key = (int(session), int(version), channel)
            columns.setdefault(key, ([], [], []))
            parts = columns[key]
            parts[0].append(int(chain))
            parts[1].append(int(index))
            parts[2].append(int(value))
    return {key: tuple(np.asarray(part, dtype=np.int64) for part in parts)
            for key, parts in columns.items()}


def load_recording(directory):
    """Verified recording: manifest, metadata, decode, packets and samples.

    Also checks the outputs against each other: one decoded packet per
    ``packets.csv`` row, and per channel the accepted samples of ``decode.json``
    equal the rows of ``samples.csv``."""
    directory = Path(directory)
    manifest = verify_recording(directory)
    metadata = _load_json(directory / "session_metadata.json")
    decode = _load_json(directory / "decode.json")
    packets = _read_packets(directory / "packets.csv")
    samples = _read_samples(directory / "samples.csv")
    if decode["decode"]["packets_decoded"] != len(packets):
        raise IngestError("packets.csv rows differ from packets_decoded")
    for session in decode["sessions"]:
        version = int(session["packet_schema"].rsplit("v0.", 1)[1])
        for key, summary in session["channels"].items():
            if "samples_accepted" not in summary:
                continue
            got = samples.get((session["session_id"], version, key))
            if (0 if got is None else len(got[0])) != summary["samples_accepted"]:
                raise IngestError(f"samples.csv rows of {key} differ from decode.json")
    return {"directory": directory, "manifest": manifest, "metadata": metadata,
            "decode": decode, "packets": packets, "samples": samples}


def _a3_block_max(anchor, residuals):
    """Largest |median residual| over 10 s blocks of anchor time (A3); the last
    block joins the one before when it spans under half a block."""
    start = anchor.min()
    block = np.floor((anchor - start) / A3_BLOCK_US)
    last = block.max()
    if last > 0 and anchor.max() - (start + last * A3_BLOCK_US) < A3_BLOCK_US / 2:
        block[block == last] = last - 1
    return float(max(abs(np.median(residuals[block == j])) for j in np.unique(block)))


def fit_timebase(packets, fs_nominal_hz, model="line"):
    """Time axis ``T_ANCHOR_US = f(k)`` over anchor-checked packets of one chain.

    ECG packets with STATUS bit 8 (SAMP edges) and FIFO-read anchors have an
    unknown offset between them, so only one source is used: SAMP when present.
    Returns a dict with a, b (us per sample) of one line, fs_hz, n_anchors,
    residual_sd_us, residual_block_max_us (largest |median residual| over 10 s
    blocks of anchor time, the statistic of A3; a last block spanning under half a
    block joins the one before, so a few trailing anchors do not carry their own
    jitter; None with fewer than three anchors), anchor_source and model; with
    fewer than two anchors b is the nominal period and the fit is flagged; with
    none, None.

    ``model`` "segmented-60s" (plan section 9) adds knots_k and knot_t_us of a
    continuous piecewise-linear fit and puts its residuals in residual_sd_us and
    residual_block_max_us; a, b stay those of the line (the overall rate, A2) and
    the line's A3 statistic is kept as line_residual_block_max_us. When the
    segmented fit breaks a rule (segment_problem), knots and residuals are None
    and the time axis falls back to the line, flagged."""
    if model not in TIMEBASE_MODELS:
        raise ValueError(f"Unknown time-axis model {model!r}")
    reliable = [p for p in packets if p["disposition"] == "accepted"]
    samp = [p for p in reliable if p["channel_id"] == "0xE1" and p["status"] >> 8 & 1]
    source = "samp" if samp else "fifo_read"
    use = samp or [p for p in reliable if not (p["status"] >> 8 & 1)]
    if not use:
        return None
    k = np.array([p["sample_index_ext"] + p["sample_count"] - 1 for p in use], float)
    anchor = np.array([p["t_anchor_us"] for p in use], float)
    if len(use) == 1 or np.ptp(k) == 0:
        b = 1e6 / fs_nominal_hz
        a = float(anchor[0] - b * k[0])
        residual, block_max, nominal = None, None, True
    else:
        b, a = np.polyfit(k - k[0], anchor, 1)
        a = float(a - b * k[0])
        residuals = anchor - (a + b * k)
        residual = float(np.std(residuals, ddof=2)) if len(use) > 2 else None
        block_max = _a3_block_max(anchor, residuals) if len(use) > 2 else None
        nominal = False
    fit = {"a_us": float(a), "b_us": float(b), "fs_hz": 1e6 / float(b),
           "n_anchors": len(use), "residual_sd_us": residual,
           "residual_block_max_us": block_max,
           "anchor_source": source, "nominal_rate": nominal, "model": model}
    if model == "segmented-60s":
        fit["line_residual_block_max_us"] = block_max
        fit.update(_fit_segmented(k, anchor, fs_nominal_hz, a, b, nominal))
    return fit


def segment_knots(k_first, k_last, fs_nominal_hz):
    """Knots of the segmented model: k_first, then every round(60 s x fs_nominal)
    samples while below k_last, then k_last; a last segment under half a
    segment joins the one before (its knot is dropped)."""
    step = int(round(SEGMENT_S * fs_nominal_hz))
    knots = [float(k_first)]
    while knots[-1] + step < k_last:
        knots.append(knots[-1] + step)
    knots.append(float(k_last))
    if len(knots) > 2 and knots[-1] - knots[-2] < step / 2:
        del knots[-2]
    return np.array(knots)


def _fit_segmented(k, anchor, fs_nominal_hz, a, b, nominal):
    """Least squares of a continuous piecewise-linear function of k (hat basis on
    the knots), fitted to the residuals of the line for numerical range. Rules:
    every segment holds at least 3 anchors spanning at least half of it, and
    every segment slope is positive; otherwise segment_problem is set."""
    empty = {"knots_k": None, "knot_t_us": None, "residual_sd_us": None,
             "residual_block_max_us": None}
    if nominal or len(k) < 3:
        return {**empty, "segment_problem": "too_few_anchors"}
    knots = segment_knots(k.min(), k.max(), fs_nominal_hz)
    j = np.clip(np.searchsorted(knots, k, side="right") - 1, 0, len(knots) - 2)
    for s in range(len(knots) - 1):
        inside = k[j == s]
        if len(inside) < 3 or np.ptp(inside) < (knots[s + 1] - knots[s]) / 2:
            return {**empty, "segment_problem": f"segment {s} sparse"}
    w = (k - knots[j]) / (knots[j + 1] - knots[j])
    y = anchor - (a + b * k)
    n = len(knots)
    gram, rhs = np.zeros((n, n)), np.zeros(n)
    for col_a, wa in ((j, 1 - w), (j + 1, w)):
        np.add.at(rhs, col_a, wa * y)
        for col_b, wb in ((j, 1 - w), (j + 1, w)):
            np.add.at(gram, (col_a, col_b), wa * wb)
    coef = np.linalg.solve(gram, rhs)
    knot_t = a + b * knots + coef
    if np.any(np.diff(knot_t) <= 0):
        return {**empty, "segment_problem": "non_positive_slope"}
    residuals = y - (coef[j] * (1 - w) + coef[j + 1] * w)
    return {"knots_k": knots.tolist(), "knot_t_us": knot_t.tolist(),
            "residual_sd_us": float(np.std(residuals, ddof=n)) if len(k) > n else None,
            "residual_block_max_us": _a3_block_max(anchor, residuals),
            "segment_problem": None}


def timebase_at(fit, k):
    """Anchor time (us) of sample index ``k`` on a fit of ``fit_timebase``: the
    segmented function when it has knots (end segments extended), else the line."""
    k = np.asarray(k, float)
    if not fit.get("knots_k"):
        return fit["a_us"] + fit["b_us"] * k
    knots, values = np.asarray(fit["knots_k"]), np.asarray(fit["knot_t_us"])
    j = np.clip(np.searchsorted(knots, k, side="right") - 1, 0, len(knots) - 2)
    slope = (values[j + 1] - values[j]) / (knots[j + 1] - knots[j])
    return values[j] + slope * (k - knots[j])


def timebase_index_at(fit, t_us):
    """Inverse of ``timebase_at``: the (fractional) sample index at time ``t_us``."""
    t_us = np.asarray(t_us, float)
    if not fit.get("knots_k"):
        return (t_us - fit["a_us"]) / fit["b_us"]
    knots, values = np.asarray(fit["knots_k"]), np.asarray(fit["knot_t_us"])
    j = np.clip(np.searchsorted(values, t_us, side="right") - 1, 0, len(knots) - 2)
    slope = (knots[j + 1] - knots[j]) / (values[j + 1] - values[j])
    return knots[j] + slope * (t_us - values[j])


def _led_state(session):
    """(LED_PW code, slot colours) of the configured MAX30101 states, or (None, {})
    when there is no state or the states disagree."""
    states = [s for s in ((session.get("afe_config") or {}).get("MAX30101") or [])
              if s["source"] == "chip" and s["configured"]]
    if not states:
        return None, {}, "no_max30101_state"
    widths = {int(s["registers"]["0x0A"], 16) & 3 for s in states}
    colors = {tuple(sorted(slot_colors(s["registers"]).items())) for s in states}
    if len(widths) != 1 or len(colors) != 1:
        return None, {}, "max30101_state_changed"
    channels = {f"0x{c:02X}": name for c, name in colors.pop()}
    return widths.pop(), channels, None


def session_series(recording, session_index=0, timebase_model="line"):
    """Per data channel ``ChannelSeries`` of one decoded session (by position in
    ``decode.json``), plus the timebase table and flags. ``timebase_model`` is one
    of ``TIMEBASE_MODELS`` (plan section 9); "line" unless a sync validation
    series qualified the segmented model."""
    decode, metadata = recording["decode"], recording["metadata"]
    session = decode["sessions"][session_index]
    sid = session["session_id"]
    version = int(session["packet_schema"].rsplit("v0.", 1)[1])
    width, colors, led_problem = _led_state(session)
    flags = [led_problem] if led_problem else []
    by_chain = {}
    for p in recording["packets"]:
        if (p["session_id"], p["version"]) == (sid, version) and p["chain_id"] is not None:
            by_chain.setdefault((p["channel_id"], p["chain_id"]), []).append(p)
    series, timebase = {}, []
    for key in DATA_CHANNELS:
        if (sid, version, key) not in recording["samples"]:
            continue
        chain, index, value = recording["samples"][(sid, version, key)]
        spec = metadata["channels"].get(key) or {}
        fs_nominal = spec.get("fs_nominal_mhz") / 1000 if spec.get(
            "fs_nominal_mhz") else None
        if fs_nominal is None:
            raise IngestError(f"No nominal rate for {key} in the session metadata")
        t_us = np.full(len(index), np.nan)
        known = True
        for chain_id in np.unique(chain):
            fit = fit_timebase(by_chain.get((key, int(chain_id)), []), fs_nominal,
                               timebase_model)
            row = {"device_session_id": sid, "channel": key, "chain_id": int(chain_id),
                   **(fit or {"n_anchors": 0})}
            # SAMP anchors have their own latency (Packet Schema V0.2 section 8).
            samp = fit is not None and fit["anchor_source"] == "samp"
            latency = spec.get("latency_samp_l_us" if samp else "latency_l_us")
            known = known and latency is not None
            row["latency_l_us"] = latency
            timebase.append(row)
            if fit is None:
                flags.append(f"{key}:chain{int(chain_id)}:no_reliable_anchor")
                continue
            if fit["nominal_rate"]:
                flags.append(f"{key}:chain{int(chain_id)}:single_anchor_nominal_rate")
            if fit.get("segment_problem"):
                flags.append(f"{key}:chain{int(chain_id)}:segmented_fit_invalid")
            elif (fit["residual_block_max_us"] is not None
                  and fit["residual_block_max_us"] > A3_LIMIT_US):
                flags.append(f"{key}:chain{int(chain_id)}:timebase_residual_above_a3")
            mask = chain == chain_id
            t_us[mask] = timebase_at(fit, index[mask]) - (latency or 0)
        offset = None
        if key in PPG_KEYS:
            slot = PPG_KEYS.index(key)
            if width is not None:
                offset = slot * SLOT_SPACING_US[width]
                t_us = t_us + offset
            else:
                flags.append(f"{key}:slot_offset_unknown")
        if not known:
            flags.append(f"{key}:latency_unknown")
        order = np.argsort(t_us, kind="stable")
        name = colors.get(key, "ecg" if key == "0xE1" else key)
        series[key] = ChannelSeries(key, name, chain[order], index[order], value[order],
                                    t_us[order], fs_nominal, known, offset)
    return series, timebase, sorted(set(flags))


def session_events(recording, session_index=0):
    """Events of one session: ordinal, code, name and MCU time (us)."""
    session = recording["decode"]["sessions"][session_index]
    return [{"device_session_id": session["session_id"],
             "event_ordinal": e["event_ordinal"], "code": e["data"][0],
             "name": EVENT_NAMES.get(e["data"][0], "unknown"),
             "t_us": e["t_anchor_us"]} for e in session["events"]]


def _number(text, name, row):
    try:
        value = float(text)
    except ValueError as exc:
        raise IngestError(f"cuff_log row {row}: {name} is not a number") from exc
    if not np.isfinite(value):
        raise IngestError(f"cuff_log row {row}: {name} is not finite")
    return value


def cuff_log_version(path):
    """``cuff-log-v1`` or ``cuff-log-v2`` from the header; any other header is an
    error."""
    with open(path, newline="", encoding="utf-8") as handle:
        header = tuple(next(csv.reader(handle), ()))
    if header not in CUFF_LOG_VERSIONS:
        raise IngestError(f"cuff_log columns must be {CUFF_COLUMNS} (v1) or "
                          f"{CUFF_COLUMNS_V2} (v2)")
    return CUFF_LOG_VERSIONS[header]


def _check_repeats(rows):
    """cuff-log-v2 repeat links over the whole log, every recording (SAP section 2,
    decided 2026-11-27). Rows are in the order of the attempts. A repeat names the
    attempt just before it at the same slot: an earlier M0 row of the log that no
    other repeat names. The motion itself (logged before t0) is in the session
    journal of the session app, which this function does not see."""
    position, children, repeats = {}, {}, 0
    originals = dict.fromkeys(PHASES, 0)
    for n, row in enumerate(rows, start=2):
        parent, reason = row["repeat_of_event_id"], row["repeat_reason"]
        if not parent:
            # The schedule has M0 x2, M1, M2 (protocol 6.4): an unlinked repeat
            # would otherwise become a slot of its own.
            originals[row["phase"]] += 1
            if originals[row["phase"]] > SLOTS_PER_PHASE[row["phase"]]:
                raise IngestError(f"cuff_log row {n}: more than "
                                  f"{SLOTS_PER_PHASE[row['phase']]} scheduled "
                                  f"{row['phase']} attempts; a repeat needs "
                                  "repeat_of_event_id")
        if (parent == "") != (reason == ""):
            raise IngestError(f"cuff_log row {n}: repeat_of_event_id and repeat_reason "
                              "are both empty or both set")
        if parent:
            repeats += 1
            if reason not in REPEAT_REASONS:
                raise IngestError(f"cuff_log row {n}: repeat_reason {REPEAT_REASONS}")
            if row["phase"] != "M0":
                raise IngestError(f"cuff_log row {n}: repeats only at M0 (SAP section 2)")
            if parent not in position:
                raise IngestError(f"cuff_log row {n}: repeat_of_event_id {parent!r} is "
                                  "not an earlier row of this log")
            first = rows[position[parent]]
            if first["phase"] != "M0" or first["status"] == "device_error":
                raise IngestError(f"cuff_log row {n}: {parent} is not an M0 attempt that "
                                  "may be repeated")
            if reason == "no_result" and first["status"] != "no_result":
                raise IngestError(f"cuff_log row {n}: reason no_result but {parent} "
                                  f"has status {first['status']}")
            if parent in children:
                raise IngestError(f"cuff_log row {n}: {parent} is already repeated by "
                                  f"{children[parent]}")
            # Same recording and MCU session: the event ordinals give the real order.
            same = all(first[k] == row[k] for k in ("recording", "device_session_id"))
            if (same and first["t0_event_ordinal"].isdigit()
                    and row["t0_event_ordinal"].isdigit()
                    and int(row["t0_event_ordinal"]) <= int(first["t0_event_ordinal"])):
                raise IngestError(f"cuff_log row {n}: its t0 is not after the t0 of "
                                  f"{parent}")
            children[parent] = row["event_id"]
        position[row["event_id"]] = n - 2
    if repeats > MAX_REPEATS:
        raise IngestError(f"cuff_log: {repeats} repeats, at most {MAX_REPEATS} per "
                          "session (protocol 6.4)")


def read_cuff_log(path, recording_name):
    """Rows of ``cuff_log.csv`` (docs/data_convention.md section 4.4) for one
    recording, v1 or v2 (``cuff_log_version``). Strict: unknown columns, duplicate
    ``event_id``, unknown phase or status, labels on rows that are not ``valid``,
    and on v2 a broken repeat link are errors. v1 rows carry no repeat link
    (``repeat_of_event_id`` and ``repeat_reason`` None)."""
    v2 = cuff_log_version(path) == "cuff-log-v2"
    with open(path, newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    for n, row in enumerate(rows, start=2):
        # DictReader fills a short row with None and keeps extra fields under None.
        if None in row or any(value is None for value in row.values()):
            raise IngestError(f"cuff_log row {n}: wrong number of fields")
    for name in LOG_CONSTANT_COLUMNS:
        if len({row[name] for row in rows}) > 1:
            raise IngestError(f"cuff_log: {name} must be the same on every row")
    seen, out = set(), []
    for n, row in enumerate(rows, start=2):
        if not re.fullmatch(r"E\d{2}", row["event_id"]):
            raise IngestError(f"cuff_log row {n}: event_id must look like E01")
        if row["event_id"] in seen:
            raise IngestError(f"cuff_log row {n}: duplicate event_id")
        seen.add(row["event_id"])
        if row["phase"] not in PHASES or row["status"] not in CUFF_STATUS:
            raise IngestError(f"cuff_log row {n}: phase {PHASES}, status {CUFF_STATUS}")
        for name in ("safety_stop", *LOG_CONSTANT_COLUMNS):
            if row[name] not in ("0", "1"):
                raise IngestError(f"cuff_log row {n}: {name} must be 0 or 1")
    if v2:
        _check_repeats(rows)
    for n, row in enumerate(rows, start=2):
        if row["recording"] != recording_name:
            continue
        cuff = {"event_id": row["event_id"], "phase": row["phase"],
                "status": row["status"], "safety_stop": row["safety_stop"] == "1",
                "led_readjusted": row["led_readjusted"] == "1",
                "pilot": row["pilot"] == "1", "note": row["note"],
                "repeat_of_event_id": (row["repeat_of_event_id"] or None) if v2 else None,
                "repeat_reason": (row["repeat_reason"] or None) if v2 else None}
        for name in ("device_session_id", "t0_event_ordinal",
                     "phase_mark_event_ordinal", "cuff_end_event_ordinal"):
            text = row[name]
            if text == "":
                cuff[name] = None
            elif not text.isdigit():
                raise IngestError(f"cuff_log row {n}: {name} must be an integer")
            else:
                cuff[name] = int(text)
        labels = [row[k] for k in ("sbp_mmhg", "dbp_mmhg")]
        if row["status"] == "valid":
            sbp, dbp = (_number(v, k, n) for v, k in zip(labels, ("sbp", "dbp")))
            if not dbp < sbp:
                raise IngestError(f"cuff_log row {n}: DBP must be below SBP")
            cuff.update(sbp_mmhg=sbp, dbp_mmhg=dbp)
        elif any(labels):
            raise IngestError(f"cuff_log row {n}: only valid rows carry SBP/DBP")
        else:
            cuff.update(sbp_mmhg=None, dbp_mmhg=None)
        rate = row["pulse_rate_bpm"]
        cuff["pulse_rate_bpm"] = _number(rate, "pulse_rate_bpm", n) if rate else None
        if cuff["t0_event_ordinal"] is None or cuff["device_session_id"] is None:
            raise IngestError(f"cuff_log row {n}: t0_event_ordinal and "
                              "device_session_id are required")
        out.append(cuff)
    return out


def _event(events, session_id, ordinal, code, what):
    if ordinal is None:
        return None
    hits = [e for e in events if e["device_session_id"] == session_id
            and e["event_ordinal"] == ordinal]
    if len(hits) != 1:
        raise IngestError(f"{what}: no event with ordinal {ordinal}")
    if hits[0]["code"] != code:
        raise IngestError(f"{what}: event {ordinal} has code {hits[0]['code']}, "
                          f"not {code}")
    return hits[0]["t_us"]


def cuff_windows(cuffs, events, window_config):
    """Signal window of every cuff (protocol 6.2): ``[t0 - stored_pre_s, t0)``.

    Also the analysis windows ``[t0 - L, t0)`` for each L of the config, the
    inflation span ``[t0, cuff_end]`` (``cuff_inflating``), and for M1/M2 the
    delay from the phase mark (event code 4) to t0, flagged when the stored window
    starts before the mark (protocol 6.4: the window must lie inside the
    maneuver)."""
    stored = float(window_config["stored_pre_s"])
    out = []
    for cuff in cuffs:
        sid, what = cuff["device_session_id"], f"cuff {cuff['event_id']}"
        t0 = _event(events, sid, cuff["t0_event_ordinal"], 1, what)
        end = _event(events, sid, cuff["cuff_end_event_ordinal"], 2, what)
        mark = _event(events, sid, cuff["phase_mark_event_ordinal"], 4, what)
        flags = []
        if end is None:
            flags.append("cuff_end_missing")
        elif end <= t0:
            raise IngestError(f"{what}: cuff_end is not after t0")
        mark_to_t0 = None
        if cuff["phase"] in ("M1", "M2"):
            if mark is None:
                flags.append("phase_mark_missing")
            else:
                mark_to_t0 = (t0 - mark) / 1e6
                if mark_to_t0 < stored:
                    flags.append("window_starts_before_phase_mark")
        windows = {f"pre_{int(s)}s": [t0 - s * 1e6, t0]
                   for s in window_config["analysis_pre_s"]}
        out.append({**cuff, "t0_us": t0, "cuff_end_us": end,
                    "stored_window_us": [t0 - stored * 1e6, t0],
                    "analysis_windows_us": windows,
                    "cuff_inflating_us": None if end is None else [t0, end],
                    "inflation_s": None if end is None else (end - t0) / 1e6,
                    "phase_mark_to_t0_s": mark_to_t0, "flags": flags})
    return out


def window_samples(series, start_us, end_us):
    """Index range of ``series`` with start <= t < end (NaN times excluded)."""
    t = series.t_us
    keep = np.isfinite(t) & (t >= start_us) & (t < end_us)
    return np.flatnonzero(keep)


def summarize(recording, series, timebase, flags, events, cuffs, session_index=0):
    """Session summary (task F4): duration, rate, loss, cuffs, markers, flags."""
    decode, manifest = recording["decode"], recording["manifest"]
    session = decode["sessions"][session_index]
    channels = {}
    starts, ends = [], []
    for key, s in series.items():
        summary = session["channels"][key]
        finite = s.t_us[np.isfinite(s.t_us)]
        if len(finite):
            starts.append(finite[0])
            ends.append(finite[-1])
        fits = [row for row in timebase if row["channel"] == key and "fs_hz" in row]
        weights = [row["n_anchors"] for row in fits]
        received = summary["packets_received"]
        missing = summary["missing_packets"]
        bits = summary.get("status_bit_counts", {})
        channels[key] = {
            "name": s.name, "fs_nominal_hz": s.fs_nominal_hz,
            "fs_estimated_hz": (float(np.average([r["fs_hz"] for r in fits],
                                                 weights=weights)) if fits else None),
            "fs_deviation_ppm": (float((np.average([r["fs_hz"] for r in fits],
                                                   weights=weights) / s.fs_nominal_hz
                                        - 1) * 1e6) if fits else None),
            "chains": summary["chains"], "packets_received": received,
            "packets_missing": missing,
            "packet_loss_fraction": missing / (received + missing)
            if received + missing else None,
            "samples_accepted": summary["samples_accepted"],
            "samples_lost_counted": sum(g["lost_samples"] or 0 for g in summary["gaps"]),
            "gaps": len(summary["gaps"]),
            "packets_quarantined": summary["packets_quarantined"],
            "status_flags": {STATUS_FLAGS[b]: bits.get(STATUS_FLAGS[b], 0)
                             for b in STATUS_FLAGS if STATUS_FLAGS[b] in bits},
            "latency_applied": s.latency_applied, "slot_offset_us": s.slot_offset_us,
        }
    codes = [e["code"] for e in events]
    return {
        "version": VERSION, "source_type": manifest["source_type"],
        "subject_id": manifest.get("subject_id"), "session_id": manifest.get("session_id"),
        "recording": Path(recording["directory"]).name,
        "raw_sha256": manifest["raw"]["sha256"],
        "device_session_id": session["session_id"],
        "device_sessions_in_recording": len(decode["sessions"]),
        "duration_s": (max(ends) - min(starts)) / 1e6 if starts else None,
        "channels": channels,
        "packets_missing_total": sum(c["packets_missing"] for c in channels.values()),
        "events": {name: codes.count(code) for code, name in EVENT_NAMES.items()},
        "markers": codes.count(4),
        "cuffs": {status: sum(c["status"] == status for c in cuffs)
                  for status in CUFF_STATUS},
        "cuffs_with_flags": sum(bool(c.get("flags")) for c in cuffs),
        "issue_counts": decode["issue_counts"], "flags": flags,
        "ppg_led_lock": session.get("ppg_led_lock"),
    }
