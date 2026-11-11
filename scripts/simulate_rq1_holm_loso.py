"""Joint SBP/DBP Holm and LOSO Ridge simulations for SAP v1 (assumptions only).

    python scripts/simulate_rq1_holm_loso.py

Reads configs/analysis/rq1_holm_loso_v1.json (and the targets and models of its
base_config), writes a new directory runs/rq1_holm_loso/<UTC>/ with
results.json, summary.md and report.json (config hashes, code hashes, commit).
Model: software/evaluation/rq1_holm_loso.py. Use: docs/protocol/sap_v1.md
sections 5, 6 and 9.
"""

import argparse
import copy
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_VERSION = "rq1-holm-loso-runner-v1"
CODE_FILES = ("scripts/simulate_rq1_holm_loso.py",
              "software/evaluation/rq1_holm_loso.py",
              "software/evaluation/rq1_sensitivity.py",
              "software/evaluation/mean_intervals.py")


def run(config, base):
    from software.evaluation.rq1_holm_loso import run_joint, run_loso

    seed, reps, draws = config["seed"], config["replicates"], config["bootstrap_draws"]
    blocks, method = config["draw_blocks"], config["ci_method"]
    targets = base["targets"]
    joint = []
    spec = config["joint"]
    for r_index, rho in enumerate(spec["rho"]):
        for s_index, (m2, effect_sbp, effect_dbp) in enumerate(spec["scenarios"]):
            effect = {"SBP": effect_sbp, "DBP": effect_dbp}
            for d_index, (subjects, sessions) in enumerate(spec["designs"]):
                row = run_joint(
                    [seed, 1, r_index, s_index, d_index], reps, draws, subjects,
                    sessions, targets,
                    {t: targets[t]["models"][effect[t]] for t in targets},
                    {t: targets[t]["m2"][m2] for t in targets}, rho, method, blocks)
                joint.append({"m2_scenario": m2, "effect": effect, **row})
    loso = []
    spec = config["loso"]
    target = targets[spec["target"]]
    for m_index, m2 in enumerate(spec["m2"]):
        for p_index, (effect, gain) in enumerate(spec["pat_gain"].items()):
            features = copy.deepcopy(spec["features"])
            features["pat"]["a"] = gain
            for d_index, (subjects, sessions) in enumerate(spec["designs"]):
                row = run_loso(
                    [seed, 2, m_index, p_index, d_index], reps, draws, subjects,
                    sessions, target, target["m2"][m2], features, spec["base_features"],
                    spec["alpha"], spec["ci_methods"], spec["level"], blocks,
                    spec["theta_replicates"])
                loso.append({"target": spec["target"], "m2_scenario": m2,
                             "effect": effect, "pat_gain": gain, **row})
    return {"joint": joint, "loso": loso}


def summary(results, config):
    reps = config["replicates"]
    lines = ["# RQ1: joint SBP/DBP Holm and LOSO Ridge (assumptions only, no human data)",
             "", f"Each row: {reps} simulated studies. CI method of the joint part: "
             f"`{config['ci_method']}`. All numbers hold only under the assumptions of "
             "the config.", "",
             "## Joint SBP and DBP after Holm (SAP section 6)", "",
             "`main`: share of studies declaring the outcome (CIs of d and d0 both "
             "below 0) after the four Holm steps; `any`: at least one outcome; "
             "`alone 95 %`: one outcome at 95 % without Holm. `d-only any`: Holm on "
             "the CI of d alone, the bound of the error rate when PAT adds nothing but "
             "the model surely beats zero-change (nominal one-sided 2.5 %).", "",
             "| rho | M2 | Effect SBP / DBP | Subjects × sessions | SBP | DBP | any | "
             "both | "
             "SBP alone 95 % | DBP alone 95 % | d-only any |",
             "| ---: | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for row in results["joint"]:
        main = row["main"]
        lines.append(
            f"| {row['rho']:g} | {row['m2_scenario']} | {row['effect']['SBP']} / "
            f"{row['effect']['DBP']} | "
            f"{row['subjects']} × {row['sessions']} | {main['SBP']:.3f} | "
            f"{main['DBP']:.3f} | {main['any']:.3f} | {main['both']:.3f} | "
            f"{main['SBP_alone_95']:.3f} | {main['DBP_alone_95']:.3f} | "
            f"{row['d_only']['any']:.3f} |")
    spec = config["loso"]
    methods = spec["ci_methods"]
    lines += ["", f"## Ridge trained in LOSO ({spec['target']}, alpha {spec['alpha']:g}, "
              f"{100 * spec['level']:g} % CI)", "",
              "`theta ± MC SE`: expected mean d of the design (models trained on n - 1 "
              f"subjects), from a separate simulation of {spec['theta_replicates']} "
              "studies. `SE ratio`: SD over studies of the study mean of d_s divided by "
              "the RMS of the naive SE (SD of d_s / sqrt n). `ICC`: mean correlation of "
              "d between two subjects of one study. `skew`: skewness of the study mean "
              "of d over studies. `miss below / above`: share of CIs entirely below / "
              "above theta, nominal 0.025 each. `shuffled`: the same check for "
              "t_envelope after shuffling each subject column across studies (same "
              "marginal d_s, no dependence within a study). Last two columns: "
              "t_envelope CI entirely below 0 / above 0.", "",
              "| M2 | PAT | Subjects × sessions | theta ± MC SE | mean d0 | SE ratio | "
              "ICC | skew | "
              + " | ".join(f"{m} miss below / above" for m in methods)
              + " | shuffled t_envelope | P(U<0) | P(L>0) |",
              "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | "
              + " | ".join("---" for _ in methods) + " | --- | ---: | ---: |"]
    for row in results["loso"]:
        cells = " | ".join(f"{row['methods'][m]['miss_below']:.3f} / "
                           f"{row['methods'][m]['miss_above']:.3f}" for m in methods)
        env, shuf = row["methods"]["t_envelope"], row["shuffled"]["t_envelope"]
        lines.append(
            f"| {row['m2_scenario']} | {row['effect']} | {row['subjects']} × "
            f"{row['sessions']} | {row['theta']:.3f} ± {row['theta_mc_se']:.3f} | "
            f"{row['mean_d0']:.2f} | {row['se_ratio']:.2f} | "
            f"{row['corr_d_between_subjects']:.3f} | {row['skew_of_study_mean_d']:.2f} | "
            f"{cells} | {shuf['miss_below']:.3f} / {shuf['miss_above']:.3f} | "
            f"{env['p_upper_below_0']:.3f} | {env['p_lower_above_0']:.3f} |")
    return "\n".join(lines)


def main():
    repo = Path(__file__).resolve().parents[1]
    if not __package__:
        sys.path.insert(0, str(repo))
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--config", type=Path,
                        default=repo / "configs/analysis/rq1_holm_loso_v1.json")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    output = args.output or (repo / "runs" / "rq1_holm_loso"
                             / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"))
    if output.exists():
        parser.exit(1, "Output directory already exists; refusing overwrite\n")
    payload = args.config.read_bytes()
    config = json.loads(payload)
    base_path = repo / config["base_config"]
    base_payload = base_path.read_bytes()
    results = run(config, json.loads(base_payload))
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
        "base_config_sha256": text_sha256(base_payload),
        "code_sha256_lf": {name: text_file_sha256(repo / name) for name in CODE_FILES},
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
