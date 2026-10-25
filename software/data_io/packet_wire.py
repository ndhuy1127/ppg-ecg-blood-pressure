"""Byte codec for Packet Schema V0.1 (configs/hardware/Packet_Schema_V0.1.md).

Pure code: no file/serial I/O and no printing. ``StreamDecoder`` accepts bytes in
arbitrary chunks, so offline replay and a live byte source share one path. A
candidate packet whose header is implausible or whose CRC fails is dropped and
the SYNC search restarts at the next byte: a declared length that has not been
validated is never used to skip ahead.
"""

import struct
from dataclasses import dataclass

SYNC = b"\xa5\x5a"
WIRE_VERSION = 0x01  # Packet Schema V0.1; the default of the decoder.
WIRE_VERSION_V02 = 0x02  # Packet Schema V0.2 (configs/hardware/Packet_Schema_V0.2.md)
# Offsets 0..39 of schema section 6: SYNC, VERSION, CHANNEL_ID, SESSION_ID, SEQ,
# FIRST_SAMPLE_INDEX, T_ANCHOR_US, T_FIRST_US, FS_NOMINAL_MHZ, SAMPLE_COUNT, STATUS.
HEADER = struct.Struct("<2sBBIIIQQIHH")
CRC = struct.Struct("<H")
SAMPLE = struct.Struct("<i")
MAX_SAMPLE_COUNT = 32
ECG_CHANNEL = 0xE1
PPG_CHANNELS = (0xF1, 0xF2, 0xF3, 0xF4)
EVENT_CHANNEL = 0xC1
# V0.2: BMI270 accelerometer X/Y/Z then gyroscope X/Y/Z, and device info.
IMU_CHANNELS = (0xA1, 0xA2, 0xA3, 0xA4, 0xA5, 0xA6)
DEVICE_INFO_CHANNEL = 0xD1
# V0.2 section 11 (2026-10-25): MAX30101 die temperature, 1/16 degC, 1 Hz, one
# value per packet; only STATUS bits 1 and 3 are defined on it.
TEMP_CHANNEL = 0xB1
TEMP_FS_MHZ = 1000
TEMP_STATUS_BITS = (1 << 1) | (1 << 3)
CHANNELS = {
    ECG_CHANNEL: "ECG", 0xF1: "PPG_SLOT1", 0xF2: "PPG_SLOT2",
    0xF3: "PPG_SLOT3", 0xF4: "PPG_SLOT4", EVENT_CHANNEL: "EVENT",
    0xA1: "ACC_X", 0xA2: "ACC_Y", 0xA3: "ACC_Z",
    0xA4: "GYRO_X", 0xA5: "GYRO_Y", 0xA6: "GYRO_Z",
    DEVICE_INFO_CHANNEL: "DEVICE_INFO", TEMP_CHANNEL: "DIE_TEMP",
}
# CHANNEL_ID registry per wire VERSION; the decoder drops other channels.
VERSION_CHANNELS = {
    WIRE_VERSION: frozenset((ECG_CHANNEL, *PPG_CHANNELS, EVENT_CHANNEL)),
    WIRE_VERSION_V02: frozenset((ECG_CHANNEL, *PPG_CHANNELS, EVENT_CHANNEL,
                                 *IMU_CHANNELS, DEVICE_INFO_CHANNEL, TEMP_CHANNEL)),
}
# Schema section 9; bits 7 and 8 exist from V0.2 on. Reserved bits must be sent as 0.
STATUS_BITS = {
    0: "afe_fifo_overflow", 1: "mcu_buffer_overflow", 2: "ecg_lead_off",
    3: "afe_error", 4: "latency_unmeasured", 5: "index_reanchored",
    6: "ppg_alc_overflow", 7: "backlog_chunk", 8: "anchor_samp",
}
STATUS_RESERVED_MASK = 0xFF80  # V0.1
STATUS_RESERVED_MASKS = {WIRE_VERSION: 0xFF80, WIRE_VERSION_V02: 0xFE00}
# V0.2 section 7.4: T_ANCHOR_US is the SAMP edge of the packet's last sample.
# Defined for ECG only; on any other channel bit 8 is reserved.
SAMP_ANCHOR_BIT = 1 << 8


def status_reserved_mask(version, channel_id):
    """Reserved STATUS bits of a packet of this VERSION and channel."""
    if channel_id == TEMP_CHANNEL:
        return 0xFFFF & ~TEMP_STATUS_BITS
    mask = STATUS_RESERVED_MASKS[version]
    return mask if channel_id == ECG_CHANNEL else mask | SAMP_ANCHOR_BIT
# V0.2 device info payload (section 6): layout 1, 25 words.
DEVICE_INFO_LAYOUT = 1
DEVICE_INFO_COUNT = 25
DECODE_ERRORS = (
    "unsupported_version", "bad_sample_count", "crc_mismatch", "unknown_channel",
    "truncated_packet",
)


def _crc_table():
    table = []
    for byte in range(256):
        crc = byte << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) if crc & 0x8000 else crc << 1
            crc &= 0xFFFF
        table.append(crc)
    return tuple(table)


_CRC_TABLE = _crc_table()


def crc16_ccitt_false(payload) -> int:
    """CRC-16/CCITT-FALSE: poly 0x1021, init 0xFFFF, no reflection, xorout 0."""
    crc = 0xFFFF
    for byte in payload:
        crc = ((crc << 8) & 0xFFFF) ^ _CRC_TABLE[(crc >> 8) ^ byte]
    return crc


@dataclass(frozen=True)
class Packet:
    """Header fields and DATA of one packet; SYNC and CRC16 are implied."""

    version: int
    channel_id: int
    session_id: int
    seq: int
    first_sample_index: int
    t_anchor_us: int
    t_first_us: int
    fs_nominal_mhz: int
    status: int
    data: tuple


@dataclass(frozen=True)
class DecodedPacket:
    packet: Packet
    offset: int  # Stream offset of the first SYNC byte.
    size: int


@dataclass(frozen=True)
class DecodeError:
    offset: int
    code: str


def device_info_data(elf_sha256, app_version, idf_version) -> tuple:
    """DATA of a V0.2 ``0xD1`` packet (Packet Schema V0.2 section 6).

    Layout word, then the 32-byte ELF SHA-256 and two 32-byte NUL-padded ASCII
    strings, each 4 bytes joined big-endian into a word kept as the int32 bit
    pattern (a word >= 2**31 becomes negative).
    """
    digest = bytes.fromhex(elf_sha256)
    if len(digest) != 32:
        raise ValueError("elf_sha256 must be 64 hex digits")

    def field(text):
        try:
            raw = text.encode("ascii")
        except (AttributeError, UnicodeEncodeError) as exc:
            raise ValueError("Version strings must be ASCII text") from exc
        if len(raw) > 31 or b"\0" in raw:
            raise ValueError("Version strings: at most 31 ASCII bytes, no NUL")
        return raw.ljust(32, b"\0")

    raw = digest + field(app_version) + field(idf_version)
    words = (int.from_bytes(raw[i:i + 4], "big") for i in range(0, len(raw), 4))
    return (DEVICE_INFO_LAYOUT,
            *(word - (1 << 32) if word >= 1 << 31 else word for word in words))


def encode_packet(packet: Packet) -> bytes:
    """Pack fields as given (little-endian) and append CRC16 over bytes 2..39+4N.

    Only field widths are checked, so tests can build packets that the decoder
    must reject (unsupported version, SAMPLE_COUNT above 32).
    """
    values = (
        packet.version, packet.channel_id, packet.session_id, packet.seq,
        packet.first_sample_index, packet.t_anchor_us, packet.t_first_us,
        packet.fs_nominal_mhz, len(packet.data), packet.status, *packet.data,
    )
    if any(isinstance(v, bool) or not isinstance(v, int) for v in values):
        raise ValueError("Packet fields and DATA must be integers")
    try:
        body = HEADER.pack(SYNC, *values[:10]) + b"".join(
            SAMPLE.pack(value) for value in packet.data
        )
    except struct.error as exc:
        raise ValueError(f"Packet field out of range: {exc}") from exc
    return body + CRC.pack(crc16_ccitt_false(body[2:]))


class StreamDecoder:
    """Incremental SYNC/CRC decoder; ``errors`` and ``skipped`` grow as bytes arrive.

    ``skipped`` lists runs of bytes that belong to no accepted packet, as
    ``(offset, length)``; every rejected candidate contributes at least its
    first SYNC byte to such a run.

    One damaged packet is one error. A ``crc_mismatch`` with a plausible header
    covers its declared length, and the first ``truncated_packet`` covers the
    rest of the stream: a rejected SYNC candidate that starts inside that span
    goes to ``rejected_candidates``, not ``errors``. A candidate that passes CRC
    there is still decoded.
    """

    def __init__(self, supported_versions=(WIRE_VERSION,)):
        self.supported_versions = frozenset(supported_versions)
        self.errors = []
        self.rejected_candidates = []
        self.skipped = []
        self.bytes_seen = 0
        self._buffer = bytearray()
        self._base = 0
        self._run = None
        self._covered = None  # Stream offset where the last counted error ends.
        self._finished = False

    def feed(self, chunk) -> list:
        if self._finished:
            raise ValueError("Decoder already finished")
        chunk = bytes(chunk)
        self.bytes_seen += len(chunk)
        self._buffer += chunk
        return self._drain(final=False)

    def finish(self) -> list:
        """Decode what is left; an incomplete tail is reported, never padded."""
        packets = self._drain(final=True)
        self._close_run()
        self._finished = True
        return packets

    def _skip(self, start, end):
        if end <= start:
            return
        start, end = self._base + start, self._base + end
        if self._run is not None and self._run[1] == start:
            self._run[1] = end
        else:
            self._close_run()
            self._run = [start, end]

    def _close_run(self):
        if self._run is not None:
            self.skipped.append((self._run[0], self._run[1] - self._run[0]))
            self._run = None

    def _reject(self, offset, problem, end):
        """Count a rejected candidate; ``end`` is the span it covers, if any."""
        if self._covered is not None and offset < self._covered:
            self.rejected_candidates.append(DecodeError(offset, problem))
            return
        self.errors.append(DecodeError(offset, problem))
        if end is not None:
            self._covered = end

    def _drain(self, final):
        buffer, position, packets = self._buffer, 0, []
        while True:
            start = buffer.find(SYNC, position)
            if start < 0:
                # A trailing 0xA5 may be the first half of a SYNC still in transit.
                keep = not final and buffer.endswith(SYNC[:1])
                end = len(buffer) - 1 if keep else len(buffer)
                if final and len(buffer) > position and buffer.endswith(SYNC[:1]):
                    # At the end it is the start of a packet that never arrived.
                    end_offset = self._base + len(buffer)
                    self._reject(end_offset - 1, "truncated_packet", end_offset)
                self._skip(position, end)
                position = max(position, end)
                break
            self._skip(position, start)
            position = start
            available = len(buffer) - start
            if available < HEADER.size:
                if not final:
                    break
                problem, size = "truncated_packet", None
            else:
                fields = HEADER.unpack_from(buffer, start)
                version, channel, count = fields[1], fields[2], fields[9]
                size = HEADER.size + SAMPLE.size * count + CRC.size
                if version not in self.supported_versions:
                    problem = "unsupported_version"
                elif not 1 <= count <= MAX_SAMPLE_COUNT:
                    problem = "bad_sample_count"
                elif available < size:
                    if not final:
                        break
                    problem = "truncated_packet"
                elif crc16_ccitt_false(buffer[start + 2:start + size - 2]) != (
                    CRC.unpack_from(buffer, start + size - 2)[0]
                ):
                    problem = "crc_mismatch"
                elif channel not in VERSION_CHANNELS.get(version, ()):
                    problem = "unknown_channel"
                else:
                    problem = None
            if problem is None:
                first = start + HEADER.size
                data = tuple(
                    SAMPLE.unpack_from(buffer, first + SAMPLE.size * i)[0]
                    for i in range(count)
                )
                packet = Packet(*fields[1:9], fields[10], data)
                self._close_run()
                self._covered = None
                packets.append(DecodedPacket(packet, self._base + start, size))
                position = start + size
                continue
            if problem == "unknown_channel":
                # Passed CRC: a real packet, counted even inside a damaged one.
                self._covered = None
            covers = None
            if problem == "crc_mismatch":
                covers = self._base + start + size
            elif problem == "truncated_packet":
                covers = self._base + len(buffer)
            self._reject(self._base + start, problem, covers)
            if problem == "unknown_channel":
                # CRC passed, so the declared length is trustworthy: skip the packet.
                self._skip(start, start + size)
                position = start + size
            else:
                self._skip(start, start + 1)
                position = start + 1
        del buffer[:position]
        self._base += position
        return packets


def decode_bytes(payload, chunk_size=4096, supported_versions=(WIRE_VERSION,)):
    """Decode a complete byte string; returns ``(packets, decoder)``."""
    if isinstance(chunk_size, bool) or not isinstance(chunk_size, int) or (
        chunk_size < 1
    ):
        raise ValueError("chunk_size must be a positive integer")
    decoder, packets, payload = StreamDecoder(supported_versions), [], bytes(payload)
    for start in range(0, len(payload), chunk_size):
        packets += decoder.feed(payload[start:start + chunk_size])
    packets += decoder.finish()
    return packets, decoder
