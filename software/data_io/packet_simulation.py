"""PC-only SYNTHETIC packet interface, not a hardware/firmware wire schema."""

import copy
import hashlib
import json
import random
from collections import Counter
from fractions import Fraction

VERSION = "synthetic-packet-v2"
CASES = ("valid", "missing", "duplicate", "reordered", "timestamp", "offset")
CHANNELS = ("ECG", "PPG")
MAX_COUNTER = 2 ** 63 - 1
QUANTIZATION_PAIR_US = 1


def json_bytes(value):
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False,
                       separators=(",", ":")) + "\n").encode("utf-8")


def _integer(value, name, minimum=0, maximum=2 ** 63 - 1):
    if isinstance(value, bool) or not isinstance(value, int) or not minimum <= value <= maximum:
        raise ValueError(f"{name} must be an integer in [{minimum}, {maximum}]")


def _text(value, name):
    if not isinstance(value, str) or not value or value.strip() != value:
        raise ValueError(f"{name} must be nonempty text without edge spaces")


def validate_config(config):
    fields = {
        "schema_version", "source_type", "session_id", "clock_id", "seed",
        "start_timestamp_us", "sequence_start", "packet_count", "channels",
        "fault_channel", "fault_index", "offset_us", "timestamp_tolerance_us",
    }
    if not isinstance(config, dict) or set(config) != fields:
        raise ValueError("Config has missing or unsupported fields")
    if config["schema_version"] != VERSION or config["source_type"] != "SYNTHETIC":
        raise ValueError("Only the SYNTHETIC interface is supported")
    for name in ("session_id", "clock_id"):
        _text(config[name], name)
    for name in ("seed", "start_timestamp_us", "sequence_start"):
        _integer(config[name], name)
    _integer(config["packet_count"], "packet_count", 3, 10000)
    _integer(config["fault_index"], "fault_index", 1, config["packet_count"] - 2)
    _integer(config["offset_us"], "offset_us", 1, 10 ** 9)
    _integer(config["timestamp_tolerance_us"], "timestamp_tolerance_us", 0, 1000)
    if config["offset_us"] <= config["timestamp_tolerance_us"] + QUANTIZATION_PAIR_US:
        raise ValueError("Injected offset must exceed tolerance plus quantization bound")
    if config["fault_channel"] not in CHANNELS:
        raise ValueError("Unknown fault channel")
    channels = config["channels"]
    if not isinstance(channels, dict) or set(channels) != set(CHANNELS):
        raise ValueError("Exactly ECG and PPG are required")
    total_samples = 0
    for channel in CHANNELS:
        spec = channels[channel]
        if not isinstance(spec, dict) or set(spec) != {"fs_hz", "sample_count"}:
            raise ValueError("Channel needs fs_hz and sample_count")
        _integer(spec["fs_hz"], "fs_hz", 1, 100000)
        _integer(spec["sample_count"], "sample_count", 1, 4096)
        total_samples += config["packet_count"] * spec["sample_count"]
    if total_samples > 1000000:
        raise ValueError("Simulation exceeds one million samples")
    _integer(config["sequence_start"] + config["packet_count"] - 1,
             "sequence_end", maximum=MAX_COUNTER)
    for channel in CHANNELS:
        final_timestamp = round(config["start_timestamp_us"] +
                                (config["packet_count"] - 1) * _duration(config, channel))
        if channel == config["fault_channel"]:
            final_timestamp += config["offset_us"]
        _integer(final_timestamp, "final_timestamp_us", maximum=MAX_COUNTER)
    return True


def _duration(config, channel):
    spec = config["channels"][channel]
    return Fraction(spec["sample_count"] * 1000000, spec["fs_hz"])


def generate_packets(config, case="valid"):
    validate_config(config)
    if case not in CASES:
        raise ValueError("Unknown simulation case")
    rng = random.Random(config["seed"])
    by_channel = {}
    for channel in CHANNELS:
        spec = config["channels"][channel]
        packets = []
        for index in range(config["packet_count"]):
            timestamp = round(config["start_timestamp_us"] + index * _duration(config, channel))
            if channel == config["fault_channel"]:
                if case == "offset" or (case == "timestamp" and index == config["fault_index"]):
                    timestamp += config["offset_us"]
            packets.append({
                "schema_version": VERSION, "source_type": "SYNTHETIC",
                "session_id": config["session_id"], "clock_id": config["clock_id"],
                "channel": channel, "sequence": config["sequence_start"] + index,
                "timestamp_us": timestamp, "timestamp_kind": "first_sample",
                "timestamp_unit": "us", "fs_hz": spec["fs_hz"],
                "sample_count": spec["sample_count"], "sample_unit": "synthetic_count",
                "samples": [rng.randint(-1000, 1000) for _ in range(spec["sample_count"])],
            })
        if channel == config["fault_channel"]:
            index = config["fault_index"]
            if case == "missing":
                del packets[index]
            elif case == "duplicate":
                packets.insert(index + 1, copy.deepcopy(packets[index]))
            elif case == "reordered":
                packets[index], packets[index + 1] = packets[index + 1], packets[index]
        by_channel[channel] = packets
    # Arrival order is transport order, not acquisition time. It has no clock meaning.
    result = []
    for index in range(max(map(len, by_channel.values()))):
        for channel in CHANNELS:
            if index < len(by_channel[channel]):
                result.append(by_channel[channel][index])
    return result


def _validate_packet(packet, config):
    fields = {
        "schema_version", "source_type", "session_id", "clock_id", "channel",
        "sequence", "timestamp_us", "timestamp_kind", "timestamp_unit", "fs_hz",
        "sample_count", "sample_unit", "samples",
    }
    if not isinstance(packet, dict) or set(packet) != fields:
        raise ValueError("Packet has missing or unsupported fields")
    for name in ("schema_version", "source_type", "session_id", "clock_id"):
        if packet[name] != config[name]:
            raise ValueError(f"Packet {name} differs from config")
    if packet["channel"] not in CHANNELS:
        raise ValueError("Unknown packet channel")
    if (packet["timestamp_kind"], packet["timestamp_unit"], packet["sample_unit"]) != (
        "first_sample", "us", "synthetic_count"
    ):
        raise ValueError("Unsupported timestamp/sample convention")
    spec = config["channels"][packet["channel"]]
    for field in ("fs_hz", "sample_count"):
        _integer(packet[field], field, 1)
        if packet[field] != spec[field]:
            raise ValueError(f"Packet {field} differs from config")
    start = config["sequence_start"]
    _integer(packet["sequence"], "sequence", start, start + config["packet_count"] - 1)
    _integer(packet["timestamp_us"], "timestamp_us")
    if not isinstance(packet["samples"], list) or len(packet["samples"]) != spec["sample_count"]:
        raise ValueError("sample_count does not match samples")
    for sample in packet["samples"]:
        _integer(sample, "sample", -(2 ** 31), 2 ** 31 - 1)


def replay_packets(packets, config):
    """Offline replay: deduplicate, sort, quarantine bad timing, keep explicit gaps.

    Gap detection uses the configured expected sequence extent, including edges.
    Clock offset is only identifiable here because simulated sequence starts
    share a known epoch; this is not a general sensor synchronization estimator.
    """
    validate_config(config)
    if not isinstance(packets, list) or len(packets) > 4 * config["packet_count"]:
        raise ValueError("Packets must be a bounded list")
    issues, streams, max_seen, conflicts = [], {c: {} for c in CHANNELS}, {}, set()

    def issue(code, channel, sequence=None):
        issues.append({"code": code, "channel": channel, "sequence": sequence})

    for packet in packets:
        _validate_packet(packet, config)
        channel, sequence = packet["channel"], packet["sequence"]
        stream = streams[channel]
        if sequence in stream:
            if packet == stream[sequence]:
                issue("duplicate", channel, sequence)
            else:
                issue("conflicting_duplicate", channel, sequence)
                conflicts.add((channel, sequence))
            continue
        if channel in max_seen and sequence < max_seen[channel]:
            issue("out_of_order", channel, sequence)
        max_seen[channel] = max(sequence, max_seen.get(channel, sequence))
        stream[sequence] = copy.deepcopy(packet)
    start = config["sequence_start"]
    anchors, output = {}, {}
    for channel in CHANNELS:
        stream = streams[channel]
        duration = _duration(config, channel)
        first = next((s for s in sorted(stream) if (channel, s) not in conflicts), None)
        if first is not None:
            anchors[channel] = Fraction(stream[first]["timestamp_us"]) - (first - start) * duration
        gap_rows, samples, accepted = [], [], 0
        for sequence in range(start, start + config["packet_count"]):
            packet = stream.get(sequence)
            reason = None
            if packet is None:
                reason = "missing"
                issue(reason, channel, sequence)
            elif (channel, sequence) in conflicts:
                reason = "conflicting_duplicate"
            else:
                expected = anchors[channel] + (sequence - start) * duration
                # Anchor and packet are independently rounded (each <= 0.5 us).
                if abs(Fraction(packet["timestamp_us"]) - expected) > (
                    config["timestamp_tolerance_us"] + QUANTIZATION_PAIR_US
                ):
                    reason = "timestamp_anomaly"
                    issue(reason, channel, sequence)
            if reason:
                epoch = anchors.get(channel, Fraction(config["start_timestamp_us"]))
                begin = epoch + (sequence - start) * duration
                gap_rows.append({
                    "sequence": sequence, "reason": reason,
                    "nominal_start_us": str(begin), "nominal_end_us": str(begin + duration),
                    "sample_count": config["channels"][channel]["sample_count"],
                })
                continue
            accepted += 1
            for index, value in enumerate(packet["samples"]):
                samples.append({
                    "sequence": sequence, "sample_index": index, "value": value,
                    "timestamp_us": str(Fraction(packet["timestamp_us"]) +
                                        Fraction(index * 1000000, packet["fs_hz"])),
                })
        output[channel] = {"accepted_packets": accepted, "samples": samples, "gaps": gap_rows}
    offset = None
    if set(anchors) == set(CHANNELS):
        offset = anchors["PPG"] - anchors["ECG"]
        if abs(offset) > config["timestamp_tolerance_us"] + QUANTIZATION_PAIR_US:
            issue("channel_offset", "ECG_PPG")
    return {
        "schema_version": VERSION, "source_type": "SYNTHETIC",
        "session_id": config["session_id"], "clock_id": config["clock_id"],
        "issues": issues, "issue_counts": dict(sorted(Counter(i["code"] for i in issues).items())),
        "offset_ppg_minus_ecg_us": str(offset) if offset is not None else None,
        "time_encoding": "rational-string-us", "channels": output,
        "limitations": [
            "SIMULATION ONLY: no real sensor synchronization or physiological inference",
            "First available nonconflicting packet anchors each channel; corrupted anchors are ambiguous",
            "No clock-drift correction, live buffering, sequence wrap/reset or hardware binary decoding",
            "Timelines are preserved, never shifted to align ECG and PPG",
        ],
    }


def packet_sha256(packets):
    return hashlib.sha256(json_bytes(packets)).hexdigest()