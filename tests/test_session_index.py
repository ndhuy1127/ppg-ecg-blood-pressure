"""Session index (session-index-v1): known answers on SYNTHETIC inputs."""

import pytest

from software.device.session_index import (
    SessionIndexError,
    build_session_index,
    check_session_indexes,
)

LOG_SHA = "a" * 64


def _ingest(recording, index, events, table_sha="b" * 64, log_sha=LOG_SHA,
            subject="SUB001", session="S001"):
    return {"provenance": {"recording": f"data/raw/{subject}/{session}/{recording}",
                           "session_index": index, "cuff_log_sha256": log_sha,
                           "outputs_sha256": {"cuff_features.csv": table_sha}},
            "rows": [{"subject_id": subject, "session_id": session, "event_id": e,
                      "source_type": "DEVICE"} for e in events],
            "table_sha256": table_sha}


def test_index_lists_every_cuff_and_ingest_run():
    # Recording r1 had an MCU restart (two session indexes); r2 is a second recording.
    ingests = [_ingest("r2", 0, ["E04", "E05"]), _ingest("r1", 1, ["E03"]),
               _ingest("r1", 0, ["E01", "E02"])]
    index = build_session_index(["E01", "E02", "E03", "E04", "E05"], LOG_SHA, ingests)
    assert index["subject_id"] == "SUB001" and index["session_id"] == "S001"
    assert index["event_ids"] == ["E01", "E02", "E03", "E04", "E05"]
    assert [(e["recording"], e["session_index"]) for e in index["ingests"]] == [
        ("r1", 0), ("r1", 1), ("r2", 0)]


@pytest.mark.parametrize("log, ingests, message", [
    # The MCU session after the restart was not ingested.
    (["E01", "E02", "E03"], [_ingest("r1", 0, ["E01", "E02"])], r"not ingested \['E03'\]"),
    (["E01"], [_ingest("r1", 0, ["E01", "E02"])], r"not in the cuff log \['E02'\]"),
    (["E01", "E02"], [_ingest("r1", 0, ["E01"]), _ingest("r1", 1, ["E01", "E02"])],
     "two ingest runs"),
    (["E01"], [_ingest("r1", 0, ["E01"], log_sha="c" * 64)], "another cuff log"),
    (["E01"], [{**_ingest("r1", 0, ["E01"]), "table_sha256": "d" * 64}],
     "does not match its provenance"),
    (["E01", "E02"], [_ingest("r1", 0, ["E01"]), _ingest("r1", 0, ["E02"])], "given twice"),
    (["E01", "E02"], [_ingest("r1", 0, ["E01"]),
                      _ingest("r2", 0, ["E02"], subject="SUB002")], "one subject"),
    (["E01", "E01"], [_ingest("r1", 0, ["E01"])], "Duplicate event_id"),
])
def test_index_refuses_incomplete_or_mixed_ingests(log, ingests, message):
    with pytest.raises(SessionIndexError, match=message):
        build_session_index(log, LOG_SHA, ingests)


def _rows(subject, session, events, source="DEVICE"):
    return [{"subject_id": subject, "session_id": session, "event_id": e,
             "source_type": source} for e in events]


INDEX = {"version": "session-index-v1", "subject_id": "SUB001", "session_id": "S001",
         "event_ids": ["E01", "E02", "E03"]}


def test_rq1_rows_must_match_the_index():
    assert check_session_indexes(_rows("SUB001", "S001", ["E01", "E02", "E03"]),
                                 [INDEX]) == 1
    # SYNTHETIC rows need no index.
    assert check_session_indexes(_rows("SYN_00", "S001", ["E01"], "SYNTHETIC"), []) == 0


@pytest.mark.parametrize("rows, indexes, message", [
    # The table of the repeat (E03) was left out: endpoint 12/13 would change silently.
    (_rows("SUB001", "S001", ["E01", "E02"]), [INDEX], r"missing \['E03'\]"),
    (_rows("SUB001", "S001", ["E01", "E02", "E03", "E04"]), [INDEX], r"extra \['E04'\]"),
    (_rows("SUB001", "S001", ["E01", "E02", "E03", "E03"]), [INDEX], r"twice \['E03'\]"),
    (_rows("SUB002", "S001", ["E01"]), [INDEX], "No session index"),
    (_rows("SUB001", "S001", ["E01", "E02", "E03"]), [INDEX, INDEX], "Two session indexes"),
    (_rows("SUB001", "S001", ["E01"]), [{**INDEX, "version": "v0"}], "version"),
])
def test_rq1_rows_that_do_not_match_are_refused(rows, indexes, message):
    with pytest.raises(SessionIndexError, match=message):
        check_session_indexes(rows, indexes)
