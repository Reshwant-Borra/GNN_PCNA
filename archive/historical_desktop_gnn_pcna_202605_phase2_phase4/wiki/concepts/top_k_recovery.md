---
type: concept
status: active
created: 2026-05-27
updated: 2026-05-27
tags: [concept, metrics]
aliases: [Top K Recovery, Top-K Recovery]
confidence: high
evidence_status: verified
---

# Top K Recovery

## Definition

Evaluation of whether the top-ranked residues recover expected positives under a governed label definition.

## Why it matters for GNN-PCNA

Useful for residue-level ranking when positives are sparse.

## How it can go wrong

Reported without per-protein context, confidence intervals, or label validity.

## Governance rules that apply

`09_EVALUATION_PROTOCOL.md`, `28_NULL_HYPOTHESIS_BASELINES.md`, `36_PUBLICATION_READINESS.md`.

## Coding implications

Implement per-protein top-k metrics with masks, bootstrap CIs where applicable, and null baselines.

## Related entities

[[PCNA]], [[CryptoBench]]

## Related raw crawl/source paths

`crawls/pcna-gap-closure-datasets-tools-structures-pass6/`

## Related implementation files, if any

None canonical yet.

## Verification questions Codex should ask

- What K values are approved?
- Is top-k primary or secondary?

## Open questions

- Approved K values are not recorded in wiki yet.

## Provenance

- Source paths: governance docs above
- Confidence level: high
- Date last updated: 2026-05-27
