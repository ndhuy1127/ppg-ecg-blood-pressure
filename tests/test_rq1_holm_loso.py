"""Checks of the joint Holm and LOSO Ridge simulations (SAP v1 sections 4-6). No
human data. Answers come from the SAP text (Holm steps, Ridge without intercept,
SD scaling without centring, equal subject weights) and from a naive per-fold
solve written independently here."""

import json
from pathlib import Path

import numpy as np
import pytest

from software.evaluation import rq1_holm_loso as sim
from software.evaluation.rq1_sensitivity import simulate_d

ROOT = Path(__file__).resolve().parents[1]
BASE = json.loads((ROOT / "configs/analysis/rq1_sensitivity_v2.json").read_bytes())
CONFIG = json.loads((ROOT / "configs/analysis/rq1_holm_loso_v1.json").read_bytes())


def test_holm_follows_the_four_steps_of_the_sap():
    t, f = True, False
    # (SBP 97.5, DBP 97.5, SBP 95, DBP 95) -> declared (SBP, DBP)
    cases = {
        (t, t, t, t): (t, t),   # step 3: both pass at 97.5 %
        (t, f, t, t): (t, t),   # step 2: DBP then tested at 95 %
        (t, f, t, f): (t, f),
        (f, t, f, t): (f, t),
        (f, t, t, t): (t, t),
        (f, f, t, t): (f, f),   # step 4: nothing passes at 97.5 %, stop
    }
    for (a, b, c, d), expected in cases.items():
        sbp, dbp = sim.holm(*(np.array([v]) for v in (a, b, c, d)))
        assert (bool(sbp[0]), bool(dbp[0])) == expected


def test_rho_one_with_identical_targets_gives_identical_outcomes():
    targets = {t: BASE["targets"]["SBP"] for t in ("SBP", "DBP")}
    models = {t: BASE["targets"]["SBP"]["models"]["benefit"] for t in targets}
    effects = {t: BASE["targets"]["SBP"]["m2"]["moderate"] for t in targets}
    out = sim.simulate_joint(np.random.default_rng(3), 20, 8, 3, targets, models,
                             effects, 1.0)
    for a, b in zip(out["SBP"], out["DBP"]):
        np.testing.assert_allclose(a, b)


def test_joint_sbp_marginal_matches_the_single_outcome_model():
    # The recorder draws standard normals and scales them, so SBP of the joint run
    # equals simulate_d on the same seed whenever numpy's normal() does the same.
    target = BASE["targets"]["SBP"]
    args = (40, 10, 2, target, target["models"]["benefit"], target["m2"]["moderate"])
    single = simulate_d(np.random.default_rng(5), *args)
    targets = {"SBP": target, "DBP": BASE["targets"]["DBP"]}
    joint = sim.simulate_joint(
        np.random.default_rng(5), 40, 10, 2, targets,
        {t: targets[t]["models"]["benefit"] for t in targets},
        {t: targets[t]["m2"]["moderate"] for t in targets}, 0.6)
    np.testing.assert_allclose(joint["SBP"][0], single[0])
    np.testing.assert_allclose(joint["SBP"][1], single[1])


def test_dbp_correlation_with_sbp_draws_is_rho():
    rng = np.random.default_rng(7)
    recorder = sim._Recorder(rng)
    z = recorder.standard_normal((200_000,))
    follower = sim._Follower(rng, recorder.draws, 0.6)
    assert np.corrcoef(z, follower.standard_normal((200_000,)))[0, 1] == pytest.approx(
        0.6, abs=0.01)
    with pytest.raises(ValueError):
        follower.standard_normal((3,))


def _naive_loso(x, y, alpha):
    r, n, k, c, f = x.shape
    out = np.empty(y.shape)
    for rep in range(r):
        for s in range(n):
            keep = [i for i in range(n) if i != s]
            xt = x[rep, keep].reshape(-1, f)
            yt = y[rep, keep].reshape(-1)
            sd = xt.std(axis=0, ddof=1)
            w = np.full(len(yt), 1.0 / (k * c))  # each training subject total 1
            xs = xt / sd
            beta = np.linalg.solve(xs.T @ (w[:, None] * xs) + alpha * np.eye(f),
                                   xs.T @ (w * yt))
            out[rep, s] = (x[rep, s] / sd) @ beta
    return out


def test_loso_ridge_matches_a_naive_fold_by_fold_solve():
    rng = np.random.default_rng(11)
    x = rng.normal(size=(3, 6, 2, 4, 3)) + 0.5
    y = x @ np.array([1.0, -2.0, 0.5]) + rng.normal(size=(3, 6, 2, 4))
    np.testing.assert_allclose(sim.loso_ridge(x, y, 1.0), _naive_loso(x, y, 1.0),
                               rtol=1e-10, atol=1e-10)


def test_zero_feature_changes_predict_zero_change():
    rng = np.random.default_rng(2)
    x = rng.normal(size=(1, 5, 2, 4, 2))
    x[0, 0] = 0.0  # held-out subject 0 has no feature change at any cuff
    y = rng.normal(size=(1, 5, 2, 4))
    assert np.all(sim.loso_ridge(x, y, 1.0)[0, 0] == 0.0)


def test_held_out_subject_does_not_enter_its_own_fold():
    rng = np.random.default_rng(4)
    x = rng.normal(size=(1, 5, 2, 4, 2))
    y = rng.normal(size=(1, 5, 2, 4))
    before = sim.loso_ridge(x, y, 1.0)[0, 2]
    y2 = y.copy()
    y2[0, 2] += 100.0  # change only the labels of subject 2
    np.testing.assert_allclose(sim.loso_ridge(x, y2, 1.0)[0, 2], before)


def test_loso_run_is_reproducible_and_reports_every_method():
    spec = CONFIG["loso"]
    target = BASE["targets"]["SBP"]
    features = json.loads(json.dumps(spec["features"]))
    features["pat"]["a"] = 0.0
    args = ([1, 2], 60, 200, 8, 2, target, target["m2"]["moderate"], features,
            spec["base_features"], 1.0, spec["ci_methods"], 0.95, 2, 120)
    first, second = sim.run_loso(*args), sim.run_loso(*args)
    assert first == second
    assert set(first["methods"]) == set(first["shuffled"]) == set(spec["ci_methods"])
    assert set(first["baselines"]) == set(spec["ci_methods"])
    assert first["se_ratio"] > 0 and first["theta_mc_se"] > 0
    m = first["mean_mae"]
    assert first["mean_d_phase"] == pytest.approx(m["ppg_pat"] - m["phase_mean"])
    assert first["mean_d0"] == pytest.approx(m["ppg_pat"] - m["zero_change"])
    b = first["baselines"]["t_envelope"]
    assert b["p_main_and_phase"] <= min(b["p_main"], b["p_d_phase_below_0"])
    assert b["theta_phase_mc_se"] > 0
    w = first["with_phase"]["t_envelope"]
    assert w["theta_mc_se"] > 0 and set(first["with_phase"]) == set(spec["ci_methods"])
    assert first["mean_d_with_phase"] == pytest.approx(
        m["phase_ppg_pat"] - m["phase_ppg"])
    assert 0 <= b["phase_miss_below"] <= 1 and 0 <= b["phase_miss_above"] <= 1


def test_reference_theta_of_several_keys_matches_single_keys():
    spec = CONFIG["loso"]
    target = BASE["targets"]["SBP"]
    features = json.loads(json.dumps(spec["features"]))
    features["pat"]["a"] = 0.1
    args = ([3], 50, 25, 6, 2, target, target["m2"]["moderate"], features,
            spec["base_features"], 1.0)
    both = sim.reference_theta(*args, key=("d", "d_phase"))
    assert both["d"] == sim.reference_theta(*args)
    assert both["d_phase"] == sim.reference_theta(*args, key="d_phase")


def _naive_phase_mean(y, phases):
    r, n, k, c = y.shape
    out = np.empty(y.shape)
    for rep in range(r):
        for s in range(n):
            for j, label in enumerate(phases):
                cols = [i for i, p in enumerate(phases) if p == label]
                # each other subject: mean over its sessions 2..K cuffs of the phase
                means = [y[rep, o, 1:][:, cols].mean() for o in range(n) if o != s]
                out[rep, s, :, j] = np.mean(means)
    return out


def test_phase_mean_matches_a_naive_equal_subject_weight_mean():
    rng = np.random.default_rng(12)
    y = rng.normal(size=(2, 5, 3, 4))
    phases = ("M0", "M0", "M1", "M2")
    np.testing.assert_allclose(sim.phase_mean_loso(y, phases),
                               _naive_phase_mean(y, phases), rtol=1e-12)
    static = sim.phase_mean_loso(y, ("all",) * 4)
    np.testing.assert_allclose(static, _naive_phase_mean(y, ("all",) * 4), rtol=1e-12)
    assert np.all(static == static[..., :1])  # one value for every cuff


def test_phase_mean_ignores_the_held_out_subject_and_session_one():
    rng = np.random.default_rng(13)
    y = rng.normal(size=(1, 4, 3, 4))
    before = sim.phase_mean_loso(y, sim.CUFFS)
    y2 = y.copy()
    y2[0, 1] += 50.0          # labels of the held-out subject 1
    y2[:, :, 0] -= 30.0       # session 1 of everyone
    after = sim.phase_mean_loso(y2, sim.CUFFS)
    np.testing.assert_allclose(after[0, 1], before[0, 1])
    np.testing.assert_allclose(after[0, 0, 0], before[0, 0, 0] + 50.0 / 3)
    with pytest.raises(ValueError):
        sim.phase_mean_loso(y, ("M0", "M1"))


def test_phase_mean_recovers_known_phase_offsets():
    # Every subject has the same change per phase: the baseline predicts it exactly.
    offsets = np.array([1.0, 1.0, -3.0, 8.0])
    y = np.broadcast_to(offsets, (1, 6, 3, 4)).copy()
    np.testing.assert_allclose(sim.phase_mean_loso(y, sim.CUFFS), y)


def test_phase_indicators_mark_m1_m2_and_later_sessions():
    ind = sim.phase_indicators((2, 3, 3, 4))
    assert ind.shape == (2, 3, 3, 4, 3)
    # session 1: M0, M0, M1, M2 -> only the maneuver flags
    np.testing.assert_array_equal(ind[0, 0, 0], [[0, 0, 0], [0, 0, 0], [1, 0, 0],
                                                 [0, 1, 0]])
    # session 2: the "session >= 2" flag is on for every cuff
    np.testing.assert_array_equal(ind[1, 2, 1], [[0, 0, 1], [0, 0, 1], [1, 0, 1],
                                                 [0, 1, 1]])


def test_phase_features_with_exact_phase_offsets_predict_them():
    # Changes are exactly a per-phase offset: Ridge on the indicators alone gets
    # close (shrunk by alpha), and much closer with a tiny alpha.
    offsets = np.array([1.0, 1.0, -3.0, 8.0])
    y = np.zeros((1, 8, 3, 4))
    y[:, :, 1:] = offsets
    y[:, :, 0, 2:] = offsets[2:] - 1.0  # session 1 maneuvers, no session offset
    x = np.array(sim.phase_indicators(y.shape))
    pred = sim.loso_ridge(x, y, 1e-9)
    np.testing.assert_allclose(pred, y, atol=1e-6)


def test_a_constant_training_feature_is_refused():
    rng = np.random.default_rng(6)
    x = rng.normal(size=(1, 4, 2, 4, 2))
    x[..., 1] = 0.0
    with pytest.raises(ValueError):
        sim.loso_ridge(x, rng.normal(size=(1, 4, 2, 4)), 1.0)


def test_session_one_has_no_day_change_and_baselines_are_the_m0_means():
    target = dict(BASE["targets"]["SBP"], sigma_cuff=1.0)
    m0 = [0, 1]
    for noise in (0.0, 1.0):
        features = {"f": {"driver": "bp", "a": 1.0, "g_sd": 0.0, "drift_sd": 0.0,
                          "noise_sd": noise}}
        reference, x = sim.simulate_loso_data(np.random.default_rng(9), 50, 4, 3, target,
                                              target["m2"]["moderate"], features)
        # BP0 and the feature baseline are means of the two session-1 M0 cuffs, so
        # the session-1 M0 changes average to 0 for both.
        np.testing.assert_allclose(reference[:, :, 0, m0].mean(axis=-1), 0.0,
                                   atol=1e-12)
        np.testing.assert_allclose(x[:, :, 0, m0, 0].mean(axis=-1), 0.0, atol=1e-12)
        if noise == 0.0:  # noise-free: the feature is the true change, 0 at M0
            assert np.all(x[:, :, 0, m0, 0] == 0.0)
