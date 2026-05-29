---
type: entity
status: active
created: 2026-05-27
updated: 2026-05-27
tags: [entity, database, binding-affinity]
aliases: [PDBbind]
confidence: medium
evidence_status: inferred
---

# PDBbind

## What it is

A protein-ligand binding affinity database/source lead.

## Why it matters for GNN-PCNA

May provide binding-site or protein-ligand context, but may not match Phase 2 residue-level cryptic/allosteric objectives.

## How Codex should use this entity

Use only after explicit governance review of scope, labels, split risks, and license.

## What Codex must NOT overclaim

Do not use affinity data as direct evidence for cryptic-pocket or PCNA mechanism claims.

## Related governance docs

- `docs/scientific_governance/04_DATASET_CONSTRAINTS.md`
- `docs/scientific_governance/06_LABELING_RULES.md`
- `docs/scientific_governance/29_BENCHMARK_LIMITATIONS.md`

## Related wiki concepts

- [[Proxy Ligand Labels]]
- [[Dataset Registry]]

## Related raw crawl/source paths

- `crawls/pcna-curated-official-tools-data-structures-pass8/SOURCE_INDEX.md`

## Related V1 references, if any

None canonical.

## Known risks / failure modes

Scope drift into affinity prediction and drug-discovery framing.

## Open questions

- Is PDBbind excluded, background-only, or a governed auxiliary source?

## Provenance

- Source paths: governance docs above; crawl path above
- Confidence level: medium
- Date last updated: 2026-05-27
