"""Ingest of SYNTHETIC device recordings with known answers (device-session-v1)."""

import json
import shutil
from pathlib import Path

import numpy as np
import pytest

from scripts import device_session
from software.device import session_ingest as si
from software.device.synthetic_session import SessionSpec
from tests.device_fixtures import DEVICE_CONFIG, cuff_row, make_recording, write_cuff_log

EVENTS = ((1, 40.0), (2, 44.0), (4, 46.0), (1, 70.0), (2, 74.0))


@pytest.fixture(scope="module")
def lossy(tmp_path_factory):
    spec = SessionSpec(duration_s=80, events=EVENTS, ppg_clock_ppm=2500,
                       ecg_clock_ppm=-40, drop_packets=(("0xF1", 5), ("0xE1", 100),
                                                        ("0xE1", 101)))
    directory, truth = make_recording(tmp_path_factory.mktemp("lossy"), spec)
    return spec, directory, truth


def test_packet_counts_rates_and_injected_loss(lossy):
    spec, directory, truth = lossy
    recording = si.load_recording(directory)
    series, timebase, flags = si.session_series(recording)
    summary = si.summarize(recording, series, timebase, flags,
                           si.session_events(recording), [])
    ecg_packets = int(spec.duration_s * truth["ecg_fs_true_hz"]) // 16
    ppg_samples = int((spec.duration_s - 0.01) * truth["ppg_fs_true_hz"])
    channels = summary["channels"]
    assert channels["0xE1"]["packets_received"] == ecg_packets - 2
    assert channels["0xE1"]["packets_missing"] == 2
    assert channels["0xF1"]["packets_received"] == ppg_samples // 8 - 1
    assert channels["0xF1"]["packets_missing"] == 1
    assert channels["0xF1"]["samples_lost_counted"] == 8
    assert channels["0xF2"]["packets_missing"] == 0
    assert summary["packets_missing_total"] == 3
    assert channels["0xE1"]["fs_deviation_ppm"] == pytest.approx(-40, abs=5)
    assert channels["0xF1"]["fs_deviation_ppm"] == pytest.approx(2500, abs=5)
    assert summary["duration_s"] == pytest.approx(spec.duration_s, abs=0.1)
    assert summary["events"] == {"cuff_t0": 2, "cuff_end": 2, "sync_pulse": 0,
                                 "operator_mark": 1}
    assert summary["markers"] == 1 and flags == []


def test_sample_times_follow_each_channel_clock(lossy):
    spec, directory, truth = lossy
    series, _, _ = si.session_series(si.load_recording(directory))
    ecg = series["0xE1"]
    true = spec.start_us + ecg.index / truth["ecg_fs_true_hz"] * 1e6
    assert np.max(np.abs(ecg.t_us - true)) < 60  # anchor jitter averaged by the fit
    for j, key in enumerate(("0xF1", "0xF2", "0xF3")):
        ppg = series[key]
        true = (spec.start_us + spec.ppg_start_offset_us
                + ppg.index / truth["ppg_fs_true_hz"] * 1e6 + j * truth["slot_spacing_us"])
        assert ppg.slot_offset_us == j * truth["slot_spacing_us"]
        assert np.max(np.abs(ppg.t_us - true)) < 60
    assert [series[k].name for k in ("0xF1", "0xF2", "0xF3")] == ["green", "red", "ir"]


def test_altered_or_incomplete_recording_is_refused(lossy, tmp_path):
    _, directory, _ = lossy
    for name, change in (("session_metadata.json", b" "), ("samples.csv", b"\n")):
        copy = tmp_path / name
        shutil.copytree(directory, copy)
        with open(copy / name, "ab") as handle:
            handle.write(change)
        with pytest.raises(si.IngestError, match="differs from the manifest"):
            si.load_recording(copy)
    copy = tmp_path / "no_manifest"
    shutil.copytree(directory, copy)
    (copy / "session_manifest.json").unlink()
    with pytest.raises(si.IngestError, match="incomplete"):
        si.load_recording(copy)
    copy = tmp_path / "bad_metadata"
    shutil.copytree(directory, copy)
    manifest = json.loads((copy / "session_manifest.json").read_text())
    manifest["outputs_sha256"]["session_metadata.json"] = "0" * 64
    (copy / "session_manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(si.IngestError):
        si.load_recording(copy)


def test_cuff_windows_and_phase_mark(lossy, tmp_path):
    spec, directory, _ = lossy
    events = si.session_events(si.load_recording(directory))
    log = write_cuff_log(tmp_path / "cuff_log.csv", [
        cuff_row("E01", "M0", 0, 1), cuff_row("E02", "M2", 3, 4, mark=2),
        cuff_row("E03", "M0", 0, recording="other")])
    cuffs = si.read_cuff_log(log, "rec")
    assert [c["event_id"] for c in cuffs] == ["E01", "E02"]
    config = json.loads(DEVICE_CONFIG.read_text())
    windows = si.cuff_windows(cuffs, events, config["window"])
    t0 = spec.start_us + 40e6
    assert windows[0]["t0_us"] == t0
    assert windows[0]["stored_window_us"] == [t0 - 60e6, t0]
    assert windows[0]["analysis_windows_us"]["pre_30s"] == [t0 - 30e6, t0]
    assert windows[0]["inflation_s"] == pytest.approx(4.0)
    # Mark at 46 s, t0 at 70 s: 24 s < 60 s, so the window starts before the mark.
    assert windows[1]["phase_mark_to_t0_s"] == pytest.approx(24.0)
    assert windows[1]["flags"] == ["window_starts_before_phase_mark"]


@pytest.mark.parametrize("row, message", [
    (dict(t0=1), "has code 2, not 1"),
    (dict(t0=9), "no event with ordinal 9"),
    (dict(t0=0, end=0), "has code 1, not 2"),
])
def test_cuff_log_must_point_at_the_right_events(lossy, tmp_path, row, message):
    _, directory, _ = lossy
    events = si.session_events(si.load_recording(directory))
    log = write_cuff_log(tmp_path / "log.csv", [cuff_row("E01", "M0", **row)])
    config = json.loads(DEVICE_CONFIG.read_text())
    with pytest.raises(si.IngestError, match=message):
        si.cuff_windows(si.read_cuff_log(log, "rec"), events, config["window"])


@pytest.mark.parametrize("change, message", [
    (dict(sbp=70, dbp=80), "DBP must be below SBP"),
    (dict(status="lost"), "phase"),
    (dict(event_id="X1"), "event_id"),
    (dict(pilot=""), "pilot must be 0 or 1"),
    (dict(led_readjusted=2), "led_readjusted must be 0 or 1"),
])
def test_cuff_log_is_strict(tmp_path, change, message):
    row = cuff_row(change.pop("event_id", "E01"), "M0", 0,
                   **{k: v for k, v in change.items()})
    log = write_cuff_log(tmp_path / "log.csv", [row])
    with pytest.raises(si.IngestError, match=message):
        si.read_cuff_log(log, "rec")


def test_cuff_log_session_columns_are_constant(tmp_path):
    rows = [cuff_row("E01", "M0", 0), cuff_row("E02", "M0", 1, led_readjusted=1)]
    log = write_cuff_log(tmp_path / "log.csv", rows)
    with pytest.raises(si.IngestError, match="led_readjusted must be the same"):
        si.read_cuff_log(log, "rec")
    rows = [cuff_row("E01", "M0", 0, pilot=1), cuff_row("E02", "M0", 1, pilot=1)]
    cuffs = si.read_cuff_log(write_cuff_log(tmp_path / "ok.csv", rows), "rec")
    assert all(c["pilot"] and not c["led_readjusted"] for c in cuffs)


def _v2(tmp_path, rows, name="log.csv"):
    return write_cuff_log(tmp_path / name, rows, v2=True)


def test_cuff_log_v2_reads_repeat_links(tmp_path):
    # SAP section 2 (decided 2026-11-27): repeats only at M0, each naming the attempt
    # just before it at the same slot; the chain may cross recordings.
    rows = [cuff_row("E01", "M0", 0, status="no_result"),
            cuff_row("E02", "M0", 1, repeat_of="E01", reason="no_result", recording="b"),
            cuff_row("E03", "M0", 2),
            cuff_row("E04", "M0", 3, repeat_of="E03", reason="observed_motion"),
            cuff_row("E05", "M1", 4)]
    log = _v2(tmp_path, rows)
    assert si.cuff_log_version(log) == "cuff-log-v2"
    cuffs = {c["event_id"]: c for c in si.read_cuff_log(log, "rec")}
    assert sorted(cuffs) == ["E01", "E03", "E04", "E05"]  # E02 is in recording b
    assert cuffs["E04"]["repeat_of_event_id"] == "E03"
    assert cuffs["E04"]["repeat_reason"] == "observed_motion"
    assert cuffs["E01"]["repeat_of_event_id"] is None and cuffs["E01"]["repeat_reason"] is None
    # A v1 log carries no link.
    v1 = write_cuff_log(tmp_path / "v1.csv", [cuff_row("E01", "M0", 0)])
    assert si.cuff_log_version(v1) == "cuff-log-v1"
    assert si.read_cuff_log(v1, "rec")[0]["repeat_of_event_id"] is None


@pytest.mark.parametrize("rows, message", [
    # A repeat at M1 (the stressor would be sampled at another time).
    ([cuff_row("E01", "M1", 0, status="no_result"),
      cuff_row("E02", "M1", 1, repeat_of="E01", reason="no_result")], "only at M0"),
    # The repeated attempt must come earlier in the log.
    ([cuff_row("E01", "M0", 0, repeat_of="E02", reason="no_result"),
      cuff_row("E02", "M0", 1, status="no_result")], "not an earlier row"),
    ([cuff_row("E01", "M0", 0, repeat_of="E09", reason="no_result")], "not an earlier row"),
    # no_result names an attempt that had no result.
    ([cuff_row("E01", "M0", 0),
      cuff_row("E02", "M0", 1, repeat_of="E01", reason="no_result")], "has status valid"),
    # A device error stops the session: never repeated.
    ([cuff_row("E01", "M0", 0, status="device_error"),
      cuff_row("E02", "M0", 1, repeat_of="E01", reason="observed_motion")], "may be repeated"),
    # One repeat per attempt: a second one names the first repeat instead.
    ([cuff_row("E01", "M0", 0, status="no_result"),
      cuff_row("E02", "M0", 1, repeat_of="E01", reason="no_result"),
      cuff_row("E03", "M0", 2, repeat_of="E01", reason="no_result")], "already repeated"),
    # At most two repeats per session.
    ([cuff_row("E01", "M0", 0, status="no_result"),
      cuff_row("E02", "M0", 1, repeat_of="E01", reason="no_result", status="no_result"),
      cuff_row("E03", "M0", 2, repeat_of="E02", reason="no_result", status="no_result"),
      cuff_row("E04", "M0", 3, repeat_of="E03", reason="no_result")], "at most 2"),
    ([cuff_row("E01", "M0", 0), cuff_row("E02", "M0", 1, repeat_of="E01")], "both empty"),
    # A repeat whose t0 comes before the t0 it repeats (same recording and session).
    ([cuff_row("E01", "M0", 3, status="no_result"),
      cuff_row("E02", "M0", 1, repeat_of="E01", reason="no_result")], "not after the t0"),
    # A third M0 without a link would be a slot of its own.
    ([cuff_row("E01", "M0", 0), cuff_row("E02", "M0", 1), cuff_row("E03", "M0", 2)],
     "more than 2 scheduled M0"),
    ([cuff_row("E01", "M0", 0),
      cuff_row("E02", "M0", 1, repeat_of="E01", reason="bad_signal")], "repeat_reason"),
])
def test_cuff_log_v2_repeat_links_are_strict(tmp_path, rows, message):
    with pytest.raises(si.IngestError, match=message):
        si.read_cuff_log(_v2(tmp_path, rows), "rec")


def test_cuff_log_header_must_be_v1_or_v2(tmp_path):
    path = tmp_path / "log.csv"
    path.write_text(",".join(si.CUFF_COLUMNS + ("repeat_of_event_id",)) + "\n",
                    encoding="utf-8")
    with pytest.raises(si.IngestError, match="cuff_log columns"):
        si.cuff_log_version(path)


def test_participant_data_need_cuff_log_v2(lossy, tmp_path, monkeypatch):
    _, directory, _ = lossy
    monkeypatch.setattr(device_session, "is_participant", lambda metadata: True)
    v1 = write_cuff_log(tmp_path / "v1.csv", [cuff_row("E01", "M0", 0, 1)])
    with pytest.raises(ValueError, match="need cuff-log-v2"):
        device_session.run(directory, v1, DEVICE_CONFIG, tmp_path / "a")
    assert not (tmp_path / "a").exists()
    v2 = _v2(tmp_path, [cuff_row("E01", "M0", 0, 1)], "v2.csv")
    _, rows = device_session.run(directory, v2, DEVICE_CONFIG, tmp_path / "b")
    assert rows[0]["repeat_of_event_id"] == "" and rows[0]["repeat_reason"] == ""
    prov = json.loads((tmp_path / "b" / "provenance.json").read_text(encoding="utf-8"))
    assert prov["cuff_log_version"] == "cuff-log-v2"


def test_session_index_script_end_to_end(lossy, tmp_path):
    from scripts import build_session_index

    _, directory, _ = lossy
    rows = [cuff_row("E01", "M0", 0, 1), cuff_row("E02", "M0", 0, 1, recording="other")]
    log = _v2(tmp_path, rows)
    device_session.run(directory, log, DEVICE_CONFIG, tmp_path / "ingest")
    # E02 belongs to a recording that was not ingested: no index.
    with pytest.raises(ValueError, match=r"not ingested \['E02'\]"):
        build_session_index.run(log, [tmp_path / "ingest"], tmp_path / "index.json")
    assert not (tmp_path / "index.json").exists()
    log = _v2(tmp_path, rows[:1], "one.csv")
    device_session.run(directory, log, DEVICE_CONFIG, tmp_path / "ingest1")
    index = build_session_index.run(log, [tmp_path / "ingest1"], tmp_path / "index.json")
    assert index["event_ids"] == ["E01"]
    assert index["ingests"] == [{"recording": Path(directory).name, "session_index": 0,
                                 "table_sha256": si.sha256_file(
                                     tmp_path / "ingest1" / "cuff_features.csv")}]
    assert index["cuff_log_sha256"] == si.sha256_file(log)
    with pytest.raises(ValueError, match="exists"):
        build_session_index.run(log, [tmp_path / "ingest1"], tmp_path / "index.json")


def test_script_writes_outputs_and_refuses_overwrite_and_raw(lossy, tmp_path):
    _, directory, _ = lossy
    log = write_cuff_log(tmp_path / "log.csv", [cuff_row("E01", "M0", 0, 1, pilot=1)])
    out = tmp_path / "out"
    summary, rows = device_session.run(directory, log, DEVICE_CONFIG, out)
    # pilot and led_readjusted travel from the cuff log into the RQ1 table.
    with open(out / "cuff_features.csv", encoding="utf-8") as handle:
        header = handle.readline().strip().split(",")
    assert header == list(device_session.FEATURE_COLUMNS)
    assert rows[0]["pilot"] == 1 and rows[0]["led_readjusted"] == 0
    # The recording start travels too, for the RQ1 session-order check.
    manifest = json.loads((Path(directory) / "session_manifest.json").read_text(
        encoding="utf-8"))
    assert rows[0]["session_start_utc"] == manifest["pc_start_time_utc"]
    for name in ("session_summary.json", "timebase.csv", "events.csv", "cuffs.json",
                 "window_samples.csv", "cuff_features.csv", "cuff_features.json",
                 "provenance.json"):
        assert (out / name).is_file()
    assert len(rows) == 1 and rows[0]["source_type"] == "SYNTHETIC"
    # The provenance names the table it describes, for the RQ1 gate.
    prov = json.loads((out / "provenance.json").read_text(encoding="utf-8"))
    assert prov["outputs_sha256"]["cuff_features.csv"] == si.sha256_file(
        out / "cuff_features.csv")
    assert set(device_session.CODE) <= set(prov["code_sha256"])
    with pytest.raises(ValueError, match="exists"):
        device_session.run(directory, log, DEVICE_CONFIG, out)
    with pytest.raises(ValueError, match="data/raw"):
        device_session.run(directory, log, DEVICE_CONFIG, tmp_path / "raw" / "x",
                           raw_root=tmp_path / "raw")


def _ecg_packets(knee_ppm, jitter_us=200, seed=1):
    """30 s of 16-sample ECG packets at 512 sps whose anchors follow one line, then
    from 15 s a rate ``knee_ppm`` faster (a temperature step, say)."""
    rng = np.random.default_rng(seed)
    out = []
    for n in range(960):
        t = (16 * n + 15) * 1e6 / 512
        extra = knee_ppm * 1e-6 * max(0.0, t - 15e6)
        out.append({"disposition": "accepted", "channel_id": "0xE1", "status": 0,
                    "sample_index_ext": 16 * n, "sample_count": 16,
                    "t_anchor_us": int(round(1_000_000 + t + extra
                                             + rng.uniform(0, jitter_us)))})
    return out


def test_timebase_reports_the_a3_statistic():
    # A3: median residual of each 10 s block within +/- 0.2 ms (added 2026-11-15).
    # Anchor jitter alone leaves the block medians near 0; a 120 ppm rate step in
    # the middle leaves about 0.3 ms, which one straight line cannot follow.
    straight = si.fit_timebase(_ecg_packets(0), 512.0)
    knee = si.fit_timebase(_ecg_packets(120), 512.0)
    assert straight["residual_block_max_us"] < 20
    assert knee["residual_block_max_us"] > si.A3_LIMIT_US
    assert si.A3_LIMIT_US == 200.0 and si.A3_BLOCK_US == 10_000_000


def test_a3_last_short_block_joins_the_one_before():
    # One late anchor (+1 ms) just after 30 s would be a block of its own whose
    # median is its own jitter; a last block under 5 s joins the one before.
    packets = _ecg_packets(0)
    t = (16 * 960 + 15) * 1e6 / 512
    packets.append({"disposition": "accepted", "channel_id": "0xE1", "status": 0,
                    "sample_index_ext": 16 * 960, "sample_count": 16,
                    "t_anchor_us": int(round(1_000_000 + t + 1000))})
    assert si.fit_timebase(packets, 512.0)["residual_block_max_us"] < 20
    # Two anchors fit any line exactly: the statistic is not assessable.
    assert si.fit_timebase(packets[:2], 512.0)["residual_block_max_us"] is None


def test_lossy_recording_has_no_a3_flag(lossy):
    _, directory, _ = lossy
    _, timebase, flags = si.session_series(si.load_recording(directory))
    assert not [f for f in flags if f.endswith("timebase_residual_above_a3")]
    assert all(row["residual_block_max_us"] < si.A3_LIMIT_US for row in timebase
               if row.get("residual_block_max_us") is not None)


def test_a3_flag_follows_the_statistic(lossy, monkeypatch):
    _, directory, _ = lossy
    fit = si.fit_timebase

    def above(packets, fs_nominal_hz, model="line"):
        out = fit(packets, fs_nominal_hz, model)
        if out is not None and not out["nominal_rate"]:
            out = {**out, "residual_block_max_us": si.A3_LIMIT_US + 1}
        return out

    monkeypatch.setattr(si, "fit_timebase", above)
    _, _, flags = si.session_series(si.load_recording(directory))
    flagged = {f.split(":")[0] for f in flags if f.endswith(":timebase_residual_above_a3")}
    assert flagged == {"0xE1", "0xF1", "0xF2", "0xF3"}


def test_script_applies_the_ecg_timing_rule_end_to_end(tmp_path):
    # Sync test plan 11.4 through the logger and the entry point: an ECG anchor
    # step of one sample (1.953 ms) at 80 s, generated before encoding, is caught
    # by A10; the cuff whose window holds it gets no PAT, the clean cuff keeps it,
    # and both keep their PPG and ECG features.
    spec = SessionSpec(duration_s=110, events=((1, 45.0), (1, 95.0)),
                       ecg_anchor_steps=((80.0, 1953.0),), ppg_noise_sd=0.0,
                       ecg_noise_sd=0.0)
    directory, _ = make_recording(tmp_path, spec)
    log = write_cuff_log(tmp_path / "log.csv", [cuff_row("E01", "M0", 0),
                                                cuff_row("E02", "M0", 1)])
    _, rows = device_session.run(directory, log, DEVICE_CONFIG, tmp_path / "out")
    clean, stepped = rows
    assert clean["pat_ms"] is not None and "ecg:timing_unverified" not in clean["flags"]
    assert stepped["pat_ms"] is None and stepped["pat_sqi_v2_median_ms"] is None
    assert "ecg:timing_unverified" in stepped["flags"]
    for row in rows:
        assert row["ppg_hr_bpm"] is not None and row["ppg_rise_time_ms"] is not None
        assert row["ecg_hr_bpm"] is not None


def test_cuff_log_v2_short_rows_are_refused(tmp_path):
    log = _v2(tmp_path, [cuff_row("E01", "M0", 0)])
    with open(log, "a", encoding="utf-8") as handle:
        handle.write("rec,E02,M0,1,1\n")
    with pytest.raises(si.IngestError, match="wrong number of fields"):
        si.read_cuff_log(log, "rec")


def test_compressed_tables_give_the_same_recording(tmp_path):
    """Logger --compress-tables (2026-11-27): the four large CSV tables are .gz on
    disk, the manifest hashes their content, and the ingest reads the same data."""
    import gzip

    from software.data_io.output_files import COMPRESSIBLE, content_sha256

    spec = SessionSpec(duration_s=20.0, events=((1, 8.0), (2, 12.0)))
    plain, _ = make_recording(tmp_path / "a", spec)
    packed, _ = make_recording(tmp_path / "b", spec, compress=True)
    m_plain = json.loads((plain / "session_manifest.json").read_text(encoding="utf-8"))
    m_packed = json.loads((packed / "session_manifest.json").read_text(encoding="utf-8"))
    assert m_plain["compressed_outputs"] == {}
    assert m_packed["compressed_outputs"] == {n: n + ".gz" for n in COMPRESSIBLE}
    for name in COMPRESSIBLE:
        assert not (packed / name).exists() and (packed / (name + ".gz")).exists()
        assert content_sha256(packed / (name + ".gz")) == m_packed["outputs_sha256"][name]
    # The decode does not depend on the PC: equal content hashes, equal gz bytes.
    for name in ("decode.json", "packets.csv", "samples.csv"):
        assert m_packed["outputs_sha256"][name] == m_plain["outputs_sha256"][name]
    assert gzip.decompress((packed / "packets.csv.gz").read_bytes()) == (
        plain / "packets.csv").read_bytes()
    again, _ = make_recording(tmp_path / "c", spec, compress=True)
    assert (again / "packets.csv.gz").read_bytes() == (packed / "packets.csv.gz").read_bytes()
    a, b = si.load_recording(plain), si.load_recording(packed)
    assert a["packets"] == b["packets"]
    assert a["samples"].keys() == b["samples"].keys()
    for key in a["samples"]:
        assert all(np.array_equal(x, y) for x, y in zip(a["samples"][key],
                                                        b["samples"][key]))
    # One changed byte inside the compressed table is caught by the content hash.
    text = gzip.decompress((packed / "samples.csv.gz").read_bytes())
    (packed / "samples.csv.gz").unlink()
    (packed / "samples.csv.gz").write_bytes(gzip.compress(text[:-2] + b"9\n"))
    with pytest.raises(si.IngestError, match="SHA-256 of samples.csv"):
        si.load_recording(packed)
