"""CA coordinate extraction with altloc resolution from mmCIF files.

Extracts the Cartesian coordinates of the CA atom for each residue node,
applying the approved altloc selection policy:

  Approved policy (graph_policy_human_decision_20260528.md):
  - Use the CA coordinate with highest occupancy.
  - Tie-break lexicographically by altloc ID, with '.' and '?' preferred over
    lettered alternates. Among lettered alternates, sort alphabetically (A < B).
  - Fail closed if any CA row required for graph construction has non-numeric
    coordinates.

This module is intentionally separate from phase3_data.mmcif, which handles
residue-identity extraction only. Both parsers operate on the same CIF file.

Governance: docs/scientific_governance/07_PREPROCESSING_AND_GRAPH_RULES.md
"""

from __future__ import annotations

import math
import shlex
from collections import defaultdict
from pathlib import Path

from phase3_data.errors import Phase3DataError


# Columns required by this parser (superset of basic residue-identity columns)
_REQUIRED_COLUMNS = frozenset({
    "group_PDB",
    "label_atom_id",
    "label_alt_id",
    "label_comp_id",
    "label_asym_id",
    "label_entity_id",
    "label_seq_id",
    "pdbx_PDB_ins_code",
    "auth_seq_id",
    "auth_comp_id",
    "auth_asym_id",
    "auth_atom_id",
    "pdbx_PDB_model_num",
    "Cartn_x",
    "Cartn_y",
    "Cartn_z",
    "occupancy",
})


def _clean(value: str | None) -> str | None:
    if value is None or value in {"?", "."}:
        return None
    return value


def _split_cif_row(line: str) -> list[str]:
    try:
        return shlex.split(line, posix=True)
    except ValueError as exc:
        raise Phase3DataError(f"Unable to parse mmCIF atom_site row: {line[:120]}") from exc


def _altloc_sort_key(altloc: str | None) -> tuple[int, str]:
    """Lower key = preferred. None/'.'/  '?' win over letters; letters sort alpha."""
    if altloc is None or altloc in {".", "?"}:
        return (0, "")
    return (1, altloc)


def _find_atom_site_loop(lines: list[str]) -> tuple[list[str], int]:
    for idx, line in enumerate(lines):
        if line.strip() != "loop_":
            continue
        cursor = idx + 1
        headers: list[str] = []
        while cursor < len(lines) and lines[cursor].strip().startswith("_atom_site."):
            headers.append(lines[cursor].strip().split(".", 1)[1])
            cursor += 1
        if not headers:
            continue
        missing = _REQUIRED_COLUMNS - set(headers)
        if missing:
            raise Phase3DataError(
                f"atom_site loop is missing columns required for coordinate extraction: "
                f"{sorted(missing)}"
            )
        return headers, cursor
    raise Phase3DataError("No atom_site loop with required coordinate columns found in mmCIF file.")


# Key: (chain_id, residue_number, insertion_code)
# Value: (x, y, z, selected_altloc_id)
CACoords = dict[tuple[str, str, str | None], tuple[float, float, float, str | None]]


def extract_ca_coordinates(path: Path) -> CACoords:
    """Return CA coordinates for each residue with altloc resolution.

    Returns a dict keyed by (chain_id, residue_number, insertion_code) mapping
    to (x, y, z, selected_altloc_id).

    selected_altloc_id is None when no altloc was present (i.e., the single CA
    record had altloc '.' or '?').

    Raises Phase3DataError for non-numeric coordinates or malformed rows.
    """
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    headers, cursor = _find_atom_site_loop(lines)

    # residue_key -> list of (occupancy, altloc_sort_key_tuple, altloc_raw, x, y, z)
    CandidateRow = tuple[float, tuple[int, str], str | None, float, float, float]
    candidates: dict[tuple[str, str, str | None], list[CandidateRow]] = defaultdict(list)

    while cursor < len(lines):
        line = lines[cursor].strip()
        cursor += 1
        if not line:
            continue
        if line == "#" or line == "loop_" or line.startswith("_"):
            break

        values = _split_cif_row(line)
        if len(values) != len(headers):
            raise Phase3DataError(
                f"atom_site row has {len(values)} values but expected {len(headers)} in {path}."
            )
        row = dict(zip(headers, values))

        group = row["group_PDB"]
        if group not in {"ATOM", "HETATM"}:
            continue
        if group == "HETATM" and _clean(row.get("label_seq_id")) is None:
            continue
        model = _clean(row.get("pdbx_PDB_model_num"))
        if model not in {None, "1"}:
            continue

        atom_name = _clean(row.get("auth_atom_id")) or _clean(row.get("label_atom_id"))
        if atom_name != "CA":
            continue

        chain_id = _clean(row.get("auth_asym_id")) or _clean(row.get("label_asym_id"))
        residue_number = _clean(row.get("auth_seq_id")) or _clean(row.get("label_seq_id"))
        if chain_id is None or residue_number is None:
            continue
        insertion_code = _clean(row.get("pdbx_PDB_ins_code"))
        key = (chain_id, residue_number, insertion_code)

        altloc_raw = _clean(row.get("label_alt_id"))
        altloc_key = _altloc_sort_key(altloc_raw)

        occ_str = row.get("occupancy", "1.0")
        try:
            occ = float(occ_str) if occ_str and occ_str not in {".", "?"} else 1.0
        except ValueError:
            occ = 1.0

        x_str = row.get("Cartn_x", "")
        y_str = row.get("Cartn_y", "")
        z_str = row.get("Cartn_z", "")
        try:
            x, y, z = float(x_str), float(y_str), float(z_str)
        except (ValueError, TypeError) as exc:
            raise Phase3DataError(
                f"Non-numeric CA coordinates for residue {key} in {path}: "
                f"({x_str!r}, {y_str!r}, {z_str!r})"
            ) from exc
        if not (math.isfinite(x) and math.isfinite(y) and math.isfinite(z)):
            raise Phase3DataError(
                f"Non-finite CA coordinates for residue {key} in {path}: "
                f"({x}, {y}, {z})"
            )

        candidates[key].append((occ, altloc_key, altloc_raw, x, y, z))

    result: CACoords = {}
    for key, records in candidates.items():
        # Sort: descending occupancy, then ascending altloc sort key (prefer None/./? over letters)
        best = sorted(records, key=lambda r: (-r[0], r[1]))[0]
        _occ, _altloc_key, altloc_raw, x, y, z = best
        # Report selected_altloc_id as None when it was the unambiguous (no-altloc) record
        selected = altloc_raw if (altloc_raw is not None and altloc_raw not in {".", "?"}) else None
        result[key] = (x, y, z, selected)

    return result
