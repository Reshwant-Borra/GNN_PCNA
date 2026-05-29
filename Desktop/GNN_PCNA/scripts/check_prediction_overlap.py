#!/usr/bin/env python3
"""Check predicted PCNA residues against known interface regions (Track 4 companion).

Takes a list of predicted PCNA residue numbers (canonical UniProt P12004 numbering) and
reports which known regions in `data/registries/pcna_interface_map.json` they overlap.

This is an interpretation aid, not a prediction tool and not a claim generator. It does
NOT run the model, read graphs, or evaluate. Per governance doc 12, any overlap reported
here means a prediction "overlaps a known PCNA interaction interface" and is NOT a novel
site; overlap with the aoh1996_contact_region is positive-control overlap only.

Usage:
    python scripts/check_prediction_overlap.py 40 44 126 128 234
    python scripts/check_prediction_overlap.py --residues residues.json
    python scripts/check_prediction_overlap.py 40 126 234 --json

`--residues FILE` accepts a JSON list of ints, or a JSON object with a top-level
"residues" list.

Governance: docs/scientific_governance/12_PCNA_SPECIFIC_CHECKS.md,
            docs/scientific_governance/14_CLAIM_POLICY.md
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MAP_PATH = ROOT / "data" / "registries" / "pcna_interface_map.json"

ALLOWED_CLAIM = (
    "overlaps a known PCNA interaction interface (governance doc 12); "
    "NOT a novel site. AOH1996/8GLA overlap is positive-control only."
)


def load_map() -> dict[str, Any]:
    if not MAP_PATH.exists():
        raise SystemExit(f"FAIL-CLOSED: interface map not found: {MAP_PATH}")
    return json.loads(MAP_PATH.read_text(encoding="utf-8"))


def parse_residue_file(path: Path) -> list[int]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        data = data.get("residues", [])
    return [int(x) for x in data]


def check_overlap(predicted: list[int], interface_map: dict[str, Any]) -> dict[str, Any]:
    pred_set = sorted(set(predicted))
    regions = interface_map["regions"]
    report: dict[str, Any] = {
        "predicted_residues": pred_set,
        "n_predicted": len(pred_set),
        "uniprot_id": interface_map.get("uniprot_id"),
        "allowed_claim_language": ALLOWED_CLAIM,
        "regions": {},
    }
    any_known = set()
    for name, region in regions.items():
        region_res = set(region["residues"])
        hit = sorted(set(pred_set) & region_res)
        any_known.update(hit)
        report["regions"][name] = {
            "n_region_residues": len(region_res),
            "overlap_residues": hit,
            "n_overlap": len(hit),
            "fraction_of_prediction": round(len(hit) / len(pred_set), 4) if pred_set else 0.0,
            "is_positive_control_region": bool(region.get("positive_control", False)),
            "source_pdb": region.get("source_pdb"),
            "source_pmid": region.get("source_pmid"),
        }
    novel = sorted(set(pred_set) - any_known)
    report["residues_not_in_any_known_region"] = novel
    report["n_not_in_any_known_region"] = len(novel)
    report["interpretation_note"] = (
        "Residues not overlapping any known region are NOT automatically novel pockets; "
        "they may be unmapped surface, crystal artifacts, or trimer-interface-adjacent. "
        "Any novelty statement requires the full PCNA-specific audit (governance doc 12) "
        "and human review. This script does not assert novelty."
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Check predicted PCNA residues vs known interfaces.")
    parser.add_argument("residues", nargs="*", type=int, help="predicted residue numbers")
    parser.add_argument("--residues", dest="residue_file", type=Path, help="JSON file of residues")
    parser.add_argument("--json", action="store_true", help="emit JSON only")
    args = parser.parse_args()

    predicted = list(args.residues)
    if args.residue_file:
        predicted += parse_residue_file(args.residue_file)
    if not predicted:
        parser.error("provide residue numbers as args or via --residues FILE")

    report = check_overlap(predicted, load_map())

    if args.json:
        print(json.dumps(report, indent=2))
        return

    print(f"Predicted residues (n={report['n_predicted']}): {report['predicted_residues']}")
    print(f"UniProt: {report['uniprot_id']}")
    print("-" * 60)
    for name, info in report["regions"].items():
        tag = " [POSITIVE CONTROL]" if info["is_positive_control_region"] else ""
        print(f"{name}{tag}: {info['n_overlap']} overlap "
              f"({info['fraction_of_prediction']*100:.0f}% of prediction) -> {info['overlap_residues']}")
    print("-" * 60)
    print(f"Not in any known region ({report['n_not_in_any_known_region']}): "
          f"{report['residues_not_in_any_known_region']}")
    print(f"\nAllowed claim language: {report['allowed_claim_language']}")


if __name__ == "__main__":
    main()
