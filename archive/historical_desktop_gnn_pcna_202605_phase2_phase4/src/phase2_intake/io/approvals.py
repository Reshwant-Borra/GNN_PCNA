"""Human approval lookup for restricted or bulk intake actions."""

from __future__ import annotations

import json
from pathlib import Path


def load_approvals(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if isinstance(data, dict):
        return list(data.get("approvals", []))
    if isinstance(data, list):
        return data
    return []


def has_bulk_approval(path: Path, *, source_name: str, url: str) -> bool:
    for approval in load_approvals(path):
        if approval.get("source_name") != source_name:
            continue
        if approval.get("url") not in {url, "*"}:
            continue
        if approval.get("decision") not in {"approved", "approved_with_limitations"}:
            continue
        return True
    return False

