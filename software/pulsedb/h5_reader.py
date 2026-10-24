"""Partial reader for PulseDB Subset files (MATLAB v7.3, i.e. HDF5) via h5py.

``PulseDBReader`` (mat73) loads the whole file into RAM, about 14 GB for
``VitalDB_Train_Subset.mat``. This reader opens the HDF5 datasets directly:
``subject_ids()`` reads only the Subject cells, ``read(rows)`` only the
requested rows (signals and per-row fields alike, sliced by row), and
``lazy(rows)`` reads them block by block on access. For a given row it returns
the same ``PulseSegment`` values as ``PulseDBReader``: same
field names and unwrapping, MATLAB's reversed axis order, and the shared
conversion helpers of ``reader.py``. Like that reader it does not filter,
normalize signals or infer missing metadata.
"""

from bisect import bisect_right
from collections.abc import Mapping
import math
import os

import h5py
import numpy as np

from software.pulsedb.reader import (
    CHANNEL_ORDER, OPTIONAL_FIELDS, PulseSegment, extract_scalar, normalize_gender,
    subject_text,
)

SIGNAL_NAMES = ["Signals", "signals", "sig"]
REQUIRED_FIELDS = {
    "sbp": ["SBP", "sbp"],
    "dbp": ["DBP", "dbp"],
    "subject_id": ["Subject", "Subject_ID", "subject", "subj"],
    "age": ["Age", "age"],
    "gender": ["Gender", "gender"],
}
# Rows per HDF5 read: bounds the temporary block (about 120 MB for 1250 samples
# x 3 channels in float64).
BLOCK_ROWS = 4096
_HIDDEN = ("#refs#", "#subsystem#")


def _matlab_class(node):
    value = node.attrs.get("MATLAB_class")
    return value.decode() if isinstance(value, bytes) else value


def _root(handle):
    """Descend single-variable groups, as PulseDBReader unwraps one-key dicts."""
    node = handle
    names = [name for name in node if name not in _HIDDEN]
    while len(names) == 1 and isinstance(node[names[0]], h5py.Group):
        node = node[names[0]]
        names = list(node)
    return node


def _lookup(group, names, required=True):
    for name in names:
        if name in group:
            return group[name]
        for key in group.keys():
            if key.lower() == name.lower():
                return group[key]
    if not required:
        return None
    raise KeyError(
        f"Không tìm thấy một trong các key: {names}. "
        f"Các key hiện có: {list(group.keys())}"
    )


def _squeeze(array):
    """mat73: MATLAB vectors are 2-D; drop the singleton axis after transposing."""
    array = np.asarray(array).T
    if array.ndim == 2 and 1 in array.shape:
        array = array.reshape([size for size in array.shape if size > 1])
    return array


def _cell_content(dataset):
    """Value of one cell, converted as mat73 does for char and numeric arrays."""
    if not isinstance(dataset, h5py.Dataset):
        raise ValueError("Ô cell không phải dataset; reader chỉ hỗ trợ char/số")
    matlab_class = _matlab_class(dataset)
    if "MATLAB_empty" in dataset.attrs:
        return "" if matlab_class == "char" else None
    if matlab_class == "char":
        return "".join(map(chr, np.ravel(dataset[()]).tolist()))
    if dataset.dtype.kind in "iuf":
        return _squeeze(dataset[()])
    raise ValueError(f"Kiểu MATLAB trong cell không hỗ trợ: {matlab_class!r}")


def _rows(rows, n_rows):
    if rows is None:
        return list(range(n_rows))
    selected = []
    for row in rows:
        if isinstance(row, (bool, np.bool_)) or not isinstance(
            row, (int, np.integer)
        ) or not 0 <= row < n_rows:
            raise ValueError("rows phải là số nguyên trong [0, số đoạn)")
        selected.append(int(row))
    if not selected or len(set(selected)) != len(selected):
        raise ValueError("rows phải khác rỗng và không trùng")
    return sorted(selected)


def _runs(rows):
    """Contiguous [start, stop) ranges of sorted rows, at most BLOCK_ROWS long."""
    start = previous = rows[0]
    for row in rows[1:]:
        if row != previous + 1 or row - start >= BLOCK_ROWS:
            yield start, previous + 1
            start = row
        previous = row
    yield start, previous + 1


class _Column:
    """One per-row field; its shape is checked without reading any value."""

    def __init__(self, dataset, n_rows, name):
        # mat73 squeezes MATLAB's (1, N) or (N, 1) vectors to N values.
        if dataset.ndim != 2 or 1 not in dataset.shape:
            raise ValueError(f"Trường {name} phải là vector, shape {dataset.shape}")
        self.dataset = dataset
        self.axis = 1 if dataset.shape[0] == 1 else 0
        if dataset.shape[self.axis] != n_rows:
            raise ValueError(
                f"Trường {name} có {dataset.shape[self.axis]} phần tử, "
                f"khác số đoạn trong Signals ({n_rows})"
            )

    def read(self, start, stop):
        """Values (numbers or cell references) of rows [start, stop) only."""
        if self.axis == 1:
            return self.dataset[0, start:stop]
        return self.dataset[start:stop, 0]


class _Source:
    """An open file's Signals plus per-row fields, read by row ranges."""

    def __init__(self, handle):
        self.handle = handle
        self.group = _root(handle)
        self.signals = _lookup(self.group, SIGNAL_NAMES)
        # HDF5 stores MATLAB's (segment, channel, sample) as (sample, channel, segment).
        if self.signals.ndim != 3:
            raise ValueError(
                f"Signals phải có 3 chiều (segment, channel, sample), "
                f"nhưng nhận được shape {self.signals.shape[::-1]}"
            )
        if self.signals.shape[1] != len(CHANNEL_ORDER):
            raise ValueError(
                f"Signals phải có đúng 3 kênh (ECG, PPG, ABP), "
                f"nhưng nhận được {self.signals.shape[1]} kênh"
            )
        self.n_rows = self.signals.shape[2]
        self._columns = {}

    def column(self, field):
        """``_Column`` of a field, or None for an absent/empty optional field."""
        if field not in self._columns:
            required = field in REQUIRED_FIELDS
            names = REQUIRED_FIELDS[field] if required else OPTIONAL_FIELDS[field]
            dataset = _lookup(self.group, names, required=required)
            if dataset is None or "MATLAB_empty" in dataset.attrs:
                if required:
                    raise ValueError(f"Trường bắt buộc {names[0]} rỗng hoặc None")
                self._columns[field] = None
            else:
                self._columns[field] = _Column(dataset, self.n_rows, names[0])
        return self._columns[field]

    def values(self, field, start, stop):
        """Converted values of rows [start, stop); NaN for an absent optional field."""
        column = self.column(field)
        if column is None:
            return [math.nan] * (stop - start)
        values = []
        for value in column.read(start, stop):
            if isinstance(value, h5py.Reference):
                value = _cell_content(self.handle[value])
            values.append(extract_scalar(value))
        return values

    def block(self, start, stop):
        """{raw_index: PulseSegment} for the contiguous rows [start, stop)."""
        # Check every field before reading values, as PulseDBReader does.
        for field in (*REQUIRED_FIELDS, *OPTIONAL_FIELDS):
            self.column(field)
        fields = {field: self.values(field, start, stop)
                  for field in (*REQUIRED_FIELDS, *OPTIONAL_FIELDS)}
        signals = self.signals[:, :, start:stop]
        segments = {}
        for offset, i in enumerate(range(start, stop)):
            def value(field):
                return fields[field][offset]

            segments[i] = PulseSegment(
                subject_id=subject_text(value("subject_id"), i),
                gender=normalize_gender(value("gender")),
                age=float(value("age")),
                height_cm=float(value("height_cm")),
                weight_kg=float(value("weight_kg")),
                bmi_kg_m2=float(value("bmi_kg_m2")),
                sbp=float(value("sbp")),
                dbp=float(value("dbp")),
                # Own copies: a segment kept by the caller must not pin the block.
                ecg=signals[:, 0, offset].copy(),
                ppg=signals[:, 1, offset].copy(),
                abp=signals[:, 2, offset].copy(),
            )
        return segments


class LazySegments(Mapping):
    """{raw_index: PulseSegment} over fixed rows, read one block at a time.

    Keeps the file open and only the current block (at most BLOCK_ROWS
    contiguous rows) in memory, so passes in raw_index order need about one
    block; each segment owns its waveforms, so segments the caller keeps cost
    only their own size. Values equal ``PulseDBH5Reader.read`` for the same rows.
    The caller checks the file's SHA-256 before and after use, and closes it
    (``with``); access after closing raises ValueError.
    """

    def __init__(self, file_path, rows):
        self._handle = h5py.File(file_path, "r")
        try:
            self._source = _Source(self._handle)
            self._rows = _rows(rows, self._source.n_rows)
        except Exception:
            self._handle.close()
            raise
        self._members = set(self._rows)
        self._runs = list(_runs(self._rows))
        self._starts = [start for start, _ in self._runs]
        self._block = {}

    def __getitem__(self, row):
        if row not in self._members:
            raise KeyError(row)
        if not self._handle.id.valid:
            raise ValueError("LazySegments đã đóng")
        if row not in self._block:
            self._block = {}  # Release the previous block before reading the next.
            start, stop = self._runs[bisect_right(self._starts, row) - 1]
            self._block = self._source.block(start, stop)
        return self._block[row]

    def __iter__(self):
        return iter(self._rows)

    def __len__(self):
        return len(self._rows)

    def close(self):
        self._block = {}
        self._handle.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()


class PulseDBH5Reader:
    """Read Subject IDs, then selected rows, of one PulseDB Subset file."""

    def __init__(self, file_path: str):
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Không tìm thấy file: {file_path}")
        self.file_path = file_path

    def subject_ids(self) -> list[str]:
        """Subject of every row in file order; reads no label, demographic or signal."""
        with h5py.File(self.file_path, "r") as handle:
            source = _Source(handle)
            values = source.values("subject_id", 0, source.n_rows)
            return [subject_text(value, i) for i, value in enumerate(values)]

    def read(self, rows=None) -> dict[int, PulseSegment]:
        """{raw_index: PulseSegment} for ``rows`` (every row if None), ascending."""
        with h5py.File(self.file_path, "r") as handle:
            source = _Source(handle)
            segments = {}
            for start, stop in _runs(_rows(rows, source.n_rows)):
                segments.update(source.block(start, stop))
            return segments

    def lazy(self, rows=None) -> LazySegments:
        """Like ``read`` but reads blocks on access; use as a context manager."""
        return LazySegments(self.file_path, rows)
