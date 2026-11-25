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
         session_update=None, mutate_packets=None, mutate_series=None,
         source_type="SYNTHETIC"):
    directory, truth = make_recording(tmp_path, spec)
    recording = si.load_recording(directory)
    series, _, flags = si.session_series(recording)
    if mutate_series is not None:
        mutate_series(series)
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
                "source_type": source_type, "clock_id": "SYN_ESP_TIMER_US"}
    if mutate_packets is not None:
        mutate_packets(recording["packets"])
    packets = [p for p in fe.annotate_ecg_timing(recording["packets"])
               if p["chain_id"] is not None]
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
    assert validity["r_status"][index] == "no_rise"  # rise-after-r-v1 status


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
    packets = [p for p in fe.annotate_ecg_timing(recording["packets"])
               if p["chain_id"] is not None]
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
    # The generator's R peak is 30 000 codes (about 11 mV), so this wander reaches
    # about 46 mV, beyond the physical range the lead-off rule targets: the rule is
    # set to full scale here (a code never reaches it) and tested below.
    spec = SessionSpec(duration_s=80, events=((1, 70.0),), ecg_wander=1.5,
                       ppg_wander=2.0, **CLEAN)
    no_filter, config = (copy.deepcopy(c) for c in (NO_FILTER, CONFIG))
    for c in (no_filter, config):
        c["sqi_hardware"]["ecg_lead_off_abs_mv"] = c["sqi_hardware"]["ecg_full_scale_mv"]
    _, raw, _, _ = _run(tmp_path / "none", spec, config=no_filter)
    assert CONFIG["signal"]["filter_mode"] == "zero_phase"
    _, filtered, truth, _ = _run(tmp_path / "filtered", spec, config=config)
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


# ECG timing rule of sync_10min_test_plan.md section 11.4 (device-features-v2): a
# window whose ECG packets A10 flagged or could not check yet, or that carry
# STATUS bit 3, gets no PAT; PPG features stay (the cuff can still enter PPG-only).

def _ecg_in(packets, start_s, end_s, start_us=1_000_000):
    return [p for p in packets if p["channel_id"] == "0xE1"
            and start_us + start_s * 1e6 <= p["t_anchor_us"] < start_us + end_s * 1e6]


def _no_pat_but_ppg(result, chosen, flag):
    assert flag in result["hardware_flags"]
    assert chosen["pat_validity"] is None and chosen["features"]["pat_median_ms"] is None
    assert chosen["features"]["ppg_hr_bpm"] is not None
    row = fe.cuff_row({"event_id": "E01", "phase": "M0", "status": "valid",
                       "safety_stop": False, "led_readjusted": False, "pilot": False,
                       "sbp_mmhg": 120.0, "dbp_mmhg": 80.0}, result,
                      {"subject_id": None, "session_id": None, "recording": "rec",
                       "source_type": "SYNTHETIC"}, "green")
    assert row["pat_ms"] is None and flag in row["flags"]


def test_clean_window_after_10_s_keeps_pat(tmp_path):
    result, chosen, _, _ = _run(tmp_path, SessionSpec(duration_s=80, events=((1, 70.0),),
                                                      **CLEAN))
    assert not set(fe.ECG_TIMING_FLAGS) & set(result["hardware_flags"])
    assert chosen["pat_validity"]["n_valid"] > 0


def test_window_in_the_first_10_s_of_the_chain_has_no_pat(tmp_path):
    # Window [5 s, 35 s): its first packets have under 10 s of history.
    spec = SessionSpec(duration_s=40, events=((1, 35.0),), **CLEAN)
    result, chosen, _, _ = _run(tmp_path, spec)
    _no_pat_but_ppg(result, chosen, "ecg:timing_unverified")


def test_anchor_step_flagged_by_a10_stops_pat(tmp_path):
    def step(packets):
        for p in _ecg_in(packets, 50.0, 80.0):
            p["t_anchor_us"] += 1953  # one ECG sample late from 50 s on
    result, chosen, _, _ = _run(tmp_path, SessionSpec(duration_s=80, events=((1, 70.0),),
                                                      **CLEAN), mutate_packets=step)
    _no_pat_but_ppg(result, chosen, "ecg:timing_unverified")


def test_ecg_afe_error_bit_stops_pat(tmp_path):
    def bit3(packets):
        _ecg_in(packets, 55.0, 56.0)[0]["status"] |= 1 << 3
    result, chosen, _, _ = _run(tmp_path, SessionSpec(duration_s=80, events=((1, 70.0),),
                                                      **CLEAN), mutate_packets=bit3)
    _no_pat_but_ppg(result, chosen, "ecg:afe_error")


def test_hardware_flags_refuse_unannotated_ecg_packets(tmp_path):
    directory, _ = make_recording(tmp_path, SessionSpec(duration_s=40,
                                                        events=((1, 35.0),), **CLEAN))
    recording = si.load_recording(directory)
    series, _, _ = si.session_series(recording)
    rows = {key: np.arange(len(s.t_us)) for key, s in series.items()}
    packets = [p for p in recording["packets"] if p["chain_id"] is not None]
    with pytest.raises(ValueError, match="a10_state"):
        fe.hardware_flags(series, rows, packets, recording["decode"]["sessions"][0], {},
                          CONFIG["sqi_hardware"], "not_applicable")


# ECG lead-off from the signal (device-features-v3, decided 2026-11-24; bring-up
# report 9.10, sync_10min_test_plan.md 11.4, SQI v1 3.3): STATUS bit 2 is not used;
# a window is flagged, and gets no PAT, when an ECG sample of [start - 30 s, t0)
# reaches |35 mV| = 35 / 50 x 2^17 = 91 750.4 codes. Window [40 s, 70 s) here.
LEAD_OFF_CODES = 91_751


def _ecg_codes_at(start_s, end_s, code, start_us=1_000_000, etag=0):
    def mutate(series):
        s = series["0xE1"]
        rows = np.flatnonzero((s.t_us >= start_us + start_s * 1e6)
                              & (s.t_us < start_us + end_s * 1e6))
        assert len(rows)
        s.value[rows] = ((code & 0x3FFFF) << 6) | (etag << 3)
    return mutate


def test_lead_off_level_matches_the_rule():
    sqi = CONFIG["sqi_hardware"]
    assert (sqi["ecg_lead_off_abs_mv"], sqi["ecg_lead_off_hold_s"],
            sqi["ecg_full_scale_mv"]) == (35.0, 30.0, 50.0)
    assert sqi["ecg_lead_off_abs_mv"] / sqi["ecg_full_scale_mv"] * 2**17 == pytest.approx(
        LEAD_OFF_CODES - 0.6, abs=0.01)


@pytest.mark.parametrize("code", [LEAD_OFF_CODES, -LEAD_OFF_CODES, 131071, -131072])
def test_saturated_ecg_in_the_window_is_lead_off_and_stops_pat(tmp_path, code):
    spec = SessionSpec(duration_s=80, events=((1, 70.0),), **CLEAN)
    result, chosen, _, _ = _run(tmp_path, spec, mutate_series=_ecg_codes_at(55.0, 56.0, code))
    _no_pat_but_ppg(result, chosen, "ecg:lead_off")
    assert result["hardware_quality"]["ecg_max_abs_mv"] >= 35.0


def test_ecg_just_under_the_level_keeps_pat(tmp_path):
    spec = SessionSpec(duration_s=80, events=((1, 70.0),), **CLEAN)
    result, chosen, _, _ = _run(tmp_path, spec,
                                mutate_series=_ecg_codes_at(55.0, 55.01, LEAD_OFF_CODES - 1))
    assert "ecg:lead_off" not in result["hardware_flags"]
    assert chosen["pat_validity"]["n_valid"] > 0
    assert 34.9 < result["hardware_quality"]["ecg_max_abs_mv"] < 35.0


@pytest.mark.parametrize("span, flagged", [((15.0, 16.0), True),   # 24-25 s before start
                                           ((9.0, 9.9), False)])   # over 30 s before
def test_lead_off_holds_30_s_after_the_last_saturated_sample(tmp_path, span, flagged):
    spec = SessionSpec(duration_s=80, events=((1, 70.0),), **CLEAN)
    result, chosen, _, _ = _run(tmp_path, spec, mutate_series=_ecg_codes_at(*span, 120000))
    assert ("ecg:lead_off" in result["hardware_flags"]) == flagged
    assert (chosen["pat_validity"] is None) == flagged
    # The quality index is that of the window itself: the samples before stay out.
    assert result["hardware_quality"]["ecg_max_abs_mv"] < 35.0
    assert result["hardware_quality"]["ecg_lead_off_lookback_s"] == pytest.approx(30, abs=0.01)


def test_status_bit_2_alone_is_not_lead_off(tmp_path):
    def bit2(packets):
        for p in packets:
            if p["channel_id"] == "0xE1":
                p["status"] |= 1 << 2
    result, chosen, _, _ = _run(tmp_path, SessionSpec(duration_s=80, events=((1, 70.0),),
                                                      **CLEAN), mutate_packets=bit2)
    assert "ecg:lead_off" not in result["hardware_flags"]
    assert chosen["pat_validity"]["n_valid"] > 0


def _chip(cnfg_ecg, configured=True):
    return {"source": "chip", "configured": configured, "registers": {"0x15": cnfg_ecg}}


@pytest.mark.parametrize("states, source_type, error", [
    ([_chip("0x001000")], "DEVICE", None),
    ([_chip("0x011000")], "DEVICE", "ECG_GAIN"),
    ([_chip("0x031000")], "SYNTHETIC", "ECG_GAIN"),
    ([_chip("0x001000"), _chip("0x011000")], "DEVICE", "ECG_GAIN"),  # later change
    ([], "DEVICE", "unverified"),  # no readback on a device recording
    ([_chip("0x001000", configured=False)], "DEVICE", "unverified"),
    ([{"source": "fake", "configured": True, "registers": {}}], "DEVICE", "unverified"),
    ([], "SYNTHETIC", None),
])
def test_lead_off_level_needs_the_20_v_per_v_gain(tmp_path, states, source_type, error):
    spec = SessionSpec(duration_s=80, events=((1, 70.0),), **CLEAN)
    def run():
        return _run(tmp_path, spec, source_type=source_type,
                    session_update={"afe_config": {"MAX30001": states}})
    if error is None:
        assert run()[1]["pat_validity"]["n_valid"] > 0
    else:
        with pytest.raises(ValueError, match=error):
            run()


def test_fast_recovery_word_is_not_a_lead_off_level(tmp_path):
    # ETAG 001 (fast recovery) carries no valid voltage (p. 65 Table 48).
    spec = SessionSpec(duration_s=80, events=((1, 70.0),), **CLEAN)
    result, chosen, _, _ = _run(tmp_path, spec,
                                mutate_series=_ecg_codes_at(55.0, 55.01, 120000, etag=1))
    assert "ecg:lead_off" not in result["hardware_flags"]
    assert result["hardware_quality"]["ecg_max_abs_mv"] < 35.0
    assert chosen["pat_validity"]["n_valid"] > 0


def _series(t_us, codes):
    from types import SimpleNamespace
    return SimpleNamespace(t_us=np.asarray(t_us, float), fs_nominal_hz=512.0,
                           value=(np.asarray(codes, np.int64) & 0x3FFFF) << 6)


@pytest.mark.parametrize("at_us, flagged", [
    (10_000_000, True),    # exactly start - 30 s: inside the hold
    (9_999_999, False),    # just before it
    (69_999_999, True),    # last instant of the window
    (70_000_000, False),   # t0 itself: outside [start, t0)
])
def test_lead_off_hold_and_window_boundaries(at_us, flagged):
    # Window [40 s, 70 s); one saturated sample among quiet ones every 1 ms.
    t = np.arange(0, 80_000_000, 1000.0)
    t = np.sort(np.append(t[t != at_us], at_us))
    codes = np.where(t == at_us, 120000, 10)
    flag, quality = fe.ecg_lead_off(_series(t, codes), 40e6, 70e6, CONFIG["sqi_hardware"])
    assert flag == flagged


def test_lookback_reports_a_gap_before_the_window():
    t = np.arange(0, 80_000_000, 1e6 / 512)
    t = t[(t < 20e6) | (t >= 30e6)]  # 10 s of ECG lost in the hold
    flag, quality = fe.ecg_lead_off(_series(t, np.full(t.size, 10)), 40e6, 70e6,
                                    CONFIG["sqi_hardware"])
    assert not flag and quality["ecg_lead_off_lookback_s"] == pytest.approx(20, abs=0.01)


def test_config_without_the_lead_off_keys_is_refused():
    old = copy.deepcopy(CONFIG)
    del old["sqi_hardware"]["ecg_lead_off_hold_s"]
    with pytest.raises(ValueError, match="ecg_lead_off_hold_s"):
        fe.load_config(old)


# PPG orientation (2026-11-25): the MAX30101 reflectance counts fall with the
# systolic blood volume, so device_session_v1 turns the PPG up (ppg_polarity -1) and
# the generator emits falling counts (synthetic-device-session-v2). The generator
# and the config are checked apart, so a matching sign error in both cannot pass.

def _raw_green(tmp_path, spec):
    directory, truth = make_recording(tmp_path, spec)
    series, _, _ = si.session_series(si.load_recording(directory))
    s = series["0xF1"]
    return np.asarray(s.t_us, float), np.asarray(s.value, float), truth


def _level(t_us, values, at_us, half_width_us=4000):
    return float(np.mean(values[np.abs(t_us - at_us) <= half_width_us]))


def test_raw_ppg_counts_fall_with_the_pulse(tmp_path):
    from software.device.synthetic_session import VERSION
    assert VERSION == "synthetic-device-session-v2"
    assert CONFIG["signal"]["ppg_polarity"] == -1
    t, v, truth = _raw_green(tmp_path, SessionSpec(duration_s=20, **CLEAN))
    lat = 1500  # ppg_latency_us of the spec: times in series are latency-corrected
    for r_us, pat in list(zip(truth["r_us"], truth["pat_ms"]))[5:10]:
        foot = r_us + pat * 1000
        before, top = _level(t, v, foot - 30_000), _level(t, v, foot + 100_000)
        assert top < before - 1000, (before, top, lat)


def test_upright_counts_of_v1_are_still_available(tmp_path):
    t, v, truth = _raw_green(tmp_path, SessionSpec(duration_s=20, ppg_raw_inverted=False,
                                                   **CLEAN))
    foot = truth["r_us"][5] + truth["pat_ms"][5] * 1000
    assert _level(t, v, foot + 100_000) > _level(t, v, foot - 30_000) + 1000


def test_stimulus_light_still_raises_the_counts(tmp_path):
    spec = SessionSpec(duration_s=20, ppg_beats=False, stim_s=(10.0,), stim_width_s=0.05,
                       **CLEAN)
    t, v, _ = _raw_green(tmp_path, spec)
    on = 1_000_000 + 10.0e6
    assert _level(t, v, on + 25_000, 15_000) > _level(t, v, on - 40_000, 15_000) + 1000


def test_wrong_ppg_orientation_loses_the_pat(tmp_path):
    spec = SessionSpec(duration_s=80, events=((1, 70.0),), **CLEAN)
    upright = copy.deepcopy(NO_FILTER)
    upright["signal"]["ppg_polarity"] = 1
    _, chosen, truth, _ = _run(tmp_path, spec, config=upright)
    validity = chosen["pat_validity"]
    # Upside down, the "upstroke" is the falling edge of the real pulse: the feet
    # pair with R but sit far from the set onset (about 175 ms on this spec).
    assert validity is not None and validity["pairs"]
    assert np.median(np.abs(_pat_errors(chosen, truth))) > 50
