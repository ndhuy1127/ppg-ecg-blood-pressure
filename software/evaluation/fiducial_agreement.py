"""Agreement between automatic fiducials and a person's manual marks.

Pure functions on two tables:

* annotations: ``record_id, split, fiducial, time_s, review_start_s,
  review_end_s, annotator, annotated_on, note``. One row per manual mark; a row
  with empty ``time_s`` only declares a reviewed region with no mark.
* detections: ``record_id, split, method, fiducial, time_s``. The detector
  writes one row with empty ``time_s`` per (record, method, fiducial) it ran, so
  "ran and found nothing" differs from "not run".

Manual marks count inside the reviewed region. A detection up to one tolerance
outside the region may still match a mark near the edge, but an unmatched one
there is not a false positive, so methods with a timing bias are not penalised
at the region edges. Splits other than train/val are rejected: test is never
opened for method selection. Manual marks are compared on train only (methods
are selected on train, so B4 - B3 on val stays independent); val is accepted
with manual marks only when every record is declared SYNTHETIC (practice
marking on generated records). Beats of one record are not independent;
per-record rows are returned alongside the pooled summary, each with its
matched errors (``errors_ms``) so subject-level gates can pool them.
"""

import numpy as np
import pandas as pd

# v1 (2026-10-25): per-record rows carry their matched errors, errors_ms.
# 2026-10-29: manual marks on val are refused unless every record is SYNTHETIC;
# accepted inputs give the same output, so the version is unchanged.
VERSION = "fiducial-agreement-v1"
FIDUCIALS = ("ecg_r", "ppg_foot")
ALLOWED_SPLITS = ("train", "val")
# Split of manual marks on real records: fiducial methods are selected on train.
MANUAL_SPLITS = ("train",)
ANNOTATION_COLUMNS = (
    "record_id", "split", "fiducial", "time_s", "review_start_s", "review_end_s",
    "annotator", "annotated_on", "note",
)
DETECTION_COLUMNS = ("record_id", "split", "method", "fiducial", "time_s")
SYNTHETIC_ANNOTATOR = "SYNTHETIC_GROUND_TRUTH_NOT_MANUAL"
# Float slack only: 1.05 - 1.0 > 0.05 in binary floating point.
TIME_TOL_S = 1e-9


def is_synthetic_annotator(name):
    """Generated truth is recognised however it is spaced or capitalised."""
    return str(name).strip().upper().startswith("SYNTHETIC")


def match_events(reference, detected, tolerance_s):
    """One-to-one matching within ``tolerance_s``: most pairs, then least |error|.

    Events on a line have an optimal matching without crossings, so a dynamic
    programme over the sorted times finds it. Closest-first greedy can miss
    pairs (marks 1.00/1.06 s, detections 1.035/1.105 s, 50 ms: 2 pairs, not 1).
    Returns (matched (ref_index, det_index) list, errors det - ref in seconds).
    """
    reference = np.asarray(reference, dtype=float)
    detected = np.asarray(detected, dtype=float)
    if not np.isfinite(tolerance_s) or tolerance_s <= 0:
        raise ValueError("tolerance_s must be finite and positive")
    limit = tolerance_s + TIME_TOL_S
    ref_order = np.argsort(reference, kind="stable")
    det_order = np.argsort(detected, kind="stable")
    ref, det = reference[ref_order], detected[det_order]
    n, m = len(ref), len(det)
    # best[i][j] = (pairs, -total |error|) using the first i marks, j detections.
    best = [[(0, 0.0)] * (m + 1) for _ in range(n + 1)]
    move = [[None] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            options = [(best[i - 1][j], "skip_ref"), (best[i][j - 1], "skip_det")]
            gap = abs(det[j - 1] - ref[i - 1])
            if gap <= limit:
                count, score = best[i - 1][j - 1]
                options.append(((count + 1, score - gap), "match"))
            best[i][j], move[i][j] = max(options, key=lambda o: (o[0], o[1] == "match"))
    matched = []
    i, j = n, m
    while i and j:
        if move[i][j] == "match":
            matched.append((int(ref_order[i - 1]), int(det_order[j - 1])))
            i, j = i - 1, j - 1
        elif move[i][j] == "skip_ref":
            i -= 1
        else:
            j -= 1
    matched.sort()
    errors = np.array([detected[j] - reference[i] for i, j in matched], dtype=float)
    return matched, errors


def _check_columns(table, columns, name):
    if not isinstance(table, pd.DataFrame) or list(table.columns) != list(columns):
        raise ValueError(f"{name} must have exactly the columns {list(columns)}")
    if table.empty:
        raise ValueError(f"{name} is empty")
    for column in ("record_id", "split", "fiducial"):
        if table[column].isna().any() or not all(
            isinstance(v, str) and v.strip() == v and v for v in table[column]
        ):
            raise ValueError(f"{name}.{column} must be nonempty text")
    if not set(table.split) <= set(ALLOWED_SPLITS):
        raise ValueError("Only train/val records may be used for fiducial review")
    if not set(table.fiducial) <= set(FIDUCIALS):
        raise ValueError(f"fiducial must be one of {FIDUCIALS}")
    times = pd.to_numeric(table.time_s, errors="coerce")
    if (times.isna() & table.time_s.notna()).any() or np.isinf(times).any():
        raise ValueError(f"{name}.time_s must be a finite number or empty")
    return times


def _regions(annotations):
    times = _check_columns(annotations, ANNOTATION_COLUMNS, "annotations")
    regions = {}
    for key, rows in annotations.groupby(["record_id", "fiducial"], sort=True):
        bounds = rows[["review_start_s", "review_end_s"]].apply(
            pd.to_numeric, errors="coerce")
        if bounds.isna().any().any() or len(bounds.drop_duplicates()) != 1:
            raise ValueError(f"{key}: one finite review region is required")
        start, end = bounds.iloc[0]
        if not np.isfinite([start, end]).all() or start >= end:
            raise ValueError(f"{key}: review_start_s must be < review_end_s")
        if rows.split.nunique() != 1:
            raise ValueError(f"{key}: inconsistent split")
        marks = np.sort(times[rows.index].dropna().to_numpy())
        if ((marks < start) | (marks > end)).any():
            raise ValueError(f"{key}: manual mark outside its review region")
        if (np.diff(marks) <= 0).any():
            raise ValueError(f"{key}: duplicate manual marks")
        regions[key] = (rows.split.iloc[0], float(start), float(end), marks)
    return regions


def _reference_type(annotations, allow_synthetic_truth):
    synthetic = annotations.annotator.map(is_synthetic_annotator)
    if not synthetic.any():
        return "MANUAL"
    if not synthetic.all():
        raise ValueError("Annotations mix generated SYNTHETIC truth with manual marks")
    if not allow_synthetic_truth:
        raise ValueError("Annotations contain generated SYNTHETIC truth; pass "
                         "allow_synthetic_truth to run a code check on it alone")
    return "SYNTHETIC_TRUTH"


def _check_manual_split(annotations, reference_type, source_types):
    """Manual marks count on train only, unless every record is SYNTHETIC.

    ``source_types`` None (undeclared) counts as real records: fail closed.
    """
    if reference_type != "MANUAL" or set(annotations.split) <= set(MANUAL_SPLITS):
        return
    if isinstance(source_types, (list, tuple)) and set(source_types) == {"SYNTHETIC"}:
        return
    raise ValueError("Manual marks on real records are compared on train only; val "
                     "is never used to select fiducial methods")


def _summary(errors, n_ref, n_det, tp):
    fp, fn = n_det - tp, n_ref - tp
    errors_ms = np.asarray(errors, dtype=float) * 1000
    return {
        "n_reference": int(n_ref), "n_detected": int(n_det),
        "tp": int(tp), "fp": int(fp), "fn": int(fn),
        "sensitivity": tp / n_ref if n_ref else None,
        "ppv": tp / n_det if n_det else None,
        "bias_ms": float(errors_ms.mean()) if tp else None,
        "mae_ms": float(np.abs(errors_ms).mean()) if tp else None,
        "sd_ms": float(errors_ms.std(ddof=1)) if tp > 1 else None,
    }


def agreement(annotations, detections, tolerance_s, allow_synthetic_truth=False,
              source_types=None):
    """Sensitivity, PPV and timing error (det - manual) per method and fiducial.

    ``tolerance_s`` maps fiducial -> matching window in seconds. Generated
    SYNTHETIC truth is refused unless ``allow_synthetic_truth`` (a code check).
    ``source_types``: list of the records' source types, vouched for by the
    caller; manual marks on val are refused unless its only value is SYNTHETIC.
    ``n_detected`` = TP + FP: detections in the region plus edge matches.
    """
    regions = _regions(annotations)
    reference_type = _reference_type(annotations, allow_synthetic_truth)
    _check_manual_split(annotations, reference_type, source_types)
    det_times = _check_columns(detections, DETECTION_COLUMNS, "detections")
    if detections.method.isna().any() or not all(
        isinstance(m, str) and m for m in detections.method
    ):
        raise ValueError("detections.method must be nonempty text")
    if set(tolerance_s) != set(FIDUCIALS):
        raise ValueError(f"tolerance_s needs exactly {FIDUCIALS}")
    per_record, pooled = [], {}
    methods = {f: sorted(set(detections.method[detections.fiducial == f]))
               for f in FIDUCIALS}
    for (record, fiducial), (split, start, end, marks) in regions.items():
        if not methods[fiducial]:
            raise ValueError(f"No method was run for {fiducial}")
        tolerance = tolerance_s[fiducial]
        for method in methods[fiducial]:
            rows = detections[(detections.record_id == record)
                              & (detections.fiducial == fiducial)
                              & (detections.method == method)]
            if rows.empty:
                raise ValueError(f"{method} was not run on {record}/{fiducial}")
            if set(rows.split) != {split}:
                raise ValueError(f"{record}: split differs between tables")
            found = np.sort(det_times[rows.index].dropna().to_numpy())
            near = found[(found >= start - tolerance - TIME_TOL_S)
                         & (found <= end + tolerance + TIME_TOL_S)]
            matched, errors = match_events(marks, near, tolerance)
            used = {j for _, j in matched}
            fp = sum(1 for j, t in enumerate(near)
                     if j not in used and start <= t <= end)
            n_det = len(matched) + fp
            row = {"record_id": record, "split": split, "fiducial": fiducial,
                   "method": method,
                   **_summary(errors, len(marks), n_det, len(matched)),
                   "errors_ms": (errors * 1000).tolist()}
            per_record.append(row)
            total = pooled.setdefault((fiducial, method), {
                "errors": [], "n_ref": 0, "n_det": 0, "records": 0})
            total["errors"].extend(errors.tolist())
            total["n_ref"] += len(marks)
            total["n_det"] += n_det
            total["records"] += 1
    summary = [
        {"fiducial": f, "method": m, "n_records": t["records"],
         "tolerance_ms": tolerance_s[f] * 1000,
         **_summary(t["errors"], t["n_ref"], t["n_det"], len(t["errors"]))}
        for (f, m), t in sorted(pooled.items())
    ]
    return {"version": VERSION, "reference_type": reference_type,
            "summary": summary, "per_record": per_record}
