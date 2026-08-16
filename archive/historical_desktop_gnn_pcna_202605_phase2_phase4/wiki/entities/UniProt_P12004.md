---
type: entity
status: active
created: 2026-05-27
updated: 2026-05-27
tags: [entity, uniprot, pcna]
aliases: [UniProt P12004, P12004]
confidence: medium
evidence_status: inferred
---

# UniProt P12004

## What it is

The UniProt accession context for human PCNA, subject to verification against official UniProt metadata.

## Why it matters for GNN-PCNA

Useful for protein identity, sequence, isoform, homolog grouping, and PCNA-specific mapping.

## How Codex should use this entity

Use official UniProt data for canonical sequence and identity checks. Crawl metadata is only a pointer.

## What Codex must NOT overclaim

Do not infer biological mechanism, target validity, or clinical relevance from UniProt annotation alone.

## Related governance docs

- `docs/scientific_governance/04_DATASET_CONSTRAINTS.md`
- `docs/scientific_governance/05_SPLIT_PROTOCOL.md`
- `docs/scientific_governance/12_PCNA_SPECIFIC_CHECKS.md`
- `docs/scientific_governance/15_PROVENANCE_AND_REPRODUCIBILITY.md`

## Related wiki concepts

- [[Sequence Split Leakage]]
- [[Homolog Leakage]]
- [[Biological Realism]]

## Related raw crawl/source paths

- `crawls/_probe2/raw/uniprot/`
- `crawls/pcna-cryptic-pocket-gat-md-kb-final/SOURCE_INDEX.md`

## Related V1 references, if any

Historical only if present.

## Known risks / failure modes

Wrong species/isoform mapping and split leakage through homolog grouping.

## Open questions

- What exact sequence/isoform is approved for Phase 2 mapping?

## Provenance

- Source paths: governance docs above; crawl paths above
- Confidence level: medium
- Date last updated: 2026-05-27
