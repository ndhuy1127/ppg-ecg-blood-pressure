"""Sync-test analysis (sync-analysis-v1) on SYNTHETIC recordings with known answers.

The generator puts a 50 ms pulse into the ECG ``stim_ecg_delay_us`` after each
event and into every PPG slot ``stim_ppg_delay_us`` after it; on the
anchor-fitted axis the true L of a channel is that delay plus the anchor latency
plus the mean anchor jitter (``truth["stim_l_*_us"]``), and the ECG-PPG offset
is their difference. Answers come from the generator, not from the analysis.
Also: the cases the plan says must be caught (phase-locked stimulus, invisible
PPG, a one-sample ECG step inside a chain, load-dependent offset, a missing
A11 boundary) and one the method cannot see (a constant shift from the start).
SYNTHETIC only: verifies code.
"""

import json
import random

import numpy as np
import pytest

from scripts import analyze_sync
from software.device import session_ingest as si
from software.device import sync_analysis as sa
from software.device.synthetic_session import SessionSpec
from tests.device_fixtures import make_recording

BASE = dict(ecg_beats=False, ppg_beats=False, declare_latency=False,
            ecg_noise_sd=0.002, ppg_noise_sd=0.002, ecg_latency_us=2500,
            ecg_clock_ppm=3, ppg_clock_ppm=-20)


def stim_times(end_s, seed=1, start_s=2.0, jitter=True):
    """About 1 Hz with a jitter in [0, 1953) us, as stim_plan.c (cumulative)."""
    rng, t, out = random.Random(seed), start_s, []
    while t < end_s:
        out.append(round(t, 6))
        t += 1.0 + (rng.uniform(0, 0.001953) if jitter else 0.0)
    return tuple(out)


def analyse(tmp_path, spec, name="rec", mutate=None, stabilization_s=5.0):
    directory, truth = make_recording(tmp_path, spec, name)
    recording = si.load_recording(directory)
    if mutate is not None:
        mutate(recording)
    return sa.analyze_run(recording, stabilization_s=stabilization_s), truth


@pytest.fixture(scope="module")
def clean(tmp_path_factory):
    spec = SessionSpec(duration_s=152, stim_s=stim_times(150), **BASE)
    return analyse(tmp_path_factory.mktemp("clean"), spec)


def test_latencies_and_offset_match_the_generator(clean):
    result, truth = clean
    assert result["events_used"] == result["events_total"] > 100
    assert result["latency"]["0xE1"]["mean_us"] == pytest.approx(truth["stim_l_ecg_us"],
                                                                  abs=100)
    assert result["latency"]["ppg"]["mean_us"] == pytest.approx(truth["stim_l_ppg_us"],
                                                                 abs=100)
    # Sign: L_ECG - L_PPG (plan section 5).
    expected = truth["stim_l_ecg_us"] - truth["stim_l_ppg_us"]
    assert result["offset"]["mean_us"] == pytest.approx(expected, abs=100)
    lo, hi = result["offset"]["ci_event_us"]
    assert lo - 100 <= expected <= hi + 100
    assert all(abs(v["mean_us"]) < 50 for v in result["slot_residual_us"].values())
    gates = result["verdict"]["gates"]
    assert all(gates[k] is True for k in ("a1", "a2", "a3", "a4", "a9", "a10"))
    assert result["a8"]["status"] == "not_evaluable"
    assert result["a6"]["status"] == "short_run"
    assert result["a11"]["status"] == "not_an_a11_run"
    assert result["verdict"]["run_passed"] is True


def test_ecg_ringing_of_an_ideal_low_pass_keeps_the_centre(tmp_path):
    spec = SessionSpec(duration_s=152, stim_s=stim_times(150), stim_ecg_lowpass_hz=40.96,
                       **BASE)
    result, truth = analyse(tmp_path, spec)
    assert result["rejections"]["0xE1"] == {"ok": result["events_total"]}
    assert result["latency"]["0xE1"]["mean_us"] == pytest.approx(truth["stim_l_ecg_us"],
                                                                  abs=150)


def test_phase_locked_stimulus_fails_a9_and_leaves_a4_unjudged(tmp_path):
    locked = dict(BASE, ecg_clock_ppm=0, ppg_clock_ppm=0, anchor_jitter_us=0)
    spec = SessionSpec(duration_s=152, stim_s=stim_times(150, jitter=False), **locked)
    result, _ = analyse(tmp_path, spec)
    assert result["a9"]["0xE1"]["passed"] is False
    assert result["verdict"]["gates"]["a9"] is False
    assert result["verdict"]["gates"]["a4"] is None
    assert result["verdict"]["run_passed"] is False


def test_invisible_ppg_is_not_detected_even_without_noise(tmp_path):
    spec = SessionSpec(duration_s=60, stim_s=stim_times(58), stim_ppg_amp=0.0,
                       **dict(BASE, ppg_noise_sd=0.0))
    result, _ = analyse(tmp_path, spec)
    assert result["rejections"]["0xF1"] == {"not_detected": result["events_total"]}
    assert result["events_used"] == 0 and result["offset"]["mean_us"] is None
    assert result["verdict"]["run_passed"] is False


def test_one_sample_ecg_step_inside_a_chain_fails_a10(tmp_path):
    spec = SessionSpec(duration_s=80, stim_s=stim_times(78),
                       ecg_anchor_steps=((40.0, 1953.0),), **BASE)
    result, _ = analyse(tmp_path, spec)
    assert result["a10"]["passed"] is False
    assert "a10" in result["verdict"]["failed"]


def test_constant_one_sample_shift_from_the_start_is_not_caught(tmp_path, clean):
    # Blind spot stated in the plan (11.2, A8 not evaluable): a shift present
    # from the first packet moves L_ECG and the offset, and no check fails.
    base_result, truth = clean
    spec = SessionSpec(duration_s=152, stim_s=stim_times(150),
                       **dict(BASE, ecg_latency_us=2500 + 1953))
    result, _ = analyse(tmp_path, spec)
    assert result["verdict"]["run_passed"] is True
    assert (result["offset"]["mean_us"] - base_result["offset"]["mean_us"]
            == pytest.approx(1953, abs=60))


def test_samp_anchors_and_declared_latency_are_refused(tmp_path):
    spec = SessionSpec(duration_s=30, stim_s=stim_times(28), **BASE)

    def samp(recording):
        next(p for p in recording["packets"] if p["channel_id"] == "0xE1")["status"] |= 1 << 8

    with pytest.raises(sa.SyncError, match="bit 8"):
        analyse(tmp_path, spec, "a", samp)
    declared = SessionSpec(duration_s=30, stim_s=stim_times(28),
                           **dict(BASE, declare_latency=True))
    with pytest.raises(sa.SyncError, match="latency_l_us"):
        analyse(tmp_path, declared, "b")


# A11 with 60 s blocks instead of 120 s (13 boundaries, same rules) so that the
# test runs in seconds; the block length is a parameter of the check, not of the
# logic.
BLOCK_S = 60.0


@pytest.fixture
def short_blocks(monkeypatch):
    monkeypatch.setitem(sa.A11, "block_s", BLOCK_S)


def _a11_spec(step_us, drop_boundary=False, channel="ecg"):
    boundaries = [3.0 + BLOCK_S * k for k in range(13)]
    if drop_boundary:
        boundaries.pop(5)
    # Load effect simulated as a FIFO read delay: ECG anchors step_us later in
    # every high block, back to normal after it.
    steps = []
    for k in range(1, 12, 2):
        steps += [(boundaries[0] + BLOCK_S * k, step_us),
                  (boundaries[0] + BLOCK_S * (k + 1), -step_us)]
    end = 3.0 + BLOCK_S * 12 + 4
    key = "ecg_anchor_steps" if channel == "ecg" else "ppg_anchor_steps"
    return SessionSpec(duration_s=end + 2, stim_s=stim_times(end, start_s=1.5),
                       events=tuple((2, t) for t in boundaries),
                       **{key: tuple(steps)}, **BASE)


@pytest.mark.parametrize("step_us, passed", [(100.0, True), (400.0, False)])
def test_a11_compares_high_and_normal_blocks(tmp_path, short_blocks, step_us, passed):
    result, _ = analyse(tmp_path, _a11_spec(step_us))
    a11 = result["a11"]
    assert a11["status"] == "evaluated" and len(a11["blocks"]) == 12
    assert a11["diff_us"] == pytest.approx(step_us, abs=40)
    assert a11["passed"] is passed and len(a11["pair_diffs_us"]) == 6


def test_a11_ppg_read_delay_counts_with_the_opposite_sign(tmp_path, short_blocks):
    # A later PPG read makes the PPG samples later in a session of its own, so the
    # offset L_ECG - L_PPG drops: the correction must use the PPG residual too.
    result, _ = analyse(tmp_path, _a11_spec(400.0, channel="ppg"))
    assert result["a11"]["diff_us"] == pytest.approx(-400.0, abs=40)
    assert result["a11"]["passed"] is False


def test_lost_stimulus_packet_fails_a1(tmp_path):
    spec = SessionSpec(duration_s=60, stim_s=stim_times(58), drop_packets=(("0xC1", 20),),
                       **BASE)
    result, _ = analyse(tmp_path, spec)
    assert result["a1"]["missing_packets"] == 1 and result["a1"]["passed"] is False


def test_a11_with_a_missing_boundary_is_not_evaluable(tmp_path, short_blocks):
    result, _ = analyse(tmp_path, _a11_spec(100.0, drop_boundary=True))
    assert result["a11"]["status"] == "not_evaluable"
    assert result["verdict"]["gates"]["a11"] is None


def _fake_run(offset, a1=True, a4=True, a9=True):
    return {"offset": {"mean_us": offset},
            "verdict": {"gates": {"a1": a1, "a4": a4, "a9": a9}}}


def test_a5_needs_ten_distinct_runs_over_two_dates_and_checks_the_range():
    dates = ["2026-12-01"] * 5 + ["2026-12-02"] * 5
    ids = [(f"raw{i}", i) for i in range(10)]
    runs = [_fake_run(32_000 + 20 * i) for i in range(10)]
    good = sa.a5(runs, dates, ids)
    assert good["status"] == "evaluated" and good["passed"] is True
    assert sa.a5(runs[:9] + [_fake_run(32_400)], dates, ids)["passed"] is False
    assert sa.a5(runs[:9], dates[:9], ids[:9])["status"] == "not_evaluable"
    assert sa.a5(runs, ["2026-12-01"] * 10, ids)["status"] == "not_evaluable"
    assert sa.a5(runs, dates[:9] + [""], ids)["status"] == "not_evaluable"
    # The same run counted twice is not ten runs.
    assert sa.a5(runs, dates, ids[:9] + [ids[0]])["status"] == "not_evaluable"
    for bad in (dict(a1=False), dict(a4=None), dict(a9=False)):
        bad_runs = runs[:9] + [_fake_run(32_000, **bad)]
        assert sa.a5(bad_runs, dates, ids)["status"] == "not_evaluable"


def _edge_case(kind="ok"):
    """One event at t = 1 s on a 512 sps grid; returns event_response."""
    t = np.arange(0, 2_000_000, 1953.125)
    x = np.zeros_like(t)
    on, off = 1_000_000 + 35_000, 1_000_000 + 85_000
    x[(t >= on) & (t < off)] = 1000.0
    chain, index = np.zeros(len(t), int), np.arange(len(t))
    if kind == "wide":
        x[(t >= off) & (t < off + 15_000)] = 1000.0
    if kind == "gap":
        index[600:] += 1
    if kind == "clipped":
        x[(t >= on) & (t < off)] = 131071.0
    if kind == "two_rises":
        x[(t >= on - 5_000) & (t < on - 3_000)] = 1000.0
    return sa.event_response(t, x, chain, index, 1_000_000, "ecg",
                             (-(1 << 17), (1 << 17) - 1))


@pytest.mark.parametrize("kind, status", [("ok", "ok"), ("wide", "bad_width"),
                                          ("gap", "gap"), ("clipped", "clipped"),
                                          ("two_rises", "rise_not_unique")])
def test_edge_rule_rejects_for_a_stated_reason(kind, status):
    out = _edge_case(kind)
    assert out["status"] == status
    if status == "ok":
        # A clean square pulse: the centre is within half a sample of the truth.
        assert abs(out["latency_us"] - 35_000) <= 1953.125 / 2


def test_script_writes_json_and_csv_and_refuses_overwrite_and_raw(tmp_path):
    # Past the 60 s stabilization of the script, so the CSV has offsets.
    spec = SessionSpec(duration_s=80, stim_s=stim_times(78), **BASE)
    directory, _ = make_recording(tmp_path, spec)
    base = tmp_path / "out" / "run1"
    analyze_sync.run(directory, base)
    data = json.loads((tmp_path / "out" / "run1.json").read_text(encoding="utf-8"))
    assert data["method"] == sa.VERSION and "provenance" in data and "events" not in data
    import csv

    with open(tmp_path / "out" / "run1_events.csv", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == data["events_total"] > 10
    assert all(r["offset_us"] != "" for r in rows)
    with pytest.raises(ValueError, match="exists"):
        analyze_sync.run(directory, base)
    raw = tmp_path / "data" / "raw"
    raw.mkdir(parents=True)
    with pytest.raises(ValueError, match="data/raw"):
        analyze_sync.check_output(raw / "x", raw_root=raw)
