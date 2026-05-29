---
type: concept
status: active
created: 2026-05-27
updated: 2026-05-27
tags: [concept, metrics]
aliases: [AUPRC vs AUROC, AUROC, AUPRC]
confidence: high
evidence_status: verified
---

# AUPRC vs AUROC

## Definition

Evaluation distinction between ranking positives under class imbalance (AUPRC) and discrimination across thresholds (AUROC).

## Why it matters for GNN-PCNA

Sparse residue positives can make AUROC look strong while practical recovery remains weak.

## How it can go wrong

High AUROC can be reported as strong model evidence despite poor AUPRC/top-k or biological failure.

## Governance rules that apply

`09_EVALUATION_PROTOCOL.md`, `28_NULL_HYPOTHESIS_BASELINES.md`, `36_PUBLICATION_READINESS.md`.

## Coding implications

Report AUROC and AUPRC, but do not let AUROC alone drive claims.

## Related entities

[[CryptoBench]]

## Related raw crawl/source paths

`crawls/pcna-gap-closure-datasets-tools-structures-pass6/`

## Related implementation files, if any

None canonical yet.

## Verification questions Codex should ask

- What metric is primary?
- Are macro/micro and per-protein metrics reported?

## Open questions

- Exact Phase 2 metric hierarchy needs final documentation.

## Provenance

- Source paths: governance docs above
- Confidence level: high
- Date last updated: 2026-05-27
