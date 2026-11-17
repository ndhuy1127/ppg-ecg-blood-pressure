"""Operator lines while recording (review of 2026-11-07), SYNTHETIC only.

Answers come from Packet Schema V0.2 section 12 (0xD2 register image of the
MAX30101), the MAX30101 datasheet (MULTI_LED slots: 1 red, 2 IR, 3 green;
SPO2_CONFIG LED_PW 2 = 17 bits, 3 = 18 bits, left-justified) and protocol 6.1
(DC 30-70 % of the ADC full scale, mean over 10 s).
"""

import json
from pathlib import Path

import pytest

from scripts.packet_logger import record
from software.data_io.live_monitor import LiveMonitor, adc_ceiling, slot_colors
from software.data_io.packet_simulation_v3 import session_metadata
from software.data_io.packet_wire import Packet, encode_packet

ROOT = Path(__file__).resolve().parents[1]
LOGGER_CONFIG = ROOT / "configs/hardware/packet_logger.json"
SIM_V02 = ROOT / "configs/hardware/packet_simulation_v3_v02.json"
PPG_REGS = (0x08, 0x0A, 0x0C, 0x0D, 0x0E, 0x0F, 0x11, 0x12, 0x02, 0x03, 0x09)
LOCK = {"green": 18, "red": 40, "ir": 44, "outside_dc_range": []}
FULL = 1 << 18
# SLOT1 green, SLOT2 red, SLOT3 IR (firmware/include/max30101.h).
V1_SLOTS = {0x11: (1 << 4) | 3, 0x12: 2}


def max30101(generation, red=0x24, ir=0x24, green=0x12, green4=None, pulse=3,
             session=1, seq=0):
    values = {0x0A: 0x60 | pulse, 0x0C: red, 0x0D: ir, 0x0E: green,
              0x0F: green if green4 is None else green4, **V1_SLOTS}
    regs = tuple((a << 24) | values.get(a, 0) for a in PPG_REGS)
    t = 1_000_000 + seq
    return Packet(2, 0xD2, session, seq, seq, t, t, 0, 0, (1, 2, 1, 1, generation, *regs))


def ppg(channel, values, session=1, status=0, seq=0, index=None, fs=200_000):
    """A PPG packet; by default its sample index follows on from packet seq - 1."""
    first = len(values) * seq if index is None else index
    return Packet(2, channel, session, seq, first, 1_000_000, 1_000_000, fs, status,
                  tuple(values))


class Clock:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t


def monitor(**kw):
    lines, clock = [], Clock()
    m = LiveMonitor(lines.append, clock, **kw)
    m.lines, m.clk = lines, clock
    return m


def test_register_helpers():
    regs = {f"0x{a:02X}": f"0x{v:02X}" for a, v in
            {0x0A: 0x63, 0x11: 0x13, 0x12: 0x02}.items()}
    assert slot_colors(regs) == {0xF1: "green", 0xF2: "red", 0xF3: "ir", 0xF4: "slot4"}
    assert adc_ceiling(regs) == FULL - 1
    regs["0x0A"] = "0x62"  # 215 us, 17 bits: the last bit is always 0
    assert adc_ceiling(regs) == FULL - 2


def test_led_states_without_a_lock_are_shown_once_each():
    m = monitor()
    m.observe([max30101(1), max30101(1, seq=1)])  # 0xD2 repeats every 10 s
    m.observe([max30101(2, red=0x2C)])
    assert m.lines == [
        "MAX30101 LED codes now green 0x12, red 0x24, ir 0x24 (SESSION_ID 1, "
        "generation 1)",
        "MAX30101 LED codes now green 0x12, red 0x2C, ir 0x24 (SESSION_ID 1, "
        "generation 2)"]


def test_lock_in_effect_then_a_mismatch_is_a_warning_at_once():
    m = monitor(lock=LOCK)
    m.observe([max30101(1)])  # boot defaults: not reported as a mismatch
    assert "not yet the locked" in m.lines[-1]
    m.observe([max30101(2, red=40, ir=44, green=18)])
    assert m.lines[-1].startswith("Locked LED codes in effect: measurement may start")
    m.observe([max30101(2, red=40, ir=44, green=18, seq=1)])
    assert len(m.lines) == 2
    m.observe([max30101(3, red=40, ir=44, green=18, green4=20)])
    assert m.lines[-1].startswith("WARNING: MAX30101 LED codes green 0x12/0x14, red "
                                  "0x28, ir 0x2C differ from the locked")
    # A new SESSION_ID (MCU restart) starts over, with the reminder.
    m.remind = lambda session: f"SESSION_ID {session}: send the locked LED codes"
    m.observe([max30101(1, session=2)])
    assert m.lines[-2:] == ["SESSION_ID 2: send the locked LED codes",
                            "MAX30101 LED codes now green 0x12, red 0x24, ir 0x24, "
                            "not yet the locked green 0x12, red 0x28, ir 0x2C "
                            "(SESSION_ID 2, generation 1)"]


def test_dc_mean_flags_ceiling_and_alc_per_colour():
    m = monitor(dc_every_s=2.0, dc_window_s=1.0)
    m.observe([max30101(1)])
    for k in range(13):  # 16 samples per packet at 200 Hz: 1.04 s
        m.observe([ppg(0xF1, [FULL // 2] * 16, seq=k),
                   ppg(0xF2, [FULL * 4 // 5] * 15 + [FULL - 1], seq=k),
                   ppg(0xF3, [FULL // 5] * 16, seq=k, status=1 << 6 if k == 3 else 0)])
    line = m.dc_line()
    assert line.startswith("PPG DC, % of ADC full scale (last 1 s; range 30-70): ")
    assert "green 50.0 (max 50.0)" in line and "ir 20.0 LOW (max 20.0)" in line
    assert "red 81.2 HIGH (max 100.0)" in line  # (15 * 0.8 + 1) / 16
    assert "samples at ceiling: red 13" in line
    assert "ALC overflow packets: ir 1" in line


def test_dc_window_keeps_only_the_last_seconds_and_restarts_on_new_codes():
    m = monitor(dc_every_s=1.0, dc_window_s=1.0)
    m.observe([max30101(1)])
    for k in range(25):  # 2 s at 10 %
        m.observe([ppg(0xF1, [FULL // 10] * 16, seq=k)])
    for k in range(13):  # then 1.04 s at 40 %: the window holds only these
        m.observe([ppg(0xF1, [FULL * 2 // 5] * 16, seq=25 + k)])
    assert "green 40.0 (max 40.0)" in m.dc_line()
    m.observe([max30101(2, green=0x16)])  # new codes: start again
    assert m.dc_line() is None
    m.observe([ppg(0xF1, [FULL * 3 // 5] * 16)])
    assert "only 0.1 of 1 s so far" in m.dc_line() and "green 60.0" in m.dc_line()
    m.observe([ppg(0xF1, [FULL // 2] * 16, status=1 << 5)])  # chip re-anchored
    assert "green 50.0" in m.dc_line()


def test_dc_lines_come_every_dc_every_s_of_pc_time():
    m = monitor(dc_every_s=2.0, dc_window_s=1.0)
    m.tick()
    for seq, t in enumerate((1.0, 1.9, 2.0, 3.0, 4.1)):
        m.clk.t = t
        m.observe([ppg(0xF1, [FULL // 2] * 16, seq=seq)])
        m.tick()
    assert len(m.lines) == 2 and all(line.startswith("PPG DC") for line in m.lines)
    assert "slot1 50.0" in m.lines[0]  # no 0xD2 yet: slot names


def test_a_stopped_ppg_stream_is_stale_not_a_current_level():
    # Review of 2026-11-07: the last window was shown as current after PPG stopped.
    m = monitor(dc_every_s=1.0, dc_window_s=1.0)
    for k in range(13):
        m.observe([ppg(0xF1, [FULL // 2] * 16, seq=k)])
    assert "slot1 50.0" in m.dc_line()
    m.clk.t = 100.0
    assert "slot1 STALE (no sample for 100 s)" in m.dc_line()
    assert "50.0" not in m.dc_line()


def test_lost_packets_restart_the_window():
    m = monitor(dc_every_s=1.0, dc_window_s=1.0)
    for k in range(13):
        m.observe([ppg(0xF1, [FULL // 10] * 16, seq=k)])
    # Sample index jumps by 160 (ten packets lost): only the new samples count.
    m.observe([ppg(0xF1, [FULL // 2] * 16, seq=23)])
    assert "only 0.1 of 1 s so far" in m.dc_line() and "slot1 50.0" in m.dc_line()


def test_a_reanchor_on_a_packet_with_fs_0_still_restarts_the_window():
    # Review of 2026-11-07: 10 % before, bit 5 on a packet with FS 0, then 60 %.
    m = monitor(dc_every_s=1.0, dc_window_s=1.0)
    for k in range(13):
        m.observe([ppg(0xF1, [FULL // 10] * 16, seq=k)])
    m.observe([ppg(0xF1, [0] * 16, seq=13, status=1 << 5, fs=0)])
    m.observe([ppg(0xF1, [FULL * 3 // 5] * 16, seq=14, index=0)])
    assert "slot1 60.0" in m.dc_line()


def test_max30101_not_running_and_a_new_session_forget_the_old_configuration():
    m = monitor(dc_every_s=1.0, dc_window_s=1.0)
    m.observe([max30101(1, pulse=2)])
    m.observe([ppg(0xF1, [FULL // 2] * 16)])
    assert "green 50.0" in m.dc_line()
    stopped = Packet(2, 0xD2, 1, 1, 1, 1_000_001, 1_000_001, 0, 0, (1, 2, 1, 0, 1))
    m.observe([stopped, stopped])
    assert m.lines[-1].startswith("WARNING: MAX30101 not running with its chip "
                                  "(source chip, configured False")
    assert len(m.lines) == 2 and m.dc_line() is None
    # Review round 2: PPG while the chip is not running is not shown, also after a
    # repeat of the same 0xD2.
    m.observe([ppg(0xF1, [FULL // 2] * 16, seq=1)])
    m.observe([stopped, ppg(0xF1, [FULL // 2] * 16, seq=2)])
    assert m.dc_line() is None and len(m.lines) == 2
    m.observe([max30101(1)])  # running again
    m.observe([ppg(0xF2, [FULL - 2] * 16, session=1)])
    assert "red 100.0" in m.dc_line() and "samples at ceiling: none" in m.dc_line()
    # A new SESSION_ID: no colour names or 18-bit ceiling from the old session.
    m.observe([ppg(0xF2, [FULL - 2] * 16, session=2)])
    assert "slot2 100.0" in m.dc_line()
    assert "samples at ceiling: slot2 16 (100.0 %)" in m.dc_line()


def test_bad_settings_are_refused():
    with pytest.raises(ValueError):
        monitor(dc_every_s=0)
    with pytest.raises(ValueError):
        monitor(dc_every_s=1.0, dc_window_s=0)


class Device:
    """V0.2 packets, one per read, 0.05 s of PC time per read: a MAX30101 0xD2
    with the locked codes, then PPG on three slots."""

    def __init__(self, reads=120):
        self.now, self.out = 0.0, [encode_packet(max30101(1, red=40, ir=44, green=18))]
        for k in range(reads):
            for slot, level in ((0xF1, 2), (0xF2, 3), (0xF3, 4)):
                anchor = 1_000_000 + (16 * k + 15) * 5_000
                self.out.append(encode_packet(Packet(
                    2, slot, 1, k, 16 * k, anchor, anchor - 75_000, 200_000, 0,
                    (FULL * level // 10,) * 16)))

    def read(self, n):
        self.now += 0.05
        return self.out.pop(0) if self.out else b""


def test_record_shows_lock_and_dc_lines(tmp_path):
    sim = json.loads(SIM_V02.read_bytes())
    meta = session_metadata(sim, "valid", "0" * 64)
    meta["schema_version"] = "packet-session-metadata-v1"
    meta.update(subject_id=None, session_id=None, ppg_led_lock=LOCK, cuff_log=None)
    meta["channels"] = {k: v for k, v in meta["channels"].items()
                        if k in ("0xF1", "0xF2", "0xF3")}
    meta["null_reasons"] = {
        **{n: r for n, r in meta["null_reasons"].items()
           if not n.startswith("channels.") or n.split(".")[1] in meta["channels"]},
        "subject_id": "test", "session_id": "test", "cuff_log": "test"}
    path = tmp_path / "meta.json"
    path.write_text(json.dumps(meta), encoding="utf-8")
    device, lines = Device(), []
    record(device, tmp_path / "rec", LOGGER_CONFIG, path, ROOT, "device",
           clock=lambda: device.now, notify=lines.append, dc_every_s=5.0,
           dc_window_s=10.0)
    assert lines[0].startswith("Locked LED codes in effect")
    dc = [line for line in lines if line.startswith("PPG DC")]
    assert len(dc) >= 3
    assert "green 20.0 LOW" in dc[-1] and "red 30.0 (max" in dc[-1]
    assert "ir 40.0 (max" in dc[-1]
    assert "only" in dc[0]
