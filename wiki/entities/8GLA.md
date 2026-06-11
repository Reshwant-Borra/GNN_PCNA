---
type: entity
status: active
created: 2026-05-27
updated: 2026-06-10
tags: [entity, pdb, pcna, structure]
aliases: [8GLA, PDB 8GLA]
confidence: high
evidence_status: verified
---

# 8GLA

## What it is

PDB 8GLA is the co-crystal structure of cancer-associated human PCNA bound to the
AOH1996 derivative AOH1996-1LE, ligand code ZQZ.

## Why it matters for GNN-PCNA

8GLA is the official Phase 5 Wave 1 positive-control starting structure for
`8gla_holo_zqz` and `8gla_apo_from_holo`. It remains a positive-control/sanity-check
system only and cannot validate novel-site predictions.

## Phase 5 Wave 1 Mapping

- Official Wave 1 biological assembly: RCSB biological assembly 1.
- Wave 1 PCNA auth chains: A, B, C.
- Deposited chain D is excluded from Wave 1 because it belongs to deposited assembly 2.
- Canonical numbering: deposited PCNA chains map to UniProt P12004 residues 1-261 by
  `struct_ref_seq`.
- Candidate window `118-122`: complete on chains A and B; chain C is missing residue
  122.
- ZQZ: six Assembly 1 ligand instances assigned to auth chains A and B in deposited
  coordinates; no ZQZ contact within 4.5 A was detected on chain C in the preparation
  audit.
- Structural caveat: 3.77 A resolution, below the project's <=3.5 A quality threshold;
  authorized only as a force-included positive control.

## How Codex should use this entity

Use only through the Phase 5 preparation audit and fail-closed launch checks. Do not use
8GLA for novel-site claims, tuning, model selection, or production launch before explicit
launch authorization and audited ZQZ parameters exist.

## What Codex must NOT overclaim

Do not treat recovery or overlap with 8GLA as independent validation if the structure influenced tuning, labels, or model selection.

## Related governance docs

- `docs/scientific_governance/05_SPLIT_PROTOCOL.md`
- `docs/scientific_governance/12_PCNA_SPECIFIC_CHECKS.md`
- `docs/scientific_governance/25_BIOLOGICAL_DATA_SANITY_REVIEW.md`

## Related wiki concepts

- [[Apo Holo Leakage]]
- [[Biological Realism]]
- [[Proxy Ligand Labels]]

## Related raw crawl/source paths

- `crawls/pcna-cryptic-pocket-gat-md-kb-final/SOURCE_INDEX.md`
- `crawls/_probe2/raw/pdb/`

## Related V1 references, if any

Historical only if present.

## Known risks / failure modes

Positive-control leakage and chain/ligand mapping errors.

## Open questions

- None for official Wave 1 assembly/chain/ligand mapping. Future launch still needs
  audited ZQZ parameters and explicit MD launch authorization.

## Provenance

- Source paths: `reports/phase5/8gla_preparation_audit_20260610.md`,
  `data/registries/phase5_wave1_preparation_audit_20260610.json`,
  `data/raw_intake/pcna_structures/8GLA.cif`,
  `data/raw_intake/pcna_structures/8GLA_metadata.json`,
  `data/raw_intake/pcna_structures/8GLA_assembly1.json`,
  `docs/scientific_governance/12_PCNA_SPECIFIC_CHECKS.md`,
  `docs/scientific_governance/13_MD_VALIDATION_RULES.md`
- Confidence level: high
- Date last updated: 2026-06-10
- Evidence status: verified
