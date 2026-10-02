import numpy as np
import pytest

from software.pulsedb.reader import PulseDBReader


def test_missing_file():
    with pytest.raises(FileNotFoundError):
        PulseDBReader("not_exist.mat")


def test_duplicate_metadata():
    subject_ids = np.array(["p001", "p001", "p002"])
    segment_ids = np.array([0, 0, 1])

    keys = list(zip(subject_ids, segment_ids))

    assert len(keys) != len(set(keys))


def test_reader_rejects_wrong_channel_count(tmp_path, monkeypatch):
    file_path = tmp_path / "wrong_channels.mat"
    file_path.touch()

    fake_data = {
        "Subset": {
            "Signals": np.zeros((2, 4, 1250)),
            "SBP": np.array([120.0, 121.0]),
            "DBP": np.array([80.0, 81.0]),
            "Subject": np.array(["p001", "p002"]),
            "Age": np.array([25.0, 26.0]),
            "Gender": np.array(["M", "F"]),
            "Height": np.array([175.0, 165.0]),
            "Weight": np.array([70.0, 60.0]),
            "BMI": np.array([22.9, 22.0]),
        }
    }

    monkeypatch.setattr(
        "software.pulsedb.reader.mat73.loadmat",
        lambda _: fake_data,
    )

    reader = PulseDBReader(str(file_path))

    with pytest.raises(ValueError, match="đúng 3 kênh"):
        reader.read(limit=1)


def test_reader_accepts_gender_m_f(tmp_path, monkeypatch):
    file_path = tmp_path / "gender_m_f.mat"
    file_path.touch()

    fake_data = {
        "Subset": {
            "Signals": np.zeros((2, 3, 1250)),
            "SBP": np.array([120.0, 121.0]),
            "DBP": np.array([80.0, 81.0]),
            "Subject": np.array(["p001", "p002"]),
            "Age": np.array([25.0, 26.0]),
            "Gender": np.array(["M", "F"]),
            "Height": np.array([175.0, 165.0]),
            "Weight": np.array([70.0, 60.0]),
            "BMI": np.array([22.9, 22.0]),
        }
    }

    monkeypatch.setattr(
        "software.pulsedb.reader.mat73.loadmat",
        lambda _: fake_data,
    )

    reader = PulseDBReader(str(file_path))
    segments = reader.read(limit=2)

    assert [segment.gender for segment in segments] == ["M", "F"]
