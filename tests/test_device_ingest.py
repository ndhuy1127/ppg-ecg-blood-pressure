"""Ingest of SYNTHETIC device recordings with known answers (device-session-v1)."""

import json
import shutil

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
