"""Queue a command for the device while ``packet_logger.py record --commands`` runs.

Appends one JSON line to <recording>/command_inbox.jsonl in a single write, then
flushes it to disk; the record loop sends it, retries it and journals the 0xD3
answer in commands_sent.jsonl, with PC times (Packet Schema V0.2 section 13).
"queued" here only means written to the inbox, never that the device applied it.

    python scripts/device_command.py --recording runs/packet_logger/<dir> ping
    python scripts/device_command.py --recording runs/packet_logger/<dir> \\
        set-ppg-led --green 18 --red 36 --ir 36
    python scripts/device_command.py --recording runs/packet_logger/<dir> \\
        mark --event cuff_end

LED codes are steps of 0.2 mA, green per sink (LED3 and LED4 both). Codes above
0x7F (127), the study ceiling, are refused here before anything is written;
--allow-over-firmware-limit lets one through only for the bring-up check that
the firmware refuses it too (result out_of_range). Never with a person.

mark sends MARK_EVENT: the device sends an event packet 0xC1 with code 2
(cuff_end) or 4 (operator), timed when the device receives the command, which
is later than this script by an unmeasured PC -> device delay (inbox polling,
USB): good for marks of about a second, not for millisecond marks (t0 stays the
SW1 button).
"""

import argparse
import json
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


def queue_command(recording, entry):
    """Append ``entry`` to the recording's inbox; returns the line written."""
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


def entry_from_args(args):
    """The inbox line (a dict) for parsed command-line arguments."""
    if args.cmd == "ping":
        return {"cmd": "ping"}
    if args.cmd == "mark":
        return {"cmd": "mark_event", "event": args.event}
    entry = {"cmd": "set_ppg_led", "green": args.green, "red": args.red, "ir": args.ir}
    if args.allow_over_firmware_limit:
        entry["allow_over_firmware_limit"] = True
    return entry


def build_parser():
    from software.data_io.command_wire import LED_CODE_MAX, MARK_EVENT_CODES

    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--recording", type=Path, required=True,
                        help="Output directory of the running record --commands")
    commands = parser.add_subparsers(dest="cmd", required=True)
    commands.add_parser("ping")
    led = commands.add_parser("set-ppg-led")
    for name in ("green", "red", "ir"):
        led.add_argument(f"--{name}", type=int, required=True,
                         help=f"code 0..{LED_CODE_MAX}, 0.2 mA steps"
                              + (" per sink" if name == "green" else ""))
    led.add_argument("--allow-over-firmware-limit", action="store_true",
                     help=f"bring-up only, no person: let a code above {LED_CODE_MAX} "
                          "through to check that the firmware refuses it (result 8)")
    mark = commands.add_parser("mark", help="MARK_EVENT: event packet timed when the "
                                            "device receives it")
    mark.add_argument("--event", required=True, choices=sorted(MARK_EVENT_CODES),
                      help="cuff_end (code 2) or operator (code 4)")
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        line = queue_command(args.recording, entry_from_args(args))
    except (ValueError, OSError) as exc:
        parser.exit(1, f"Not queued: {exc}\n")
    print(f"queued (not yet sent): {line}", end="")


if __name__ == "__main__":
    main()
