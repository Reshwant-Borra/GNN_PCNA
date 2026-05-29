---
type: concept
status: active
created: 2026-05-27
updated: 2026-05-27
tags: [concept, graphs, labels]
aliases: [Graph Node Label Alignment]
confidence: high
evidence_status: verified
---

# Graph Node Label Alignment

## Definition

The requirement that graph nodes, residue IDs, chains, masks, and labels refer to the same biological residues.

## Why it matters for GNN-PCNA

Misalignment creates false labels and invalid metrics.

## How it can go wrong

PDB numbering, missing residues, insertion codes, alternate chains, or feature arrays can drift.

## Governance rules that apply

`07_PREPROCESSING_AND_GRAPH_RULES.md`, `06_LABELING_RULES.md`, `15_PROVENANCE_AND_REPRODUCIBILITY.md`.

## Coding implications

Add explicit residue identity tables and alignment audits.

## Related entities

[[PCNA]], [[8GLA]], [[UniProt P12004]]

## Related raw crawl/source paths

`crawls/_probe2/raw/pdb/`, `crawls/_probe2/raw/uniprot/`

## Related implementation files, if any

None canonical yet.

## Verification questions Codex should ask

- Are node indices traceable to chain/residue identifiers?

## Open questions

- Canonical residue numbering policy is not yet documented in wiki.

## Provenance

- Source paths: governance docs above
- Confidence level: high
- Date last updated: 2026-05-27
