"""Pre-registered acceptance gate for R/foot detectors, and annotator repeatability.

Decided by Huy on 2026-10-25, before any PulseDB segment was marked
(docs/protocol/week05_fiducials_pat_validity.md section 9); the numbers live in
the ``acceptance`` block of configs/data/week05_huy.json and have no source:
they are engineering proposals.

``gate``: the selection group scores every candidate method; methods that pass
every limit are kept and the lowest subject-averaged MAE wins (exact ties: the
config's tie order). The confirmation group then scores only the winner of
each fiducial, once; no switching after a failed confirmation. Point estimates
decide; subject-bootstrap percentile CIs are reported but not gated.

Metrics of a group: sensitivity, PPV and MAE are averaged equally over subjects
(each subject pools its segments); bias and SD (ddof=1) pool every matched
error; the segment floor is the fraction of segments with sensitivity and PPV
at or above the floor. Matched errors are automatic - manual, in ms. A metric
that is undefined for any subject (no marks, no detection, no match) is None
and fails its limit; a segment without manual marks fails the floor; every
planned segment must have been compared for every method.

``repeatability``: two marking sessions of the same annotator on the same
segments with the same review regions, at least ``min_days`` apart; errors are
second - first session. It passes only when every mark of both sessions is
matched and the MAE is within the limit, so missed or extra marks cannot hide
behind a small MAE.
"""

from datetime import date

import numpy as np

from software.evaluation.fiducial_agreement import (
    FIDUCIALS, _regions, is_synthetic_annotator, match_events,
)

VERSION = "fiducial-gate-v1"
GROUPS = ("selection", "confirmation")
LIMIT_FIELDS = ("min_sensitivity", "min_ppv", "max_abs_bias_ms", "max_mae_ms",
                "max_sd_ms")
# Float slack for comparisons with the limits (e.g. 99/100 against 0.99).
SLACK = 1e-12


def _ratio(numerator, denominator):
    return numerator / denominator if denominator else None


def _mean(values):
    """Mean over subjects; None as soon as one subject's value is undefined."""
    values = list(values)
    if not values or any(v is None for v in values):
        return None
    return float(np.mean(values))


def _pooled(rows):
    """Totals and matched errors (ms) of per-record rows, summed."""
    errors = [e for row in rows for e in row["errors_ms"]]
    return (sum(row["tp"] for row in rows), sum(row["n_reference"] for row in rows),
            sum(row["n_detected"] for row in rows), errors)


def _point(rows_by_subject, floor):
    subjects = {}
    for subject, rows in rows_by_subject.items():
        tp, n_ref, n_det, errors = _pooled(rows)
        subjects[subject] = (_ratio(tp, n_ref), _ratio(tp, n_det),
                             float(np.mean(np.abs(errors))) if errors else None)
    errors = np.array([e for rows in rows_by_subject.values()
                       for row in rows for e in row["errors_ms"]], dtype=float)
    segments = [row for rows in rows_by_subject.values() for row in rows]

    def segment_ok(row):
        if row["n_reference"] == 0:
            return False  # An unmarked 10 s segment is not evidence.
        sensitivity = row["tp"] / row["n_reference"]
        ppv = _ratio(row["tp"], row["n_detected"])
        return (sensitivity >= floor["min_sensitivity"] - SLACK and ppv is not None
                and ppv >= floor["min_ppv"] - SLACK)

    return {
        "sensitivity": _mean(s for s, _, _ in subjects.values()),
        "ppv": _mean(p for _, p, _ in subjects.values()),
        "mae_ms": _mean(m for _, _, m in subjects.values()),
        "bias_ms": float(errors.mean()) if errors.size else None,
        "sd_ms": float(errors.std(ddof=1)) if errors.size > 1 else None,
        "segment_fraction": sum(map(segment_ok, segments)) / len(segments),
    }


def _worst_segment(rows):
    def score(row):
        sensitivity = _ratio(row["tp"], row["n_reference"])
        ppv = _ratio(row["tp"], row["n_detected"])
        if sensitivity is None or ppv is None:
            return 0.0
        return min(sensitivity, ppv)

    worst = min(rows, key=lambda row: (score(row), row["record_id"]))
    return {"record_id": worst["record_id"], "min_sensitivity_ppv": score(worst),
            "tp": worst["tp"], "n_reference": worst["n_reference"],
            "n_detected": worst["n_detected"]}


def group_metrics(rows, record_subject, floor, bootstrap):
    """Point metrics, segment floor, worst segment and subject-bootstrap CIs."""
    by_subject = {}
    for row in rows:
        by_subject.setdefault(record_subject[row["record_id"]], []).append(row)
    point = _point(by_subject, floor)
    subjects = sorted(by_subject)
    rng = np.random.default_rng(bootstrap["seed"])
    draws = {name: [] for name in point}
    for _ in range(bootstrap["repetitions"]):
        picked = rng.integers(len(subjects), size=len(subjects))
        sample = {k: by_subject[subjects[i]] for k, i in enumerate(picked)}
        for name, value in _point(sample, floor).items():
            if value is not None:
                draws[name].append(value)
    alpha = (1 - bootstrap["confidence"]) / 2
    ci = {name: ([float(np.quantile(values, alpha)),
                  float(np.quantile(values, 1 - alpha))] if values else None)
          for name, values in draws.items()}
    return {"n_subjects": len(subjects), "n_segments": len(rows),
            "n_reference": sum(row["n_reference"] for row in rows),
            **point, "ci": ci, "worst_segment": _worst_segment(rows)}


def check_limits(metrics, limits, floor):
    """Each limit -> passed (None counts as failed)."""
    def at_least(value, bound):
        return value is not None and value >= bound - SLACK

    def at_most(value, bound):
        return value is not None and value <= bound + SLACK

    bias = metrics["bias_ms"]
    return {
        "sensitivity": at_least(metrics["sensitivity"], limits["min_sensitivity"]),
        "ppv": at_least(metrics["ppv"], limits["min_ppv"]),
        "abs_bias_ms": at_most(None if bias is None else abs(bias),
                               limits["max_abs_bias_ms"]),
        "mae_ms": at_most(metrics["mae_ms"], limits["max_mae_ms"]),
        "sd_ms": at_most(metrics["sd_ms"], limits["max_sd_ms"]),
        "segment_fraction": at_least(metrics["segment_fraction"],
                                     floor["min_fraction_of_segments"]),
    }


def check_acceptance(acceptance):
    """Refuse a malformed or incomplete acceptance block."""
    if set(acceptance) != {"version", "limits", "segment_floor", "tie_order",
                           "repeatability_max_mae_ms", "repeat_min_days",
                           "bootstrap"}:
        raise ValueError("acceptance needs exactly the documented fields")
    for fiducial in FIDUCIALS:
        limits = acceptance["limits"][fiducial]
        if set(limits) != set(LIMIT_FIELDS) or not all(
            isinstance(v, (int, float)) and not isinstance(v, bool) and v >= 0
            for v in limits.values()
        ):
            raise ValueError(f"limits.{fiducial} needs nonnegative {LIMIT_FIELDS}")
        order = acceptance["tie_order"][fiducial]
        if not order or len(set(order)) != len(order):
            raise ValueError(f"tie_order.{fiducial} must list distinct methods")
    if set(acceptance["segment_floor"]) != {"min_sensitivity", "min_ppv",
                                            "min_fraction_of_segments"}:
        raise ValueError("segment_floor needs min_sensitivity, min_ppv, "
                         "min_fraction_of_segments")
    if set(acceptance["bootstrap"]) != {"seed", "repetitions", "confidence"}:
        raise ValueError("bootstrap needs seed, repetitions, confidence")


def gate(per_record, record_subject, groups, acceptance):
    """Select on the selection group, confirm the winner on the other group.

    ``per_record``: rows of ``agreement`` (manual reference) with ``errors_ms``.
    ``record_subject``: record_id -> subject. ``groups``: group -> subjects.
    """
    check_acceptance(acceptance)
    if set(groups) != set(GROUPS) or not all(groups[g] for g in GROUPS):
        raise ValueError("Both selection and confirmation groups are required")
    selection, confirmation = (set(groups[g]) for g in GROUPS)
    if selection & confirmation:
        raise ValueError("A subject is in both groups")
    if set(record_subject.values()) != selection | confirmation:
        raise ValueError("Planned records and group subjects differ")
    floor, boot = acceptance["segment_floor"], acceptance["bootstrap"]
    result = {"version": VERSION, "acceptance_version": acceptance["version"],
              "fiducials": {}}
    for fiducial in FIDUCIALS:
        rows = [row for row in per_record if row["fiducial"] == fiducial]
        methods = sorted({row["method"] for row in rows})
        order = acceptance["tie_order"][fiducial]
        if set(order) != set(methods):
            raise ValueError(f"tie_order.{fiducial} must list exactly {methods}")
        for method in methods:
            compared = [row["record_id"] for row in rows if row["method"] == method]
            if sorted(compared) != sorted(record_subject):
                raise ValueError(f"{fiducial}/{method}: every planned segment must "
                                 "be compared exactly once")
        limits = acceptance["limits"][fiducial]

        def of(method, group, rows=rows):
            members = selection if group == "selection" else confirmation
            return [row for row in rows if row["method"] == method
                    and record_subject[row["record_id"]] in members]

        scored = {}
        for method in methods:
            metrics = group_metrics(of(method, "selection"), record_subject, floor,
                                    boot)
            checks = check_limits(metrics, limits, floor)
            scored[method] = {**metrics, "checks": checks,
                              "passed": all(checks.values())}
        passing = [m for m in methods if scored[m]["passed"]]
        winner = min(passing, key=lambda m: (scored[m]["mae_ms"], order.index(m)),
                     default=None)
        entry = {"limits": limits, "selection": scored, "winner": winner,
                 "confirmation": None, "confirmed": False}
        if winner is not None:
            metrics = group_metrics(of(winner, "confirmation"), record_subject,
                                    floor, boot)
            checks = check_limits(metrics, limits, floor)
            entry["confirmation"] = {**metrics, "checks": checks}
            entry["confirmed"] = all(checks.values())
        result["fiducials"][fiducial] = entry
    result["detectors_confirmed"] = all(
        result["fiducials"][f]["confirmed"] for f in FIDUCIALS)
    return result


def _session(annotations):
    """(annotator, first day, last day); a session may span sittings (resume)."""
    if annotations.annotator.map(is_synthetic_annotator).any():
        raise ValueError("Repeatability needs manual marks, not SYNTHETIC truth")
    names = set(annotations.annotator)
    if len(names) != 1:
        raise ValueError("Each session must have one annotator")
    days = sorted(date.fromisoformat(str(day)) for day in set(annotations.annotated_on))
    return names.pop(), days[0], days[-1]


def repeatability(first, second, tolerance_s, max_mae_ms, min_days,
                  expected_records):
    """Second - first session on ``expected_records`` (the repeat segments)."""
    first_regions, second_regions = _regions(first), _regions(second)
    (who_1, start_1, end_1), (who_2, start_2, end_2) = _session(first), _session(second)
    if who_1 != who_2:
        raise ValueError("Repeatability compares one annotator with themself")
    if (start_2 - end_1).days < min_days:
        raise ValueError(f"The repeat session must start at least {min_days} days "
                         "after the first session ended")
    if len(set(expected_records)) != len(expected_records):
        raise ValueError("Repeat segments must be distinct")
    expected = {(record, f) for record in expected_records for f in FIDUCIALS}
    if set(second_regions) != expected:
        raise ValueError("The repeat session must cover exactly the repeat segments")
    if not expected <= set(first_regions):
        raise ValueError("Repeat segments must all be in the first session")
    result = {"version": VERSION,
              "first_session": [str(start_1), str(end_1)],
              "second_session": [str(start_2), str(end_2)],
              "days_apart": (start_2 - end_1).days, "fiducials": {}}
    for fiducial in FIDUCIALS:
        keys = sorted(k for k in expected if k[1] == fiducial)
        errors, n_first, n_second, matched = [], 0, 0, 0
        for key in keys:
            _, region_start_1, region_end_1, marks_1 = first_regions[key]
            _, region_start_2, region_end_2, marks_2 = second_regions[key]
            if not np.allclose([region_start_1, region_end_1],
                               [region_start_2, region_end_2], rtol=0, atol=1e-9):
                raise ValueError(f"{key}: review regions differ between sessions")
            pairs, found = match_events(marks_1, marks_2, tolerance_s[fiducial])
            errors += (found * 1000).tolist()
            n_first, n_second, matched = (n_first + len(marks_1),
                                          n_second + len(marks_2),
                                          matched + len(pairs))
        errors = np.array(errors, dtype=float)
        mae = float(np.abs(errors).mean()) if errors.size else None
        complete = matched == n_first == n_second and matched > 0
        result["fiducials"][fiducial] = {
            "n_segments": len(keys), "n_first": n_first, "n_second": n_second,
            "matched": matched, "unmatched_first": n_first - matched,
            "unmatched_second": n_second - matched,
            "complete_correspondence": complete,
            "bias_ms": float(errors.mean()) if errors.size else None,
            "mae_ms": mae,
            "sd_ms": float(errors.std(ddof=1)) if errors.size > 1 else None,
            "max_mae_ms": max_mae_ms[fiducial],
            "passed": complete and mae <= max_mae_ms[fiducial] + SLACK,
        }
    result["passed"] = all(result["fiducials"][f]["passed"] for f in FIDUCIALS)
    return result
