---
type: concept
status: active
created: 2026-05-27
updated: 2026-05-27
tags: [concept, md, validation]
aliases: [MD Validation Limits]
confidence: high
evidence_status: verified
---

# MD Validation Limits

## Definition

Rules limiting what molecular dynamics can and cannot support in Phase 2.

## Why it matters for GNN-PCNA

MD may be exploratory/supportive only under pre-registered questions and provenance.

## How it can go wrong

RMSF, DCCM, pocket volume, or trajectory behavior can be overstated as binding, mechanism, or therapeutic validation.

## Governance rules that apply

`13_MD_VALIDATION_RULES.md`, `33_PRE_MD_REALITY_CHECK.md`, `14_CLAIM_POLICY.md`.

## Coding implications

Do not generate MD interpretation reports without setup provenance, pre-registered questions, and claim limits.

## Related entities

[[PCNA]], [[AOH1996]], [[fpocket]]

## Related raw crawl/source paths

`crawls/pcna-cryptic-pocket-gat-md-kb-final/`, `crawls/pcna-gap-closure-datasets-tools-structures-pass6/`

## Related implementation files, if any

None canonical yet.

## Verification questions Codex should ask

- What claim was allowed before MD?
- Are apo and ligand-bound setups comparable?

## Open questions

- Is any Phase 2 MD analysis approved yet?

## Provenance

- Source paths: governance docs above
- Confidence level: high
- Date last updated: 2026-05-27
