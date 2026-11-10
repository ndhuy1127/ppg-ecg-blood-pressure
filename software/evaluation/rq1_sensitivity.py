"""Simulated sensitivity of the RQ1 comparison (SAP v1, docs/protocol/sap_v1.md).

No human data: every input is an assumption stated in the config
(configs/analysis/rq1_sensitivity_v1.json) and replaced by pilot values later.
For each design (subjects x sessions) it simulates the RQ1 data the SAP
analyses, computes the per-subject MAE differences d_s (PPG+PAT - PPG-only)
and d0_s (PPG+PAT - zero-change) exactly as the SAP does, takes a subject-level
CI of their means (CI_METHODS; one of them is the primary method of the run), and
reports how often each reading of SAP section 7 comes out. One set of subject
draws per simulated study is shared by d, d0, every CI level and every bootstrap
method (SAP section 5). SBP and DBP are simulated
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
from scipy import stats

CUFFS = ("M0", "M0", "M1", "M2")  # per evaluation session (protocol 6.4)
READINGS = ("benefit_at_delta", "benefit_below_delta", "equivalent", "harm",
            "inconclusive")
# CI of the mean over subjects. "percentile" is the SAP v1 method; the other three
# were added on 2026-11-10 after the null scenarios showed it under-covers at
# 15-35 subjects (share of CIs below 0 about 3.7 % against a nominal 2.5 %).
CI_METHODS = ("percentile", "bca", "bootstrap_t", "student_t", "t_envelope")
# Mean-zero shapes of d_s for the method check (ci_error_rates): the BP model above
# draws normal errors, which favours the Student t interval.
CHECK_DISTRIBUTIONS = ("normal", "t3", "skew_right", "skew_left", "outlier_10pct")


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


def _row_quantile(ordered, prob):
    """Linearly interpolated quantile of each row of ``ordered`` (sorted along
    axis 1) at that row's own probability."""
    position = np.clip(prob, 0, 1) * (ordered.shape[1] - 1)
    lower = np.floor(position).astype(int)
    upper = np.minimum(lower + 1, ordered.shape[1] - 1)
    weight = position - lower
    rows = np.arange(ordered.shape[0])
    return ordered[rows, lower] * (1 - weight) + ordered[rows, upper] * weight


def interval(values, counts, level, method="percentile"):
    """Two-sided CI of the mean over subjects (axis 1); ``values`` (replicates,
    subjects) -> (low, high) arrays. Every bootstrap method uses the same subject
    draws ``counts`` (draws, subjects).

    - percentile: quantiles of the resampled means;
    - bca: bias-corrected and accelerated, acceleration from the jackknife;
    - bootstrap_t: studentised, each draw divided by its own standard error;
    - student_t: mean +/- t(n-1) * SD / sqrt(n), no resampling;
    - t_envelope: the wider limit on each side of bootstrap_t and student_t, so
      it lies below 0 only when both do (student_t is the more liberal one when
      d_s is skewed, bootstrap_t when it has heavy tails).
    """
    if method not in CI_METHODS:
        raise ValueError(f"Unknown CI method: {method}")
    if method == "t_envelope":
        low_b, high_b = interval(values, counts, level, "bootstrap_t")
        low_t, high_t = interval(values, counts, level, "student_t")
        return np.minimum(low_b, low_t), np.maximum(high_b, high_t)
    subjects = values.shape[1]
    alpha = 1 - level
    mean = values.mean(axis=1)
    se = values.std(axis=1, ddof=1) / np.sqrt(subjects)
    if method == "student_t":
        half = stats.t.ppf(1 - alpha / 2, subjects - 1) * se
        return mean - half, mean + half
    means = values @ counts.T / subjects  # (replicates, draws)
    if method == "percentile":
        return (np.quantile(means, alpha / 2, axis=1),
                np.quantile(means, 1 - alpha / 2, axis=1))
    centred = means - mean[:, None]
    if method == "bootstrap_t":
        squares = (values ** 2) @ counts.T / subjects
        variance = np.maximum(squares - means ** 2, 0) * subjects / (subjects - 1)
        se_draw = np.sqrt(variance / subjects)
        with np.errstate(divide="ignore", invalid="ignore"):
            t_draw = np.where(se_draw > 0, centred / se_draw, 0.0)
        return (mean - np.quantile(t_draw, 1 - alpha / 2, axis=1) * se,
                mean - np.quantile(t_draw, alpha / 2, axis=1) * se)
    draws = means.shape[1]
    below = (centred < 0).mean(axis=1) + 0.5 * (centred == 0).mean(axis=1)
    bias = stats.norm.ppf(np.clip(below, 0.5 / draws, 1 - 0.5 / draws))
    deviation = values - mean[:, None]
    spread = (deviation ** 2).sum(axis=1)
    with np.errstate(divide="ignore", invalid="ignore"):
        accel = np.where(spread > 0,
                         (deviation ** 3).sum(axis=1) / (6 * spread ** 1.5), 0.0)
    ordered = np.sort(means, axis=1)
    limits = []
    for z in (stats.norm.ppf(alpha / 2), stats.norm.ppf(1 - alpha / 2)):
        shifted = bias + z
        limits.append(_row_quantile(
            ordered, stats.norm.cdf(bias + shifted / (1 - accel * shifted))))
    return limits[0], limits[1]


def bootstrap_ci(values, counts, level):
    """Percentile CI of the mean over subjects (the SAP v1 method)."""
    return interval(values, counts, level, "percentile")


def check_sample(rng, name, shape):
    """Mean-zero, unit-variance draws of d_s with the named shape."""
    if name == "normal":
        return rng.standard_normal(shape)
    if name == "t3":
        return rng.standard_t(3, shape) / np.sqrt(3)
    if name == "skew_right":
        return rng.exponential(1, shape) - 1
    if name == "skew_left":
        return 1 - rng.exponential(1, shape)
    if name == "outlier_10pct":  # one subject in ten has five times the SD
        scale = np.where(rng.random(shape) < 0.1, 5.0, 1.0)
        return rng.standard_normal(shape) * scale / np.sqrt(0.9 + 0.1 * 25)
    raise ValueError(f"Unknown distribution: {name}")


def ci_error_rates(seed, name, subjects, replicates, draws, levels, methods,
                   chunk=2000):
    """Share of CIs that miss a true mean of 0 on each side, per method and level,
    when d_s has the named shape. ``{method: {level: {below, above, width}}}``."""
    rng = np.random.default_rng(seed)
    totals = {m: {str(level): np.zeros(3) for level in levels} for m in methods}
    done = 0
    while done < replicates:
        size = min(chunk, replicates - done)
        values = check_sample(rng, name, (size, subjects))
        counts = draw_counts(draws, subjects, rng)
        for method in methods:
            for level in levels:
                low, high = interval(values, counts, level, method)
                totals[method][str(level)] += [np.sum(high < 0), np.sum(low > 0),
                                               np.sum(high - low)]
        done += size
    return {m: {level: {"below": float(t[0] / replicates),
                        "above": float(t[1] / replicates),
                        "width": float(t[2] / replicates)}
                for level, t in by_level.items()}
            for m, by_level in totals.items()}


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
               deltas, levels, methods=("percentile",), primary="percentile",
               draw_blocks=1):
    """One design. ``levels`` holds the full results of the ``primary`` CI method;
    ``ci_methods`` holds the error shares and width of every method in ``methods``.
    The simulated studies are split into ``draw_blocks`` blocks, each with its own
    subject draws (1, as in v1: every study of the design shares one set)."""
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
           "ci_method": primary, "levels": {}, "ci_methods": {}}
    wanted = list(dict.fromkeys((primary, *methods)))
    limits = {(m, level): np.empty((4, replicates)) for m in wanted for level in levels}
    for rows in np.array_split(np.arange(replicates), draw_blocks):
        # One set of draws per block, shared by d, d0, every level and every method.
        counts = draw_counts(draws, subjects, rng)
        for (method, level), store in limits.items():
            store[0, rows], store[1, rows] = interval(d[rows], counts, level, method)
            store[2, rows], store[3, rows] = interval(d0[rows], counts, level, method)
    for method in wanted:
        for level in levels:
            low, high, low0, high0 = limits[method, level]
            block = {"ci_width_mean": float(np.mean(high - low)),
                     "p_upper_below_0": float(np.mean(high < 0)),
                     "p_lower_above_0": float(np.mean(low > 0)),
                     "p_upper_below_0_zero_change": float(np.mean(high0 < 0)),
                     "p_main_conclusion": float(np.mean((high < 0) & (high0 < 0)))}
            out["ci_methods"].setdefault(method, {})[str(level)] = dict(block)
            if method != primary:
                continue
            block["readings"] = {}
            for delta in deltas:
                labels = reading(low, high, delta)
                block["readings"][str(delta)] = {name: float(np.mean(labels == name))
                                                 for name in READINGS}
            out["levels"][str(level)] = block
    return out
