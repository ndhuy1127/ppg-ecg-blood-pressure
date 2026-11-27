"""Write the session index of one study session (``session-index-v1``).

Reads the locked ``cuff_log.csv`` of the session and every ingest output of
``scripts/device_session.py`` for it (one per recording and MCU session index),
checks that each cuff of the log comes out of exactly one of them, and writes
``session_index.json`` (a new file; never overwritten). ``run_rq1_analysis.py
--session-indexes`` then refuses feature tables that do not match it (session
app spec section 10.1, point 12, decided 2026-11-27).
"""

import argparse
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from software.device import session_ingest as si  # noqa: E402
from software.device.session_index import build_session_index  # noqa: E402


def run(cuff_log, ingest_dirs, output):
    output = Path(output)
    if output.exists():
        raise ValueError(f"Output {output} exists; choose a new file")
    si.cuff_log_version(cuff_log)  # header check
    with open(cuff_log, newline="", encoding="utf-8") as handle:
        event_ids = [row["event_id"] for row in csv.DictReader(handle)]
    ingests = []
    for directory in map(Path, ingest_dirs):
        table = directory / "cuff_features.csv"
        with open(table, newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        ingests.append({
            "provenance": json.loads((directory / "provenance.json").read_text(
                encoding="utf-8")),
            "rows": rows, "table_sha256": si.sha256_file(table)})
    index = build_session_index(event_ids, si.sha256_file(cuff_log), ingests)
    index["created_utc"] = datetime.now(timezone.utc).isoformat()
    with open(output, "x", encoding="utf-8") as handle:
        json.dump(index, handle, indent=2, sort_keys=True)
        handle.write("\n")
    return index


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--cuff-log", required=True, type=Path)
    parser.add_argument("--ingest", required=True, nargs="+", type=Path,
                        help="Output directories of device_session.py for this session")
    parser.add_argument("--output", required=True, type=Path, help="New session_index.json")
    args = parser.parse_args()
    index = run(args.cuff_log, args.ingest, args.output)
    print(json.dumps({"output": str(args.output), "cuffs": len(index["event_ids"]),
                      "ingests": len(index["ingests"])}, indent=2))


if __name__ == "__main__":
    main()
