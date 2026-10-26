"""SYNTHETIC checks: the h5py partial reader returns the mat73 reader's rows."""

import math

import h5py
import numpy as np
import pytest

from scripts.compare_pulsedb_readers import SCALARS, WAVEFORMS, compare
from software.pulsedb import h5_reader
from software.pulsedb.h5_reader import PulseDBH5Reader
from software.pulsedb.reader import PulseDBReader
from tests.pulsedb_h5_fixture import synthetic_rows, write_subset


def _equal(left, right):
    for field in SCALARS:
        a, b = getattr(left, field), getattr(right, field)
        assert type(a) is type(b)
        assert (isinstance(a, float) and math.isnan(a) and math.isnan(b)) or a == b
    for field in WAVEFORMS:
        a, b = getattr(left, field), getattr(right, field)
        assert a.dtype == b.dtype and np.array_equal(a, b)


@pytest.mark.parametrize("optional", [True, False])
def test_h5_reader_matches_mat73_reader(tmp_path, optional):
    rows = synthetic_rows()
    path = write_subset(tmp_path / "SYN_subset.mat", rows, optional=optional)
    expected = PulseDBReader(str(path)).read()
    actual = PulseDBH5Reader(str(path)).read()
    assert list(actual) == list(range(len(rows)))
    for i, segment in enumerate(expected):
        _equal(segment, actual[i])
    assert compare(path)["pass"]
    # Known answers from the written rows, not from either reader.
    assert [actual[i].subject_id for i in range(3)] == ["SYN_000"] * 3
    assert [actual[i].gender for i in range(3)] == ["M", "F", "Unknown"]
    assert actual[0].sbp == rows[0].sbp and actual[2].dbp == rows[2].dbp
    assert np.array_equal(actual[4].ppg, rows[4].ppg)
    assert math.isnan(actual[1].height_cm)
    assert math.isnan(actual[0].height_cm) is not optional


def test_partial_read_matches_full_read_across_blocks(tmp_path, monkeypatch):
    rows = synthetic_rows()
    reader = PulseDBH5Reader(str(write_subset(tmp_path / "SYN_subset.mat", rows)))
    full = reader.read()
    monkeypatch.setattr(h5_reader, "BLOCK_ROWS", 2)
    wanted = [17, 0, 1, 2, 5, 6, 7, 8]
    part = reader.read(wanted)
    assert list(part) == sorted(wanted)
    for i in wanted:
        _equal(full[i], part[i])
    assert reader.subject_ids() == [row.subject_id for row in rows]


def test_runs_split_contiguous_rows_at_the_block_limit(monkeypatch):
    monkeypatch.setattr(h5_reader, "BLOCK_ROWS", 3)
    assert list(h5_reader._runs([0, 1, 2, 3, 4, 7, 8])) == [(0, 3), (3, 5), (7, 9)]


@pytest.mark.parametrize("rows", [[], [True], [-1], [18], [1, 1], [1.0]])
def test_rows_are_validated(tmp_path, rows):
    reader = PulseDBH5Reader(str(write_subset(tmp_path / "SYN.mat", synthetic_rows())))
    with pytest.raises(ValueError, match="rows"):
        reader.read(rows)


def test_two_channel_signals_are_rejected(tmp_path):
    path = write_subset(tmp_path / "SYN.mat", synthetic_rows())
    with h5py.File(path, "a") as handle:
        del handle["Subset/Signals"]
        handle["Subset"].create_dataset("Signals", data=np.zeros((50, 2, 18)))
    reader = PulseDBH5Reader(str(path))
    for call in (reader.read, reader.subject_ids):
        with pytest.raises(ValueError, match="3 kênh"):
            call()


def test_missing_file_is_reported(tmp_path):
    with pytest.raises(FileNotFoundError):
        PulseDBH5Reader(str(tmp_path / "absent.mat"))


def test_lazy_rows_match_eager_read_and_hold_one_block(tmp_path, monkeypatch):
    reader = PulseDBH5Reader(str(write_subset(tmp_path / "SYN.mat", synthetic_rows())))
    wanted = [17, 0, 1, 2, 5, 6, 7, 8]
    eager = reader.read(wanted)
    monkeypatch.setattr(h5_reader, "BLOCK_ROWS", 2)
    with reader.lazy(wanted) as lazy:
        assert list(lazy) == sorted(wanted) and len(lazy) == len(wanted)
        for i in lazy:
            _equal(eager[i], lazy[i])
            assert len(lazy._block) <= 2  # Only the current block is kept.
        assert np.int64(5) in lazy and 3 not in lazy
        with pytest.raises(KeyError):
            lazy[3]
    with pytest.raises(ValueError, match="rows"):
        reader.lazy([18])


def test_partial_reads_touch_only_requested_rows_of_label_fields(tmp_path, monkeypatch):
    reader = PulseDBH5Reader(str(write_subset(tmp_path / "SYN.mat", synthetic_rows())))
    accesses = []
    original = h5py.Dataset.__getitem__

    def spy(self, args, *rest, **kwargs):
        accesses.append((self.name, args))
        return original(self, args, *rest, **kwargs)

    monkeypatch.setattr(h5py.Dataset, "__getitem__", spy)
    reader.read([3, 4, 10])
    for field in ("SBP", "DBP", "Age", "Subject", "Gender", "Signals"):
        keys = [args for name, args in accesses if name == f"/Subset/{field}"]
        assert keys and all(slice(3, 5) in key or slice(10, 11) in key for key in keys)
    accesses.clear()
    with reader.lazy([3, 4, 10]) as lazy:
        lazy[10]
    sbp = [args for name, args in accesses if name == "/Subset/SBP"]
    assert sbp == [(0, slice(10, 11))]
    accesses.clear()
    reader.subject_ids()
    assert {name for name, _ in accesses if not name.startswith("/#refs#")} == {
        "/Subset/Subject"}


def test_segments_own_their_waveforms(tmp_path):
    reader = PulseDBH5Reader(str(write_subset(tmp_path / "SYN.mat", synthetic_rows())))
    with reader.lazy([0, 1]) as lazy:
        kept = lazy[0]
    for segment in (kept, *reader.read([2, 3]).values()):
        for field in WAVEFORMS:
            values = getattr(segment, field)
            assert values.flags.owndata and values.flags.c_contiguous


def test_lazy_file_is_closed_on_exit_error_and_failed_init(tmp_path, monkeypatch):
    reader = PulseDBH5Reader(str(write_subset(tmp_path / "SYN.mat", synthetic_rows())))
    opened = []
    original = h5py.File

    def recording(*args, **kwargs):
        handle = original(*args, **kwargs)
        opened.append(handle)
        return handle

    monkeypatch.setattr(h5_reader.h5py, "File", recording)
    with reader.lazy([0, 1]) as lazy:
        lazy[0]
    with pytest.raises(ValueError, match="đóng"):
        lazy[1]
    with pytest.raises(RuntimeError):
        with reader.lazy([0, 1]):
            raise RuntimeError("caller failure")
    with pytest.raises(ValueError, match="rows"):
        reader.lazy([18])
    assert len(opened) == 3 and not any(handle.id.valid for handle in opened)
