"""Device-rate fiducials, PAT and SQI flags on SYNTHETIC recordings with known PAT.

ECG 512 sps, PPG 200 sps (three slots), each channel on its own clock and
timestamps; the generator's PPG upstroke is linear, so the tangent foot equals the
set onset and the PAT error left is the R-peak quantization (half an ECG period,
0.98 ms) plus the anchor fit (tens of us).
"""

import copy
import json

import numpy as np
import pytest

from software.device import features as fe
from software.device import session_ingest as si
from software.device.synthetic_session import SessionSpec
from tests.device_fixtures import DEVICE_CONFIG, make_recording

CONFIG = json.loads(DEVICE_CONFIG.read_text())
# The time-axis tests run without filtering, so the tangent foot on the linear
# upstroke equals the set onset; the zero-phase band-pass of the config rounds the
# corner of that upstroke (tested separately below).
NO_FILTER = copy.deepcopy(CONFIG)
NO_FILTER["signal"]["filter_mode"] = "none"
ECG_HALF_PERIOD_MS = 0.5 / 512 * 1000
FIT_MS = 0.15
# Filtered PAT on the generator's pulse, measured 2026-11-15: mean error +1.2 ms,
# largest 2.7 ms (the band-pass rounds the corner at the onset). A guard against
# regressions on SYNTHETIC data, not a validation of the filter.
FILTERED_PAT_MS = 3.0
CLEAN = dict(ppg_noise_sd=0.0, ecg_noise_sd=0.0)


def _run(tmp_path, spec, t0_s=70.0, color="green", config=CONFIG, subject=None,
         session_update=None):
    directory, truth = make_recording(tmp_path, spec)
    recording = si.load_recording(directory)
    series, _, flags = si.session_series(recording)
    events = si.session_events(recording)
    cuff = {"event_id": "E01", "phase": "M0", "status": "valid", "safety_stop": False,
            "led_readjusted": False, "pilot": False, "note": "", "device_session_id": 1,
            "t0_event_ordinal": [e["event_ordinal"] for e in events if e["code"] == 1][0],
            "phase_mark_event_ordinal": None, "cuff_end_event_ordinal": None,
            "sbp_mmhg": 120.0, "dbp_mmhg": 80.0, "pulse_rate_bpm": None}
    window = si.cuff_windows([cuff], events, config["window"])[0]
    session = {**recording["decode"]["sessions"][0], **(session_update or {})}
    identity = {"subject_id": subject, "session_id": "S001" if subject else None,
                "recording": "rec", "raw_sha256": recording["manifest"]["raw"]["sha256"],
                "source_type": "SYNTHETIC", "clock_id": "SYN_ESP_TIMER_US"}
    packets = [p for p in recording["packets"] if p["chain_id"] is not None]
    result = fe.window_features(window, series, packets, session, config, identity)
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
    result, chosen, truth, flags = _run(tmp_path, spec, config=NO_FILTER)
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


def test_window_without_ecg_keeps_ppg_features(tmp_path):
    # SAP section 10 and endpoint 3: a cuff without ECG still gets its PPG
    # features (PPG-only on every cuff); PAT and ECG features stay empty.
    spec = SessionSpec(duration_s=80, events=((1, 70.0),), **CLEAN)
    directory, _ = make_recording(tmp_path, spec)
    recording = si.load_recording(directory)
    series, _, _ = si.session_series(recording)
    events = si.session_events(recording)
    _, with_ecg, _, _ = _run(tmp_path / "ref", spec)
    del series["0xE1"]
    cuff = {"event_id": "E01", "phase": "M0", "status": "valid", "safety_stop": False,
            "led_readjusted": False, "pilot": False, "note": "", "device_session_id": 1,
            "t0_event_ordinal": [e["event_ordinal"] for e in events if e["code"] == 1][0],
            "phase_mark_event_ordinal": None, "cuff_end_event_ordinal": None,
            "sbp_mmhg": 120.0, "dbp_mmhg": 80.0, "pulse_rate_bpm": None}
    window = si.cuff_windows([cuff], events, CONFIG["window"])[0]
    identity = {"subject_id": None, "session_id": None, "recording": "rec",
                "raw_sha256": recording["manifest"]["raw"]["sha256"],
                "source_type": "SYNTHETIC", "clock_id": "SYN_ESP_TIMER_US"}
    packets = [p for p in recording["packets"] if p["chain_id"] is not None]
    result = fe.window_features(window, series, packets,
                                recording["decode"]["sessions"][0], CONFIG, identity)
    assert result["missing"] == "ecg" and "ecg:absent" in result["hardware_flags"]
    chosen = result["by_color"]["green"]
    for name in ("ppg_rise_time_median_ms", "ppg_width50_median_ms",
                 "ppg_amplitude_median", "ppg_hr_bpm"):
        assert chosen["features"][name] == pytest.approx(with_ecg["features"][name])
    assert chosen["features"]["ecg_hr_bpm"] is None
    assert chosen["features"]["pat_median_ms"] is None and chosen["pat_validity"] is None
    row = fe.cuff_row(window, result, identity, "green")
    assert row["pat_ms"] is None and row["ppg_hr_bpm"] is not None
    assert "ecg:absent" in row["flags"].split(";")


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


def test_baseline_wander_needs_the_configured_filter(tmp_path):
    # Wander of about 3 R heights (ECG) and 4 pulse heights (PPG) peak to peak: the
    # prominence threshold (0.2 x the window's range) then hides most beats unless
    # the 0.5 Hz high-pass of the config removes the wander (added 2026-11-15).
    spec = SessionSpec(duration_s=80, events=((1, 70.0),), ecg_wander=1.5,
                       ppg_wander=2.0, **CLEAN)
    _, raw, _, _ = _run(tmp_path / "none", spec, config=NO_FILTER)
    assert CONFIG["signal"]["filter_mode"] == "zero_phase"
    _, filtered, truth, _ = _run(tmp_path / "filtered", spec)
    assert len(raw["fiducials"]["r_times_s"]) < len(filtered["fiducials"]["r_times_s"]) / 2
    assert filtered["flags"] == [] and filtered["pat_validity"]["n_valid"] >= 30
    assert np.max(np.abs(_pat_errors(filtered, truth))) <= FILTERED_PAT_MS


def test_ppg_that_stops_early_in_the_window_does_not_stop_the_session(tmp_path):
    # Every PPG packet from 1008 on (about 40.3 s) is lost: the window [40, 70) s
    # keeps 0.32 s of PPG, under 2 x edge_s + foot_lookback_s = 0.7 s. Before
    # 2026-11-15 this raised and stopped the whole session.
    drop = tuple((key, seq) for key in ("0xF1", "0xF2", "0xF3")
                 for seq in range(1008, 2000))
    spec = SessionSpec(duration_s=80, events=((1, 70.0),), drop_packets=drop, **CLEAN)
    result, chosen, _, _ = _run(tmp_path, spec)
    assert len(chosen["fiducials"]["r_times_s"]) > 20
    assert chosen["pat_validity"] is None and "pat:no_foot_span" in chosen["flags"]
    row = fe.cuff_row({"event_id": "E01", "phase": "M0", "status": "valid",
                       "safety_stop": False, "led_readjusted": False, "pilot": False,
                       "sbp_mmhg": 120.0, "dbp_mmhg": 80.0}, result,
                      {"subject_id": None, "session_id": None, "recording": "rec",
                       "source_type": "SYNTHETIC"}, "green")
    assert row["pat_ms"] is None and "pat:no_foot_span" in row["flags"].split(";")


def _state(seq, t_us, codes, generation, source="chip", configured=True):
    red, ir, green = codes
    return {"first_seq": seq, "t_anchor_us": t_us, "source": source,
            "configured": configured, "generation": generation,
            "registers": {"0x0C": f"0x{red:02X}", "0x0D": f"0x{ir:02X}",
                          "0x0E": f"0x{green:02X}", "0x0F": f"0x{green:02X}"}}


def test_led_lock_status_covers_every_case():
    locked, other = (40, 44, 18), (48, 44, 18)
    states = [_state(5, 1_000_000, (36, 36, 18), 1),  # boot defaults
              _state(9, 2_000_000, locked, 2),  # the lock takes effect
              _state(20, 50_000_000, other, 3),  # codes changed after the lock
              _state(30, 80_000_000, locked, 4)]  # locked codes sent again
    session = {"afe_config": {"MAX30101": states},
               "ppg_led_lock": {"applied": {"seq": 9, "t_anchor_us": 2_000_000,
                                            "generation": 2}}}
    status = fe.led_lock_status
    assert status(session, 10e6, 40e6, True) == "locked"
    assert status(session, 20e6, 50e6, True) == "locked"  # [start, t0) excludes t0
    assert status(session, 40e6, 60e6, True) == "codes_differ"  # change inside
    assert status(session, 55e6, 70e6, True) == "codes_differ"  # change before start
    assert status(session, 85e6, 95e6, True) == "locked"
    assert status(session, 1.5e6, 30e6, True) == "applied_after_window_start"
    assert status({**session, "ppg_led_lock": {"applied": None}},
                  10e6, 40e6, False) == "not_applied"
    assert status({**session, "ppg_led_lock": None}, 10e6, 40e6, True) == "no_lock_metadata"
    assert status({**session, "ppg_led_lock": None}, 10e6, 40e6, False) == "not_checked"
    down = states[:2] + [_state(15, 30_000_000, locked, 2, configured=False)]
    assert status({**session, "afe_config": {"MAX30101": down}},
                  31e6, 40e6, True) == "state_unverified"
    wrong_generation = {**session, "ppg_led_lock": {"applied": {
        "seq": 9, "t_anchor_us": 2_000_000, "generation": 3}}}
    assert status(wrong_generation, 10e6, 40e6, True) == "state_unverified"
    for name in ("no_lock_metadata", "not_applied", "applied_after_window_start",
                 "state_unverified", "codes_differ"):
        assert name in fe.LOCK_NOT_HELD
    assert not {"locked", "not_checked"} & set(fe.LOCK_NOT_HELD)


def test_led_not_locked_reaches_the_cuff_row(tmp_path):
    spec = SessionSpec(duration_s=80, events=((1, 70.0),), **CLEAN)
    # SYNTHETIC recordings have no lock: no subject, nothing to check.
    result, _, _, _ = _run(tmp_path / "plain", spec)
    assert result["led_lock_status"] == "not_checked"
    assert "ppg:led_not_locked" not in result["hardware_flags"]
    # A subject's recording whose lock never took effect (an MCU restart, say).
    result, _, _, _ = _run(tmp_path / "study", spec, subject="SYN_A",
                           session_update={"ppg_led_lock": {"applied": None}})
    assert result["led_lock_status"] == "not_applied"
    assert "ppg:led_not_locked" in result["hardware_flags"]
    row = fe.cuff_row({"event_id": "E01", "phase": "M0", "status": "valid",
                       "safety_stop": False, "led_readjusted": False, "pilot": False,
                       "sbp_mmhg": 120.0, "dbp_mmhg": 80.0}, result,
                      {"subject_id": "SYN_A", "session_id": "S001", "recording": "rec",
                       "source_type": "SYNTHETIC"}, "green")
    assert "ppg:led_not_locked" in row["flags"].split(";")


def test_slot_spacing_is_the_datasheet_table():
    # MAX30101 p. 22 Table 11, as copied in Packet Schema V0.1 section 7; the
    # ingest no longer takes it from the SYNTHETIC generator (2026-11-15), and A4
    # checks it on the bench (sync_10min_test_plan.md section 9).
    from software.device.max30101 import SLOT_SPACING_US
    assert SLOT_SPACING_US == {0: 427, 1: 525, 2: 720, 3: 1107}
    assert si.SLOT_SPACING_US is SLOT_SPACING_US
