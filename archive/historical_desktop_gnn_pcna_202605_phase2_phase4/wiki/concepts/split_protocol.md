---
type: concept
status: active
created: 2026-05-27
updated: 2026-05-27
tags: [concept, splits, protocol]
aliases: [Split Protocol]
confidence: high
evidence_status: verified
---

# Split Protocol

## Definition

Rules for leakage-resistant train/validation/test splits.

## Why it matters for GNN-PCNA

Invalid splits invalidate metrics and downstream claims.

## How it can go wrong

Splitting by row or structure ID rather than protein system, homolog group, and apo/holo group.

## Governance rules that apply

`05_SPLIT_PROTOCOL.md`, `04_DATASET_CONSTRAINTS.md`, `29_BENCHMARK_LIMITATIONS.md`.

## Coding implications

Implement split generation and audits before graph generation/training.

## Related entities

[[CryptoBench]], [[PCNA]], [[8GLA]]

## Related raw crawl/source paths

`crawls/pcna-dataset-repositories-pass9/`

## Related implementation files, if any

None canonical yet.

## Verification questions Codex should ask

- Are PCNA final-claim structures isolated?
- Are homolog and apo/holo groups held together?

## Open questions

- Human split-freeze record is not yet present.

## Provenance

- Source paths: governance docs above
- Confidence level: high
- Date last updated: 2026-05-27
