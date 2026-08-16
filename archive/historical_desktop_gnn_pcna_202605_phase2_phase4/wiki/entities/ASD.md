---
type: entity
status: active
created: 2026-05-27
updated: 2026-05-27
tags: [entity, database, allostery]
aliases: [ASD, Allosteric Database]
confidence: medium
evidence_status: inferred
---

# ASD

## What it is

Allosteric Database source lead for allosteric proteins, modulators, and allosteric-site data.

## Why it matters for GNN-PCNA

May provide allosteric context or candidate benchmark leads.

## How Codex should use this entity

Use after checking schema, version, coverage, and whether entries map to Phase 2 scope.

## What Codex must NOT overclaim

Do not treat allosteric-database context as proof of PCNA predicted-site mechanism.

## Related governance docs

- `docs/scientific_governance/04_DATASET_CONSTRAINTS.md`
- `docs/scientific_governance/11_BIOLOGICAL_REALISM_RULES.md`
- `docs/scientific_governance/14_CLAIM_POLICY.md`

## Related wiki concepts

- [[Allosteric Sites]]
- [[Scientific Claim Control]]

## Related raw crawl/source paths

- `crawls/pcna-curated-official-tools-data-structures-pass8/SOURCE_INDEX.md`

## Related V1 references, if any

None canonical.

## Known risks / failure modes

Allostery overclaim without mechanism or PCNA-specific evidence.

## Open questions

- Are any ASD entries relevant to human PCNA?

## Provenance

- Source paths: governance docs above; crawl path above
- Confidence level: medium
- Date last updated: 2026-05-27
