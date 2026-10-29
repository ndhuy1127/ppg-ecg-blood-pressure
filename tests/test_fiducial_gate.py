"""Acceptance gate and annotator repeatability (decided 2026-10-25): known
answers on hand-built rows, and the export/detect/compare/repeat/gate chain on
SYNTHETIC records. Stand-in marks in these tests are not manual annotations."""

import copy
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from scripts.week05_fiducials import (
    RECORD_COLUMNS, SYNTHETIC_CASES, run_annotate, run_compare, run_detect, run_gate,
    run_repeat, synthetic_record,
)
from software._provenance import text_sha256
from software.evaluation.fiducial_agreement import ANNOTATION_COLUMNS
from software.evaluation.fiducial_gate import gate, group_metrics, repeatability

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "configs/data/week05_huy.json"
CONFIG = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
FLOOR = CONFIG["acceptance"]["segment_floor"]
BOOT = {"seed": 1, "repetitions": 50, "confidence": 0.95}
TOL = {"ecg_r": 0.024, "ppg_foot": 0.048}
LIMITS = {"ecg_r": 8.0, "ppg_foot": 16.0}


def row(record, method, tp, n_ref, n_det, errors, fiducial="ecg_r"):
    return {"record_id": record, "fiducial": fiducial, "method": method, "tp": tp,
            "n_reference": n_ref, "n_detected": n_det, "errors_ms": list(errors)}


def test_group_metrics_average_over_subjects_and_pool_errors():
    # Subject A: 1 of 2 beats, 2 detections, error 10 ms. B: 18 of 18, 2 ms.
    rows = [row("a1", "m", 1, 2, 2, [10.0]), row("b1", "m", 9, 9, 9, [2.0] * 9),
            row("b2", "m", 9, 9, 9, [2.0] * 9)]
    metrics = group_metrics(rows, {"a1": "A", "b1": "B", "b2": "B"}, FLOOR, BOOT)
    assert metrics["sensitivity"] == pytest.approx(0.75)  # Pooled would be 0.95.
    assert metrics["ppv"] == pytest.approx(0.75)  # Pooled would be 19 / 20.
    assert metrics["mae_ms"] == pytest.approx(6.0)  # Pooled would be 46 / 19.
    assert metrics["bias_ms"] == pytest.approx(46 / 19)
    assert metrics["sd_ms"] == pytest.approx(np.std([10.0] + [2.0] * 18, ddof=1))
    assert metrics["segment_fraction"] == pytest.approx(2 / 3)  # a1: sens 0.5.
    assert metrics["worst_segment"]["record_id"] == "a1"
    assert (metrics["n_subjects"], metrics["n_segments"]) == (2, 3)
    low, high = metrics["ci"]["sensitivity"]
    assert 0.5 <= low <= 0.75 <= high <= 1.0


def test_undefined_subject_metrics_and_unmarked_segments_fail():
    good = [row("b1", "m", 9, 9, 9, [0.0] * 9)]
    unmarked = good + [row("a1", "m", 0, 0, 0, [])]
    metrics = group_metrics(unmarked, {"a1": "A", "b1": "B"}, FLOOR, BOOT)
    assert metrics["sensitivity"] is None and metrics["ppv"] is None
    assert metrics["segment_fraction"] == pytest.approx(0.5)
    silent = good + [row("a1", "m", 0, 9, 0, [])]  # Marks, no detection.
    metrics = group_metrics(silent, {"a1": "A", "b1": "B"}, FLOOR, BOOT)
    assert metrics["sensitivity"] == pytest.approx(0.5)
    assert metrics["ppv"] is None and metrics["mae_ms"] is None


def acceptance(**limits):
    base = {"min_sensitivity": 0.99, "min_ppv": 0.99, "max_abs_bias_ms": 4.0,
            "max_mae_ms": 8.0, "max_sd_ms": 8.0}
    return {"version": "test", "segment_floor": FLOOR, "bootstrap": BOOT,
            "limits": {"ecg_r": {**base, **limits}, "ppg_foot": {**base, **limits}},
            "tie_order": {"ecg_r": ["m1", "m2"], "ppg_foot": ["f1"]},
            "repeatability_max_mae_ms": LIMITS, "repeat_min_days": 2}


def table(errors_by_method, records, fiducial):
    """Every record: 10 of 10 beats found, the given errors for each method."""
    return [row(record, method, 10, 10, 10, errors, fiducial)
            for method, errors in errors_by_method.items() for record in records]


SUBJECTS = {"s1": "S1", "s2": "S2", "c1": "C1", "c2": "C2"}
GROUPS = {"selection": ["S1", "S2"], "confirmation": ["C1", "C2"]}
FOOT = table({"f1": [0.0] * 10}, ["s1", "s2", "c1", "c2"], "ppg_foot")


def test_winner_comes_from_selection_and_only_it_is_confirmed():
    # Selection favours m1; confirmation would favour m2.
    rows = (table({"m1": [1.0, -1.0] * 5, "m2": [3.0, -3.0] * 5}, ["s1", "s2"], "ecg_r")
            + table({"m1": [2.0, -2.0] * 5, "m2": [0.0] * 10}, ["c1", "c2"], "ecg_r")
            + FOOT)
    result = gate(rows, SUBJECTS, GROUPS, acceptance())
    r = result["fiducials"]["ecg_r"]
    assert r["winner"] == "m1" and r["confirmed"]
    assert r["confirmation"]["mae_ms"] == pytest.approx(2.0)  # m1, not m2.
    assert result["detectors_confirmed"]


def test_failed_winner_is_not_replaced_by_a_passing_alternative():
    rows = (table({"m1": [1.0, -1.0] * 5, "m2": [2.0, -2.0] * 5}, ["s1", "s2"], "ecg_r")
            + table({"m1": [6.0] * 10, "m2": [0.0] * 10}, ["c1", "c2"], "ecg_r")
            + FOOT)
    result = gate(rows, SUBJECTS, GROUPS, acceptance())
    r = result["fiducials"]["ecg_r"]
    assert r["winner"] == "m1" and not r["confirmed"]
    assert not r["confirmation"]["checks"]["abs_bias_ms"]
    assert not result["detectors_confirmed"]


def test_tie_order_and_no_passing_method():
    same = table({"m1": [2.0, -2.0] * 5, "m2": [2.0, -2.0] * 5}, ["s1", "s2"], "ecg_r")
    conf = table({"m1": [0.0] * 10, "m2": [0.0] * 10}, ["c1", "c2"], "ecg_r")
    assert gate(same + conf + FOOT, SUBJECTS, GROUPS,
                acceptance())["fiducials"]["ecg_r"]["winner"] == "m1"
    missed = [{**x, "tp": 9, "errors_ms": x["errors_ms"][:9]} for x in same]
    result = gate(missed + conf + FOOT, SUBJECTS, GROUPS, acceptance())
    assert result["fiducials"]["ecg_r"]["winner"] is None  # Sensitivity 0.9.
    assert result["fiducials"]["ecg_r"]["confirmation"] is None
    assert not result["detectors_confirmed"]


def test_gate_refuses_overlap_missing_subjects_incomplete_grid_and_tie_order():
    rows = (table({"m1": [0.0] * 10, "m2": [0.0] * 10}, ["s1", "s2", "c1", "c2"],
                  "ecg_r") + FOOT)
    with pytest.raises(ValueError, match="both groups"):
        gate(rows, SUBJECTS, {"selection": ["S1", "C1"], "confirmation": ["C1"]},
             acceptance())
    with pytest.raises(ValueError, match="differ"):
        gate(rows, SUBJECTS, {"selection": ["S1"], "confirmation": ["C2"]},
             acceptance())
    with pytest.raises(ValueError, match="every planned segment"):
        gate([x for x in rows if x["record_id"] != "c2" or x["method"] != "m2"],
             SUBJECTS, GROUPS, acceptance())
    bad = acceptance()
    bad["tie_order"]["ecg_r"] = ["m1"]
    with pytest.raises(ValueError, match="tie_order"):
        gate(rows, SUBJECTS, GROUPS, bad)


def marks(records, offset_s=0.0, annotator="Tester", day="2026-10-25", region=9.5):
    rows = []
    for record, times in records.items():
        for fiducial in ("ecg_r", "ppg_foot"):
            shift = offset_s if fiducial == "ppg_foot" else offset_s / 2
            rows += [{"record_id": record, "split": "train", "fiducial": fiducial,
                      "time_s": t + shift, "review_start_s": 0.5,
                      "review_end_s": region, "annotator": annotator,
                      "annotated_on": day, "note": ""} for t in times]
    return pd.DataFrame(rows, columns=ANNOTATION_COLUMNS)


def test_repeatability_known_answer_and_session_rules():
    first = marks({"r1": [1.0, 2.0, 3.0], "r2": [1.5, 2.5]})
    second = marks({"r1": [1.0, 2.0, 3.0]}, offset_s=0.010, day="2026-10-27")
    result = repeatability(first, second, TOL, LIMITS, 2, ["r1"])
    assert result["fiducials"]["ecg_r"]["mae_ms"] == pytest.approx(5.0)
    assert result["fiducials"]["ppg_foot"]["bias_ms"] == pytest.approx(10.0)
    assert result["passed"] and result["days_apart"] == 2
    late = marks({"r1": [1.0, 2.0, 3.0]}, offset_s=0.020, day="2026-10-27")
    assert not repeatability(first, late, TOL, LIMITS, 2, ["r1"])["passed"]
    for bad, message in ((marks({"r1": [1.0]}, day="2026-10-26"), "2 days"),
                         (marks({"r1": [1.0]}, annotator="Other", day="2026-10-27"),
                          "themself"),
                         (marks({"r2": [1.5]}, day="2026-10-27"), "exactly"),
                         (marks({"r1": [1.0]}, day="2026-10-27", region=9.0),
                          "regions differ")):
        with pytest.raises(ValueError, match=message):
            repeatability(first, bad, TOL, LIMITS, 2, ["r1"])


def test_repeatability_fails_when_marks_are_missing_or_far_apart():
    first = marks({"r1": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0]})
    # 7 of 8 beats 100 ms later: only the unchanged one matches (MAE 0).
    moved = [1.0] + [t + 0.1 for t in (2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0)]
    second = marks({"r1": moved}, day="2026-10-27")
    result = repeatability(first, second, TOL, LIMITS, 2, ["r1"])
    assert result["fiducials"]["ecg_r"]["mae_ms"] == 0
    assert not result["fiducials"]["ecg_r"]["complete_correspondence"]
    assert not result["passed"]


def test_session_may_span_sittings_and_days_count_from_its_end():
    first = pd.concat([marks({"r1": [1.0, 2.0]}, day="2026-10-25"),
                       marks({"r2": [1.5]}, day="2026-10-26")], ignore_index=True)
    second = marks({"r1": [1.0, 2.0]}, day="2026-10-28")
    assert repeatability(first, second, TOL, LIMITS, 2, ["r1"])["days_apart"] == 2
    with pytest.raises(ValueError, match="2 days"):
        repeatability(first, marks({"r1": [1.0, 2.0]}, day="2026-10-27"), TOL,
                      LIMITS, 2, ["r1"])


# --- the command chain on SYNTHETIC records ---------------------------------------

def write_records(directory, records):
    directory.mkdir(parents=True)
    rows = []
    for record_id, subject, (ecg, ppg, ecg_fs, ppg_fs) in records:
        path = directory / f"{record_id}.npz"
        np.savez(path, ecg=ecg, ppg=ppg)
        rows.append({"record_id": record_id, "subject_id": subject, "split": "train",
                     "source_type": "SYNTHETIC", "origin": "synthetic",
                     "ecg_fs_hz": ecg_fs, "ppg_fs_hz": ppg_fs, "file": path.name,
                     "file_sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    pd.DataFrame(rows, columns=RECORD_COLUMNS).to_csv(
        directory / "records.csv", index=False, lineterminator="\n")
    return hashlib.sha256((directory / "records.csv").read_bytes()).hexdigest()


def stand_in_marks(path, records_dir, truth, day):
    """Generated truth written as if marked, with the sidecar annotate writes."""
    rows = []
    for record_id, (r_times, feet) in truth.items():
        for fiducial, times in (("ecg_r", r_times), ("ppg_foot", feet)):
            rows += [{"record_id": record_id, "split": "train", "fiducial": fiducial,
                      "time_s": f"{t:.6f}", "review_start_s": 0.5,
                      "review_end_s": 9.5, "annotator": "Tester",
                      "annotated_on": day, "note": ""}
                     for t in times if 0.5 <= t <= 9.5]
    pd.DataFrame(rows, columns=ANNOTATION_COLUMNS).to_csv(
        path, index=False, lineterminator="\n")
    records_sha = hashlib.sha256((records_dir / "records.csv").read_bytes()).hexdigest()
    path.with_name(path.stem + ".provenance.json").write_text(json.dumps({
        "output_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "provenance": {"inputs_sha256": {"records_csv": records_sha}}}))
    return path


@pytest.fixture
def chain(tmp_path):
    """Four one-segment subjects (2 + 2 groups), two repeat segments."""
    config = tmp_path / "w5.json"
    plan = {**CONFIG["review_plan"], "n_subjects": 4, "per_subject": 1,
            "selection_subjects": 2, "repeat_segments": 2}
    config.write_text(json.dumps({**CONFIG, "review_plan": plan}), encoding="utf-8")
    export = tmp_path / "export"
    records, truth = [], {}
    for k, rr in enumerate((1.0, 0.9, 0.8, 0.95)):
        ecg, ppg, ecg_fs, ppg_fs, r, feet = synthetic_record(
            **{**SYNTHETIC_CASES["SYN_CLEAN_HR60"], "rr_s": rr})
        records.append((f"SYN_R{k}", f"SYN_S{k}", (ecg, ppg, ecg_fs, ppg_fs)))
        truth[f"SYN_R{k}"] = (r, feet)
    info = {"review_plan": plan,
            "groups": {"selection": ["SYN_S0", "SYN_S1"],
                       "confirmation": ["SYN_S2", "SYN_S3"]},
            "records_csv_sha256": {
                "main": write_records(export / "main", records),
                "repeat": write_records(export / "repeat", records[:1] + records[2:3])},
            "provenance": {"inputs_sha256": {
                "config": text_sha256(config.read_bytes())}}}
    (export / "export.json").write_text(json.dumps(info))
    run_detect(export / "main", config, tmp_path / "det.csv")
    first = stand_in_marks(tmp_path / "first.csv", export / "main", truth,
                           "2026-10-25")
    run_compare(first, tmp_path / "det.csv", config, tmp_path / "agreement.json")
    second = stand_in_marks(tmp_path / "second.csv", export / "repeat",
                            {k: truth[k] for k in ("SYN_R0", "SYN_R2")}, "2026-10-27")
    return {"dir": tmp_path, "config": config, "export": export / "export.json",
            "info": info, "first": first, "second": second, "truth": truth}


def test_chain_selects_confirms_and_needs_repeatability(chain):
    d, config, export = chain["dir"], chain["config"], chain["export"]
    result = run_gate(d / "agreement.json", export, config, d / "gate.json")
    # Documented SYNTHETIC behaviour: prominence also returns T waves at HR 60;
    # tangent (+27 ms) and d2_max (+9 ms) fail |bias| <= 8 ms.
    assert result["fiducials"]["ecg_r"]["winner"] == "derivative_energy"
    assert result["fiducials"]["ecg_r"]["selection"]["prominence"]["passed"] is False
    assert result["fiducials"]["ppg_foot"]["winner"] == "valley_min"
    assert result["detectors_confirmed"]
    assert result["verdict"] == "PENDING_REPEATABILITY"
    assert "SYN_S" not in (d / "gate.json").read_text(encoding="utf-8")
    repeat = run_repeat(chain["first"], chain["second"], export, config,
                        d / "repeat.json")
    assert repeat["passed"] and repeat["fiducials"]["ecg_r"]["mae_ms"] == 0
    final = run_gate(d / "agreement.json", export, config, d / "gate2.json",
                     d / "repeat.json")
    assert final["repeatability_passed"] is True and final["verdict"] == "B4_ALLOWED"


def test_chain_refusals(chain):
    d, config, export = chain["dir"], chain["config"], chain["export"]
    with pytest.raises(ValueError, match="other records"):
        run_repeat(chain["second"], chain["first"], export, config, d / "bad.json")
    other = copy.deepcopy(chain["info"])
    other["records_csv_sha256"]["main"] = "0" * 64
    (export.parent / "other.json").write_text(json.dumps(other))
    with pytest.raises(ValueError, match="differs from export"):
        run_gate(d / "agreement.json", export.parent / "other.json", config,
                 d / "bad2.json")
    with pytest.raises(ValueError, match="another config"):
        run_gate(d / "agreement.json", export, CONFIG_PATH, d / "bad3.json")
    # Marks without provenance never reach the gate.
    bare = d / "bare.csv"
    bare.write_bytes(chain["first"].read_bytes())
    run_compare(bare, d / "det.csv", config, d / "agreement_bare.json",
                allow_annotations_without_provenance=True)
    with pytest.raises(ValueError, match="verified provenance"):
        run_gate(d / "agreement_bare.json", export, config, d / "bad4.json")
    # A repeatability result whose passed is not true, or from other marks.
    run_repeat(chain["first"], chain["second"], export, config, d / "repeat.json")
    fake = json.loads((d / "repeat.json").read_text(encoding="utf-8"))
    fake["passed"] = None
    (d / "repeat_null.json").write_text(json.dumps(fake))
    result = run_gate(d / "agreement.json", export, config, d / "gate_null.json",
                      d / "repeat_null.json")
    assert result["verdict"] == "B4_NOT_ALLOWED"
    fake["provenance"]["inputs_sha256"]["first"] = "f" * 64
    (d / "repeat_other.json").write_text(json.dumps(fake))
    with pytest.raises(ValueError, match="other first-session"):
        run_gate(d / "agreement.json", export, config, d / "bad5.json",
                 d / "repeat_other.json")


def test_annotate_resumes_an_interrupted_session(chain, monkeypatch):
    import matplotlib
    matplotlib.use("Agg", force=True)
    import matplotlib.pyplot as plt

    main_dir, out = chain["export"].parent / "main", chain["dir"] / "manual.csv"
    shown = []

    def show(*args, **kwargs):
        shown.append(1)
        if len(shown) == 2:
            raise KeyboardInterrupt  # The annotator stops during record 2.

    monkeypatch.setattr(plt, "show", show)
    with pytest.raises(KeyboardInterrupt):
        run_annotate(main_dir, out, "HUY", "2026-10-25", 0.5)
    assert not (chain["dir"] / "manual.provenance.json").exists()
    with pytest.raises(FileExistsError):
        run_annotate(main_dir, out, "HUY", "2026-10-25", 0.5)
    with pytest.raises(ValueError, match="same records"):
        run_annotate(main_dir, out, "OTHER", "2026-10-26", 0.5, resume=True)
    monkeypatch.setattr(plt, "show", lambda *a, **k: shown.append(1))
    assert run_annotate(main_dir, out, "HUY", "2026-10-26", 0.5, resume=True) == out
    table = pd.read_csv(out, dtype=str)
    assert list(dict.fromkeys(table.record_id)) == ["SYN_R0", "SYN_R1", "SYN_R2",
                                                    "SYN_R3"]
    assert set(table.annotated_on) == {"2026-10-25", "2026-10-26"}
    sidecar = json.loads((chain["dir"] / "manual.provenance.json").read_text())
    assert [s["first_record"] for s in sidecar["sittings"]] == [0, 1]
    with pytest.raises(FileExistsError):
        run_annotate(main_dir, out, "HUY", "2026-10-27", 0.5, resume=True)


def test_undefined_metrics_block_selection_and_confirmation():
    good = {"m1": [1.0, -1.0] * 5, "m2": [2.0, -2.0] * 5}
    rows = (table(good, ["s1", "s2"], "ecg_r")
            + table(good, ["c1", "c2"], "ecg_r") + FOOT)
    # m1 finds nothing in s2: PPV and MAE of that subject are undefined.
    silent = [{**x, "tp": 0, "n_detected": 0, "errors_ms": []}
              if (x["record_id"], x["method"]) == ("s2", "m1") else x for x in rows]
    result = gate(silent, SUBJECTS, GROUPS, acceptance())
    assert result["fiducials"]["ecg_r"]["selection"]["m1"]["ppv"] is None
    assert result["fiducials"]["ecg_r"]["winner"] == "m2"
    # The winner m1 finds nothing in c2: confirmation fails.
    silent = [{**x, "tp": 0, "n_detected": 0, "errors_ms": []}
              if (x["record_id"], x["method"]) == ("c2", "m1") else x for x in rows]
    result = gate(silent, SUBJECTS, GROUPS, acceptance())
    assert result["fiducials"]["ecg_r"]["winner"] == "m1"
    assert not result["fiducials"]["ecg_r"]["confirmed"]


def test_repeat_segments_must_be_distinct():
    first = marks({"r1": [1.0, 2.0]})
    with pytest.raises(ValueError, match="distinct"):
        repeatability(first, marks({"r1": [1.0, 2.0]}, day="2026-10-27"), TOL,
                      LIMITS, 2, ["r1", "r1"])


def test_export_with_duplicate_or_misplanned_records_is_refused(chain):
    export = chain["export"]
    main_csv = export.parent / "main" / "records.csv"
    rows = pd.read_csv(main_csv, dtype=str)
    for bad in (pd.concat([rows.iloc[:3], rows.iloc[:1]]),  # Duplicate record.
                rows.assign(subject_id=["SYN_S0", "SYN_S0", "SYN_S2", "SYN_S3"]),
                rows.assign(split="val")):  # Not the plan's train split.
        bad.to_csv(main_csv, index=False, lineterminator="\n")
        info = copy.deepcopy(chain["info"])
        info["records_csv_sha256"]["main"] = hashlib.sha256(
            main_csv.read_bytes()).hexdigest()
        export.write_text(json.dumps(info))
        with pytest.raises(ValueError, match="review_plan"):
            run_gate(chain["dir"] / "agreement.json", export, chain["config"],
                     chain["dir"] / "bad_dup.json")


def _interrupt_after(n, shown):
    def show(*args, **kwargs):
        shown.append(1)
        if len(shown) == n:
            raise KeyboardInterrupt
    return show


def test_resume_refuses_edits_and_recovers_an_uncommitted_record(chain, monkeypatch):
    import matplotlib
    matplotlib.use("Agg", force=True)
    import matplotlib.pyplot as plt

    main_dir = chain["export"].parent / "main"
    shown = []
    monkeypatch.setattr(plt, "show", _interrupt_after(3, shown))
    edited = chain["dir"] / "edited.csv"
    with pytest.raises(KeyboardInterrupt):
        run_annotate(main_dir, edited, "HUY", "2026-10-25", 0.5)
    edited.write_text(edited.read_text().replace("2026-10-25", "2026-10-20"))
    with pytest.raises(ValueError, match="last checkpoint"):
        run_annotate(main_dir, edited, "HUY", "2026-10-26", 0.5, resume=True)
    # A crash after the CSV write but before the checkpoint: rows of a third
    # record are in the CSV only. Resume cuts them and marks that record again.
    shown.clear()
    monkeypatch.setattr(plt, "show", _interrupt_after(3, shown))
    crashed = chain["dir"] / "crashed.csv"
    with pytest.raises(KeyboardInterrupt):
        run_annotate(main_dir, crashed, "HUY", "2026-10-25", 0.5)
    with crashed.open("a", encoding="utf-8", newline="") as stream:
        stream.write("SYN_R2,train,ecg_r,,0.5,9.5,HUY,2026-10-25,\n"
                     "SYN_R2,train,ppg_foot,,0.5,9.5,HUY,2026-10-25,\n")
    monkeypatch.setattr(plt, "show", lambda *a, **k: None)
    assert run_annotate(main_dir, crashed, "HUY", "2026-10-26", 0.5,
                        resume=True) == crashed
    table = pd.read_csv(crashed, dtype=str)
    assert table.groupby("record_id").size().to_dict() == {
        f"SYN_R{k}": 2 for k in range(4)}
    sittings = json.loads(
        (chain["dir"] / "crashed.provenance.json").read_text())["sittings"]
    assert sittings[1]["discarded_uncommitted_bytes"] > 0
    progress = chain["dir"] / "broken.progress.json"
    (chain["dir"] / "broken.csv").write_text("x")
    progress.write_text("{not json")
    with pytest.raises(ValueError, match="Unreadable progress"):
        run_annotate(main_dir, chain["dir"] / "broken.csv", "HUY", "2026-10-26", 0.5,
                     resume=True)


def test_gate_refuses_compared_rows_outside_train(chain):
    d, config, export = chain["dir"], chain["config"], chain["export"]
    compared = json.loads((d / "agreement.json").read_text(encoding="utf-8"))
    compared["per_record"][0]["split"] = "val"
    (d / "agreement_val.json").write_text(json.dumps(compared), encoding="utf-8")
    with pytest.raises(ValueError, match="train rows only"):
        run_gate(d / "agreement_val.json", export, config, d / "gate_val.json")


def test_check_limits_fails_every_undefined_metric():
    from software.evaluation.fiducial_gate import check_limits

    limits = acceptance()["limits"]["ecg_r"]
    good = {"sensitivity": 1.0, "ppv": 1.0, "bias_ms": 0.0, "mae_ms": 0.0,
            "sd_ms": 0.0, "segment_fraction": 1.0}
    assert all(check_limits(good, limits, FLOOR).values())
    for name in good:
        checks = check_limits({**good, name: None}, limits, FLOOR)
        assert [k for k, ok in checks.items() if not ok] == [
            "abs_bias_ms" if name == "bias_ms" else name]
