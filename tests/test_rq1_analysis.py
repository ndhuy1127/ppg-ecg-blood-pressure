"""RQ1 analysis (SAP v1) on SYNTHETIC per-cuff tables with known answers."""

import copy
import json
from pathlib import Path

import numpy as np
import pytest

from scripts import run_rq1_analysis
from software.evaluation import rq1_analysis as ra
from software.evaluation import rq1_holm_loso as rh
from software.evaluation.mean_intervals import interval
from software.evaluation.rq1_sensitivity import CUFFS, draw_counts

ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / "configs/analysis/rq1_analysis_v1.json").read_text())
FAST = {**CONFIG, "bootstrap": {**CONFIG["bootstrap"], "draws": 2000}}
PPG = CONFIG["models"]["ppg"]["features"]


def table(seed, n=20, sessions=2, sbp_pat=0.0, dbp_pat=0.0, drop=(), day_coupling=None):
    """Cuffs M0, M0, M1, M2 per session. True change: day effect (0 in session 1)
    plus M1 -4 / M2 +8 (SBP; DBP 0.6 x with its own day effect). PAT falls by
    ``sbp_pat`` ms per mmHg of the true SBP change and ``dbp_pat`` per mmHg of
    DBP; PPG features are weak and HR marks M2. ``drop``: (subject, session)
    removed. ``day_coupling``: the DBP day effect becomes ``day_coupling`` x the
    SBP one plus a quarter of its own draw (same random stream, so the other
    columns do not move)."""
    rng = np.random.default_rng(seed)
    rows = []
    for s in range(n):
        m2_s, m2_d = rng.normal(8, 3), rng.normal(5, 2)
        for k in range(1, sessions + 1):
            if (s, k) in drop:
                continue
            day_s = 0 if k == 1 else rng.normal(0, 5)
            day_d = 0 if k == 1 else rng.normal(0, 4)
            if day_coupling is not None and k > 1:
                day_d = day_coupling * day_s + 0.25 * day_d
            for c, phase in enumerate(CUFFS):
                ts = day_s + {"M0": 0, "M1": -4, "M2": m2_s}[phase]
                td = day_d + {"M0": 0, "M1": -2, "M2": m2_d}[phase]
                rows.append({
                    "subject_id": f"SYN_{s:02d}", "session_id": f"S{k:03d}",
                    "event_id": f"E{c + 1:02d}", "phase": phase, "status": "valid",
                    "safety_stop": 0, "source_type": "SYNTHETIC",
                    "sbp_mmhg": 120 + ts + rng.normal(0, 1.5),
                    "dbp_mmhg": 75 + td + rng.normal(0, 1.5),
                    "ppg_rise_time_ms": 150 + rng.normal(0, 5),
                    "ppg_width50_ms": 300 + rng.normal(0, 8),
                    "ppg_amplitude": 1000 + rng.normal(0, 30),
                    "ppg_hr_bpm": 70 + 10 * (phase == "M2") + rng.normal(0, 2),
                    "pat_ms": 220 - sbp_pat * ts - dbp_pat * td + rng.normal(0, 1.0),
                    "ecg_hr_bpm": 70 + rng.normal(0, 2), "ecg_rmssd_ms": 40 + rng.normal(0, 3),
                    "flags": ""})
    return rows


def conclusion(report, target):
    return report["main"]["targets"][target]["main_conclusion"]


def test_pat_helps_both_outputs():
    # Positive control, one seed: not a power estimate (SAP section 9 holds those).
    # With one evaluated session per subject (protocol section 3, 2026-11-19) the
    # DBP gain was not detected on this seed with independent day effects; coupling
    # the DBP day change to SBP makes the injected signal easier to detect.
    report = ra.analyze(table(1, sbp_pat=2.0, dbp_pat=1.0, day_coupling=0.6), FAST)
    for target in ("SBP", "DBP"):
        assert conclusion(report, target)["declared"]
        assert conclusion(report, target)["passes_at_975"]
        d = report["main"]["targets"][target]["contrasts"]["d"]
        # PAT carries SBP 2 ms/mmHg and DBP 1 ms/mmHg, so DBP gains less.
        assert d["ci_975"][1] < 0 and d["mean"] < (-1 if target == "SBP" else 0)
        # PAT tracks each person's change, so it also beats the phase baseline.
        assert report["main"]["targets"][target]["contrasts"]["d_phase"]["ci_95"][1] < 0


def test_pat_adds_nothing():
    report = ra.analyze(table(2), FAST)
    for target in ("SBP", "DBP"):
        assert not conclusion(report, target)["declared"]
        low, high = report["main"]["targets"][target]["contrasts"]["d"]["ci_975"]
        assert low < 0.1 and high > -0.1  # the CI reaches zero
    assert conclusion(report, "SBP")["reading"] == "delta_not_set"


def test_only_one_output_has_an_effect_holm():
    report = ra.analyze(table(3, sbp_pat=2.0), FAST)
    assert conclusion(report, "SBP")["declared"]
    assert not conclusion(report, "DBP")["declared"]
    # SBP passed step 1, so DBP was judged at 95 % (SAP section 6 step 2).
    assert conclusion(report, "DBP")["level_used"] == 0.95
    assert conclusion(report, "SBP")["level_used"] == 0.975


def test_holm_steps_and_delta_reading():
    assert ra.reading(-5, -3, 2) == "benefit_at_delta"
    assert ra.reading(-5, -1, 2) == "benefit_below_delta"
    assert ra.reading(-1, 1, 2) == "equivalent"
    assert ra.reading(1, 3, 2) == "harm"
    assert ra.reading(-3, 3, 2) == "inconclusive"
    sbp, dbp = rh.holm(np.array([True]), np.array([False]), np.array([True]),
                       np.array([True]))
    assert sbp[0] and dbp[0]


def test_missing_cuffs_and_sessions_follow_sap_section_10():
    rows = table(4, sbp_pat=2.0, drop={(0, 2)})
    # Subject 1: session 1 has one valid computable cuff left -> session 1 fails.
    rows = [r for r in rows if not (r["subject_id"] == "SYN_01" and r["session_id"] == "S001"
                                    and r["event_id"] in ("E02", "E03", "E04"))]
    # Subject 2: ECG lost (no PAT, no ECG HR) on M1 and M2 of session 2; its two M0
    # cuffs still compute, so session 2 passes and half its cuffs lost ECG.
    for r in rows:
        if (r["subject_id"] == "SYN_02" and r["session_id"] == "S002"
                and r["event_id"] in ("E03", "E04")):
            r.update(pat_ms="", ecg_hr_bpm="")
    # Subject 5: PAT missing with ECG present (pairing failed): not an ECG loss.
    for r in rows:
        if (r["subject_id"], r["session_id"], r["event_id"]) == ("SYN_05", "S002", "E03"):
            r["pat_ms"] = ""
    # Subject 3: one cuff without a cuff result; it is dropped, not filled.
    for r in rows:
        if (r["subject_id"], r["session_id"], r["event_id"]) == ("SYN_03", "S002", "E01"):
            r.update(status="no_result", sbp_mmhg="", dbp_mmhg="")
    report = ra.analyze(rows, FAST)
    assert report["subjects"]["excluded"] == {"SYN_00": "session2_not_passing",
                                              "SYN_01": "session1_not_passing"}
    assert report["subjects"]["eligible"] == 18
    assert report["counts"]["ecg_loss_share"]["SYN_02"] == pytest.approx(0.5)
    assert report["counts"]["ecg_loss_share"]["SYN_05"] == 0
    assert report["counts"]["main_cuffs"] == 18 * 4 - 2 - 1 - 1
    skipped = report["counts"]["skipped_by_phase"]
    assert skipped["M0"]["not_valid"] == 1 and skipped["M1"]["valid_not_computable"] == 2
    # Endpoint 3 keeps the cuffs without PAT for PPG-only.
    assert report["secondary"]["3_ppg_only_all_cuffs"]["SBP"]["n_cuffs"] == 18 * 4 - 1


def test_safety_stops_are_kept_in_main_and_dropped_in_endpoint_7():
    rows = table(5, sbp_pat=2.0)
    for r in rows:
        if r["subject_id"] == "SYN_04" and r["phase"] == "M2" and r["session_id"] != "S001":
            r["safety_stop"] = 1
    report = ra.analyze(rows, FAST)
    assert report["counts"]["safety_stop_in_main"] == 1
    assert report["counts"]["main_cuffs"] == 20 * 4
    endpoint = report["secondary"]["7_without_safety_stops"]
    assert endpoint["rows_dropped"] == 1
    assert endpoint["main_cuffs"] == 20 * 4 - 1 and endpoint["main_cuffs_change"] == -1
    # Any 0/1 spelling counts; one reader for every 0/1 column.
    for r in rows:
        if r["safety_stop"] == 1:
            r["safety_stop"] = "true"
    again = ra.analyze(rows, FAST)["secondary"]["7_without_safety_stops"]
    assert again["rows_dropped"] == 1


def test_held_out_subject_never_enters_its_fold(monkeypatch):
    prep = ra.prepare(table(6, n=6, sbp_pat=1.0), FAST)
    seen = []
    ridge, phase = ra.loso_ridge, ra.phase_mean

    def spy_ridge(train, test, *args, **kwargs):
        seen.append(({c["subject"] for c in train}, {c["subject"] for c in test}))
        return ridge(train, test, *args, **kwargs)

    def spy_phase(train, test, *args, **kwargs):
        seen.append(({c["subject"] for c in train}, {c["subject"] for c in test}))
        return phase(train, test, *args, **kwargs)

    monkeypatch.setattr(ra, "loso_ridge", spy_ridge)
    monkeypatch.setattr(ra, "phase_mean", spy_phase)
    ra._fold_predictions(prep, FAST)
    assert seen and all(len(test) == 1 and not test & train for train, test in seen)


def test_held_out_labels_do_not_change_its_predictions():
    rows = table(7, n=6, sbp_pat=1.0)
    prep = ra.prepare(rows, FAST)
    preds, _, _ = ra._fold_predictions(prep, FAST)
    changed = copy.deepcopy(rows)
    for r in changed:
        if r["subject_id"] == "SYN_00" and r["session_id"] != "S001":
            r["sbp_mmhg"] += 30
    prep2 = ra.prepare(changed, FAST)
    preds2, _, _ = ra._fold_predictions(prep2, FAST)
    for model in ("ppg", "ppg_pat", "phase_mean", "constant", "phase_ppg_pat"):
        a = [preds[("SBP", model)][id(c)] for c in prep["cuffs"]
             if c["subject"] == "SYN_00" and c["in_main"]]
        b = [preds2[("SBP", model)][id(c)] for c in prep2["cuffs"]
             if c["subject"] == "SYN_00" and c["in_main"]]
        assert np.allclose(a, b)


def test_matches_rq1_holm_loso_on_the_same_data():
    sim = json.loads((ROOT / "configs/analysis/rq1_holm_loso_v1.json").read_text())["loso"]
    features = {**sim["features"], "pat": {**sim["features"]["pat"], "a": 0.15}}
    target = {"tau_day": 4.0, "m1_mean": -3.0, "m1_sd": 2.0, "sigma_cuff": 4.0}
    effect = {"m2_mean": 8.0, "m2_sd": 4.0}
    n, sessions = 10, 2
    reference, x = rh.simulate_loso_data(np.random.default_rng(11), 1, n, sessions,
                                         target, effect, features)
    expected = rh.loso_d(np.random.default_rng(11), 1, n, sessions, target, effect,
                         features, sim["base_features"], 1.0)
    names = list(features)
    rows = []
    for s in range(n):
        for k in range(sessions):
            for c, phase in enumerate(CUFFS):
                row = {"subject_id": f"SYN_{s:02d}", "session_id": f"S{k + 1:03d}",
                       "event_id": f"E{c + 1:02d}", "phase": phase, "status": "valid",
                       "safety_stop": 0, "source_type": "SYNTHETIC",
                       "sbp_mmhg": 120 + reference[0, s, k, c],
                       "dbp_mmhg": 80 + reference[0, s, k, c]}
                row.update({name: x[0, s, k, c, i] for i, name in enumerate(names)})
                rows.append(row)
    base = sim["base_features"]
    config = {**FAST, "models": {
        "ppg": {"features": base}, "ppg_pat": {"features": names},
        "phase_ppg": {"features": base, "phase_indicators": True},
        "phase_ppg_pat": {"features": names, "phase_indicators": True}}}
    report = ra.analyze(rows, config)
    contrasts = report["main"]["targets"]["SBP"]["contrasts"]
    for key in ("d", "d0", "d_phase"):
        got = np.array(list(contrasts[key]["per_subject"].values()))
        assert np.allclose(got, expected[key][0], atol=1e-9)
    assert report["secondary"]["SBP"]["10_pat_given_phase"]["mean_d"] == pytest.approx(
        expected["d_with_phase"][0].mean(), abs=1e-9)


def test_script_writes_report(tmp_path):
    rows = table(8, n=8, sbp_pat=2.0)
    path = tmp_path / "cuff_features.csv"
    columns = list(rows[0])
    with open(path, "w", encoding="utf-8", newline="") as handle:
        import csv

        writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(FAST))
    report = run_rq1_analysis.run([path], config_path, tmp_path / "out")
    assert (tmp_path / "out" / "report.json").is_file()
    assert "SYNTHETIC input" in (tmp_path / "out" / "summary.md").read_text()
    assert report["source_types"] == ["SYNTHETIC"]
    with pytest.raises(ValueError, match="exists"):
        run_rq1_analysis.run([path], config_path, tmp_path / "out")


def test_device_feature_table_has_every_model_column():
    from scripts.device_session import FEATURE_COLUMNS

    needed = {f for spec in CONFIG["models"].values() for f in spec["features"]}
    assert needed - {"pat_inv_sq"} <= set(FEATURE_COLUMNS)
    for column in ("subject_id", "session_id", "event_id", "phase", "status",
                   "safety_stop", "led_readjusted", "pilot", "sbp_mmhg", "dbp_mmhg",
                   "flags", "source_type"):
        assert column in FEATURE_COLUMNS


def _real(rows):
    return [{**r, "source_type": "DEVICE", "led_readjusted": 0, "pilot": 0,
             "session_start_utc": f"2026-12-{int(r['session_id'][1:]):02d}T08:00:00+00:00"}
            for r in rows]


def _write(path, rows):
    import csv

    with open(path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    return path


def test_real_data_gate_needs_locked_config_and_committed_files(tmp_path, monkeypatch):
    for name in ("software/evaluation/rq1_sensitivity.py", "software/_provenance.py",
                 "software/device/session_ingest.py", "software/device/features.py"):
        assert name in run_rq1_analysis.LOCKED
    path = _write(tmp_path / "cuff_features.csv", _real(table(8, n=8)))
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(FAST))
    with pytest.raises(ValueError, match="status must be LOCKED"):
        run_rq1_analysis.run([path], config_path, tmp_path / "a")
    # A LOCKED copy outside the repository is not the committed config.
    config_path.write_text(json.dumps({**FAST, "status": "LOCKED"}))
    with pytest.raises(ValueError, match="'config'"):
        run_rq1_analysis.run([path], config_path, tmp_path / "b")
    # Config accepted, one changed code file: refused, and the file is named.
    import scripts.run_b2_pulsedb as b2

    monkeypatch.setattr(b2, "committed_unchanged",
                        lambda repo, p: not str(p).endswith("features.py"))
    with pytest.raises(ValueError, match="software/device/features.py"):
        run_rq1_analysis.run([path], config_path, tmp_path / "c")
    assert not any((tmp_path / n).exists() for n in "abc")


def test_main_decision_needs_d_and_d0_and_follows_holm():
    def upper(sbp, dbp):
        return {t: {level: dict(zip(("d", "d0"), values[level]))
                    for level in (0.975, 0.95)}
                for t, values in (("SBP", sbp), ("DBP", dbp))}

    no = {0.975: (1.0, 1.0), 0.95: (1.0, 1.0)}
    # d below 0 at both levels, d0 not: nothing is declared.
    d_only = {0.975: (-1.0, 0.5), 0.95: (-1.0, 0.5)}
    out = ra.main_decision(upper(d_only, no))
    assert not out["SBP"]["declared"] and not out["SBP"]["passes_at_975"]
    # Both outcomes pass only at 95 %: Holm stops at step 1.
    at95 = {0.975: (-1.0, 0.2), 0.95: (-1.0, -0.1)}
    out = ra.main_decision(upper(at95, at95))
    assert not out["SBP"]["declared"] and not out["DBP"]["declared"]
    assert out["SBP"]["passes_at_95"] and out["SBP"]["level_used"] == 0.975
    # SBP passes at 97.5 %, DBP only at 95 %: both declared, DBP at 95 %.
    first = {0.975: (-1.0, -1.0), 0.95: (-1.0, -1.0)}
    out = ra.main_decision(upper(first, at95))
    assert out["SBP"]["declared"] and out["DBP"]["declared"]
    assert out["DBP"]["level_used"] == 0.95 and out["SBP"]["level_used"] == 0.975


def test_led_readjusted_on_one_cuff_removes_the_whole_session():
    rows = table(9, n=6, sbp_pat=1.0)
    for r in rows:
        if (r["subject_id"], r["session_id"], r["event_id"]) == ("SYN_01", "S002", "E03"):
            r["led_readjusted"] = 1
    prep = ra.prepare(rows, FAST)
    session = [c for c in prep["cuffs"] if c["subject"] == "SYN_01" and c["session"] == 2]
    assert len(session) == 4
    assert not any(c["in_main"] or c["trainable"] for c in session)
    assert prep["led_readjusted_sessions"] == ["SYN_01|S002"]
    # A readjusted session 2 is not a passing session (SAP section 2): the subject
    # is out, its session-1 cuffs too.
    assert prep["excluded"] == {"SYN_01": "session2_not_passing"}
    assert not any(c["trainable"] for c in prep["cuffs"] if c["subject"] == "SYN_01")


def test_session2_must_pass_and_session3_is_refused():
    """SAP section 2 (amended 2026-11-21): session 1 and session 2 must pass, a
    session passing with >= 2 computable cuffs. Protocol section 3 (2026-11-19):
    no session 3, so such a row is a log error and is refused."""
    rows = table(11, n=6, sbp_pat=1.0)
    for r in rows:
        # SYN_01: ECG lost on every session-2 cuff -> session 2 fails.
        if r["subject_id"] == "SYN_01" and r["session_id"] == "S002":
            r.update(pat_ms="", ecg_hr_bpm="")
        # SYN_02: ECG lost on 3 of 4 session-2 cuffs -> 1 computable, fails.
        if (r["subject_id"] == "SYN_02" and r["session_id"] == "S002"
                and r["event_id"] != "E01"):
            r.update(pat_ms="", ecg_hr_bpm="")
        # SYN_03: ECG lost on 2 of 4 -> 2 computable, passes (the boundary).
        if (r["subject_id"] == "SYN_03" and r["session_id"] == "S002"
                and r["event_id"] in ("E03", "E04")):
            r.update(pat_ms="", ecg_hr_bpm="")
    prep = ra.prepare(rows, FAST)
    assert prep["excluded"] == {"SYN_01": "session2_not_passing",
                                "SYN_02": "session2_not_passing"}
    assert prep["eligible"] == ["SYN_00", "SYN_03", "SYN_04", "SYN_05"]
    assert not any(c["in_main"] or c["trainable"] for c in prep["cuffs"]
                   if c["subject"] in ("SYN_01", "SYN_02"))
    third = copy.deepcopy(rows[-1])
    third.update(session_id="S003", event_id="E01")
    with pytest.raises(ValueError, match="'S003' of subject 'SYN_05'.*only S001 and S002"):
        ra.prepare(rows + [third], FAST)
    # Finding 1 of the review: int() reads non-ASCII digits, so a full-width copy of
    # one S002 cuff passed the duplicate check and counted twice toward the
    # 2-cuff threshold. Other spellings of a session are refused as well.
    for spelling in ("S００２", "S2", "s002", "S000", " S002"):
        copied = copy.deepcopy(rows[-1])
        copied["session_id"] = spelling
        with pytest.raises(ValueError, match="only S001 and S002"):
            ra.prepare(rows + [copied], FAST)


def test_pilot_subject_is_excluded_and_real_rows_need_the_columns():
    rows = table(10, n=6)
    for r in rows:
        if (r["subject_id"], r["session_id"], r["event_id"]) == ("SYN_02", "S002", "E04"):
            r["pilot"] = 1
    prep = ra.prepare(rows, FAST)
    assert prep["excluded"] == {"SYN_02": "pilot"}
    assert not any(c["trainable"] for c in prep["cuffs"] if c["subject"] == "SYN_02")
    real = _real(table(10, n=6))
    ra.prepare(real, FAST)
    for column in ("pilot", "led_readjusted", "safety_stop"):
        broken = copy.deepcopy(real)
        del broken[5][column]
        with pytest.raises(ValueError, match=f"{column}.*required"):
            ra.prepare(broken, FAST)
    broken = copy.deepcopy(real)
    broken[0]["pilot"] = "yes"
    with pytest.raises(ValueError, match="must be 0 or 1"):
        ra.prepare(broken, FAST)


def test_ragged_cuff_counts_match_a_hand_computation():
    def cuff(subject, phase, x, y, session=2):
        return {"subject": subject, "session": session, "phase": phase,
                "x": {"f": x}, "delta_bp": np.array([y, 0.0]), "in_main": True}

    # Subject A has three cuffs, B one: weights 1/3, 1/3, 1/3 and 1.
    train = [cuff("A", "M1", 1.0, 2.0), cuff("A", "M1", 2.0, 3.0),
             cuff("A", "M2", 3.0, 7.0), cuff("B", "M1", 4.0, 10.0)]
    x = np.array([1.0, 2.0, 3.0, 4.0])
    y = np.array([2.0, 3.0, 7.0, 10.0])
    w = np.array([1, 1, 1, 3]) / 3
    sd = x.std(ddof=1)
    beta = (w * x / sd * y).sum() / ((w * (x / sd) ** 2).sum() + 1.0) / sd
    got = ra.loso_ridge(train, [cuff("C", "M1", 2.5, 0.0)], ["f"], 1.0, 0)
    assert got[0] == pytest.approx(2.5 * beta, rel=1e-12)
    # Phase mean: per subject first (M1: A 2.5, B 10), then equal weight -> 6.25,
    # not the pooled (2 + 3 + 10) / 3; M2 has only A; M0 has nobody -> 0.
    test = [cuff("C", p, 0.0, 0.0) for p in ("M1", "M2", "M0")]
    pred, empty = ra.phase_mean(train, test, 0)
    assert pred.tolist() == pytest.approx([6.25, 7.0, 0.0]) and empty == ["M0"]
    # Constant: A mean 4.0, B 10 -> 7.0.
    pred, _ = ra.phase_mean(train, test, 0, by_phase=False)
    assert pred.tolist() == pytest.approx([7.0, 7.0, 7.0])


def test_main_ci_is_the_t_envelope_on_the_configured_draws():
    report = ra.analyze(table(11, n=12, sbp_pat=1.5), FAST)
    boot = FAST["bootstrap"]
    for target in ("SBP", "DBP"):
        for name in ("d", "d0", "d_phase"):
            c = report["main"]["targets"][target]["contrasts"][name]
            d = np.array(list(c["per_subject"].values()))
            counts = draw_counts(boot["draws"], len(d), np.random.default_rng(boot["seed"]))
            for level, key in ((0.975, "ci_975"), (0.95, "ci_95")):
                low, high = interval(d[None, :], counts, level, "t_envelope")
                assert c[key] == pytest.approx([low[0], high[0]], abs=1e-12)
    sens = report["main"]["ci_sensitivity"]
    assert set(sens["methods"]) == set(ra.SENSITIVITY_METHODS)
    for method, out in sens["methods"].items():
        differs = any(out[t]["declared"] != conclusion(report, t)["declared"]
                      for t in ("SBP", "DBP"))
        assert (method in sens["changed"]) == differs
    assert report["secondary"]["SBP"]["11_phase_median_baseline"]["ci_95"] is not None
    # 12 eligible subjects: below the SAP minimum of 15, so the report warns.
    assert report["subjects"]["below_min_eligible"] and report["warnings"]
    full = ra.analyze(table(11, n=15, sbp_pat=1.5), FAST)
    assert not full["subjects"]["below_min_eligible"] and not full["warnings"]


def test_empty_phase_folds_are_counted():
    rows = [r for r in table(12, n=6) if not (r["phase"] == "M2"
                                              and r["session_id"] != "S001"
                                              and r["subject_id"] != "SYN_00")]
    report = ra.analyze(rows, FAST)
    # Only SYN_00 has later M2 cuffs: its own fold has no training M2.
    assert report["main"]["phase_baseline_empty_phase_folds"]["SBP"] == {
        "M0": 0, "M1": 0, "M2": 1}
    skipped = report["counts"]["skipped_by_phase"]["M2"]
    assert skipped["later_sessions_without_main_cuff"] == 5


def test_endpoints_5_and_7_keep_the_main_calibration():
    """SAP section 3 (rule of 2026-11-14): a flagged session-1 M0 cuff leaves the
    training set but not BP0 or the feature baseline, so the labels of every other
    cuff stay those of the main analysis and no subject is lost."""
    rows = table(6, sbp_pat=2.0)
    for r in rows:
        if r["subject_id"] == "SYN_03" and r["session_id"] == "S001" and r["event_id"] == "E01":
            r["flags"] = "motion"
            r["safety_stop"] = 1
    report = ra.analyze(rows, FAST)
    for name in ("5_sqi_filtered", "7_without_safety_stops"):
        endpoint = report["secondary"][name]
        assert endpoint["rows_dropped"] == 1 and endpoint["main_cuffs_change"] == 0
        assert endpoint["subjects_without_evaluated_cuffs"] == []
        assert endpoint["calibration"] == "main_analysis"
        for target in ("SBP", "DBP"):
            # Zero-change depends only on the labels of the evaluated cuffs: a new BP0
            # for SYN_03 (recalibration without E01) would change it.
            assert (endpoint["targets"][target]["models"]["zero_change"]["mae"]
                    == pytest.approx(report["main"]["targets"][target]["models"]
                                     ["zero_change"]["mae"], abs=1e-12))


def test_endpoint_5_reports_a_subject_left_without_evaluated_cuffs():
    rows = table(7, sbp_pat=2.0)
    for r in rows:
        if r["subject_id"] == "SYN_05" and r["session_id"] != "S001":
            r["flags"] = "stream:gap"
    report = ra.analyze(rows, FAST)
    endpoint = report["secondary"]["5_sqi_filtered"]
    assert endpoint["subjects_without_evaluated_cuffs"] == ["SYN_05"]
    assert endpoint["evaluated_cuffs_by_subject"]["SYN_05"] == [0, 4]
    assert endpoint["n_folds"] == 19 and endpoint["main_cuffs_change"] == -4
    # Eligibility is not re-examined: the main analysis keeps all 20 subjects.
    assert report["main"]["n_folds"] == 20


def _local_imports(start, leaves=("scripts/run_b2_pulsedb.py",)):
    """Local modules reachable from ``start`` by import (``leaves`` not expanded)."""
    import ast

    seen, todo = set(), list(start)
    while todo:
        name = todo.pop()
        if name in seen:
            continue
        seen.add(name)
        if name in leaves:
            continue
        for node in ast.walk(ast.parse((ROOT / name).read_text(encoding="utf-8"))):
            mods = []
            if isinstance(node, ast.ImportFrom) and node.module:
                mods = [node.module] + [f"{node.module}.{a.name}" for a in node.names]
            elif isinstance(node, ast.Import):
                mods = [a.name for a in node.names]
            for mod in mods:
                if mod.split(".")[0] not in ("software", "scripts"):
                    continue
                parts = mod.split(".")
                # Importing a.b.c also runs a/__init__.py and a/b/__init__.py.
                parents = ["/".join(parts[:i]) + "/__init__.py" for i in range(1, len(parts))]
                for candidate in (mod.replace(".", "/") + ".py",
                                  mod.replace(".", "/") + "/__init__.py", *parents):
                    if (ROOT / candidate).is_file():
                        todo.append(candidate)
    return seen


def test_lock_covers_every_module_of_the_analysis_and_the_feature_step():
    from scripts import device_session

    feature = _local_imports(["scripts/device_session.py"])
    assert feature <= set(device_session.CODE)
    every = _local_imports(["scripts/run_rq1_analysis.py", "scripts/device_session.py"])
    # The graph includes the parent packages, so dropping one from the lock fails here.
    assert {"software/__init__.py", "software/evaluation/__init__.py",
            "software/signal_processing/__init__.py"} <= every
    assert every <= set(run_rq1_analysis.LOCKED)
    assert device_session.CONFIG in run_rq1_analysis.LOCKED


def _provenance(path, **override):
    from scripts import device_session
    from software._provenance import text_file_sha256
    from software.device.session_ingest import sha256_file

    prov = {"source_type": "DEVICE", "git_commit": "abc", "git_dirty": False,
            "code_sha256": {c: text_file_sha256(ROOT / c) for c in device_session.CODE},
            "config_sha256": text_file_sha256(ROOT / device_session.CONFIG),
            "outputs_sha256": {"cuff_features.csv": sha256_file(path)}, **override}
    (path.parent / "provenance.json").write_text(json.dumps(prov))


def _commit_holds_current_files(commit, path):
    """Stand-in for ``commit_text_sha256``: commit "abc" holds today's files."""
    from software._provenance import text_file_sha256

    return text_file_sha256(ROOT / path) if commit == "abc" else None


def test_feature_provenance_gate(tmp_path, monkeypatch):
    import scripts.run_b2_pulsedb as b2

    monkeypatch.setattr(b2, "committed_unchanged", lambda repo, p: True)
    monkeypatch.setattr(run_rq1_analysis, "commit_text_sha256", _commit_holds_current_files)
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps({**FAST, "status": "LOCKED"}))
    cases = {
        "none": None,
        "dirty": {"git_dirty": True},
        "code": {"code_sha256": {}},
        "config": {"config_sha256": "0" * 64},
        "source": {"source_type": "SYNTHETIC"},
        # Another table placed next to this provenance, or an edited table.
        "swapped": {"outputs_sha256": {"cuff_features.csv": "0" * 64}},
        "unlisted": {"outputs_sha256": {}},
        # A commit that does not hold the recorded code (or does not exist).
        "commit": {"git_commit": "not-a-commit"},
    }
    messages = {"none": "no provenance.json", "dirty": "uncommitted workspace",
                "code": "feature code differs", "config": "feature config differs",
                "source": "provenance.json says", "swapped": "not the one",
                "unlisted": "not the one", "commit": "does not hold"}
    for name, override in cases.items():
        folder = tmp_path / name
        folder.mkdir()
        path = _write(folder / "cuff_features.csv", _real(table(8, n=8)))
        if override is not None:
            _provenance(path, **override)
        with pytest.raises(ValueError, match=messages[name]):
            run_rq1_analysis.run([path], config_path, folder / "out")
        assert not (folder / "out").exists()
    good = tmp_path / "good"
    good.mkdir()
    path = _write(good / "cuff_features.csv", _real(table(8, n=8)))
    _provenance(path)
    report = run_rq1_analysis.run([path], config_path, good / "out")
    entry = report["provenance"]["feature_provenance"][str(path)]
    assert entry["git_dirty"] is False and len(entry["provenance_sha256"]) == 64


def test_commit_text_sha256_reads_the_committed_file():
    import subprocess

    from software._provenance import text_sha256

    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    blob = subprocess.check_output(["git", "show", f"{head}:pyproject.toml"], cwd=ROOT)
    assert run_rq1_analysis.commit_text_sha256(head, "pyproject.toml") == text_sha256(blob)
    assert run_rq1_analysis.commit_text_sha256("0" * 40, "pyproject.toml") is None
    assert run_rq1_analysis.commit_text_sha256("not-a-commit", "pyproject.toml") is None
    assert run_rq1_analysis.commit_text_sha256(head, "no/such/file.py") is None
    # A tree id reads the same files but is not a commit: refused.
    tree = subprocess.check_output(["git", "rev-parse", "HEAD^{tree}"], cwd=ROOT,
                                   text=True).strip()
    assert run_rq1_analysis.commit_text_sha256(tree, "pyproject.toml") is None


def test_filtered_endpoint_keeps_labels_features_and_drops_flagged_cuffs(monkeypatch):
    """Endpoints 5/7 against the main preparation, cuff by cuff: same delta BP and
    delta features; a flagged cuff leaves both the training and the evaluated set;
    nothing else moves."""
    rows = table(9, sbp_pat=2.0)
    for r in rows:
        if r["subject_id"] == "SYN_02" and r["event_id"] == "E01":
            r["flags"] = "motion"  # session 1 (calibration) and session 2
    prep = ra.prepare(rows, FAST)
    snapshot = copy.deepcopy(prep)
    seen = {}
    monkeypatch.setattr(ra, "_core", lambda sub, config: seen.setdefault("sub", sub) and {})
    exclusion = set(FAST["sqi_exclusion_flags"])
    out = ra._filtered(prep, FAST, lambda c: bool(exclusion & c["flags"]),
                       sum(c["in_main"] for c in prep["cuffs"]))
    sub = seen["sub"]
    assert len(sub["cuffs"]) == len(snapshot["cuffs"])
    # The main preparation itself is untouched (no in-place edit leaks back).
    for kept, now in zip(snapshot["cuffs"], prep["cuffs"]):
        assert np.array_equal(kept["delta_bp"], now["delta_bp"]) and kept["x"] == now["x"]
        assert (kept["in_main"], kept["trainable"]) == (now["in_main"], now["trainable"])
    for before, after in zip(snapshot["cuffs"], sub["cuffs"]):
        assert np.array_equal(before["delta_bp"], after["delta_bp"])
        assert before["x"] == after["x"]
        flagged = before["subject"] == "SYN_02" and before["event_id"] == "E01"
        assert after["trainable"] == (before["trainable"] and not flagged)
        assert after["in_main"] == (before["in_main"] and not flagged)
    assert out["rows_dropped"] == 2
    assert out["dropped_from_training"] == 2 and out["dropped_from_evaluation"] == 1
    assert out["confirmatory"] is False and out["n_evaluated_subjects"] == 20
    assert out["below_min_eligible"] is False


@pytest.mark.parametrize("lost, below", [(1, False), (2, True)])
def test_filtered_endpoint_flags_too_few_evaluated_subjects(monkeypatch, lost, below):
    """16 eligible subjects; losing every evaluated cuff of 1 leaves 15 (the SAP
    minimum, no flag), of 2 leaves 14 (flagged)."""
    rows = table(10, n=16, sbp_pat=2.0)
    gone = {f"SYN_{i:02d}" for i in range(lost)}
    for r in rows:
        if r["subject_id"] in gone and r["session_id"] != "S001":
            r["safety_stop"] = 1
    prep = ra.prepare(rows, FAST)
    monkeypatch.setattr(ra, "_core", lambda sub, config: {})
    out = ra._filtered(prep, FAST, lambda c: c["safety_stop"],
                       sum(c["in_main"] for c in prep["cuffs"]))
    assert out["n_evaluated_subjects"] == 16 - lost
    assert out["below_min_eligible"] is below
    assert out["subjects_without_evaluated_cuffs"] == sorted(gone)


def test_rows_labelled_synthetic_with_device_provenance_are_refused(tmp_path):
    path = _write(tmp_path / "cuff_features.csv", table(8, n=8))
    _provenance(path)  # the logger says DEVICE, the rows say SYNTHETIC
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(FAST))
    with pytest.raises(ValueError, match="provenance.json says 'DEVICE'"):
        run_rq1_analysis.run([path], config_path, tmp_path / "out")


def test_session_numbers_must_follow_time():
    # BP0 comes from session 1, so a misnumbered session would calibrate on a
    # later visit: refused, on SYNTHETIC rows too when the column is given.
    rows = _real(table(13, n=4))
    ra.prepare(rows, FAST)
    swapped = copy.deepcopy(rows)
    for r in swapped:
        if r["subject_id"] == "SYN_02" and r["session_id"] in ("S001", "S002"):
            r["session_start_utc"] = ("2026-12-05T08:00:00+00:00" if r["session_id"] == "S001"
                                      else "2026-12-01T08:00:00+00:00")
    with pytest.raises(ValueError, match="SYN_02.*S002.*must follow time"):
        ra.prepare(swapped, FAST)
    same = copy.deepcopy(rows)
    for r in same:
        if r["subject_id"] == "SYN_01" and r["session_id"] == "S002":
            r["session_start_utc"] = "2026-12-01T08:00:00+00:00"
    with pytest.raises(ValueError, match="SYN_01.*S002"):
        ra.prepare(same, FAST)
    # A late recording filed under session 1 (its earliest start still first):
    # BP0 would use a visit after session 2, so it is refused too.
    late = copy.deepcopy(rows)
    for r in late:
        if (r["subject_id"], r["session_id"], r["event_id"]) == ("SYN_03", "S001", "E02"):
            r["session_start_utc"] = "2026-12-02T12:00:00+00:00"
    with pytest.raises(ValueError, match="SYN_03.*last recording of S001"):
        ra.prepare(late, FAST)
    for value, message in (("", "session_start_utc.*required"),
                           ("2026-12-01T08:00:00", "UTC offset"),
                           ("yesterday", "ISO 8601")):
        broken = copy.deepcopy(rows)
        broken[3]["session_start_utc"] = value
        with pytest.raises(ValueError, match=message):
            ra.prepare(broken, FAST)
    synthetic = table(13, n=4)
    synthetic[0]["session_start_utc"] = "2026-12-09T08:00:00+00:00"
    synthetic[5]["session_start_utc"] = "2026-12-01T08:00:00+00:00"  # SYN_00 S002
    with pytest.raises(ValueError, match="SYN_00"):
        ra.prepare(synthetic, FAST)


def test_led_readjusted_on_session_1_is_refused():
    rows = table(14, n=4)
    rows[1]["led_readjusted"] = 1  # SYN_00, S001
    with pytest.raises(ValueError, match=r"SYN_00\|S001.*sessions >= 2"):
        ra.prepare(rows, FAST)


def test_secondary_model_contrasts_use_the_same_cuffs():
    rows = table(15, n=8, sbp_pat=1.0)
    # No HRV on two main-set cuffs: the ablation has no prediction there.
    holes = {("SYN_03", "S002", "E03"), ("SYN_05", "S002", "E04")}
    for r in rows:
        if (r["subject_id"], r["session_id"], r["event_id"]) in holes:
            r["ecg_rmssd_ms"] = ""
    prep = ra.prepare(rows, FAST)
    preds, _, _ = ra._fold_predictions(prep, FAST)
    report = ra._secondary(rows, prep, FAST, None)
    main_set = sum(c["in_main"] for c in prep["cuffs"])
    for ti, target in enumerate(ra.TARGETS):
        entry = report[target]["model_ablation_ecg"]
        assert entry["main_set_cuffs"] == main_set
        assert entry["paired_cuffs"] == main_set - len(holes)
        by = {}
        for c in prep["cuffs"]:
            a = preds[(target, "ablation_ecg")].get(id(c), np.nan)
            if c["in_main"] and np.isfinite(a):
                b = preds[(target, "ppg")][id(c)]
                truth = c["delta_bp"][ti]
                by.setdefault(c["subject"], []).append(abs(a - truth) - abs(b - truth))
        # The per-subject difference is over the shared cuffs only.
        assert entry["mean_minus_ppg"] == pytest.approx(
            np.mean([np.mean(v) for v in by.values()]))
        # Endpoint 10 reports its own pairing; both phase models use the main
        # features, so every main-set cuff is shared.
        ten = report[target]["10_pat_given_phase"]
        assert ten["paired_cuffs"] == ten["main_set_cuffs"] == main_set
        assert ten["paired_subjects"] == len(prep["eligible"])


def test_counts_split_ecg_loss_and_calibration():
    rows = table(16, n=6, sbp_pat=1.0)
    marks = {("SYN_01", "S002", "E02"): "absent", ("SYN_01", "S002", "E03"): "unusable",
             ("SYN_02", "S002", "E04"): "pat", ("SYN_04", "S001", "E01"): "cal"}
    for r in rows:
        mark = marks.get((r["subject_id"], r["session_id"], r["event_id"]))
        if mark in ("absent", "unusable"):
            r["ecg_hr_bpm"], r["ecg_rmssd_ms"], r["pat_ms"] = "", "", ""
            r["flags"] = "ecg:absent" if mark == "absent" else "ecg:too_few_peaks"
        elif mark == "pat":
            r["pat_ms"] = ""
        elif mark == "cal":
            r["ppg_amplitude"] = ""
    counts = ra._counts(ra.prepare(rows, FAST))
    assert counts["ecg_pat_by_subject"]["SYN_01"] == {
        "ecg_absent": 1, "ecg_unusable": 1, "pat_failed": 0, "pat_available": 2}
    assert counts["ecg_pat_by_subject"]["SYN_02"]["pat_failed"] == 1
    assert counts["ecg_pat_by_phase"]["M0"]["ecg_absent"] == 1
    assert counts["ecg_pat_by_phase"]["M1"]["ecg_unusable"] == 1
    assert counts["ecg_pat_by_phase"]["M2"]["pat_failed"] == 1
    cal = counts["calibration_counts"]["SYN_04"]
    assert cal["bp0"] == 2 and cal["ppg_amplitude"] == 1 and cal["pat_ms"] == 2


def test_session2_ecg_counts_cover_subjects_excluded_for_it():
    """Finding 3 of the review: a subject who lost ECG on every session-2 cuff fails
    session 2 and leaves the eligible-only summaries; the all-subject block keeps
    it (4/4), skips pilots, and counts a readjusted session 2."""
    rows = table(17, n=6, sbp_pat=1.0)
    for r in rows:
        key = (r["subject_id"], r["session_id"], r["event_id"])
        if r["subject_id"] == "SYN_01" and r["session_id"] == "S002":
            r.update(ecg_hr_bpm="", ecg_rmssd_ms="", pat_ms="")
            r["flags"] = ("ecg:absent" if r["event_id"] in ("E01", "E02")
                          else "ecg:too_few_peaks")
        if r["subject_id"] == "SYN_02":
            r["pilot"] = 1
        if key == ("SYN_03", "S002", "E01"):
            r.update(status="no_result", sbp_mmhg="", dbp_mmhg="")
        if key == ("SYN_04", "S002", "E02"):
            r["led_readjusted"] = 1
    counts = ra._counts(ra.prepare(rows, FAST))
    assert "SYN_01" not in counts["ecg_loss_share"]  # the gap this block closes
    block = counts["session2_all_subjects"]
    subjects = block["by_subject"]
    assert sorted(subjects) == ["SYN_00", "SYN_01", "SYN_03", "SYN_04", "SYN_05"]
    assert subjects["SYN_01"] == {
        "rows": 4, "valid_cuffs": 4, "ecg_lost": 4, "ecg_absent": 2, "ecg_unusable": 2,
        "pat_failed": 0, "pat_available": 0, "ecg_loss_share": 1.0,
        "led_readjusted": False, "eligible": False,
        "excluded_reason": "session2_not_passing"}
    # A cuff without a result leaves the denominator, not the row count.
    assert subjects["SYN_03"]["rows"] == 4 and subjects["SYN_03"]["valid_cuffs"] == 3
    assert subjects["SYN_03"]["ecg_loss_share"] == 0.0 and subjects["SYN_03"]["eligible"]
    assert subjects["SYN_04"]["led_readjusted"] and not subjects["SYN_04"]["eligible"]
    phase = block["ecg_pat_by_phase"]
    assert phase["M0"]["ecg_absent"] == 2
    assert phase["M1"]["ecg_unusable"] == 1 and phase["M2"]["ecg_unusable"] == 1
    # M0 with PAT: two each for SYN_00, SYN_04, SYN_05, one for SYN_03.
    assert phase["M0"]["pat_available"] == 7


def test_committed_unchanged_sees_through_assume_unchanged(tmp_path):
    import subprocess

    from scripts.run_b2_pulsedb import committed_unchanged

    def git(*args):
        subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", *args],
                       cwd=tmp_path, check=True, capture_output=True)

    git("init", "-q")
    path = tmp_path / "code.py"
    path.write_text("ALPHA = 1\n", encoding="utf-8")
    git("add", "code.py")
    git("commit", "-q", "-m", "x")
    assert committed_unchanged(tmp_path, path)
    git("update-index", "--assume-unchanged", "code.py")
    path.write_text("ALPHA = 37\n", encoding="utf-8")
    assert not committed_unchanged(tmp_path, path)


def test_a_secondary_model_that_cannot_be_fitted_does_not_stop_the_main_result():
    # Only SYN_00 keeps its M1 cuffs: in the fold that holds SYN_00 out, the M1
    # indicator of the endpoint 10 models is 0 on every training cuff, so they
    # cannot be fitted there. Before 2026-11-15 this stopped the whole analysis.
    rows = table(1, n=16)
    for r in rows:
        if r["phase"] == "M1" and r["subject_id"] != "SYN_00":
            r["status"], r["sbp_mmhg"], r["dbp_mmhg"] = "no_result", "", ""
    report = ra.analyze(rows, FAST)
    failures = report["main"]["model_fit_failures"]
    assert set(failures) == {f"{t}|{m}" for t in ra.TARGETS
                             for m in ("phase_ppg", "phase_ppg_pat")}
    assert all(f["held_out"] == "SYN_00" for v in failures.values() for f in v)
    for t in ra.TARGETS:
        assert "not_computed" in report["secondary"][t]["10_pat_given_phase"]
        assert report["secondary"][t]["model_phase_ppg"]["fit_failures"]
    # The main result is that of the same analysis without the endpoint 10 models.
    lean = copy.deepcopy(FAST)
    for m in ("phase_ppg", "phase_ppg_pat"):
        del lean["models"][m]
    del lean["comparison"]["with_phase"]
    other = ra.analyze(rows, lean)
    assert other["main"]["model_fit_failures"] == {}
    for t in ra.TARGETS:
        assert (report["main"]["targets"][t]["contrasts"]
                == other["main"]["targets"][t]["contrasts"])
        assert (report["main"]["targets"][t]["main_conclusion"]
                == other["main"]["targets"][t]["main_conclusion"])


def test_a_main_model_that_cannot_be_fitted_still_stops(monkeypatch):
    ridge = ra.loso_ridge
    full = FAST["models"][FAST["comparison"]["full"]]["features"]

    def broken(train, test, features, alpha, target, with_phase=False):
        if list(features) == full and not with_phase:
            raise ValueError("A feature is constant over the training cuffs of a fold")
        return ridge(train, test, features, alpha, target, with_phase)

    monkeypatch.setattr(ra, "loso_ridge", broken)
    with pytest.raises(ValueError, match="constant"):
        ra.analyze(table(2, n=6), FAST)


def test_cuffs_without_the_locked_led_codes_leave_main_training_and_calibration():
    # SAP sections 2-4, amended 2026-11-15: a cuff measured without the locked LED
    # codes (ppg:led_not_locked) leaves the calibration, the main set and the
    # training set on its own; endpoint 6 takes it back, calibration included.
    rows = table(11, n=6, sbp_pat=1.0)
    flagged = {("SYN_01", "S002", "E03"), ("SYN_02", "S001", "E01"),
               ("SYN_03", "S001", "E01"), ("SYN_03", "S001", "E02")}
    for r in rows:
        if (r["subject_id"], r["session_id"], r["event_id"]) in flagged:
            r["flags"] = "ppg:led_not_locked"
    prep = ra.prepare(rows, FAST)
    cuff = {(c["subject"], c["session"], c["event_id"]): c for c in prep["cuffs"]}
    assert not cuff[("SYN_01", 2, "E03")]["in_main"]
    assert not cuff[("SYN_01", 2, "E03")]["trainable"]
    assert all(cuff[("SYN_01", 2, e)]["in_main"] for e in ("E01", "E02", "E04"))
    # SYN_02 calibrates on its other session-1 M0 cuff only.
    assert prep["calibration_counts"]["SYN_02"]["bp0"] == 1
    assert cuff[("SYN_02", 1, "E02")]["delta_bp"] == pytest.approx([0.0, 0.0])
    assert prep["excluded"] == {"SYN_03": "session1_m0_led_not_locked"}
    report = ra.analyze(rows, FAST)
    counts = report["counts"]
    assert counts["led_not_locked_by_subject"] == {
        "SYN_00": 0, "SYN_01": 1, "SYN_02": 1, "SYN_03": 2, "SYN_04": 0, "SYN_05": 0}
    assert counts["skipped_by_phase"]["M1"]["led_not_locked"] == 1
    assert counts["skipped_by_phase"]["M1"]["valid_not_computable"] == 0
    # Endpoint 6: SYN_01's cuff and the 4 session-2 cuffs of SYN_03 come back.
    assert report["secondary"]["6_with_led_readjusted"]["main_cuffs_change"] == 5
