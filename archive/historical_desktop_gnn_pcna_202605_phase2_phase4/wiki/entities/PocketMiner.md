---
type: entity
status: active
created: 2026-05-27
updated: 2026-05-27
tags: [entity, method, cryptic-pockets]
aliases: [PocketMiner]
confidence: medium
evidence_status: inferred
---

# PocketMiner

## What it is

A cryptic-pocket prediction method/source lead in the Phase 2 crawl corpus.

## Why it matters for GNN-PCNA

Potential baseline, label-source context, or benchmark comparison point for cryptic-pocket prediction.

## How Codex should use this entity

Use as a candidate method or dataset lead only after checking official paper/repo/data availability and same-split baseline rules.

## What Codex must NOT overclaim

Do not compare Phase 2 GNN metrics to published PocketMiner numbers as proof of superiority unless run under a governed same-split protocol.

## Related governance docs

- `docs/scientific_governance/10_BASELINE_REQUIREMENTS.md`
- `docs/scientific_governance/29_BENCHMARK_LIMITATIONS.md`

## Related wiki concepts

- [[Cryptic Pockets]]
- [[Baseline Comparison]]
- [[Dataset Registry]]

## Related raw crawl/source paths

- `crawls/pcna-curated-official-tools-data-structures-pass8/SOURCE_INDEX.md`
- `crawls/pcna-cryptic-pocket-gat-md-kb-final/SOURCE_INDEX.md`

## Related V1 references, if any

Historical only if present.

## Known risks / failure modes

Baseline mismatch, label mismatch, and leakage if used without split audit.

## Open questions

- Can PocketMiner be run on the exact Phase 2 split?

## Provenance

- Source paths: governance docs above; crawl paths above
- Confidence level: medium
- Date last updated: 2026-05-27
