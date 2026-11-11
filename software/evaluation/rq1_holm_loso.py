"""Two simulations left open by SAP v1 (docs/protocol/sap_v1.md sections 5, 6, 9).

No human data: every input is an assumption stated in the config
(configs/analysis/rq1_holm_loso_v1.json).

1. **Joint SBP and DBP with Holm** (SAP section 6). The SBP and DBP data of one
   simulated study come from the model of ``rq1_sensitivity.simulate_d`` with
   every standard normal draw of DBP correlated (``rho``) with the matching draw of
   SBP: day-to-day change, maneuver responses, cuff noise, calibration error and
   model errors. Holm is then applied exactly as SAP section 6 states.
2. **Ridge trained in LOSO** (SAP sections 4 and 5). Features are generated from
   the true ΔBP; for each held-out subject a Ridge model (alpha fixed, no
   intercept, each feature divided by its SD over the training cuffs, every
   training subject the same total weight) is fitted on the other subjects and
   predicts the held-out subject. This checks whether the per-subject
   differences d_s stay close enough to independent for a subject-level CI.
   It also compares PPG+PAT with two no-signal baselines fitted in the same
   folds (``phase_mean_loso``): the mean change of each protocol phase (M0, M1,
   M2) over the training subjects, and one mean over every phase ("constant
   offset"; not the "static" baseline of S4, which also used the time of day).
   Last, both Ridge arms get three phase indicators (M1, M2, session >= 2), so
   the comparison asks whether PAT adds anything once the model knows the phase
   (SAP secondary endpoint 10).

The model of section 2 (per subject s, session k = 1..K, cuff j of CUFFS):

- true change from the session-1 resting level: day_{s,k} (0 at k = 1) plus
  M1_s or M2_s at those cuffs;
- reference change = true change + cuff noise - mean of the cuff noise of the two
  session-1 M0 cuffs (BP0 is their mean, SAP section 4);
- feature f: a_f (1 + g_{s,f}) x driver + drift_{s,k,f} (0 at k = 1) + noise,
  minus the mean noise of the two session-1 M0 cuffs (the feature baseline is
  measured with noise, SAP section 4), where the driver is the true change, or
  the M2 indicator for a feature that only marks the maneuver (heart rate from
  PPG; SAP section 13, open baseline question);
- training uses every cuff of the training subjects (sessions 1..K), the
  analysis every cuff of sessions 2..K of the held-out subject.
"""

import numpy as np

from software.evaluation.mean_intervals import interval
from software.evaluation.rq1_sensitivity import CUFFS, draw_counts, simulate_d

TARGETS = ("SBP", "DBP")


class _Recorder:
    """Stands in for a numpy Generator and keeps every standard normal it draws."""

    def __init__(self, rng):
        self.rng, self.draws = rng, []

    def standard_normal(self, shape):
        z = self.rng.standard_normal(shape)
        self.draws.append(z)
        return z

    def normal(self, loc, scale, size):
        return loc + scale * self.standard_normal(size)


class _Follower:
    """Replays the draws of a _Recorder, each correlated ``rho`` with the original."""

    def __init__(self, rng, draws, rho):
        if not -1 <= rho <= 1:
            raise ValueError("rho must be in [-1, 1]")
        self.rng, self.draws, self.rho = rng, list(draws), rho

    def standard_normal(self, shape):
        if not self.draws:
            raise ValueError("DBP drew more normals than SBP")
        z = self.draws.pop(0)
        if z.shape != tuple(np.atleast_1d(shape)):
            raise ValueError("DBP and SBP draws differ in shape")
        fresh = self.rng.standard_normal(shape)
        return self.rho * z + np.sqrt(1 - self.rho ** 2) * fresh

    def normal(self, loc, scale, size):
        return loc + scale * self.standard_normal(size)


def simulate_joint(rng, replicates, subjects, sessions, targets, models, effects, rho):
    """``{target: (d, d0)}`` for SBP and DBP of the same simulated studies."""
    recorder = _Recorder(rng)
    out = {"SBP": simulate_d(recorder, replicates, subjects, sessions, targets["SBP"],
                             models["SBP"], effects["SBP"])[:2]}
    follower = _Follower(rng, recorder.draws, rho)
    out["DBP"] = simulate_d(follower, replicates, subjects, sessions, targets["DBP"],
                            models["DBP"], effects["DBP"])[:2]
    if follower.draws:
        raise ValueError("SBP drew more normals than DBP")
    return out


def holm(first_sbp, first_dbp, second_sbp, second_dbp):
    """SAP section 6: ``first_*`` passes at 97.5 %, ``second_*`` at 95 % (boolean
    arrays). Returns the declared SBP and DBP outcomes."""
    one = first_sbp | first_dbp
    return (first_sbp | (one & second_sbp)), (first_dbp | (one & second_dbp))


def run_joint(seed, replicates, draws, subjects, sessions, targets, models, effects,
              rho, method, draw_blocks):
    """Shares of studies declaring SBP, DBP, at least one and both after Holm.

    ``main``: Holm on the main conclusion (CIs of d and d0 both below 0).
    ``d_only``: Holm on the CI of d alone, the upper bound of the main conclusion's
    error rate when the model surely beats zero-change (SAP section 6 note)."""
    rng = np.random.default_rng(seed)
    data = simulate_joint(rng, replicates, subjects, sessions, targets, models,
                          effects, rho)
    passes = {}
    for rows in np.array_split(np.arange(replicates), draw_blocks):
        counts = draw_counts(draws, subjects, rng)  # same subjects for SBP and DBP
        for target, (d, d0) in data.items():
            for level in (0.975, 0.95):
                below = interval(d[rows], counts, level, method)[1] < 0
                below0 = interval(d0[rows], counts, level, method)[1] < 0
                for kind, value in (("main", below & below0), ("d_only", below)):
                    passes.setdefault((target, level, kind),
                                      np.zeros(replicates, bool))[rows] = value
    out = {"subjects": subjects, "sessions": sessions, "rho": rho,
           "mean_d": {t: float(data[t][0].mean()) for t in TARGETS},
           "mean_d0": {t: float(data[t][1].mean()) for t in TARGETS}}
    for kind in ("main", "d_only"):
        sbp, dbp = holm(passes["SBP", 0.975, kind], passes["DBP", 0.975, kind],
                        passes["SBP", 0.95, kind], passes["DBP", 0.95, kind])
        out[kind] = {"SBP": float(sbp.mean()), "DBP": float(dbp.mean()),
                     "any": float((sbp | dbp).mean()), "both": float((sbp & dbp).mean()),
                     "SBP_alone_95": float(passes["SBP", 0.95, kind].mean()),
                     "DBP_alone_95": float(passes["DBP", 0.95, kind].mean())}
    return out


def simulate_loso_data(rng, replicates, subjects, sessions, target, effect, features):
    """Reference changes ``(R, n, K, cuffs)`` and features ``(R, n, K, cuffs, F)``
    in the order of ``features`` (a dict name -> spec)."""
    shape = (replicates, subjects, sessions, len(CUFFS))
    day = rng.normal(0, target["tau_day"], (replicates, subjects, sessions, 1))
    day[:, :, 0] = 0.0  # session 1 is the resting level
    m1 = rng.normal(target["m1_mean"], target["m1_sd"], (replicates, subjects, 1, 1))
    m2 = rng.normal(effect["m2_mean"], effect["m2_sd"], (replicates, subjects, 1, 1))
    is_m1 = np.array([c == "M1" for c in CUFFS])
    is_m2 = np.array([c == "M2" for c in CUFFS])
    true = day + np.where(is_m1, m1, 0) + np.where(is_m2, m2, 0)
    noise = rng.normal(0, target["sigma_cuff"], shape)
    m0 = [i for i, c in enumerate(CUFFS) if c == "M0"]
    cal = noise[:, :, :1, m0].mean(axis=-1, keepdims=True)
    reference = true + noise - cal
    columns = []
    for spec in features.values():
        driver = true if spec["driver"] == "bp" else np.broadcast_to(
            is_m2.astype(float), shape)
        gain = spec["a"] * (1 + rng.normal(0, spec["g_sd"], (replicates, subjects, 1, 1)))
        drift = rng.normal(0, spec["drift_sd"], (replicates, subjects, sessions, 1))
        drift[:, :, 0] = 0.0
        feature_noise = rng.normal(0, spec["noise_sd"], shape)
        baseline = feature_noise[:, :, :1, m0].mean(axis=-1, keepdims=True)
        columns.append(gain * driver + drift + feature_noise - baseline)
    return reference, np.stack(columns, axis=-1)


def loso_ridge(x, y, alpha):
    """Leave-one-subject-out Ridge predictions for every cuff.

    ``x`` ``(R, n, K, C, F)``, ``y`` ``(R, n, K, C)``. Fold of subject s: fit on
    every cuff of the other subjects, each subject total weight 1 (so the weights
    sum to n - 1), each feature divided by its SD over the training cuffs
    (ddof 1, no centring), no intercept, penalty ``alpha``; predict subject s.
    Returns ``(R, n, K, C)``."""
    r, n, k, c, f = x.shape
    flat_x = x.reshape(r, n, k * c, f)
    flat_y = y.reshape(r, n, k * c)
    w = 1.0 / (k * c)
    gram = w * np.einsum("rnmf,rnmg->rnfg", flat_x, flat_x)
    cross = w * np.einsum("rnmf,rnm->rnf", flat_x, flat_y)
    s1, s2 = flat_x.sum(axis=2), (flat_x ** 2).sum(axis=2)
    gram_f = gram.sum(axis=1, keepdims=True) - gram
    cross_f = cross.sum(axis=1, keepdims=True) - cross
    count = (n - 1) * k * c
    s1_f = s1.sum(axis=1, keepdims=True) - s1
    s2_f = s2.sum(axis=1, keepdims=True) - s2
    sd = np.sqrt(np.maximum(s2_f - s1_f ** 2 / count, 0.0) / (count - 1))
    if not np.all(sd > 1e-12 * np.sqrt(s2_f / count + 1e-300)):
        raise ValueError("A feature is constant over the training cuffs of a fold")
    scaled_gram = gram_f / (sd[..., :, None] * sd[..., None, :])
    beta = np.linalg.solve(scaled_gram + alpha * np.eye(f),
                           (cross_f / sd)[..., None])[..., 0] / sd
    return np.einsum("rnmf,rnf->rnm", flat_x, beta).reshape(r, n, k, c)


def phase_mean_loso(y, phases):
    """No-signal phase-mean baseline in LOSO (SAP section 4, decided 2026-11-12).

    ``y`` ``(R, n, K, C)`` reference changes, ``phases`` the protocol phase of each
    of the C cuffs of a session. For each phase: every subject's mean of y over
    its cuffs of that phase in sessions 2..K, then the equal-weight mean of those
    subject means over the other subjects of the study; that value is the
    prediction for every cuff of that phase of the held-out subject. One label for
    every cuff gives the "constant" baseline. Returns ``(R, n, K, C)``."""
    if len(phases) != y.shape[-1]:
        raise ValueError("One phase label per cuff is needed")
    n = y.shape[1]
    out = np.empty(y.shape)
    for label in dict.fromkeys(phases):
        cols = [i for i, p in enumerate(phases) if p == label]
        own = y[:, :, 1:][..., cols].mean(axis=(2, 3))
        others = (own.sum(axis=1, keepdims=True) - own) / (n - 1)
        out[..., cols] = others[:, :, None, None]
    return out


def phase_indicators(shape):
    """The three 0/1 phase features of SAP section 4 (secondary endpoint 10): M1,
    M2 and session >= 2, for an array ``(R, n, K, C)`` of cuffs. Session-1 M0
    cuffs have all three at 0. Returns ``(R, n, K, C, 3)``. No random draws."""
    r, n, k, c = shape
    is_m1 = np.array([p == "M1" for p in CUFFS], float)
    is_m2 = np.array([p == "M2" for p in CUFFS], float)
    late = (np.arange(k) >= 1).astype(float)[:, None]
    columns = [np.broadcast_to(is_m1, (k, c)), np.broadcast_to(is_m2, (k, c)),
               np.broadcast_to(late, (k, c))]
    return np.broadcast_to(np.stack(columns, axis=-1), (r, n, k, c, 3))


def loso_d(rng, replicates, subjects, sessions, target, effect, features,
           base_features, alpha):
    """Per-subject differences ``(replicates, subjects)`` of LOSO Ridge models:
    ``d`` (PPG+PAT - PPG-only), ``d0`` (- zero-change), ``d_phase`` (- phase mean),
    ``d_constant`` (- constant offset), ``d_with_phase`` (both arms with the phase
    indicators added: phase+PPG+PAT - phase+PPG), and the mean MAE of each model
    over every subject. The phase indicators draw no random numbers, so the other
    differences are those of the same seed without them."""
    reference, x = simulate_loso_data(rng, replicates, subjects, sessions, target,
                                      effect, features)
    names = list(features)
    base = [names.index(name) for name in base_features]
    phase = phase_indicators(reference.shape)
    mae = lambda e: np.abs(e[:, :, 1:]).mean(axis=(2, 3))  # noqa: E731  sessions >= 2
    fit = lambda z: mae(loso_ridge(z, reference, alpha) - reference)  # noqa: E731
    maes = {"ppg": fit(x[..., base]),
            "ppg_pat": fit(x),
            "zero_change": mae(-reference),
            "phase_mean": mae(phase_mean_loso(reference, CUFFS) - reference),
            "constant": mae(phase_mean_loso(reference, ("all",) * len(CUFFS))
                            - reference),
            "phase_ppg": fit(np.concatenate([x[..., base], phase], axis=-1)),
            "phase_ppg_pat": fit(np.concatenate([x, phase], axis=-1))}
    full = maes["ppg_pat"]
    return {"d": full - maes["ppg"], "d0": full - maes["zero_change"],
            "d_phase": full - maes["phase_mean"], "d_constant": full - maes["constant"],
            "d_with_phase": maes["phase_ppg_pat"] - maes["phase_ppg"],
            "mean_mae": {name: float(v.mean()) for name, v in maes.items()}}


def reference_theta(seed, replicates, chunk, subjects, sessions, target, effect,
                    features, base_features, alpha, key="d"):
    """theta = expected mean d of the design (models trained on n - 1 subjects,
    averaged over training sets and held-out subjects), from a simulation
    separate from the studies whose CIs are judged; with its Monte Carlo SE.
    With ``key`` another difference of ``loso_d`` (e.g. ``"d_phase"``) instead;
    a list of keys returns ``{key: (theta, se)}`` from the same studies."""
    rng = np.random.default_rng(seed)
    keys = [key] if isinstance(key, str) else list(key)
    means = {k: [] for k in keys}
    for size in [chunk] * (replicates // chunk) + ([replicates % chunk]
                                                    if replicates % chunk else []):
        diffs = loso_d(rng, size, subjects, sessions, target, effect, features,
                       base_features, alpha)
        for k in keys:
            means[k].append(diffs[k].mean(axis=1))
    out = {}
    for k, parts in means.items():
        values = np.concatenate(parts)
        out[k] = float(values.mean()), float(values.std(ddof=1) / np.sqrt(len(values)))
    return out[key] if isinstance(key, str) else out


def run_loso(seed, replicates, draws, subjects, sessions, target, effect, features,
             base_features, alpha, methods, level, draw_blocks, theta_replicates):
    """d_s from Ridge trained in LOSO, and how often subject-level CIs miss theta
    (``reference_theta``) on each side. ``shuffled`` repeats the check after
    shuffling each subject column across studies: same marginal d_s, no
    dependence within a study, so the difference shows what that dependence does."""
    thetas = reference_theta(
        [*np.atleast_1d(seed), 99], theta_replicates, 2000, subjects, sessions, target,
        effect, features, base_features, alpha, key=("d", "d_phase", "d_with_phase"))
    (theta, theta_se), (theta_p, theta_p_se) = thetas["d"], thetas["d_phase"]
    theta_w, theta_w_se = thetas["d_with_phase"]
    rng = np.random.default_rng(seed)
    diffs = loso_d(rng, replicates, subjects, sessions, target, effect, features,
                   base_features, alpha)
    d = diffs["d"]
    shuffled = np.column_stack([rng.permutation(d[:, j]) for j in range(subjects)])
    study_mean = d.mean(axis=1)
    naive_se = d.std(axis=1, ddof=1) / np.sqrt(subjects)
    centred = study_mean - study_mean.mean()
    out = {"subjects": subjects, "sessions": sessions, "theta": theta,
           "theta_mc_se": theta_se, "mean_d": float(d.mean()),
           "mean_d0": float(diffs["d0"].mean()),
           "mean_d_phase": float(diffs["d_phase"].mean()),
           "mean_d_constant": float(diffs["d_constant"].mean()),
           "mean_d_with_phase": float(diffs["d_with_phase"].mean()),
           "mean_mae": diffs["mean_mae"],
           "sd_of_study_mean_d": float(study_mean.std(ddof=1)),
           "rms_naive_se": float(np.sqrt(np.mean(naive_se ** 2))),
           "skew_of_study_mean_d": float((centred ** 3).mean() / centred.std() ** 3),
           "corr_d_between_subjects": float(_mean_pair_corr(d)),
           "methods": {}, "shuffled": {}, "baselines": {}, "with_phase": {}}
    out["se_ratio"] = out["sd_of_study_mean_d"] / out["rms_naive_se"]
    kinds = {"methods": d, "shuffled": shuffled, "d0": diffs["d0"],
             "d_phase": diffs["d_phase"], "d_constant": diffs["d_constant"],
             "d_with_phase": diffs["d_with_phase"]}
    limits = {(m, kind): np.empty((2, replicates)) for m in methods for kind in kinds}
    for rows in np.array_split(np.arange(replicates), draw_blocks):
        # One set of subject draws per block, shared by every difference.
        counts = draw_counts(draws, subjects, rng)
        for (method, kind), store in limits.items():
            store[0, rows], store[1, rows] = interval(kinds[kind][rows], counts, level,
                                                      method)
    for method in methods:
        for kind in ("methods", "shuffled"):
            low, high = limits[method, kind]
            out[kind][method] = {"miss_below": float(np.mean(high < theta)),
                                 "miss_above": float(np.mean(low > theta)),
                                 "p_upper_below_0": float(np.mean(high < 0)),
                                 "p_lower_above_0": float(np.mean(low > 0)),
                                 "width": float(np.mean(high - low))}
        below = {k: limits[method, k][1] < 0
                 for k in ("methods", "d0", "d_phase", "d_constant")}
        main = below["methods"] & below["d0"]
        out["baselines"][method] = {
            "p_d0_below_0": float(below["d0"].mean()),
            "p_d_phase_below_0": float(below["d_phase"].mean()),
            "p_d_constant_below_0": float(below["d_constant"].mean()),
            "p_d_phase_above_0": float(np.mean(limits[method, "d_phase"][0] > 0)),
            "theta_phase": theta_p, "theta_phase_mc_se": theta_p_se,
            "phase_miss_below": float(np.mean(limits[method, "d_phase"][1] < theta_p)),
            "phase_miss_above": float(np.mean(limits[method, "d_phase"][0] > theta_p)),
            "p_main": float(main.mean()),
            "p_main_and_phase": float((main & below["d_phase"]).mean())}
        low_w, high_w = limits[method, "d_with_phase"]
        out["with_phase"][method] = {
            "theta": theta_w, "theta_mc_se": theta_w_se,
            "miss_below": float(np.mean(high_w < theta_w)),
            "miss_above": float(np.mean(low_w > theta_w)),
            "p_upper_below_0": float(np.mean(high_w < 0)),
            "p_lower_above_0": float(np.mean(low_w > 0))}
    return out


def _mean_pair_corr(d):
    """Mean correlation of d between two different subjects of the same study,
    estimated over studies (the intraclass correlation the CI ignores)."""
    centred = d - d.mean()
    total = centred.sum(axis=1)
    pair = (total ** 2 - (centred ** 2).sum(axis=1)).sum()
    n = d.shape[1]
    return pair / (d.shape[0] * n * (n - 1)) / centred.var()
