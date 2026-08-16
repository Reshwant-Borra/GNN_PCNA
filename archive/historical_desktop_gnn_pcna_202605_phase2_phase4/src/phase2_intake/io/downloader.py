"""Fail-closed HTTP download utilities for governed raw intake."""

from __future__ import annotations

import shutil
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from phase2_intake.config import USER_AGENT
from phase2_intake.io.hasher import sha256_file


@dataclass
class ProbeResult:
    http_status: int | None
    file_size_bytes: int | None
    error: str | None = None


@dataclass
class DownloadResult:
    http_status: int | None
    file_size_bytes: int | None
    sha256: str | None
    error: str | None = None


def request_headers() -> dict[str, str]:
    return {"User-Agent": USER_AGENT}


def probe_url(url: str, timeout: int = 30) -> ProbeResult:
    request = urllib.request.Request(url, method="HEAD", headers=request_headers())
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            size_raw = response.headers.get("Content-Length")
            size = int(size_raw) if size_raw and size_raw.isdigit() else None
            return ProbeResult(http_status=response.status, file_size_bytes=size)
    except urllib.error.HTTPError as exc:
        # Some endpoints reject HEAD. Report the status and let the controller
        # decide whether a body request is safe.
        return ProbeResult(http_status=exc.code, file_size_bytes=None, error=str(exc))
    except Exception as exc:
        return ProbeResult(http_status=None, file_size_bytes=None, error=str(exc))


def infer_filename(url: str, fallback: str) -> str:
    path = urlparse(url).path
    name = Path(path).name
    if name:
        return name
    return fallback


def guarded_target(root: Path, source_name: str, relative_path: str) -> Path:
    source_root = (root / source_name).resolve()
    target = (source_root / relative_path).resolve()
    if source_root != target and source_root not in target.parents:
        raise ValueError(f"Refusing to write outside raw intake source folder: {target}")
    return target


def download_url(url: str, target: Path, timeout: int = 60) -> DownloadResult:
    target.parent.mkdir(parents=True, exist_ok=True)
    part = target.with_suffix(target.suffix + ".part")
    headers = request_headers()
    resume_from = part.stat().st_size if part.exists() else 0
    if resume_from:
        headers["Range"] = f"bytes={resume_from}-"
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            mode = "ab" if resume_from and response.status == 206 else "wb"
            with part.open(mode) as handle:
                shutil.copyfileobj(response, handle)
            part.replace(target)
            return DownloadResult(
                http_status=response.status,
                file_size_bytes=target.stat().st_size,
                sha256=sha256_file(target),
            )
    except Exception as exc:
        return DownloadResult(http_status=None, file_size_bytes=None, sha256=None, error=str(exc))
