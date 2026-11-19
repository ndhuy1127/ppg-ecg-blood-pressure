"""Checks of the RQ1 sensitivity simulation (SAP v1 section 9). No human data.

Answers come from the SAP: the readings of section 7, a subject-level percentile
bootstrap of the mean, d_s = MAE(PPG+PAT) - MAE(PPG-only) per subject, zero-change
predicting 0, and R3 as the median over subjects of the per-subject median |ΔBP|.
"""

import json
from pathlib import Path

import numpy as np

from software.evaluation import rq1_sensitivity as sim

CONFIG = json.loads((Path(__file__).resolve().parents[1]
                     / "configs/analysis/rq1_sensitivity_v1.json").read_bytes())


def test_readings_follow_the_sap():
    low = np.array([-3.0, -2.5, -0.5, 0.5, -3.0, -1.0])
    high = np.array([-2.5, -1.0, 0.5, 3.0, 1.0, -0.2])
    assert sim.reading(low, high, 2.0).tolist() == [
        "benefit_at_delta", "benefit_below_delta", "equivalent", "harm", "inconclusive",
        "equivalent"]


def test_bootstrap_of_a_constant_is_the_constant_and_the_ci_covers_the_mean():
    rng = np.random.default_rng(1)
    low, high = sim.bootstrap_ci(np.full((3, 10), 2.0), sim.draw_counts(200, 10, rng),
                                 0.95)
    assert np.allclose(low, 2.0) and np.allclose(high, 2.0)
    values = rng.normal(0, 1, (400, 30))
    low, high = sim.bootstrap_ci(values, sim.draw_counts(400, 30, rng), 0.95)
    covered = np.mean((low < 0) & (high > 0))
    assert 0.88 < covered < 0.99  # percentile bootstrap, n = 30


def test_null_models_give_no_difference_and_zero_change_has_error_of_the_reference():
    rng = np.random.default_rng(2)
    target = CONFIG["targets"]["SBP"]
    d, d0, sd, reference = sim.simulate_d(rng, 400, 20, 3, target,
                                          target["models"]["null"], target["m2"]["narrow"])
    assert d.shape == (400, 20) and reference.shape == (400, 20, 2, 4)
    assert abs(d.mean()) < 0.05
    assert d0.mean() > 0  # a noisy model loses to zero-change when ΔBP is small
    assert 4 < np.median(sd) < 8


def test_same_seed_same_result_and_r3_definition():
    target = CONFIG["targets"]["DBP"]
    args = (5, 100, 50, 15, 2, target, target["models"]["benefit"],
            target["m2"]["wide"], target["deltas"], [0.95])
    assert sim.run_design(*args) == sim.run_design(*args)
    reference = np.array([[[[1.0, -3.0, 2.0, 10.0]], [[0.0, 1.0, -1.0, 4.0]]]])
    # Subject medians of |x|: 2.5 and 1.0; their median is 1.75.
    assert sim.r3_statistic(reference).tolist() == [1.75]
    # P2 from the first session: M2 minus the mean of the two M0: 11 and 3.5.
    assert sim.p2_statistic(reference).tolist() == [7.25]


def test_ci_methods_known_answers():
    rng = np.random.default_rng(4)
    counts = sim.draw_counts(200, 10, rng)
    for method in sim.CI_METHODS:  # a constant has a zero-width CI in every method
        low, high = sim.interval(np.full((3, 10), 2.0), counts, 0.95, method)
        assert np.allclose(low, 2.0) and np.allclose(high, 2.0)
    # Student t by hand: mean 2.5, SD 1.2910, SE 0.6455, t(3; 0.975) = 3.1824.
    low, high = sim.interval(np.array([[1.0, 2.0, 3.0, 4.0]]),
                             sim.draw_counts(10, 4, rng), 0.95, "student_t")
    assert np.allclose([low[0], high[0]], [2.5 - 2.0543, 2.5 + 2.0543], atol=1e-3)
    # Row quantiles: position 0.5 * 4 = 2 and 0.1 * 4 = 0.4 on 0..4.
    from software.evaluation.mean_intervals import row_quantile

    ordered = np.array([[0.0, 1.0, 2.0, 3.0, 4.0], [0.0, 1.0, 2.0, 3.0, 4.0]])
    assert np.allclose(row_quantile(ordered, np.array([0.5, 0.1])), [2.0, 0.4])
    try:
        sim.interval(np.zeros((1, 4)), counts[:, :4], 0.95, "unknown")
    except ValueError:
        pass
    else:
        raise AssertionError("an unknown CI method must be refused")


def test_percentile_under_covers_at_15_subjects_and_t_methods_do_not():
    # Normal d_s with true mean 0: a 95 % CI should miss 0 in 5 % of samples.
    rates = sim.ci_error_rates([6, 15], "normal", 15, 4000, 1000, [0.95],
                               sim.CI_METHODS)
    missed = {m: r["0.95"]["below"] + r["0.95"]["above"] for m, r in rates.items()}
    assert missed["percentile"] > 0.065  # (n-1)/n variance and normal quantiles
    for method in ("bootstrap_t", "student_t"):
        assert 0.035 < missed[method] < 0.065
    assert rates["bootstrap_t"]["0.95"]["width"] > rates["percentile"]["0.95"]["width"]


def test_envelope_is_the_wider_limit_of_the_two_t_intervals():
    rng = np.random.default_rng(9)
    values = sim.check_sample(rng, "skew_right", (50, 15))
    counts = sim.draw_counts(300, 15, rng)
    low, high = sim.interval(values, counts, 0.95, "t_envelope")
    for method in ("bootstrap_t", "student_t"):
        other_low, other_high = sim.interval(values, counts, 0.95, method)
        assert (low <= other_low).all() and (high >= other_high).all()
    low_t, high_t = sim.interval(values, counts, 0.95, "student_t")
    low_b, high_b = sim.interval(values, counts, 0.95, "bootstrap_t")
    assert np.array_equal(low, np.minimum(low_t, low_b))
    assert np.array_equal(high, np.maximum(high_t, high_b))


def test_draw_blocks_give_each_block_its_own_draws():
    target = CONFIG["targets"]["DBP"]
    args = (10, 120, 60, 15, 3, target, target["models"]["null"],
            target["m2"]["narrow"], target["deltas"], [0.95])
    one = sim.run_design(*args)
    assert one == sim.run_design(*args, draw_blocks=1)  # v1 behaviour by default
    four = sim.run_design(*args, draw_blocks=4)
    # Same simulated studies (same mean d); only the bootstrap draws differ.
    assert four["mean_d"] == one["mean_d"]
    assert four["levels"]["0.95"]["ci_width_mean"] != one["levels"]["0.95"]["ci_width_mean"]


def test_check_shapes_have_mean_zero_and_unit_variance():
    rng = np.random.default_rng(7)
    for name in sim.CHECK_DISTRIBUTIONS:
        sample = sim.check_sample(rng, name, (400000,))
        assert abs(sample.mean()) < 0.02, name
        assert abs(sample.var() - 1) < 0.25, name  # t3 converges slowly


def test_run_design_reports_every_method_and_keeps_the_percentile_numbers():
    target = CONFIG["targets"]["SBP"]
    args = (8, 200, 100, 15, 2, target, target["models"]["null"],
            target["m2"]["moderate"], target["deltas"], [0.95, 0.975])
    old = sim.run_design(*args)
    new = sim.run_design(*args, methods=sim.CI_METHODS, primary="bootstrap_t")
    assert old["ci_method"] == "percentile" and new["ci_method"] == "bootstrap_t"
    assert set(new["ci_methods"]) == set(sim.CI_METHODS)
    # Same seed and draws: adding methods leaves the percentile results unchanged.
    assert new["ci_methods"]["percentile"] == old["ci_methods"]["percentile"]
    assert (new["levels"]["0.95"]["p_upper_below_0"]
            == new["ci_methods"]["bootstrap_t"]["0.95"]["p_upper_below_0"])
    shares = new["levels"]["0.95"]["readings"][str(target["deltas"][1])]
    assert abs(sum(shares.values()) - 1) < 1e-9


def test_config_v2_keeps_the_v1_assumptions():
    v2 = json.loads((Path(__file__).resolve().parents[1]
                     / "configs/analysis/rq1_sensitivity_v2.json").read_bytes())
    for key in ("seed", "replicates", "bootstrap_draws", "levels", "targets",
                "p2_grid", "subject_grid"):
        assert v2[key] == CONFIG[key], key
    assert set(v2["ci_methods"]) == set(sim.CI_METHODS)
    assert v2["primary_ci_method"] in v2["ci_methods"]
    assert set(v2["ci_check"]["distributions"]) <= set(sim.CHECK_DISTRIBUTIONS)


def test_runner_summary_has_the_method_and_reading_tables():
    from scripts.simulate_rq1_sensitivity import run, run_ci_check, summary

    v2 = json.loads((Path(__file__).resolve().parents[1]
                     / "configs/analysis/rq1_sensitivity_v2.json").read_bytes())
    small = {**v2, "replicates": 30, "bootstrap_draws": 40, "subject_grid": [15],
             "ci_check": {"subjects": [15], "distributions": ["normal"],
                          "replicates": 30,
                          "convergence": {"distribution": "normal", "subjects": 15,
                                          "draws": [20, 40]}}}
    results = run(small)
    text = summary(results, small, run_ci_check(small))
    assert f"CI method of the tables below: `{v2['primary_ci_method']}`" in text
    assert "## Number of bootstrap draws" in text
    assert "## SBP, CI methods when PAT adds nothing" in text
    assert "## DBP, readings of SAP section 7 at δ = 1.5" in text
    assert "## CI method check on mean-zero d_s of several shapes" in text
    # A v1 config (no CI keys) still runs, with the percentile CI as before.
    old = {**CONFIG, "replicates": 30, "bootstrap_draws": 40, "subject_grid": [15]}
    assert "`percentile`" in summary(run(old), old)


def test_m6_adds_one_cuff_and_leaves_the_v2_draws_alone():
    target = CONFIG["targets"]["SBP"]
    args = (11, 80, 60, 15, 2, target, target["models"]["strong"],
            target["m2"]["moderate"], target["deltas"], [0.95])
    assert sim.run_design(*args) == sim.run_design(*args, m6=None)
    assert sim.session_cuffs() == sim.CUFFS
    assert sim.session_cuffs({"m6_mean": 10, "m6_sd": 0}) == (*sim.CUFFS, "M6")
    m6 = sim.run_design(*args, m6={"m6_mean": 20.0, "m6_sd": 6.0})
    assert m6["eval_cuffs_per_subject"] == 5 and "p6_median" in m6
    assert "p6_median" not in sim.run_design(*args)


def test_p6_tracks_the_m6_response_with_a_noise_free_cuff():
    rng = np.random.default_rng(12)
    target = {**CONFIG["targets"]["SBP"], "sigma_cuff": 0.0, "tau_day": 0.0}
    m6 = {"m6_mean": 18.0, "m6_sd": 0.0}
    *_, reference = sim.simulate_d(rng, 5, 10, 2, target, target["models"]["null"],
                                   target["m2"]["moderate"], m6)
    cuffs = sim.session_cuffs(m6)
    assert reference.shape == (5, 10, 1, 5)
    # No day effect and no cuff noise: M0 changes are 0 and M6 is exactly +18.
    assert np.allclose(reference[..., cuffs.index("M6")], 18.0)
    assert np.allclose(sim.p2_statistic(reference, cuffs, "M6"), 18.0)


def test_repeat_scales_only_the_listed_phases():
    target = {**CONFIG["targets"]["SBP"], "tau_day": 0.0, "m1_mean": 0.0, "m1_sd": 0.0}
    args = (20, 4, 2, target, target["models"]["null"],
            {"m2_mean": 0.0, "m2_sd": 0.0})
    base = sim.simulate_d(np.random.default_rng(13), *args)[3]
    # rho = -1: two perfectly opposed errors cancel, so M1 and M2 equal minus BP0 error.
    rep = sim.simulate_d(np.random.default_rng(13), *args,
                         repeat={"phases": ["M1", "M2"], "rho": -1.0})[3]
    m0 = [i for i, c in enumerate(sim.CUFFS) if c == "M0"]
    assert np.array_equal(rep[..., m0], base[..., m0])
    # No true change: both averaged phases hold only minus the BP0 error.
    assert np.allclose(rep[..., sim.CUFFS.index("M2")], rep[..., sim.CUFFS.index("M1")])
    same = sim.simulate_d(np.random.default_rng(13), *args,
                          repeat={"phases": ["M1", "M2"], "rho": 1.0})[3]
    assert np.allclose(same, base)  # rho = 1: averaging does not help


def test_no_pat_gain_at_m6_gives_the_ppg_slope_there():
    target = {**CONFIG["targets"]["SBP"], "sigma_cuff": 0.0}
    models = {"ppg": {"b": 0.3, "sigma_u": 0.0, "sigma_v": 0.0},
              "ppg_pat": {"b": 0.8, "sigma_u": 0.0, "sigma_v": 0.0},
              "rho_u": 0.0, "rho_v": 0.0}
    args = (np.random.default_rng(14), 3, 6, 2, target, models,
            {"m2_mean": 0.0, "m2_sd": 0.0})
    m6 = {"m6_mean": 20.0, "m6_sd": 0.0}
    gain = sim.simulate_d(*args, m6={**m6, "pat_gain": True}, extras=True)[4]
    args = (np.random.default_rng(14), *args[1:])
    flat = sim.simulate_d(*args, m6={**m6, "pat_gain": False}, extras=True)[4]
    # Same draws; only the M6 cuff differs, and only for PPG+PAT.
    assert np.allclose(gain["d_core"], flat["d_core"])
    assert (flat["d_true"] > gain["d_true"]).all()
    assert gain["mae_ppg"] == flat["mae_ppg"]


def test_v3_rules_and_a_small_run():
    from scripts.simulate_rq1_sensitivity import (resting_median, rule_delta,
                                                  run_v3, summary_v3)

    rule = {"factor": 0.5, "floor": 1.0, "step": 0.5}
    assert [rule_delta(s, rule) for s in (1.0, 2.5, 3.0, 4.0, 5.0, 7.0)] == [
        1.0, 1.5, 1.5, 2.0, 2.5, 3.5]
    # v2 calibration: tau 2.5 and sigma 3 give a resting median of about 3 mmHg.
    assert abs(resting_median(2.5, 3.0) - 3.0) < 0.01
    v3 = json.loads((Path(__file__).resolve().parents[1]
                     / "configs/analysis/rq1_sensitivity_v3.json").read_bytes())
    assert v3["targets"] == json.loads((Path(__file__).resolve().parents[1]
                                        / "configs/analysis/rq1_sensitivity_v2.json"
                                        ).read_bytes())["targets"]
    small = {**v3, "replicates": 20, "bootstrap_draws": 30, "designs": [[32, 2]],
             "noise_levels": {"SBP": [5.0], "DBP": [4.0]},
             "decision_check": {**v3["decision_check"], "bootstrap_draws": 40}}
    results, decision = run_v3(small)
    # 3 M2 x 5 M6 x 2 repeat x 3 models per target; check rows: null and strong.
    assert len(results) == 2 * 3 * 5 * 2 * 3 and len(decision) == 2 * 2
    assert all("mean_d_true" in r for r in results)
    text = summary_v3(results, decision, small)
    assert "## Decision check (40 bootstrap draws)" in text
    assert "## SBP, options at 32 × 2" in text
    assert text.count("| pass |") + text.count("| **fail** |") == 2  # R1: SBP, DBP


def test_one_set_of_draws_serves_both_differences():
    rng = np.random.default_rng(3)
    counts = sim.draw_counts(50, 8, rng)
    assert counts.shape == (50, 8) and (counts.sum(axis=1) == 8).all()
    values = rng.normal(0, 1, (5, 8))
    assert np.array_equal(sim.bootstrap_ci(values, counts, 0.95)[0],
                          sim.bootstrap_ci(values.copy(), counts, 0.95)[0])
