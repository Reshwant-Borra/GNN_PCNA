---
type: analysis-report
status: complete
created: 2026-05-27
decisions_applied: [4a, 4b, 4c, 4d]
---

# Label Generation Report — Phase 2

**Policy:** Positive-unlabeled (PU) learning. Positives from `apo_pocket_selection`;
unlisted residues = background/unlabeled; absent residues = masked from loss.
**Governance:** `docs/scientific_governance/06_LABELING_RULES.md`

---

## Summary

| Metric | Value |
|---|---|
| Structures labeled | 1101 |
| Structures excluded | 6 |
| Structures failed (CIF parse error) | 0 |
| Total positive labels | 16335 |
| Total masked labels | 3704 |
| Total Class 1 remaps (4a) | 0 |

---

## Excluded Structures

| Apo PDB | Reason | Policy |
|---|---|---|
| 1lx7 | class4c_high_mask_fraction | Decision 4c |
| 2b23 | class3_wrong_chain | Decision 4d |
| 4gpi | class3_wrong_chain | Decision 4d |
| 5e0v | pcna_exact_contamination | Decision decision_2 |
| 8hc1 | class3_wrong_chain | Decision 4d |
| 8oqp | class3_wrong_chain | Decision 4d |

---

## Class 1 Remaps (Decision 4a)

Total remaps: 0

Pocket selection tokens that matched label_seq_id but not auth_seq_id.
These are valid residues; they were just referenced by the wrong numbering scheme.

---

## Provenance

- Source: CryptoBench `dataset.json` + CIF files from `data/raw_intake/cryptobench/`
- Decisions: 4a (remap), 4b (mask), 4c (exclude 1lx7), 4d (exclude wrong-chain records)
- Governance: `docs/scientific_governance/06_LABELING_RULES.md`
- Evidence status: verified (all counts from local CIF parsing and approved registries)
- Generated: 2026-05-27T23:43:27.241462
