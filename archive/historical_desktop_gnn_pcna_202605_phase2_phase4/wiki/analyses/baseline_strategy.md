---
type: analysis
status: active
created: 2026-05-27
updated: 2026-05-27
tags: [baselines, evaluation]
aliases: [Baseline Strategy]
confidence: high
evidence_status: verified
---

# Baseline Strategy

## Strategy

No model value or superiority claim without fair same-split baselines and null baselines.

## Candidate baselines

[[fpocket]], [[P2Rank]], [[PocketMiner]], null/random/heuristic baselines, and any approved benchmark-specific methods.

## Required controls

Same split, same label mapping, provenance, output manifests, and honest reporting if baselines match or beat GNN.

## Governance

`10_BASELINE_REQUIREMENTS.md`, `28_NULL_HYPOTHESIS_BASELINES.md`, `09_EVALUATION_PROTOCOL.md`.

## Provenance

- Source paths: governance docs above; `crawls/pcna-curated-official-tools-data-structures-pass8/`
- Confidence level: high for required process; medium for candidate list
- Date last updated: 2026-05-27
