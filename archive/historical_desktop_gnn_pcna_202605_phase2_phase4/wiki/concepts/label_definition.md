---
type: concept
status: active
created: 2026-05-27
updated: 2026-05-27
tags: [concept, labels]
aliases: [Label Definition]
confidence: high
evidence_status: verified
---

# Label Definition

## Definition

The documented rule that defines positive, negative, unlabeled, uncertain, and excluded residues.

## Why it matters for GNN-PCNA

The model can only learn and be evaluated against what labels actually mean.

## How it can go wrong

Changing thresholds, mixing label types, or claiming proxy labels mean cryptic biology.

## Governance rules that apply

`06_LABELING_RULES.md`, `04_DATASET_CONSTRAINTS.md`, `14_CLAIM_POLICY.md`.

## Coding implications

Do not implement label logic unless label source, threshold, residue mapping, and limitations are documented.

## Related entities

[[CryptoBench]], [[BioLiP]], [[8GLA]]

## Related raw crawl/source paths

`crawls/pcna-dataset-repositories-pass9/`, `crawls/pcna-curated-official-tools-data-structures-pass8/`

## Related implementation files, if any

None canonical yet.

## Verification questions Codex should ask

- What exact label rule is approved?
- Who froze it?

## Open questions

- Phase 2 label schema is not yet confirmed.

## Provenance

- Source paths: governance docs above
- Confidence level: high
- Date last updated: 2026-05-27
