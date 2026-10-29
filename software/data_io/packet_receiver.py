"""Receiver checks of Packet Schema V0.1/V0.2 section 12, per session and channel.

Pure code: the input is decoded packets in arrival order plus the decoder log,
the output is JSON/CSV bytes. Nothing here reads a port or file or prints.
Gaps are marked, never interpolated or bridged; ECG and PPG are never joined
by sample index and no channel is shifted in time. PC receive time (``t_rx``)
is not an input: the runner logs it in a separate file and it is never used as
a sample time. Tolerances are configuration values that have not been
verified on hardware.
"""

import json
import re
from bisect import bisect_left, bisect_right
from collections import Counter
from fractions import Fraction
from pathlib import PurePosixPath

from software.data_io.command_wire import LED_CODE_MAX
from software.data_io.packet_wire import (
    AFE_CONFIG_CHANNEL, AFE_CONFIG_LAYOUT, AFES, COMMAND_ACK_CHANNEL,
    COMMAND_ACK_LAYOUT, COMMAND_NAMES, COMMAND_RESULTS,
    CHANNELS, DEVICE_INFO_CHANNEL, DEVICE_INFO_COUNT, DEVICE_INFO_LAYOUT, ECG_CHANNEL,
    EVENT_CHANNEL, IMU_CHANNELS, MAX_SAMPLE_COUNT, PPG_CHANNELS, SAMP_ANCHOR_BIT,
    STATUS_BITS, TEMP_CHANNEL, TEMP_FS_MHZ, WIRE_VERSION, WIRE_VERSION_V02,
    status_reserved_mask,
)

# v1 (2026-10-23): channel_missing, event ordinal check, FS 0 never an index
# reference, rate (not period) tolerance; Packet Schema V0.2 (2026-10-24), with
# its section 7 (SAMP anchor, bit 8) the same day and section 11 (die temperature
# 0xB1) on 2026-10-25. v0 was committed in 250139d. v2 (2026-10-25): sections 12-13
# (0xD2, 0xD3), channel_holes with two new required config keys, 0xD1 phase check.
# v3 (2026-10-29): session metadata v1 (study ids, locked LED codes), the locked
# codes checked against the MAX30101 0xD2 states (``ppg_led_lock`` per session).
LOGGER_VERSION = "packet-logger-v3"
DEVICE_INFO_PERIOD_US = 10_000_000  # V0.2 section 6: one 0xD1 every 10 s
PACKET_SCHEMAS = {WIRE_VERSION: "packet-v0.1", WIRE_VERSION_V02: "packet-v0.2"}
# v1 (2026-10-29) adds STUDY_FIELDS; v0 (the generator's, and every recording
# before v1) is still read, with those fields taken as null.
METADATA_VERSION = "packet-session-metadata-v1"
METADATA_V0 = "packet-session-metadata-v0"
SOURCE_TYPES = ("SYNTHETIC", "DEVICE")
# Study identifiers (docs/quy_uoc_du_lieu.md): a participant is SUB + 3 digits and
# only ever DEVICE data; SYN_* is test data and only ever SYNTHETIC. session_id is
# the study session (S + 3 digits), not the firmware SESSION_ID, which the manifest
# calls device_session_id; one study session may span several of those.
SUBJECT_PATTERN = re.compile(r"SUB[0-9]{3}")
SYNTHETIC_SUBJECT_PATTERN = re.compile(r"SYN_[A-Za-z0-9_]+")
STUDY_SESSION_PATTERN = re.compile(r"S[0-9]{3}")
STUDY_FIELDS = ("subject_id", "session_id", "ppg_led_lock", "cuff_log")
# Locked PPG LED codes (protocol 6.1): 0.2 mA steps, green per sink. MAX30101
# registers (firmware/include/max30101.h): LED1_PA red, LED2_PA IR, LED3_PA and
# LED4_PA green, both driven with the green code.
LED_COLORS = ("green", "red", "ir")
LED_LOCK_FIELDS = {*LED_COLORS, "outside_dc_range"}
LED_REGISTERS = {"red": "0x0C", "ir": "0x0D", "green_led3": "0x0E",
                 "green_led4": "0x0F"}
UINT32 = 1 << 32
# Provisional rules, pending Duc Anh (docs/protocol/packet_logger.md): a
# FIRST_SAMPLE_INDEX jump of known length is explained by STATUS bit 0 or 1, a
# re-anchor of unknown length by bit 5; the bit may be on either packet next to
# the jump. Event packets (0xC1) skip the anchor check (step 6); their
# FIRST_SAMPLE_INDEX is the event ordinal and is checked against SEQ instead.
AFE_OVERFLOW_BIT = 1 << 0
MCU_BUFFER_BIT = 1 << 1
KNOWN_GAP_BITS = AFE_OVERFLOW_BIT | MCU_BUFFER_BIT
REANCHOR_BIT = 1 << 5
BACKLOG_BIT = 1 << 7  # V0.2: backlog chunk, the anchor belongs to a later chunk
# Accepted DATA range [low, high) per channel; IMU words are signed int16, the
# die temperature TINT * 16 + TFRAC (signed 8-bit TINT, 1/16 degC).
DATA_LIMITS = {ECG_CHANNEL: (0, 1 << 24),
               **{channel: (0, 1 << 18) for channel in PPG_CHANNELS},
               **{channel: (-(1 << 15), 1 << 15) for channel in IMU_CHANNELS},
               TEMP_CHANNEL: (-(1 << 11), 1 << 11)}
EVENT_CODES = (1, 2, 3, 4)
ORDINAL_CHANNELS = {
    EVENT_CHANNEL: ("events_lost_before_send", "event_ordinal_inconsistent"),
    DEVICE_INFO_CHANNEL: ("device_info_lost_before_send",
                          "device_info_ordinal_inconsistent"),
    AFE_CONFIG_CHANNEL: ("afe_config_lost_before_send",
                         "afe_config_ordinal_inconsistent"),
    COMMAND_ACK_CHANNEL: ("command_ack_lost_before_send",
                          "command_ack_ordinal_inconsistent"),
}
# Channels that carry no samples and need no metadata entry (V0.2 sections 12-13).
CONTROL_CHANNELS = (AFE_CONFIG_CHANNEL, COMMAND_ACK_CHANNEL)
CONFIG_FIELDS = {
    "schema_version", "packet_schemas", "status", "wire_versions",
    "anchor_tolerance_samples", "anchor_tolerance_extra_us",
    "anchor_rate_tolerance_ppm", "ecg_anchor_rate_tolerance_ppm",
    "samp_anchor_tolerance_us", "temp_anchor_tolerance_us",
    "channel_offset_tolerance_us", "channel_silence_tolerance_us",
    "device_info_anchor_tolerance_us", "read_chunk_bytes",
}
TEXT_FIELDS = (
    "clock_id", "firmware_version", "firmware_commit", "device_id", "operator",
    "electrode_type", "electrode_placement",
)
CHANNEL_FIELDS = (
    "sensor", "fs_nominal_mhz", "latency_l_us", "latency_source",
    "unit_conversion", "afe_config",
)
# V0.2 section 8: ECG may declare the latency of SAMP anchors (bit 8) apart from
# latency_l_us, which belongs to FIFO-read anchors. Both or neither.
SAMP_LATENCY_FIELDS = ("latency_samp_l_us", "latency_samp_source")
SIMULATION_FIELDS = {"generator", "case", "config_sha256", "common_index_epoch"}
PACKET_COLUMNS = (
    "arrival", "stream_offset", "session_id", "version", "channel_id", "seq", "seq_ext",
    "first_sample_index", "sample_index_ext", "chain_id", "t_anchor_us",
    "t_first_us", "fs_nominal_mhz", "sample_count", "status", "disposition",
)
# version last: a session that mixes versions has two (channel, chain, index) sets.
SAMPLE_COLUMNS = (
    "session_id", "channel_id", "chain_id", "seq_ext", "sample_index_ext", "value",
    "version",
)
LIMITATIONS = [
    "Tolerances and STATUS rules are provisional and not verified on hardware",
    "Packets lost before the first or after the last received SEQ are not detectable",
    "Channel offset is reported only for SYNTHETIC streams with a known common epoch",
    "Anchors are checked from both ends of each chain and the direction that "
    "quarantines fewer packets is kept (forward on a tie): a lasting time step "
    "quarantines the shorter side, and if the first and the last anchor of a "
    "chain are both bad, the good packets between them can be quarantined",
    "The anchor rate tolerance assumes the true sample rate is within "
    "anchor_rate_tolerance_ppm (ECG: ecg_anchor_rate_tolerance_ppm) of "
    "FS_NOMINAL_MHZ; it is not measured",
    "A false SYNC followed by a passing CRC (about 1 in 65536) is not excluded",
    "Anchors of packets with STATUS bit 0 (AFE FIFO overflow) are neither checked "
    "nor used as references: the FIFO held older samples, so the anchor is late. "
    "Their samples are kept (disposition accepted_anchor_unreliable); a bit 0 "
    "carried from a lost packet also skips the check",
    "V0.2 backlog chunks (STATUS bit 7) are handled like bit 0: samples kept, "
    "anchor neither checked nor a reference; if the newest chunk is lost, the "
    "earlier chunks have no usable anchor",
    "A V0.2 re-anchor (STATUS bit 5) always starts a new chain; several lost "
    "re-anchors merged into one gap are seen as one",
    "V0.2 ECG anchors are checked per source within a chain: SAMP edges (bit 8) "
    "against SAMP edges with samp_anchor_tolerance_us, FIFO reads against FIFO "
    "reads; the two are never compared. A one-sample error of the SAMP mapping "
    "that holds from the first SAMP packet of a chain is not detectable here "
    "(Packet Schema V0.2 section 7.2)",
    "A SAMP check that would also pass a one-sample shift at some rate and anchor "
    "error inside the tolerance (a long gap), or a SAMP packet with no other SAMP "
    "packet in its chain, is reported as anchor_check_weak, not as checked",
    "ppg_led_lock is checked against the MAX30101 states of 0xD2 only: states "
    "before the first one with the locked codes in a session (boot defaults, "
    "calibration) are not reported; whether a subject wears the device is not "
    "known to the logger",
]


def channel_key(channel_id):
    return f"0x{channel_id:02X}"


def json_bytes(value):
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False,
                       allow_nan=False) + "\n").encode("utf-8")


def _integer(value, name, minimum=0, maximum=None):
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum or (
        maximum is not None and value > maximum
    ):
        raise ValueError(f"{name} must be an integer in [{minimum}, {maximum}]")


def validate_config(config):
    # Version first: a config of another logger version has other keys, and the
    # error should name the version, not the keys.
    if not isinstance(config, dict):
        raise ValueError("Logger config must be a JSON object")
    if config.get("schema_version") != LOGGER_VERSION:
        raise ValueError(f"Unsupported logger config version "
                         f"{config.get('schema_version')!r}; this logger is "
                         f"{LOGGER_VERSION}")
    if set(config) != CONFIG_FIELDS:
        raise ValueError("Logger config has missing or unsupported fields")
    if not isinstance(config["status"], str) or not config["status"]:
        raise ValueError("status must be nonempty text")
    versions = config["wire_versions"]
    if (not isinstance(versions, list) or not versions
            or any(v not in PACKET_SCHEMAS for v in versions)
            or versions != sorted(set(versions))):
        raise ValueError("wire_versions must be a sorted list of 1 (V0.1) and/or 2 "
                         "(V0.2)")
    if config["packet_schemas"] != [PACKET_SCHEMAS[v] for v in versions]:
        raise ValueError("packet_schemas must name the schema of each wire version")
    _integer(config["anchor_tolerance_samples"], "anchor_tolerance_samples", 0, 32)
    _integer(config["anchor_tolerance_extra_us"], "anchor_tolerance_extra_us", 0,
             10 ** 6)
    _integer(config["anchor_rate_tolerance_ppm"], "anchor_rate_tolerance_ppm", 0,
             10 ** 5)
    _integer(config["ecg_anchor_rate_tolerance_ppm"], "ecg_anchor_rate_tolerance_ppm",
             0, 10 ** 5)
    _integer(config["samp_anchor_tolerance_us"], "samp_anchor_tolerance_us", 0,
             10 ** 6)
    # Below one period, so that a window of phases keeps anchors increasing.
    _integer(config["temp_anchor_tolerance_us"], "temp_anchor_tolerance_us", 0,
             10 ** 6 - 1)
    _integer(config["channel_offset_tolerance_us"], "channel_offset_tolerance_us",
             0, 10 ** 6)
    _integer(config["channel_silence_tolerance_us"], "channel_silence_tolerance_us",
             1, 10 ** 8)
    # Below half a period, so that one window never holds two ordinals' phases.
    _integer(config["device_info_anchor_tolerance_us"],
             "device_info_anchor_tolerance_us", 0, DEVICE_INFO_PERIOD_US // 2 - 1)
    _integer(config["read_chunk_bytes"], "read_chunk_bytes", 1, 1 << 20)
    return True


def validate_metadata(metadata):
    """Session metadata (schema section 11): unknown values are null with a reason.

    v1 adds the study fields (``STUDY_FIELDS``); v0 has none of them."""
    if not isinstance(metadata, dict):
        raise ValueError("Session metadata must be a JSON object")
    version = metadata.get("schema_version")
    if version not in (METADATA_V0, METADATA_VERSION):
        raise ValueError(f"Unsupported session metadata version {version!r}")
    fields = {"schema_version", "source_type", *TEXT_FIELDS, "channels",
              "simulation", "null_reasons"}
    if version == METADATA_VERSION:
        fields.update(STUDY_FIELDS)
    if set(metadata) != fields:
        raise ValueError(f"Session metadata has missing or unsupported fields for "
                         f"{version}")
    if metadata["source_type"] not in SOURCE_TYPES:
        raise ValueError("source_type must be SYNTHETIC or DEVICE")
    nulls = set()
    for name in TEXT_FIELDS:
        value = metadata[name]
        if value is None:
            nulls.add(name)
        elif not isinstance(value, str) or not value or value.strip() != value:
            raise ValueError(f"{name} must be nonempty text or null")
    channels = metadata["channels"]
    known = {channel_key(channel) for channel in CHANNELS}
    if not isinstance(channels, dict) or not channels or not set(channels) <= known:
        raise ValueError("channels must map known CHANNEL_ID keys such as 0xE1")
    for key, spec in channels.items():
        names = CHANNEL_FIELDS
        if key == channel_key(ECG_CHANNEL) and isinstance(spec, dict) and (
            set(SAMP_LATENCY_FIELDS) <= set(spec)
        ):
            names = CHANNEL_FIELDS + SAMP_LATENCY_FIELDS
        if not isinstance(spec, dict) or set(spec) != set(names):
            raise ValueError(f"Channel {key} metadata has missing or extra fields")
        for name in names:
            value = spec[name]
            if value is None:
                nulls.add(f"channels.{key}.{name}")
            elif name in ("fs_nominal_mhz", "latency_l_us", "latency_samp_l_us"):
                _integer(value, f"{key}.{name}")
            elif name == "afe_config":
                if not isinstance(value, dict):
                    raise ValueError("afe_config must be an object or null")
            elif not isinstance(value, str) or not value:
                raise ValueError(f"{key}.{name} must be nonempty text or null")
    simulation = metadata["simulation"]
    if simulation is not None:
        if metadata["source_type"] != "SYNTHETIC":
            raise ValueError("simulation metadata is only allowed for SYNTHETIC")
        if not isinstance(simulation, dict) or set(simulation) != SIMULATION_FIELDS:
            raise ValueError("simulation metadata has missing or extra fields")
        if not isinstance(simulation["common_index_epoch"], bool):
            raise ValueError("common_index_epoch must be a boolean")
    if version == METADATA_VERSION:
        nulls |= _validate_study_fields(metadata)
    reasons = metadata["null_reasons"]
    if not isinstance(reasons, dict) or set(reasons) != nulls or not all(
        isinstance(text, str) and text.strip() for text in reasons.values()
    ):
        raise ValueError("null_reasons must give a reason for exactly the null fields")
    return True


def _validate_study_fields(metadata):
    """Checks of the v1 study fields; returns the names that are null."""
    subject, session = metadata["subject_id"], metadata["session_id"]
    lock, cuff_log = metadata["ppg_led_lock"], metadata["cuff_log"]
    if subject is not None:
        if not isinstance(subject, str):
            raise ValueError("subject_id must be text or null")
        if SUBJECT_PATTERN.fullmatch(subject):
            if metadata["source_type"] != "DEVICE":
                raise ValueError("A participant subject_id (SUB###) needs DEVICE")
        elif SYNTHETIC_SUBJECT_PATTERN.fullmatch(subject):
            if metadata["source_type"] != "SYNTHETIC":
                raise ValueError("A SYN_* subject_id needs SYNTHETIC")
        else:
            raise ValueError("subject_id must be SUB + 3 digits (participant), "
                             "SYN_* (test) or null")
    if session is not None and (
        not isinstance(session, str) or not STUDY_SESSION_PATTERN.fullmatch(session)
    ):
        raise ValueError("session_id must be S + 3 digits (study session) or null")
    if (subject is None) != (session is None):
        raise ValueError("subject_id and session_id are both set or both null")
    if lock is not None:
        if not isinstance(lock, dict) or set(lock) != LED_LOCK_FIELDS:
            raise ValueError(f"ppg_led_lock must have exactly "
                             f"{sorted(LED_LOCK_FIELDS)}")
        for color in LED_COLORS:
            _integer(lock[color], f"ppg_led_lock.{color}", 0, LED_CODE_MAX)
        outside = lock["outside_dc_range"]
        if not isinstance(outside, list) or any(
            color not in LED_COLORS for color in outside
        ) or len(set(outside)) != len(outside):
            raise ValueError("ppg_led_lock.outside_dc_range must list distinct colors "
                             "of green, red, ir")
        if not {channel_key(c) for c in PPG_CHANNELS} & set(metadata["channels"]):
            raise ValueError("ppg_led_lock needs a declared PPG channel")
    if cuff_log is not None:
        path = PurePosixPath(cuff_log) if isinstance(cuff_log, str) else None
        if (path is None or not cuff_log or cuff_log.strip() != cuff_log
                or "\\" in cuff_log or ":" in cuff_log or path.is_absolute()
                or ".." in path.parts):
            raise ValueError("cuff_log must be a relative path (inside the study "
                             "session directory) or null")
        if session is None:
            raise ValueError("cuff_log needs a study session_id")
    return {name for name in STUDY_FIELDS if metadata[name] is None}


def study_metadata(metadata):
    """The study fields of validated metadata; all null for v0."""
    return {name: metadata.get(name) for name in STUDY_FIELDS}


def is_participant(metadata):
    """True for participant data (a SUB### subject_id); never for v0 metadata."""
    subject = metadata.get("subject_id")
    return subject is not None and bool(SUBJECT_PATTERN.fullmatch(subject))


def _unwrap(value, reference):
    """Extend a uint32 counter to the integer congruent mod 2**32 nearest reference."""
    half = UINT32 // 2
    return reference + (value - reference + half) % UINT32 - half


def _status_counts(packets, version, channel_id):
    """Named bits of the packet's version and channel; reserved bits are reported
    apart."""
    reserved = status_reserved_mask(version, channel_id)
    counts = Counter()
    for packet in packets:
        for bit, name in STATUS_BITS.items():
            if not reserved >> bit & 1 and packet.status >> bit & 1:
                counts[name] += 1
    return dict(sorted(counts.items()))


def analyze_stream(decoded, decoder, config, metadata):
    """Check decoded packets (arrival order); return result, packet and sample rows."""
    validate_config(config)
    validate_metadata(metadata)
    issues = []

    def issue(code, **detail):
        issues.append({"code": code, **detail})

    for error in decoder.errors:
        issue(error.code, offset=error.offset)
    for offset, length in decoder.skipped:
        issue("skipped_bytes", offset=offset, length=length)

    # State per (SESSION_ID, VERSION): a session must not mix versions, and if it
    # does, SEQ and timing of the two are never joined (V0.2 section 1).
    rows, sessions, previous, first_version = [], {}, None, {}
    for arrival, item in enumerate(decoded):
        packet = item.packet
        if previous is not None and packet.session_id != previous:
            issue("session_change", offset=item.offset, session_id=packet.session_id,
                  previous_session_id=previous)
        previous = packet.session_id
        known_version = first_version.setdefault(packet.session_id, packet.version)
        if packet.version != known_version and (
            (packet.session_id, packet.version) not in sessions
        ):
            issue("version_mixed_in_session", offset=item.offset,
                  session_id=packet.session_id, version=packet.version,
                  first_version=known_version)
        state = sessions.setdefault((packet.session_id, packet.version), {}).setdefault(
            packet.channel_id, {"received": {}, "rows": {}, "conflicts": set(),
                                "max": None},
        )
        seq = packet.seq if state["max"] is None else _unwrap(packet.seq, state["max"])
        row = {
            "arrival": arrival, "stream_offset": item.offset,
            "session_id": packet.session_id, "version": packet.version,
            "channel_id": channel_key(packet.channel_id), "seq": packet.seq,
            "seq_ext": seq, "first_sample_index": packet.first_sample_index,
            "sample_index_ext": None, "chain_id": None,
            "t_anchor_us": packet.t_anchor_us,
            "t_first_us": packet.t_first_us,
            "fs_nominal_mhz": packet.fs_nominal_mhz,
            "sample_count": len(packet.data), "status": packet.status,
            "disposition": None,
        }
        rows.append(row)
        where = {"session_id": packet.session_id,
                 "channel": channel_key(packet.channel_id), "seq": seq}
        known = state["received"].get(seq)
        if known is not None:
            if known.packet == packet:
                issue("duplicate", **where)
                row["disposition"] = "duplicate"
            else:
                issue("conflicting_duplicate", **where)
                state["conflicts"].add(seq)
                row["disposition"] = "conflicting_duplicate"
            continue
        if state["max"] is not None and seq < state["max"]:
            issue("out_of_order", **where)
        state["max"] = seq if state["max"] is None else max(seq, state["max"])
        state["received"][seq] = item
        state["rows"][seq] = row

    result_sessions, samples = [], []
    lock = study_metadata(metadata)["ppg_led_lock"]
    first_session = decoded[0].packet.session_id if decoded else None
    for (session_id, version), channels in sessions.items():
        summaries, events, firsts, records = {}, [], {}, {}
        for channel_id in sorted(channels):
            summary, channel_events, channel_samples, first, info = _check_channel(
                session_id, version, channel_id, channels[channel_id], config,
                metadata, issue,
            )
            summaries[channel_key(channel_id)] = summary
            events += channel_events
            samples += channel_samples
            records[channel_id] = info
            if first is not None:
                firsts[channel_id] = first
        # A declared data channel with no decoded packet at all in this session
        # (a dead AFE, say) would otherwise leave no trace. Events may be absent;
        # device info has its own check below.
        missing = [key for key in sorted(metadata["channels"])
                   if int(key, 16) not in (EVENT_CHANNEL, DEVICE_INFO_CHANNEL,
                                           *CONTROL_CHANNELS)
                   and int(key, 16) not in channels]
        for key in missing:
            issue("channel_missing", session_id=session_id, version=version,
                  channel=key)
        holes = _channel_holes(session_id, version, channels, config, metadata, issue)
        control = _session_control(session_id, version,
                                   records.get(AFE_CONFIG_CHANNEL, []),
                                   records.get(COMMAND_ACK_CHANNEL, []), metadata, issue)
        result_sessions.append({
            "session_id": session_id, "packet_schema": PACKET_SCHEMAS[version],
            "channels": summaries, "channels_missing": missing,
            "channel_holes": holes, "events": events,
            "device_info": _session_device_info(
                session_id, version, records.get(DEVICE_INFO_CHANNEL, []), metadata,
                issue),
            **control,
            "ppg_led_lock": _led_lock(session_id, version, control["afe_config"], lock,
                                      session_id != first_session, issue),
            "channel_offset": _channel_offset(session_id, firsts, config, metadata,
                                              issue),
        })
    result = {
        "logger_version": LOGGER_VERSION,
        "packet_schemas": sorted({s["packet_schema"] for s in result_sessions}),
        "source_type": metadata["source_type"],
        "time_encoding": "integer-us; deviation/offset as rational-string-us",
        "decode": {
            "bytes": decoder.bytes_seen, "packets_decoded": len(decoded),
            "errors": dict(sorted(Counter(e.code for e in decoder.errors).items())),
            # SYNC candidates inside a packet already counted as an error.
            "sync_candidates_rejected": len(decoder.rejected_candidates),
            "skipped_runs": len(decoder.skipped),
            "skipped_bytes": sum(length for _, length in decoder.skipped),
        },
        "sessions": result_sessions,
        "issues": issues,
        "issue_counts": dict(sorted(Counter(i["code"] for i in issues).items())),
        "limitations": LIMITATIONS,
    }
    return result, rows, samples


def _check_channel(session_id, version, channel_id, state, config, metadata, issue):
    """Checks of one (session, version, channel); returns ``(summary, events,
    samples, first, device_info)``."""
    received, conflicts, rows = state["received"], state["conflicts"], state["rows"]
    key = channel_key(channel_id)
    where = {"session_id": session_id, "version": version, "channel": key}
    seqs = sorted(received)
    missing = 0
    for before, after in zip(seqs, seqs[1:]):
        if after - before > 1:
            missing += after - before - 1
            issue("missing_packets", **where, after_seq=before,
                  count=after - before - 1)
    reserved = status_reserved_mask(version, channel_id)
    for seq in seqs:
        packet = received[seq].packet
        if packet.status & reserved:
            issue("status_reserved_bits", **where, seq=seq, status=packet.status)
        if seq in conflicts:
            rows[seq]["disposition"] = "conflicting_duplicate"
    present = [seq for seq in seqs if seq not in conflicts]
    if channel_id in CONTROL_CHANNELS:
        # V0.2 sections 12-13: no samples, no metadata entry, no anchor check.
        summary = {
            "name": CHANNELS[channel_id], "packets_received": len(seqs),
            "conflicting_duplicates": len(conflicts), "missing_packets": missing,
            "first_seq": seqs[0], "last_seq": seqs[-1],
            "status_bit_counts": _status_counts((received[s].packet for s in seqs),
                                                version, channel_id),
        }
        decode = (decode_afe_config if channel_id == AFE_CONFIG_CHANNEL
                  else decode_command_ack)
        valid = _check_control(channel_id, decode, present, received, rows, where,
                               issue)
        summary["valid_packets"] = len(valid)
        return summary, [], [], None, valid
    # V0.2 section 11.2: a 0xB1 header outside its contract is not trusted.
    untrusted = set()
    if channel_id == TEMP_CHANNEL:
        for seq in present:
            packet = received[seq].packet
            if (len(packet.data) != 1 or packet.fs_nominal_mhz != TEMP_FS_MHZ
                    or packet.t_first_us != packet.t_anchor_us
                    or packet.status & reserved):
                issue("temp_header_invalid", **where, seq=seq)
                untrusted.add(seq)
    spec = metadata["channels"].get(key)
    if spec is None:
        issue("channel_without_metadata", **where)
    summary = {
        "name": CHANNELS[channel_id], "packets_received": len(seqs),
        "conflicting_duplicates": len(conflicts), "missing_packets": missing,
        "first_seq": seqs[0], "last_seq": seqs[-1],
        "status_bit_counts": _status_counts((received[s].packet for s in seqs),
                                            version, channel_id),
        "fs_nominal_mhz": sorted({received[s].packet.fs_nominal_mhz for s in seqs}),
    }
    if channel_id == EVENT_CHANNEL:
        events = _check_events(session_id, present, received, rows, where, issue)
        summary["events"] = len(events)
        return summary, events, [], None, []
    if channel_id == DEVICE_INFO_CHANNEL:
        identities = _check_device_info(present, received, rows, where, issue)
        summary["device_info_valid_packets"] = len(identities)
        return summary, [], [], None, identities

    if spec is not None and spec["fs_nominal_mhz"] is not None and (
        summary["fs_nominal_mhz"] != [spec["fs_nominal_mhz"]]
    ):
        issue("fs_metadata_mismatch", **where)
    index, quarantine, jumps = _index_pass(present, received, where, issue, version,
                                           untrusted, channel_id == TEMP_CHANNEL)
    quarantine.update(dict.fromkeys(untrusted, "temp_header_invalid"))
    chain_of, chains = _chains(present, received, quarantine, jumps, where, issue)
    # Bit 0: the FIFO was full, so the samples are older than the anchor. V0.2
    # bit 7: a backlog chunk, whose anchor is that of a later chunk. Keep the
    # samples; leave the anchor out of the timing check and the references.
    untimed_bits = AFE_OVERFLOW_BIT | (BACKLOG_BIT if version >= WIRE_VERSION_V02
                                       else 0)
    untimed = {seq for seq in present
               if received[seq].packet.status & untimed_bits}
    rate_ppm = config["ecg_anchor_rate_tolerance_ppm" if channel_id == ECG_CHANNEL
                      else "anchor_rate_tolerance_ppm"]
    fifo_read = (config["anchor_tolerance_samples"],
                 config["anchor_tolerance_extra_us"], rate_ppm)
    # V0.2 section 7.5: ECG anchors are SAMP edges (bit 8) or FIFO reads, with an
    # unknown offset between the two, so each source is checked on its own.
    by_source = version >= WIRE_VERSION_V02 and channel_id == ECG_CHANNEL
    edges = {seq for seq in present
             if by_source and received[seq].packet.status & SAMP_ANCHOR_BIT}
    # Anchors that passed a comparison with another one (for _channel_holes).
    verified = state["verified"] = set()
    for chain in chains:
        checked = [seq for seq in chain if seq not in untimed]
        if channel_id == TEMP_CHANNEL:
            verified |= _phase_pass(checked, received, index, quarantine,
                                    config["temp_anchor_tolerance_us"], where, issue)
            continue
        if not by_source:
            verified |= _timing_pass(checked, received, index, quarantine, fifo_read,
                                     where, issue)
            continue
        verified |= _timing_pass([seq for seq in checked if seq in edges], received,
                                 index, quarantine,
                                 (0, config["samp_anchor_tolerance_us"], rate_ppm),
                                 where, issue, "samp")
        verified |= _timing_pass([seq for seq in checked if seq not in edges], received,
                                 index, quarantine, fifo_read, where, issue,
                                 "fifo_read")
    if edges:
        # Section 7.2: SAMP comes back only after a mapping restart (SYNCH), whose
        # first packet has bit 5 (or gets it from FS-0 packets just before, as in
        # _index_pass). With no SEQ missing between, none was lost.
        pending = 0
        for before, seq in zip(present, present[1:]):
            packet = received[before].packet
            pending = pending | packet.status if packet.fs_nominal_mhz == 0 else 0
            restart = (received[seq].packet.status | pending) & REANCHOR_BIT
            if seq == before + 1 and seq in edges and before not in edges and (
                not restart
            ):
                issue("samp_resumed_without_reanchor", **where, seq=seq)
        # Section 8: the latency of SAMP anchors is not that of FIFO reads.
        if spec is not None and SAMP_LATENCY_FIELDS[0] not in spec:
            issue("samp_latency_metadata_missing", **where)
    accepted = [seq for seq in present if seq not in quarantine]
    gaps = _gaps(seqs, accepted, received, index, quarantine, conflicts, jumps)
    samples = []
    low, high = DATA_LIMITS[channel_id]
    for seq in present:
        rows[seq]["sample_index_ext"] = index[seq]
        rows[seq]["chain_id"] = chain_of[seq]
        rows[seq]["disposition"] = quarantine.get(
            seq, "accepted_anchor_unreliable" if seq in untimed else "accepted")
    for seq in accepted:
        packet = received[seq].packet
        if any(not low <= value < high for value in packet.data):
            issue("data_out_of_range", **where, seq=seq)
        samples += [(session_id, key, chain_of[seq], seq, index[seq] + i, value,
                     version) for i, value in enumerate(packet.data)]
    timed = [seq for seq in accepted if seq not in untimed]
    summary.update({
        "packets_accepted": len(accepted),
        "packets_anchor_unreliable": len(accepted) - len(timed),
        "packets_quarantined": dict(sorted(Counter(quarantine.values()).items())),
        "chains": len(chains),
        "first_sample_index": index[accepted[0]] if accepted else None,
        "samples_accepted": len(samples), "gaps": gaps,
    })
    if by_source:
        # Bit 8 as sent, on every received packet (quarantined and bit 0/7 ones
        # too), so that a fallback to FIFO reads stays visible.
        summary["anchor_sources"] = {
            "samp": len(edges), "fifo_read": len(present) - len(edges),
            "switch_seqs": [seq for before, seq in zip(present, present[1:])
                            if (before in edges) != (seq in edges)],
        }
    first = None
    if timed:
        packet = received[timed[0]].packet
        first = (index[timed[0]] + len(packet.data) - 1, packet)
    return summary, [], samples, first, []


def _ordinals(channel_id, present, received, where, issue, bit1_means_loss=True):
    """Ordinal (FIRST_SAMPLE_INDEX) against SEQ for 0xC1 and 0xD1; ``{seq: ordinal}``.

    SEQ is assigned at send time, so between two received packets the ordinal
    moves by the SEQ gap (lost on USB, already ``missing_packets``) plus the
    packets dropped before a SEQ was given. More is ``*_lost_before_send``; less
    is ``*_ordinal_inconsistent``, after which the check restarts from that
    packet, so one bad ordinal does not flag every later one (the loss count next
    to a bad ordinal is then unreliable). STATUS bit 1 with no counted gap (the
    first packet, or, for t0, an edge the firmware dropped before it became an
    event) gives a loss of unknown count.
    """
    lost_code, inconsistent_code = ORDINAL_CHANNELS[channel_id]
    ordinals, previous = {}, None
    for seq in present:
        packet = received[seq].packet
        if previous is None:
            ordinal, lost = packet.first_sample_index, 0
        else:
            ordinal = _unwrap(packet.first_sample_index, previous[1])
            lost = (ordinal - previous[1]) - (seq - previous[0])
        detail = {**where, "seq": seq, "ordinal": ordinal}
        if lost < 0:
            issue(inconsistent_code, **detail, previous_seq=previous[0],
                  previous_ordinal=previous[1])
        elif lost > 0:
            issue(lost_code, **detail, lost=lost)
        elif bit1_means_loss and packet.status & MCU_BUFFER_BIT:
            issue(lost_code, **detail, lost=None)
        previous = ordinals[seq] = (seq, ordinal)
    return {seq: ordinal for seq, (_, ordinal) in ordinals.items()}


def _check_events(session_id, present, received, rows, where, issue):
    """Event packets: code checks, and the event ordinal against SEQ (R1)."""
    ordinals = _ordinals(EVENT_CHANNEL, present, received, where, issue)
    events = []
    for seq in present:
        packet = received[seq].packet
        rows[seq]["disposition"] = "event"
        if len(packet.data) != 1:
            issue("event_sample_count", **where, seq=seq)
        elif packet.data[0] not in EVENT_CODES:
            issue("unknown_event_code", **where, seq=seq, event_code=packet.data[0])
        events.append({"session_id": session_id, "seq_ext": seq,
                       "event_ordinal": ordinals[seq],
                       "t_anchor_us": packet.t_anchor_us, "data": list(packet.data)})
    return events


def _ascii_field(raw):
    """A NUL-terminated, NUL-padded ASCII field (V0.2 section 6); None if not."""
    end = raw.find(b"\0")
    if end < 0 or any(raw[end:]) or any(b >= 0x80 for b in raw[:end]):
        return None
    return raw[:end].decode("ascii")


def decode_device_info(packet):
    """Payload of a V0.2 0xD1 packet as ``(identity, problem)``.

    Words are int32 holding the bit pattern of 4 bytes joined big-endian (V0.2
    section 6): DATA[1..8] the ELF SHA-256, DATA[9..16] the app version and
    DATA[17..24] the ESP-IDF version, 32 bytes of ASCII each.
    """
    data = packet.data
    if len(data) != DEVICE_INFO_COUNT:
        return None, "sample_count"
    if data[0] != DEVICE_INFO_LAYOUT:
        return None, "layout"
    if packet.fs_nominal_mhz != 0 or packet.t_first_us != packet.t_anchor_us:
        return None, "header"
    if packet.status & ~MCU_BUFFER_BIT:
        return None, "status"
    raw = b"".join((word & 0xFFFFFFFF).to_bytes(4, "big") for word in data[1:])
    app, idf = _ascii_field(raw[32:64]), _ascii_field(raw[64:96])
    if app is None or idf is None:
        return None, "text"
    return {"elf_sha256": raw[:32].hex(), "app_version": app, "idf_version": idf}, None


def _check_device_info(present, received, rows, where, issue):
    """V0.2 device info: payload checks and ordinal against SEQ; valid identities
    as ``(seq, identity)`` in SEQ order."""
    _ordinals(DEVICE_INFO_CHANNEL, present, received, where, issue)
    identities = []
    for seq in present:
        identity, problem = decode_device_info(received[seq].packet)
        rows[seq]["disposition"] = "device_info" if problem is None else (
            "device_info_invalid")
        if problem is not None:
            issue("device_info_invalid", **where, seq=seq, problem=problem)
        else:
            identities.append((seq, identity))
    return identities


def decode_afe_config(packet):
    """Payload of a V0.2 0xD2 packet (section 12) as ``(config, problem)``."""
    data = [word & 0xFFFFFFFF for word in packet.data]
    if packet.fs_nominal_mhz != 0 or packet.t_first_us != packet.t_anchor_us:
        return None, "header"
    if packet.status & ~MCU_BUFFER_BIT:
        return None, "status"
    if len(data) < 5:
        return None, "sample_count"
    layout, afe, source, state, generation = data[:5]
    words = data[5:]
    if layout != AFE_CONFIG_LAYOUT:
        return None, "layout"
    if afe not in AFES:
        return None, "afe"
    if source not in (0, 1) or state not in (0, 1):
        return None, "source_or_state"
    name, _, addresses, bits = AFES[afe]
    configured = source == 1 and state == 1
    if (source == 0 and generation != 0) or (configured and generation < 1):
        return None, "generation"
    if not configured:
        if words:
            return None, "registers"
        registers = {}
    else:
        if [w >> 24 for w in words] != list(addresses) or any(
            (w & 0xFFFFFF) >> bits for w in words
        ):
            return None, "registers"
        width = bits // 4
        registers = {f"0x{w >> 24:02X}": f"0x{w & 0xFFFFFF:0{width}X}" for w in words}
    return {"afe": name, "source": "chip" if source else "fake",
            "configured": bool(state), "generation": generation,
            "registers": registers}, None


def decode_command_ack(packet):
    """Payload of a V0.2 0xD3 packet (section 13) as ``(ack, problem)``.

    Only a SET_PPG_LED that was done carries a generation (>= 1); every other
    answer, PING and MARK_EVENT included, carries 0."""
    data = [word & 0xFFFFFFFF for word in packet.data]
    if packet.fs_nominal_mhz != 0 or packet.t_first_us != packet.t_anchor_us:
        return None, "header"
    if packet.status & ~MCU_BUFFER_BIT:
        return None, "status"
    if len(data) != 5:
        return None, "sample_count"
    layout, cmd_id, cmd_seq, result, generation = data
    if layout != COMMAND_ACK_LAYOUT:
        return None, "layout"
    if cmd_id > 0xFF or cmd_seq > 0xFFFF or result not in COMMAND_RESULTS:
        return None, "range"
    set_led_done = COMMAND_NAMES.get(cmd_id) == "set_ppg_led" and result == 0
    if (generation >= 1) != set_led_done:
        return None, "generation"
    return {"cmd_id": cmd_id, "cmd": COMMAND_NAMES.get(cmd_id), "cmd_seq": cmd_seq,
            "result": COMMAND_RESULTS[result], "generation": generation}, None


def _check_control(channel_id, decode, present, received, rows, where, issue):
    """0xD2 / 0xD3: ordinal against SEQ, then payload; valid ones as
    ``(seq, t_anchor_us, payload)`` in SEQ order.

    On 0xD2 the ordinal alone counts lost packets: bit 1 belongs to one AFE (its
    own earlier 0xD2 or transition was lost, V0.2 section 12), since three AFEs
    share the channel, and is reported per AFE (``afe_config_transition_lost``).
    """
    is_config = channel_id == AFE_CONFIG_CHANNEL
    _ordinals(channel_id, present, received, where, issue, bit1_means_loss=not is_config)
    code = "afe_config" if is_config else "command_ack"
    valid = []
    for seq in present:
        packet = received[seq].packet
        payload, problem = decode(packet)
        rows[seq]["disposition"] = code if problem is None else f"{code}_invalid"
        if problem is not None:
            issue(f"{code}_invalid", **where, seq=seq, problem=problem)
            continue
        if is_config and packet.status & MCU_BUFFER_BIT:
            issue("afe_config_transition_lost", **where, seq=seq, afe=payload["afe"])
        valid.append((seq, packet.t_anchor_us, payload))
    return valid


def _session_control(session_id, version, configs, acks, metadata, issue):
    """Session ``afe_config`` and ``commands`` (V0.2 sections 12-13); V0.1: None."""
    if version < WIRE_VERSION_V02:
        return {"afe_config": None, "commands": None}
    where = {"session_id": session_id}
    by_afe, highest, images = {}, {}, {}
    for seq, t_anchor, config in configs:
        name = config["afe"]
        epochs = by_afe.setdefault(name, [])
        state = {k: config[k] for k in ("source", "configured", "generation",
                                        "registers")}
        # Generations only go up, and one generation has one register image,
        # whatever came between (a down state, say).
        if config["generation"] < highest.get(name, 0):
            issue("afe_config_generation_backwards", **where, afe=name, seq=seq)
        highest[name] = max(highest.get(name, 0), config["generation"])
        if config["source"] == "chip" and config["configured"]:
            known = images.setdefault((name, config["generation"]),
                                      config["registers"])
            if known != config["registers"]:
                issue("afe_config_changed_in_generation", **where, afe=name, seq=seq)
        if not epochs or {k: epochs[-1][k] for k in state} != state:
            epochs.append({"first_seq": seq, "t_anchor_us": t_anchor, **state,
                           "packets": 0})
        epochs[-1]["packets"] += 1
    if metadata["source_type"] == "DEVICE":
        declared = {int(key, 16) for key in metadata["channels"]}
        for afe_id, (name, channels, _, _) in sorted(AFES.items()):
            if not declared & set(channels):
                continue
            epochs = by_afe.get(name, [])
            if not epochs:
                issue("afe_config_missing", **where, afe=name)
            for epoch in epochs:
                if epoch["source"] == "fake":
                    issue("afe_fake_source", **where, afe=name, seq=epoch["first_seq"])
                elif not epoch["configured"]:
                    issue("afe_not_configured", **where, afe=name,
                          seq=epoch["first_seq"])
    generations = {e["generation"] for e in by_afe.get(AFES[2][0], [])
                   if e["configured"]}
    commands = []
    for seq, t_anchor, ack in acks:
        if ack["generation"] >= 1 and ack["generation"] not in generations:
            issue("command_ack_without_config", **where, seq=seq,
                  generation=ack["generation"])
        if ack["result"] != "ok":
            issue("command_failed", **where, seq=seq, cmd_id=ack["cmd_id"],
                  cmd_seq=ack["cmd_seq"], result=ack["result"])
        commands.append({"seq": seq, "t_anchor_us": t_anchor, **ack})
    return {"afe_config": {name: by_afe.get(name, [])
                           for name, _, _, _ in AFES.values()},
            "commands": commands}


def _led_codes(registers):
    """LED codes of a configured MAX30101 register image (V0.2 section 12)."""
    return {name: int(registers[address], 16)
            for name, address in LED_REGISTERS.items()}


def _led_lock(session_id, version, afe_config, lock, after_change, issue):
    """Session ``ppg_led_lock``: where the locked LED codes (metadata, protocol 6.1)
    take effect in the MAX30101 states of 0xD2; None without a lock.

    The PC sends the locked codes at the start of every device session, since the
    firmware boots with its defaults (V0.2 section 13). States before the first
    locked one (boot defaults, calibration) are not reported. A configured chip
    state with other codes after it is ``ppg_led_lock_mismatch``; a session with
    no locked state at all, a V0.1 one included (no 0xD2), is
    ``ppg_led_lock_not_applied``, with ``after_session_change`` when the SESSION_ID
    changed within the raw stream (an MCU restart: the codes must be sent again).
    """
    if lock is None:
        return None
    where = {"session_id": session_id, "version": version}
    locked = {"red": lock["red"], "ir": lock["ir"], "green_led3": lock["green"],
              "green_led4": lock["green"]}
    applied, last = None, None
    states = [] if afe_config is None else [
        state for state in afe_config[AFES[2][0]]
        if state["source"] == "chip" and state["configured"]
    ]
    for state in states:
        last = _led_codes(state["registers"])
        if applied is None and last == locked:
            applied = {"seq": state["first_seq"], "t_anchor_us": state["t_anchor_us"],
                       "generation": state["generation"]}
        elif applied is not None and last != locked:
            issue("ppg_led_lock_mismatch", **where, seq=state["first_seq"],
                  generation=state["generation"], led_codes=last)
    if applied is None:
        issue("ppg_led_lock_not_applied", **where, after_session_change=after_change,
              last_led_codes=last)
    return {"applied": applied}


def _channel_holes(session_id, version, channels, config, metadata, issue):
    """Data channels with no trusted time for longer than
    ``channel_silence_tolerance_us``.

    ``channel_missing`` only sees a channel with no packet at all; a channel that
    stops (an AFE reset, say), starts late or pauses would pass. Trusted times are
    the anchors of accepted data packets that passed a comparison with another
    anchor of their chain (a lone packet after a re-anchor is never compared), and
    the device info heartbeat 0xD1, which keeps the session span going when the
    only data channel stops. A heartbeat is sent every DEVICE_INFO_PERIOD_US
    (V0.2 section 6) with its ordinal in FIRST_SAMPLE_INDEX, so ``anchor - ordinal
    * period`` is the same for all; the valid ones whose phases fit in one window
    of ``device_info_anchor_tolerance_us`` with at least one other count (the
    largest such group), the others are reported (``device_info_anchor_inconsistent``)
    and left out. The span runs from the first to the last trusted time; each data
    channel's trusted anchors, with the span's ends, must not leave a hole above
    the tolerance (``late_start``, ``gap``, ``ended_early``, or ``whole_span`` for
    a channel with packets but no trusted anchor). ``packets_inside`` counts the
    SEQ numbers of the channel inside the hole, between its first and last
    received SEQ: received packets and those lost after a SEQ;
    ``dropped_before_seq`` tells whether one of them, or the packet closing the
    hole, has bit 1. With neither, the channel sent nothing: ``channel_silent``.
    Otherwise it was alive but when is unknown, so it may still have been quiet
    for most of the hole: ``channel_timing_unknown``. All anchors share the MCU
    clock. Generator streams (metadata ``simulation`` set) give their channels
    different lengths on purpose, so they are not checked (None).
    """
    if metadata["simulation"] is not None:
        return None
    tolerance = config["channel_silence_tolerance_us"]
    timed = {}  # data channel -> [(seq, anchor)] of trusted packets, in SEQ order
    for channel_id, state in channels.items():
        if channel_id not in (EVENT_CHANNEL, DEVICE_INFO_CHANNEL, *CONTROL_CHANNELS):
            timed[channel_id] = [(seq, state["received"][seq].packet.t_anchor_us)
                                 for seq in sorted(state.get("verified", ()))]
    heartbeat = _heartbeat(session_id, version, channels.get(DEVICE_INFO_CHANNEL),
                           config, issue)
    times = [a for points in timed.values() for _, a in points] + heartbeat
    if not times:
        return []
    start, end = min(times), max(times)
    holes = []
    for channel_id, points in sorted(timed.items()):
        received = channels[channel_id]["received"]
        first_seq, last_seq = min(received), max(received)
        bounds = [(None, start), *points, (None, end)]
        for (s0, a), (s1, b) in zip(bounds, bounds[1:]):
            if b - a <= tolerance:
                continue
            if s0 is None:  # whole_span: packets, but no trusted anchor at all
                kind = "late_start" if s1 is not None else "whole_span"
            else:
                kind = "gap" if s1 is not None else "ended_early"
            inside = [seq for seq in sorted(received)
                      if (s0 is None or seq > s0) and (s1 is None or seq < s1)]
            closing = [] if s1 is None else [s1]
            low = first_seq if s0 is None else s0 + 1
            high = last_seq if s1 is None else s1 - 1
            entry = {
                "channel": channel_key(channel_id), "kind": kind, "from_us": a,
                "to_us": b, "packets_inside": max(0, high - low + 1),
                "dropped_before_seq": any(received[seq].packet.status & MCU_BUFFER_BIT
                                          for seq in inside + closing),
            }
            alive = entry["packets_inside"] or entry["dropped_before_seq"]
            issue("channel_timing_unknown" if alive else "channel_silent",
                  session_id=session_id, version=version, **entry)
            holes.append(entry)
    return holes


def _heartbeat(session_id, version, info, config, issue):
    """Trusted 0xD1 anchors (see _channel_holes), in SEQ order."""
    if info is None:
        return []
    valid = [seq for seq in sorted(info["received"])
             if info["rows"][seq].get("disposition") == "device_info"]
    phase = {seq: info["received"][seq].packet.t_anchor_us
             - info["received"][seq].packet.first_sample_index * DEVICE_INFO_PERIOD_US
             for seq in valid}
    reference, kept = _phase_window(phase, config["device_info_anchor_tolerance_us"])
    for seq in valid:
        if seq not in kept:
            issue("device_info_anchor_inconsistent", session_id=session_id,
                  version=version, channel=channel_key(DEVICE_INFO_CHANNEL), seq=seq,
                  deviation_us=str(phase[seq] - phase[reference]), reference_seq=reference)
    return [info["received"][seq].packet.t_anchor_us for seq in valid
            if seq in kept and len(kept) > 1]


def _session_device_info(session_id, version, identities, metadata, issue):
    """Session ``device_info``: distinct identities in SEQ order, with the checks
    of V0.2 section 6 (changed within the session, missing, metadata mismatch)."""
    distinct = []
    for seq, identity in identities:
        if not distinct or distinct[-1]["identity"] != identity:
            if distinct:
                issue("device_info_changed", session_id=session_id, seq=seq)
            distinct.append({"first_seq": seq, "identity": identity, "packets": 0})
        distinct[-1]["packets"] += 1
    if version >= WIRE_VERSION_V02 and not identities and (
        metadata["source_type"] == "DEVICE"
    ):
        issue("device_info_missing", session_id=session_id)
    declared = metadata["firmware_version"]
    if declared is not None and any(d["identity"]["app_version"] != declared
                                    for d in distinct):
        issue("firmware_metadata_mismatch", session_id=session_id,
              metadata_firmware_version=declared)
    if version < WIRE_VERSION_V02:
        return None
    return {"valid_packets": len(identities),
            "identities": [{**d["identity"], "first_seq": d["first_seq"],
                            "packets": d["packets"]} for d in distinct]}


def _index_pass(present, received, where, issue, version=WIRE_VERSION,
                untrusted=(), counted=False):
    """Schema step 4: FIRST_SAMPLE_INDEX continuity, cross-checked with STATUS.

    A packet with FS 0 is quarantined as ``fs_invalid`` later, one in
    ``untrusted`` by the caller; its header is not trusted, so it gets an index
    for its row but never becomes the reference. ``counted``: the index counts
    ticks (V0.2 section 11, 0xB1), so a forward jump of at least the number of
    missing packets is a gap of known length (``sample_gap_counted``) that keeps
    the chain.
    V0.1 (R2): bit 5 on either packet next to an index jump marks a re-anchor.
    V0.2 (section 5): bit 5 is only on the first packet after the gap; that
    packet always re-anchors, even with a continuous index, before any overlap
    or continuity check.
    """
    index, quarantine, jumps, previous = {}, {}, {}, None
    # STATUS of skipped FS-0 packets: their gap bits and a V0.2 re-anchor still
    # apply to the next trusted packet (its index is checked against the last
    # trusted packet before them).
    pending = 0
    for seq in present:
        packet = received[seq].packet
        if packet.fs_nominal_mhz == 0 or seq in untrusted:
            index[seq] = packet.first_sample_index if previous is None else _unwrap(
                packet.first_sample_index,
                index[previous] + len(received[previous].packet.data))
            if seq not in untrusted:
                pending |= packet.status
            continue
        own, pending = packet.status | pending, 0
        if previous is None:
            index[seq] = packet.first_sample_index
            previous = seq
            continue
        before = received[previous].packet
        expected = index[previous] + len(before.data)
        index[seq] = value = _unwrap(packet.first_sample_index, expected)
        absent, lost = seq - previous - 1, value - expected
        bits = own | before.status
        detail = {**where, "seq": seq, "expected_index": expected, "index": value}
        if version >= WIRE_VERSION_V02:
            reanchored = own & REANCHOR_BIT
        else:
            reanchored = lost != 0 and bits & REANCHOR_BIT
        if reanchored:
            issue("sample_index_reanchored", **detail)
            jumps[seq] = "reanchored"
        elif counted and lost >= absent:
            if lost > absent:
                issue("sample_gap_counted", **detail, absent_packets=absent,
                      lost_samples=lost)
                jumps[seq] = "counted_gap"
        elif lost < 0:
            issue("sample_index_overlap", **detail)
            quarantine[seq] = "index_overlap"
            continue
        elif lost < absent or (
            absent > 0 and lost > MAX_SAMPLE_COUNT * absent
            and not bits & KNOWN_GAP_BITS
        ):
            # Every absent packet carried 1 to MAX_SAMPLE_COUNT samples; more is
            # explained only by a known sample loss (bit 0 or 1).
            issue("sample_index_inconsistent", **detail, absent_packets=absent)
            jumps[seq] = "index_inconsistent"
        elif absent == 0 and lost > 0:
            explained = bits & KNOWN_GAP_BITS
            issue("sample_gap_status" if explained else "sample_gap_unexplained",
                  **detail, lost_samples=lost)
            jumps[seq] = "status_sample_loss" if explained else "unexplained_index_jump"
        previous = seq
    return index, quarantine, jumps


def _chains(present, received, quarantine, jumps, where, issue):
    """Split a channel into index/timing chains; return ``(chain_of, chains)``.

    A new chain starts at a re-anchor (an index jump with STATUS bit 5 on either
    side) or an FS change, so a sample index can repeat only across chains. Bit
    5 with a continuous index does not split the chain. A packet with FS 0 is
    quarantined and does not split its chain. ``chain_of`` maps every present
    SEQ to its chain id; ``chains`` lists the SEQs left for the timing check.
    """
    chain_of, chains, rate = {}, [], None
    for seq in present:
        fs = received[seq].packet.fs_nominal_mhz
        if seq not in quarantine and fs == 0:
            issue("fs_invalid", **where, seq=seq)
            quarantine[seq] = "fs_invalid"
        new = not chains or jumps.get(seq) == "reanchored"
        if seq not in quarantine:
            if rate is not None and fs != rate:
                issue("fs_changed", **where, seq=seq)
                new = True
            rate = fs
        if new:
            chains.append([])
        chain_of[seq] = len(chains) - 1
        if seq not in quarantine:
            chains[-1].append(seq)
    return chain_of, chains


def _timing_pass(chain, received, index, quarantine, tolerance, where, issue,
                 source=None):
    """Schema step 6 on one chain: T_ANCHOR_US increases and matches index/fs.

    ``tolerance`` is ``(samples, extra_us, rate_ppm)``: the fixed part is
    ``samples`` periods plus ``extra_us``. ``source`` names the V0.2 ECG anchor
    source in the issues (None elsewhere); for ``"samp"`` the checks that cannot
    tell a one-sample shift are also reported (``anchor_check_weak``).

    Each packet is compared with the last kept packet before it, so a single
    bad anchor is quarantined without moving the reference. The walk is done
    from both ends of the chain and the direction that quarantines fewer
    packets is kept (forward on a tie), so a bad first anchor costs one packet,
    not the chain. The true sample rate is only known within
    ``anchor_rate_tolerance_ppm`` (r) of the nominal rate, so the true period is
    in [T/(1+r), T/(1-r)] and the allowed time grows with the number of samples
    since the reference (a gap of missing packets).

    Returns the kept anchors when there are two or more: each was then compared
    with a kept one next to it. A lone anchor was compared with nothing.
    """
    if not chain:
        return set()
    # Microseconds per sample; FS_NOMINAL_MHZ is in millihertz.
    period = Fraction(10 ** 9, received[chain[0]].packet.fs_nominal_mhz)
    fixed = tolerance[0] * period + tolerance[1]
    rate = Fraction(tolerance[2], 10 ** 6)
    shortest, longest = period / (1 + rate), period / (1 - rate)
    points = [(seq, index[seq] + len(received[seq].packet.data) - 1,
               received[seq].packet.t_anchor_us) for seq in chain]

    def walk(order):
        flagged, reference = {}, None
        for seq, last, anchor in order:
            if reference is not None:
                steps = last - reference[1]
                elapsed = anchor - reference[2]
                deviation = elapsed - steps * period
                # Time elapsed in the direction of the index, over |steps| samples.
                along = elapsed if steps > 0 else -elapsed
                inside = (abs(steps) * shortest - fixed <= along
                          <= abs(steps) * longest + fixed)
                # Anchors must move the same way as the sample index.
                kind = ("not_increasing" if elapsed * steps <= 0
                        else "mismatch" if not inside else None)
                if kind:
                    flagged[seq] = (kind, deviation, reference[0])
                    continue
            reference = (seq, last, anchor)
        return flagged

    forward, backward = walk(points), walk(points[::-1])
    flagged = backward if len(backward) < len(forward) else forward
    named = {} if source is None else {"anchor_source": source}
    for seq in chain:
        if seq in flagged:
            kind, deviation, reference = flagged[seq]
            issue("timestamp_anomaly", **where, seq=seq, kind=kind,
                  deviation_us=str(deviation), reference_seq=reference, **named)
            quarantine[seq] = "timestamp_anomaly"
    kept = [point for point in points if point[0] not in flagged]
    if source == "samp":
        if len(points) == 1:
            issue("anchor_check_weak", **where, seq=points[0][0], reference_seq=None,
                  steps=None, **named)
        # Kept packets were each checked against the kept packet next to them. An
        # anchor one sample late comes at least (n + 1) * shortest - fixed after
        # the reference (fastest rate, anchor error up to the fixed part); the
        # check is weak when that fits under n * longest + fixed. One sample early
        # can only pass where one sample late already does.
        for (reference, before, _), (seq, last, _) in zip(kept, kept[1:]):
            steps = abs(last - before)
            if (steps + 1) * shortest - fixed <= steps * longest + fixed:
                issue("anchor_check_weak", **where, seq=seq, reference_seq=reference,
                      steps=steps, **named)
    return {seq for seq, _, _ in kept} if len(kept) > 1 else set()


def _phase_pass(chain, received, index, quarantine, window_us, where, issue):
    """Schema step 6 for one 0xB1 chain (V0.2 section 11.2).

    The phase ``T_ANCHOR_US - index * T`` is the readout delay after tick k plus
    the tick epoch. The ticks run on the same esp_timer as the anchors, so the
    phases of a whole chain must fit in one window of ``window_us``; a pairwise
    check would let the delay drift a little at every packet. The window that
    keeps the most packets wins (the earliest on a tie); the others are
    quarantined. A window below one period keeps anchors increasing. Returns the
    kept anchors when there are two or more (a lone one was compared with nothing).
    """
    if not chain:
        return set()
    period = Fraction(10 ** 9, received[chain[0]].packet.fs_nominal_mhz)
    phase = {seq: received[seq].packet.t_anchor_us - index[seq] * period
             for seq in chain}
    reference, kept = _phase_window(phase, window_us)
    for seq in chain:
        if seq not in kept:
            issue("timestamp_anomaly", **where, seq=seq, kind="phase",
                  deviation_us=str(phase[seq] - phase[reference]),
                  reference_seq=reference)
            quarantine[seq] = "timestamp_anomaly"
    return kept if len(kept) > 1 else set()


def _phase_window(phase, window_us):
    """The largest set of packets whose phases fit in one window (the earliest on
    a tie), and the packet of its smallest phase: ``(reference, kept)``."""
    if not phase:
        return None, set()
    order = sorted(phase, key=lambda seq: (phase[seq], seq))
    best, start = (0, 0), 0
    for end, seq in enumerate(order):
        while phase[seq] - phase[order[start]] > window_us:
            start += 1
        if end - start + 1 > best[1] - best[0]:
            best = (start, end + 1)
    return order[best[0]], set(order[best[0]:best[1]])


def _gaps(seqs, accepted, received, index, quarantine, conflicts, jumps):
    """Holes in the accepted sample stream; lost_samples is null after a re-anchor."""
    gaps = []
    for before, after in zip(accepted, accepted[1:]):
        expected = index[before] + len(received[before].packet.data)
        reasons = set()
        between = seqs[bisect_right(seqs, before):bisect_left(seqs, after)]
        if len(between) < after - before - 1:
            reasons.add("missing")
        for seq in between:
            reasons.add(quarantine.get(seq)
                        or ("conflicting_duplicate" if seq in conflicts else "missing"))
        for seq in seqs[bisect_right(seqs, before):bisect_right(seqs, after)]:
            if seq in jumps:
                reasons.add(jumps[seq])
        if index[after] != expected or reasons:
            reanchored = "reanchored" in reasons
            gaps.append({
                "after_seq": before, "before_seq": after, "index_from": expected,
                "index_to": index[after], "reasons": sorted(reasons),
                "lost_samples": None if reanchored else index[after] - expected,
            })
    return gaps


def _channel_offset(session_id, firsts, config, metadata, issue):
    """Offset of each channel's implied index-0 epoch from ECG; SYNTHETIC only.

    It is identifiable only because the generator declares that all channels
    share one epoch for sample index 0. On a device the AFEs have different,
    unmeasured latencies, so this is not reported. It is not PAT.
    """
    simulation = metadata["simulation"]
    if metadata["source_type"] != "SYNTHETIC" or not (
        simulation and simulation["common_index_epoch"]
    ):
        return {"offset_vs_ecg_us": None,
                "reason": "needs a SYNTHETIC stream with a known common epoch; "
                          "device offset is measured by sync_10min_test_plan.md"}
    if ECG_CHANNEL not in firsts:
        return {"offset_vs_ecg_us": None, "reason": "no accepted ECG packet"}

    def epoch(channel_id):
        last, packet = firsts[channel_id]
        return packet.t_anchor_us - Fraction(last * 10 ** 9, packet.fs_nominal_mhz)

    offsets = {}
    # Only accepted packets reach here, and FS 0 is quarantined (fs_invalid).
    # The 0xB1 anchor is a readout time, not a sample time (V0.2 section 11.2).
    for channel_id in sorted(firsts):
        if channel_id in (ECG_CHANNEL, TEMP_CHANNEL):
            continue
        offset = epoch(channel_id) - epoch(ECG_CHANNEL)
        offsets[channel_key(channel_id)] = str(offset)
        if abs(offset) > config["channel_offset_tolerance_us"]:
            issue("channel_offset", session_id=session_id,
                  channel=channel_key(channel_id), offset_us=str(offset))
    return {"offset_vs_ecg_us": offsets, "reason": None}


def _csv(columns, rows):
    lines = [",".join(columns)]
    for row in rows:
        lines.append(",".join("" if value is None else str(value) for value in row))
    return ("\n".join(lines) + "\n").encode("utf-8")


def render_outputs(result, rows, samples):
    """Deterministic bytes of decode.json, packets.csv and samples.csv."""
    # (session, channel, chain, sample index): an index may repeat across chains.
    ordered = sorted(samples, key=lambda s: (s[0], s[6], s[1], s[2], s[4]))
    return {
        "decode.json": json_bytes(result),
        "packets.csv": _csv(PACKET_COLUMNS,
                            ([row[name] for name in PACKET_COLUMNS] for row in rows)),
        "samples.csv": _csv(SAMPLE_COLUMNS, ordered),
    }
