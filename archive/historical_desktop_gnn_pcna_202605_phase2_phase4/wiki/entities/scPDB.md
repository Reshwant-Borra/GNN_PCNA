---
type: entity
status: active
created: 2026-05-27
updated: 2026-05-27
tags: [entity, database, binding-sites]
aliases: [scPDB]
confidence: medium
evidence_status: inferred
---

# scPDB

## What it is

A protein-ligand binding-site database/source lead.

## Why it matters for GNN-PCNA

May provide binding-site context or dataset leads, but requires governance review before use.

## How Codex should use this entity

Check source availability, license, schema, residue mapping, and split risks before using.

## What Codex must NOT overclaim

Do not treat scPDB ligand sites as cryptic-pocket labels without an approved label definition.

## Related governance docs

- `docs/scientific_governance/04_DATASET_CONSTRAINTS.md`
- `docs/scientific_governance/06_LABELING_RULES.md`
- `docs/scientific_governance/29_BENCHMARK_LIMITATIONS.md`

## Related wiki concepts

- [[Proxy Ligand Labels]]
- [[Dataset Registry]]
- [[Label Definition]]

## Related raw crawl/source paths

- `crawls/pcna-curated-official-tools-data-structures-pass8/SOURCE_INDEX.md`

## Related V1 references, if any

None canonical.

## Known risks / failure modes

Proxy-label misuse and benchmark contamination.

## Open questions

- Is scPDB in scope for training, evaluation, or background only?

## Provenance

- Source paths: governance docs above; crawl path above
- Confidence level: medium
- Date last updated: 2026-05-27
