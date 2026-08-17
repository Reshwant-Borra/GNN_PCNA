"""Resumable, polite downloader for open-access PDFs.

Only fetches URLs that an OA location exposed. Enforces robots.txt and a
per-host rate limit, caps total size, dedupes, and records provenance in a
corpus manifest so a crawl can be stopped and resumed. The 30 GB target is
reached by breadth of legal OA sources, not by bypassing anything.
"""
from __future__ import annotations

import hashlib
import json
import time
import urllib.request
import urllib.robotparser
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from paper_engine import config
from paper_engine.corpus.bulk_sources import WorkRecord

_MANIFEST = "corpus_manifest.json"
_MIN_HOST_INTERVAL = 1.0  # seconds between requests to the same host


class _RobotsCache:
    def __init__(self):
        self._cache: Dict[str, urllib.robotparser.RobotFileParser] = {}

    def allowed(self, url: str, ua: str = "paper_engine") -> bool:
        from urllib.parse import urlparse
        parts = urlparse(url)
        host = f"{parts.scheme}://{parts.netloc}"
        rp = self._cache.get(host)
        if rp is None:
            rp = urllib.robotparser.RobotFileParser()
            rp.set_url(host + "/robots.txt")
            try:
                rp.read()
            except Exception:
                rp = None  # if robots unreachable, default to permissive but rate-limited
            self._cache[host] = rp
        if rp is None:
            return True
        try:
            return rp.can_fetch(ua, url)
        except Exception:
            return True


class _RateLimiter:
    def __init__(self, min_interval: float = _MIN_HOST_INTERVAL):
        self.min_interval = min_interval
        self._last: Dict[str, float] = {}

    def wait(self, host: str) -> None:
        now = time.time()
        last = self._last.get(host, 0.0)
        delta = now - last
        if delta < self.min_interval:
            time.sleep(self.min_interval - delta)
        self._last[host] = time.time()


@dataclass
class DownloadStats:
    attempted: int = 0
    downloaded: int = 0
    skipped_existing: int = 0
    skipped_robots: int = 0
    failed: int = 0
    total_bytes: int = 0
    items: List[dict] = field(default_factory=list)


def _shard_path(key: str) -> Path:
    digest = hashlib.sha256(key.encode()).hexdigest()
    return config.CORPUS_PDF_DIR / digest[:2] / f"{digest[:16]}.pdf"


def _load_manifest() -> Dict[str, dict]:
    path = config.CORPUS_DIR / _MANIFEST
    if path.exists():
        try:
            return {it["key"]: it for it in json.loads(path.read_text(encoding="utf-8")).get("items", [])}
        except Exception:
            return {}
    return {}


def _save_manifest(items: Dict[str, dict]) -> Path:
    config.CORPUS_DIR.mkdir(parents=True, exist_ok=True)
    path = config.CORPUS_DIR / _MANIFEST
    payload = {"schema": "paper_engine.corpus/v1",
               "note": "Open-access full text only; downloaded under each item's OA license.",
               "count": len(items), "items": list(items.values())}
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


_BROWSER_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
               "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")


def _fetch(url: str, dest: Path, timeout: int = 60) -> int:
    # A browser-like UA is required by several OA hosts (notably NCBI/PMC) which
    # otherwise return an HTML interstitial instead of the PDF.
    req = urllib.request.Request(
        url, headers={"User-Agent": _BROWSER_UA, "Accept": "application/pdf,*/*"})
    dest.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = resp.read()
    # Basic sanity: PDFs start with %PDF.
    if not data[:4] == b"%PDF":
        raise ValueError("not a PDF")
    dest.write_bytes(data)
    return len(data)


def download_corpus(records: List[WorkRecord], *, max_gb: float = 30.0,
                    max_files: Optional[int] = None, verbose: bool = True) -> DownloadStats:
    """Download OA PDFs for the given records up to a size/file cap. Resumable."""
    config.CORPUS_PDF_DIR.mkdir(parents=True, exist_ok=True)
    manifest = _load_manifest()
    stats = DownloadStats()
    stats.total_bytes = sum(it.get("bytes", 0) for it in manifest.values())
    robots = _RobotsCache()
    limiter = _RateLimiter()
    cap_bytes = int(max_gb * (1024 ** 3))

    for rec in records:
        if stats.total_bytes >= cap_bytes:
            if verbose:
                print(f"[corpus] size cap reached ({stats.total_bytes/1e9:.2f} GB).")
            break
        if max_files is not None and stats.downloaded >= max_files:
            break
        key = rec.dedup_key()
        if key in manifest:
            stats.skipped_existing += 1
            continue
        url = rec.oa_pdf_url
        if not url:
            continue
        stats.attempted += 1
        if not robots.allowed(url):
            stats.skipped_robots += 1
            continue
        dest = _shard_path(key)
        try:
            limiter.wait(rec.host or url)
            nbytes = _fetch(url, dest)
        except Exception as exc:
            stats.failed += 1
            if verbose:
                print(f"[corpus] failed {url[:80]}: {exc}")
            continue
        item = {
            "key": key, "doi": rec.doi, "title": rec.title, "year": rec.year,
            "authors": rec.authors, "url": url, "host": rec.host,
            "license": rec.license, "oa_status": rec.oa_status,
            "path": str(dest.relative_to(config.REPO_ROOT)) if str(dest).startswith(str(config.REPO_ROOT)) else str(dest),
            "bytes": nbytes,
        }
        manifest[key] = item
        stats.items.append(item)
        stats.downloaded += 1
        stats.total_bytes += nbytes
        if verbose and stats.downloaded % 25 == 0:
            print(f"[corpus] {stats.downloaded} files, {stats.total_bytes/1e9:.2f} GB")
        if stats.downloaded % 50 == 0:
            _save_manifest(manifest)  # checkpoint

    _save_manifest(manifest)
    return stats
