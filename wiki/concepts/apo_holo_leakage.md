---
type: concept
status: active
created: 2026-05-27
updated: 2026-05-27
tags: [concept, leakage, splits]
aliases: [Apo Holo Leakage, Apo/Holo Leakage]
confidence: high
evidence_status: verified
---

# Apo Holo Leakage

## Definition

Leakage where apo and holo forms, ligand variants, or conformations of the same protein system cross splits.

## Why it matters for GNN-PCNA

It can make a model appear to generalize while memorizing the same protein system.

## How it can go wrong

Using benchmark-provided splits without grouping apo/holo pairs.

## Governance rules that apply

`04_DATASET_CONSTRAINTS.md`, `05_SPLIT_PROTOCOL.md`, `29_BENCHMARK_LIMITATIONS.md`.

## Coding implications

Build system-level grouping before graph generation and training.

## Related entities

[[8GLA]], [[PCNA]], [[CryptoBench]]

## Related raw crawl/source paths

`crawls/pcna-dataset-repositories-pass9/`, `crawls/pcna-cryptic-pocket-gat-md-kb-final/`

## Related implementation files, if any

None canonical yet.

## Verification questions Codex should ask

- Are all structures for the same system assigned to one split?

## Open questions

- What exact apo/holo grouping table will Phase 2 use?

## Provenance

- Source paths: governance docs above
- Confidence level: high
- Date last updated: 2026-05-27
