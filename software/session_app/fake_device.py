"""A SYNTHETIC device for the demo mode of the session app (spec sections 4, 11).

It plays a ``synthetic_session`` stream as time passes and answers what the app
would send to a real device: an operator or cuff-end mark becomes an event
packet (0xC1) with the next event ordinal, and the demo "t0 button" one with
code 1. Pure code: the caller passes the time and gets bytes; no thread, port or
file. Only for showing and testing the app: SYNTHETIC, never a recording.
"""

from software.data_io.packet_wire import (
    EVENT_CHANNEL,
    WIRE_VERSION_V02,
    Packet,
    StreamDecoder,
    encode_packet,
)
from software.device.synthetic_session import SessionSpec, generate


class FakeDevice:
    def __init__(self, duration_s=900.0, seed=20261127):
        self.spec = SessionSpec(duration_s=duration_s, seed=seed, events=())
        stream, self.metadata, _ = generate(self.spec)
        decoder = StreamDecoder(supported_versions=(WIRE_VERSION_V02,))
        items = decoder.feed(stream) + decoder.finish()
        # (anchor, bytes) in stream order; the stream is sorted by anchor.
        self._packets = [(i.packet.t_anchor_us, stream[i.offset:i.offset + i.size])
                         for i in items]
        self._next = 0
        self._ordinal = 0
        self._seq = 0
        self._extra = []      # event packets waiting for their time

    @property
    def start_us(self):
        return self.spec.start_us

    def event(self, code, now_s):
        """An event packet at ``now_s`` (seconds from the start of the stream)."""
        anchor = int(round(self.start_us + now_s * 1e6))
        packet = Packet(WIRE_VERSION_V02, EVENT_CHANNEL, self.spec.session_id,
                        self._seq, self._ordinal, anchor, anchor, 0, 0, (code,))
        self._extra.append((anchor, encode_packet(packet)))
        self._seq += 1
        self._ordinal += 1
        return self._ordinal - 1

    def read(self, now_s):
        """Every byte due by ``now_s``, data and events in anchor order."""
        until = self.start_us + now_s * 1e6
        due = []
        while self._next < len(self._packets) and self._packets[self._next][0] <= until:
            due.append(self._packets[self._next])
            self._next += 1
        due += self._extra
        self._extra = []
        due.sort(key=lambda item: item[0])
        return b"".join(chunk for _, chunk in due)

    @property
    def finished(self):
        return self._next >= len(self._packets) and not self._extra
