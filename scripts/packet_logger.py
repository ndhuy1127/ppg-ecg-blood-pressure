"""PC logger for Packet Schema V0.1: record a byte source, or replay a raw file.

record: every received byte, corrupt ones included, goes to raw.bin opened with
exclusive create; PC receive times go to separate files and are never sample
times; packets are decoded and checked, and session_manifest.json is written
last. replay: the same decode/check code on an existing raw file; --expect
compares the result hashes with a session manifest. Live serial is not
implemented: pyserial is not an approved dependency (docs/protocol/packet_logger.md).
"""

import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
import time
from bisect import bisect_right
from datetime import datetime, timezone
from pathlib import Path

CODE_FILES = (
    "scripts/packet_logger.py", "software/data_io/packet_wire.py",
    "software/data_io/packet_receiver.py", "software/_provenance.py",
)
DECODE_OUTPUTS = ("decode.json", "packets.csv", "samples.csv")


def _git(repo, *args):
    try:
        return subprocess.check_output(["git", *args], cwd=repo, text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def _sha256(payload):
    return hashlib.sha256(payload).hexdigest()


def _provenance(repo):
    from software._provenance import text_file_sha256

    status = _git(repo, "status", "--porcelain")
    return {
        "git_commit": _git(repo, "rev-parse", "HEAD"),
        "workspace_has_changes": None if status is None else bool(status),
        # Tracked code hashed with LF endings, as stored in Git.
        "code_sha256_lf": {name: text_file_sha256(repo / name) for name in CODE_FILES},
        "python": platform.python_version(),
        "libraries": "standard library only",
    }


def _inputs(config_path, metadata_path):
    from software._provenance import text_sha256
    from software.data_io.packet_receiver import validate_config, validate_metadata

    config_bytes = Path(config_path).read_bytes()
    metadata_bytes = Path(metadata_path).read_bytes()
    config, metadata = json.loads(config_bytes), json.loads(metadata_bytes)
    validate_config(config)
    validate_metadata(metadata)
    hashes = {"logger_config": text_sha256(config_bytes),
              "session_metadata": _sha256(metadata_bytes)}
    return config, metadata, hashes, config_bytes, metadata_bytes


def _decode_outputs(payload, config, metadata):
    from software.data_io.packet_receiver import analyze_stream, render_outputs
    from software.data_io.packet_wire import decode_bytes

    packets, decoder = decode_bytes(payload, config["read_chunk_bytes"],
                                    config["wire_versions"])
    result, rows, samples = analyze_stream(packets, decoder, config, metadata)
    return render_outputs(result, rows, samples), result


def _write(directory, name, payload):
    with (directory / name).open("xb") as handle:
        handle.write(payload)


def _csv(header, rows):
    lines = [",".join(header)] + [",".join(str(value) for value in row) for row in rows]
    return ("\n".join(lines) + "\n").encode("utf-8")


def record(source, output, config_path, metadata_path, repo, source_name):
    """Log ``source`` until ``read`` returns b"" (end of session).

    ``source`` is any object with ``read(n) -> bytes``: an open file now, a
    serial port once pyserial is approved (it then needs a stop condition).
    """
    from software.data_io.packet_receiver import (
        LOGGER_VERSION, PACKET_SCHEMA, analyze_stream, render_outputs,
    )
    from software.data_io.packet_wire import StreamDecoder

    output = Path(output)
    if output.exists():
        raise FileExistsError("Output directory already exists; refusing overwrite")
    config, metadata, input_hashes, config_bytes, metadata_bytes = _inputs(
        config_path, metadata_path)
    output.mkdir(parents=True, exist_ok=False)
    # Input copies go first, so an interrupted capture still says what it was
    # recorded with. The manifest is still written last.
    inputs = {"logger_config.json": config_bytes,
              "session_metadata.json": metadata_bytes}
    for name, payload in inputs.items():
        _write(output, name, payload)
    started = datetime.now(timezone.utc).isoformat()
    origin = time.monotonic_ns()
    decoder, packets, chunks = StreamDecoder(config["wire_versions"]), [], []
    with (output / "raw.bin").open("xb") as raw:
        while True:
            chunk = source.read(config["read_chunk_bytes"])
            if not isinstance(chunk, bytes):
                raise ValueError("Byte source must return bytes")
            if not chunk:
                break
            received = time.monotonic_ns() - origin
            raw.write(chunk)
            chunks.append((len(chunks), decoder.bytes_seen, len(chunk), received))
            packets += decoder.feed(chunk)
        raw.flush()
        os.fsync(raw.fileno())
    packets += decoder.finish()
    ended = datetime.now(timezone.utc).isoformat()
    result, rows, samples = analyze_stream(packets, decoder, config, metadata)
    outputs = render_outputs(result, rows, samples)
    raw_bytes = (output / "raw.bin").read_bytes()
    # Offline replay of the stored raw must equal the live chunked decode.
    if _decode_outputs(raw_bytes, config, metadata)[0] != outputs:
        raise ValueError("Offline decode of raw.bin differs from the live decode")

    starts = [chunk[1] for chunk in chunks]
    t_rx = []
    for item in packets:
        index = bisect_right(starts, item.offset + item.size - 1) - 1
        packet = item.packet
        t_rx.append((item.offset, packet.session_id, f"0x{packet.channel_id:02X}",
                     packet.seq, index, chunks[index][3]))
    files = {
        **outputs,
        "rx_chunks.csv": _csv(("chunk", "stream_offset", "bytes", "t_rx_monotonic_ns"),
                              chunks),
        "t_rx_packets.csv": _csv(("stream_offset", "session_id", "channel_id", "seq",
                                  "chunk", "t_rx_monotonic_ns"), t_rx),
    }
    for name, payload in files.items():
        _write(output, name, payload)
    files.update(inputs)

    session_ids = [session["session_id"] for session in result["sessions"]]
    null_reasons = dict(metadata["null_reasons"])
    if len(session_ids) != 1:
        null_reasons["session_id"] = (
            "no packet decoded" if not session_ids
            else "several SESSION_IDs in one raw stream (MCU restart); see session_ids"
        )
    outputs_sha256 = {"raw.bin": _sha256(raw_bytes)}
    outputs_sha256.update({name: _sha256(payload) for name, payload in files.items()})
    manifest = {
        "schema_version": PACKET_SCHEMA, "logger_version": LOGGER_VERSION,
        "mode": "record", "source_type": metadata["source_type"],
        "source": {"kind": "file", "name": source_name},
        "session_id": session_ids[0] if len(session_ids) == 1 else None,
        "session_ids": session_ids,
        **{name: metadata[name] for name in (
            "clock_id", "firmware_version", "firmware_commit", "device_id",
            "operator", "electrode_type", "electrode_placement", "channels",
            "simulation",
        )},
        "null_reasons": dict(sorted(null_reasons.items())),
        "pc_start_time_utc": started, "pc_end_time_utc": ended,
        "pc_time_note": "PC clock, reference only; never a sample time",
        "raw": {"file": "raw.bin", "bytes": len(raw_bytes),
                "sha256": outputs_sha256["raw.bin"]},
        "decode": result["decode"], "issue_counts": result["issue_counts"],
        "live_equals_offline_decode": True,
        "inputs_sha256": input_hashes, "outputs_sha256": outputs_sha256,
        "provenance": _provenance(repo),
        "limitations": result["limitations"],
    }
    # The manifest is written last: without it the session is incomplete.
    _write(output, "session_manifest.json",
           (json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False)
            + "\n").encode("utf-8"))
    return manifest


def replay(raw_path, output, config_path, metadata_path, repo, expect=None):
    """Decode an existing raw file into a new directory; never touches the raw."""
    output = Path(output)
    if output.exists():
        raise FileExistsError("Output directory already exists; refusing overwrite")
    config, metadata, input_hashes, _, _ = _inputs(config_path, metadata_path)
    raw_bytes = Path(raw_path).read_bytes()
    raw_sha256 = _sha256(raw_bytes)
    outputs, result = _decode_outputs(raw_bytes, config, metadata)
    if _sha256(Path(raw_path).read_bytes()) != raw_sha256:
        raise ValueError("Raw file changed during replay")
    outputs_sha256 = {name: _sha256(payload) for name, payload in outputs.items()}
    comparison = None
    if expect is not None:
        manifest = json.loads(Path(expect).read_bytes())
        checks = {
            # A manifest of another logger version explains decode differences.
            "logger_version": (manifest.get("logger_version"),
                               result["logger_version"]),
            "raw.bin": (manifest["raw"]["sha256"], raw_sha256),
            **{name: (manifest["outputs_sha256"][name], outputs_sha256[name])
               for name in DECODE_OUTPUTS},
            **{f"input:{name}": (manifest["inputs_sha256"][name], value)
               for name, value in input_hashes.items()},
        }
        comparison = {
            "manifest_sha256": _sha256(Path(expect).read_bytes()),
            "mismatches": sorted(name for name, (a, b) in checks.items() if a != b),
        }
    report = {
        "logger_version": result["logger_version"], "mode": "replay",
        "source_type": result["source_type"],
        "raw": {"name": Path(raw_path).name, "bytes": len(raw_bytes),
                "sha256": raw_sha256},
        "decode": result["decode"], "issue_counts": result["issue_counts"],
        "inputs_sha256": input_hashes, "outputs_sha256": outputs_sha256,
        "expected_manifest": comparison, "provenance": _provenance(repo),
    }
    output.mkdir(parents=True, exist_ok=False)
    for name, payload in outputs.items():
        _write(output, name, payload)
    _write(output, "replay_report.json",
           (json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False)
            + "\n").encode("utf-8"))
    return report


def main():
    repo = Path(__file__).resolve().parents[1]
    if not __package__:
        sys.path.insert(0, str(repo))
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    runs = repo / "runs" / "packet_logger"
    for name in ("record", "replay"):
        command = commands.add_parser(name)
        if name == "record":
            command.add_argument("--source-file", type=Path, required=True,
                                 help="Byte stream read as if it came from the device")
        else:
            command.add_argument("--raw", type=Path, required=True)
            command.add_argument("--expect", type=Path,
                                 help="session_manifest.json to compare hashes with")
        command.add_argument("--metadata", type=Path, required=True,
                             help="Session metadata JSON (schema section 11)")
        command.add_argument("--config", type=Path,
                             default=repo / "configs/hardware/packet_logger.json")
        command.add_argument("--output", type=Path,
                             default=runs / f"{stamp}_{name}")
    args = parser.parse_args()
    try:
        if args.command == "record":
            with args.source_file.open("rb") as source:
                summary = record(source, args.output, args.config, args.metadata,
                                 repo, args.source_file.name)
        else:
            summary = replay(args.raw, args.output, args.config, args.metadata,
                             repo, args.expect)
    except (ValueError, OSError, KeyError) as exc:
        parser.exit(1, f"Packet logger stopped: {exc}\n")
    print(json.dumps({
        "mode": summary["mode"], "source_type": summary["source_type"],
        "raw_sha256": summary["raw"]["sha256"], "issue_counts": summary["issue_counts"],
        "expected_manifest": summary.get("expected_manifest"),
        "output": str(args.output),
    }, indent=2))
    comparison = summary.get("expected_manifest")
    if comparison is not None and comparison["mismatches"]:
        parser.exit(1, "Replay differs from the expected session manifest\n")


if __name__ == "__main__":
    main()
