---
type: concept
status: active
created: 2026-05-27
updated: 2026-05-27
tags: [concept, baselines, evaluation]
aliases: [Baseline Comparison]
confidence: high
evidence_status: verified
---

# Baseline Comparison

## Definition

Governed comparison against required null, geometry, heuristic, and method baselines.

## Why it matters for GNN-PCNA

No model value or superiority claim is allowed without fair baselines.

## How it can go wrong

Comparing only to random, comparing to literature numbers, or running baselines on different splits.

## Governance rules that apply

`10_BASELINE_REQUIREMENTS.md`, `28_NULL_HYPOTHESIS_BASELINES.md`, `09_EVALUATION_PROTOCOL.md`.

## Coding implications

Baseline scripts must use the same registered splits and provenance as GNN evaluation.

## Related entities

[[fpocket]], [[P2Rank]], [[PocketMiner]]

## Related raw crawl/source paths

`crawls/pcna-gap-closure-datasets-tools-structures-pass6/`, `crawls/pcna-curated-official-tools-data-structures-pass8/`

## Related implementation files, if any

None canonical yet.

## Verification questions Codex should ask

- Which baselines are required before claims?
- Are outputs mapped to the same residue labels?

## Open questions

- MVP baseline set is not yet frozen.

## Provenance

- Source paths: governance docs above
- Confidence level: high
- Date last updated: 2026-05-27
