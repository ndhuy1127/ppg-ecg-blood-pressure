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


def test_one_set_of_draws_serves_both_differences():
    rng = np.random.default_rng(3)
    counts = sim.draw_counts(50, 8, rng)
    assert counts.shape == (50, 8) and (counts.sum(axis=1) == 8).all()
    values = rng.normal(0, 1, (5, 8))
    assert np.array_equal(sim.bootstrap_ci(values, counts, 0.95)[0],
                          sim.bootstrap_ci(values.copy(), counts, 0.95)[0])
