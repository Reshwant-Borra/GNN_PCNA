"""Interface-overlap audit for Phase 4 PCNA inference.

Computes overlap between predicted high-scoring residues and known PCNA
interaction interfaces from data/registries/pcna_interface_map.json.

Canonical P12004 numbering applies to human PCNA (Parts 1 and 2A).
Part 2C (homologs) are excluded from canonical-overlap reporting.

Governance: docs/scientific_governance/12_PCNA_SPECIFIC_CHECKS.md
Authorization: reports/phase4/gate6_authorization_20260529.md
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_interface_map(registry_path: Path) -> dict[str, list[int]]:
    """Return interface_name -> sorted list of canonical residue numbers."""
    data = json.loads(registry_path.read_text(encoding="utf-8"))
    result: dict[str, list[int]] = {}
    for iface_name, iface_data in data.items():
        if isinstance(iface_data, dict) and "residues" in iface_data:
            result[iface_name] = sorted(iface_data["residues"])
        elif isinstance(iface_data, list):
            result[iface_name] = sorted(iface_data)
    return result


def _expand_residue_ranges(raw_residues: list[Any]) -> list[int]:
    """Expand [n, [a, b], ...] forms to flat integer list."""
    result: list[int] = []
    for item in raw_residues:
        if isinstance(item, list):
            result.extend(range(item[0], item[1] + 1))
        else:
            result.append(int(item))
    return result


def load_interface_map_from_file(registry_path: Path) -> dict[str, set[int]]:
    """Return interface_name -> set of canonical residue positions.

    Parses the 'regions' key of pcna_interface_map.json.
    """
    raw = json.loads(registry_path.read_text(encoding="utf-8"))
    regions = raw.get("regions", raw)  # fall back to top-level if no 'regions' key
    result: dict[str, set[int]] = {}
    for iface_name, iface_data in regions.items():
        if isinstance(iface_data, dict) and "residues" in iface_data:
            residues = _expand_residue_ranges(iface_data["residues"])
        elif isinstance(iface_data, list):
            residues = _expand_residue_ranges(iface_data)
        else:
            residues = []
        if residues:
            result[iface_name] = set(residues)
    return result


def compute_interface_overlaps(
    residue_scores: list[dict[str, Any]],
    interface_map: dict[str, set[int]],
    top_k: int = 20,
) -> dict[str, Any]:
    """Compute interface overlap for a single structure's residue scores.

    Args:
        residue_scores: List of dicts with keys 'residue_number' (str), 'score' (float),
                        'chain_id' (str). Must be from human PCNA (canonical numbering).
        interface_map:  Output of load_interface_map_from_file().
        top_k:         Number of top-scoring residues to consider for overlap.

    Returns:
        Dict with per-interface overlap counts, fractions, and top-K residue list.
    """
    scored = sorted(residue_scores, key=lambda r: -r["score"])
    top_residues = scored[:top_k]

    top_resnums: set[int] = set()
    for r in top_residues:
        try:
            top_resnums.add(int(r["residue_number"]))
        except (ValueError, TypeError):
            pass

    all_resnums: set[int] = set()
    for r in residue_scores:
        try:
            all_resnums.add(int(r["residue_number"]))
        except (ValueError, TypeError):
            pass

    overlaps: dict[str, Any] = {}
    for iface_name, iface_residues in interface_map.items():
        iface_in_structure = iface_residues & all_resnums
        overlap_top_k = iface_residues & top_resnums
        overlaps[iface_name] = {
            "interface_size": len(iface_residues),
            "interface_residues_in_structure": len(iface_in_structure),
            "top_k_overlap_count": len(overlap_top_k),
            "top_k_overlap_fraction": (
                len(overlap_top_k) / len(iface_in_structure)
                if iface_in_structure else 0.0
            ),
            "overlapping_residues": sorted(overlap_top_k),
        }

    return {
        "top_k": top_k,
        "n_residues_scored": len(residue_scores),
        "top_k_residue_numbers": sorted(top_resnums),
        "interface_overlaps": overlaps,
    }


def aggregate_chain_scores(
    per_chain_scores: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    """Aggregate per-residue scores across homotrimer chains by max score.

    For each canonical residue number, takes the max score across all chains.

    Args:
        per_chain_scores: chain_id -> list of {'residue_number', 'score', 'chain_id', ...}

    Returns:
        List of {'residue_number', 'score', 'chains'} sorted by canonical residue number.
    """
    max_by_resnum: dict[str, dict[str, Any]] = {}

    for chain_id, scores in per_chain_scores.items():
        for rec in scores:
            rn = rec["residue_number"]
            if rn not in max_by_resnum or rec["score"] > max_by_resnum[rn]["score"]:
                max_by_resnum[rn] = {
                    "residue_number": rn,
                    "score": rec["score"],
                    "best_chain": chain_id,
                }

    return sorted(max_by_resnum.values(), key=lambda r: _safe_int(r["residue_number"]))


def _safe_int(s: Any) -> int:
    try:
        return int(s)
    except (ValueError, TypeError):
        return 0
