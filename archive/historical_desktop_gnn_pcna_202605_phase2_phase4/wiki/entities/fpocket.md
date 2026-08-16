---
type: entity
status: active
created: 2026-05-27
updated: 2026-05-27
tags: [entity, tool, baseline]
aliases: [fpocket, MDpocket]
confidence: medium
evidence_status: inferred
---

# fpocket

## What it is

A geometry-based pocket detection tool and possible baseline or MDpocket-related context.

## Why it matters for GNN-PCNA

May provide baseline pocket predictions or pocket-volume/dynamics context.

## How Codex should use this entity

Use only with documented version, inputs, outputs, residue-mapping method, and same-split comparison plan.

## What Codex must NOT overclaim

Do not treat fpocket or MDpocket output as cryptic-pocket ground truth or PCNA validation.

## Related governance docs

- `docs/scientific_governance/10_BASELINE_REQUIREMENTS.md`
- `docs/scientific_governance/13_MD_VALIDATION_RULES.md`
- `docs/scientific_governance/15_PROVENANCE_AND_REPRODUCIBILITY.md`

## Related wiki concepts

- [[Baseline Comparison]]
- [[MD Validation Limits]]

## Related raw crawl/source paths

- `crawls/pcna-curated-official-tools-data-structures-pass8/SOURCE_INDEX.md`
- `crawls/pcna-gap-closure-datasets-tools-structures-pass6/SOURCE_INDEX.md`

## Related V1 references, if any

Historical only if present.

## Known risks / failure modes

Output-to-residue mapping errors and baseline provenance gaps.

## Open questions

- Is fpocket required for MVP baselines?

## Provenance

- Source paths: governance docs above; crawl paths above
- Confidence level: medium
- Date last updated: 2026-05-27
