"""Sensitivity simulation of RQ1 for SAP v1 (no human data; assumptions only).

    python scripts/simulate_rq1_sensitivity.py

Reads configs/analysis/rq1_sensitivity_v2.json, writes a new directory
runs/rq1_sensitivity/<UTC>/ with results.json, ci_check.json, summary.md and
report.json (config hash, code hash, commit). See
software/evaluation/rq1_sensitivity.py for the model and docs/protocol/sap_v1.md
section 9 for how the result is used. The v1 config still runs and gives the v1
numbers (percentile CI only).
"""

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_VERSION = "rq1-sensitivity-runner-v2"
EQUAL_BUDGET = ((25, 2), (17, 3), (30, 2), (20, 3), (35, 2), (23, 3))
READING_DESIGNS = ((25, 2), (20, 3))  # rows of the readings table


def ci_setup(config):
    """CI methods of the run and the primary one (v1 configs: percentile only)."""
    methods = config.get("ci_methods", ["percentile"])
    return methods, config.get("primary_ci_method", "percentile")


def designs(config):
    grid = [(n, k) for n in config["subject_grid"] for k in (2, 3)]
    return sorted(set(grid) | set(EQUAL_BUDGET))


def run(config):
    from software.evaluation.rq1_sensitivity import run_design

    results = []
    seed = config["seed"]
    methods, primary = ci_setup(config)
    blocks = config.get("draw_blocks", 1)
    for t_index, (name, target) in enumerate(config["targets"].items()):
        for m_index, (scenario, m2) in enumerate(target["m2"].items()):
            for e_index, (effect, models) in enumerate(target["models"].items()):
                for d_index, (subjects, sessions) in enumerate(designs(config)):
                    row = run_design(
                        [seed, t_index, m_index, e_index, d_index],
                        config["replicates"], config["bootstrap_draws"], subjects,
                        sessions, target, models, m2, target["deltas"],
                        config["levels"], methods, primary, blocks)
                    results.append({"target": name, "m2_scenario": scenario,
                                    "effect": effect, **row})
    grid = config["p2_grid"]
    for t_index, (name, target) in enumerate(config["targets"].items()):
        spec = grid[name]
        for e_index, effect in enumerate(grid["models"]):
            for m_index, mean in enumerate(spec["m2_means"]):
                for d_index, (subjects, sessions) in enumerate(grid["designs"]):
                    row = run_design(
                        [seed, 100 + t_index, e_index, m_index, d_index],
                        config["replicates"], config["bootstrap_draws"], subjects,
                        sessions, target, target["models"][effect],
                        {"m2_mean": mean, "m2_sd": spec["m2_sd"]}, target["deltas"],
                        config["levels"], methods, primary, blocks)
                    results.append({"target": name, "m2_scenario": f"grid_{mean:g}",
                                    "effect": effect, "m2_mean": mean, **row})
    return results


def run_ci_check(config):
    """Error shares of every CI method on mean-zero d_s of several shapes."""
    from software.evaluation.rq1_sensitivity import ci_error_rates

    spec = config.get("ci_check")
    if not spec:
        return []
    methods, _ = ci_setup(config)
    rows = []
    for d_index, name in enumerate(spec["distributions"]):
        for subjects in spec["subjects"]:
            rows.append({"distribution": name, "subjects": subjects,
                         "methods": ci_error_rates(
                             [config["seed"], 200 + d_index, subjects], name, subjects,
                             spec["replicates"], config["bootstrap_draws"],
                             config["levels"], methods)})
    conv = spec.get("convergence")
    for draws in (conv["draws"] if conv else ()):  # does 1 000 draws suffice?
        rows.append({"distribution": conv["distribution"], "subjects": conv["subjects"],
                     "draws": draws,
                     "methods": ci_error_rates(
                         [config["seed"], 300, draws], conv["distribution"],
                         conv["subjects"], spec["replicates"], draws,
                         config["levels"], methods)})
    return rows


def method_sections(results, check, config):
    """Tables added in runner v2: CI methods under the null, readings, shape check."""
    methods, primary = ci_setup(config)
    lines = []
    for target in config["targets"]:
        null = [r for r in results if r["target"] == target and r["effect"] == "null"
                and "m2_mean" not in r]
        lines += [f"## {target}, CI methods when PAT adds nothing", "",
                  f"All {len(null)} null rows of the tables above (true mean d = 0). "
                  "Nominal share on each side: 0.025 at 95 %, 0.0125 at 97.5 %.", "",
                  "| CI method | Level | P(U<0) mean | P(U<0) min–max | P(L>0) mean | "
                  "CI width mean |",
                  "| --- | ---: | ---: | --- | ---: | ---: |"]
        for method in methods:
            for level in config["levels"]:
                blocks = [r["ci_methods"][method][str(level)] for r in null]
                below = [b["p_upper_below_0"] for b in blocks]
                lines.append(
                    f"| {method} | {100 * level:g} % | {sum(below) / len(below):.4f} | "
                    f"{min(below):.3f}–{max(below):.3f} | "
                    f"{sum(b['p_lower_above_0'] for b in blocks) / len(blocks):.4f} | "
                    f"{sum(b['ci_width_mean'] for b in blocks) / len(blocks):.2f} |")
        mid = config["targets"][target]["deltas"][1]
        lines += ["", f"## {target}, readings of SAP section 7 at δ = {mid:g} "
                  f"({primary} CI, 95 %)", "",
                  "Columns follow the five readings in SAP order: U < −δ; U < 0 and "
                  "L < −δ ≤ U (a benefit, δ not shown); −δ ≤ L and U ≤ δ; L > 0 and "
                  "U > δ (error increases); the rest.", "",
                  "| M2 | Effect | Subjects × sessions | mean d | benefit ≥ δ shown | "
                  "benefit, δ not shown | equivalent within δ | error increases | "
                  "inconclusive |",
                  "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |"]
        for row in results:
            if (row["target"] != target or "m2_mean" in row
                    or (row["subjects"], row["sessions"]) not in READING_DESIGNS):
                continue
            share = row["levels"]["0.95"]["readings"][str(mid)]
            lines.append(
                f"| {row['m2_scenario']} | {row['effect']} | {row['subjects']} × "
                f"{row['sessions']} | {row['mean_d']:.2f} | "
                f"{share['benefit_at_delta']:.2f} | {share['benefit_below_delta']:.2f} | "
                f"{share['equivalent']:.2f} | {share['harm']:.2f} | "
                f"{share['inconclusive']:.2f} |")
        lines.append("")
    if check:
        lines += ["## CI method check on mean-zero d_s of several shapes", "",
                  f"{config['ci_check']['replicates']} samples per row, drawn directly "
                  "as d_s with true mean 0 and SD 1 (not from the BP model, whose normal "
                  "errors favour the Student t interval). `below`/`above`: share of 95 % "
                  "CIs entirely below/above 0; nominal 0.025 each.", "",
                  "| Shape of d_s | Subjects | " + " | ".join(
                      f"{m} below / above" for m in methods) + " |",
                  "| --- | ---: | " + " | ".join("---" for _ in methods) + " |"]
        for row in check:
            if "draws" in row:
                continue
            cells = " | ".join(
                f"{row['methods'][m]['0.95']['below']:.3f} / "
                f"{row['methods'][m]['0.95']['above']:.3f}" for m in methods)
            lines.append(f"| {row['distribution']} | {row['subjects']} | {cells} |")
        lines.append("")
        converged = [row for row in check if "draws" in row]
        if converged:
            lines += ["## Number of bootstrap draws", "",
                      f"Shape `{converged[0]['distribution']}`, "
                      f"{converged[0]['subjects']} subjects, 97.5 % CIs (nominal 0.0125 "
                      "on each side): the tail of 1 000 draws holds about 12 draws.", "",
                      "| Draws | " + " | ".join(
                          f"{m} below / above" for m in methods) + " |",
                      "| ---: | " + " | ".join("---" for _ in methods) + " |"]
            for row in converged:
                cells = " | ".join(
                    f"{row['methods'][m]['0.975']['below']:.4f} / "
                    f"{row['methods'][m]['0.975']['above']:.4f}" for m in methods)
                lines.append(f"| {row['draws']} | {cells} |")
            lines.append("")
    return lines


def summary(results, config, check=()):
    _, primary = ci_setup(config)
    lines = ["# RQ1 sensitivity simulation (assumptions only, no human data)", "",
             f"CI method of the tables below: `{primary}` (subject level; the other "
             "methods are compared in the sections at the end). Subject draws: "
             f"{config.get('draw_blocks', 1)} separate set(s) per design.", "",
             "Each row: 2000 simulated studies. `CI width`: mean width of the 95 % "
             "subject-level CI of mean d_s (PPG+PAT - PPG-only). `P(U<0)`: share "
             "of studies whose CI lies below 0; `P(main)`: share where the CIs of "
             "d_s and d0_s (vs zero-change) both lie below 0 (SAP section 6), one "
             "outcome alone, at 95 % (no Holm) and at 97.5 % (Holm's first step); "
             "SBP and DBP are simulated apart, so the Holm procedure itself is not "
             "applied. `inconclusive@δ`: share read as inconclusive at the middle δ. "
             "`R3`: median over studies of the R3 statistic (median of per-subject "
             "median |ΔBP|); `P2`: median over studies of the P2 statistic (median "
             "over subjects of the signed M2 change against same-session M0). All "
             "numbers hold only under the assumptions of the config.", ""]
    for target in config["targets"]:
        mid = config["targets"][target]["deltas"][1]
        for scenario in config["targets"][target]["m2"]:
            lines += [f"## {target}, M2 {scenario}", "",
                      "| Subjects × sessions | Visits | Effect | mean d | mean d0 | "
                      "CI width | P(U<0) | P(main) 95 % | P(main) 97.5 % | "
                      f"inconclusive@δ={mid:g} | SD ΔBP ref | R3 | P2 |",
                      "| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | "
                      "---: | ---: | ---: | ---: |"]
            for row in results:
                if (row["target"], row["m2_scenario"]) != (target, scenario):
                    continue
                level = row["levels"]["0.95"]
                holm = row["levels"]["0.975"]
                lines.append(
                    f"| {row['subjects']} × {row['sessions']} | {row['visits']} | "
                    f"{row['effect']} | {row['mean_d']:.2f} | {row['mean_d0']:.2f} | "
                    f"{level['ci_width_mean']:.2f} | {level['p_upper_below_0']:.2f} | "
                    f"{level['p_main_conclusion']:.2f} | "
                    f"{holm['p_main_conclusion']:.2f} | "
                    f"{level['readings'][str(mid)]['inconclusive']:.2f} | "
                    f"{row['reference_delta_sd']:.1f} | {row['r3_median']:.1f} | "
                    f"{row['p2_median']:.1f} |")
            lines.append("")
        lines += [f"## {target}, P2 grid (M2 mean response varied)", "",
                  "| M2 mean | Effect | Subjects × sessions | P2 | P(main) 95 % | "
                  "P(main) 97.5 % | P(U<0) |",
                  "| ---: | --- | --- | ---: | ---: | ---: | ---: |"]
        for row in results:
            if row["target"] != target or "m2_mean" not in row:
                continue
            lines.append(
                f"| {row['m2_mean']:g} | {row['effect']} | {row['subjects']} × "
                f"{row['sessions']} | {row['p2_median']:.1f} | "
                f"{row['levels']['0.95']['p_main_conclusion']:.2f} | "
                f"{row['levels']['0.975']['p_main_conclusion']:.2f} | "
                f"{row['levels']['0.95']['p_upper_below_0']:.2f} |")
        lines.append("")
    lines += method_sections(results, check, config)
    return "\n".join(lines)


def main():
    repo = Path(__file__).resolve().parents[1]
    if not __package__:
        sys.path.insert(0, str(repo))
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--config", type=Path,
                        default=repo / "configs/analysis/rq1_sensitivity_v2.json")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    output = args.output or (repo / "runs" / "rq1_sensitivity"
                             / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"))
    if output.exists():
        parser.exit(1, "Output directory already exists; refusing overwrite\n")
    payload = args.config.read_bytes()
    config = json.loads(payload)
    results = run(config)
    check = run_ci_check(config)
    from software._provenance import text_file_sha256, text_sha256

    def git(*a):
        try:
            return subprocess.check_output(["git", *a], cwd=repo, text=True).strip()
        except (OSError, subprocess.CalledProcessError):
            return None

    status = git("status", "--porcelain")
    files = {"results.json": (json.dumps(results, indent=1) + "\n").encode("utf-8"),
             "ci_check.json": (json.dumps(check, indent=1) + "\n").encode("utf-8"),
             "summary.md": (summary(results, config, check) + "\n").encode("utf-8")}
    report = {
        "script_version": SCRIPT_VERSION, "source_type": "SIMULATED_ASSUMPTIONS_ONLY",
        "config_sha256": text_sha256(payload),
        "code_sha256_lf": {name: text_file_sha256(repo / name) for name in (
            "scripts/simulate_rq1_sensitivity.py",
            "software/evaluation/rq1_sensitivity.py")},
        "git_commit": git("rev-parse", "HEAD"),
        "workspace_has_changes": None if status is None else bool(status),
        "outputs_sha256": {n: hashlib.sha256(p).hexdigest() for n, p in files.items()},
        "run_time_utc": datetime.now(timezone.utc).isoformat(),
    }
    output.mkdir(parents=True)
    for name, data in files.items():
        (output / name).write_bytes(data)
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n",
                                        encoding="utf-8", newline="\n")
    print("Saved:", output)


if __name__ == "__main__":
    main()
