"""Shared SYNTHETIC device recordings: generator -> logger ``record`` -> directory."""

import csv
import io
import json
from pathlib import Path

from scripts.packet_logger import record
from software.device.session_ingest import CUFF_COLUMNS
from software.device.synthetic_session import generate

ROOT = Path(__file__).resolve().parents[1]
LOGGER_CONFIG = ROOT / "configs/hardware/packet_logger.json"
DEVICE_CONFIG = ROOT / "configs/data/device_session_v1.json"


def make_recording(base, spec, name="rec"):
    """Record ``spec`` through the logger into ``base/name``; returns (dir, truth)."""
    stream, metadata, truth = generate(spec)
    base.mkdir(parents=True, exist_ok=True)
    meta_path = base / f"{name}_metadata.json"
    meta_path.write_text(json.dumps(metadata), encoding="utf-8")
    record(io.BytesIO(stream), base / name, LOGGER_CONFIG, meta_path, ROOT, "synthetic")
    return base / name, truth


def cuff_row(event_id, phase, t0, end=None, mark=None, recording="rec", sbp=120,
             dbp=80, status="valid", safety_stop=0, session=1, led_readjusted=0,
             pilot=0):
    row = dict.fromkeys(CUFF_COLUMNS, "")
    row.update(recording=recording, event_id=event_id, phase=phase,
               device_session_id=session, t0_event_ordinal=t0, status=status,
               safety_stop=safety_stop, led_readjusted=led_readjusted, pilot=pilot)
    if end is not None:
        row["cuff_end_event_ordinal"] = end
    if mark is not None:
        row["phase_mark_event_ordinal"] = mark
    if status == "valid":
        row.update(sbp_mmhg=sbp, dbp_mmhg=dbp)
    return row


def write_cuff_log(path, rows):
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CUFF_COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    return path
