"""Logger output files kept gzip-compressed on disk (added 2026-11-27).

The large text tables of a recording (``packets.csv``, ``samples.csv``,
``rx_chunks.csv``, ``t_rx_packets.csv``) can be stored as ``<name>.gz``. Their
SHA-256 in the session manifest is always that of the **uncompressed** content,
so the hash does not depend on the compressor and a reader checks exactly the
bytes it parses. ``compressed_outputs`` in the manifest maps a name to the file
that holds it; a name not in that map is stored as is. The gzip header carries
no file name and time 0, so equal content gives equal ``.gz`` bytes.

This module only opens the files it is given; it reads no dataset by itself.
"""

import gzip
import hashlib
import io
from pathlib import Path

SUFFIX = ".gz"
COMPRESSIBLE = ("packets.csv", "samples.csv", "rx_chunks.csv", "t_rx_packets.csv")
LEVEL = 6
CHUNK = 1 << 20


class GzipOut:
    """A new ``<path>.gz`` (exclusive create) written like a binary file."""

    def __init__(self, path):
        self.path = Path(str(path) + SUFFIX)
        self._raw = open(self.path, "xb")
        try:
            self._gzip = gzip.GzipFile(filename="", mode="wb", fileobj=self._raw,
                                       compresslevel=LEVEL, mtime=0)
        except BaseException:
            self._raw.close()
            raise

    def write(self, payload):
        return self._gzip.write(payload)

    def flush(self):
        self._gzip.flush()

    def fileno(self):
        return self._raw.fileno()

    @property
    def closed(self):
        return self._raw.closed

    def close(self):
        if not self._raw.closed:
            try:
                self._gzip.close()
            finally:
                self._raw.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
        return False


def open_new(path, compress):
    """A new output file: ``path`` itself, or ``path.gz`` when ``compress``."""
    return GzipOut(path) if compress else Path(path).open("xb")


def stored_name(name, compressed_outputs):
    return (compressed_outputs or {}).get(name, name)


def content_sha256(path):
    """SHA-256 of the content: decompressed for a ``.gz`` file."""
    digest = hashlib.sha256()
    opener = gzip.open if str(path).endswith(SUFFIX) else open
    with opener(path, "rb") as handle:
        for block in iter(lambda: handle.read(CHUNK), b""):
            digest.update(block)
    return digest.hexdigest()


def open_text(directory, name, compressed_outputs=None):
    """Text reader of output ``name`` of a recording, compressed or not."""
    path = Path(directory) / stored_name(name, compressed_outputs)
    if str(path).endswith(SUFFIX):
        return io.TextIOWrapper(gzip.open(path, "rb"), encoding="utf-8", newline="")
    return open(path, newline="", encoding="utf-8")
