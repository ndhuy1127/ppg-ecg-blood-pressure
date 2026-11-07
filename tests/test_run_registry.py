"""Run registry, run collection and the B3 multi-seed determinism check.

Reports here are hand-built dicts with the runners' report.json shape; no
dataset is read. Numbers only exercise the code, never BP performance.
"""

import copy
import json

import pytest

from scripts import collect_runs, run_b3_multiseed
from software.evaluation import run_registry

SHA = "a" * 64
COMMIT = "b" * 40


def _evaluation(mae=10.0):
    def target(value):
        return {m: value for m in run_registry.METRICS}

    def ci(value):
        return {m: {"bounds": [value - 1, value + 1], "valid_repetitions": 2000,
                    "status": "ok"} for m in run_registry.METRICS}

    return {"models": {name: {"point": {"SBP": target(mae), "DBP": target(mae / 2)},
                              "ci": {"SBP": ci(mae), "DBP": ci(mae / 2)}}
                       for name in ("B0", "B3")}}


def _b3_report(seed=42, mae=10.0, split="val", commit=COMMIT):
    return {
        "schema_version": "b3-pipeline-v1",
        "config": {"schema_version": "b3-pipeline-v1", "evaluation_split": split,
                   "b3": {"seed": seed, "params": {}},
                   "bootstrap": {"seed": 20261013}},
        "inputs_sha256": {"config": SHA, "raw": SHA, "split_inventory": SHA,
                          "split_manifest": SHA},
        "split_counts": {"val": {"subjects": 40, "segments": 14400}},
        "evaluation": _evaluation(mae),
        "code_provenance": {"git_commit": commit, "workspace_has_changes": False},
        "run_time_utc": "2026-11-07T00:00:00+00:00",
    }


def _b2_report():
    report = _b3_report()
    report["schema_version"] = report["config"]["schema_version"] = "b2-pipeline-v0"
    report["config"]["xgboost"] = report["config"].pop("b3")
    del report["split_counts"], report["evaluation"]
    report["panels"] = {name: {"counts": {"val": {"subjects": 40, "segments": n}},
                               "evaluation": _evaluation()}
                        for name, n in (("full", 14400), ("hr_available", 14000))}
    return report


def test_b3_report_gives_one_row_per_model_and_target_with_trace():
    rows = run_registry.run_rows(_b3_report(), "b3_pulsedb", "20261107T000000Z")
    assert len(rows) == 4
    assert {(r["model"], r["target"]) for r in rows} == {
        ("B0", "SBP"), ("B0", "DBP"), ("B3", "SBP"), ("B3", "DBP")}
    row = rows[0]
    assert set(row) == set(run_registry.ROW_FIELDS)
    assert row["git_commit"] == COMMIT and row["model_seeds"] == "b3=42"
    assert row["bootstrap_seed"] == 20261013 and row["evaluation_split"] == "val"
    assert row["subject_balanced_mae_ci_low"] == 9.0


def test_b2_report_rows_carry_each_panel():
    rows = run_registry.run_rows(_b2_report(), "b2_pulsedb", "run")
    assert {r["panel"] for r in rows} == {"full", "hr_available"}
    assert {r["model_seeds"] for r in rows} == {"xgboost=42"}
    assert {r["n_rows"] for r in rows if r["panel"] == "hr_available"} == {14000}


@pytest.mark.parametrize("change, message", [
    (lambda r: r["config"].update(evaluation_split="test"), "only val"),
    (lambda r: r["code_provenance"].pop("git_commit"), "git_commit"),
    (lambda r: r["code_provenance"].update(git_commit="abc"), "full commit"),
    (lambda r: r["inputs_sha256"].update(raw="xyz"), "SHA-256"),
    (lambda r: r.update(schema_version="b3-multiseed-v1"), "not a model run"),
    (lambda r: r["config"]["b3"].update(seed=True), "seed"),
])
def test_untraceable_or_non_val_reports_are_refused(change, message):
    report = _b3_report()
    change(report)
    with pytest.raises(ValueError, match=message):
        run_registry.run_rows(report, "b3_pulsedb", "run")


def test_failed_ci_is_kept_empty_not_dropped():
    report = _b3_report()
    report["evaluation"]["models"]["B3"]["ci"]["SBP"]["subject_balanced_mae"] = {
        "bounds": None, "status": "too_few_subjects"}
    rows = run_registry.run_rows(report, "b3_pulsedb", "run")
    row = next(r for r in rows if r["model"] == "B3" and r["target"] == "SBP")
    assert row["subject_balanced_mae_ci_low"] is None
    assert "CI n/a" in run_registry.markdown_table(rows)


def test_seed_spread_is_zero_for_identical_runs_and_catches_a_difference():
    rows = []
    for seed in (42, 43, 44):
        rows += run_registry.run_rows(_b3_report(seed), "b3_multiseed", f"s{seed}")
    spread = run_registry.seed_spread(rows)
    assert all(item["max_minus_min"] == 0 and item["sd"] == 0 for item in spread)
    rows += run_registry.run_rows(_b3_report(45, mae=10.5), "b3_multiseed", "s45")
    spread = run_registry.seed_spread(rows)
    assert max(item["max_minus_min"] for item in spread) == pytest.approx(0.5)


def test_seed_spread_refuses_runs_that_differ_in_more_than_the_seed():
    rows = run_registry.run_rows(_b3_report(42), "x", "a")
    rows += run_registry.run_rows(_b3_report(43, commit="c" * 40), "x", "b")
    with pytest.raises(ValueError, match="git_commit"):
        run_registry.seed_spread(rows)


def test_seed_configs_change_only_the_b3_seed():
    base = _b3_report()["config"]
    configs = run_b3_multiseed.seed_configs(base, [42, 43, 44])
    for seed, payload in configs.items():
        derived = json.loads(payload)
        expected = copy.deepcopy(base)
        expected["b3"]["seed"] = seed
        assert derived == expected
    for bad in ([42, 43], [42, 42, 43], [42, 43, -1]):
        with pytest.raises(ValueError):
            run_b3_multiseed.seed_configs(base, bad)


def test_determinism_needs_identical_predictions_and_metrics():
    rows = []
    for seed in (42, 43, 44):
        rows += run_registry.run_rows(_b3_report(seed), "b3_multiseed", f"s{seed}")
    same = {42: SHA, 43: SHA, 44: SHA}
    assert run_b3_multiseed.determinism(rows, same)[0] == "DETERMINISTIC"
    assert run_b3_multiseed.determinism(rows, {**same, 44: "c" * 64})[0] == "DIFFERS"


def _write(path, report):
    path.mkdir(parents=True)
    (path / "report.json").write_text(json.dumps(report), encoding="utf-8")


def test_collect_lists_every_run_and_every_skip(tmp_path):
    runs = tmp_path / "runs"
    _write(runs / "b3_pulsedb" / "r1", _b3_report())
    _write(runs / "b3_pulsedb" / "r_test", _b3_report(split="test"))
    (runs / "b3_pulsedb" / "r_interrupted").mkdir()
    _write(runs / "b3_multiseed" / "m1" / "seed_42", _b3_report(42))
    (runs / "b3_multiseed" / "m1" / "report.json").write_text(
        json.dumps({"schema_version": "b3-multiseed-v1", "status": "DETERMINISTIC"}),
        encoding="utf-8")
    rows, sources, skipped = collect_runs.collect(
        runs, ["b3_pulsedb", "b3_multiseed", "b2_pulsedb"])
    assert len(rows) == 8
    assert {s["kind"] for s in sources} == {"run", "summary"}
    reasons = {s["path"]: s["reason"] for s in skipped}
    assert "only val" in reasons["b3_pulsedb/r_test/report.json"]
    assert "no report.json" in reasons["b3_pulsedb/r_interrupted"]
    assert reasons["b2_pulsedb"] == "experiment folder missing"

    out = tmp_path / "registry"
    report = collect_runs.write(out, rows, sources, skipped, tmp_path, ["b3_pulsedb"])
    assert report["n_runs"] == 2 and report["n_rows"] == 8
    text = (out / "runs.md").read_text(encoding="utf-8")
    assert "r_interrupted" in text and "status DETERMINISTIC" in text
    with pytest.raises(FileExistsError):
        collect_runs.write(out, rows, sources, skipped, tmp_path, ["b3_pulsedb"])
