"""CIF utility functions for Phase 4 inference.

Handles gzip decompression and entity-description parsing from mmCIF files.
Governance: docs/scientific_governance/12_PCNA_SPECIFIC_CHECKS.md
Authorization: reports/phase4/gate6_authorization_20260529.md
"""

from __future__ import annotations

import contextlib
import gzip
import shlex
import tempfile
from pathlib import Path


def read_cif_text(path: Path) -> str:
    """Return the full text of a .cif or .cif.gz file."""
    if path.suffix == ".gz":
        with gzip.open(path, "rt", encoding="utf-8", errors="replace") as fh:
            return fh.read()
    return path.read_text(encoding="utf-8", errors="replace")


@contextlib.contextmanager
def temp_cif(path: Path):
    """Context manager: yield an uncompressed .cif Path for parsers that need a file path.

    Decompresses .cif.gz to a temp file; passes .cif through unchanged.
    Cleans up the temp file on exit (only if we created it).
    """
    if path.suffix != ".gz":
        yield path
        return

    text = read_cif_text(path)
    with tempfile.NamedTemporaryFile(
        suffix=".cif", delete=False, mode="w", encoding="utf-8"
    ) as tmp:
        tmp.write(text)
        tmp_path = Path(tmp.name)
    try:
        yield tmp_path
    finally:
        tmp_path.unlink(missing_ok=True)


def parse_entity_descriptions(cif_text: str) -> dict[str, str]:
    """Return a mapping of entity_id -> pdbx_description from CIF text.

    Handles both loop_ form and key-value form.
    Returns empty dict if no entity section is found.
    """
    lines = cif_text.splitlines()
    entities: dict[str, str] = {}

    i = 0
    while i < len(lines):
        stripped = lines[i].strip()

        # Loop_ form: look for a loop_ followed by _entity. headers
        if stripped == "loop_":
            j = i + 1
            hdrs: list[str] = []
            while j < len(lines) and lines[j].strip().startswith("_entity."):
                hdrs.append(lines[j].strip().split(".", 1)[1])
                j += 1
            if "id" in hdrs and "pdbx_description" in hdrs:
                id_idx = hdrs.index("id")
                desc_idx = hdrs.index("pdbx_description")
                k = j
                while k < len(lines):
                    row = lines[k].strip()
                    k += 1
                    if not row or row in {"#", "loop_"} or row.startswith("_"):
                        break
                    try:
                        vals = shlex.split(row, posix=True)
                    except ValueError:
                        continue
                    if len(vals) > max(id_idx, desc_idx):
                        eid = vals[id_idx]
                        raw = vals[desc_idx]
                        entities[eid] = "" if raw in {".", "?"} else raw
                i = k
                continue

        # Key-value form: _entity.id / _entity.pdbx_description on separate lines
        if stripped.startswith("_entity.id ") or stripped == "_entity.id":
            parts = stripped.split(None, 1)
            eid = parts[1].strip() if len(parts) > 1 else None
            if eid and eid not in {".", "?"}:
                # Look ahead for _entity.pdbx_description
                for ahead in range(i + 1, min(i + 10, len(lines))):
                    s2 = lines[ahead].strip()
                    if s2.startswith("_entity.pdbx_description"):
                        p2 = s2.split(None, 1)
                        raw = p2[1].strip().strip("'\"") if len(p2) > 1 else ""
                        entities[eid] = "" if raw in {".", "?"} else raw
                        break

        i += 1

    return entities
