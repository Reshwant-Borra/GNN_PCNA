"""Content-addressed hashing for files, directories, and arbitrary text.

We use sha256 truncated to 16 hex chars for compactness in registries; the
full sha is recoverable on demand by calling `file_hash(path, full=True)`.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Iterable, Optional


def text_hash(text: str, *, full: bool = False) -> str:
    h = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return h if full else h[:16]


def file_hash(path: Path | str, *, full: bool = False) -> str:
    """SHA-256 of file contents. Returns empty string if file is missing."""
    p = Path(path)
    if not p.is_file():
        return ""
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    digest = h.hexdigest()
    return digest if full else digest[:16]


def directory_hash(
    path: Path | str,
    *,
    glob: str = "**/*",
    ignore: Optional[Iterable[str]] = None,
    full: bool = False,
) -> str:
    """Hash a directory by hashing each file's content + relative path.

    The hash is order-independent because we sort relative paths first.
    """
    p = Path(path)
    ignore_set = set(ignore or [])
    if not p.is_dir():
        return ""
    h = hashlib.sha256()
    files = sorted(
        f for f in p.glob(glob) if f.is_file() and f.name not in ignore_set
    )
    for f in files:
        rel = str(f.relative_to(p)).replace("\\", "/")
        h.update(rel.encode("utf-8"))
        h.update(b"\x00")
        h.update(file_hash(f, full=True).encode("utf-8"))
        h.update(b"\n")
    digest = h.hexdigest()
    return digest if full else digest[:16]


__all__ = ["directory_hash", "file_hash", "text_hash"]
