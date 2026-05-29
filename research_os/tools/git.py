"""Git state capture without depending on GitPython.

ResearchOS only needs three things from git: the current commit SHA, whether
the worktree is dirty, and the current branch. We shell out and tolerate the
absence of git or the absence of a repo.
"""
from __future__ import annotations

import subprocess
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, Optional


@dataclass
class GitState:
    inside_repo: bool
    commit: str = ""
    short_commit: str = ""
    branch: str = ""
    dirty: bool = False
    remote: str = ""
    untracked_count: int = 0
    modified_count: int = 0
    error: str = ""

    def to_dict(self) -> Dict[str, object]:
        return asdict(self)


def _run(cmd: list[str], cwd: Path) -> Optional[str]:
    try:
        result = subprocess.run(
            cmd,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def is_inside_git_repo(cwd: Path | str) -> bool:
    out = _run(["git", "rev-parse", "--is-inside-work-tree"], Path(cwd))
    return out == "true"


def capture_git_state(cwd: Path | str = ".") -> GitState:
    cwd = Path(cwd)
    if not is_inside_git_repo(cwd):
        return GitState(inside_repo=False, error="not inside a git repo")
    commit = _run(["git", "rev-parse", "HEAD"], cwd) or ""
    short = _run(["git", "rev-parse", "--short", "HEAD"], cwd) or ""
    branch = _run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd) or ""
    remote = _run(["git", "remote", "get-url", "origin"], cwd) or ""
    status = _run(["git", "status", "--porcelain"], cwd) or ""
    untracked = sum(1 for line in status.splitlines() if line.startswith("??"))
    modified = sum(
        1
        for line in status.splitlines()
        if line and not line.startswith("??")
    )
    return GitState(
        inside_repo=True,
        commit=commit,
        short_commit=short,
        branch=branch,
        remote=remote,
        dirty=bool(status),
        untracked_count=untracked,
        modified_count=modified,
    )


__all__ = ["GitState", "capture_git_state", "is_inside_git_repo"]
