---
type: concept
status: active
created: 2026-05-27
updated: 2026-05-27
tags: [concept, pockets]
aliases: [Cryptic Pockets]
confidence: medium
evidence_status: inferred
---

# Cryptic Pockets

## Definition

Pocket-like regions not necessarily apparent in a single static apo structure and requiring careful evidence before being treated as biologically meaningful.

## Why it matters for GNN-PCNA

Phase 2 focuses on residue-level candidate cryptic/allosteric/pocket-like regions, but labels and claims must be governed.

## How it can go wrong

Proxy ligand contacts, static pockets, or model scores can be mislabeled as true cryptic pockets.

## Governance rules that apply

`04_DATASET_CONSTRAINTS.md`, `06_LABELING_RULES.md`, `11_BIOLOGICAL_REALISM_RULES.md`, `14_CLAIM_POLICY.md`.

## Coding implications

Do not hard-code cryptic labels without an approved label definition and provenance.

## Related entities

[[PCNA]], [[PocketMiner]], [[CryptoBench]]

## Related raw crawl/source paths

`crawls/pcna-cryptic-pocket-gat-md-kb-final/`, `crawls/pcna-curated-official-tools-data-structures-pass8/`

## Related implementation files, if any

None canonical yet.

## Verification questions Codex should ask

- What is the label source?
- Is the label residue-level?
- What leakage controls apply?

## Open questions

- Which source defines Phase 2 cryptic-pocket labels?

## Provenance

- Source paths: governance docs above; crawl paths above
- Confidence level: medium
- Date last updated: 2026-05-27
