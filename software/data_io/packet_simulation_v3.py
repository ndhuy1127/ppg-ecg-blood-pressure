"""SYNTHETIC byte streams in the Packet Schema layout (``synthetic-packet-v3``).

Pure code: returns bytes and metadata, writes nothing. It lets the PC logger be
tested before firmware exists. Sample rates, packet sizes, anchor delay/jitter
and fault magnitudes are simulation parameters, not hardware decisions (schema
section 15 is still open). Payloads are reproducible random integers in the
schema value ranges, not physiological waveforms. ``synthetic-packet-v2``
(JSON interface, ``packet_simulation.py``) is unchanged and still supported.

``wire_version`` 1 gives Packet Schema V0.1 streams. ``wire_version`` 2 gives
V0.2 streams: the same channels plus optional BMI270 IMU axes (one FIFO read
shared by the six axes, signed payload) and device info packets, with the V0.2
cases ``V02_CASES``. Streams of a V0.1 config are byte for byte those of the
code before V0.2 support (2026-10-24), except event STATUS (2026-10-23).
"""

import random
from dataclasses import replace
from fractions import Fraction

from software.data_io.packet_wire import (
    CHANNELS, DEVICE_INFO_CHANNEL, ECG_CHANNEL, EVENT_CHANNEL, IMU_CHANNELS,
    MAX_SAMPLE_COUNT, PPG_CHANNELS, STATUS_RESERVED_MASKS, VERSION_CHANNELS,
    WIRE_VERSION, WIRE_VERSION_V02, Packet, device_info_data, encode_packet,
)

VERSION = "synthetic-packet-v3"
CASES = (
    "valid", "missing", "duplicate", "reordered", "timestamp", "timestamp_first",
    "offset", "crc", "byte_loss", "index_jump", "reanchor", "version",
    "session_restart",
)
# V0.2 only: IMU backlog split into chunks (bit 7), IMU FIFO full then re-anchor
# (bit 0, then bit 5), one packet of the old VERSION, device info that changes.
V02_CASES = ("imu_backlog", "imu_fifo_full", "mixed_version", "device_info_changed")
CONFIG_FIELDS = {
    "schema_version", "source_type", "wire_version", "seed", "session_id",
    "restart_session_id", "epoch_us", "anchor_delay_us", "anchor_jitter_us",
    "seq_start", "index_start", "packet_count", "status", "channels", "events",
    "fault_channel", "fault_index", "time_fault_us", "index_jump_samples",
    "reanchor_jump_samples", "byte_loss_count", "unsupported_version",
}
DATA_CHANNELS = (ECG_CHANNEL, *PPG_CHANNELS, *IMU_CHANNELS)
ORDER = (*DATA_CHANNELS, EVENT_CHANNEL, DEVICE_INFO_CHANNEL)
DEVICE_INFO_FIELDS = {"elf_sha256", "app_version", "idf_version", "interval_us"}
UINT16, UINT32 = (1 << 16) - 1, (1 << 32) - 1
AFE_OVERFLOW_BIT, REANCHOR_BIT, BACKLOG_BIT = 1 << 0, 1 << 5, 1 << 7


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
    if not isinstance(config, dict):
        raise ValueError("Config must be an object")
    v02 = config.get("wire_version") == WIRE_VERSION_V02
    if set(config) != (CONFIG_FIELDS | {"device_info"} if v02 else CONFIG_FIELDS):
        raise ValueError("Config has missing or unsupported fields")
    if (config["schema_version"], config["source_type"]) != (VERSION, "SYNTHETIC"):
        raise ValueError("Only the synthetic-packet-v3 SYNTHETIC config is supported")
    if config["wire_version"] not in (WIRE_VERSION, WIRE_VERSION_V02):
        raise ValueError("wire_version must be 1 (Packet Schema V0.1) or 2 (V0.2)")
    for name in ("seed", "epoch_us", "anchor_delay_us", "anchor_jitter_us"):
        _integer(config[name], name, 0, 10 ** 12)
    for name in ("session_id", "restart_session_id", "seq_start", "index_start"):
        _integer(config[name], name, 0, UINT32)
    if config["session_id"] == config["restart_session_id"]:
        raise ValueError("restart_session_id must differ from session_id")
    _integer(config["packet_count"], "packet_count", 3, 10000)
    _integer(config["status"], "status", 0, UINT16)
    if config["status"] & STATUS_RESERVED_MASKS[config["wire_version"]]:
        raise ValueError("STATUS reserved bits of this wire version must be 0")
    channels = config["channels"]
    if not isinstance(channels, dict) or _key(ECG_CHANNEL) not in channels:
        raise ValueError("channels must include 0xE1")
    ppg, imu = [], []
    for key, spec in channels.items():
        if _channel_id(key) not in DATA_CHANNELS:
            raise ValueError("channels holds data channels only; events are separate")
        if _channel_id(key) in IMU_CHANNELS and not v02:
            raise ValueError("IMU channels need wire_version 2 (Packet Schema V0.2)")
        if not isinstance(spec, dict) or (
            set(spec) != {"fs_nominal_mhz", "sample_count"}
        ):
            raise ValueError("Channel needs fs_nominal_mhz and sample_count")
        _integer(spec["fs_nominal_mhz"], "fs_nominal_mhz", 1, UINT32)
        _integer(spec["sample_count"], "sample_count", 1, 32)
        if _channel_id(key) in PPG_CHANNELS:
            ppg.append((spec["fs_nominal_mhz"], spec["sample_count"]))
        if _channel_id(key) in IMU_CHANNELS:
            imu.append((spec["fs_nominal_mhz"], spec["sample_count"]))
    if len(set(ppg)) > 1:
        raise ValueError("PPG slots come from one FIFO read: same fs and sample_count")
    if imu and (len(imu) != len(IMU_CHANNELS) or len(set(imu)) > 1):
        raise ValueError("IMU: all six axes, from one FIFO read (same fs and count)")
    if config["fault_channel"] in channels and (
        _channel_id(config["fault_channel"]) in IMU_CHANNELS
    ):
        raise ValueError("fault_channel must be ECG or PPG; IMU faults are V0.2 cases")
    if v02:
        info = config["device_info"]
        if not isinstance(info, dict) or set(info) != DEVICE_INFO_FIELDS:
            fields = ", ".join(sorted(DEVICE_INFO_FIELDS))
            raise ValueError(f"device_info needs {fields}")
        device_info_data(info["elf_sha256"], info["app_version"], info["idf_version"])
        _integer(info["interval_us"], "device_info interval_us", 1, 10 ** 9)
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
    if config["unsupported_version"] in VERSION_CHANNELS:
        # 1 and 2 are both decodable (Packet Schema V0.1, V0.2).
        raise ValueError("unsupported_version must not be a supported wire VERSION")
    return True


def _payload(rng, channel_id, count):
    if channel_id == ECG_CHANNEL:
        # 18-bit two's complement sample left-aligned in a 24-bit word, ETAG/PTAG 0.
        return tuple((rng.randint(-(1 << 17), (1 << 17) - 1) & 0x3FFFF) << 6
                     for _ in range(count))
    return tuple(rng.randint(0, (1 << 18) - 1) for _ in range(count))


def _round_half_up(value):
    return int((value * 2 + 1) // 2)


def backlog_chunks(first, frames, anchor, period, status):
    """Split one FIFO read of ``frames`` frames latched at ``anchor`` (V0.2 section 4).

    Returns ``(first_index, count, t_first, status)`` per chunk of at most 32
    frames: indices continuous, every chunk the anchor of the read, T_FIRST of the
    chunk starting at frame s = anchor - round_half_up((frames - 1 - s) * period),
    and STATUS bit 7 on every chunk but the one holding the newest frame.
    """
    chunks = []
    for start in range(0, frames, MAX_SAMPLE_COUNT):
        count = min(MAX_SAMPLE_COUNT, frames - start)
        newest = start + count == frames
        chunks.append((first + start, count,
                       anchor - _round_half_up((frames - 1 - start) * period),
                       status if newest else status | BACKLOG_BIT))
    return chunks


def reanchor_index(last_prev, ref_last, ref_anchor, next_anchor, period, next_count):
    """FIRST_SAMPLE_INDEX of the read after a full FIFO (V0.2 section 5).

    q = round_half_up((A_next - A_ref) / T); FIRST = max(last_prev + 1,
    I_ref + q - (M_next - 1)), with (I_ref, A_ref) the last sample index and
    anchor of the last reliable read. Without a usable reference (elapsed <= 0)
    the index continues: last_prev + 1.
    """
    elapsed = next_anchor - ref_anchor
    if elapsed <= 0:
        return last_prev + 1
    q = _round_half_up(Fraction(elapsed) / period)
    return max(last_prev + 1, ref_last + q - (next_count - 1))


def _imu_reads(config, rng, case, packet_count):
    """BMI270 FIFO reads shared by the six axes: ``(first, count, anchor, t_first,
    status)`` per emitted chunk, with the V0.2 backlog and FIFO-full cases.

    imu_backlog: reads fault_index .. fault_index + k - 1 are one late read of
    k * count > 32 frames (V0.2 section 4). imu_fifo_full (section 5): the read
    fault_index finds the FIFO full; it holds that read's frames but happens at
    the time of read fault_index + 2, so reads fault_index + 1 and + 2 are lost.
    It sets bit 0; the next read re-anchors from the last reliable read with the
    section 5 formula and sets bit 5; later reads continue from that index.
    """
    spec = config["channels"][_key(IMU_CHANNELS[0])]
    count = spec["sample_count"]
    period = Fraction(10 ** 9, spec["fs_nominal_mhz"])
    reads = []
    for ordinal in range(packet_count):
        first = config["index_start"] + ordinal * count
        last = first + count - 1
        anchor = round(config["epoch_us"] + last * period + config["anchor_delay_us"]
                       + rng.randint(0, config["anchor_jitter_us"]))
        reads.append((first, count, anchor, config["status"]))
    fault = config["fault_index"]
    if case == "imu_backlog":
        merged = MAX_SAMPLE_COUNT // count + 1  # so that the read exceeds 32 frames
        if fault + merged > packet_count:
            raise ValueError("imu_backlog needs packet_count >= fault_index + "
                             f"{merged}")
        backlog = reads[fault:fault + merged]
        late = backlog[-1][2]
        chunks = [(f, n, late, t_first, s) for f, n, t_first, s in backlog_chunks(
            backlog[0][0], merged * count, late, period, config["status"])]
        rest = reads[:fault], reads[fault + merged:]
    elif case == "imu_fifo_full":
        if fault + 3 >= packet_count:
            raise ValueError("imu_fifo_full needs packet_count > fault_index + 3")
        ref_first, ref_count, ref_anchor, _ = reads[fault - 1]
        full_first, _, _, status = reads[fault]
        next_first, _, next_anchor, _ = reads[fault + 3]
        reanchored = reanchor_index(full_first + count - 1, ref_first + ref_count - 1,
                                    ref_anchor, next_anchor, period, count)
        shift = reanchored - next_first
        reads = (reads[:fault]
                 + [(full_first, count, reads[fault + 2][2], status | AFE_OVERFLOW_BIT)]
                 + [(f + shift, n, a, s | (REANCHOR_BIT if i == 0 else 0))
                    for i, (f, n, a, s) in enumerate(reads[fault + 3:])])
        chunks, rest = [], (reads, [])
    else:
        chunks, rest = [], (reads, [])

    def plain(part):
        return [(f, n, a, a - _round_half_up((n - 1) * period), s)
                for f, n, a, s in part]

    return plain(rest[0]) + chunks + plain(rest[1])


def _v02_rows(config, rng, case, session_id, packet_count, end_us):
    """IMU and device info rows of one V0.2 session. They are drawn after the V0.1
    channels, so the random draws of those do not change."""
    version = config["wire_version"]
    rows = []
    if _key(IMU_CHANNELS[0]) in config["channels"]:
        fs = config["channels"][_key(IMU_CHANNELS[0])]["fs_nominal_mhz"]
        reads = _imu_reads(config, rng, case, packet_count)
        for seq, (first, count, anchor, t_first, status) in enumerate(reads):
            for channel_id in IMU_CHANNELS:
                payload = tuple(rng.randint(-(1 << 15), (1 << 15) - 1)
                                for _ in range(count))
                packet = Packet(version, channel_id, session_id,
                                (config["seq_start"] + seq) & UINT32, first & UINT32,
                                anchor, t_first, fs, status, payload)
                rows.append(((anchor, ORDER.index(channel_id), seq), channel_id, seq,
                             packet))
    info = config["device_info"]
    end_us = max([end_us, *(row[0][0] for row in rows)])
    for ordinal in range((end_us - config["epoch_us"]) // info["interval_us"] + 1):
        t = config["epoch_us"] + ordinal * info["interval_us"]
        app = info["app_version"]
        if case == "device_info_changed" and ordinal == 1:
            app += "-b"  # a different firmware identity within the session
        packet = Packet(version, DEVICE_INFO_CHANNEL, session_id,
                        (config["seq_start"] + ordinal) & UINT32, ordinal, t, t, 0, 0,
                        device_info_data(info["elf_sha256"], app, info["idf_version"]))
        rows.append(((t, ORDER.index(DEVICE_INFO_CHANNEL), ordinal),
                     DEVICE_INFO_CHANNEL, ordinal, packet))
    return rows


def _session(config, rng, case, session_id, packet_count, with_events):
    """Return ``(sort_key, channel_id, ordinal, Packet)`` rows of one session."""
    fault = _channel_id(config["fault_channel"])
    version = config["wire_version"]
    rows = []
    jitter = {}
    for key in sorted(config["channels"], key=lambda k: ORDER.index(_channel_id(k))):
        channel_id = _channel_id(key)
        if channel_id in IMU_CHANNELS:
            continue  # V0.2: generated by _v02_rows from one shared FIFO read
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
                version, channel_id, session_id,
                (config["seq_start"] + ordinal) & UINT32, first & UINT32,
                anchor, round(anchor - (count - 1) * period), fs, status,
                _payload(rng, channel_id, count),
            )
            rows.append(((anchor, ORDER.index(channel_id), ordinal),
                         channel_id, ordinal, packet))
    if with_events:
        for ordinal, event in enumerate(config["events"]):
            # Schema section 10: STATUS bit 4 (latency unmeasured) is off for
            # events; config "status" applies to data packets only (2026-10-23,
            # as the firmware sends them).
            packet = Packet(
                version, EVENT_CHANNEL, session_id,
                (config["seq_start"] + ordinal) & UINT32, ordinal, event["time_us"],
                event["time_us"], 0, 0, (event["code"],),
            )
            rows.append(((event["time_us"], ORDER.index(EVENT_CHANNEL), ordinal),
                         EVENT_CHANNEL, ordinal, packet))
    if version == WIRE_VERSION_V02:
        end_us = max(row[0][0] for row in rows)
        rows += _v02_rows(config, rng, case, session_id, packet_count, end_us)
    rows.sort(key=lambda row: row[0])
    return rows


def generate_stream(config, case="valid"):
    """Return ``(stream_bytes, layout)``; layout rows describe each sent packet.

    Each layout row is ``(offset, size, channel_key, seq, ordinal, fault)`` where
    ``fault`` marks the packet carrying the injected byte or header fault.
    """
    validate_config(config)
    if case not in CASES and case not in V02_CASES:
        raise ValueError("Unknown simulation case")
    if case in V02_CASES and config["wire_version"] != WIRE_VERSION_V02:
        raise ValueError(f"Case {case} needs wire_version 2 (Packet Schema V0.2)")
    if case in V02_CASES[:2] and _key(IMU_CHANNELS[0]) not in config["channels"]:
        raise ValueError(f"Case {case} needs the IMU channels")
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
        is_fault = case in ("crc", "byte_loss", "version", "mixed_version") and (
            i == target)
        if is_fault and case == "version":
            # Otherwise valid packet (CRC recomputed) with an unsupported VERSION.
            packet = replace(packet, version=config["unsupported_version"])
        elif is_fault and case == "mixed_version":
            # A V0.1 packet inside a V0.2 session (V0.2 section 1).
            packet = replace(packet, version=WIRE_VERSION)
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
    extra = [_key(EVENT_CHANNEL)]
    if config["wire_version"] == WIRE_VERSION_V02:
        extra.append(_key(DEVICE_INFO_CHANNEL))
    for key in [*keys, *extra]:
        is_event = key in extra  # no sample rate: events and device info
        sensor = {_key(EVENT_CHANNEL): "SYNTHETIC_EVENT",
                  _key(DEVICE_INFO_CHANNEL): "SYNTHETIC_DEVICE_INFO"}
        channels[key] = {
            "sensor": sensor.get(key, "SYNTHETIC"),
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
                if key == _key(EVENT_CHANNEL)
                else "device info packets have no sample rate (V0.2 section 6)"
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
