"""Sensitivity simulation of RQ1 for SAP v1 (no human data; assumptions only).

    python scripts/simulate_rq1_sensitivity.py

Reads configs/analysis/rq1_sensitivity_v1.json, writes a new directory
runs/rq1_sensitivity/<UTC>/ with results.json, summary.md and report.json
(config hash, code hash, commit). See software/evaluation/rq1_sensitivity.py for
the model and docs/protocol/sap_v1.md section 9 for how the result is used.
"""

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_VERSION = "rq1-sensitivity-runner-v1"
EQUAL_BUDGET = ((25, 2), (17, 3), (30, 2), (20, 3), (35, 2), (23, 3))


def designs(config):
    grid = [(n, k) for n in config["subject_grid"] for k in (2, 3)]
    return sorted(set(grid) | set(EQUAL_BUDGET))


def run(config):
    from software.evaluation.rq1_sensitivity import run_design

    results = []
    seed = config["seed"]
    for t_index, (name, target) in enumerate(config["targets"].items()):
        for m_index, (scenario, m2) in enumerate(target["m2"].items()):
            for e_index, (effect, models) in enumerate(target["models"].items()):
                for d_index, (subjects, sessions) in enumerate(designs(config)):
                    row = run_design(
                        [seed, t_index, m_index, e_index, d_index],
                        config["replicates"], config["bootstrap_draws"], subjects,
                        sessions, target, models, m2, target["deltas"],
                        config["levels"])
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
                        config["levels"])
                    results.append({"target": name, "m2_scenario": f"grid_{mean:g}",
                                    "effect": effect, "m2_mean": mean, **row})
    return results


def summary(results, config):
    lines = ["# RQ1 sensitivity simulation (assumptions only, no human data)", "",
             "Each row: 2000 simulated studies. `CI width`: mean width of the 95 % "
             "subject bootstrap CI of mean d_s (PPG+PAT - PPG-only). `P(U<0)`: share "
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
    return "\n".join(lines)


def main():
    repo = Path(__file__).resolve().parents[1]
    if not __package__:
        sys.path.insert(0, str(repo))
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--config", type=Path,
                        default=repo / "configs/analysis/rq1_sensitivity_v1.json")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    output = args.output or (repo / "runs" / "rq1_sensitivity"
                             / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"))
    if output.exists():
        parser.exit(1, "Output directory already exists; refusing overwrite\n")
    payload = args.config.read_bytes()
    config = json.loads(payload)
    results = run(config)
    from software._provenance import text_file_sha256, text_sha256

    def git(*a):
        try:
            return subprocess.check_output(["git", *a], cwd=repo, text=True).strip()
        except (OSError, subprocess.CalledProcessError):
            return None

    status = git("status", "--porcelain")
    files = {"results.json": (json.dumps(results, indent=1) + "\n").encode("utf-8"),
             "summary.md": (summary(results, config) + "\n").encode("utf-8")}
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
