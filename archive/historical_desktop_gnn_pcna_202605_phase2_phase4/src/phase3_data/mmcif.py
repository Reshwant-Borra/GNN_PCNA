"""Minimal mmCIF residue parser for audit manifests.

This parser intentionally extracts residue identity and atom-presence metadata only. It
does not resolve alternate locations into coordinates or construct graph edges. HETATM
records are included only when they carry a polymer sequence position, which preserves
modified residues such as MSE while excluding free ligands and waters.
"""

from __future__ import annotations

import shlex
from collections import OrderedDict
from pathlib import Path

from phase3_data.errors import Phase3DataError
from phase3_data.models import ResidueNode


ATOM_SITE_COLUMNS = {
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
}


def _clean(value: str | None) -> str | None:
    if value is None or value in {"?", "."}:
        return None
    return value


def _split_cif_row(line: str) -> list[str]:
    try:
        return shlex.split(line, posix=True)
    except ValueError as exc:
        raise Phase3DataError(f"Unable to parse mmCIF atom_site row: {line[:120]}") from exc


def _find_atom_site_loop(lines: list[str]) -> tuple[list[str], int]:
    for idx, line in enumerate(lines):
        if line.strip() != "loop_":
            continue
        cursor = idx + 1
        headers: list[str] = []
        while cursor < len(lines) and lines[cursor].startswith("_atom_site."):
            headers.append(lines[cursor].strip().split(".", 1)[1])
            cursor += 1
        if headers:
            missing = ATOM_SITE_COLUMNS - set(headers)
            if missing:
                raise Phase3DataError(f"atom_site loop is missing required columns: {sorted(missing)}")
            return headers, cursor
    raise Phase3DataError("No atom_site loop found in mmCIF file.")


def parse_mmcif_residues(path: Path) -> list[ResidueNode]:
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    headers, cursor = _find_atom_site_loop(lines)
    residues: OrderedDict[tuple[str, str, str | None], dict[str, object]] = OrderedDict()
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
        chain_id = _clean(row.get("auth_asym_id")) or _clean(row.get("label_asym_id"))
        residue_number = _clean(row.get("auth_seq_id")) or _clean(row.get("label_seq_id"))
        residue_name = _clean(row.get("auth_comp_id")) or _clean(row.get("label_comp_id"))
        if chain_id is None or residue_number is None or residue_name is None:
            raise Phase3DataError(f"atom_site row lacks residue identity in {path}.")
        insertion_code = _clean(row.get("pdbx_PDB_ins_code"))
        key = (chain_id, residue_number, insertion_code)
        atom_name = _clean(row.get("auth_atom_id")) or _clean(row.get("label_atom_id")) or "UNKNOWN"
        altloc = _clean(row.get("label_alt_id"))
        if key not in residues:
            label_token = f"{residue_number}{insertion_code or ''}"
            residues[key] = {
                "chain_id": chain_id,
                "residue_number": residue_number,
                "insertion_code": insertion_code,
                "residue_name": residue_name,
                "label_key": f"{chain_id}_{label_token}",
                "label_seq_id": _clean(row.get("label_seq_id")),
                "entity_id": _clean(row.get("label_entity_id")),
                "atom_names": set(),
                "altloc_ids": set(),
            }
        residues[key]["atom_names"].add(atom_name)  # type: ignore[index, union-attr]
        if altloc:
            residues[key]["altloc_ids"].add(altloc)  # type: ignore[index, union-attr]
    nodes: list[ResidueNode] = []
    for row in residues.values():
        atom_names = tuple(sorted(row["atom_names"]))  # type: ignore[arg-type]
        altloc_ids = tuple(sorted(row["altloc_ids"]))  # type: ignore[arg-type]
        nodes.append(
            ResidueNode(
                chain_id=str(row["chain_id"]),
                residue_number=str(row["residue_number"]),
                insertion_code=row["insertion_code"],  # type: ignore[arg-type]
                residue_name=str(row["residue_name"]),
                label_key=str(row["label_key"]),
                label_seq_id=row["label_seq_id"],  # type: ignore[arg-type]
                entity_id=row["entity_id"],  # type: ignore[arg-type]
                atom_count=len(atom_names),
                atom_names=atom_names,
                altloc_ids=altloc_ids,
                has_ca="CA" in atom_names,
            )
        )
    if not nodes:
        raise Phase3DataError(f"No residue nodes recovered from {path}.")
    return nodes
