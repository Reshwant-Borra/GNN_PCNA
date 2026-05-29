"""Small-file schema probing for downloaded or linked raw intake artifacts."""

from __future__ import annotations

import csv
import json
from pathlib import Path


TEXT_SUFFIXES = {".txt", ".md", ".rst", ".json", ".csv", ".tsv", ".xml", ".html", ".cif", ".mmcif", ".pdb"}
MAX_SCHEMA_PROBE_BYTES = 2 * 1024 * 1024


def schema_status_for_path(path: Path) -> tuple[str, str]:
    if not path.is_file():
        return "SCHEMA_UNKNOWN", "No local file available for schema probe."
    if path.stat().st_size > MAX_SCHEMA_PROBE_BYTES:
        return "SCHEMA_PARTIAL", "File is larger than schema probe limit; header-only inspection required later."
    suffix = path.suffix.lower()
    if suffix not in TEXT_SUFFIXES:
        return "SCHEMA_UNREADABLE", f"File suffix {suffix or '<none>'} is not safely readable as text."
    try:
        if suffix == ".json":
            with path.open("r", encoding="utf-8") as handle:
                value = json.load(handle)
            if isinstance(value, dict):
                return "SCHEMA_PARTIAL", "Readable JSON object with keys: " + ", ".join(list(value.keys())[:20])
            if isinstance(value, list):
                return "SCHEMA_PARTIAL", f"Readable JSON list with {len(value)} top-level entries."
            return "SCHEMA_PARTIAL", f"Readable JSON top-level type: {type(value).__name__}."
        if suffix in {".csv", ".tsv"}:
            dialect = "excel-tab" if suffix == ".tsv" else "excel"
            with path.open("r", encoding="utf-8", newline="") as handle:
                reader = csv.reader(handle, dialect=dialect)
                header = next(reader, [])
            return "SCHEMA_PARTIAL", "Delimited header: " + ", ".join(header[:40])
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            first_line = handle.readline().strip()
        return "SCHEMA_PARTIAL", f"Readable text-like file; first line: {first_line[:160]}"
    except Exception as exc:
        return "SCHEMA_UNREADABLE", str(exc)

