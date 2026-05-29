---
type: concept
status: active
created: 2026-05-27
updated: 2026-05-27
tags: [concept, prediction, residues]
aliases: [Residue Level Prediction]
confidence: high
evidence_status: verified
---

# Residue Level Prediction

## Definition

Prediction where outputs align to individual residues rather than whole proteins, structures, pockets, or ligands.

## Why it matters for GNN-PCNA

Phase 2 scope is residue-level candidate region prediction and auditing.

## How it can go wrong

Pocket-level or structure-level labels can be treated as residue-level labels without mapping rules.

## Governance rules that apply

`04_DATASET_CONSTRAINTS.md`, `06_LABELING_RULES.md`, `09_EVALUATION_PROTOCOL.md`.

## Coding implications

Outputs, targets, masks, and metrics must share residue indices and provenance.

## Related entities

[[PCNA]], [[CryptoBench]]

## Related raw crawl/source paths

`crawls/pcna-dataset-repositories-pass9/`, `crawls/pcna-gap-closure-datasets-tools-structures-pass6/`

## Related implementation files, if any

None canonical yet.

## Verification questions Codex should ask

- Are labels residue-level?
- Are unlabeled/masked residues handled explicitly?

## Open questions

- Which datasets truly provide residue-level labels?

## Provenance

- Source paths: governance docs above
- Confidence level: high
- Date last updated: 2026-05-27
