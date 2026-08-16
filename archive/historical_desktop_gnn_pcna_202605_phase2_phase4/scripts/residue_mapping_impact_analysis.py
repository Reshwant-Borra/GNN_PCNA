"""
Per-structure impact analysis for Class 2 residue mapping failures
(residue_token_absent_from_atom_site) — informs Decision 4c.

Reads:
  data/registries/residue_mapping_failures.json
  data/raw_intake/cryptobench/metadata_files/66c328c87352852f68dbeac4_dataset.json

Outputs:
  reports/phase2/residue_mapping_4c_impact_analysis.md
  data/registries/residue_mapping_per_structure_impact.json
"""

import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FAILURES_PATH = ROOT / "data/registries/residue_mapping_failures.json"
DATASET_PATH = (
    ROOT
    / "data/raw_intake/cryptobench/metadata_files"
    / "66c328c87352852f68dbeac4_dataset.json"
)
REPORT_PATH = ROOT / "reports/phase2/residue_mapping_4c_impact_analysis.md"
REGISTRY_PATH = ROOT / "data/registries/residue_mapping_per_structure_impact.json"


def load_failures():
    with open(FAILURES_PATH) as f:
        data = json.load(f)
    return data["failures"]


def load_dataset_total_tokens():
    """Return dict: apo_pdb_id -> unique pocket selection token count (union across all holos)."""
    if not DATASET_PATH.exists():
        print(f"WARNING: dataset.json not found at {DATASET_PATH}", file=sys.stderr)
        return {}
    with open(DATASET_PATH) as f:
        dataset = json.load(f)
    totals = {}
    # dataset: {apo_pdb_id: [list of holo records]}
    for apo_id, records in dataset.items():
        if not isinstance(records, list):
            records = [records]
        unique_tokens = set()
        for rec in records:
            pocket = rec.get("apo_pocket_selection", [])
            if isinstance(pocket, list):
                unique_tokens.update(pocket)
            elif isinstance(pocket, dict):
                unique_tokens.update(pocket.keys())
        totals[apo_id.lower()] = len(unique_tokens)
    return totals


def main():
    failures = load_failures()
    totals = load_dataset_total_tokens()
    has_totals = bool(totals)

    # Filter: cryptic records with absent_from_atom_site failures only
    class2_cryptic = [
        f for f in failures
        if f["record_type"] == "cryptic"
        and f["reason"] == "residue_token_absent_from_atom_site"
    ]

    # Group by apo_pdb_id
    per_apo = defaultdict(list)
    for f in class2_cryptic:
        per_apo[f["apo_pdb_id"].lower()].append(f)

    # Also get all cryptic failures per apo (any class) for context
    all_cryptic = [f for f in failures if f["record_type"] == "cryptic"]
    all_cryptic_by_apo = defaultdict(list)
    for f in all_cryptic:
        all_cryptic_by_apo[f["apo_pdb_id"].lower()].append(f)

    # Build per-structure table
    rows = []
    for apo_id, absent_failures in sorted(per_apo.items(),
                                           key=lambda x: -len(x[1])):
        total_pocket = totals.get(apo_id, None)
        absent_count = len(absent_failures)
        fraction = (absent_count / total_pocket) if total_pocket else None
        fold = absent_failures[0].get("fold", "unknown")
        uniprot = absent_failures[0].get("uniprot_id", "unknown")
        rows.append({
            "apo_pdb_id": apo_id,
            "fold": fold,
            "uniprot_id": uniprot,
            "absent_from_atom_site_count": absent_count,
            "total_pocket_tokens": total_pocket,
            "fraction_masked": round(fraction, 4) if fraction is not None else None,
            "all_class_failure_count": len(all_cryptic_by_apo[apo_id]),
        })

    # Distribution stats
    absent_counts = [r["absent_from_atom_site_count"] for r in rows]
    fractions = [r["fraction_masked"] for r in rows if r["fraction_masked"] is not None]

    def pct(threshold, lst):
        return sum(1 for x in lst if x >= threshold)

    # Buckets by absent count
    buckets_count = {
        "1": pct(1, absent_counts),
        "2+": pct(2, absent_counts),
        "5+": pct(5, absent_counts),
        "10+": pct(10, absent_counts),
        "20+": pct(20, absent_counts),
    }

    # Buckets by fraction (only if totals available)
    buckets_frac = {}
    if fractions:
        for t in [0.10, 0.25, 0.50, 0.75]:
            buckets_frac[f">={int(t*100)}%"] = pct(t, fractions)

    total_unique_apos_affected = len(rows)
    total_unique_apos_cryptic = len(set(
        f["apo_pdb_id"].lower() for f in failures if f["record_type"] == "cryptic"
    ))
    total_class2_cryptic_tokens = len(class2_cryptic)

    # Save registry
    registry_out = {
        "analysis_date": "2026-05-27",
        "source": str(FAILURES_PATH.relative_to(ROOT)),
        "scope": "cryptic records, residue_token_absent_from_atom_site only",
        "total_class2_cryptic_tokens": total_class2_cryptic_tokens,
        "unique_apo_structures_affected": total_unique_apos_affected,
        "unique_apo_structures_with_any_cryptic_failure": total_unique_apos_cryptic,
        "has_fraction_data": has_totals,
        "per_structure": rows,
    }
    REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(REGISTRY_PATH, "w") as f:
        json.dump(registry_out, f, indent=2)
    print(f"Registry written: {REGISTRY_PATH}")

    # Write markdown report
    lines = []
    lines += [
        "---",
        "type: analysis-report",
        "status: complete",
        "created: 2026-05-27",
        "informs: Decision 4c — residue_mapping_resolution_policy.md",
        "---",
        "",
        "# Residue Mapping Class 2 Per-Structure Impact Analysis",
        "",
        "**Decision this informs:** 4c — whether structures with a high fraction of",
        "masked pocket residues should be excluded entirely rather than masked.",
        "",
        f"**Scope:** Cryptic records only, `residue_token_absent_from_atom_site` failures only.",
        f"**Source:** `data/registries/residue_mapping_failures.json`",
        f"**Dataset total-token source:** {'`' + str(DATASET_PATH.relative_to(ROOT)) + '`' if has_totals else 'NOT AVAILABLE — fraction analysis skipped'}",
        "",
        "---",
        "",
        "## Top-Line Numbers",
        "",
        f"| Metric | Value |",
        f"|---|---|",
        f"| Total Class 2 cryptic tokens (absent from atom_site) | {total_class2_cryptic_tokens} |",
        f"| Unique apo structures with >=1 Class 2 cryptic failure | {total_unique_apos_affected} |",
        f"| Unique apo structures with any cryptic failure | {total_unique_apos_cryptic} |",
        f"| Fraction of all cryptic apos affected by Class 2 | "
        f"{total_unique_apos_affected}/{total_unique_apos_cryptic} = "
        f"{total_unique_apos_affected/total_unique_apos_cryptic:.1%} |",
        "",
    ]

    lines += [
        "## Distribution by Absent-Residue Count per Structure",
        "",
        "| Structures with N+ absent cryptic pocket residues | Count |",
        "|---|---|",
    ]
    for label, count in buckets_count.items():
        lines.append(f"| >={label} absent residues | {count} |")

    lines += [""]

    if fractions:
        lines += [
            "## Distribution by Fraction of Pocket Residues Masked",
            "",
            "| Threshold | Structures affected |",
            "|---|---|",
        ]
        for label, count in buckets_frac.items():
            lines.append(f"| {label} of pocket residues masked | {count} |")
        lines += [""]
    else:
        lines += [
            "## Fraction Analysis",
            "",
            "> dataset.json not available — fraction analysis could not be computed.",
            "> Only raw absent-residue counts are available.",
            "",
        ]

    lines += [
        "## Per-Structure Table (sorted by absent count, descending)",
        "",
        "| Apo PDB ID | Fold | UniProt | Absent (Class 2) | Total Pocket Tokens | Fraction Masked | All-Class Failures |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        frac_str = f"{r['fraction_masked']:.1%}" if r["fraction_masked"] is not None else "N/A"
        total_str = str(r["total_pocket_tokens"]) if r["total_pocket_tokens"] is not None else "N/A"
        lines.append(
            f"| {r['apo_pdb_id']} | {r['fold']} | {r['uniprot_id']} | "
            f"{r['absent_from_atom_site_count']} | {total_str} | {frac_str} | "
            f"{r['all_class_failure_count']} |"
        )

    lines += [
        "",
        "---",
        "",
        "## Recommendation for Decision 4c",
        "",
    ]

    if fractions:
        high_frac = buckets_frac.get(">=50%", 0)
        med_frac = buckets_frac.get(">=25%", 0)
        lines += [
            f"Based on the fraction analysis:",
            f"- {high_frac} structure(s) have >=50% of pocket residues absent from atom_site.",
            f"- {med_frac} structure(s) have >=25% of pocket residues absent from atom_site.",
            "",
            "**Suggested threshold to propose to Rishi:**",
            "Exclude structures where >=50% of cryptic pocket residues are absent from atom_site.",
            "Mask individual absent residues for structures below that threshold.",
            "This preserves training signal while removing structures where the pocket annotation",
            "is mostly unresolvable.",
        ]
    else:
        max_absent = max(absent_counts) if absent_counts else 0
        lines += [
            f"Fraction data unavailable (dataset.json not loaded). Raw counts only.",
            f"The worst-affected structure has {max_absent} absent pocket residues.",
            "",
            "**Suggested approach for Rishi:**",
            "Structures with 10+ absent pocket residues are likely poor training candidates —",
            f"there are {buckets_count['10+']} such structure(s). Review the per-structure table",
            "above and set a raw-count exclusion threshold (e.g. exclude if >10 absent residues),",
            "or run this script after loading dataset.json for fraction-based analysis.",
        ]

    lines += [
        "",
        "---",
        "",
        "## Provenance",
        "",
        "- Script: `scripts/residue_mapping_impact_analysis.py`",
        "- Source: `data/registries/residue_mapping_failures.json`",
        "- Governance: `docs/scientific_governance/06_LABELING_RULES.md`, `07_PREPROCESSING_AND_GRAPH_RULES.md`",
        "- Evidence status: verified for all counts from registry; inferred for threshold recommendation.",
        "- Machine-readable output: `data/registries/residue_mapping_per_structure_impact.json`",
    ]

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"Report written: {REPORT_PATH}")


if __name__ == "__main__":
    main()
