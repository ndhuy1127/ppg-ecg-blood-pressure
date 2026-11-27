"""Live view of the packet stream for the session app (spec section 6.1).

Pure code: bytes in (read from the growing ``raw.bin`` the logger writes, or from
the demo device), display buffers and device happenings out. It decodes with the
logger's own ``StreamDecoder``; it never writes anything and is not the record:
``decode.json`` after the session is (spec section 2, point 3). Live numbers lag
and are not the SQI flags of the analysis.
"""

from collections import deque

import numpy as np

from software.data_io.live_monitor import led_codes
from software.data_io.packet_receiver import decode_afe_config
from software.data_io.packet_wire import (
    AFE_CONFIG_CHANNEL,
    COMMAND_ACK_CHANNEL,
    ECG_CHANNEL,
    EVENT_CHANNEL,
    PPG_CHANNELS,
    STATUS_BITS,
    WIRE_VERSION,
    WIRE_VERSION_V02,
    StreamDecoder,
)
from software.device.features import ECG_VALID_ETAGS

ACC_CHANNELS = (0xA1, 0xA2, 0xA3)
MCU_OVERFLOW = 1 << 1
# STATUS bits worth showing the operator: FIFO and MCU buffer overflow, AFE error,
# ALC overflow. Bit 2 (ECG lead-off) is not used since 2026-11-24 (lead-off comes
# from the signal); bit 4 (latency unmeasured) is set on every packet of V1; the
# others are timing details of the logger.
SHOWN_STATUS_BITS = (0, 1, 3, 6)
DATA_CHANNELS = (ECG_CHANNEL, *PPG_CHANNELS, *ACC_CHANNELS)


def ecg_display(words):
    """Signed 18-bit samples of MAX30001 words; invalid ETAGs become NaN so the
    trace shows a gap instead of a value (schema section 8)."""
    words = np.asarray(words, dtype=np.int64) & 0xFFFFFF
    codes = (words >> 6) & 0x3FFFF
    codes = np.where(codes >= 1 << 17, codes - (1 << 18), codes).astype(float)
    etag = (words >> 3) & 7
    codes[~np.isin(etag, ECG_VALID_ETAGS)] = np.nan
    return codes


def display_points(x, y, max_points=1200):
    """At most ``max_points`` points for drawing, keeping each bucket's minimum and
    maximum in time order so R peaks and pulse feet stay visible (drawing only;
    the data are not changed)."""
    x, y = np.asarray(x, dtype=float), np.asarray(y, dtype=float)
    if y.size <= max_points:
        return x, y
    size = -(-y.size // (max_points // 2))          # samples per bucket, rounded up
    buckets = -(-y.size // size)
    padded = np.full(buckets * size, np.nan)
    padded[:y.size] = y
    grid = padded.reshape(buckets, size)
    finite = np.isfinite(grid)
    low = np.argmin(np.where(finite, grid, np.inf), axis=1)
    high = np.argmax(np.where(finite, grid, -np.inf), axis=1)
    base = np.arange(buckets) * size
    index = np.sort(np.stack((base + low, base + high), axis=1), axis=1).ravel()
    index = np.minimum(index, y.size - 1)
    return x[index], y[index]


def y_limits(y, margin=0.1):
    """Limits of a trace with a margin; None when there is nothing finite."""
    y = np.asarray(y, dtype=float)
    y = y[np.isfinite(y)]
    if not y.size:
        return None
    low, high = float(y.min()), float(y.max())
    pad = (high - low) * margin or max(abs(high), 1.0) * margin
    return low - pad, high + pad


class LiveStream:
    """Decode bytes as they come; keep the last ``window_s`` of each channel."""

    def __init__(self, window_s=10.0):
        self.window_s = window_s
        self.decoder = StreamDecoder(supported_versions=(WIRE_VERSION, WIRE_VERSION_V02))
        self.buffers, self.fs_hz = {}, {}
        self.session_id = None
        # Gaps of SEQ per channel: ``lost`` while recording; ``lost_overflow`` those
        # whose next packet says the MCU buffer overflowed (bit 1), i.e. the device
        # ran while nobody read the port, as before a recording starts.
        self.last_seq, self.lost, self.lost_overflow = {}, {}, {}
        self.status_seen = {}
        self.led = None
        self.bytes = 0

    def _buffer(self, channel, fs_hz, count):
        if channel not in self.buffers:
            self.fs_hz[channel] = fs_hz
            self.buffers[channel] = deque(maxlen=max(int(fs_hz * self.window_s), count))
        return self.buffers[channel]

    def feed(self, chunk):
        """Returns what happened in these bytes, in stream order:
        ``("session", id)``, ``("event", code, ordinal)``, ``("ack", data)``."""
        self.bytes += len(chunk)
        out = []
        for item in self.decoder.feed(chunk):
            packet = item.packet
            if packet.session_id != self.session_id:
                self.session_id = packet.session_id
                self.last_seq.clear()
                out.append(("session", packet.session_id))
            channel = packet.channel_id
            previous = self.last_seq.get(channel)
            if previous is not None and packet.seq > previous + 1:
                into = self.lost_overflow if packet.status & MCU_OVERFLOW else self.lost
                into[channel] = into.get(channel, 0) + packet.seq - previous - 1
            self.last_seq[channel] = packet.seq
            for bit, name in STATUS_BITS.items():
                if packet.status & (1 << bit) and bit in SHOWN_STATUS_BITS:
                    self.status_seen[name] = self.status_seen.get(name, 0) + 1
            if channel == EVENT_CHANNEL and len(packet.data) == 1:
                out.append(("event", int(packet.data[0]), int(packet.first_sample_index)))
            elif channel == COMMAND_ACK_CHANNEL:
                out.append(("ack", tuple(packet.data)))
            elif channel == AFE_CONFIG_CHANNEL:
                config, problem = decode_afe_config(packet)
                if problem is None and config.get("registers") and "MAX30101" in str(
                        config.get("afe", "")):
                    try:
                        self.led = led_codes(config["registers"])
                    except (KeyError, ValueError):
                        pass
            elif channel in DATA_CHANNELS and packet.fs_nominal_mhz > 0:
                values = list(packet.data)
                fs = packet.fs_nominal_mhz / 1000.0
                buffer = self._buffer(channel, fs, len(values))
                buffer.extend(ecg_display(values) if channel == ECG_CHANNEL else values)
        return out

    def trace(self, channel):
        """(time in s, ending at 0, values) of the last window of ``channel``."""
        values = np.asarray(self.buffers.get(channel, ()), dtype=float)
        if not values.size:
            return np.zeros(0), values
        fs = self.fs_hz[channel]
        return (np.arange(values.size) - values.size) / fs, values

    def acc_magnitude(self):
        """|acceleration| from the last samples common to the three axes."""
        parts = [np.asarray(self.buffers.get(c, ()), dtype=float) for c in ACC_CHANNELS]
        n = min(p.size for p in parts)
        if n == 0:
            return np.zeros(0), np.zeros(0)
        magnitude = np.sqrt(sum(p[-n:] ** 2 for p in parts))
        return (np.arange(n) - n) / self.fs_hz[ACC_CHANNELS[0]], magnitude
