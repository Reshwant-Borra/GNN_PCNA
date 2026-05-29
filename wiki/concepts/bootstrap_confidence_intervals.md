---
type: concept
status: active
created: 2026-05-27
updated: 2026-05-27
tags: [concept, statistics, metrics]
aliases: [Bootstrap Confidence Intervals]
confidence: high
evidence_status: verified
---

# Bootstrap Confidence Intervals

## Definition

Uncertainty intervals estimated by resampling proteins or other approved units.

## Why it matters for GNN-PCNA

Prevents overinterpreting unstable metrics from small or imbalanced datasets.

## How it can go wrong

Resampling residues instead of proteins can understate uncertainty.

## Governance rules that apply

`09_EVALUATION_PROTOCOL.md`, `28_NULL_HYPOTHESIS_BASELINES.md`, `36_PUBLICATION_READINESS.md`.

## Coding implications

Use the governance-approved resampling unit and preserve seeds/configs.

## Related entities

[[CryptoBench]]

## Related raw crawl/source paths

`crawls/pcna-gap-closure-datasets-tools-structures-pass6/`

## Related implementation files, if any

None canonical yet.

## Verification questions Codex should ask

- What unit is bootstrapped?
- Are seeds and sample counts recorded?

## Open questions

- Approved bootstrap parameters are not recorded in wiki yet.

## Provenance

- Source paths: governance docs above
- Confidence level: high
- Date last updated: 2026-05-27
