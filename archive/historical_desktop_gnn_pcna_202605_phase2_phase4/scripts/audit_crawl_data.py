#!/usr/bin/env python3
"""Phase 4 crawl quality audit (Advay parallel track, Track 2a).

Reads the committed PCNA crawl registry (`data/registries/friend_crawl_registry.json`,
JSON Lines despite the `.json` extension) and flags each of the 72 structures against the
Phase 4 quality criteria defined in `docs/advay_parallel_track.md` Track 2a:

  - resolution_angstrom <= 3.5 Angstrom
  - organism == "Homo sapiens"
  - chain_count >= 3 (PCNA is a homotrimer; monomer crystals may be artifacts)
  - has_parsed_features == True (ESM-2 array exists)
  - file_path is not null (raw PDB available)

This script only reads the committed registry and writes one compact audit registry.
It does NOT touch Phase 3, generate graphs, train, evaluate, run MD, read the test
split, or make scientific claims. Quality flags are mechanical filters, not biological
judgements. The positive control 8GLA is audited like every other structure and is NOT
exempted here; the resolution exception for 8GLA is handled downstream in
`rank_pcna_candidates.py` with an explicit, documented override.

Governance: docs/scientific_governance/12_PCNA_SPECIFIC_CHECKS.md,
            docs/scientific_governance/04_DATASET_CONSTRAINTS.md,
            docs/scientific_governance/15_PROVENANCE_AND_REPRODUCIBILITY.md
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_DIR = ROOT / "data" / "registries"
REGISTRY_PATH = REGISTRY_DIR / "friend_crawl_registry.json"
OUTPUT_PATH = REGISTRY_DIR / "phase4_crawl_audit.json"

# Quality thresholds (from docs/advay_parallel_track.md Track 2a).
MAX_RESOLUTION_ANGSTROM = 3.5
REQUIRED_ORGANISM = "Homo sapiens"
MIN_CHAIN_COUNT = 3


def sha256_of_file(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def load_registry(path: Path) -> list[dict[str, Any]]:
    """The registry is JSON Lines (one record per line)."""
    records: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


@dataclass
class AuditEntry:
    pdb_id: str
    passes_filter: bool
    failure_reasons: list[str] = field(default_factory=list)
    resolution_angstrom: float | None = None
    chain_count: int | None = None
    organism: str | None = None
    has_parsed_features: bool | None = None
    has_file_path: bool = False
    heuristic_pocket_score: float | None = None


def audit_record(rec: dict[str, Any]) -> AuditEntry:
    reasons: list[str] = []

    resolution = rec.get("resolution_angstrom")
    if resolution is None:
        reasons.append("resolution missing")
    elif resolution > MAX_RESOLUTION_ANGSTROM:
        reasons.append(f"resolution {resolution} A > {MAX_RESOLUTION_ANGSTROM} A")

    organism = rec.get("organism")
    if organism is None:
        reasons.append("organism missing")
    elif organism != REQUIRED_ORGANISM:
        reasons.append(f"organism '{organism}' != '{REQUIRED_ORGANISM}'")

    chain_count = rec.get("chain_count")
    if chain_count is None:
        reasons.append("chain_count missing")
    elif chain_count < MIN_CHAIN_COUNT:
        reasons.append(f"chain_count {chain_count} < {MIN_CHAIN_COUNT}")

    if not rec.get("has_parsed_features"):
        reasons.append("no parsed ESM-2 features")

    has_file_path = rec.get("file_path") is not None
    if not has_file_path:
        reasons.append("file_path null (no raw PDB)")

    return AuditEntry(
        pdb_id=rec["id"],
        passes_filter=len(reasons) == 0,
        failure_reasons=reasons,
        resolution_angstrom=resolution,
        chain_count=chain_count,
        organism=organism,
        has_parsed_features=rec.get("has_parsed_features"),
        has_file_path=has_file_path,
        heuristic_pocket_score=rec.get("heuristic_pocket_score"),
    )


def main() -> None:
    if not REGISTRY_PATH.exists():
        raise SystemExit(f"FAIL-CLOSED: registry not found: {REGISTRY_PATH}")

    records = load_registry(REGISTRY_PATH)
    entries = [audit_record(rec) for rec in records]

    n_pass = sum(1 for entry in entries if entry.passes_filter)
    n_fail = len(entries) - n_pass

    # Aggregate failure-reason counts for quick human review.
    reason_counts: dict[str, int] = {}
    for entry in entries:
        for reason in entry.failure_reasons:
            # Normalise resolution/chain/organism messages to a category key.
            key = reason.split(" ")[0] if reason[0].isalpha() else reason
            if reason.startswith("resolution"):
                key = "resolution > threshold or missing"
            elif reason.startswith("organism"):
                key = "organism not Homo sapiens or missing"
            elif reason.startswith("chain_count"):
                key = "chain_count < 3 or missing"
            elif reason.startswith("no parsed"):
                key = "no parsed ESM-2 features"
            elif reason.startswith("file_path"):
                key = "file_path null"
            reason_counts[key] = reason_counts.get(key, 0) + 1

    output = {
        "schema_version": "1.0",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "generator": "scripts/audit_crawl_data.py",
        "source_registry": str(REGISTRY_PATH.relative_to(ROOT)),
        "source_registry_sha256": sha256_of_file(REGISTRY_PATH),
        "criteria": {
            "max_resolution_angstrom": MAX_RESOLUTION_ANGSTROM,
            "required_organism": REQUIRED_ORGANISM,
            "min_chain_count": MIN_CHAIN_COUNT,
            "require_parsed_features": True,
            "require_file_path": True,
        },
        "summary": {
            "n_structures": len(entries),
            "n_pass": n_pass,
            "n_fail": n_fail,
            "failure_reason_counts": reason_counts,
        },
        "note": (
            "Mechanical quality filter only. 8GLA (AOH1996 positive control) fails the "
            "resolution criterion at 3.77 A; the documented override that keeps it as a "
            "positive control lives in rank_pcna_candidates.py, not here."
        ),
        "structures": [asdict(entry) for entry in entries],
    }

    OUTPUT_PATH.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(f"Audited {len(entries)} structures: {n_pass} pass, {n_fail} fail.")
    print(f"Failure-reason counts: {reason_counts}")
    print(f"Wrote {OUTPUT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
