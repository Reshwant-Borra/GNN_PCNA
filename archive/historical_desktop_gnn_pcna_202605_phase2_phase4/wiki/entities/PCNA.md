---
type: entity
status: active
created: 2026-05-27
updated: 2026-05-27
tags: [entity, pcna, protein]
aliases: [PCNA, Proliferating Cell Nuclear Antigen]
confidence: medium
evidence_status: inferred
---

# PCNA

## What it is

Proliferating cell nuclear antigen, the central protein context for Phase 2.

## Why it matters for GNN-PCNA

Phase 2 aims to build a governed residue-level workflow for PCNA candidate cryptic, allosteric, or pocket-like region prediction and auditing.

## How Codex should use this entity

Use PCNA pages to route to PCNA-specific governance, structures, UniProt records, known interfaces, and crawl source paths before coding PCNA-specific logic.

## What Codex must NOT overclaim

Do not claim therapeutic validation, confirmed mechanism, clinical value, druggability, or new target discovery from PCNA prediction, MD, docking, or cancer relevance.

## Related governance docs

- `docs/scientific_governance/11_BIOLOGICAL_REALISM_RULES.md`
- `docs/scientific_governance/12_PCNA_SPECIFIC_CHECKS.md`
- `docs/scientific_governance/14_CLAIM_POLICY.md`
- `docs/scientific_governance/24_PROJECT_SCOPE.md`

## Related wiki concepts

- [[Biological Realism]]
- [[Cryptic Pockets]]
- [[Allosteric Sites]]
- [[Scientific Claim Control]]

## Related raw crawl/source paths

- `crawls/pcna-cryptic-pocket-gat-md-kb-final/SOURCE_INDEX.md`
- `crawls/pcna-gap-closure-datasets-tools-structures-pass6/SOURCE_INDEX.md`
- `crawls/_probe2/raw/uniprot/`

## Related V1 references, if any

V1 is historical reference only. Local V1 path is not confirmed in this checkout.

## Known risks / failure modes

PCNA-specific leakage, known-interface novelty overclaims, chain mapping errors, and cancer/therapy overreach.

## Open questions

- Which PCNA structures are final holdout versus positive controls?
- What exact PCNA chain mapping table is approved?

## Provenance

- Source paths: governance docs above; crawl paths above
- Confidence level: medium
- Date last updated: 2026-05-27
