"""PAT validity rules: physiological window and robust within-window outliers.

Inputs are fiducial times only. BP/ABP is never read, and no beat is excluded
because of a BP value. Beats are labelled, not deleted, so callers can report
how many were set aside and why.
"""

from dataclasses import dataclass

import numpy as np

from software.signal_processing.fiducials import finite_number

VERSION = "pat-validity-v0"
MAD_SCALE = 1.4826  # MAD -> SD for a normal distribution
# Float slack only: a foot exactly 80.000 ms after R can come out as 79.99999.
BOUNDARY_TOL_MS = 1e-6


@dataclass(frozen=True)
class PatRules:
    """Engineering proposals, NOT_TEST_TUNED; see configs/data/week05_huy.json."""

    min_ms: float = 80.0
    max_ms: float = 400.0
    mad_k: float = 3.0
    mad_floor_ms: float = 10.0
    min_pairs: int = 3

    def __post_init__(self):
        low = finite_number(self.min_ms, "min_ms")
        high = finite_number(self.max_ms, "max_ms")
        if not 0 < low < high:
            raise ValueError("PAT limits need 0 < min_ms < max_ms")
        if finite_number(self.mad_k, "mad_k") <= 0:
            raise ValueError("mad_k must be positive")
        if finite_number(self.mad_floor_ms, "mad_floor_ms") < 0:
            raise ValueError("mad_floor_ms must be nonnegative")
        if (isinstance(self.min_pairs, bool) or not isinstance(self.min_pairs, int)
                or self.min_pairs < 2):
            raise ValueError("min_pairs must be an integer >= 2")


def _in_range(values, rules):
    values = np.asarray(values, dtype=float)
    return ((values >= rules.min_ms - BOUNDARY_TOL_MS)
            & (values <= rules.max_ms + BOUNDARY_TOL_MS))


def classify_pat(pat_ms, rules: PatRules) -> dict:
    """Label each beat PAT as valid, out_of_range or outlier.

    1. out_of_range: outside [min_ms, max_ms].
    2. outlier: among in-range beats,
       |PAT - median| > max(mad_k * 1.4826 * MAD, mad_floor_ms).
       The floor stops sample quantization (8 ms at 125 Hz) from becoming an
       "outlier" when PAT is nearly constant. Applied only with at least
       ``min_pairs`` in-range beats; with MAD = 0 the flag ``pat:mad_zero`` is
       set and only the floor applies.
    Summary statistics use valid beats only; ``median_all_ms`` is kept so the
    effect of the rule stays visible.
    """
    values = np.asarray(pat_ms, dtype=float)
    if values.ndim != 1 or not np.isfinite(values).all():
        raise ValueError("PAT values must be a finite 1-D vector")
    status = np.where(_in_range(values, rules), "valid", "out_of_range")
    flags = []
    inside = values[status == "valid"]
    if len(inside) >= rules.min_pairs:
        median = np.median(inside)
        spread = MAD_SCALE * np.median(np.abs(inside - median))
        if spread == 0:
            flags.append("pat:mad_zero")
        limit = max(rules.mad_k * spread, rules.mad_floor_ms)
        status[(status == "valid") & (np.abs(values - median) > limit)] = "outlier"
    else:
        flags.append("pat:too_few_in_range_for_outlier_rule")
    valid = values[status == "valid"]
    if len(valid) < rules.min_pairs:
        flags.append("pat:too_few_valid")
    enough = len(valid) >= rules.min_pairs
    return {
        "version": VERSION,
        "status": status.tolist(),
        "n_pairs": len(values),
        "n_valid": int((status == "valid").sum()),
        "n_out_of_range": int((status == "out_of_range").sum()),
        "n_outlier": int((status == "outlier").sum()),
        "median_all_ms": float(np.median(values)) if len(values) else None,
        "median_valid_ms": float(np.median(valid)) if enough else None,
        "iqr_valid_ms": (float(np.percentile(valid, 75) - np.percentile(valid, 25))
                         if enough else None),
        "flags": flags,
    }


def pair_between_r(r_times, foot_times, rules: PatRules):
    """Pair each R with a foot after it and before the next R.

    The PAT limits are not a pairing gate, so a 450 ms or 60 ms beat is still
    paired and then labelled ``out_of_range`` by ``classify_pat`` instead of
    disappearing as an unpaired R. One foot in the interval is paired whatever
    its PAT. With several feet, the beat is paired only if exactly one of them
    is inside the limits; otherwise it is "ambiguous". The last R looks one
    previous RR ahead (unbounded when there is a single R). Intervals do not
    overlap, so a foot belongs to at most one R.

    Returns (pairs [(r_index, foot_index, pat_ms)], per-R status list with
    "paired", "no_foot" or "ambiguous").
    """
    r_times = np.asarray(r_times, dtype=float)
    foot_times = np.asarray(foot_times, dtype=float)
    for times in (r_times, foot_times):
        if (times.ndim != 1 or not np.isfinite(times).all()
                or (np.diff(times) <= 0).any()):
            raise ValueError("Fiducial times must be finite and strictly increasing")
    pairs, r_status = [], []
    for i, r in enumerate(r_times):
        if i + 1 < len(r_times):
            upper = r_times[i + 1]
        elif i > 0:
            upper = r + (r - r_times[i - 1])
        else:
            upper = np.inf
        candidates = np.flatnonzero((foot_times > r) & (foot_times < upper))
        if len(candidates) > 1:
            pats = (foot_times[candidates] - r) * 1000
            candidates = candidates[_in_range(pats, rules)]
            if len(candidates) != 1:
                r_status.append("ambiguous")
                continue
        if not len(candidates):
            r_status.append("no_foot")
            continue
        j = int(candidates[0])
        pairs.append((int(i), j, float((foot_times[j] - r) * 1000)))
        r_status.append("paired")
    return pairs, r_status


def pat_beats(r_times, foot_times, rules: PatRules) -> dict:
    """Pair R and feet with ``pair_between_r``, then classify every pair.

    This pairing is NOT the ``pair_pat`` of features-sqi-v1 (which keeps only
    feet inside the PAT limits); v1 output is unchanged. Callers must only pass
    times whose clock alignment and upstream delays are verified; this function
    cannot check that.
    """
    pairs, r_status = pair_between_r(r_times, foot_times, rules)
    result = classify_pat([p[2] for p in pairs], rules)
    result["pairs"] = pairs
    result["r_status"] = r_status
    result["n_unpaired_r"] = sum(s != "paired" for s in r_status)
    result["n_no_foot"] = r_status.count("no_foot")
    result["n_ambiguous"] = r_status.count("ambiguous")
    return result
