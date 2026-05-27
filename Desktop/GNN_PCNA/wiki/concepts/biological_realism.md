---
type: concept
status: active
created: 2026-05-27
updated: 2026-05-27
tags: [concept, biology, pcna]
aliases: [Biological Realism]
confidence: high
evidence_status: verified
---

# Biological Realism

## Definition

The requirement that predicted residue clusters make biological and structural sense before supporting PCNA candidate-pocket claims.

## Why it matters for GNN-PCNA

Numerical metrics are insufficient if predictions are biologically incoherent.

## How it can go wrong

Model scores can be promoted despite known-interface overlap, mapping errors, or shortcut features.

## Governance rules that apply

`11_BIOLOGICAL_REALISM_RULES.md`, `12_PCNA_SPECIFIC_CHECKS.md`, `25_BIOLOGICAL_DATA_SANITY_REVIEW.md`.

## Coding implications

Support audits that inspect predicted clusters, known interfaces, residue identities, and alternative explanations.

## Related entities

[[PCNA]], [[AOH1996]], [[ATX-101]]

## Related raw crawl/source paths

`crawls/pcna-cryptic-pocket-gat-md-kb-final/`, `crawls/pcna-biogrid-full-pass5/`

## Related implementation files, if any

None canonical yet.

## Verification questions Codex should ask

- Is the predicted region plausible and source-supported?
- Could leakage or shortcut features explain it?

## Open questions

- What manual PCNA mapping review is required before claims?

## Provenance

- Source paths: governance docs above
- Confidence level: high
- Date last updated: 2026-05-27
