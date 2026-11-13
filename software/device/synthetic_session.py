"""SYNTHETIC ECG + PPG device sessions with a known PAT (Packet Schema V0.2).

Unlike ``packet_simulation_v3`` (random payloads), this builds waveforms:

- R peaks are narrow Gaussians on the ECG; each PPG pulse starts at R + PAT with a
  linear upstroke, so the maximum-upslope tangent of ``fiducials.ppg_fiducials``
  meets the valley level exactly at the set onset (no shape bias in the answer);
- every channel has its own sample clock: the true rate is the nominal rate times
  (1 + ppm 1e-6), and the sample times of the AFE never meet those of another AFE;
- packet anchors follow Packet Schema V0.1 section 5: ``T_ANCHOR_US`` = true time
  of the last sample + latency + a uniform delay in [0, jitter), on the MCU clock;
- the three PPG slots share ``FIRST_SAMPLE_INDEX`` and ``T_ANCHOR_US``, and slot j is
  emitted (j - 1) x the LED spacing of ``LED_PW`` later (schema section 7);
- one MAX30101 ``0xD2`` state gives the LED pulse width, slots and LED codes.

Pure code: returns bytes and metadata, no file I/O. Results only verify code.
"""

import hashlib
import json
from dataclasses import asdict, dataclass

import numpy as np

from software.data_io.packet_wire import (
    AFE_CONFIG_CHANNEL, AFES, ECG_CHANNEL, EVENT_CHANNEL, WIRE_VERSION_V02, Packet,
    encode_packet,
)

VERSION = "synthetic-device-session-v1"
# MAX30101 LED_PW code -> spacing between rising edges of consecutive slots, us
# (Packet Schema V0.1 section 7: MAX30101 p. 22, Table 11).
SLOT_SPACING_US = {0: 427, 1: 525, 2: 720, 3: 1107}
PPG_SLOTS = {0xF1: "green", 0xF2: "red", 0xF3: "ir"}  # V1 (schema section 7)
ECG_SCALE = 30000.0  # ADC codes per unit of the synthetic ECG
PPG_DC, PPG_AC = 100000.0, 20000.0


@dataclass(frozen=True)
class SessionSpec:
    """One synthetic recording; every field is a simulation parameter."""

    duration_s: float = 60.0
    hr_bpm: float = 70.0
    # Piecewise-linear PAT (ms) over beat time (s): ((t0, pat0), (t1, pat1), ...).
    pat_profile: tuple = ((0.0, 200.0),)
    ecg_fs_hz: float = 512.0
    ppg_fs_hz: float = 200.0
    ecg_clock_ppm: float = 0.0
    ppg_clock_ppm: float = 0.0
    ecg_latency_us: int = 20839
    ppg_latency_us: int = 1500
    anchor_jitter_us: int = 200
    ecg_packet_samples: int = 16
    ppg_packet_samples: int = 8
    start_us: int = 1_000_000
    ppg_start_offset_us: int = 1234  # PPG sampling phase vs ECG
    led_pw_code: int = 3
    missed_ppg_beats: tuple = ()  # beat numbers with an R but no PPG pulse
    noisy_spans_s: tuple = ()  # ((start, end), ...) of heavy PPG noise
    noise_sd: float = 0.6  # in units of the pulse amplitude, inside noisy spans
    ecg_noise_sd: float = 0.005
    ppg_noise_sd: float = 0.002
    events: tuple = ()  # ((code, time_s), ...); time from the session start
    drop_packets: tuple = ()  # (("0xF1", seq), ...): lost on USB
    session_id: int = 1
    seed: int = 20261113


def pat_at(spec, t_s):
    """PAT in ms at beat time ``t_s`` (piecewise linear, constant outside)."""
    points = np.asarray(spec.pat_profile, dtype=float)
    return np.interp(t_s, points[:, 0], points[:, 1])


def beat_times(spec):
    """R-peak times (s from the session start) of every beat."""
    rr = 60.0 / spec.hr_bpm
    return np.arange(0.5, spec.duration_s - 0.5, rr)


def _ecg(t, beats, rng, spec):
    values = np.zeros_like(t)
    for r in beats:
        near = np.abs(t - r) < 0.05
        values[near] += np.exp(-0.5 * ((t[near] - r) / 0.008) ** 2)
    values += rng.normal(0, spec.ecg_noise_sd, t.shape)
    codes = np.clip(np.round(values * ECG_SCALE), -(1 << 17), (1 << 17) - 1).astype(int)
    return (codes & 0x3FFFF) << 6  # MAX30001 word: 18-bit sample, ETAG 000, PTAG 000


def _pulse(dt):
    """Unit pulse: linear rise over 0.1 s, cosine decay to 0 over 0.35 s."""
    rise, fall = 0.1, 0.35
    out = np.zeros_like(dt)
    up = (dt >= 0) & (dt < rise)
    out[up] = dt[up] / rise
    down = (dt >= rise) & (dt < rise + fall)
    out[down] = 0.5 * (1 + np.cos(np.pi * (dt[down] - rise) / fall))
    return out


def _ppg(t, feet, rng, spec, gain):
    values = np.zeros_like(t)
    for foot in feet:
        values += _pulse(t - foot)
    noise = np.full(t.shape, spec.ppg_noise_sd)
    for start, end in spec.noisy_spans_s:
        noise[(t >= start) & (t < end)] = spec.noise_sd
    values = values + rng.normal(0, 1, t.shape) * noise
    counts = PPG_DC + gain * PPG_AC * values
    return np.clip(np.round(counts), 0, (1 << 18) - 1).astype(int)


def _anchor(rng, true_last_s, spec, latency_us):
    jitter = rng.uniform(0, spec.anchor_jitter_us) if spec.anchor_jitter_us else 0.0
    return int(round(spec.start_us + true_last_s * 1e6 + latency_us + jitter))


def _data_packets(rng, channel_ids, values, times_s, fs_hz, spec, latency_us, per):
    """(t_anchor, Packet) of one AFE; channels share index and anchor."""
    out = []
    count = len(times_s)
    for n, first in enumerate(range(0, count - per + 1, per)):
        anchor = _anchor(rng, times_s[first + per - 1], spec, latency_us)
        t_first = anchor - int(round((per - 1) * 1e6 / fs_hz))
        for channel_id, series in zip(channel_ids, values):
            data = tuple(int(v) for v in series[first:first + per])
            out.append((anchor, Packet(WIRE_VERSION_V02, channel_id, spec.session_id, n,
                                       first, anchor, t_first, int(fs_hz * 1000), 0,
                                       data)))
    return out


def _max30101_state(spec, anchor):
    """MAX30101 0xD2 (section 12): multi-LED, ADC 16384 nA, 200 sps, LED_PW."""
    values = {0x08: 0x10, 0x0A: (3 << 5) | (2 << 2) | spec.led_pw_code,
              0x0C: 40, 0x0D: 44, 0x0E: 18, 0x0F: 18, 0x11: 0x13, 0x12: 0x02,
              0x02: 0x40, 0x03: 0x00, 0x09: 0x07}
    words = tuple((address << 24) | values[address] for address in AFES[2][2])
    data = (1, 2, 1, 1, 1, *words)
    return Packet(WIRE_VERSION_V02, AFE_CONFIG_CHANNEL, spec.session_id, 0, 0, anchor,
                  anchor, 0, 0, data)


def generate(spec: SessionSpec):
    """``(stream_bytes, metadata, truth)`` of one synthetic recording.

    ``truth`` holds the set R times, foot times and PAT of every beat on the MCU
    clock (us), and the true sample rates."""
    rng = np.random.default_rng(spec.seed)
    beats = beat_times(spec)
    pats = pat_at(spec, beats)
    feet = beats + pats / 1000
    missed = set(spec.missed_ppg_beats)
    ppg_feet = np.array([f for i, f in enumerate(feet) if i not in missed])

    ecg_fs = spec.ecg_fs_hz * (1 + spec.ecg_clock_ppm * 1e-6)
    ppg_fs = spec.ppg_fs_hz * (1 + spec.ppg_clock_ppm * 1e-6)
    t_ecg = np.arange(int(spec.duration_s * ecg_fs)) / ecg_fs
    t_ppg = spec.ppg_start_offset_us * 1e-6 + np.arange(
        int((spec.duration_s - 0.01) * ppg_fs)) / ppg_fs
    spacing_s = SLOT_SPACING_US[spec.led_pw_code] * 1e-6
    ppg = [_ppg(t_ppg + j * spacing_s, ppg_feet, rng, spec, gain)
           for j, gain in enumerate((1.0, 0.8, 0.9))]

    rows = _data_packets(rng, (ECG_CHANNEL,), [_ecg(t_ecg, beats, rng, spec)], t_ecg,
                         spec.ecg_fs_hz, spec, spec.ecg_latency_us,
                         spec.ecg_packet_samples)
    rows += _data_packets(rng, tuple(PPG_SLOTS), ppg, t_ppg, spec.ppg_fs_hz, spec,
                          spec.ppg_latency_us, spec.ppg_packet_samples)
    rows.append((spec.start_us - 1, _max30101_state(spec, spec.start_us - 1)))
    for ordinal, (code, time_s) in enumerate(spec.events):
        anchor = int(round(spec.start_us + time_s * 1e6))
        rows.append((anchor, Packet(WIRE_VERSION_V02, EVENT_CHANNEL, spec.session_id,
                                    ordinal, ordinal, anchor, anchor, 0, 0, (code,))))
    dropped = {(int(key, 16), seq) for key, seq in spec.drop_packets}
    rows.sort(key=lambda row: (row[0], row[1].channel_id))
    stream = b"".join(encode_packet(p) for _, p in rows
                      if (p.channel_id, p.seq) not in dropped)
    truth = {
        "r_us": (spec.start_us + beats * 1e6).tolist(),
        "foot_us": (spec.start_us + feet * 1e6).tolist(),
        "pat_ms": pats.tolist(),
        "missed_ppg_beats": sorted(missed),
        "ecg_fs_true_hz": ecg_fs, "ppg_fs_true_hz": ppg_fs,
        "slot_spacing_us": SLOT_SPACING_US[spec.led_pw_code],
    }
    return stream, metadata(spec), truth


def spec_sha256(spec):
    payload = json.dumps(asdict(spec), sort_keys=True, default=list).encode()
    return hashlib.sha256(payload).hexdigest()


def metadata(spec):
    """``packet-session-metadata-v0`` with the latencies the generator used.

    The declared latency is the expected anchor delay (latency + jitter / 2),
    as the effective latency L of schema section 5.3."""
    reasons = {name: "SYNTHETIC generator; no firmware or operator"
               for name in ("firmware_version", "firmware_commit", "operator",
                            "electrode_type", "electrode_placement")}
    half = spec.anchor_jitter_us // 2
    channels = {}
    for key, fs, latency in (("0xE1", spec.ecg_fs_hz, spec.ecg_latency_us),
                             *((f"0x{c:02X}", spec.ppg_fs_hz, spec.ppg_latency_us)
                               for c in PPG_SLOTS)):
        channels[key] = {"sensor": "SYNTHETIC", "fs_nominal_mhz": int(fs * 1000),
                         "latency_l_us": int(latency + half),
                         "latency_source": f"SYNTHETIC: {VERSION} parameter",
                         "unit_conversion": None, "afe_config": None}
        reasons[f"channels.{key}.unit_conversion"] = "synthetic integers"
        reasons[f"channels.{key}.afe_config"] = "no AFE in simulation"
    channels["0xC1"] = {"sensor": "SYNTHETIC_EVENT", "fs_nominal_mhz": None,
                        "latency_l_us": None, "latency_source": None,
                        "unit_conversion": None, "afe_config": None}
    for name in ("fs_nominal_mhz", "latency_l_us", "latency_source", "unit_conversion",
                 "afe_config"):
        reasons[f"channels.0xC1.{name}"] = "event packets have no samples"
    return {
        "schema_version": "packet-session-metadata-v0", "source_type": "SYNTHETIC",
        "clock_id": "SYN_ESP_TIMER_US", "firmware_version": None,
        "firmware_commit": None, "device_id": "SYN_DEVICE_001", "operator": None,
        "electrode_type": None, "electrode_placement": None, "channels": channels,
        "simulation": {"generator": VERSION, "case": "waveform",
                       "config_sha256": spec_sha256(spec),
                       "common_index_epoch": False},
        "null_reasons": dict(sorted(reasons.items())),
    }
