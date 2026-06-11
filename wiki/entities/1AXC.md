---
type: entity
status: active
created: 2026-06-10
updated: 2026-06-10
tags: [entity, pdb, pcna, structure, phase5]
aliases: [1AXC, PDB 1AXC]
confidence: high
evidence_status: verified
---

# 1AXC

## What it is

PDB 1AXC is the human PCNA-p21 peptide complex used as the official Phase 5 Wave 1
starting structure for `1axc_apo_from_p21`.

## Why it matters for GNN-PCNA

1AXC provides the Wave 1 PCNA trimer for Tier 1A candidate windows `239-243`,
`28-32`, `206-210`, and the interface-adjacent control `134-138`.

## Phase 5 Wave 1 Mapping

- Biological assembly 1 is the deposited hexameric complex: PCNA trimer A/C/E plus
  p21 peptide chains B/D/F.
- PCNA chains retained for `1axc_apo_from_p21`: A, C, E.
- p21 peptide chains to remove before future setup: B, D, F.
- PCNA canonical numbering maps to UniProt P12004 residues 1-261 by `struct_ref_seq`.
- p21 peptide chains map to UniProt P38936 residues 139-160.
- Candidate windows `239-243`, `28-32`, `206-210`, and `134-138` are complete on all
  three PCNA chains A/C/E.
- Apo-from-p21 is a setup transformation, not a clean apo crystal structure.

## How Codex should use this entity

Use 1AXC only through the Phase 5 preparation audit and fail-closed launch checks.
Future launch must record p21-chain removal, prepared-coordinate hashes, trimer-integrity
checks, and IDCL/front-face geometry checks before production.

## What Codex must NOT overclaim

Do not treat `1axc_apo_from_p21` as an experimentally observed apo structure. Do not make
MD, mechanism, novelty, druggability, therapeutic, or clinical claims from this setup.

## Related governance docs

- `docs/scientific_governance/12_PCNA_SPECIFIC_CHECKS.md`
- `docs/scientific_governance/13_MD_VALIDATION_RULES.md`
- `docs/scientific_governance/14_CLAIM_POLICY.md`
- `docs/scientific_governance/15_PROVENANCE_AND_REPRODUCIBILITY.md`

## Provenance

- Source paths: `reports/phase5/1axc_preparation_audit_20260610.md`,
  `data/registries/phase5_wave1_preparation_audit_20260610.json`,
  `data/raw_intake/pcna_structures/1AXC.cif`,
  `data/raw_intake/pcna_structures/1AXC_metadata.json`
- Governance paths: `docs/scientific_governance/12_PCNA_SPECIFIC_CHECKS.md`,
  `docs/scientific_governance/13_MD_VALIDATION_RULES.md`
- Confidence level: high
- Date last updated: 2026-06-10
- Evidence status: verified
