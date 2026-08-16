---
type: concept
status: active
created: 2026-05-27
updated: 2026-05-27
tags: [concept, provenance, reproducibility]
aliases: [Provenance Tracking]
confidence: high
evidence_status: verified
---

# Provenance Tracking

## Definition

Recording source paths, hashes, versions, configs, decisions, and artifact lineage.

## Why it matters for GNN-PCNA

Without provenance, Phase 2 artifacts cannot support training, evaluation, MD interpretation, or claims.

## How it can go wrong

Stale V1 graphs, unregistered crawls, missing hashes, or reports with no source trace.

## Governance rules that apply

`01_SOURCE_OF_TRUTH.md`, `15_PROVENANCE_AND_REPRODUCIBILITY.md`, `31_DATA_LIFECYCLE_TRACKING.md`.

## Coding implications

Make scripts fail closed when required manifests or hashes are missing.

## Related entities

[[PCNA]], [[CryptoBench]], [[BioLiP]]

## Related raw crawl/source paths

All used `crawls/` paths.

## Related implementation files, if any

None canonical yet.

## Verification questions Codex should ask

- Can every artifact be traced to registered inputs?

## Open questions

- What exact Phase 2 manifest schema will be implemented?

## Provenance

- Source paths: governance docs above
- Confidence level: high
- Date last updated: 2026-05-27
