---
type: concept
status: active
created: 2026-05-27
updated: 2026-05-27
tags: [concept, leakage, splits]
aliases: [Sequence Split Leakage]
confidence: high
evidence_status: verified
---

# Sequence Split Leakage

## Definition

Train/validation/test contamination caused by related or identical protein sequences crossing splits.

## Why it matters for GNN-PCNA

It can inflate metrics and invalidate generalization claims.

## How it can go wrong

Random splits or benchmark splits can place homologous proteins in different splits.

## Governance rules that apply

`04_DATASET_CONSTRAINTS.md`, `05_SPLIT_PROTOCOL.md`, `29_BENCHMARK_LIMITATIONS.md`.

## Coding implications

Splits must be grouped by sequence identity/family as approved, with audit artifacts.

## Related entities

[[UniProt P12004]], [[CryptoBench]]

## Related raw crawl/source paths

`crawls/pcna-dataset-repositories-pass9/`, `crawls/pcna-gap-closure-datasets-tools-structures-pass6/`

## Related implementation files, if any

None canonical yet.

## Verification questions Codex should ask

- What sequence clustering tool and threshold are approved?
- Are PCNA homologs isolated?

## Open questions

- The approved clustering threshold is not recorded in the wiki yet.

## Provenance

- Source paths: governance docs above
- Confidence level: high
- Date last updated: 2026-05-27
