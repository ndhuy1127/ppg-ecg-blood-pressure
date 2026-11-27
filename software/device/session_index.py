"""Session index (``session-index-v1``): what one study session produced.

One file per session of one subject (session app spec section 10.1, point 12,
decided 2026-11-27): the SHA-256 and ``event_id`` list of its locked cuff log,
and every ingest run (recording, MCU session index) with the hash of its feature
table. ``build_session_index`` checks that every cuff of the log comes out of
exactly one ingest run; ``check_session_indexes`` makes the RQ1 analysis refuse
feature tables that miss a cuff, repeat one, or belong to no index. Without it, a
missing table of a repeat would change endpoints 12 and 13 silently.

Pure code: parsed inputs in, dicts out; the scripts read and write the files.
"""

VERSION = "session-index-v1"


class SessionIndexError(ValueError):
    pass


def build_session_index(log_event_ids, log_sha256, ingests):
    """The index of one session.

    ``log_event_ids``: every ``event_id`` of the locked cuff log, all recordings.
    ``ingests``: one dict per ingest output with ``provenance`` (the
    ``provenance.json`` of ``scripts/device_session.py``), ``rows`` (its
    ``cuff_features.csv`` rows) and ``table_sha256`` (hash of that file)."""
    if len(set(log_event_ids)) != len(log_event_ids):
        raise SessionIndexError("Duplicate event_id in the cuff log")
    seen, runs, ids, entries = {}, set(), set(), []
    for item in ingests:
        prov, rows = item["provenance"], item["rows"]
        if prov.get("cuff_log_sha256") != log_sha256:
            raise SessionIndexError(f"{prov.get('recording')}: ingest used another cuff log")
        if prov.get("outputs_sha256", {}).get("cuff_features.csv") != item["table_sha256"]:
            raise SessionIndexError(f"{prov.get('recording')}: cuff_features.csv does not "
                                    "match its provenance")
        name = (prov.get("recording") or "").replace("\\", "/").rstrip("/").split("/")[-1]
        run = (name, prov.get("session_index"))
        if run in runs:
            raise SessionIndexError(f"Ingest run {run} given twice")
        runs.add(run)
        entries.append({"recording": run[0], "session_index": run[1],
                        "table_sha256": item["table_sha256"]})
        for row in rows:
            ids.add((row["subject_id"], row["session_id"], row.get("source_type")))
            if row["event_id"] in seen:
                raise SessionIndexError(f"event_id {row['event_id']} comes out of two "
                                        f"ingest runs: {seen[row['event_id']]} and {run}")
            seen[row["event_id"]] = run
    if len(ids) != 1:
        raise SessionIndexError(f"The tables must be of one subject and session, got "
                                f"{sorted(ids, key=str)}")
    missing = sorted(set(log_event_ids) - set(seen))
    extra = sorted(set(seen) - set(log_event_ids))
    if missing or extra:
        raise SessionIndexError(f"Cuff log and feature tables differ: not ingested "
                                f"{missing}, not in the cuff log {extra}")
    subject, session, source = ids.pop()
    return {"version": VERSION, "subject_id": subject, "session_id": session,
            "source_type": source, "cuff_log_sha256": log_sha256,
            "event_ids": sorted(log_event_ids),
            "ingests": sorted(entries, key=lambda e: (e["recording"], e["session_index"]))}


def check_session_indexes(rows, indexes):
    """RQ1 rows against the session indexes (before the session adjudication,
    on the raw session_id). Every (subject_id, session_id) of a non-SYNTHETIC
    row needs exactly one index, and its rows must carry each indexed
    ``event_id`` exactly once and no other. Returns the number of indexes used."""
    by_key = {}
    for index in indexes:
        if index.get("version") != VERSION:
            raise SessionIndexError(f"Session index version must be {VERSION}")
        key = (index["subject_id"], index["session_id"])
        if key in by_key:
            raise SessionIndexError(f"Two session indexes for {key}")
        by_key[key] = index
    found = {}
    for row in rows:
        key = (row.get("subject_id"), row.get("session_id"))
        if key not in by_key:
            if row.get("source_type") == "SYNTHETIC":
                continue
            raise SessionIndexError(f"No session index for {key}: the feature tables of "
                                    "every session need its session_index.json")
        found.setdefault(key, []).append(row["event_id"])
    for key, index in by_key.items():
        got = found.get(key, [])
        repeated = sorted({e for e in got if got.count(e) > 1})
        missing = sorted(set(index["event_ids"]) - set(got))
        extra = sorted(set(got) - set(index["event_ids"]))
        if repeated or missing or extra:
            raise SessionIndexError(f"Session {key}: feature tables do not match its index "
                                    f"(missing {missing}, extra {extra}, twice {repeated})")
    return len(by_key)
