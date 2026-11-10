"""Simulated sensitivity of the RQ1 comparison (SAP v1, docs/protocol/sap_v1.md).

No human data: every input is an assumption stated in the config
(configs/analysis/rq1_sensitivity_v1.json) and replaced by pilot values later.
For each design (subjects x sessions) it simulates the RQ1 data the SAP
analyses, computes the per-subject MAE differences d_s (PPG+PAT - PPG-only)
and d0_s (PPG+PAT - zero-change) exactly as the SAP does, takes the
subject-level percentile bootstrap CI of their means, and reports how often each
reading of SAP section 7 comes out. One set of subject draws per simulated study
is shared by d, d0 and every CI level (SAP section 5). SBP and DBP are simulated
apart, so the Holm step of SAP section 6 is not applied: the 95 % and 97.5 %
columns are the per-outcome probabilities before and at Holm's first step. The
P2 statistic of the pilot (median over subjects of the signed M2 change against
the same-session M0 mean) is reported from the first evaluation session.

Per subject s, evaluation session k (2..K) and cuff j (M0, M0, M1, M2):

- true change from the session-1 resting level: day_{s,k} + effect_{s,j}, with
  day ~ N(0, tau_day) per session and effect 0 for M0, M1_s or M2_s for the
  maneuvers (subject-level N(mean, sd));
- reference change = true change + cuff noise N(0, sigma_cuff) minus the
  calibration error of BP0 (mean of two session-1 M0 cuffs, N(0, sigma_cuff/sqrt 2));
- model prediction = b * true change + u_s + v_{s,j} (b: share of the change the
  model tracks, u: subject drift, v: cuff-level error); the two models share
  part of u and v (correlations rho_u, rho_v);
- zero-change predicts 0.
"""

import numpy as np

CUFFS = ("M0", "M0", "M1", "M2")  # per evaluation session (protocol 6.4)
READINGS = ("benefit_at_delta", "benefit_below_delta", "equivalent", "harm",
            "inconclusive")


def _correlated(rng, shape, sd_a, sd_b, rho):
    """Two normal arrays with SDs sd_a, sd_b and correlation rho."""
    z1, z2 = rng.standard_normal(shape), rng.standard_normal(shape)
    return sd_a * z1, sd_b * (rho * z1 + np.sqrt(1 - rho ** 2) * z2)


def simulate_d(rng, replicates, subjects, sessions, target, models, effect):
    """``(d, d0, delta_sd)``: per-subject d_s and d0_s, shape (replicates, subjects),
    and the SD of the reference changes (one value per replicate)."""
    n_eval = sessions - 1
    shape = (replicates, subjects, n_eval, len(CUFFS))
    day = rng.normal(0, target["tau_day"], (replicates, subjects, n_eval, 1))
    m1 = rng.normal(target["m1_mean"], target["m1_sd"], (replicates, subjects, 1, 1))
    m2 = rng.normal(effect["m2_mean"], effect["m2_sd"], (replicates, subjects, 1, 1))
    maneuver = np.zeros((1, 1, 1, len(CUFFS)))
    is_m1 = np.array([c == "M1" for c in CUFFS])
    is_m2 = np.array([c == "M2" for c in CUFFS])
    true = day + np.where(is_m1, m1, 0) + np.where(is_m2, m2, 0) + maneuver
    cal = rng.normal(0, target["sigma_cuff"] / np.sqrt(2), (replicates, subjects, 1, 1))
    reference = true + rng.normal(0, target["sigma_cuff"], shape) - cal
    base, added = models["ppg"], models["ppg_pat"]
    u_p, u_a = _correlated(rng, (replicates, subjects, 1, 1), base["sigma_u"],
                           added["sigma_u"], models["rho_u"])
    v_p, v_a = _correlated(rng, shape, base["sigma_v"], added["sigma_v"],
                           models["rho_v"])
    error_p = base["b"] * true + u_p + v_p - reference
    error_a = added["b"] * true + u_a + v_a - reference
    mae = lambda e: np.abs(e).mean(axis=(2, 3))  # noqa: E731
    mae_a = mae(error_a)
    d = mae_a - mae(error_p)
    d0 = mae_a - mae(-reference)
    delta_sd = reference.reshape(replicates, -1).std(axis=1, ddof=1)
    return d, d0, delta_sd, reference


def draw_counts(draws, subjects, rng):
    """How often each subject is drawn in each bootstrap draw: (draws, subjects)."""
    counts = np.zeros((draws, subjects))
    picks = rng.integers(0, subjects, (draws, subjects))
    np.add.at(counts, (np.repeat(np.arange(draws), subjects), picks.ravel()), 1)
    return counts


def bootstrap_ci(values, counts, level):
    """Percentile CI of the mean over subjects (axis 1) for the given draws;
    ``values`` (replicates, subjects) -> (low, high) arrays."""
    means = values @ counts.T / values.shape[1]  # (replicates, draws)
    alpha = 1 - level
    return (np.quantile(means, alpha / 2, axis=1),
            np.quantile(means, 1 - alpha / 2, axis=1))


def reading(low, high, delta):
    """SAP section 7 reading of a CI [low, high] of mean d_s against delta."""
    return np.select(
        [high < -delta, (high < 0) & (low < -delta),
         (low >= -delta) & (high <= delta), (low > 0) & (high > delta)],
        list(READINGS[:4]), READINGS[4])


def p2_statistic(reference):
    """Median over subjects of the signed M2 change against the mean of the M0
    cuffs of the same (first evaluation) session: the P2 statistic of the pilot."""
    first = reference[:, :, 0, :]
    m0 = first[:, :, [i for i, c in enumerate(CUFFS) if c == "M0"]].mean(axis=2)
    m2 = first[:, :, CUFFS.index("M2")]
    return np.median(m2 - m0, axis=1)


def r3_statistic(reference):
    """Median over subjects of each subject's median |reference change| (R3)."""
    flat = np.abs(reference).reshape(reference.shape[0], reference.shape[1], -1)
    return np.median(np.median(flat, axis=2), axis=1)


def run_design(seed, replicates, draws, subjects, sessions, target, models, effect,
               deltas, levels):
    rng = np.random.default_rng(seed)
    d, d0, delta_sd, reference = simulate_d(rng, replicates, subjects, sessions,
                                            target, models, effect)
    out = {"subjects": subjects, "sessions": sessions,
           "visits": subjects * sessions,
           "eval_cuffs_per_subject": (sessions - 1) * len(CUFFS),
           "mean_d": float(d.mean()), "mean_d0": float(d0.mean()),
           "reference_delta_sd": float(np.median(delta_sd)),
           "r3_median": float(np.median(r3_statistic(reference))),
           "p2_median": float(np.median(p2_statistic(reference))),
           "levels": {}}
    counts = draw_counts(draws, subjects, rng)  # shared by d, d0 and every level
    for level in levels:
        low, high = bootstrap_ci(d, counts, level)
        low0, high0 = bootstrap_ci(d0, counts, level)
        block = {"ci_width_mean": float(np.mean(high - low)),
                 "p_upper_below_0": float(np.mean(high < 0)),
                 "p_upper_below_0_zero_change": float(np.mean(high0 < 0)),
                 "p_main_conclusion": float(np.mean((high < 0) & (high0 < 0))),
                 "readings": {}}
        for delta in deltas:
            labels = reading(low, high, delta)
            block["readings"][str(delta)] = {name: float(np.mean(labels == name))
                                             for name in READINGS}
        out["levels"][str(level)] = block
    return out
