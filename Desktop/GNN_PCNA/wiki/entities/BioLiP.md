---
type: entity
status: active
created: 2026-05-27
updated: 2026-05-27
tags: [entity, database, binding-sites]
aliases: [BioLiP, BioLiP2]
confidence: medium
evidence_status: inferred
---

# BioLiP

## What it is

A biologically relevant ligand-protein binding database/source lead.

## Why it matters for GNN-PCNA

Potential binding-site annotation context, subject to label and leakage governance.

## How Codex should use this entity

Use only after confirming version, license, schema, download method, chain/residue mapping, and label definition.

## What Codex must NOT overclaim

Do not equate ligand-contact annotations with cryptic-pocket truth.

## Related governance docs

- `docs/scientific_governance/04_DATASET_CONSTRAINTS.md`
- `docs/scientific_governance/06_LABELING_RULES.md`
- `docs/scientific_governance/15_PROVENANCE_AND_REPRODUCIBILITY.md`

## Related wiki concepts

- [[Proxy Ligand Labels]]
- [[Label Definition]]
- [[Dataset Registry]]

## Related raw crawl/source paths

- `crawls/pcna-curated-official-tools-data-structures-pass8/SOURCE_INDEX.md`

## Related V1 references, if any

None canonical.

## Known risks / failure modes

Proxy label overclaim and chain/residue mapping mismatch.

## Open questions

- Is BioLiP in scope for Phase 2 labels or only background context?

## Provenance

- Source paths: governance docs above; crawl path above
- Confidence level: medium
- Date last updated: 2026-05-27
