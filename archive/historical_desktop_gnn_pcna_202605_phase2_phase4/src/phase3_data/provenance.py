"""Small provenance helpers for governed Phase 3 artifacts."""

from __future__ import annotations

import os
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from phase3_data.hashing import sha256_file


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def safe_commit_hash(root: Path) -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=root,
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except Exception:
        return "UNKNOWN"


def environment_summary() -> dict[str, str]:
    return {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "executable": sys.executable,
    }


def input_hashes(paths: Iterable[Path]) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for path in paths:
        if path.is_file():
            hashes[str(path)] = sha256_file(path)
    return hashes


def command_from_argv(argv: list[str] | None = None) -> str:
    args = sys.argv if argv is None else argv
    return " ".join(args)


def process_context(root: Path, command: str) -> dict[str, object]:
    return {
        "created_at": utc_timestamp(),
        "created_by": "codex",
        "command": command,
        "cwd": os.fspath(root),
        "commit_hash": safe_commit_hash(root),
        "environment": environment_summary(),
    }

