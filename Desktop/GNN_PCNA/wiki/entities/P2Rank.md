---
type: entity
status: active
created: 2026-05-27
updated: 2026-05-27
tags: [entity, tool, baseline]
aliases: [P2Rank, PRANK]
confidence: medium
evidence_status: inferred
---

# P2Rank

## What it is

A protein binding-site prediction tool and possible baseline.

## Why it matters for GNN-PCNA

Could be used for same-split baseline comparison or binding-site context.

## How Codex should use this entity

Use only with documented version, inputs, outputs, and mapping to Phase 2 residue labels.

## What Codex must NOT overclaim

Do not treat P2Rank scores as evidence of cryptic-pocket validation or PCNA mechanism.

## Related governance docs

- `docs/scientific_governance/10_BASELINE_REQUIREMENTS.md`
- `docs/scientific_governance/15_PROVENANCE_AND_REPRODUCIBILITY.md`
- `docs/scientific_governance/28_NULL_HYPOTHESIS_BASELINES.md`

## Related wiki concepts

- [[Baseline Comparison]]
- [[Residue Level Prediction]]

## Related raw crawl/source paths

- `crawls/pcna-curated-official-tools-data-structures-pass8/SOURCE_INDEX.md`
- `crawls/pcna-gap-closure-datasets-tools-structures-pass6/SOURCE_INDEX.md`

## Related V1 references, if any

Historical only if present.

## Known risks / failure modes

Baseline mismatch and unregistered output provenance.

## Open questions

- Is P2Rank required or optional for Phase 2 baseline gates?

## Provenance

- Source paths: governance docs above; crawl paths above
- Confidence level: medium
- Date last updated: 2026-05-27
