"""Session metadata v1 (study ids, locked LED codes) and where record may write.

Decision of 2026-10-29: participant data (subject_id SUB###) lives only in
data/raw/<subject_id>/<session_id>/<recording>/, never in runs/; the firmware
SESSION_ID is device_session_id in the manifest; the locked PPG LED codes are
checked against the MAX30101 states of 0xD2. Answers are derived from
docs/protocol/packet_logger.md and Packet Schema V0.2 section 12. SYNTHETIC only:
the paths live in tmp_path, never in the repository's data/ or runs/.
"""

import copy
import json
import os
import sys
from pathlib import Path

import pytest

from scripts import packet_logger
from scripts.packet_logger import check_location, default_output, record, replay
from scripts.simulate_packets import run as simulate
from software.data_io.packet_receiver import analyze_stream, validate_metadata
from software.data_io.packet_simulation_v3 import session_metadata
from software.data_io.packet_wire import Packet, decode_bytes, encode_packet

ROOT = Path(__file__).resolve().parents[1]
SIM_V01 = ROOT / "configs/hardware/packet_simulation_v3.json"
SIM_V02 = ROOT / "configs/hardware/packet_simulation_v3_v02.json"
LOGGER_CONFIG = ROOT / "configs/hardware/packet_logger.json"
V1 = "packet-session-metadata-v1"
PPG_REGS = (0x08, 0x0A, 0x0C, 0x0D, 0x0E, 0x0F, 0x11, 0x12, 0x02, 0x03, 0x09)
LOCK = {"green": 18, "red": 40, "ir": 44, "outside_dc_range": []}
DEFAULTS = (0x24, 0x24, 0x12, 0x12)  # red, IR, green LED3, green LED4 at boot


def v1(base, source_type=None, **study):
    """``base`` (generator metadata v0) as v1 with the given study fields; null
    fields get a reason."""
    m = copy.deepcopy(base)
    m["schema_version"] = V1
    if source_type == "DEVICE":
        m.update(source_type="DEVICE", simulation=None)
    fields = {"subject_id": None, "session_id": None, "ppg_led_lock": None,
              "cuff_log": None, **study}
    m.update(fields)
    m["null_reasons"].update({name: "test: not set" for name, value in fields.items()
                              if value is None})
    return m


def ppg_only(sim):
    m = copy.deepcopy(session_metadata(sim, "valid", "0" * 64))
    m["channels"] = {"0xF1": m["channels"]["0xF1"]}
    m["null_reasons"] = {n: r for n, r in m["null_reasons"].items()
                         if not n.startswith("channels.") or n.split(".")[1] == "0xF1"}
    return m


@pytest.fixture
def sim():
    return json.loads(SIM_V02.read_bytes())


@pytest.fixture
def logger():
    return json.loads(LOGGER_CONFIG.read_bytes())


# --- metadata v1 ---------------------------------------------------------------------

def test_valid_v1_metadata_and_v0_still_read(sim):
    base = ppg_only(sim)
    assert validate_metadata(base)  # v0, the generator's
    assert validate_metadata(v1(base, "DEVICE", subject_id="SUB001",
                                session_id="S001", ppg_led_lock=LOCK,
                                cuff_log="cuff_log.csv"))
    assert validate_metadata(v1(base, subject_id="SYN_LED", session_id="S002"))
    assert validate_metadata(v1(base, "DEVICE"))  # bring-up: no participant


def _set(name, value):
    return lambda m: m.update({name: value})


def _lock(**change):
    return lambda m: m.update(ppg_led_lock={**LOCK, **change})


@pytest.mark.parametrize("mutate", [
    _set("subject_id", "SUB01"), _set("subject_id", "SUB0001"),
    _set("subject_id", "sub001"), _set("subject_id", "SUB001 "),
    _set("subject_id", "P001"), _set("subject_id", 1),
    _set("subject_id", "SYN_X"),            # SYN_* with DEVICE
    _set("session_id", "S01"), _set("session_id", "S0001"),
    _set("session_id", "s001"), _set("session_id", 1),
    _lock(red=128), _lock(ir=-1), _lock(green=True), _lock(green=18.0),
    _lock(outside_dc_range="green"), _lock(outside_dc_range=["blue"]),
    _lock(outside_dc_range=["red", "red"]), _lock(outside_dc_range=[["red"]]),
    lambda m: m["ppg_led_lock"].pop("ir"),
    _lock(note="x"),
    _set("cuff_log", "/abs/cuff.csv"), _set("cuff_log", "../cuff.csv"),
    _set("cuff_log", "C:/cuff.csv"), _set("cuff_log", "a\\cuff.csv"),
    _set("cuff_log", ""), _set("cuff_log", " cuff.csv"), _set("cuff_log", 3),
    lambda m: m.pop("cuff_log"),
    lambda m: m.update(schema_version="packet-session-metadata-v2"),
    lambda m: m["null_reasons"].update(subject_id="not null"),
])
def test_bad_v1_metadata_is_refused(sim, mutate):
    m = v1(ppg_only(sim), "DEVICE", subject_id="SUB001", session_id="S001",
           ppg_led_lock=copy.deepcopy(LOCK), cuff_log="cuff_log.csv")
    mutate(m)
    with pytest.raises(ValueError):
        validate_metadata(m)


def test_study_field_combinations(sim):
    base = ppg_only(sim)
    for broken in (
        v1(base, subject_id="SUB001", session_id="S001"),   # participant, SYNTHETIC
        v1(base, "DEVICE", subject_id="SUB001"),             # no session
        v1(base, "DEVICE", session_id="S001"),               # session, no subject
        v1(base, "DEVICE", cuff_log="cuff_log.csv"),         # cuff log, no session
        {**v1(base), "null_reasons": {k: v for k, v in v1(base)["null_reasons"].items()
                                      if k != "subject_id"}},
    ):
        with pytest.raises(ValueError):
            validate_metadata(broken)
    # A lock needs a PPG channel.
    ecg = copy.deepcopy(session_metadata(sim, "valid", "0" * 64))
    ecg["channels"] = {"0xE1": ecg["channels"]["0xE1"]}
    ecg["null_reasons"] = {n: r for n, r in ecg["null_reasons"].items()
                           if not n.startswith("channels.") or ".0xE1." in n}
    assert validate_metadata(v1(ecg))
    with pytest.raises(ValueError):
        validate_metadata(v1(ecg, ppg_led_lock=LOCK))
    # v0 never carries study fields.
    with pytest.raises(ValueError):
        validate_metadata({**base, "subject_id": None})


# --- locked LED codes against 0xD2 -----------------------------------------------------

def ppg(seq, session=1, version=2):
    anchor = 1_000_000 + (4 * seq + 3) * 10_000
    return Packet(version, 0xF1, session, seq, 4 * seq, anchor, anchor - 30_000,
                  100000, 16, (7,) * 4)


def led_state(seq, gen, codes, session=1):
    """A configured MAX30101 0xD2 (ordinal = seq) with LED1..LED4_PA = codes."""
    values = dict(zip((0x0C, 0x0D, 0x0E, 0x0F), codes))
    regs = tuple((a << 24) | values.get(a, 0x24) for a in PPG_REGS)
    t = 1_000_000 + 10_000 * seq
    return Packet(2, 0xD2, session, seq, seq, t, t, 0, 0, (1, 2, 1, 1, gen, *regs))


LOCKED = (LOCK["red"], LOCK["ir"], LOCK["green"], LOCK["green"])


def analyze(packets, logger, meta):
    stream = b"".join(encode_packet(p) for p in packets)
    decoded, decoder = decode_bytes(stream, 4096, (1, 2))
    return analyze_stream(decoded, decoder, logger, meta)


def lock_issues(result):
    return [i for i in result["issues"] if i["code"].startswith("ppg_led_lock")]


def test_locked_codes_after_boot_defaults_are_clean(sim, logger):
    meta = v1(ppg_only(sim), subject_id="SYN_LED", session_id="S002",
              ppg_led_lock=LOCK)
    result, _, _ = analyze([ppg(0), led_state(0, 1, DEFAULTS),
                            led_state(1, 2, LOCKED), led_state(2, 2, LOCKED)],
                           logger, meta)
    assert result["issue_counts"] == {}
    assert result["sessions"][0]["ppg_led_lock"] == {
        "applied": {"seq": 1, "t_anchor_us": 1_010_000, "generation": 2}}


def test_codes_never_locked_are_not_applied(sim, logger):
    meta = v1(ppg_only(sim), subject_id="SYN_LED", session_id="S002",
              ppg_led_lock=LOCK)
    typo = (LOCK["red"], LOCK["ir"] + 1, LOCK["green"], LOCK["green"])
    result, _, _ = analyze([ppg(0), led_state(0, 1, DEFAULTS), led_state(1, 2, typo)],
                           logger, meta)
    assert result["issue_counts"] == {"ppg_led_lock_not_applied": 1}
    (issue,) = lock_issues(result)
    assert issue["after_session_change"] is False and issue["session_id"] == 1
    assert issue["last_led_codes"] == {"red": 40, "ir": 45, "green_led3": 18,
                                       "green_led4": 18}
    assert result["sessions"][0]["ppg_led_lock"] == {"applied": None}
    # Both green sinks carry the green code; one of them off is not the lock.
    half = (LOCK["red"], LOCK["ir"], LOCK["green"], 0)
    result, _, _ = analyze([ppg(0), led_state(0, 1, half)], logger, meta)
    assert result["issue_counts"] == {"ppg_led_lock_not_applied": 1}


def test_codes_changed_after_the_lock_are_a_mismatch(sim, logger):
    meta = v1(ppg_only(sim), subject_id="SYN_LED", session_id="S002",
              ppg_led_lock=LOCK)
    other = (0x30, 0x30, 0x10, 0x10)
    result, _, _ = analyze([ppg(0), led_state(0, 1, DEFAULTS), led_state(1, 2, LOCKED),
                            led_state(2, 3, other), led_state(3, 4, LOCKED)],
                           logger, meta)
    assert result["issue_counts"] == {"ppg_led_lock_mismatch": 1}
    (issue,) = lock_issues(result)
    assert (issue["seq"], issue["generation"]) == (2, 3)
    assert issue["led_codes"]["red"] == 0x30
    assert result["sessions"][0]["ppg_led_lock"]["applied"]["seq"] == 1


def test_session_change_needs_the_locked_codes_again(sim, logger):
    meta = v1(ppg_only(sim), subject_id="SYN_LED", session_id="S002",
              ppg_led_lock=LOCK)
    first = [ppg(0), led_state(0, 1, DEFAULTS), led_state(1, 2, LOCKED)]
    # The MCU restarts: a new SESSION_ID boots with the default codes.
    restarted = [ppg(0, session=2), led_state(0, 1, DEFAULTS, session=2)]
    result, _, _ = analyze(first + restarted, logger, meta)
    assert result["issue_counts"] == {"ppg_led_lock_not_applied": 1,
                                      "session_change": 1}
    (issue,) = lock_issues(result)
    assert issue["session_id"] == 2 and issue["after_session_change"] is True
    assert issue["last_led_codes"]["red"] == DEFAULTS[0]
    # Sent again after the restart: clean.
    result, _, _ = analyze(first + restarted + [led_state(1, 2, LOCKED, session=2)],
                           logger, meta)
    assert result["issue_counts"] == {"session_change": 1}


def test_no_lock_no_check_and_v01_cannot_apply_it(sim, logger):
    base = ppg_only(sim)
    other = (0x30, 0x30, 0x10, 0x10)
    packets = [ppg(0), led_state(0, 1, LOCKED), led_state(1, 2, other)]
    for meta in (base, v1(base, subject_id="SYN_LED", session_id="S002")):
        result, _, _ = analyze(packets, logger, meta)
        assert result["issue_counts"] == {}
        assert result["sessions"][0]["ppg_led_lock"] is None
    # V0.1 firmware has no 0xD2 and cannot set LED codes.
    meta = v1(base, subject_id="SYN_LED", session_id="S002", ppg_led_lock=LOCK)
    result, _, _ = analyze([ppg(0, version=1)], logger, meta)
    assert result["issue_counts"] == {"ppg_led_lock_not_applied": 1}


# --- where record and replay may write -----------------------------------------------

def _stream(tmp_path, case="valid"):
    generated = tmp_path / f"generated_{case}"
    simulate(SIM_V01, case, generated)
    return generated / "stream.bin", json.loads(
        (generated / "session_metadata.json").read_bytes())


def _write_meta(tmp_path, meta, name="meta.json"):
    path = tmp_path / name
    path.write_text(json.dumps(meta), encoding="utf-8")
    return path


def _participant(base, **study):
    return v1(base, "DEVICE", **{"subject_id": "SUB001", "session_id": "S001",
                                 "cuff_log": "cuff_log.csv", **study})


def test_participant_record_goes_to_data_raw_only(tmp_path):
    stream, base = _stream(tmp_path)
    meta = _write_meta(tmp_path, _participant(base))
    raw_root = tmp_path / "data" / "raw"
    output = raw_root / "SUB001" / "S001" / "20261105T090000000000Z"
    with stream.open("rb") as source:
        manifest = record(source, output, LOGGER_CONFIG, meta, ROOT, "stream.bin",
                          subject_id="SUB001", session_id="S001", raw_root=raw_root)
    assert (output / "raw.bin").read_bytes() == stream.read_bytes()
    assert (output / "session_manifest.json").exists()
    assert manifest["session_metadata_version"] == V1
    assert (manifest["subject_id"], manifest["session_id"]) == ("SUB001", "S001")
    assert manifest["cuff_log"] == "cuff_log.csv" and manifest["ppg_led_lock"] is None
    assert manifest["device_session_id"] == 1
    assert manifest["sessions"][0]["device_session_id"] == 1
    assert manifest["sessions"][0]["ppg_led_lock"] is None
    # A replay elsewhere says whose signals it decoded.
    report = replay(output / "raw.bin", tmp_path / "runs" / "replay", LOGGER_CONFIG,
                    meta, ROOT, output / "session_manifest.json", raw_root=raw_root)
    assert (report["subject_id"], report["session_id"]) == ("SUB001", "S001")
    assert report["session_metadata_version"] == V1
    assert report["expected_manifest"]["mismatches"] == []


def _link_dir(link, target):
    """A directory symlink, or a junction on Windows without the symlink right."""
    target.mkdir(parents=True, exist_ok=True)
    link.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.symlink(target, link, target_is_directory=True)
        return
    except (OSError, NotImplementedError):
        pass
    if sys.platform != "win32":
        pytest.skip("cannot create a directory link here")
    import _winapi

    _winapi.CreateJunction(str(target), str(link))


def test_a_linked_session_directory_cannot_move_raw_out(tmp_path):
    stream, base = _stream(tmp_path)
    raw_root = tmp_path / "data" / "raw"
    outside = tmp_path / "outside" / "S001"
    _link_dir(raw_root / "SUB001" / "S001", outside)
    participant = _write_meta(tmp_path, _participant(base))
    with stream.open("rb") as source, pytest.raises(ValueError, match="goes only to"):
        record(source, raw_root / "SUB001" / "S001" / "rec", LOGGER_CONFIG,
               participant, tmp_path, "stream.bin", subject_id="SUB001",
               session_id="S001", raw_root=raw_root)
    # Bring-up written through the same link is still inside data/raw as written.
    bring_up = _write_meta(tmp_path, v1(base, "DEVICE"), "bring_up.json")
    with stream.open("rb") as source, pytest.raises(
        ValueError, match="participant recordings only"
    ):
        record(source, raw_root / "SUB001" / "S001" / "rec2", LOGGER_CONFIG, bring_up,
               tmp_path, "stream.bin", raw_root=raw_root)
    assert list(outside.iterdir()) == []


def test_data_raw_itself_may_be_a_link(tmp_path):
    # data/raw on another (encrypted) drive, reached through a link: allowed.
    stream, base = _stream(tmp_path)
    raw_root, vault = tmp_path / "data" / "raw", tmp_path / "vault"
    _link_dir(raw_root, vault)
    meta = _write_meta(tmp_path, _participant(base))
    with stream.open("rb") as source:
        record(source, raw_root / "SUB001" / "S001" / "rec", LOGGER_CONFIG, meta, ROOT,
               "stream.bin", subject_id="SUB001", session_id="S001",
               raw_root=raw_root)
    assert (vault / "SUB001" / "S001" / "rec" / "raw.bin").read_bytes() == (
        stream.read_bytes())


@pytest.mark.parametrize("where", [
    "runs/packet_logger/x",              # runs/ of the repository
    "data/raw/SUB002/S001/x",            # another subject
    "data/raw/SUB001/S002/x",            # another session
    "data/raw/SUB001/S001",              # the session directory itself
    "data/raw/SUB001/S001/a/b",          # nested
    "data/raw/SUB001/S001/_x",           # not a plain recording name
    "elsewhere/x",
])
def test_participant_record_refuses_any_other_place(tmp_path, where):
    stream, base = _stream(tmp_path)
    meta = _write_meta(tmp_path, _participant(base))
    output = tmp_path / where
    # The same metadata records fine into its own directory
    # (test_participant_record_goes_to_data_raw_only): the refusal is the place.
    expected = "never written to runs/" if where.startswith("runs/") else "goes only to"
    with stream.open("rb") as source, pytest.raises(ValueError, match=expected):
        # repo = tmp_path, so its runs/ is tmp_path/runs; the refusal comes before
        # anything is created.
        record(source, output, LOGGER_CONFIG, meta, tmp_path, "stream.bin",
               subject_id="SUB001", session_id="S001")
    assert not output.exists()


@pytest.mark.parametrize("typed", [(None, None), ("SUB002", "S001"),
                                   ("SUB001", "S002"), ("SYN_A", "S001")])
def test_typed_ids_must_equal_the_participant_metadata(tmp_path, typed):
    stream, base = _stream(tmp_path)
    meta = _write_meta(tmp_path, _participant(base))
    output = tmp_path / "data" / "raw" / "SUB001" / "S001" / "rec"
    with stream.open("rb") as source, pytest.raises(ValueError, match="--subject-id"):
        record(source, output, LOGGER_CONFIG, meta, tmp_path, "stream.bin",
               subject_id=typed[0], session_id=typed[1])
    assert not output.exists()


def test_non_participant_data_stays_out_of_data_raw(tmp_path):
    stream, base = _stream(tmp_path)
    raw_root = tmp_path / "data" / "raw"
    for k, (meta, typed) in enumerate((
        (base, {}),                                              # v0 SYNTHETIC
        (v1(base, subject_id="SYN_A", session_id="S001"),
         {"subject_id": "SYN_A", "session_id": "S001"}),
        (v1(base, "DEVICE"), {}),                                # bring-up
    )):
        path = _write_meta(tmp_path, meta, f"meta{k}.json")
        output = raw_root / "SUB001" / "S001" / f"rec{k}"
        with stream.open("rb") as source, pytest.raises(
            ValueError, match="participant recordings only"
        ):
            record(source, output, LOGGER_CONFIG, path, tmp_path, "stream.bin",
                   raw_root=raw_root, **typed)
        assert not output.exists()
        # Anywhere else is fine, as before.
        with stream.open("rb") as source:
            record(source, tmp_path / "runs" / f"rec{k}", LOGGER_CONFIG, path, ROOT,
                   "stream.bin", raw_root=raw_root, **typed)


def test_device_recordings_need_metadata_v1(tmp_path):
    stream, base = _stream(tmp_path)
    old = {**copy.deepcopy(base), "source_type": "DEVICE", "simulation": None}
    meta = _write_meta(tmp_path, old)
    with stream.open("rb") as source, pytest.raises(ValueError, match="v1"):
        record(source, tmp_path / "rec", LOGGER_CONFIG, meta, ROOT, "stream.bin")
    assert not (tmp_path / "rec").exists()


def test_check_location_names_runs_for_participants(tmp_path):
    _, base = _stream(tmp_path)
    meta = _participant(base)
    with pytest.raises(ValueError, match="never written to runs/"):
        check_location(tmp_path / "runs" / "packet_logger" / "x", meta, tmp_path,
                       subject_id="SUB001", session_id="S001")
    check_location(tmp_path / "data" / "raw" / "SUB001" / "S001" / "x", meta,
                   tmp_path, subject_id="SUB001", session_id="S001")


def test_default_output_follows_the_typed_subject(tmp_path):
    stamp = "20261105T090000000000Z"
    assert default_output(tmp_path, "record", stamp, "SUB001", "S001") == (
        tmp_path / "data" / "raw" / "SUB001" / "S001" / stamp)
    for args in ((), ("SYN_A", "S001"), (None, None)):
        assert default_output(tmp_path, "record", stamp, *args) == (
            tmp_path / "runs" / "packet_logger" / f"{stamp}_record")
    assert default_output(tmp_path, "replay", stamp) == (
        tmp_path / "runs" / "packet_logger" / f"{stamp}_replay")


def test_cli_pairs_subject_with_session(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["packet_logger.py", "record", "--source-file",
                                      "x.bin", "--metadata", "m.json",
                                      "--subject-id", "SUB001"])
    with pytest.raises(SystemExit) as stopped:
        packet_logger.main()
    assert stopped.value.code == 2


# --- live reminder ----------------------------------------------------------------------

class ByteSource:
    """A writable byte source with no device behind it (record --commands)."""

    def __init__(self, payload):
        self.payload, self.written = payload, []

    def read(self, n):
        chunk, self.payload = self.payload[:n], self.payload[n:]
        return chunk

    def write(self, data):
        self.written.append(data)
        return len(data)


def test_record_reminds_to_send_the_locked_codes_at_each_session(tmp_path):
    stream, base = _stream(tmp_path, "session_restart")
    meta = _write_meta(tmp_path, v1(base, subject_id="SYN_LED", session_id="S002",
                                    ppg_led_lock=LOCK))
    notes = []
    manifest = record(ByteSource(stream.read_bytes()), tmp_path / "rec", LOGGER_CONFIG,
                      meta, ROOT, "fake", commands=True, notify=notes.append)
    assert notes[0].startswith("Recording to ")
    assert [n.split(":")[0] for n in notes[1:]] == ["SESSION_ID 1", "SESSION_ID 2"]
    assert "--green 18 --red 40 --ir 44" in notes[1]
    # V0.1 generator streams have no 0xD2, so neither session has the lock.
    decode = json.loads((tmp_path / "rec" / "decode.json").read_bytes())
    flags = [(i["session_id"], i["after_session_change"]) for i in decode["issues"]
             if i["code"] == "ppg_led_lock_not_applied"]
    assert flags == [(1, False), (2, True)]
    assert manifest["device_session_ids"] == [1, 2]


# --- reading older outputs -----------------------------------------------------------

def test_replay_reads_v0_metadata_and_a_v2_manifest(tmp_path):
    stream, base = _stream(tmp_path, "session_restart")
    meta = _write_meta(tmp_path, base)
    with stream.open("rb") as source:
        manifest = record(source, tmp_path / "rec", LOGGER_CONFIG, meta, ROOT,
                          "stream.bin")
    # A packet-logger-v2 manifest: SESSION_ID under session_id(s), no study fields.
    old = {k: v for k, v in manifest.items()
           if k not in ("device_session_id", "device_session_ids", "subject_id",
                        "ppg_led_lock", "cuff_log", "session_metadata_version")}
    old.update(logger_version="packet-logger-v2", session_id=None, session_ids=[1, 2],
               sessions=[{**{k: v for k, v in s.items()
                             if k not in ("device_session_id", "ppg_led_lock")},
                          "session_id": s["device_session_id"]}
                         for s in manifest["sessions"]])
    expect = _write_meta(tmp_path, old, "old_manifest.json")
    result = replay(tmp_path / "rec" / "raw.bin", tmp_path / "replay", LOGGER_CONFIG,
                    meta, ROOT, expect)
    assert result["expected_manifest"]["mismatches"] == ["logger_version"]
    # Old DEVICE metadata v0 is still read by replay (record refuses it).
    device = _write_meta(tmp_path, {**copy.deepcopy(base), "source_type": "DEVICE",
                                    "simulation": None}, "device_v0.json")
    result = replay(tmp_path / "rec" / "raw.bin", tmp_path / "replay_device",
                    LOGGER_CONFIG, device, ROOT)
    assert result["source_type"] == "DEVICE"


def test_replay_never_writes_into_data_raw(tmp_path):
    stream, base = _stream(tmp_path)
    meta = _write_meta(tmp_path, base)
    with stream.open("rb") as source:
        record(source, tmp_path / "rec", LOGGER_CONFIG, meta, ROOT, "stream.bin")
    raw_root = tmp_path / "data" / "raw"
    output = raw_root / "SUB001" / "S001" / "replay"
    with pytest.raises(ValueError, match="derived"):
        replay(tmp_path / "rec" / "raw.bin", output, LOGGER_CONFIG, meta, ROOT,
               raw_root=raw_root)
    assert not output.exists()


def test_a_v02_device_session_with_the_lock_in_the_manifest(tmp_path, sim):
    # ppg(0) and a locked 0xD2 in one DEVICE session of a participant.
    meta = _participant(ppg_only(sim), ppg_led_lock=LOCK)
    path = _write_meta(tmp_path, meta)
    payload = b"".join(encode_packet(p) for p in (
        ppg(0), led_state(0, 1, DEFAULTS), led_state(1, 2, LOCKED), ppg(1)))
    raw_root = tmp_path / "data" / "raw"
    output = raw_root / "SUB001" / "S001" / "rec"
    manifest = record(ByteSource(payload), output, LOGGER_CONFIG, path, ROOT, "fake",
                      subject_id="SUB001", session_id="S001", raw_root=raw_root)
    assert manifest["ppg_led_lock"] == LOCK
    assert manifest["sessions"][0]["ppg_led_lock"]["applied"]["generation"] == 2
    assert not {"ppg_led_lock_not_applied", "ppg_led_lock_mismatch"} & set(
        manifest["issue_counts"])
