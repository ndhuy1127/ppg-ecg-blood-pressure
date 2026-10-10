"""Generate/replay SYNTHETIC packets only; never decode hardware packets."""

import argparse
import hashlib
import json
import platform
import subprocess
import sys
from pathlib import Path


def run(config_path, case, output, packets_path=None):
    from software.data_io.packet_simulation import (
        generate_packets, json_bytes, packet_sha256, replay_packets,
    )

    output = Path(output)
    if output.exists():
        raise FileExistsError("Output already exists; refusing overwrite")
    config = json.loads(Path(config_path).read_bytes())
    packets = (json.loads(Path(packets_path).read_bytes()) if packets_path is not None
               else generate_packets(config, case))
    result = replay_packets(packets, config)
    repo = Path(__file__).resolve().parents[1]
    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
        dirty = bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=repo, text=True).strip())
    except (OSError, subprocess.CalledProcessError):
        commit, dirty = None, None
    code = (Path(__file__), repo / "software/data_io/packet_simulation.py")
    report = {
        "source_type": "SYNTHETIC", "schema_version": config["schema_version"],
        "mode": "replay" if packets_path is not None else "generate_and_replay",
        "case": None if packets_path is not None else case,
        "seed": config["seed"], "config_sha256": hashlib.sha256(json_bytes(config)).hexdigest(),
        "packets_sha256": packet_sha256(packets),
        "result_sha256": hashlib.sha256(json_bytes(result)).hexdigest(),
        "python": platform.python_version(), "commit": commit, "working_tree_dirty": dirty,
        "code_sha256": {p.relative_to(repo).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                        for p in code},
        "packet_count": len(packets), "issue_counts": result["issue_counts"],
        "offset_ppg_minus_ecg_us": result["offset_ppg_minus_ecg_us"],
        "channel_summary": {channel: {
            "accepted_packets": data["accepted_packets"], "samples": len(data["samples"]),
            "gaps": len(data["gaps"]),
        } for channel, data in result["channels"].items()},
        "limitations": result["limitations"],
    }
    # Failures during writes may leave a partial directory; report is written last.
    output.mkdir(parents=True, exist_ok=False)
    for name, value in (("config.json", config), ("packets.json", packets),
                        ("replay.json", result), ("report.json", report)):
        with (output / name).open("xb") as stream:
            stream.write(json_bytes(value))
    return report


def main():
    repo = Path(__file__).resolve().parents[1]
    if not __package__:
        sys.path.insert(0, str(repo))
    from software.data_io.packet_simulation import CASES

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=repo / "configs/hardware/packet_simulation.json")
    parser.add_argument("--case", choices=CASES, default=None)
    parser.add_argument("--packets", type=Path, help="Replay JSON list in the synthetic schema")
    parser.add_argument("--output", required=True, type=Path, help="New output directory")
    args = parser.parse_args()
    if args.case is not None and args.packets is not None:
        parser.error("Choose --case or --packets, not both")
    try:
        report = run(args.config, args.case or "valid", args.output, args.packets)
    except (ValueError, OSError, KeyError) as exc:
        parser.exit(1, f"Simulation failed: {exc}\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()