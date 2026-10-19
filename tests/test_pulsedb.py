import math

import numpy as np
import pytest

from software.pulsedb.reader import PulseDBReader, PulseSegment
from software.pulsedb.validator import PulseValidator


def make_subset(n=2, **overrides):
    """Subset giả lập theo đúng tên trường của PulseDB; dữ liệu SYNTHETIC."""
    signals = np.zeros((n, 3, 1250))
    signals[:, 0, :] = 1.0  # ECG
    signals[:, 1, :] = 2.0  # PPG
    signals[:, 2, :] = 3.0  # ABP
    subset = {
        "Signals": signals,
        "SBP": np.array([120.0, 121.0, 122.0][:n]),
        "DBP": np.array([80.0, 81.0, 82.0][:n]),
        "Subject": np.array(["SYN_001", "SYN_002", "SYN_003"][:n]),
        "Age": np.array([25.0, 26.0, 27.0][:n]),
        "Gender": np.array(["M", "F", "M"][:n]),
        "Height": np.array([175.0, 165.0, 170.0][:n]),
        "Weight": np.array([70.0, 60.0, 65.0][:n]),
        "BMI": np.array([22.9, 22.0, 22.5][:n]),
    }
    subset.update(overrides)
    return subset


def read_subset(tmp_path, monkeypatch, subset, limit=None):
    file_path = tmp_path / "subset.mat"
    file_path.touch()
    monkeypatch.setattr(
        "software.pulsedb.reader.mat73.loadmat",
        lambda _: {"Subset": subset},
    )
    return PulseDBReader(str(file_path)).read(limit=limit)


def make_segment(subject="SYN_001", sbp=120.0, dbp=80.0, value=0.0):
    wave = np.full(1250, value)
    return PulseSegment(
        subject, "M", 30.0, np.nan, np.nan, np.nan, sbp, dbp,
        wave.copy(), wave.copy(), wave.copy(),
    )


def test_missing_file():
    with pytest.raises(FileNotFoundError):
        PulseDBReader("not_exist.mat")


def test_reader_rejects_wrong_channel_count(tmp_path, monkeypatch):
    subset = make_subset(Signals=np.zeros((2, 4, 1250)))
    with pytest.raises(ValueError, match="đúng 3 kênh"):
        read_subset(tmp_path, monkeypatch, subset, limit=1)


def test_reader_accepts_gender_m_f(tmp_path, monkeypatch):
    segments = read_subset(tmp_path, monkeypatch, make_subset(), limit=2)
    assert [segment.gender for segment in segments] == ["M", "F"]


def test_reader_maps_channels_in_documented_order(tmp_path, monkeypatch):
    segment = read_subset(tmp_path, monkeypatch, make_subset())[0]
    assert (segment.ecg == 1.0).all()
    assert (segment.ppg == 2.0).all()
    assert (segment.abp == 3.0).all()


def test_reader_keeps_rows_in_file_order(tmp_path, monkeypatch):
    segments = read_subset(tmp_path, monkeypatch, make_subset(n=3))
    assert [s.subject_id for s in segments] == ["SYN_001", "SYN_002", "SYN_003"]
    assert [s.sbp for s in segments] == [120.0, 121.0, 122.0]


def test_missing_optional_demographics_are_nan_not_zero(tmp_path, monkeypatch):
    subset = make_subset()
    for key in ("Height", "Weight", "BMI"):
        del subset[key]
    segment = read_subset(tmp_path, monkeypatch, subset)[0]
    assert math.isnan(segment.height_cm)
    assert math.isnan(segment.weight_kg)
    assert math.isnan(segment.bmi_kg_m2)


@pytest.mark.parametrize("field", ["SBP", "DBP", "Subject", "Age", "Gender"])
def test_required_field_none_raises(tmp_path, monkeypatch, field):
    subset = make_subset()
    subset[field] = None
    with pytest.raises(ValueError, match=f"bắt buộc {field}"):
        read_subset(tmp_path, monkeypatch, subset)


def test_optional_field_none_is_nan(tmp_path, monkeypatch):
    subset = make_subset(Height=None)
    segment = read_subset(tmp_path, monkeypatch, subset)[0]
    assert math.isnan(segment.height_cm)
    assert segment.weight_kg == 70.0


def test_missing_required_key_raises(tmp_path, monkeypatch):
    subset = make_subset()
    del subset["SBP"]
    with pytest.raises(KeyError, match="SBP"):
        read_subset(tmp_path, monkeypatch, subset)


@pytest.mark.parametrize("field", ["SBP", "DBP", "Subject", "Age", "Gender", "BMI"])
@pytest.mark.parametrize("length", [1, 3])
def test_field_length_must_match_segment_count(tmp_path, monkeypatch, field, length):
    subset = make_subset(n=2)
    subset[field] = make_subset(n=3)[field][:length]
    with pytest.raises(ValueError, match="khác số đoạn"):
        read_subset(tmp_path, monkeypatch, subset)


def test_single_segment_file_with_scalar_fields(tmp_path, monkeypatch):
    subset = make_subset(n=1, SBP=np.float64(118.0), DBP=np.float64(76.0))
    segments = read_subset(tmp_path, monkeypatch, subset)
    assert len(segments) == 1
    assert (segments[0].sbp, segments[0].dbp) == (118.0, 76.0)


def test_unrecognized_gender_code_raises(tmp_path, monkeypatch):
    subset = make_subset(Gender=np.array([1.0, 0.0]))
    with pytest.raises(ValueError, match="Gender"):
        read_subset(tmp_path, monkeypatch, subset)


def test_missing_gender_is_unknown(tmp_path, monkeypatch):
    subset = make_subset(Gender=np.array([np.nan, np.nan]))
    segments = read_subset(tmp_path, monkeypatch, subset)
    assert [s.gender for s in segments] == ["Unknown", "Unknown"]


@pytest.mark.parametrize("limit", [-1, 1.5, True])
def test_invalid_limit_raises(tmp_path, monkeypatch, limit):
    with pytest.raises(ValueError, match="limit"):
        read_subset(tmp_path, monkeypatch, make_subset(), limit=limit)


def test_limit_zero_returns_empty(tmp_path, monkeypatch):
    assert read_subset(tmp_path, monkeypatch, make_subset(), limit=0) == []


def test_validator_flags_identical_waveform_with_different_labels():
    segments = [
        make_segment("SYN_001", 120.0, 80.0, value=0.5),
        make_segment("SYN_002", 130.0, 85.0, value=0.5),
    ]
    stats = PulseValidator(segments).validate_and_summarize()
    assert stats["waveform_duplicate_of"].isna().iloc[0]
    assert stats["waveform_duplicate_of"].iloc[1] == 0
    assert len(stats) == 2  # Gắn cờ, không xóa dòng.


def test_validator_does_not_flag_same_labels_with_different_waveforms():
    segments = [
        make_segment("SYN_001", 120.0, 80.0, value=0.5),
        make_segment("SYN_001", 120.0, 80.0, value=0.6),
    ]
    stats = PulseValidator(segments).validate_and_summarize()
    assert stats["waveform_duplicate_of"].isna().all()


def test_validator_flags_label_problems_without_dropping():
    segments = [
        make_segment("SYN_001", 265.0, 258.0),
        make_segment("SYN_002", 80.0, 90.0),
        make_segment("SYN_003", np.nan, 80.0),
        make_segment("nan", 120.0, 80.0),
    ]
    stats = PulseValidator(segments).validate_and_summarize()
    assert stats["pulse_pressure"].iloc[0] == pytest.approx(7.0)
    assert stats["dbp_ge_sbp"].tolist() == [False, True, False, False]
    assert stats["label_nonfinite"].tolist() == [False, False, True, False]
    assert stats["subject_missing"].tolist() == [False, False, False, True]
    assert stats["meta_has_nan"].tolist() == [False, False, True, True]
    assert len(stats) == len(segments)


def test_validator_flags_missing_age_per_row():
    segments = [make_segment("SYN_001"), make_segment("SYN_002")]
    segments[1].age = np.nan
    stats = PulseValidator(segments).validate_and_summarize()
    assert stats["age_missing"].tolist() == [False, True]
    assert len(stats) == 2


def test_validator_flags_channel_length_mismatch():
    segment = make_segment()
    segment.ppg = np.zeros(1000)
    stats = PulseValidator([segment]).validate_and_summarize()
    assert bool(stats["length_mismatch"].iloc[0])


def test_reader_accepts_mat73_cell_arrays_as_lists(tmp_path, monkeypatch):
    # mat73 returns MATLAB cell arrays (Subject, Gender in PulseDB) as lists.
    subset = make_subset(Subject=["SYN_001", "SYN_002"], Gender=["M", "F"])
    segments = read_subset(tmp_path, monkeypatch, subset)
    assert [s.subject_id for s in segments] == ["SYN_001", "SYN_002"]
    assert [s.gender for s in segments] == ["M", "F"]


def test_reader_rejects_multi_value_subject(tmp_path, monkeypatch):
    subset = make_subset(Subject=[["SYN_001", "SYN_009"], "SYN_002"])
    with pytest.raises(ValueError, match="Subject"):
        read_subset(tmp_path, monkeypatch, subset)


def test_validator_and_split_share_missing_subject_tokens():
    from software.data_io.split_manifest import build_inventory

    segment = make_segment("NULL")
    assert PulseValidator([segment]).validate_and_summarize()["subject_missing"].iloc[0]
    with pytest.raises(ValueError, match="subject_id"):
        build_inventory([segment], "SYNTHETIC", "c" * 64)
