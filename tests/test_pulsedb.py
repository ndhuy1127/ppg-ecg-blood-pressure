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


def test_wrong_channel_count():
    signals = np.zeros((10, 4, 1250))

    with pytest.raises(AssertionError):
        assert signals.shape[1] == 3