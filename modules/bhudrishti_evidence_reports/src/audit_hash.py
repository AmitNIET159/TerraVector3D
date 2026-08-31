"""
SHA-256 audit-hash utilities for BhuDrishti 3D validation reports.

Provides deterministic hashing of:
- Arbitrary Python data structures (via sorted JSON serialisation)
- File contents (streamed for memory efficiency)
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def calculate_audit_hash(data: Any) -> str:
    """Return the SHA-256 hex digest of *data*.

    If *data* is already a ``str`` it is hashed directly; otherwise it is
    serialised to JSON with sorted keys for determinism.
    """
    if isinstance(data, str):
        content = data
    elif isinstance(data, bytes):
        return hashlib.sha256(data).hexdigest()
    else:
        content = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def calculate_file_hash(file_path: str | Path, chunk_size: int = 8192) -> str:
    """Return the SHA-256 hex digest of the file at *file_path*.

    The file is read in chunks so that large files do not need to be loaded
    entirely into memory.
    """
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as fh:
        while True:
            chunk = fh.read(chunk_size)
            if not chunk:
                break
            sha256.update(chunk)
    return sha256.hexdigest()

