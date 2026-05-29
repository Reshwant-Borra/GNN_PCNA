"""Capture the current Python/OS environment for provenance."""
from __future__ import annotations

import platform
import socket
import subprocess
import sys
from dataclasses import dataclass, field, asdict
from typing import Dict, List

from research_os.tools.hashing import text_hash


@dataclass
class EnvironmentSnapshot:
    environment_id: str
    python_version: str
    python_executable: str
    os: str
    os_release: str
    machine: str
    hostname: str
    cuda_version: str = ""
    pip_freeze: List[str] = field(default_factory=list)
    package_hash: str = ""

    def to_dict(self) -> Dict[str, object]:
        return asdict(self)


def _safe_pip_freeze() -> List[str]:
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "freeze", "--disable-pip-version-check"],
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return []
    if result.returncode != 0:
        return []
    return [line for line in result.stdout.splitlines() if line.strip()]


def _detect_cuda() -> str:
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=driver_version", "--format=csv,noheader"],
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return ""
    if result.returncode != 0:
        return ""
    line = result.stdout.strip().splitlines()
    return line[0] if line else ""


def capture_environment(*, include_pip_freeze: bool = True) -> EnvironmentSnapshot:
    freeze = _safe_pip_freeze() if include_pip_freeze else []
    package_hash = text_hash("\n".join(sorted(freeze))) if freeze else ""
    return EnvironmentSnapshot(
        environment_id=f"ENV-{package_hash or 'unknown'}",
        python_version=sys.version.split()[0],
        python_executable=sys.executable,
        os=platform.system(),
        os_release=platform.release(),
        machine=platform.machine(),
        hostname=socket.gethostname(),
        cuda_version=_detect_cuda(),
        pip_freeze=freeze,
        package_hash=package_hash,
    )


__all__ = ["EnvironmentSnapshot", "capture_environment"]
