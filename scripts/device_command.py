"""Queue a command for the device while ``packet_logger.py record --commands`` runs.

Appends one JSON line to <recording>/command_inbox.jsonl in a single write, then
flushes it to disk; the record loop sends it, retries it and journals the 0xD3
answer in commands_sent.jsonl (Packet Schema V0.2 section 13). "queued" here
only means written to the inbox, never that the device applied it.

    python scripts/device_command.py --recording runs/packet_logger/<dir> ping
    python scripts/device_command.py --recording runs/packet_logger/<dir> \\
        set-ppg-led --green 18 --red 36 --ir 36

LED codes are steps of 0.2 mA, green per sink (LED3 and LED4 both); the firmware
refuses codes above 0x7F (127) with result out_of_range.
"""

import argparse
import json
import os
import sys
from pathlib import Path


def queue_command(recording, entry):
    """Append ``entry`` to the recording's inbox; returns the line written."""
    repo = Path(__file__).resolve().parents[1]
    if str(repo) not in sys.path:
        sys.path.insert(0, str(repo))
    from software.data_io.command_desk import MAX_LINE
    from software.data_io.command_wire import command_from_json

    command_from_json(entry, 0)  # same checks as the record loop
    inbox = Path(recording) / "command_inbox.jsonl"
    if not inbox.is_file():
        raise FileNotFoundError(f"{inbox} not found: is record --commands running?")
    line = (json.dumps(entry, sort_keys=True) + "\n").encode("utf-8")
    if len(line) > MAX_LINE:
        raise ValueError("command line too long")
    fd = os.open(inbox, os.O_WRONLY | os.O_APPEND | getattr(os, "O_BINARY", 0))
    try:
        if os.write(fd, line) != len(line):
            raise OSError("partial write to the inbox")
        os.fsync(fd)
    finally:
        os.close(fd)
    return line.decode("utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--recording", type=Path, required=True,
                        help="Output directory of the running record --commands")
    commands = parser.add_subparsers(dest="cmd", required=True)
    commands.add_parser("ping")
    led = commands.add_parser("set-ppg-led")
    for name in ("green", "red", "ir"):
        led.add_argument(f"--{name}", type=int, required=True,
                         help="code 0..127, 0.2 mA steps" + (" per sink"
                                                              if name == "green" else ""))
    args = parser.parse_args()
    entry = {"cmd": "ping"} if args.cmd == "ping" else {
        "cmd": "set_ppg_led", "green": args.green, "red": args.red, "ir": args.ir}
    try:
        line = queue_command(args.recording, entry)
    except (ValueError, OSError) as exc:
        parser.exit(1, f"Not queued: {exc}\n")
    print(f"queued (not yet sent): {line}", end="")


if __name__ == "__main__":
    main()
