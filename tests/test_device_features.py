"""Device-rate fiducials, PAT and SQI flags on SYNTHETIC recordings with known PAT.

ECG 512 sps, PPG 200 sps (three slots), each channel on its own clock and
timestamps; the generator's PPG upstroke is linear, so the tangent foot equals the
set onset and the PAT error left is the R-peak quantization (half an ECG period,
0.98 ms) plus the anchor fit (tens of us).
"""

import json

import numpy as np
import pytest

from software.device import features as fe
from software.device import session_ingest as si
from software.device.synthetic_session import SessionSpec
from tests.device_fixtures import DEVICE_CONFIG, make_recording

CONFIG = json.loads(DEVICE_CONFIG.read_text())
ECG_HALF_PERIOD_MS = 0.5 / 512 * 1000
FIT_MS = 0.15
CLEAN = dict(ppg_noise_sd=0.0, ecg_noise_sd=0.0)


def _run(tmp_path, spec, t0_s=70.0, color="green"):
    directory, truth = make_recording(tmp_path, spec)
    recording = si.load_recording(directory)
    series, _, flags = si.session_series(recording)
    events = si.session_events(recording)
    cuff = {"event_id": "E01", "phase": "M0", "status": "valid", "safety_stop": False,
            "led_readjusted": False, "pilot": False, "note": "", "device_session_id": 1,
            "t0_event_ordinal": [e["event_ordinal"] for e in events if e["code"] == 1][0],
            "phase_mark_event_ordinal": None, "cuff_end_event_ordinal": None,
            "sbp_mmhg": 120.0, "dbp_mmhg": 80.0, "pulse_rate_bpm": None}
    window = si.cuff_windows([cuff], events, CONFIG["window"])[0]
    session = recording["decode"]["sessions"][0]
    identity = {"subject_id": None, "session_id": None, "recording": "rec",
                "raw_sha256": recording["manifest"]["raw"]["sha256"],
                "source_type": "SYNTHETIC", "clock_id": "SYN_ESP_TIMER_US"}
    packets = [p for p in recording["packets"] if p["chain_id"] is not None]
    result = fe.window_features(window, series, packets, session, CONFIG, identity)
    return result, result["by_color"].get(color), truth, flags


def _pat_errors(chosen, truth):
    r_true = np.array(truth["r_us"]) / 1e6
    r = np.array(chosen["fiducials"]["r_times_s"])
    pairs = chosen["pat_validity"]["pairs"]
    errors = [pat - truth["pat_ms"][int(np.argmin(np.abs(r_true - r[i])))]
              for i, _, pat in pairs]
    return np.array(errors)


@pytest.mark.parametrize("spec", [
    SessionSpec(duration_s=80, events=((1, 70.0),), **CLEAN),
    SessionSpec(duration_s=80, events=((1, 70.0),), pat_profile=((0, 170), (80, 260)),
                hr_bpm=83, **CLEAN),
    SessionSpec(duration_s=80, events=((1, 70.0),), ppg_clock_ppm=3000,
                ecg_clock_ppm=-60, pat_profile=((0, 150), (40, 150), (40.01, 210)),
                **CLEAN),
], ids=["constant", "drifting", "clock_skew_and_step"])
def test_pat_matches_the_set_value_within_quantization(tmp_path, spec):
    result, chosen, truth, flags = _run(tmp_path, spec)
    assert flags == [] and result["hardware_flags"] == []
    errors = _pat_errors(chosen, truth)
    assert chosen["pat_validity"]["n_pairs"] >= 30
    assert np.max(np.abs(errors)) <= ECG_HALF_PERIOD_MS + FIT_MS
    assert chosen["flags"] == []
    # Same PAT from every colour: the slot offset is added before fiducials.
    for color in ("red", "ir"):
        other = result["by_color"][color]
        assert np.max(np.abs(_pat_errors(other, truth))) <= ECG_HALF_PERIOD_MS + FIT_MS


def test_missed_ppg_beat_is_flagged(tmp_path):
    spec = SessionSpec(duration_s=80, events=((1, 70.0),), missed_ppg_beats=(60,),
                       **CLEAN)
    _, chosen, truth, _ = _run(tmp_path, spec)
    assert "pat:unmatched_beats" in chosen["flags"]
    validity = chosen["pat_validity"]
    assert validity["n_no_foot"] == 1
    missed_r = truth["r_us"][60] / 1e6
    r = np.array(chosen["fiducials"]["r_times_s"])
    index = int(np.argmin(np.abs(r - missed_r)))
    assert abs(r[index] - missed_r) < 0.002
    assert validity["r_status"][index] == "no_foot"


def test_noisy_span_is_flagged_and_clean_window_is_not(tmp_path):
    clean = SessionSpec(duration_s=80, events=((1, 70.0),))
    _, chosen, _, _ = _run(tmp_path / "clean", clean)
    assert chosen["flags"] == []
    noisy = SessionSpec(duration_s=80, events=((1, 70.0),), noisy_spans_s=((50, 60),))
    _, chosen, _, _ = _run(tmp_path / "noisy", noisy)
    assert {"ppg:shape_inconsistent", "pat:unmatched_beats"} & set(chosen["flags"])


def test_lost_packet_in_window_is_a_stream_gap(tmp_path):
    # Window [40, 70) s; PPG packet 1375 holds samples 11000-11007, about 55 s.
    spec = SessionSpec(duration_s=80, events=((1, 70.0),), drop_packets=(("0xF1", 1375),),
                       **CLEAN)
    result, chosen, _, _ = _run(tmp_path, spec)
    assert "stream:gap" in result["hardware_flags"]
    assert "ppg:time_gap" in chosen["flags"]
    assert chosen["features"]["pat_median_ms"] is None
    # The other slots kept every packet.
    assert result["by_color"]["red"]["flags"] == []


def test_unknown_latency_blocks_pat(tmp_path):
    spec = SessionSpec(duration_s=80, events=((1, 70.0),), **CLEAN)
    directory, _ = make_recording(tmp_path, spec)
    recording = si.load_recording(directory)
    recording["metadata"]["channels"]["0xF1"]["latency_l_us"] = None
    series, _, flags = si.session_series(recording)
    assert "0xF1:latency_unknown" in flags
    assert not series["0xF1"].latency_applied


def test_ecg_codes_are_signed_18_bit():
    words = np.array([(5 << 6) | (1 << 3), ((-5) & 0x3FFFF) << 6])
    codes, etag = fe.ecg_codes(words)
    assert codes.tolist() == [5, -5] and etag.tolist() == [1, 0]


def test_quantization_bound_is_what_the_docs_state():
    assert ECG_HALF_PERIOD_MS == pytest.approx(0.977, abs=1e-3)
    assert 0.5 / 200 * 1000 == 2.5
