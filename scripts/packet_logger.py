"""PC logger for Packet Schema V0.1: record a byte source, or replay a raw file.

record: every received byte, corrupt ones included, goes to raw.bin opened with
exclusive create; PC receive times go to separate files and are never sample
times; packets are decoded and checked, and session_manifest.json is written
last. replay: the same decode/check code on an existing raw file; --expect
compares the result hashes with a session manifest. record --port reads a serial
port (pyserial) until --duration-s elapses or Ctrl+C (docs/protocol/packet_logger.md).
record --commands also sends commands to the device from the recording's
command_inbox.jsonl (scripts/device_command.py; Packet Schema V0.2 section 13).

Participant data (metadata subject_id SUB###) is recorded only as
data/raw/<subject_id>/<session_id>/<recording>/ and needs --subject-id and
--session-id equal to the metadata; bring-up and SYNTHETIC recordings stay out of
data/raw/ (default runs/packet_logger/). Replay output never goes to data/raw/.
"""

import argparse
import hashlib
import json
import os
import platform
import re
import subprocess
import sys
import time
from bisect import bisect_right
from datetime import datetime, timezone
from pathlib import Path

CODE_FILES = (
    "scripts/packet_logger.py", "software/data_io/packet_wire.py",
    "software/data_io/packet_receiver.py", "software/_provenance.py",
    "software/data_io/command_wire.py", "software/data_io/command_desk.py",
)
COMMAND_FILES = ("command_inbox.jsonl", "commands_sent.jsonl")
DECODE_OUTPUTS = ("decode.json", "packets.csv", "samples.csv")
# One path component under data/raw/<subject_id>/<session_id>/.
RECORDING_NAME = re.compile(r"[0-9A-Za-z][0-9A-Za-z_.-]*")


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


def _resolved(path):
    return os.path.normcase(str(Path(path).resolve()))


def _contains(root, path):
    try:
        return os.path.commonpath([path, root]) == root
    except ValueError:  # another drive
        return False


def _inside(path, root):
    """Inside ``root`` as written or once links are resolved."""
    lexical = [os.path.normcase(os.path.abspath(p)) for p in (root, path)]
    return _contains(*lexical) or _contains(_resolved(root), _resolved(path))


def check_location(output, metadata, repo, raw_root=None, subject_id=None,
                   session_id=None):
    """Refuse a record ``output`` that does not fit the metadata's subject.

    ``subject_id`` and ``session_id`` are what the operator typed (``--subject-id``,
    ``--session-id``); they must equal the metadata for participant data, so a
    stale metadata file of another participant is caught before any byte is read.
    Participant data goes only to ``<raw_root>/<subject_id>/<session_id>/<one
    name>`` (never ``runs/``); anything else never goes inside ``raw_root``.
    """
    from software.data_io.packet_receiver import is_participant, study_metadata

    raw_root = Path(raw_root) if raw_root is not None else Path(repo) / "data" / "raw"
    study = study_metadata(metadata)
    declared = (study["subject_id"], study["session_id"])
    typed = (subject_id, session_id)
    if (is_participant(metadata) or typed != (None, None)) and typed != declared:
        raise ValueError(f"--subject-id/--session-id {typed} must equal the session "
                         f"metadata subject_id/session_id {declared}")
    output = Path(output)
    if is_participant(metadata):
        subject, session = declared
        if _inside(output, Path(repo) / "runs"):
            raise ValueError(f"Participant data ({subject}) is never written to runs/; "
                             f"record into data/raw/{subject}/{session}/<recording>")
        # raw_root itself may be a link (an encrypted drive, say), but a subject or
        # session directory that is a link out of it is refused.
        if (_resolved(output.parent) != _resolved(raw_root / subject / session)
                or not _contains(_resolved(raw_root), _resolved(output))
                or not RECORDING_NAME.fullmatch(output.name)):
            raise ValueError(f"Participant data ({subject}) goes only to "
                             f"{raw_root / subject / session}/<recording>; refusing "
                             f"{output}")
    elif _inside(output, raw_root):
        raise ValueError(f"{raw_root} holds participant recordings only; bring-up and "
                         "SYNTHETIC recordings go elsewhere (runs/packet_logger/)")


def _csv(header, rows):
    lines = [",".join(header)] + [",".join(str(value) for value in row) for row in rows]
    return ("\n".join(lines) + "\n").encode("utf-8")


class SerialSource:
    """A serial port as a byte source that ends after ``duration_s`` or Ctrl+C.

    pyserial's ``read`` returns b"" on timeout; here that only means no bytes
    yet, so reading continues until the deadline. Ctrl+C during a read ends the
    session normally (raw, decode and manifest are still written).
    """

    def __init__(self, port, duration_s, name, clock=time.monotonic):
        if not duration_s > 0:
            raise ValueError("duration_s must be > 0")
        self.port, self.name, self.clock = port, name, clock
        self.duration_s = duration_s
        self.deadline = clock() + duration_s
        self.stopped_by = None
        self.on_idle = None  # called after each read timeout with no bytes

    def read(self, n):
        try:
            while self.clock() < self.deadline:
                chunk = self.port.read(n)
                if chunk:
                    return bytes(chunk)
                if self.on_idle is not None:
                    self.on_idle()
        except KeyboardInterrupt:
            self.stopped_by = "keyboard_interrupt"
            return b""
        self.stopped_by = self.stopped_by or "duration"
        return b""

    def write(self, data):
        """Command bytes to the device; returns the count written."""
        written = self.port.write(data)
        return len(data) if written is None else written

    def describe(self):
        import serial

        return {"kind": "serial", "name": self.name, "baudrate": self.port.baudrate,
                "duration_s": self.duration_s, "stopped_by": self.stopped_by,
                "pyserial": serial.__version__}


def open_serial(name, baudrate, timeout_s=0.1, write_timeout_s=0.5):
    """Open ``name`` with DTR and RTS deasserted.

    A write that does not finish within ``write_timeout_s`` raises, so a stuck
    port cannot stall the recording (record --commands).

    The ESP32-S3 USB Serial/JTAG port resets the chip on some DTR/RTS
    transitions (as esptool uses them), so both stay deasserted while opening.
    Not yet checked on the board. The native USB port ignores the baud rate.
    """
    import serial

    port = serial.Serial()
    port.port, port.baudrate, port.timeout = name, baudrate, timeout_s
    port.write_timeout = write_timeout_s
    port.dtr = False
    port.rts = False
    port.open()
    return port


def _lock_reminder(session_id, lock, output):
    return (f"SESSION_ID {session_id}: send the locked LED codes now "
            f"(protocol 6.1): python scripts/device_command.py --recording {output} "
            f"set-ppg-led --green {lock['green']} --red {lock['red']} "
            f"--ir {lock['ir']}")


def record(source, output, config_path, metadata_path, repo, source_name,
           commands=False, clock=time.monotonic, subject_id=None, session_id=None,
           raw_root=None, notify=None):
    """Log ``source`` until ``read`` returns b"" (end of session).

    ``source`` is any object with ``read(n) -> bytes``: an open file, or a
    ``SerialSource`` (its ``describe()`` goes into the manifest). With
    ``commands`` the source also needs ``write(bytes)``; a fresh
    ``command_inbox.jsonl`` is created in ``output`` and served by a
    ``CommandDesk`` after every read, bytes or not (``on_idle``).

    ``output`` must fit the metadata (``check_location``; ``raw_root`` defaults to
    ``<repo>/data/raw``). DEVICE recordings need metadata v1. With ``commands``,
    ``notify(text)`` gets the recording directory at the start and, when the
    metadata has ``ppg_led_lock``, a reminder to send the locked codes at each
    new SESSION_ID (an MCU restart boots with default codes).
    """
    from software.data_io.packet_receiver import (
        LOGGER_VERSION, METADATA_VERSION, analyze_stream, render_outputs,
        study_metadata,
    )
    from software.data_io.packet_wire import StreamDecoder

    output = Path(output)
    if output.exists():
        raise FileExistsError("Output directory already exists; refusing overwrite")
    config, metadata, input_hashes, config_bytes, metadata_bytes = _inputs(
        config_path, metadata_path)
    if metadata["source_type"] == "DEVICE" and (
        metadata["schema_version"] != METADATA_VERSION
    ):
        raise ValueError(f"A DEVICE recording needs {METADATA_VERSION} metadata "
                         "(subject_id stated, or null with a reason for bring-up)")
    check_location(output, metadata, repo, raw_root, subject_id, session_id)
    study = study_metadata(metadata)
    output.mkdir(parents=True, exist_ok=False)
    # Input copies go first, so an interrupted capture still says what it was
    # recorded with. The manifest is still written last.
    inputs = {"logger_config.json": config_bytes,
              "session_metadata.json": metadata_bytes}
    for name, payload in inputs.items():
        _write(output, name, payload)
    desk = journal = None
    if commands:
        from software.data_io.command_desk import CommandDesk

        if not hasattr(source, "write"):
            raise ValueError("Commands need a source that can be written to")
        (output / COMMAND_FILES[0]).open("xb").close()
        journal = (output / COMMAND_FILES[1]).open("x", encoding="utf-8", newline="\n")
        desk = CommandDesk(output / COMMAND_FILES[0], journal, source.write, clock)
        if hasattr(source, "on_idle"):
            source.on_idle = desk.service
    remind = commands and notify is not None
    if remind:
        notify(f"Recording to {output}; commands: python scripts/device_command.py "
               f"--recording {output} ...")
    seen_sessions = set()
    started = datetime.now(timezone.utc).isoformat()
    origin = time.monotonic_ns()
    decoder, packets, chunks = StreamDecoder(config["wire_versions"]), [], []
    try:
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
                new = decoder.feed(chunk)
                packets += new
                if remind and study["ppg_led_lock"] is not None:
                    for item in new:
                        if item.packet.session_id not in seen_sessions:
                            seen_sessions.add(item.packet.session_id)
                            notify(_lock_reminder(item.packet.session_id,
                                                  study["ppg_led_lock"], output))
                if desk is not None:
                    desk.observe([item.packet for item in new])
                    desk.service()
            raw.flush()
            os.fsync(raw.fileno())
    finally:
        if desk is not None:
            desk.close()
            journal.close()
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
        **({name: (output / name).read_bytes() for name in COMMAND_FILES}
           if commands else {}),
        "rx_chunks.csv": _csv(("chunk", "stream_offset", "bytes", "t_rx_monotonic_ns"),
                              chunks),
        "t_rx_packets.csv": _csv(("stream_offset", "session_id", "channel_id", "seq",
                                  "chunk", "t_rx_monotonic_ns"), t_rx),
    }
    for name, payload in files.items():
        if name not in COMMAND_FILES:  # written during the recording
            _write(output, name, payload)
    files.update(inputs)

    # A session that mixes versions appears once per version in the result. The
    # firmware SESSION_ID is device_session_id here (packet-logger-v3); session_id
    # is the study session of the metadata. decode.json and the CSV files keep the
    # wire name session_id for SESSION_ID.
    device_sessions = list(dict.fromkeys(s["session_id"] for s in result["sessions"]))
    null_reasons = dict(metadata["null_reasons"])
    if metadata["schema_version"] != METADATA_VERSION:
        null_reasons.update({name: f"not in {metadata['schema_version']}"
                             for name in study})
    if len(device_sessions) != 1:
        null_reasons["device_session_id"] = (
            "no packet decoded" if not device_sessions
            else "several SESSION_IDs in one raw stream (MCU restart); see "
                 "device_session_ids"
        )
    outputs_sha256 = {"raw.bin": _sha256(raw_bytes)}
    outputs_sha256.update({name: _sha256(payload) for name, payload in files.items()})
    manifest = {
        "packet_schemas": result["packet_schemas"], "logger_version": LOGGER_VERSION,
        "session_metadata_version": metadata["schema_version"],
        "mode": "record", "source_type": metadata["source_type"],
        "source": (source.describe() if hasattr(source, "describe")
                   else {"kind": "file", "name": source_name}),
        **study,
        "device_session_id": device_sessions[0] if len(device_sessions) == 1 else None,
        "device_session_ids": device_sessions,
        # Schema, device info and locked LED codes as decoded, per SESSION_ID.
        "sessions": [{"device_session_id": s["session_id"],
                      "packet_schema": s["packet_schema"],
                      "device_info": s["device_info"],
                      "ppg_led_lock": s["ppg_led_lock"]} for s in result["sessions"]],
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
        # Section 13: commands sent; the decode above depends on raw.bin only.
        "commands": ({"inbox": COMMAND_FILES[0], "journal": COMMAND_FILES[1]}
                     if commands else None),
        "inputs_sha256": input_hashes, "outputs_sha256": outputs_sha256,
        "provenance": _provenance(repo),
        "limitations": result["limitations"],
    }
    # The manifest is written last: without it the session is incomplete.
    _write(output, "session_manifest.json",
           (json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False)
            + "\n").encode("utf-8"))
    return manifest


def replay(raw_path, output, config_path, metadata_path, repo, expect=None,
           raw_root=None):
    """Decode an existing raw file into a new directory; never touches the raw.

    Reads session metadata v0 or v1 and a manifest of any logger version (only
    its hashes and ``logger_version``). The output is derived data and never goes
    inside ``raw_root`` (default ``<repo>/data/raw``)."""
    output = Path(output)
    if output.exists():
        raise FileExistsError("Output directory already exists; refusing overwrite")
    raw_root = Path(raw_root) if raw_root is not None else Path(repo) / "data" / "raw"
    if _inside(output, raw_root):
        raise ValueError(f"Replay output is derived data, never inside {raw_root}")
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
    from software.data_io.packet_receiver import study_metadata

    report = {
        "logger_version": result["logger_version"], "mode": "replay",
        "source_type": result["source_type"],
        # Who the decoded signals belong to (withdrawal, cuff log), since the
        # decode outputs carry only the firmware SESSION_ID.
        "session_metadata_version": metadata["schema_version"],
        **study_metadata(metadata),
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


def default_output(repo, command, stamp, subject_id=None, session_id=None):
    """``data/raw/<subject_id>/<session_id>/<stamp>`` for a participant record
    (``--subject-id`` not SYN_*), else ``runs/packet_logger/<stamp>_<command>``.
    ``record`` still checks the ids against the metadata (``check_location``)."""
    if command == "record" and subject_id is not None and (
        not subject_id.startswith("SYN_")
    ):
        return Path(repo) / "data" / "raw" / subject_id / session_id / stamp
    return Path(repo) / "runs" / "packet_logger" / f"{stamp}_{command}"


def main():
    repo = Path(__file__).resolve().parents[1]
    if not __package__:
        sys.path.insert(0, str(repo))
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    for name in ("record", "replay"):
        command = commands.add_parser(name)
        if name == "record":
            source = command.add_mutually_exclusive_group(required=True)
            source.add_argument("--source-file", type=Path,
                                help="Byte stream read as if it came from the device")
            source.add_argument("--port", help="Serial port, e.g. COM5 or /dev/ttyACM0")
            command.add_argument("--duration-s", type=float,
                                 help="Recording length for --port (Ctrl+C stops early)")
            command.add_argument("--baud", type=int, default=115200,
                                 help="Baud rate for --port (ignored by native USB)")
            command.add_argument("--commands", action="store_true",
                                 help="With --port: send commands written to the "
                                      "recording's command_inbox.jsonl "
                                      "(scripts/device_command.py)")
            command.add_argument("--subject-id",
                                 help="Participant code SUB### (or SYN_* for tests); "
                                      "must equal the metadata subject_id")
            command.add_argument("--session-id",
                                 help="Study session code S###; must equal the "
                                      "metadata session_id")
        else:
            command.add_argument("--raw", type=Path, required=True)
            command.add_argument("--expect", type=Path,
                                 help="session_manifest.json to compare hashes with")
        command.add_argument("--metadata", type=Path, required=True,
                             help="Session metadata JSON (schema section 11)")
        command.add_argument("--config", type=Path,
                             default=repo / "configs/hardware/packet_logger.json")
        command.add_argument("--output", type=Path,
                             help="New directory (default runs/packet_logger/"
                                  f"<UTC>_{name}; a participant record: "
                                  "data/raw/<subject_id>/<session_id>/<UTC>)")
    args = parser.parse_args()
    if args.command == "record" and (args.port is None) != (args.duration_s is None):
        parser.error("--port and --duration-s go together")
    if args.command == "record" and args.commands and args.port is None:
        parser.error("--commands needs --port")
    subject = getattr(args, "subject_id", None)
    if args.command == "record" and (subject is None) != (args.session_id is None):
        parser.error("--subject-id and --session-id go together")
    ids = ({"subject_id": subject, "session_id": args.session_id}
           if args.command == "record" else {})
    if args.output is None:
        args.output = default_output(repo, args.command, stamp, **ids)

    def notify(text):
        print(text, file=sys.stderr, flush=True)

    try:
        if args.command == "record" and args.port is not None:
            port = open_serial(args.port, args.baud)
            try:
                source = SerialSource(port, args.duration_s, args.port)
                summary = record(source, args.output, args.config, args.metadata,
                                 repo, args.port, commands=args.commands,
                                 notify=notify, **ids)
            finally:
                port.close()
        elif args.command == "record":
            with args.source_file.open("rb") as source:
                summary = record(source, args.output, args.config, args.metadata,
                                 repo, args.source_file.name, **ids)
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
