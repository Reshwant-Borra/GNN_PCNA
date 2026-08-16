"""Append-only download manifest writer and reader."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from phase2_intake.models import ManifestEntry


class ManifestWriter:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, entry: ManifestEntry) -> None:
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry.to_json_dict(), sort_keys=True) + "\n")


def read_manifest(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def iter_manifest(path: Path) -> Iterable[dict]:
    yield from read_manifest(path)

