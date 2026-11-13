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


def table(seed, n=20, sessions=3, sbp_pat=0.0, dbp_pat=0.0, drop=()):
    """Cuffs M0, M0, M1, M2 per session. True change: day effect (0 in session 1)
    plus M1 -4 / M2 +8 (SBP; DBP 0.6 x with its own day effect). PAT falls by
    ``sbp_pat`` ms per mmHg of the true SBP change and ``dbp_pat`` per mmHg of
    DBP; PPG features are weak and HR marks M2. ``drop``: (subject, session)
    removed."""
    rng = np.random.default_rng(seed)
    rows = []
    for s in range(n):
        m2_s, m2_d = rng.normal(8, 3), rng.normal(5, 2)
        for k in range(1, sessions + 1):
            if (s, k) in drop:
                continue
            day_s = 0 if k == 1 else rng.normal(0, 5)
            day_d = 0 if k == 1 else rng.normal(0, 4)
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
    report = ra.analyze(table(1, sbp_pat=2.0, dbp_pat=1.0), FAST)
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
    rows = table(4, sbp_pat=2.0, drop={(0, 2), (0, 3)})
    # Subject 1: session 1 has one valid computable cuff left -> session 1 fails.
    rows = [r for r in rows if not (r["subject_id"] == "SYN_01" and r["session_id"] == "S001"
                                    and r["event_id"] in ("E02", "E03", "E04"))]
    # Subject 2: ECG lost (no PAT, no ECG HR) in session 2, session 3 still passes.
    for r in rows:
        if r["subject_id"] == "SYN_02" and r["session_id"] == "S002":
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
    assert report["subjects"]["excluded"] == {"SYN_00": "no_later_session_passing",
                                              "SYN_01": "session1_not_passing"}
    assert report["subjects"]["eligible"] == 18
    assert report["counts"]["ecg_loss_share"]["SYN_02"] == pytest.approx(0.5)
    assert report["counts"]["ecg_loss_share"]["SYN_05"] == 0
    assert report["counts"]["main_cuffs"] == 18 * 8 - 4 - 1 - 1
    skipped = report["counts"]["skipped_by_phase"]
    assert skipped["M0"]["not_valid"] == 1 and skipped["M1"]["valid_not_computable"] == 2
    # Endpoint 3 keeps the cuffs without PAT for PPG-only.
    assert report["secondary"]["3_ppg_only_all_cuffs"]["SBP"]["n_cuffs"] == 18 * 8 - 1


def test_safety_stops_are_kept_in_main_and_dropped_in_endpoint_7():
    rows = table(5, sbp_pat=2.0)
    for r in rows:
        if r["subject_id"] == "SYN_04" and r["phase"] == "M2" and r["session_id"] != "S001":
            r["safety_stop"] = 1
    report = ra.analyze(rows, FAST)
    assert report["counts"]["safety_stop_in_main"] == 2
    assert report["counts"]["main_cuffs"] == 20 * 8
    endpoint = report["secondary"]["7_without_safety_stops"]
    assert endpoint["rows_dropped"] == 2
    assert endpoint["main_cuffs"] == 20 * 8 - 2 and endpoint["main_cuffs_change"] == -2
    # Any 0/1 spelling counts; one reader for every 0/1 column.
    for r in rows:
        if r["safety_stop"] == 1:
            r["safety_stop"] = "true"
    again = ra.analyze(rows, FAST)["secondary"]["7_without_safety_stops"]
    assert again["rows_dropped"] == 2


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
    preds, _ = ra._fold_predictions(prep, FAST)
    changed = copy.deepcopy(rows)
    for r in changed:
        if r["subject_id"] == "SYN_00" and r["session_id"] != "S001":
            r["sbp_mmhg"] += 30
    prep2 = ra.prepare(changed, FAST)
    preds2, _ = ra._fold_predictions(prep2, FAST)
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
    n, sessions = 10, 3
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
    return [{**r, "source_type": "DEVICE", "led_readjusted": 0, "pilot": 0} for r in rows]


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
    assert "SYN_01" in prep["eligible"]  # session 3 still passes
    later = [c for c in prep["cuffs"] if c["subject"] == "SYN_01" and c["session"] == 3]
    assert all(c["in_main"] for c in later)


def test_pilot_subject_is_excluded_and_real_rows_need_the_columns():
    rows = table(10, n=6)
    for r in rows:
        if (r["subject_id"], r["session_id"], r["event_id"]) == ("SYN_02", "S003", "E04"):
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
    assert skipped["later_sessions_without_main_cuff"] == 10


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
    assert endpoint["evaluated_cuffs_by_subject"]["SYN_05"] == [0, 8]
    assert endpoint["n_folds"] == 19 and endpoint["main_cuffs_change"] == -8
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
                for candidate in (mod.replace(".", "/") + ".py",
                                  mod.replace(".", "/") + "/__init__.py"):
                    if (ROOT / candidate).is_file():
                        todo.append(candidate)
    return seen


def test_lock_covers_every_module_of_the_analysis_and_the_feature_step():
    from scripts import device_session

    feature = _local_imports(["scripts/device_session.py"])
    assert feature <= set(device_session.CODE)
    every = _local_imports(["scripts/run_rq1_analysis.py", "scripts/device_session.py"])
    assert every <= set(run_rq1_analysis.LOCKED)
    assert device_session.CONFIG in run_rq1_analysis.LOCKED


def _provenance(path, **override):
    from scripts import device_session
    from software._provenance import text_file_sha256

    prov = {"source_type": "DEVICE", "git_commit": "abc", "git_dirty": False,
            "code_sha256": {c: text_file_sha256(ROOT / c) for c in device_session.CODE},
            "config_sha256": text_file_sha256(ROOT / device_session.CONFIG), **override}
    (path.parent / "provenance.json").write_text(json.dumps(prov))


def test_feature_provenance_gate(tmp_path, monkeypatch):
    import scripts.run_b2_pulsedb as b2

    monkeypatch.setattr(b2, "committed_unchanged", lambda repo, p: True)
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps({**FAST, "status": "LOCKED"}))
    cases = {
        "none": None,
        "dirty": {"git_dirty": True},
        "code": {"code_sha256": {}},
        "config": {"config_sha256": "0" * 64},
        "source": {"source_type": "SYNTHETIC"},
    }
    messages = {"none": "no provenance.json", "dirty": "uncommitted workspace",
                "code": "feature code differs", "config": "feature config differs",
                "source": "provenance.json says"}
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
    assert report["provenance"]["feature_provenance"][str(path)]["git_dirty"] is False


def test_rows_labelled_synthetic_with_device_provenance_are_refused(tmp_path):
    path = _write(tmp_path / "cuff_features.csv", table(8, n=8))
    _provenance(path)  # the logger says DEVICE, the rows say SYNTHETIC
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(FAST))
    with pytest.raises(ValueError, match="provenance.json says 'DEVICE'"):
        run_rq1_analysis.run([path], config_path, tmp_path / "out")
