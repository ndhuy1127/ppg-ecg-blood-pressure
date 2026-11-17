"""Confidence intervals of a mean over subjects (SAP v1 section 5).

Shared by the RQ1 sensitivity simulation (software/evaluation/rq1_sensitivity.py)
and the analysis bootstrap (software/evaluation/subject_bootstrap.py), so both use
the same formulas. Moved here from rq1_sensitivity.py on 2026-11-11 without
changing them.

``values`` is (replicates, subjects): one value per subject, for example
d_s = MAE_s(model) - MAE_s(reference). ``counts`` is (draws, subjects): how often
each subject is drawn in each bootstrap draw; every bootstrap method uses the
same draws.
"""

import numpy as np
from scipy import stats

# "percentile" is the SAP v1 method of 2026-11-07; the others were added on
# 2026-11-10 after the simulated null scenarios showed it under-covers at 15-35
# subjects (share of CIs below 0 about 3.7 % against a nominal 2.5 %).
CI_METHODS = ("percentile", "bca", "bootstrap_t", "student_t", "t_envelope")


def row_quantile(ordered, prob):
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
        limits.append(row_quantile(
            ordered, stats.norm.cdf(bias + shifted / (1 - accel * shifted))))
    return limits[0], limits[1]
