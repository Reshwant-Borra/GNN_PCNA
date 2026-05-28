#!/usr/bin/env python3
"""Phase 4 candidate ranking (Advay parallel track, Track 2b).

Consumes `data/registries/phase4_crawl_audit.json` (from audit_crawl_data.py) and the
source registry, and produces a ranked Phase 4 inference candidate manifest per
docs/advay_parallel_track.md Track 2b:

  - Exclude structures that fail the quality filter.
  - Rank surviving structures by:
      (1) has_ligand AND heuristic_pocket_score, descending
      (2) resolution, ascending
  - 8GLA (AOH1996 complex) is force-included as POSITIVE CONTROL even though it fails the
    resolution filter (3.77 A > 3.5 A). This is an explicit, documented override, not a
    silent threshold change. 8GLA is a positive control / sanity check ONLY -- per
    governance doc 12 its recovery never validates a novel-site prediction.
  - 5E0V (apo PCNA) is flagged as the REFERENCE structure.

This is a ranking of inference *candidates*. It is NOT a prediction, NOT a ranking of
druggability, and NOT a scientific claim. Inference itself is gated (GATE 6, PCNA gate)
and is Reshwant's Phase 3/4 work. This script only reads committed registries and writes
a manifest.

Governance: docs/scientific_governance/12_PCNA_SPECIFIC_CHECKS.md,
            docs/scientific_governance/04_DATASET_CONSTRAINTS.md,
            docs/scientific_governance/15_PROVENANCE_AND_REPRODUCIBILITY.md
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_DIR = ROOT / "data" / "registries"
REGISTRY_PATH = REGISTRY_DIR / "friend_crawl_registry.json"
AUDIT_PATH = REGISTRY_DIR / "phase4_crawl_audit.json"
OUTPUT_PATH = REGISTRY_DIR / "phase4_candidate_manifest.json"

POSITIVE_CONTROL_ID = "8GLA"
REFERENCE_ID = "5E0V"


def sha256_of_file(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def load_registry(path: Path) -> dict[str, dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rec = json.loads(line)
                records[rec["id"].upper()] = rec
    return records


def sort_key(rec: dict[str, Any]) -> tuple:
    """Rank key. Python sort is ascending, so negate descending criteria.

    Tier 1: has_ligand True before False.
    Tier 2: heuristic_pocket_score descending (missing score sorts last).
    Tier 3: resolution ascending (missing resolution sorts last).
    """
    has_ligand = bool(rec.get("has_ligand"))
    score = rec.get("heuristic_pocket_score")
    resolution = rec.get("resolution_angstrom")
    return (
        0 if has_ligand else 1,
        -score if score is not None else float("inf"),
        resolution if resolution is not None else float("inf"),
    )


def main() -> None:
    for required in (REGISTRY_PATH, AUDIT_PATH):
        if not required.exists():
            raise SystemExit(f"FAIL-CLOSED: required input not found: {required}")

    registry = load_registry(REGISTRY_PATH)
    audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
    audit_by_id = {entry["pdb_id"].upper(): entry for entry in audit["structures"]}

    # Surviving structures = those that pass the quality filter.
    passing_ids = [pid for pid, entry in audit_by_id.items() if entry["passes_filter"]]

    # Force-include the positive control even if it failed the filter.
    pc_forced = False
    if POSITIVE_CONTROL_ID in audit_by_id and POSITIVE_CONTROL_ID not in passing_ids:
        passing_ids.append(POSITIVE_CONTROL_ID)
        pc_forced = True

    ranked_records = sorted(
        (registry[pid] for pid in passing_ids if pid in registry),
        key=sort_key,
    )

    candidates: list[dict[str, Any]] = []
    for rank, rec in enumerate(ranked_records, start=1):
        pid = rec["id"].upper()
        audit_entry = audit_by_id.get(pid, {})

        role = "candidate"
        inclusion_reason_parts: list[str] = []
        notes_parts: list[str] = []

        if pid == POSITIVE_CONTROL_ID:
            role = "positive_control"
            inclusion_reason_parts.append(
                "AOH1996/8GLA positive control; force-included despite resolution "
                f"{rec.get('resolution_angstrom')} A > 3.5 A filter (documented override)"
            )
            notes_parts.append(
                "Positive-control sanity check only; recovery does NOT validate novel "
                "sites (governance doc 12)."
            )
        elif pid == REFERENCE_ID:
            role = "reference"
            inclusion_reason_parts.append("nominal PCNA reference structure")
            notes_parts.append(
                "CAVEAT: 5E0V is NOT apo wild-type PCNA -- it is the PCNA S228I disease "
                "variant bound to a FEN1 peptide (Duffy 2016, PMID 26688547). A true-apo "
                "WT PCNA reference should be confirmed before use as the MD apo reference."
            )
        else:
            score = rec.get("heuristic_pocket_score")
            if rec.get("has_ligand") and score is not None:
                inclusion_reason_parts.append(
                    f"passes quality filter; has_ligand + heuristic_pocket_score={score}"
                )
            elif rec.get("has_ligand"):
                inclusion_reason_parts.append(
                    "passes quality filter; has_ligand, no heuristic_pocket_score"
                )
            else:
                inclusion_reason_parts.append(
                    "passes quality filter; no ligand, no heuristic_pocket_score"
                )

        if rec.get("heuristic_pocket_score") is None:
            notes_parts.append("heuristic_pocket_score absent in registry")

        candidates.append(
            {
                "rank": rank,
                "pdb_id": rec["id"],
                "role": role,
                "passes_quality_filter": audit_entry.get("passes_filter"),
                "inclusion_reason": "; ".join(inclusion_reason_parts),
                "has_ligand": rec.get("has_ligand"),
                "heuristic_pocket_score": rec.get("heuristic_pocket_score"),
                "resolution_angstrom": rec.get("resolution_angstrom"),
                "chain_count": rec.get("chain_count"),
                "notes": "; ".join(notes_parts) if notes_parts else rec.get("notes"),
            }
        )

    # Identify the top non-control, non-reference candidate (input to Track 3c).
    top_candidate = next(
        (c["pdb_id"] for c in candidates if c["role"] == "candidate"), None
    )

    output = {
        "schema_version": "1.0",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "generator": "scripts/rank_pcna_candidates.py",
        "source_registry": str(REGISTRY_PATH.relative_to(ROOT)),
        "source_registry_sha256": sha256_of_file(REGISTRY_PATH),
        "source_audit": str(AUDIT_PATH.relative_to(ROOT)),
        "source_audit_sha256": sha256_of_file(AUDIT_PATH),
        "ranking_rule": (
            "Exclude quality-filter failures (except force-included positive control). "
            "Sort by (has_ligand desc, heuristic_pocket_score desc, resolution asc)."
        ),
        "positive_control": POSITIVE_CONTROL_ID,
        "positive_control_force_included": pc_forced,
        "reference_structure": REFERENCE_ID,
        "top_non_control_candidate": top_candidate,
        "disclaimer": (
            "Candidate inference ranking only. Not a prediction, druggability claim, or "
            "novel-site claim. PCNA inference is gated (GATE 6) and is not run here."
        ),
        "summary": {
            "n_ranked": len(candidates),
            "n_quality_pass": len([c for c in candidates if c["passes_quality_filter"]]),
            "n_force_included": 1 if pc_forced else 0,
        },
        "candidates": candidates,
    }

    OUTPUT_PATH.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(f"Ranked {len(candidates)} candidates.")
    print(f"Positive control {POSITIVE_CONTROL_ID} force-included: {pc_forced}")
    print(f"Top non-control candidate: {top_candidate}")
    print(f"Wrote {OUTPUT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
