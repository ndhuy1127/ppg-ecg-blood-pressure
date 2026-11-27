"""Live stream reader and demo device of the session app (SYNTHETIC)."""

import numpy as np
import pytest

from software.data_io.packet_wire import StreamDecoder
from software.session_app.fake_device import FakeDevice
from software.session_app.live import LiveStream, ecg_display


@pytest.fixture(scope="module")
def device_bytes():
    device = FakeDevice(duration_s=30.0)
    first = device.read(10.0)
    ordinals = [device.event(1, 10.5), device.event(4, 11.0), device.event(2, 12.0)]
    rest = device.read(31.0)  # anchors carry latency past 30 s
    return first, rest, ordinals, device


def test_events_come_back_in_order_with_their_ordinals(device_bytes):
    first, rest, ordinals, device = device_bytes
    assert ordinals == [0, 1, 2]
    live = LiveStream()
    assert live.feed(first) == [("session", 1)]
    events = [e for e in live.feed(rest) if e[0] == "event"]
    assert events == [("event", 1, 0), ("event", 4, 1), ("event", 2, 2)]
    assert device.finished
    # The demo stream is one valid packet stream: nothing dropped by the decoder.
    decoder = StreamDecoder(supported_versions=(2,))
    decoder.feed(first + rest)
    decoder.finish()
    assert decoder.errors == [] and decoder.skipped == []


def test_chunking_does_not_change_the_buffers(device_bytes):
    first, rest, _, _ = device_bytes
    whole, pieces = LiveStream(window_s=5.0), LiveStream(window_s=5.0)
    whole.feed(first + rest)
    data = first + rest
    for start in range(0, len(data), 777):
        pieces.feed(data[start:start + 777])
    for channel in (0xE1, 0xF1, 0xF2, 0xF3):
        t1, v1 = whole.trace(channel)
        t2, v2 = pieces.trace(channel)
        assert np.array_equal(v1, v2, equal_nan=True) and np.array_equal(t1, t2)
    # 5 s window: 512 x 5 ECG samples, 200 x 5 per PPG slot; times end at 0.
    assert whole.trace(0xE1)[1].size == 2560 and whole.trace(0xF1)[1].size == 1000
    assert whole.trace(0xF1)[0][-1] == pytest.approx(-1 / 200)
    assert whole.led == {"red": 40, "ir": 44, "green_led3": 18, "green_led4": 18}


def test_lost_packets_are_counted(device_bytes):
    first, _, _, _ = device_bytes
    items = StreamDecoder(supported_versions=(2,)).feed(first)
    ppg = [i for i in items if i.packet.channel_id == 0xF1]
    victim = ppg[10]  # one green PPG packet lost on the way
    data = first[:victim.offset] + first[victim.offset + victim.size:]
    live = LiveStream()
    live.feed(data)
    assert live.lost == {0xF1: 1}


def test_ecg_display_decodes_18_bit_words_and_hides_invalid_etags():
    # code -5 (18-bit two's complement) with ETAG 000, code 7 with ETAG 010 (EOF),
    # code 3 with ETAG 111 (FIFO empty: not a sample).
    words = [((-5) & 0x3FFFF) << 6, (7 << 6) | (2 << 3), (3 << 6) | (7 << 3)]
    out = ecg_display(words)
    assert out[0] == -5 and out[1] == 7 and np.isnan(out[2])


def test_display_points_keep_the_peaks_and_never_exceed_the_budget():
    from software.session_app.live import display_points, y_limits

    x = np.arange(5000) / 512.0
    y = np.zeros(5000)
    y[1234], y[4321] = 900.0, -700.0   # an R peak and a deep trough
    y[2000:2100] = np.nan              # a gap (invalid ETAG)
    xs, ys = display_points(x, y, max_points=1200)
    assert xs.size <= 1200 and np.all(np.diff(xs) >= 0)
    assert np.nanmax(ys) == 900.0 and np.nanmin(ys) == -700.0
    assert 1234 / 512.0 in xs and 4321 / 512.0 in xs
    short = np.arange(10.0)
    assert np.array_equal(display_points(short, short)[1], short)
    assert y_limits([0.0, 10.0]) == (-1.0, 11.0)
    assert y_limits([np.nan]) is None and y_limits([5.0, 5.0]) == (4.5, 5.5)


def test_overflow_gaps_and_hidden_status_bits(device_bytes):
    """A gap whose next packet carries MCU buffer overflow (bit 1) is counted apart
    (the device ran while nobody read the port); bits 2 and 4 are not shown."""
    from dataclasses import replace

    from software.data_io.packet_wire import encode_packet

    first, _, _, _ = device_bytes
    items = StreamDecoder(supported_versions=(2,)).feed(first)
    green = [i for i in items if i.packet.channel_id == 0xF1]
    red = [i for i in items if i.packet.channel_id == 0xF2]
    drop = {id(green[5]), id(green[6]), id(red[9])}
    out = b""
    for i in items:
        if id(i) in drop:
            continue
        packet = i.packet
        if i is green[7]:      # after the green gap: overflow, lead-off and latency bits
            packet = replace(packet, status=packet.status | 0b10110)
        out += encode_packet(packet)
    live = LiveStream()
    live.feed(out)
    assert live.lost_overflow == {0xF1: 2} and live.lost == {0xF2: 1}
    assert live.status_seen == {"mcu_buffer_overflow": 1}
