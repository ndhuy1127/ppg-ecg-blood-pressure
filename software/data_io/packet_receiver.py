"""Receiver checks of Packet Schema V0.1 section 12, per session and channel.

Pure code: the input is decoded packets in arrival order plus the decoder log,
the output is JSON/CSV bytes. Nothing here reads a port or file or prints.
Gaps are marked, never interpolated or bridged; ECG and PPG are never joined
by sample index and no channel is shifted in time. PC receive time (``t_rx``)
is not an input: the runner logs it in a separate file and it is never used as
a sample time. Tolerances are configuration values that have not been
verified on hardware.
"""

import json
from bisect import bisect_left, bisect_right
from collections import Counter
from fractions import Fraction

from software.data_io.packet_wire import (
    CHANNELS, ECG_CHANNEL, EVENT_CHANNEL, MAX_SAMPLE_COUNT, PPG_CHANNELS,
    STATUS_BITS, STATUS_RESERVED_MASK, WIRE_VERSION,
)

LOGGER_VERSION = "packet-logger-v0"
PACKET_SCHEMA = "packet-v0.1"
METADATA_VERSION = "packet-session-metadata-v0"
SOURCE_TYPES = ("SYNTHETIC", "DEVICE")
UINT32 = 1 << 32
# Provisional rules, pending Duc Anh (docs/protocol/packet_logger.md): a
# FIRST_SAMPLE_INDEX jump of known length is explained by STATUS bit 0 or 1, a
# re-anchor of unknown length by bit 5; the bit may be on either packet next to
# the jump. Event packets (0xC1) skip the index and anchor checks (steps 4, 6).
KNOWN_GAP_BITS = (1 << 0) | (1 << 1)
REANCHOR_BIT = 1 << 5
DATA_LIMITS = {ECG_CHANNEL: 1 << 24, **{channel: 1 << 18 for channel in PPG_CHANNELS}}
EVENT_CODES = (1, 2, 3, 4)
CONFIG_FIELDS = {
    "schema_version", "packet_schema", "status", "wire_versions",
    "anchor_tolerance_samples", "anchor_tolerance_extra_us",
    "anchor_rate_tolerance_ppm", "channel_offset_tolerance_us", "read_chunk_bytes",
}
TEXT_FIELDS = (
    "clock_id", "firmware_version", "firmware_commit", "device_id", "operator",
    "electrode_type", "electrode_placement",
)
CHANNEL_FIELDS = (
    "sensor", "fs_nominal_mhz", "latency_l_us", "latency_source",
    "unit_conversion", "afe_config",
)
SIMULATION_FIELDS = {"generator", "case", "config_sha256", "common_index_epoch"}
PACKET_COLUMNS = (
    "arrival", "stream_offset", "session_id", "channel_id", "seq", "seq_ext",
    "first_sample_index", "sample_index_ext", "chain_id", "t_anchor_us",
    "t_first_us", "fs_nominal_mhz", "sample_count", "status", "disposition",
)
SAMPLE_COLUMNS = (
    "session_id", "channel_id", "chain_id", "seq_ext", "sample_index_ext", "value",
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
    "anchor_rate_tolerance_ppm of FS_NOMINAL_MHZ; it is not measured",
    "A false SYNC followed by a passing CRC (about 1 in 65536) is not excluded",
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
    if not isinstance(config, dict) or set(config) != CONFIG_FIELDS:
        raise ValueError("Logger config has missing or unsupported fields")
    if (config["schema_version"], config["packet_schema"]) != (
        LOGGER_VERSION, PACKET_SCHEMA
    ):
        raise ValueError("Unsupported logger config or packet schema version")
    if not isinstance(config["status"], str) or not config["status"]:
        raise ValueError("status must be nonempty text")
    if config["wire_versions"] != [WIRE_VERSION]:
        raise ValueError("Only wire VERSION 0x01 (schema V0.1) is supported")
    _integer(config["anchor_tolerance_samples"], "anchor_tolerance_samples", 0, 32)
    _integer(config["anchor_tolerance_extra_us"], "anchor_tolerance_extra_us", 0,
             10 ** 6)
    _integer(config["anchor_rate_tolerance_ppm"], "anchor_rate_tolerance_ppm", 0,
             10 ** 5)
    _integer(config["channel_offset_tolerance_us"], "channel_offset_tolerance_us",
             0, 10 ** 6)
    _integer(config["read_chunk_bytes"], "read_chunk_bytes", 1, 1 << 20)
    return True


def validate_metadata(metadata):
    """Session metadata (schema section 11): unknown values are null with a reason."""
    fields = {"schema_version", "source_type", *TEXT_FIELDS, "channels",
              "simulation", "null_reasons"}
    if not isinstance(metadata, dict) or set(metadata) != fields:
        raise ValueError("Session metadata has missing or unsupported fields")
    if metadata["schema_version"] != METADATA_VERSION:
        raise ValueError("Unsupported session metadata version")
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
        if not isinstance(spec, dict) or set(spec) != set(CHANNEL_FIELDS):
            raise ValueError(f"Channel {key} metadata has missing or extra fields")
        for name in CHANNEL_FIELDS:
            value = spec[name]
            if value is None:
                nulls.add(f"channels.{key}.{name}")
            elif name in ("fs_nominal_mhz", "latency_l_us"):
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
    reasons = metadata["null_reasons"]
    if not isinstance(reasons, dict) or set(reasons) != nulls or not all(
        isinstance(text, str) and text.strip() for text in reasons.values()
    ):
        raise ValueError("null_reasons must give a reason for exactly the null fields")
    return True


def _unwrap(value, reference):
    """Extend a uint32 counter to the integer congruent mod 2**32 nearest reference."""
    half = UINT32 // 2
    return reference + (value - reference + half) % UINT32 - half


def _status_counts(packets):
    counts = Counter()
    for packet in packets:
        for bit, name in STATUS_BITS.items():
            if packet.status >> bit & 1:
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

    rows, sessions, previous = [], {}, None
    for arrival, item in enumerate(decoded):
        packet = item.packet
        if previous is not None and packet.session_id != previous:
            issue("session_change", offset=item.offset, session_id=packet.session_id,
                  previous_session_id=previous)
        previous = packet.session_id
        state = sessions.setdefault(packet.session_id, {}).setdefault(
            packet.channel_id, {"received": {}, "rows": {}, "conflicts": set(),
                                "max": None},
        )
        seq = packet.seq if state["max"] is None else _unwrap(packet.seq, state["max"])
        row = {
            "arrival": arrival, "stream_offset": item.offset,
            "session_id": packet.session_id,
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
    for session_id, channels in sessions.items():
        summaries, events, firsts = {}, [], {}
        for channel_id in sorted(channels):
            summary, channel_events, channel_samples, first = _check_channel(
                session_id, channel_id, channels[channel_id], config, metadata, issue,
            )
            summaries[channel_key(channel_id)] = summary
            events += channel_events
            samples += channel_samples
            if first is not None:
                firsts[channel_id] = first
        result_sessions.append({
            "session_id": session_id, "channels": summaries, "events": events,
            "channel_offset": _channel_offset(session_id, firsts, config, metadata,
                                              issue),
        })
    result = {
        "logger_version": LOGGER_VERSION, "packet_schema": PACKET_SCHEMA,
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


def _check_channel(session_id, channel_id, state, config, metadata, issue):
    received, conflicts, rows = state["received"], state["conflicts"], state["rows"]
    key = channel_key(channel_id)
    where = {"session_id": session_id, "channel": key}
    seqs = sorted(received)
    missing = 0
    for before, after in zip(seqs, seqs[1:]):
        if after - before > 1:
            missing += after - before - 1
            issue("missing_packets", **where, after_seq=before,
                  count=after - before - 1)
    for seq in seqs:
        packet = received[seq].packet
        if packet.status & STATUS_RESERVED_MASK:
            issue("status_reserved_bits", **where, seq=seq, status=packet.status)
        if seq in conflicts:
            rows[seq]["disposition"] = "conflicting_duplicate"
    present = [seq for seq in seqs if seq not in conflicts]
    spec = metadata["channels"].get(key)
    if spec is None:
        issue("channel_without_metadata", **where)
    summary = {
        "name": CHANNELS[channel_id], "packets_received": len(seqs),
        "conflicting_duplicates": len(conflicts), "missing_packets": missing,
        "first_seq": seqs[0], "last_seq": seqs[-1],
        "status_bit_counts": _status_counts(received[s].packet for s in seqs),
        "fs_nominal_mhz": sorted({received[s].packet.fs_nominal_mhz for s in seqs}),
    }
    if channel_id == EVENT_CHANNEL:
        events = []
        for seq in present:
            packet = received[seq].packet
            rows[seq]["disposition"] = "event"
            if len(packet.data) != 1:
                issue("event_sample_count", **where, seq=seq)
            elif packet.data[0] not in EVENT_CODES:
                issue("unknown_event_code", **where, seq=seq,
                      event_code=packet.data[0])
            events.append({"session_id": session_id, "seq_ext": seq,
                           "t_anchor_us": packet.t_anchor_us,
                           "data": list(packet.data)})
        summary["events"] = len(events)
        return summary, events, [], None

    if spec is not None and spec["fs_nominal_mhz"] is not None and (
        summary["fs_nominal_mhz"] != [spec["fs_nominal_mhz"]]
    ):
        issue("fs_metadata_mismatch", **where)
    index, quarantine, jumps = _index_pass(present, received, where, issue)
    chain_of, chains = _chains(present, received, quarantine, jumps, where, issue)
    for chain in chains:
        _timing_pass(chain, received, index, quarantine, config, where, issue)
    accepted = [seq for seq in present if seq not in quarantine]
    gaps = _gaps(seqs, accepted, received, index, quarantine, conflicts, jumps)
    samples = []
    limit = DATA_LIMITS[channel_id]
    for seq in present:
        rows[seq]["sample_index_ext"] = index[seq]
        rows[seq]["chain_id"] = chain_of[seq]
        rows[seq]["disposition"] = quarantine.get(seq, "accepted")
    for seq in accepted:
        packet = received[seq].packet
        if any(not 0 <= value < limit for value in packet.data):
            issue("data_out_of_range", **where, seq=seq)
        samples += [(session_id, key, chain_of[seq], seq, index[seq] + i, value)
                    for i, value in enumerate(packet.data)]
    summary.update({
        "packets_accepted": len(accepted),
        "packets_quarantined": dict(sorted(Counter(quarantine.values()).items())),
        "chains": len(chains),
        "first_sample_index": index[accepted[0]] if accepted else None,
        "samples_accepted": len(samples), "gaps": gaps,
    })
    first = None
    if accepted:
        packet = received[accepted[0]].packet
        first = (index[accepted[0]] + len(packet.data) - 1, packet)
    return summary, [], samples, first


def _index_pass(present, received, where, issue):
    """Schema step 4: FIRST_SAMPLE_INDEX continuity, cross-checked with STATUS."""
    index, quarantine, jumps, previous = {}, {}, {}, None
    for seq in present:
        packet = received[seq].packet
        if previous is None:
            index[seq] = packet.first_sample_index
            previous = seq
            continue
        before = received[previous].packet
        expected = index[previous] + len(before.data)
        index[seq] = value = _unwrap(packet.first_sample_index, expected)
        absent, lost = seq - previous - 1, value - expected
        bits = packet.status | before.status
        detail = {**where, "seq": seq, "expected_index": expected, "index": value}
        if lost != 0 and bits & REANCHOR_BIT:
            issue("sample_index_reanchored", **detail)
            jumps[seq] = "reanchored"
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

    A new chain starts at a re-anchor (STATUS bit 5) or an FS change, so a
    sample index can repeat only across chains. A packet with FS 0 is
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


def _timing_pass(chain, received, index, quarantine, config, where, issue):
    """Schema step 6 on one chain: T_ANCHOR_US increases and matches index/fs.

    Each packet is compared with the last kept packet before it, so a single
    bad anchor is quarantined without moving the reference. The walk is done
    from both ends of the chain and the direction that quarantines fewer
    packets is kept (forward on a tie), so a bad first anchor costs one packet,
    not the chain. The true sample rate is only known within
    ``anchor_rate_tolerance_ppm``, so the tolerance grows with the number of
    samples since the reference (a gap of missing packets).
    """
    if not chain:
        return
    # Microseconds per sample; FS_NOMINAL_MHZ is in millihertz.
    period = Fraction(10 ** 9, received[chain[0]].packet.fs_nominal_mhz)
    fixed = (config["anchor_tolerance_samples"] * period
             + config["anchor_tolerance_extra_us"])
    per_sample = Fraction(config["anchor_rate_tolerance_ppm"], 10 ** 6) * period
    points = [(seq, index[seq] + len(received[seq].packet.data) - 1,
               received[seq].packet.t_anchor_us) for seq in chain]

    def walk(order):
        flagged, reference = {}, None
        for seq, last, anchor in order:
            if reference is not None:
                steps = last - reference[1]
                deviation = anchor - reference[2] - steps * period
                # Anchors must move the same way as the sample index.
                kind = ("not_increasing" if (anchor - reference[2]) * steps <= 0
                        else "mismatch"
                        if abs(deviation) > fixed + per_sample * abs(steps)
                        else None)
                if kind:
                    flagged[seq] = (kind, deviation, reference[0])
                    continue
            reference = (seq, last, anchor)
        return flagged

    forward, backward = walk(points), walk(points[::-1])
    flagged = backward if len(backward) < len(forward) else forward
    for seq in chain:
        if seq in flagged:
            kind, deviation, reference = flagged[seq]
            issue("timestamp_anomaly", **where, seq=seq, kind=kind,
                  deviation_us=str(deviation), reference_seq=reference)
            quarantine[seq] = "timestamp_anomaly"


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
    for channel_id in sorted(firsts):
        if channel_id == ECG_CHANNEL:
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
    ordered = sorted(samples, key=lambda s: (s[0], s[1], s[2], s[4]))
    return {
        "decode.json": json_bytes(result),
        "packets.csv": _csv(PACKET_COLUMNS,
                            ([row[name] for name in PACKET_COLUMNS] for row in rows)),
        "samples.csv": _csv(SAMPLE_COLUMNS, ordered),
    }
