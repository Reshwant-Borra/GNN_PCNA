---
type: entity
status: active
created: 2026-05-27
updated: 2026-05-27
tags: [entity, pdb, pcna, structure]
aliases: [8GLA, PDB 8GLA]
confidence: medium
evidence_status: inferred
---

# 8GLA

## What it is

A PDB structure lead associated with PCNA/AOH1996 context in the crawl corpus.

## Why it matters for GNN-PCNA

Potential positive-control or PCNA structural context, subject to strict split and leakage controls.

## How Codex should use this entity

Use only after checking official PDB metadata, chain mapping, ligand status, and governance.

## What Codex must NOT overclaim

Do not treat recovery or overlap with 8GLA as independent validation if the structure influenced tuning, labels, or model selection.

## Related governance docs

- `docs/scientific_governance/05_SPLIT_PROTOCOL.md`
- `docs/scientific_governance/12_PCNA_SPECIFIC_CHECKS.md`
- `docs/scientific_governance/25_BIOLOGICAL_DATA_SANITY_REVIEW.md`

## Related wiki concepts

- [[Apo Holo Leakage]]
- [[Biological Realism]]
- [[Proxy Ligand Labels]]

## Related raw crawl/source paths

- `crawls/pcna-cryptic-pocket-gat-md-kb-final/SOURCE_INDEX.md`
- `crawls/_probe2/raw/pdb/`

## Related V1 references, if any

Historical only if present.

## Known risks / failure modes

Positive-control leakage and chain/ligand mapping errors.

## Open questions

- What is the official 8GLA chain/ligand mapping used by Phase 2?

## Provenance

- Source paths: governance docs above; crawl paths above
- Confidence level: medium
- Date last updated: 2026-05-27
