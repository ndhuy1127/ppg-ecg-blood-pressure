"""Generate/replay SYNTHETIC packets only; never decode hardware packets.

v2 configs: JSON packets plus replay. v3 configs: a byte stream in the Packet
Schema V0.1 layout plus session metadata, to be read by scripts/packet_logger.py.
"""

import argparse
import hashlib
import json
import platform
import subprocess
import sys
from pathlib import Path


def _git(repo):
    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo,
                                         text=True).strip()
        dirty = bool(subprocess.check_output(["git", "status", "--porcelain"],
                                             cwd=repo, text=True).strip())
    except (OSError, subprocess.CalledProcessError):
        commit, dirty = None, None
    return commit, dirty


def run_v3(config, case, output):
    """Write config.json, stream.bin, session_metadata.json, then report.json."""
    from software._provenance import text_file_sha256
    from software.data_io import packet_simulation_v3 as v3
    from software.data_io.packet_simulation import json_bytes

    stream, layout = v3.generate_stream(config, case)
    config_sha256 = hashlib.sha256(json_bytes(config)).hexdigest()
    metadata = v3.session_metadata(config, case, config_sha256)
    repo = Path(__file__).resolve().parents[1]
    commit, dirty = _git(repo)
    code = ("scripts/simulate_packets.py", "software/data_io/packet_simulation_v3.py",
            "software/data_io/packet_wire.py")
    channels = {}
    for _, _, channel, _, _, _ in layout:
        channels[channel] = channels.get(channel, 0) + 1
    report = {
        "source_type": "SYNTHETIC", "schema_version": v3.VERSION, "case": case,
        "seed": config["seed"], "config_sha256": config_sha256,
        "stream_sha256": hashlib.sha256(stream).hexdigest(),
        "stream_bytes": len(stream), "packets_sent": len(layout),
        "packets_by_channel": dict(sorted(channels.items())),
        "fault_packets": [{"offset": row[0], "channel": row[2], "seq": row[3]}
                          for row in layout if row[5]],
        "session_metadata_sha256": hashlib.sha256(json_bytes(metadata)).hexdigest(),
        "python": platform.python_version(), "commit": commit,
        "working_tree_dirty": dirty,
        # Tracked code hashed with LF endings, as stored in Git.
        "code_sha256": {name: text_file_sha256(repo / name) for name in code},
        "limitations": [
            "SIMULATION ONLY: fs, N, delay, jitter and faults are simulation "
            "parameters",
            "Payloads are random integers in schema ranges, not waveforms",
            "Event (0xC1) FIRST_SAMPLE_INDEX/FS/T_FIRST values are provisional",
        ],
    }
    output.mkdir(parents=True, exist_ok=False)
    for name, payload in (("config.json", json_bytes(config)), ("stream.bin", stream),
                          ("session_metadata.json", json_bytes(metadata)),
                          ("report.json", json_bytes(report))):
        with (output / name).open("xb") as handle:
            handle.write(payload)
    return report


def run(config_path, case, output, packets_path=None):
    from software._provenance import text_file_sha256
    from software.data_io.packet_simulation import (
        generate_packets, json_bytes, packet_sha256, replay_packets,
    )
    from software.data_io.packet_simulation_v3 import VERSION as V3

    output = Path(output)
    if output.exists():
        raise FileExistsError("Output already exists; refusing overwrite")
    config = json.loads(Path(config_path).read_bytes())
    if isinstance(config, dict) and config.get("schema_version") == V3:
        if packets_path is not None:
            raise ValueError("v3 streams are replayed by scripts/packet_logger.py")
        return run_v3(config, case, output)
    packets = (json.loads(Path(packets_path).read_bytes()) if packets_path is not None
               else generate_packets(config, case))
    result = replay_packets(packets, config)
    repo = Path(__file__).resolve().parents[1]
    commit, dirty = _git(repo)
    code = (Path(__file__), repo / "software/data_io/packet_simulation.py")
    report = {
        "source_type": "SYNTHETIC", "schema_version": config["schema_version"],
        "mode": "replay" if packets_path is not None else "generate_and_replay",
        "case": None if packets_path is not None else case,
        "seed": config["seed"], "config_sha256": hashlib.sha256(json_bytes(config)).hexdigest(),
        "packets_sha256": packet_sha256(packets),
        "result_sha256": hashlib.sha256(json_bytes(result)).hexdigest(),
        "python": platform.python_version(), "commit": commit, "working_tree_dirty": dirty,
        # Tracked code hashed with LF endings, as stored in Git.
        "code_sha256": {p.relative_to(repo).as_posix(): text_file_sha256(p) for p in code},
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
    from software.data_io.packet_simulation_v3 import CASES as V3_CASES

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=repo / "configs/hardware/packet_simulation.json")
    # Each config version accepts only its own cases; the generator checks this.
    extra_cases = tuple(case for case in V3_CASES if case not in CASES)
    parser.add_argument("--case", choices=CASES + extra_cases, default=None)
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