---
type: concept
status: active
created: 2026-05-27
updated: 2026-05-27
tags: [concept, leakage, homologs]
aliases: [Homolog Leakage]
confidence: high
evidence_status: verified
---

# Homolog Leakage

## Definition

Leakage caused by homologous proteins appearing across splits.

## Why it matters for GNN-PCNA

It can inflate performance and undermine PCNA final-claim holdout logic.

## How it can go wrong

Splitting by structure ID rather than protein system or sequence cluster.

## Governance rules that apply

`04_DATASET_CONSTRAINTS.md`, `05_SPLIT_PROTOCOL.md`, `31_DATA_LIFECYCLE_TRACKING.md`.

## Coding implications

Require homolog grouping and split audits before graph generation/training.

## Related entities

[[UniProt P12004]], [[PCNA]]

## Related raw crawl/source paths

`crawls/pcna-dataset-repositories-pass9/`, `crawls/pcna-gap-closure-datasets-tools-structures-pass6/`

## Related implementation files, if any

None canonical yet.

## Verification questions Codex should ask

- Are homologs grouped and blocked from crossing splits?

## Open questions

- Which tool, threshold, and database define homolog groups?

## Provenance

- Source paths: governance docs above
- Confidence level: high
- Date last updated: 2026-05-27
