"""PCNA chain identification from mmCIF structures.

Strategy (in order of preference):
  1. Entity description match: find entity whose _entity.pdbx_description
     contains 'PCNA' or 'proliferating cell nuclear antigen' (case-insensitive).
  2. Heuristic (Part 1/2A only): entity whose mean residues-per-chain is
     closest to 261 (canonical human PCNA length).
  3. Fallback: all protein chains.

For Part 2C (sliding clamp homologs), all protein chains are always included.

Governance: docs/scientific_governance/12_PCNA_SPECIFIC_CHECKS.md
Authorization: reports/phase4/gate6_authorization_20260529.md
"""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any

from phase4_inference.cif_utils import parse_entity_descriptions, temp_cif

_PCNA_KEYWORDS = ("pcna", "proliferating cell nuclear antigen", "dna sliding clamp")

HUMAN_PCNA_LENGTH = 261


def _is_pcna_description(desc: str) -> bool:
    d = desc.lower()
    return any(kw in d for kw in _PCNA_KEYWORDS)


def select_inference_chains(
    cif_path: Path,
    part: str,
    cif_text: str,
) -> tuple[set[str], str, dict[str, Any]]:
    """Identify which auth_asym_id chains to include in Phase 4 inference.

    Args:
        cif_path: Path to the .cif or .cif.gz file.
        part:     Manifest part — '1', '2A', or '2C'.
        cif_text: Pre-read CIF text (avoid re-reading).

    Returns:
        selected_chains: set of auth_asym_id strings.
        method:          Human-readable description of the selection strategy used.
        audit:           Dict with full selection provenance for the governance record.
    """
    from phase3_data.mmcif import parse_mmcif_residues

    # Parse residues via temp uncompressed path
    with temp_cif(cif_path) as tmp:
        residues = parse_mmcif_residues(tmp)

    # Build chain/entity maps from residue data
    entity_chains: dict[str, set[str]] = defaultdict(set)   # entity_id -> auth_chains
    chain_residues: dict[str, set[tuple]] = defaultdict(set) # auth_chain -> {(resnum, icode)}

    for r in residues:
        if r.entity_id:
            entity_chains[r.entity_id].add(r.chain_id)
        chain_residues[r.chain_id].add((r.residue_number, r.insertion_code))

    entity_descriptions = parse_entity_descriptions(cif_text)

    # Strategy 1: entity description match
    pcna_entities = {
        eid for eid, desc in entity_descriptions.items()
        if _is_pcna_description(desc)
    }

    if pcna_entities:
        selected_chains: set[str] = set()
        for eid in pcna_entities:
            selected_chains.update(entity_chains.get(eid, set()))
        method = f"entity_description_match:entities={sorted(pcna_entities)}"

    elif part in {"1", "2A"}:
        # Strategy 2: heuristic — entity with mean residue count closest to 261
        best_entity: str | None = None
        best_diff = float("inf")
        for eid, chains in entity_chains.items():
            if not chains:
                continue
            # Only consider entities present in multiple chains (trimer = 3 chains)
            chain_list = list(chains)
            mean_res = sum(len(chain_residues[c]) for c in chain_list) / len(chain_list)
            diff = abs(mean_res - HUMAN_PCNA_LENGTH)
            if diff < best_diff:
                best_diff = diff
                best_entity = eid

        if best_entity is not None:
            selected_chains = entity_chains[best_entity]
            method = (
                f"heuristic_261aa_proximity:entity={best_entity}"
                f",mean_res={sum(len(chain_residues[c]) for c in entity_chains[best_entity]) / max(len(entity_chains[best_entity]), 1):.0f}"
                f",diff={best_diff:.0f}"
            )
        else:
            selected_chains = set(chain_residues.keys())
            method = "fallback_all_chains"

    else:
        # Part 2C: all chains (unknown homolog topology)
        selected_chains = set(chain_residues.keys())
        method = "part2c_all_protein_chains"

    audit: dict[str, Any] = {
        "cif_path": str(cif_path),
        "part": part,
        "n_total_chains": len(chain_residues),
        "n_selected_chains": len(selected_chains),
        "selected_chains": sorted(selected_chains),
        "entity_descriptions": entity_descriptions,
        "pcna_entities_found": sorted(pcna_entities),
        "entity_chain_map": {
            eid: sorted(chains) for eid, chains in entity_chains.items()
        },
        "chain_residue_counts": {
            c: len(rr) for c, rr in chain_residues.items()
        },
        "method": method,
        "n_residues_total": len(residues),
    }

    return selected_chains, method, audit, residues
