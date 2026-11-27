"""Shared SYNTHETIC device recordings: generator -> logger ``record`` -> directory."""

import csv
import io
import json
from pathlib import Path

from scripts.packet_logger import record
from software.device.session_ingest import CUFF_COLUMNS, CUFF_COLUMNS_V2
from software.device.synthetic_session import generate

ROOT = Path(__file__).resolve().parents[1]
LOGGER_CONFIG = ROOT / "configs/hardware/packet_logger.json"
DEVICE_CONFIG = ROOT / "configs/data/device_session_v1.json"


def make_recording(base, spec, name="rec", compress=False):
    """Record ``spec`` through the logger into ``base/name``; returns (dir, truth)."""
    stream, metadata, truth = generate(spec)
    base.mkdir(parents=True, exist_ok=True)
    meta_path = base / f"{name}_metadata.json"
    meta_path.write_text(json.dumps(metadata), encoding="utf-8")
    record(io.BytesIO(stream), base / name, LOGGER_CONFIG, meta_path, ROOT, "synthetic",
           compress=compress)
    return base / name, truth


def cuff_row(event_id, phase, t0, end=None, mark=None, recording="rec", sbp=120,
             dbp=80, status="valid", safety_stop=0, session=1, led_readjusted=0,
             pilot=0, repeat_of="", reason=""):
    row = dict.fromkeys(CUFF_COLUMNS_V2, "")
    row.update(repeat_of_event_id=repeat_of, repeat_reason=reason)
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


def write_cuff_log(path, rows, v2=False):
    """A cuff log; v1 (the default) leaves out the two repeat columns of v2."""
    columns = CUFF_COLUMNS_V2 if v2 else CUFF_COLUMNS
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n",
                                extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    return path
