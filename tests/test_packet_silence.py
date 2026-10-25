"""Data channels with no trusted time within a session (channel_holes), SYNTHETIC
only.

channel_missing only sees a channel with no packet at all. These answers come
from the rule in docs/protocol/packet_logger.md: between the first and the last
trusted time (an accepted data anchor compared with another one, or the 0xD1
heartbeat), no data channel may leave a hole longer than
channel_silence_tolerance_us (3 s), at the start, in the middle or at the end.
A hole with no packet of the channel by SEQ (nor bit 1) is channel_silent;
otherwise channel_timing_unknown. Generator streams (metadata ``simulation``
set) are not checked.
"""

import copy
import json
from dataclasses import replace
from pathlib import Path

import pytest

from software.data_io.packet_receiver import analyze_stream
from software.data_io.packet_simulation_v3 import session_metadata
from software.data_io.packet_wire import (
    Packet, decode_bytes, device_info_data, encode_packet,
)

ROOT = Path(__file__).resolve().parents[1]
SIM_V02 = ROOT / "configs/hardware/packet_simulation_v3_v02.json"
LOGGER_CONFIG = ROOT / "configs/hardware/packet_logger.json"
ECG_T = 10 ** 9 / 512_000  # us per ECG sample


@pytest.fixture
def logger():
    return json.loads(LOGGER_CONFIG.read_bytes())


@pytest.fixture
def meta():
    m = copy.deepcopy(session_metadata(json.loads(SIM_V02.read_bytes()), "valid",
                                       "0" * 64))
    keys = ("0xE1", "0xF1", "0xD1")
    m["channels"] = {k: v for k, v in m["channels"].items() if k in keys}
    m["null_reasons"] = {n: r for n, r in m["null_reasons"].items()
                         if not n.startswith("channels.") or n.split(".")[1] in keys}
    m["simulation"] = None  # a recorded stream, not the generator's
    return m


def ecg_packets(t_from_s, t_to_s):
    out, k = [], 0
    while True:
        first = 16 * k
        anchor = round(1_000_000 + (first + 15) * ECG_T)
        if anchor > 1_000_000 + t_to_s * 1e6:
            return out
        if anchor >= 1_000_000 + t_from_s * 1e6:
            out.append(Packet(2, 0xE1, 1, len(out), first, anchor,
                              round(anchor - 15 * ECG_T), 512_000, 16, (7 << 6,) * 16))
        k += 1


def ppg_packets(spans):
    """PPG slot 1 at 100 Hz, 4 samples a packet, in [from, to) spans of seconds;
    the first packet after a hole re-anchors (bit 5)."""
    out = []
    for n, (t_from, t_to) in enumerate(spans):
        k = int(t_from * 25)
        while k < t_to * 25:
            anchor = 1_000_000 + (4 * k + 3) * 10_000
            status = 16 | (32 if n > 0 and k == int(t_from * 25) else 0)
            out.append(Packet(2, 0xF1, 1, len(out), 4 * k, anchor, anchor - 30_000,
                              100_000, status, (7,) * 4))
            k += 1
    return out


def silences(packets, logger, meta):
    stream = b"".join(encode_packet(p) for p in sorted(packets,
                                                      key=lambda p: p.t_anchor_us))
    decoded, decoder = decode_bytes(stream, 4096, (1, 2))
    result, _, _ = analyze_stream(decoded, decoder, logger, meta)
    return result, result["sessions"][0]["channel_holes"]


def kinds(found):
    return [(h["channel"], h["kind"], h["packets_inside"], h["dropped_before_seq"])
            for h in found]


def heartbeat(n, jitter_us=0):
    """0xD1 every 10 s (V0.2 section 6) from 1 s; odd ordinals ``jitter_us`` late."""
    data = device_info_data("ab" * 32, "0.2.0", "v5.5.3")
    return [Packet(2, 0xD1, 1, k, k, 1_000_000 + 10_000_000 * k + jitter_us * (k % 2),
                   1_000_000 + 10_000_000 * k + jitter_us * (k % 2), 0, 0, data)
            for k in range(n)]


def test_channels_running_the_whole_session_have_no_hole(logger, meta):
    result, found = silences(ecg_packets(0, 10) + ppg_packets([(0, 10)]), logger, meta)
    assert found == []
    assert not {"channel_silent", "channel_timing_unknown"} & set(result["issue_counts"])


def test_a_channel_that_stops_starts_late_or_pauses(logger, meta):
    result, found = silences(ecg_packets(0, 10) + ppg_packets([(0, 4)]), logger, meta)
    assert kinds(found) == [("0xF1", "ended_early", 0, False)]
    assert result["issue_counts"]["channel_silent"] == 1
    assert "channel_timing_unknown" not in result["issue_counts"]
    _, found = silences(ecg_packets(0, 10) + ppg_packets([(5, 10)]), logger, meta)
    assert kinds(found) == [("0xF1", "late_start", 0, False)]
    # SEQ numbers before the first received one are not counted: the logger may
    # have started after them.
    late = [replace(p, seq=p.seq + 7) for p in ppg_packets([(5, 10)])]
    _, found = silences(ecg_packets(0, 10) + late, logger, meta)
    assert kinds(found) == [("0xF1", "late_start", 0, False)]
    _, found = silences(ecg_packets(0, 10) + ppg_packets([(0, 3), (7, 10)]), logger,
                        meta)
    assert kinds(found) == [("0xF1", "gap", 0, False)]
    gap = found[0]
    assert 3.9e6 < gap["to_us"] - gap["from_us"] < 4.1e6


@pytest.mark.parametrize("pause_s,flagged", [(2.9, False), (3.2, True)])
def test_tolerance(logger, meta, pause_s, flagged):
    _, found = silences(ecg_packets(0, 10) + ppg_packets([(0, 3), (3 + pause_s, 10)]),
                        logger, meta)
    assert bool(found) is flagged


def test_a_channel_alive_with_bad_timestamps_has_unknown_timing(logger, meta):
    # PPG keeps sending to 10 s, but its anchors after 4 s are 0.5 s late. The
    # longer run wins and the 100 packets before it are quarantined
    # (timestamp_anomaly): alive, but with no trusted time for 4.5 s.
    ppg = [replace(p, t_anchor_us=p.t_anchor_us + 500_000,
                   t_first_us=p.t_first_us + 500_000)
           if p.t_anchor_us > 5_000_000 else p for p in ppg_packets([(0, 10)])]
    result, found = silences(ecg_packets(0, 10) + ppg, logger, meta)
    assert result["issue_counts"]["timestamp_anomaly"] == 100
    assert kinds(found) == [("0xF1", "late_start", 100, False)]
    assert result["issue_counts"]["channel_timing_unknown"] == 1
    assert "channel_silent" not in result["issue_counts"]


def test_an_untrusted_anchor_does_not_stretch_the_session(logger, meta):
    # One PPG packet with bit 0 (FIFO full: anchor unchecked) 100 s late.
    ppg = ppg_packets([(0, 10)])
    ppg[-1] = replace(ppg[-1], status=ppg[-1].status | 1,
                      t_anchor_us=ppg[-1].t_anchor_us + 100_000_000,
                      t_first_us=ppg[-1].t_first_us + 100_000_000)
    _, found = silences(ecg_packets(0, 10) + ppg, logger, meta)
    assert found == []


def test_the_device_info_heartbeat_bounds_a_single_channel(logger, meta):
    _, found = silences(ecg_packets(0, 4) + heartbeat(3, jitter_us=900_000), logger,
                        meta)
    assert kinds(found) == [("0xE1", "ended_early", 0, False)]
    assert found[0]["to_us"] == 21_000_000


def test_a_device_info_anchor_off_its_10_s_grid_is_left_out(logger, meta):
    # Reviewer's finding: one 0xD1 with a wrong timestamp (100 s late) must not
    # stretch the session and make ECG look silent; it is reported instead. A
    # lone heartbeat is compared with nothing and does not count either.
    beats = heartbeat(2)
    beats.append(replace(heartbeat(3)[2], t_anchor_us=121_000_000,
                         t_first_us=121_000_000))
    result, found = silences(ecg_packets(0, 10) + beats, logger, meta)
    assert found == []
    assert result["issue_counts"]["device_info_anchor_inconsistent"] == 1
    _, found = silences(ecg_packets(0, 4) + heartbeat(3)[2:], logger, meta)
    assert found == []
    _, found = silences(ecg_packets(0, 4) + heartbeat(3, jitter_us=1_200_000), logger,
                        meta)
    assert kinds(found) == [("0xE1", "ended_early", 0, False)]
    assert found[0]["to_us"] == 21_000_000  # 0 and 2 agree; 1 is 1.2 s off


def test_an_unchecked_last_packet_does_not_hide_a_stop(logger, meta):
    # Codex round 2, finding 3: ECG stops at 4 s, its last packet with bit 0
    # (anchor not checked). That packet shows ECG alive at some point after the
    # last trusted anchor, not until 21 s: reported, as timing unknown.
    ecg = ecg_packets(0, 4)
    ecg[-1] = replace(ecg[-1], status=ecg[-1].status | 1)
    result, found = silences(ecg + heartbeat(3), logger, meta)
    assert kinds(found) == [("0xE1", "ended_early", 1, False)]
    assert result["issue_counts"]["channel_timing_unknown"] == 1


def test_a_lone_re_anchored_packet_is_not_trusted_time(logger, meta):
    # Finding 4: PPG stops at 5 s, then sends one packet that starts a new chain
    # (bit 5) at 9.96 s; nothing checks its anchor. 100 s off, it must not stretch
    # the session (ECG would end early) nor close a PPG gap.
    ppg = ppg_packets([(0, 5), (9.96, 10)])
    assert ppg[-1].status & 32 and ppg[-2].t_anchor_us < 6_100_000
    ppg[-1] = replace(ppg[-1], t_anchor_us=ppg[-1].t_anchor_us + 100_000_000,
                      t_first_us=ppg[-1].t_first_us + 100_000_000)
    result, found = silences(ecg_packets(0, 10) + ppg, logger, meta)
    assert kinds(found) == [("0xF1", "ended_early", 1, False)]
    assert found[0]["to_us"] < 11_100_000
    assert "channel_silent" not in result["issue_counts"]


def test_a_lone_temperature_packet_is_not_trusted_time(logger, meta):
    # The 0xB1 phase window compares nothing for a single packet either. 90 s
    # late, it must not stretch the session; the channel has no trusted time.
    lone = Packet(2, 0xB1, 1, 0, 100, 101_050_000, 101_050_000, 1000, 0, (400,))
    result, found = silences(ecg_packets(0, 10) + [lone], logger, meta)
    assert kinds(found) == [("0xB1", "whole_span", 1, False)]
    assert "channel_silent" not in result["issue_counts"]


def test_a_channel_with_no_trusted_anchor_has_unknown_timing(logger, meta):
    # Every PPG packet has bit 0 (AFE FIFO overflow): samples kept, anchors never.
    ppg = [replace(p, status=p.status | 1) for p in ppg_packets([(0, 10)])]
    result, found = silences(ecg_packets(0, 10) + ppg, logger, meta)
    assert kinds(found) == [("0xF1", "whole_span", 250, False)]
    assert result["issue_counts"]["channel_timing_unknown"] == 1
    # Only SEQ 0 and 100 received: the 99 lost between them count too.
    _, found = silences(ecg_packets(0, 10) + [ppg[0], ppg[100]], logger, meta)
    assert kinds(found) == [("0xF1", "whole_span", 101, False)]


def test_packets_lost_in_a_hole_mean_unknown_timing_not_silence(logger, meta):
    # Lost after a SEQ: the SEQ gap counts them. Dropped before a SEQ: SEQ runs
    # on and the next packet has bit 1. Either way PPG was not silent.
    ppg = [p for p in ppg_packets([(0, 10)]) if not 4e6 <= p.t_anchor_us < 8e6]
    _, found = silences(ecg_packets(0, 10) + ppg, logger, meta)
    assert kinds(found) == [("0xF1", "gap", 100, False)]
    dropped = [replace(p, seq=k) for k, p in enumerate(ppg)]
    after = next(k for k, p in enumerate(dropped) if p.t_anchor_us >= 8e6)
    dropped[after] = replace(dropped[after], status=dropped[after].status | 2)
    result, found = silences(ecg_packets(0, 10) + dropped, logger, meta)
    assert kinds(found) == [("0xF1", "gap", 0, True)]
    assert result["issue_counts"]["channel_timing_unknown"] == 1
    assert "channel_silent" not in result["issue_counts"]


def test_generator_streams_are_not_checked(logger, meta):
    meta["simulation"] = {"generator": "synthetic-packet-v3", "case": "valid",
                          "config_sha256": "0" * 64, "common_index_epoch": True}
    _, found = silences(ecg_packets(0, 10) + ppg_packets([(0, 4)]), logger, meta)
    assert found is None


def test_packets_inside_counts_seq_numbers_lost_at_either_end(logger, meta):
    # ECG stops at 4 s; after its last trusted packet two are lost and one with
    # bit 0 arrives: three SEQ numbers inside the hole, not one.
    ecg = ecg_packets(0, 4)
    ecg[-1] = replace(ecg[-1], status=ecg[-1].status | 1, seq=ecg[-1].seq + 2)
    _, found = silences(ecg + heartbeat(3), logger, meta)
    assert kinds(found) == [("0xE1", "ended_early", 3, False)]
    # PPG starts with a bit-0 packet, two lost, then trusted packets from 5 s.
    ppg = ppg_packets([(5, 10)])
    ppg = [replace(p, seq=p.seq + 3) for p in ppg]
    ppg.insert(0, replace(ppg_packets([(0, 1)])[0], status=16 | 1))
    _, found = silences(ecg_packets(0, 10) + ppg, logger, meta)
    assert kinds(found) == [("0xF1", "late_start", 3, False)]
