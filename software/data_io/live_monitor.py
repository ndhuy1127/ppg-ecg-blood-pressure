"""Operator messages while ``packet_logger.py record`` runs (review of 2026-11-07).

Pure code: decoded packets in, text lines out through ``notify(text)``; the clock
is passed in. Nothing here changes the raw stream, its decode or any output
file. These are live hints for the operator; ``decode.json`` stays the record.

- MAX30101 LED codes from ``0xD2`` (Packet Schema V0.2 section 12): each new
  configured chip state is shown, and with ``ppg_led_lock`` in the session
  metadata the monitor says when the locked codes take effect and warns at once
  when a later state has other codes (after the session ``decode.json`` reports
  the same as ``ppg_led_lock_mismatch``). The periodic repeats of one state are
  shown once.
- With ``remind`` (``record --commands``) and a lock: at each new SESSION_ID a
  reminder to send the locked codes, since an MCU restart boots with defaults.
- PPG DC level for the LED procedure of protocol 6.1 (``dc_every_s``): per
  colour, the mean of the last ``dc_window_s`` seconds of samples in percent of
  the ADC full scale (2^18 codes), the samples at the ADC ceiling and the packets
  with STATUS bit 6 (ALC overflow), every ``dc_every_s`` seconds of PC time. The
  window restarts when the MAX30101 gets a new configuration (a SET_PPG_LED),
  when a PPG packet re-anchors (bit 5, also on a
  packet with FS 0), when its sample index does not follow on (packets lost),
  and when the SESSION_ID changes, so it only holds contiguous samples taken with
  the current LED codes. A colour with no new sample for ``DC_STALE_S`` seconds
  of PC time is shown as STALE, not as a current level. Once 0xD2 says the
  MAX30101 is not running (fake source or not configured), no DC is kept or
  shown until a running chip state comes again.
"""

from collections import deque

from software.data_io.packet_receiver import LED_REGISTERS, decode_afe_config
from software.data_io.packet_wire import AFE_CONFIG_CHANNEL, PPG_CHANNELS

ADC_FULL_SCALE = 1 << 18  # MAX30101 18-bit ADC codes, left-justified (p. 15-16)
# Protocol 6.1 (2026-10-25): DC between 30 and 70 % of the ADC full scale
# (a technical proposal, no source yet).
DC_RANGE_PERCENT = (30, 70)
ALC_OVERFLOW_BIT = 1 << 6
REANCHOR_BIT = 1 << 5
# PPG packets come about every 80 ms; a second with none means the stream stopped.
DC_STALE_S = 1.0
UINT32 = 1 << 32
# MULTI_LED_CTRL SLOTx codes (datasheet p. 21): LED1 red, LED2 IR, LED3 green
# (the V1 board drives LED3 and LED4 together in that slot).
SLOT_COLORS = {1: "red", 2: "ir", 3: "green"}
SPO2_CONFIG, MULTI_LED1, MULTI_LED2 = "0x0A", "0x11", "0x12"


def led_codes(registers):
    """``{"red", "ir", "green_led3", "green_led4"}`` of a MAX30101 register image."""
    return {name: int(registers[address], 16) for name, address in LED_REGISTERS.items()}


def _show_codes(codes):
    green = (f"0x{codes['green_led3']:02X}" if codes["green_led3"] == codes["green_led4"]
             else f"0x{codes['green_led3']:02X}/0x{codes['green_led4']:02X}")
    return f"green {green}, red 0x{codes['red']:02X}, ir 0x{codes['ir']:02X}"


def slot_colors(registers):
    """PPG channel -> colour from MULTI_LED_CTRL1/2 (0x11, 0x12)."""
    words = int(registers[MULTI_LED1], 16), int(registers[MULTI_LED2], 16)
    slots = (words[0] & 7, words[0] >> 4 & 7, words[1] & 7, words[1] >> 4 & 7)
    return {channel: SLOT_COLORS.get(code, f"slot{n + 1}")
            for n, (channel, code) in enumerate(zip(PPG_CHANNELS, slots))}


def adc_ceiling(registers):
    """Highest code of the ADC at the configured resolution (SPO2_CONFIG LED_PW):
    left-justified, so 17 bits end at 0x3FFFE and 18 bits at 0x3FFFF."""
    bits = 15 + (int(registers[SPO2_CONFIG], 16) & 3)
    return (ADC_FULL_SCALE - 1) & ~((1 << (18 - bits)) - 1)


class LiveMonitor:
    def __init__(self, notify, clock, lock=None, remind=None, dc_every_s=None,
                 dc_window_s=10.0):
        """``lock``: ``ppg_led_lock`` of the session metadata or None.
        ``remind(session_id)``: the reminder text at a new SESSION_ID, or None.
        ``dc_every_s``: seconds between DC lines, None for no DC lines."""
        if dc_every_s is not None and not dc_every_s > 0:
            raise ValueError("dc_every_s must be > 0")
        if not dc_window_s > 0:
            raise ValueError("dc_window_s must be > 0")
        self.notify, self.clock, self.remind = notify, clock, remind
        self.lock = None if lock is None else {
            "red": lock["red"], "ir": lock["ir"], "green_led3": lock["green"],
            "green_led4": lock["green"]}
        self.dc_every_s, self.dc_window_s = dc_every_s, dc_window_s
        self.session_id, self.state, self.applied = None, None, False
        self.running = None  # MAX30101 running per 0xD2: None until one says
        self._unknown_config()
        self.next_dc = None

    def _unknown_config(self):
        """No MAX30101 state known (yet): slot names, a ceiling that fits 17 and 18
        bits, and no DC window."""
        self.colors = {channel: f"slot{n + 1}" for n, channel in enumerate(PPG_CHANNELS)}
        self.ceiling = ADC_FULL_SCALE - 2
        self.windows = {}

    def observe(self, packets):
        """Decoded packets of the last read, in stream order."""
        for packet in packets:
            if packet.session_id != self.session_id:
                self.session_id, self.state, self.applied = packet.session_id, None, False
                self.running = None
                self._unknown_config()
                if self.remind is not None:
                    self.notify(self.remind(packet.session_id))
            if packet.channel_id == AFE_CONFIG_CHANNEL:
                self._afe_config(packet)
            elif packet.channel_id in PPG_CHANNELS and self.dc_every_s is not None:
                self._dc(packet)

    def _afe_config(self, packet):
        config, problem = decode_afe_config(packet)
        if problem is not None or config["afe"] != "MAX30101":
            return
        generation = config["generation"]
        if config["source"] != "chip" or not config["configured"]:
            state = ("not running", config["source"], config["configured"], generation)
            self.running = False
            self._unknown_config()
            if state != self.state:
                self.state = state
                self.notify(f"WARNING: MAX30101 not running with its chip (source "
                            f"{config['source']}, configured {config['configured']}; "
                            f"SESSION_ID {self.session_id}, generation {generation}); "
                            "PPG DC is not meaningful until it runs again")
            return
        registers = config["registers"]
        self.running = True
        codes, generation = led_codes(registers), config["generation"]
        if (generation, codes) == self.state:
            return
        self.state = (generation, codes)
        self.colors, self.ceiling = slot_colors(registers), adc_ceiling(registers)
        self.windows = {}
        where = f"SESSION_ID {self.session_id}, generation {generation}"
        if self.lock is None:
            self.notify(f"MAX30101 LED codes now {_show_codes(codes)} ({where})")
        elif codes == self.lock:
            self.notify(("MAX30101 reconfigured with the locked LED codes" if self.applied
                         else "Locked LED codes in effect: measurement may start")
                        + f" ({where})")
            self.applied = True
        elif self.applied:
            self.notify(f"WARNING: MAX30101 LED codes {_show_codes(codes)} differ from "
                        f"the locked {_show_codes(self.lock)} ({where}); protocol "
                        "deviation, decode.json will report ppg_led_lock_mismatch")
        else:
            self.notify(f"MAX30101 LED codes now {_show_codes(codes)}, not yet the "
                        f"locked {_show_codes(self.lock)} ({where})")

    def _dc(self, packet):
        # A re-anchor restarts the window even on a packet whose FS 0 makes its
        # samples unusable here (the receiver carries bit 5 over such packets too).
        if packet.status & REANCHOR_BIT:
            self.windows.pop(packet.channel_id, None)
        if packet.fs_nominal_mhz == 0 or self.running is False:
            return
        window = self.windows.get(packet.channel_id)
        if window is not None and (
            window["fs_mhz"] != packet.fs_nominal_mhz
            or window["next_index"] != packet.first_sample_index
        ):
            window = None  # another rate, or samples lost or repeated: start again
        if window is None:
            window = self.windows[packet.channel_id] = {
                "blocks": deque(), "n": 0, "total": 0, "peak": 0, "ceiling": 0,
                "alc": 0, "fs_mhz": packet.fs_nominal_mhz}
        window["next_index"] = (packet.first_sample_index + len(packet.data)) % UINT32
        window["last_pc"] = self.clock()
        values = tuple(packet.data)
        block = (len(values), sum(values), max(values),
                 sum(value >= self.ceiling for value in values),
                 1 if packet.status & ALC_OVERFLOW_BIT else 0)
        window["blocks"].append(block)
        for name, value in zip(("n", "total", "ceiling", "alc"), block[:2] + block[3:]):
            window[name] += value
        target = max(1, round(packet.fs_nominal_mhz * self.dc_window_s / 1000))
        blocks = window["blocks"]
        while window["n"] - blocks[0][0] >= target:
            old = blocks.popleft()
            for name, value in zip(("n", "total", "ceiling", "alc"), old[:2] + old[3:]):
                window[name] -= value
        window["peak"] = max(b[2] for b in blocks)

    def dc_line(self):
        """The DC text of the current windows, or None if none has samples."""
        parts, ceiling, alc, short = [], [], [], None
        low, high = DC_RANGE_PERCENT
        now = self.clock()
        for channel in PPG_CHANNELS:
            window = self.windows.get(channel)
            if not window:
                continue
            color = self.colors[channel]
            quiet = now - window["last_pc"]
            if quiet > DC_STALE_S:
                parts.append(f"{color} STALE (no sample for {quiet:.0f} s)")
                continue
            # Flags follow the value shown (0.1 %), so "30.0" is never LOW.
            mean = round(100 * window["total"] / window["n"] / ADC_FULL_SCALE, 1)
            peak = 100 * window["peak"] / ADC_FULL_SCALE
            flag = " LOW" if mean < low else " HIGH" if mean > high else ""
            parts.append(f"{color} {mean:.1f}{flag} (max {peak:.1f})")
            if window["ceiling"]:
                share = 100 * window["ceiling"] / window["n"]
                ceiling.append(f"{color} {window['ceiling']} ({share:.1f} %)")
            if window["alc"]:
                alc.append(f"{color} {window['alc']}")
            seconds = window["n"] * 1000 / window["fs_mhz"]
            if seconds < self.dc_window_s - 1e-9:
                short = seconds if short is None else min(short, seconds)
        if not parts:
            return None
        span = (f"last {self.dc_window_s:g} s" if short is None
                else f"only {short:.1f} of {self.dc_window_s:g} s so far")
        return (f"PPG DC, % of ADC full scale ({span}; range {low}-{high}): "
                + " | ".join(parts)
                + f" | samples at ceiling: {', '.join(ceiling) or 'none'}"
                + f" | ALC overflow packets: {', '.join(alc) or 'none'}")

    def tick(self):
        """Call often (after every read); writes a DC line when one is due."""
        if self.dc_every_s is None:
            return
        now = self.clock()
        if self.next_dc is None:
            self.next_dc = now + self.dc_every_s
        if now < self.next_dc:
            return
        self.next_dc = now + self.dc_every_s
        line = self.dc_line()
        if line is not None:
            self.notify(line)
