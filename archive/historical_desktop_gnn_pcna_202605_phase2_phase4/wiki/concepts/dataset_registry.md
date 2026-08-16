---
type: concept
status: active
created: 2026-05-27
updated: 2026-05-27
tags: [concept, dataset, registry]
aliases: [Dataset Registry]
confidence: high
evidence_status: verified
---

# Dataset Registry

## Definition

The governed inventory of data sources, licenses, IDs, chains, labels, splits, leakage risks, hashes, and lifecycle status.

## Why it matters for GNN-PCNA

No dataset should drive code or training unless registered and audited.

## How it can go wrong

Crawl metadata or old graphs can be treated as a ready dataset.

## Governance rules that apply

`04_DATASET_CONSTRAINTS.md`, `15_PROVENANCE_AND_REPRODUCIBILITY.md`, `31_DATA_LIFECYCLE_TRACKING.md`.

## Coding implications

Build registries before graph generation and training.

## Related entities

[[CryptoBench]], [[BioLiP]], [[scPDB]], [[PDBbind]], [[ASD]]

## Related raw crawl/source paths

`crawls/pcna-dataset-repositories-pass9/`, `crawls/pcna-curated-official-tools-data-structures-pass8/`

## Related implementation files, if any

None canonical yet.

## Verification questions Codex should ask

- Is each item accepted, excluded, or quarantined?
- Are hashes recorded?

## Open questions

- Dataset registry path/schema is not yet implemented.

## Provenance

- Source paths: governance docs above
- Confidence level: high
- Date last updated: 2026-05-27
