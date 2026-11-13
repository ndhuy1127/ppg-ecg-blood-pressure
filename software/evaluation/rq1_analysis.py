"""RQ1 analysis of a per-cuff feature table, as SAP v1 states it.

docs/protocol/sap_v1.md (decided 2026-11-12): calibration by the mean of the
valid session-1 M0 cuffs (section 4), Ridge with alpha = 1 and no intercept on
delta features divided by their SD over the training cuffs, each training subject
total weight 1 (section 4), leave-one-subject-out over eligible subjects (section
1), no-signal baselines by phase and constant (section 4), phase indicators
(secondary endpoint 10), subject-level CIs (t envelope of bootstrap-t and Student
t, section 5) and Holm between SBP and DBP (option A, section 6).

The model fits and the phase baseline repeat, on ragged real-shaped data, the
array code of ``rq1_holm_loso`` (``loso_ridge``, ``phase_mean_loso``,
``phase_indicators``); tests check that both give the same per-subject values on
the same data. CIs come from ``mean_intervals.interval`` and the Holm steps from
``rq1_holm_loso.holm``. The held-out subject never enters the SD scaling, the
weights, the Ridge fit or the phase baseline of its fold. Its own calibration
(BP0 and feature baseline from its session 1) is part of the design.

No file I/O, no printing. Results on SYNTHETIC tables only verify code.
"""

import numpy as np
from scipy import stats

from software.evaluation.mean_intervals import interval
from software.evaluation.rq1_holm_loso import holm
from software.evaluation.rq1_sensitivity import draw_counts

VERSION = "rq1-analysis-v1"
TARGETS = ("SBP", "DBP")
LABELS = {"SBP": "sbp_mmhg", "DBP": "dbp_mmhg"}
PHASES = ("M0", "M1", "M2")
SENSITIVITY_METHODS = ("percentile", "bca", "bootstrap_t", "student_t")
FLAG_COLUMNS = ("safety_stop", "led_readjusted", "pilot")
# SAP section 9, rule 3 of the sample-size choice: at least 15 eligible subjects.
# Fewer still runs, but the report carries a warning.
MIN_ELIGIBLE = 15
_TRUE, _FALSE = ("1", "true"), ("0", "false")


def _finite(value):
    try:
        return value is not None and value != "" and np.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def _session_index(text):
    if not isinstance(text, str) or len(text) != 4 or text[0] != "S" or not text[1:].isdigit():
        raise ValueError(f"session_id must look like S001, got {text!r}")
    return int(text[1:])


def flag01(row, column):
    """The one reader of every 0/1 column (``safety_stop``, ``led_readjusted``,
    ``pilot``): 0/1, "0"/"1", True/False or "true"/"false" (any case). A missing or
    empty value is 0 only on SYNTHETIC rows; on any other row it is an error, so
    a pilot subject or a re-adjusted session cannot slip in by default."""
    value = row.get(column)
    if value is None or value == "":
        if row.get("source_type") == "SYNTHETIC":
            return False
        raise ValueError(f"Column {column!r} is required on non-SYNTHETIC rows "
                         f"(cuff {row.get('subject_id')}/{row.get('session_id')}/"
                         f"{row.get('event_id')})")
    text = str(value).strip().lower()
    if isinstance(value, bool) or text in _TRUE + _FALSE:
        return bool(value) if isinstance(value, bool) else text in _TRUE
    raise ValueError(f"Column {column!r} must be 0 or 1, got {value!r}")


def derive(row, name):
    """Value of a raw or derived feature: ``pat_inv_sq`` = 1 / PAT^2 (PAT in s),
    the PAT-only feature of SAP section 4 (its delta is taken later)."""
    if name == "pat_inv_sq":
        pat = row.get("pat_ms")
        return 1.0 / (float(pat) / 1000) ** 2 if _finite(pat) and float(pat) > 0 else None
    value = row.get(name)
    return float(value) if _finite(value) else None


def prepare(rows, config):
    """Calibration, delta features, computability and eligibility (SAP 2, 4, 10).

    ``rows``: one dict per cuff with subject_id, session_id (S###), event_id,
    phase, status, safety_stop, sbp_mmhg, dbp_mmhg, the feature columns and
    led_readjusted, pilot (0/1; may be absent only on SYNTHETIC rows, see
    ``flag01``) and flags (``;``-separated). ``led_readjusted`` and ``pilot`` act
    on the whole session and the whole subject (SAP section 2), whatever cuff
    carries them."""
    models = config["models"]
    names = sorted({f for spec in models.values() for f in spec["features"]})
    main_ppg = models[config["comparison"]["base"]]["features"]
    main_full = models[config["comparison"]["full"]]["features"]
    seen, cuffs = set(), []
    for raw in rows:
        key = (raw["subject_id"], raw["session_id"], raw["event_id"])
        if key in seen:
            raise ValueError(f"Duplicate cuff {key}")
        seen.add(key)
        if raw["phase"] not in PHASES:
            raise ValueError(f"Unknown phase {raw['phase']!r}")
        valid = raw["status"] == "valid" and all(_finite(raw[LABELS[t]]) for t in TARGETS)
        cuffs.append({
            "subject": raw["subject_id"], "session": _session_index(raw["session_id"]),
            "event_id": raw["event_id"], "phase": raw["phase"], "valid": valid,
            **{column: flag01(raw, column) for column in FLAG_COLUMNS},
            "ecg_ok": _finite(raw.get("ecg_hr_bpm")),
            "flags": set(filter(None, str(raw.get("flags") or "").split(";"))),
            "bp": np.array([float(raw[LABELS[t]]) if valid else np.nan for t in TARGETS]),
            "raw": {name: derive(raw, name) for name in names},
        })
    subjects = sorted({c["subject"] for c in cuffs})
    # SAP section 2: a later session with led_readjusted is out as a whole.
    readjusted = {(c["subject"], c["session"]) for c in cuffs
                  if c["led_readjusted"] and c["session"] >= 2}
    pilots = {c["subject"] for c in cuffs if c["pilot"]}
    for c in cuffs:
        c["led_session"] = (c["subject"], c["session"]) in readjusted
    excluded, base = {}, {}
    for s in subjects:
        cal = [c for c in cuffs if c["subject"] == s and c["session"] == 1
               and c["phase"] == "M0" and c["valid"]]
        if not cal:
            excluded[s] = "no_valid_session1_m0"
            continue
        bp0 = np.mean([c["bp"] for c in cal], axis=0)
        feat0 = {}
        for name in names:
            values = [c["raw"][name] for c in cal if c["raw"][name] is not None]
            feat0[name] = float(np.median(values)) if values else None
        base[s] = (bp0, feat0)
    for c in cuffs:
        if c["subject"] not in base:
            c["delta_bp"], c["x"] = np.full(2, np.nan), {}
            continue
        bp0, feat0 = base[c["subject"]]
        c["delta_bp"] = c["bp"] - bp0
        c["x"] = {n: c["raw"][n] - feat0[n] for n in names
                  if c["raw"][n] is not None and feat0[n] is not None}
        c["main_ok"] = c["valid"] and all(n in c["x"] for n in set(main_ppg) | set(main_full))
    for s in subjects:
        if s in excluded:
            continue
        mine = [c for c in cuffs if c["subject"] == s]
        if s in pilots:
            excluded[s] = "pilot"
            continue
        passing = {k for k in {c["session"] for c in mine}
                   if sum(c["main_ok"] for c in mine if c["session"] == k) >= 2
                   and (s, k) not in readjusted}
        if 1 not in passing:
            excluded[s] = "session1_not_passing"
        elif not any(k >= 2 for k in passing):
            excluded[s] = "no_later_session_passing"
    eligible = [s for s in subjects if s not in excluded]
    for c in cuffs:
        c["eligible"] = c["subject"] in eligible
        c["in_main"] = (c["eligible"] and c["session"] >= 2 and c.get("main_ok", False)
                        and not c["led_session"])
        c["trainable"] = c["eligible"] and c.get("main_ok", False) and not c["led_session"]
    return {"cuffs": cuffs, "subjects": subjects, "eligible": eligible,
            "excluded": excluded, "names": names,
            "led_readjusted_sessions": sorted(f"{s}|S{k:03d}" for s, k in readjusted)}


def phase_columns(cuff):
    """SAP secondary endpoint 10: M1, M2 and session >= 2 as 0/1."""
    return [float(cuff["phase"] == "M1"), float(cuff["phase"] == "M2"),
            float(cuff["session"] >= 2)]


def _design(cuffs, features, with_phase):
    x = np.array([[c["x"][f] for f in features] + (phase_columns(c) if with_phase else [])
                  for c in cuffs], dtype=float)
    return x.reshape(len(cuffs), len(features) + 3 * with_phase)


def loso_ridge(train, test, features, alpha, target, with_phase=False):
    """Ridge of one fold, exactly as ``rq1_holm_loso.loso_ridge``: weight 1 / (cuffs
    of the subject) so each training subject sums to 1, each column divided by its
    SD over the training cuffs (ddof 1, unweighted, no centring), no intercept."""
    x, y = _design(train, features, with_phase), np.array([c["delta_bp"][target] for c in train])
    counts = {}
    for c in train:
        counts[c["subject"]] = counts.get(c["subject"], 0) + 1
    w = np.array([1.0 / counts[c["subject"]] for c in train])
    sd = x.std(axis=0, ddof=1)
    if not np.all(sd > 1e-12 * np.sqrt((x ** 2).mean(axis=0) + 1e-300)):
        raise ValueError("A feature is constant over the training cuffs of a fold")
    z = x / sd
    beta = np.linalg.solve(z.T @ (w[:, None] * z) + alpha * np.eye(z.shape[1]),
                           z.T @ (w * y)) / sd
    return _design(test, features, with_phase) @ beta


def phase_mean(train, test, target, by_phase=True, use_median=False):
    """No-signal baseline (SAP 4): per training subject the mean delta BP of its
    main-set cuffs of each phase (sessions >= 2), then the equal-weight mean (or
    median, endpoint 11) over subjects; 0 when no training subject has the phase.
    Returns (predictions, phases with no training cuff)."""
    label = (lambda c: c["phase"]) if by_phase else (lambda c: "all")
    per = {}
    for c in train:
        if c["in_main"]:
            per.setdefault(label(c), {}).setdefault(c["subject"], []).append(
                c["delta_bp"][target])
    level, empty = {}, set()
    for c in test:
        p = label(c)
        if p not in level:
            means = [np.mean(v) for v in per.get(p, {}).values()]
            if not means:
                empty.add(p)
            level[p] = 0.0 if not means else float(
                np.median(means) if use_median else np.mean(means))
    return np.array([level[label(c)] for c in test]), sorted(empty)


def _fold_predictions(prep, config, eval_key="in_main"):
    """Predictions of every model for every evaluated cuff, LOSO over eligible
    subjects; ``eval_key`` picks the evaluated cuffs (``in_main`` or an endpoint
    set)."""
    alpha = config["ridge"]["alpha"]
    out = {}
    empty_phase = {t: {p: 0 for p in PHASES} for t in TARGETS}
    for held in prep["eligible"]:
        train = [c for c in prep["cuffs"] if c["trainable"] and c["subject"] != held]
        test = [c for c in prep["cuffs"] if c["subject"] == held and c.get(eval_key)]
        if not test:
            continue
        for ti, target in enumerate(TARGETS):
            preds = {"zero_change": np.zeros(len(test))}
            for name, spec in config["models"].items():
                ok = [all(f in c["x"] for f in spec["features"]) for c in test]
                values = np.full(len(test), np.nan)
                rows = [c for c, good in zip(test, ok) if good]
                # Models whose features the main set does not require (PAT-only,
                # ablation) train on the trainable cuffs that have them.
                fit_on = [c for c in train if all(f in c["x"] for f in spec["features"])]
                if rows:
                    values[np.array(ok)] = loso_ridge(fit_on, rows, spec["features"], alpha,
                                                      ti, spec.get("phase_indicators",
                                                                   False))
                preds[name] = values
            preds["phase_mean"], empty = phase_mean(train, test, ti)
            for p in empty:
                empty_phase[target][p] += 1
            preds["phase_median"], _ = phase_mean(train, test, ti, use_median=True)
            preds["constant"], _ = phase_mean(train, test, ti, by_phase=False)
            for name, values in preds.items():
                for c, v in zip(test, values):
                    out.setdefault((target, name), {})[id(c)] = v
    return out, empty_phase


def subject_mae(prep, preds, target, model, select=lambda c: c["in_main"]):
    """{subject: MAE_s} over the selected cuffs that have a prediction."""
    ti = TARGETS.index(target)
    errors = {}
    for c in prep["cuffs"]:
        value = preds.get((target, model), {}).get(id(c))
        if select(c) and value is not None and np.isfinite(value):
            errors.setdefault(c["subject"], []).append(abs(value - c["delta_bp"][ti]))
    return {s: float(np.mean(v)) for s, v in errors.items()}


def _ci(values, counts, level, method):
    low, high = interval(np.asarray(values, float)[None, :], counts, level, method)
    return [float(low[0]), float(high[0])]


def reading(low, high, delta):
    """SAP section 7, on the CI [L; U] of the mean d_s."""
    if delta is None:
        return "delta_not_set"
    if high < -delta:
        return "benefit_at_delta"
    if high < 0 and low < -delta <= high:
        return "benefit_below_delta"
    if -delta <= low and high <= delta:
        return "equivalent"
    if low > 0 and high > delta:
        return "harm"
    return "inconclusive"


def _contrast(maes, model, reference, subjects):
    common = [s for s in subjects if s in maes[model] and s in maes[reference]]
    return common, np.array([maes[model][s] - maes[reference][s] for s in common])


def analyze(rows, config):
    """Full SAP v1 analysis; returns a JSON-ready report."""
    prep = prepare(rows, config)
    main = _core(prep, config)
    n = len(prep["eligible"])
    report = {"version": VERSION, "config_version": config["version"],
              "subjects": {"total": len(prep["subjects"]), "eligible": n,
                           "excluded": prep["excluded"],
                           "min_eligible_sap": MIN_ELIGIBLE,
                           "below_min_eligible": n < MIN_ELIGIBLE},
              "warnings": ([f"Only {n} eligible subjects, below the {MIN_ELIGIBLE} of SAP "
                            "section 9; the CIs do not hold their level"]
                           if n < MIN_ELIGIBLE else []),
              "counts": _counts(prep), "main": main, "secondary": {}}
    report["secondary"] = _secondary(rows, prep, config, main)
    return report


def main_decision(upper):
    """SAP sections 6-7 from the CI upper bounds of the main contrasts.

    ``upper[target][level][contrast]`` is the upper CI limit of the mean d_s
    (contrast "d") and d0_s ("d0") at level 0.975 or 0.95. An outcome passes a
    level when both limits are below 0 (intersection-union). Holm (option A):
    both outcomes at 97.5 %; only when exactly one passes is the other judged at
    95 %; when none passes at 97.5 %, nothing is declared. Returns, per target,
    ``declared``, ``level_used`` (the level whose CI is reported), and the
    pass/fail at each level."""
    steps = {level: {t: bool(upper[t][level]["d"] < 0 and upper[t][level]["d0"] < 0)
                     for t in TARGETS} for level in (0.975, 0.95)}
    declared = holm(*(np.array([steps[level][t]]) for level in (0.975, 0.95)
                      for t in TARGETS))
    one_first = any(steps[0.975].values())
    out = {}
    for t, flag in zip(TARGETS, declared):
        out[t] = {"declared": bool(flag[0]),
                  "level_used": 0.95 if one_first and not steps[0.975][t] else 0.975,
                  "passes_at_975": steps[0.975][t], "passes_at_95": steps[0.95][t]}
    return out


def _main_contrasts(maes, full, base, eligible, counts, method):
    """CIs of d and d0 at both Holm levels with one CI method."""
    out = {}
    for name, reference in (("d", base), ("d0", "zero_change")):
        _, d = _contrast(maes, full, reference, eligible)
        out[name] = {level: _ci(d, counts, level, method) for level in (0.975, 0.95)}
    return out


def _core(prep, config):
    eligible = prep["eligible"]
    if len(eligible) < 3:
        raise ValueError("At least three eligible subjects are needed for LOSO and CIs")
    preds, empty_phase = _fold_predictions(prep, config)
    comparison = config["comparison"]
    full, base = comparison["full"], comparison["base"]
    boot = config["bootstrap"]
    counts = draw_counts(boot["draws"], len(eligible), np.random.default_rng(boot["seed"]))
    models = ["zero_change", "constant", "phase_mean", "phase_median", *config["models"]]
    out = {"targets": {}, "phase_baseline_empty_phase_folds": empty_phase,
           "n_folds": len(eligible)}
    contrasts = {"d": base, "d0": "zero_change", "d_phase": "phase_mean"}
    all_maes = {}
    for target in TARGETS:
        maes = {m: subject_mae(prep, preds, target, m) for m in models}
        if any(set(maes[m]) != set(eligible) for m in (full, base, "zero_change")):
            raise ValueError("Every eligible subject needs main-set cuffs")
        all_maes[target] = maes
        result = {"models": _model_table(prep, preds, target, models), "contrasts": {}}
        for name, reference in contrasts.items():
            _, d = _contrast(maes, full, reference, eligible)
            result["contrasts"][name] = {
                "reference": reference, "mean": float(d.mean()),
                "ci_975": _ci(d, counts, 0.975, config["ci_method"]),
                "ci_95": _ci(d, counts, 0.95, config["ci_method"]),
                "per_subject": dict(zip(eligible, d.tolist()))}
        d = np.array([maes[full][s] - maes[base][s] for s in eligible])
        result["wilcoxon_p"] = (float(stats.wilcoxon(d).pvalue)
                                if np.any(d != 0) else None)
        out["targets"][target] = result
    decision = main_decision({t: {level: {name: out["targets"][t]["contrasts"][name][key][1]
                                          for name in ("d", "d0")}
                                  for level, key in ((0.975, "ci_975"), (0.95, "ci_95"))}
                              for t in TARGETS})
    for t in TARGETS:
        result = out["targets"][t]
        # SAP 6-7: the CI at the level actually used for this outcome.
        key = "ci_975" if decision[t]["level_used"] == 0.975 else "ci_95"
        low, high = result["contrasts"]["d"][key]
        result["main_conclusion"] = {
            **decision[t],
            "reading": reading(low, high, config["delta_mmhg"].get(t)),
            "phase_baseline_beaten": result["contrasts"]["d_phase"]["ci_95"][1] < 0}
    out["ci_sensitivity"] = _ci_sensitivity(all_maes, full, base, eligible, counts,
                                            decision)
    return out


def _ci_sensitivity(all_maes, full, base, eligible, counts, decision):
    """SAP section 5: the main conclusion (d and d0, Holm) redone with each
    sensitivity CI method; ``changed`` lists the methods whose declared outcomes
    differ from the main CI, which then reads as not robust."""
    out, changed = {}, []
    for method in SENSITIVITY_METHODS:
        cis = {t: _main_contrasts(all_maes[t], full, base, eligible, counts, method)
               for t in TARGETS}
        redo = main_decision({t: {level: {name: cis[t][name][level][1]
                                          for name in ("d", "d0")}
                                  for level in (0.975, 0.95)} for t in TARGETS})
        out[method] = {t: {**redo[t],
                           "d_ci_975": cis[t]["d"][0.975], "d_ci_95": cis[t]["d"][0.95],
                           "d0_ci_975": cis[t]["d0"][0.975],
                           "d0_ci_95": cis[t]["d0"][0.95]} for t in TARGETS}
        if any(redo[t]["declared"] != decision[t]["declared"] for t in TARGETS):
            changed.append(method)
    return {"methods": out, "changed": changed, "robust": not changed}


def _model_table(prep, preds, target, models):
    """MAE (mean of MAE_s), ME and SD of errors, overall and per phase."""
    ti = TARGETS.index(target)
    table = {}
    for m in models:
        rows = [(c, preds[(target, m)][id(c)]) for c in prep["cuffs"]
                if c["in_main"] and id(c) in preds.get((target, m), {})]
        rows = [(c, v) for c, v in rows if np.isfinite(v)]
        maes = subject_mae(prep, preds, target, m)
        entry = {"mae": float(np.mean(list(maes.values()))) if maes else None}
        for phase in (None, *PHASES):
            errs = np.array([v - c["delta_bp"][ti] for c, v in rows
                             if phase is None or c["phase"] == phase])
            key = "all" if phase is None else phase
            entry[key] = {"n": len(errs),
                          "me": float(errs.mean()) if len(errs) else None,
                          "sd": float(errs.std(ddof=1)) if len(errs) > 1 else None,
                          "mae_pooled": float(np.abs(errs).mean()) if len(errs) else None}
        table[m] = entry
    ref = np.array([c["delta_bp"][ti] for c in prep["cuffs"] if c["in_main"]])
    table["reference_delta"] = {
        "sd": float(ref.std(ddof=1)) if len(ref) > 1 else None,
        "share_abs_above_5": float(np.mean(np.abs(ref) > 5)) if len(ref) else None,
        "by_phase": {p: {"sd": _sd([c["delta_bp"][ti] for c in prep["cuffs"]
                                     if c["in_main"] and c["phase"] == p]),
                         "share_abs_above_5": _share([c["delta_bp"][ti]
                                                      for c in prep["cuffs"]
                                                      if c["in_main"] and c["phase"] == p])}
                     for p in PHASES}}
    return table


def _sd(values):
    return float(np.std(values, ddof=1)) if len(values) > 1 else None


def _share(values):
    return float(np.mean(np.abs(values) > 5)) if len(values) else None


def _counts(prep):
    """SAP sections 2, 4 and 10: cuffs by subject, session and phase; share of
    ECG-lost cuffs per subject; cuffs of each phase that did not reach the main
    set and later sessions with no main-set cuff of a phase."""
    by = {}
    for c in prep["cuffs"]:
        if c["in_main"]:
            key = f"{c['subject']}|S{c['session']:03d}|{c['phase']}"
            by[key] = by.get(key, 0) + 1
    ecg_loss = {}
    later = [c for c in prep["cuffs"] if c["eligible"] and c["session"] >= 2]
    for s in prep["eligible"]:
        mine = [c for c in later if c["subject"] == s and c["valid"]]
        # ECG lost: no ECG heart rate in the cuff window (SAP 10, "mất ECG").
        ecg_loss[s] = sum(not c["ecg_ok"] for c in mine) / len(mine) if mine else None
    by_phase = {}
    for p in PHASES:
        rows = [c for c in later if c["phase"] == p]
        sessions = {(c["subject"], c["session"]) for c in later}
        with_phase = {(c["subject"], c["session"]) for c in rows if c["in_main"]}
        by_phase[p] = {
            "rows": len(rows), "main": sum(c["in_main"] for c in rows),
            "not_valid": sum(not c["valid"] for c in rows),
            "valid_not_computable": sum(c["valid"] and not c.get("main_ok", False)
                                        for c in rows),
            "led_readjusted_session": sum(c["valid"] and c.get("main_ok", False)
                                          and c["led_session"] for c in rows),
            "later_sessions_without_main_cuff": len(sessions - with_phase)}
    return {"main_cuffs": sum(c["in_main"] for c in prep["cuffs"]),
            "by_subject_session_phase": by, "ecg_loss_share": ecg_loss,
            "skipped_by_phase": by_phase,
            "led_readjusted_sessions": prep["led_readjusted_sessions"],
            "safety_stop_in_main": sum(c["in_main"] and c["safety_stop"]
                                       for c in prep["cuffs"])}


def _rerun(rows, config, keep, main_cuffs):
    """A sensitivity endpoint: the full analysis on the rows ``keep`` retains,
    with the rows dropped and the main-set cuffs it loses against the main run."""
    sub = [r for r in rows if keep(r)]
    try:
        prep = prepare(sub, config)
        out = _core(prep, config)
    except ValueError as exc:
        return {"rows_dropped": len(rows) - len(sub), "not_computed": str(exc)}
    kept = sum(c["in_main"] for c in prep["cuffs"])
    return {"rows_dropped": len(rows) - len(sub), "main_cuffs": kept,
            "main_cuffs_change": kept - main_cuffs, **out}


def _secondary(rows, prep, config, main):
    """Secondary endpoints of SAP section 3 (descriptive, not confirmatory)."""
    full, base = config["comparison"]["full"], config["comparison"]["base"]
    preds, _ = _fold_predictions(prep, config)
    out = {}
    for target in TARGETS:
        ti = TARGETS.index(target)
        entry = {}
        for name, select in (("1_m0_only", lambda c: c["in_main"] and c["phase"] == "M0"),
                             *((f"2_phase_{p}", (lambda p: lambda c: c["in_main"]
                                                 and c["phase"] == p)(p)) for p in PHASES)):
            a = subject_mae(prep, preds, target, full, select)
            b = subject_mae(prep, preds, target, base, select)
            common = sorted(set(a) & set(b))
            d = np.array([a[s] - b[s] for s in common])
            entry[name] = {"n_subjects": len(common),
                           "mean_d": float(d.mean()) if len(d) else None,
                           "ci_95": _ci(d, draw_counts(
                               config["bootstrap"]["draws"], len(d),
                               np.random.default_rng(config["bootstrap"]["seed"])),
                               0.95, config["ci_method"]) if len(d) >= 3 else None}
        for name in [m for m in config["models"] if m not in (full, base)]:
            maes = subject_mae(prep, preds, target, name)
            ref = subject_mae(prep, preds, target, base)
            common = sorted(set(maes) & set(ref))
            entry[f"model_{name}"] = {
                "mae": float(np.mean(list(maes.values()))) if maes else None,
                "mean_minus_" + base: float(np.mean([maes[s] - ref[s] for s in common]))
                if common else None}
        phase_ppg = config["comparison"].get("with_phase")
        if phase_ppg:
            a = subject_mae(prep, preds, target, phase_ppg[0])
            b = subject_mae(prep, preds, target, phase_ppg[1])
            d = np.array([a[s] - b[s] for s in prep["eligible"]])
            counts = draw_counts(config["bootstrap"]["draws"], len(d),
                                 np.random.default_rng(config["bootstrap"]["seed"]))
            entry["10_pat_given_phase"] = {"mean_d": float(d.mean()),
                                           "ci_95": _ci(d, counts, 0.95,
                                                        config["ci_method"])}
        a = subject_mae(prep, preds, target, full)
        m = subject_mae(prep, preds, target, "phase_median")
        d = np.array([a[s] - m[s] for s in prep["eligible"]])
        counts = draw_counts(config["bootstrap"]["draws"], len(d),
                             np.random.default_rng(config["bootstrap"]["seed"]))
        entry["11_phase_median_baseline"] = {
            "mean_d": float(d.mean()), "ci_95": _ci(d, counts, 0.95, config["ci_method"])}
        pairs = np.array([(preds[(target, full)][id(c)], c["delta_bp"][ti])
                          for c in prep["cuffs"] if c["in_main"]])
        err = np.abs(pairs[:, 0] - pairs[:, 1])
        entry["9_descriptive"] = {
            "pearson_r": float(np.corrcoef(pairs[:, 0], pairs[:, 1])[0, 1])
            if len(pairs) > 2 else None,
            "share_abs_error_le_5": float(np.mean(err <= 5)),
            "share_abs_error_le_10": float(np.mean(err <= 10))}
        out[target] = entry
    out["3_ppg_only_all_cuffs"] = _ppg_all_cuffs(prep, config)
    exclusion = set(config["sqi_exclusion_flags"])
    main_cuffs = sum(c["in_main"] for c in prep["cuffs"])
    out["5_sqi_filtered"] = _rerun(rows, config, lambda r: not exclusion & set(
        filter(None, str(r.get("flags") or "").split(";"))), main_cuffs)
    out["6_with_led_readjusted"] = _rerun(
        [{**r, "led_readjusted": 0} for r in rows], config, lambda r: True, main_cuffs)
    out["7_without_safety_stops"] = _rerun(
        rows, config, lambda r: not flag01(r, "safety_stop"), main_cuffs)
    out["8_rq2b"] = {"not_computed": "RQ2b same- vs other-session is not part of v1"}
    return out


def _ppg_all_cuffs(prep, config):
    """Endpoint 3: PPG-only on every valid session >= 2 cuff of eligible subjects
    with PPG features, including cuffs without PAT (lost ECG)."""
    base = config["comparison"]["base"]
    features = config["models"][base]["features"]
    for c in prep["cuffs"]:
        c["ppg_eval"] = (c["eligible"] and c["valid"] and c["session"] >= 2
                         and all(f in c["x"] for f in features)
                         and not c["led_session"])
    preds, _ = _fold_predictions(prep, config, "ppg_eval")
    out = {}
    for target in TARGETS:
        maes = subject_mae(prep, preds, target, base, lambda c: c["ppg_eval"])
        out[target] = {"mae": float(np.mean(list(maes.values()))) if maes else None,
                       "n_cuffs": sum(c["ppg_eval"] for c in prep["cuffs"])}
    return out
