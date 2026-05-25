"""Provenance capture: bundle git + environment + hashes + command into one record."""
from __future__ import annotations

import os
import socket
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from research_os.tools.environment import EnvironmentSnapshot, capture_environment
from research_os.tools.git import GitState, capture_git_state
from research_os.tools.hashing import file_hash, directory_hash


@dataclass
class ProvenanceRecord:
    timestamp: str
    machine: str
    git: Dict[str, object]
    environment: Dict[str, object]
    command: str = ""
    inputs: List[Dict[str, str]] = field(default_factory=list)
    outputs: List[Dict[str, str]] = field(default_factory=list)
    notes: str = ""

    def to_dict(self) -> Dict[str, object]:
        return asdict(self)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _hash_input(path: Path) -> Dict[str, str]:
    if path.is_dir():
        return {"path": str(path), "hash": directory_hash(path), "kind": "directory"}
    return {"path": str(path), "hash": file_hash(path), "kind": "file"}


def capture_provenance(
    *,
    cwd: Path | str = ".",
    command: str = "",
    inputs: Optional[List[Path | str]] = None,
    outputs: Optional[List[Path | str]] = None,
    notes: str = "",
    include_pip_freeze: bool = False,
) -> ProvenanceRecord:
    """Capture a single provenance snapshot.

    ``include_pip_freeze`` is off by default to keep audit runs fast; turn it
    on for run records you want to lock to a specific environment.
    """
    git_state: GitState = capture_git_state(cwd)
    env: EnvironmentSnapshot = capture_environment(include_pip_freeze=include_pip_freeze)
    return ProvenanceRecord(
        timestamp=_utc_now_iso(),
        machine=socket.gethostname(),
        git=git_state.to_dict(),
        environment=env.to_dict(),
        command=command or " ".join(os.sys.argv if hasattr(os, "sys") else []),
        inputs=[_hash_input(Path(p)) for p in (inputs or [])],
        outputs=[_hash_input(Path(p)) for p in (outputs or [])],
        notes=notes,
    )


__all__ = ["ProvenanceRecord", "capture_provenance"]
