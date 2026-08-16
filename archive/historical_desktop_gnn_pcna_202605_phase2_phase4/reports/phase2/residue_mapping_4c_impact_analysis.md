---
type: analysis-report
status: complete
created: 2026-05-27
informs: Decision 4c — residue_mapping_resolution_policy.md
---

# Residue Mapping Class 2 Per-Structure Impact Analysis

**Decision this informs:** 4c — whether structures with a high fraction of
masked pocket residues should be excluded entirely rather than masked.

**Scope:** Cryptic records only, `residue_token_absent_from_atom_site` failures only.
**Source:** `data/registries/residue_mapping_failures.json`
**Dataset total-token source:** `data\raw_intake\cryptobench\metadata_files\66c328c87352852f68dbeac4_dataset.json`

---

## Top-Line Numbers

| Metric | Value |
|---|---|
| Total Class 2 cryptic tokens (absent from atom_site) | 96 |
| Unique apo structures with >=1 Class 2 cryptic failure | 28 |
| Unique apo structures with any cryptic failure | 53 |
| Fraction of all cryptic apos affected by Class 2 | 28/53 = 52.8% |

## Distribution by Absent-Residue Count per Structure

| Structures with N+ absent cryptic pocket residues | Count |
|---|---|
| >=1 absent residues | 28 |
| >=2+ absent residues | 17 |
| >=5+ absent residues | 7 |
| >=10+ absent residues | 3 |
| >=20+ absent residues | 0 |

## Distribution by Fraction of Pocket Residues Masked

| Threshold | Structures affected |
|---|---|
| >=10% of pocket residues masked | 16 |
| >=25% of pocket residues masked | 4 |
| >=50% of pocket residues masked | 1 |
| >=75% of pocket residues masked | 1 |

## Per-Structure Table (sorted by absent count, descending)

| Apo PDB ID | Fold | UniProt | Absent (Class 2) | Total Pocket Tokens | Fraction Masked | All-Class Failures |
|---|---|---|---|---|---|---|
| 1lx7 | train-2 | P12758 | 15 | 19 | 79.0% | 15 |
| 2b23 | train-2 | P03372 | 13 | 64 | 20.3% | 13 |
| 4f5h | train-2 | P00509 | 10 | 22 | 45.5% | 12 |
| 2qlr | train-0 | Q8N5Z0 | 7 | 70 | 10.0% | 8 |
| 4yt8 | train-0 | Q58734 | 6 | 42 | 14.3% | 6 |
| 7qni | train-0 | P0A9S1 | 6 | 50 | 12.0% | 6 |
| 4c6b | train-3 | P27708 | 5 | 21 | 23.8% | 5 |
| 3zo8 | train-0 | P19080 | 4 | 15 | 26.7% | 4 |
| 1h3g | train-3 | Q8KKG0 | 3 | 20 | 15.0% | 3 |
| 1esw | train-1 | O87172 | 2 | 12 | 16.7% | 2 |
| 2hq8 | train-2 | C9V488 | 2 | 22 | 9.1% | 2 |
| 4ei8 | train-1 | Q74P24 | 2 | 25 | 8.0% | 2 |
| 4fl8 | train-0 | P03367 | 2 | 15 | 13.3% | 2 |
| 5igh | test | Q47396 | 2 | 24 | 8.3% | 2 |
| 6q7q | train-1 | O58216 | 2 | 9 | 22.2% | 2 |
| 7alf | train-2 | A0A0S4TLR1 | 2 | 5 | 40.0% | 2 |
| 7cif | train-2 | A0A0G4DBU7 | 2 | 25 | 8.0% | 2 |
| 1pt7 | train-0 | P69902 | 1 | 12 | 8.3% | 1 |
| 1rxd | train-0 | Q93096 | 1 | 7 | 14.3% | 1 |
| 2e1c | train-0 | O59188 | 1 | 17 | 5.9% | 1 |
| 2yzg | train-3 | Q5SHZ3 | 1 | 8 | 12.5% | 1 |
| 3db3 | train-1 | Q96T88 | 1 | 9 | 11.1% | 1 |
| 3qas | train-1 | P60472 | 1 | 61 | 1.6% | 1 |
| 4ekf | train-1 | P03252 | 1 | 12 | 8.3% | 1 |
| 4oyz | train-2 | Q96PN6 | 1 | 35 | 2.9% | 2 |
| 6l61 | train-2 | M1HE54 | 1 | 25 | 4.0% | 1 |
| 6xl4 | train-2 | P00533 | 1 | 58 | 1.7% | 1 |
| 7c48 | test | P96356 | 1 | 23 | 4.3% | 1 |

---

## Recommendation for Decision 4c

Based on the fraction analysis:
- 1 structure(s) have >=50% of pocket residues absent from atom_site.
- 4 structure(s) have >=25% of pocket residues absent from atom_site.

**Suggested threshold to propose to Rishi:**
Exclude structures where >=50% of cryptic pocket residues are absent from atom_site.
Mask individual absent residues for structures below that threshold.
This preserves training signal while removing structures where the pocket annotation
is mostly unresolvable.

---

## Provenance

- Script: `scripts/residue_mapping_impact_analysis.py`
- Source: `data/registries/residue_mapping_failures.json`
- Governance: `docs/scientific_governance/06_LABELING_RULES.md`, `07_PREPROCESSING_AND_GRAPH_RULES.md`
- Evidence status: verified for all counts from registry; inferred for threshold recommendation.
- Machine-readable output: `data/registries/residue_mapping_per_structure_impact.json`