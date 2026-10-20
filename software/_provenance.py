"""Line-ending independent SHA-256 for tracked text files (code, JSON configs).

Git stores these files with LF; a Windows checkout with ``core.autocrlf=true``
has CRLF on disk. Hashing raw bytes would then give a value that no committed
blob reproduces. Raw data and generated binaries must still use a byte hash.
"""

import hashlib
from pathlib import Path


def normalized_text(payload: bytes) -> bytes:
    """Return ``payload`` with CRLF converted to LF; other bytes unchanged."""
    if not isinstance(payload, bytes):
        raise ValueError("payload must be bytes")
    return payload.replace(b"\r\n", b"\n")


def text_sha256(payload: bytes) -> str:
    return hashlib.sha256(normalized_text(payload)).hexdigest()


def text_file_sha256(path) -> str:
    return text_sha256(Path(path).read_bytes())
