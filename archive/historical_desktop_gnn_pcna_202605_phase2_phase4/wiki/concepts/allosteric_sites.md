---
type: concept
status: active
created: 2026-05-27
updated: 2026-05-27
tags: [concept, allostery]
aliases: [Allosteric Sites]
confidence: medium
evidence_status: inferred
---

# Allosteric Sites

## Definition

Sites whose perturbation may affect protein function through nonlocal structural or dynamic coupling.

## Why it matters for GNN-PCNA

PCNA candidate regions may be discussed as allosteric only under strict evidence and claim limits.

## How it can go wrong

Allostery can be inferred from proximity, database labels, or MD motion without mechanism-level evidence.

## Governance rules that apply

`11_BIOLOGICAL_REALISM_RULES.md`, `12_PCNA_SPECIFIC_CHECKS.md`, `14_CLAIM_POLICY.md`, `24_PROJECT_SCOPE.md`.

## Coding implications

Code should store allosteric labels or flags only when source provenance and label meaning are explicit.

## Related entities

[[ASD]], [[PCNA]], [[ATX-101]]

## Related raw crawl/source paths

`crawls/pcna-curated-official-tools-data-structures-pass8/`, `crawls/pcna-cryptic-pocket-gat-md-kb-final/`

## Related implementation files, if any

None canonical yet.

## Verification questions Codex should ask

- Is this an allosteric label, site annotation, or hypothesis?
- What evidence supports it?

## Open questions

- Are allosteric labels in scope for Phase 2 training?

## Provenance

- Source paths: governance docs above; crawl paths above
- Confidence level: medium
- Date last updated: 2026-05-27
