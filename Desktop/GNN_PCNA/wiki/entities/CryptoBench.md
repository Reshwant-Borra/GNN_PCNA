---
type: entity
status: active
created: 2026-05-27
updated: 2026-05-27
tags: [entity, benchmark, dataset]
aliases: [CryptoBench]
confidence: low
evidence_status: uncertain
---

# CryptoBench

## What it is

A candidate cryptic-pocket benchmark/source lead identified in dataset crawls.

## Why it matters for GNN-PCNA

Could provide benchmark data, but only after file inventory, license, label schema, and leakage risks are audited.

## How Codex should use this entity

Treat as an unverified dataset lead until downloaded/inspected and registered under governance.

## What Codex must NOT overclaim

Do not assume CryptoBench labels are residue-level, leakage-free, PCNA-safe, or directly compatible with Phase 2.

## Related governance docs

- `docs/scientific_governance/04_DATASET_CONSTRAINTS.md`
- `docs/scientific_governance/05_SPLIT_PROTOCOL.md`
- `docs/scientific_governance/06_LABELING_RULES.md`
- `docs/scientific_governance/29_BENCHMARK_LIMITATIONS.md`

## Related wiki concepts

- [[Dataset Registry]]
- [[Label Definition]]
- [[Sequence Split Leakage]]
- [[Apo Holo Leakage]]

## Related raw crawl/source paths

- `crawls/pcna-dataset-repositories-pass9/SOURCE_INDEX.md`

## Related V1 references, if any

None canonical.

## Known risks / failure modes

Unknown label schema, hidden apo/holo or homolog leakage, unavailable files, licensing gaps.

## Open questions

- What is the exact CryptoBench label schema?
- Is the dataset residue-level or pocket/structure-level?

## Provenance

- Source paths: governance docs above; crawl path above
- Confidence level: low
- Date last updated: 2026-05-27
