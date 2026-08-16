"""JSON I/O helpers with fail-closed error messages."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from phase3_data.errors import Phase3DataError
from phase3_data.hashing import sha256_file


def read_json(path: Path) -> Any:
    if not path.is_file():
        raise Phase3DataError(f"Required JSON file is missing: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise Phase3DataError(f"Invalid JSON in {path}: {exc}") from exc


def write_json(path: Path, data: Any) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return sha256_file(path)


def reject_original_folds_path(path: Path) -> None:
    if path.name.lower() == "folds.json":
        raise Phase3DataError(
            "Original CryptoBench folds.json is forbidden for Phase 3. "
            "Use data/registries/split_manifest_frozen.json."
        )

