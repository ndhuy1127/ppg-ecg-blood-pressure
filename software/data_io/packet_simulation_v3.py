"""SYNTHETIC byte streams in the Packet Schema V0.1 layout (``synthetic-packet-v3``).

Pure code: returns bytes and metadata, writes nothing. It lets the PC logger be
tested before firmware exists. Sample rates, packet sizes, anchor delay/jitter
and fault magnitudes are simulation parameters, not hardware decisions (schema
section 15 is still open). Payloads are reproducible random integers in the
schema value ranges, not physiological waveforms. ``synthetic-packet-v2``
(JSON interface, ``packet_simulation.py``) is unchanged and still supported.
"""

import random
from dataclasses import replace
from fractions import Fraction

from software.data_io.packet_wire import (
    CHANNELS, ECG_CHANNEL, EVENT_CHANNEL, PPG_CHANNELS, STATUS_RESERVED_MASK,
    WIRE_VERSION, Packet, encode_packet,
)

VERSION = "synthetic-packet-v3"
CASES = (
    "valid", "missing", "duplicate", "reordered", "timestamp", "timestamp_first",
    "offset", "crc", "byte_loss", "index_jump", "reanchor", "version",
    "session_restart",
)
CONFIG_FIELDS = {
    "schema_version", "source_type", "wire_version", "seed", "session_id",
    "restart_session_id", "epoch_us", "anchor_delay_us", "anchor_jitter_us",
    "seq_start", "index_start", "packet_count", "status", "channels", "events",
    "fault_channel", "fault_index", "time_fault_us", "index_jump_samples",
    "reanchor_jump_samples", "byte_loss_count", "unsupported_version",
}
DATA_CHANNELS = (ECG_CHANNEL, *PPG_CHANNELS)
ORDER = (*DATA_CHANNELS, EVENT_CHANNEL)
UINT16, UINT32 = (1 << 16) - 1, (1 << 32) - 1


def _key(channel_id):
    return f"0x{channel_id:02X}"


def _channel_id(key):
    ids = {_key(channel): channel for channel in CHANNELS}
    if key not in ids:
        raise ValueError(f"Unknown channel key {key!r}")
    return ids[key]


def _integer(value, name, minimum=0, maximum=None):
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum or (
        maximum is not None and value > maximum
    ):
        raise ValueError(f"{name} must be an integer in [{minimum}, {maximum}]")


def validate_config(config):
    if not isinstance(config, dict) or set(config) != CONFIG_FIELDS:
        raise ValueError("Config has missing or unsupported fields")
    if (config["schema_version"], config["source_type"]) != (VERSION, "SYNTHETIC"):
        raise ValueError("Only the synthetic-packet-v3 SYNTHETIC config is supported")
    if config["wire_version"] != WIRE_VERSION:
        raise ValueError("wire_version must be 1 (Packet Schema V0.1)")
    for name in ("seed", "epoch_us", "anchor_delay_us", "anchor_jitter_us"):
        _integer(config[name], name, 0, 10 ** 12)
    for name in ("session_id", "restart_session_id", "seq_start", "index_start"):
        _integer(config[name], name, 0, UINT32)
    if config["session_id"] == config["restart_session_id"]:
        raise ValueError("restart_session_id must differ from session_id")
    _integer(config["packet_count"], "packet_count", 3, 10000)
    _integer(config["status"], "status", 0, UINT16)
    if config["status"] & STATUS_RESERVED_MASK:
        raise ValueError("STATUS reserved bits 7..15 must be 0")
    channels = config["channels"]
    if not isinstance(channels, dict) or _key(ECG_CHANNEL) not in channels:
        raise ValueError("channels must include 0xE1")
    ppg = []
    for key, spec in channels.items():
        if _channel_id(key) not in DATA_CHANNELS:
            raise ValueError("channels holds data channels only; events are separate")
        if not isinstance(spec, dict) or (
            set(spec) != {"fs_nominal_mhz", "sample_count"}
        ):
            raise ValueError("Channel needs fs_nominal_mhz and sample_count")
        _integer(spec["fs_nominal_mhz"], "fs_nominal_mhz", 1, UINT32)
        _integer(spec["sample_count"], "sample_count", 1, 32)
        if _channel_id(key) in PPG_CHANNELS:
            ppg.append((spec["fs_nominal_mhz"], spec["sample_count"]))
    if len(set(ppg)) > 1:
        raise ValueError("PPG slots come from one FIFO read: same fs and sample_count")
    if not isinstance(config["events"], list):
        raise ValueError("events must be a list")
    previous = -1
    for event in config["events"]:
        if not isinstance(event, dict) or set(event) != {"code", "time_us"}:
            raise ValueError("Each event needs code and time_us")
        _integer(event["code"], "event code", 0, 2 ** 31 - 1)
        _integer(event["time_us"], "event time_us", previous + 1, 2 ** 63)
        previous = event["time_us"]
    if config["fault_channel"] not in channels:
        raise ValueError("fault_channel must be a configured data channel")
    _integer(config["fault_index"], "fault_index", 1, config["packet_count"] - 2)
    # A time fault inside the jitter band could not be told apart from jitter.
    _integer(config["time_fault_us"], "time_fault_us",
             config["anchor_jitter_us"] + 2, 10 ** 9)
    _integer(config["index_jump_samples"], "index_jump_samples", 1, 10 ** 6)
    _integer(config["reanchor_jump_samples"], "reanchor_jump_samples", 1, 10 ** 6)
    data_bytes = 4 * channels[config["fault_channel"]]["sample_count"]
    _integer(config["byte_loss_count"], "byte_loss_count", 1, data_bytes)
    _integer(config["unsupported_version"], "unsupported_version", 0, 255)
    if config["unsupported_version"] == WIRE_VERSION:
        raise ValueError("unsupported_version must differ from 1")
    return True


def _payload(rng, channel_id, count):
    if channel_id == ECG_CHANNEL:
        # 18-bit two's complement sample left-aligned in a 24-bit word, ETAG/PTAG 0.
        return tuple((rng.randint(-(1 << 17), (1 << 17) - 1) & 0x3FFFF) << 6
                     for _ in range(count))
    return tuple(rng.randint(0, (1 << 18) - 1) for _ in range(count))


def _session(config, rng, case, session_id, packet_count, with_events):
    """Return ``(sort_key, channel_id, ordinal, Packet)`` rows of one session."""
    fault = _channel_id(config["fault_channel"])
    rows = []
    jitter = {}
    for key in sorted(config["channels"], key=lambda k: ORDER.index(_channel_id(k))):
        channel_id = _channel_id(key)
        spec = config["channels"][key]
        fs, count = spec["fs_nominal_mhz"], spec["sample_count"]
        period = Fraction(10 ** 9, fs)  # microseconds per sample
        group = "PPG" if channel_id in PPG_CHANNELS else key
        for ordinal in range(packet_count):
            first = config["index_start"] + ordinal * count
            status = config["status"]
            if channel_id == fault and ordinal > config["fault_index"]:
                if case == "index_jump":
                    first += config["index_jump_samples"]
                elif case == "reanchor":
                    first += config["reanchor_jump_samples"]
            if channel_id == fault and case == "index_jump" and (
                ordinal == config["fault_index"]
            ):
                status |= 1 << 0
            if channel_id == fault and case == "reanchor" and (
                ordinal == config["fault_index"] + 1
            ):
                status |= (1 << 0) | (1 << 5)
            # PPG slots of one read share the anchor, hence one jitter draw.
            if (group, ordinal) not in jitter:
                jitter[group, ordinal] = rng.randint(0, config["anchor_jitter_us"])
            last = first + count - 1
            anchor = (config["epoch_us"] + last * period + config["anchor_delay_us"]
                      + jitter[group, ordinal])
            # timestamp_first: the first anchor of a chain, which is the hardest
            # one for a receiver that compares with the previous packet.
            if channel_id == fault and (case == "offset" or (
                case == "timestamp" and ordinal == config["fault_index"]
            ) or (case == "timestamp_first" and ordinal == 0)):
                anchor += config["time_fault_us"]
            anchor = round(anchor)
            packet = Packet(
                WIRE_VERSION, channel_id, session_id,
                (config["seq_start"] + ordinal) & UINT32, first & UINT32,
                anchor, round(anchor - (count - 1) * period), fs, status,
                _payload(rng, channel_id, count),
            )
            rows.append(((anchor, ORDER.index(channel_id), ordinal),
                         channel_id, ordinal, packet))
    if with_events:
        for ordinal, event in enumerate(config["events"]):
            # Provisional values for fields that schema section 15 leaves open.
            packet = Packet(
                WIRE_VERSION, EVENT_CHANNEL, session_id,
                (config["seq_start"] + ordinal) & UINT32, ordinal, event["time_us"],
                event["time_us"], 0, config["status"], (event["code"],),
            )
            rows.append(((event["time_us"], ORDER.index(EVENT_CHANNEL), ordinal),
                         EVENT_CHANNEL, ordinal, packet))
    rows.sort(key=lambda row: row[0])
    return rows


def generate_stream(config, case="valid"):
    """Return ``(stream_bytes, layout)``; layout rows describe each sent packet.

    Each layout row is ``(offset, size, channel_key, seq, ordinal, fault)`` where
    ``fault`` marks the packet carrying the injected byte or header fault.
    """
    validate_config(config)
    if case not in CASES:
        raise ValueError("Unknown simulation case")
    rng = random.Random(config["seed"])
    fault = _channel_id(config["fault_channel"])
    index = config["fault_index"]
    if case == "session_restart":
        # MCU restart after packet ``fault_index`` of every data channel: a new
        # SESSION_ID, SEQ/index/clock restart, and events after the cut are lost.
        first = _session(config, rng, case, config["session_id"], index + 1, True)
        cut = max(row[0][0] for row in first if row[1] != EVENT_CHANNEL)
        first = [row for row in first
                 if row[1] != EVENT_CHANNEL or row[0][0] <= cut]
        rows = first + _session(config, rng, case, config["restart_session_id"],
                                config["packet_count"] - index - 1, False)
    else:
        rows = _session(config, rng, case, config["session_id"],
                        config["packet_count"], True)

    def position(ordinal):
        return next(i for i, row in enumerate(rows)
                    if row[1] == fault and row[2] == ordinal)

    target = position(index) if case != "session_restart" else None
    if case == "missing":
        del rows[target]
    elif case == "duplicate":
        rows.insert(target + 1, rows[target])
    elif case == "reordered":
        later = position(index + 1)
        rows[target], rows[later] = rows[later], rows[target]

    stream, layout = bytearray(), []
    for i, (_, channel_id, ordinal, packet) in enumerate(rows):
        is_fault = case in ("crc", "byte_loss", "version") and i == target
        if is_fault and case == "version":
            # Otherwise valid packet (CRC recomputed) with a VERSION byte not 0x01.
            packet = replace(packet, version=config["unsupported_version"])
        payload = bytearray(encode_packet(packet))
        if is_fault and case == "crc":
            payload[40] ^= 0x01  # First DATA byte; CRC16 left unchanged.
        elif is_fault and case == "byte_loss":
            del payload[40:40 + config["byte_loss_count"]]
        layout.append((len(stream), len(payload), _key(channel_id), packet.seq,
                       ordinal, is_fault))
        stream += payload
    return bytes(stream), layout


def session_metadata(config, case, config_sha256):
    """Schema section 11 metadata of a generated stream; every null has a reason."""
    validate_config(config)
    reasons = {
        "firmware_version": "SYNTHETIC generator; no firmware",
        "firmware_commit": "SYNTHETIC generator; no firmware",
        "operator": "SYNTHETIC; no operator",
        "electrode_type": "SYNTHETIC; no electrodes",
        "electrode_placement": "SYNTHETIC; no electrodes",
    }
    channels = {}
    keys = sorted(config["channels"], key=lambda k: ORDER.index(_channel_id(k)))
    for key in [*keys, _key(EVENT_CHANNEL)]:
        is_event = key == _key(EVENT_CHANNEL)
        channels[key] = {
            "sensor": "SYNTHETIC_EVENT" if is_event else "SYNTHETIC",
            "fs_nominal_mhz": None if is_event
            else config["channels"][key]["fs_nominal_mhz"],
            "latency_l_us": None, "latency_source": None,
            "unit_conversion": None, "afe_config": None,
        }
        reasons.update({
            f"channels.{key}.latency_l_us": "not measured; generator anchor delay "
                                            "is a simulation parameter",
            f"channels.{key}.latency_source": "no bench measurement",
            f"channels.{key}.unit_conversion": "synthetic integers, no physical unit",
            f"channels.{key}.afe_config": "no AFE in simulation",
        })
        if is_event:
            reasons[f"channels.{key}.fs_nominal_mhz"] = (
                "event packets have no sample rate (schema section 15 open)"
            )
    return {
        "schema_version": "packet-session-metadata-v0", "source_type": "SYNTHETIC",
        "clock_id": "SYN_ESP_TIMER_US", "firmware_version": None,
        "firmware_commit": None, "device_id": "SYN_DEVICE_001", "operator": None,
        "electrode_type": None, "electrode_placement": None, "channels": channels,
        "simulation": {"generator": VERSION, "case": case,
                       "config_sha256": config_sha256, "common_index_epoch": True},
        "null_reasons": dict(sorted(reasons.items())),
    }
