---
type: concept
status: active
created: 2026-05-27
updated: 2026-05-27
tags: [concept, results, governance]
aliases: [Unexpected Results Policy]
confidence: high
evidence_status: verified
---

# Unexpected Results Policy

## Definition

Rules for handling results that contradict expectations, including weak GNN performance, baseline wins, or negative controls.

## Why it matters for GNN-PCNA

Phase 2 must report negative or inconclusive results honestly.

## How it can go wrong

Evidence can be reshaped to fit the original story or claims softened without fixing invalid methods.

## Governance rules that apply

`22_UNEXPECTED_RESULTS_POLICY.md`, `30_NEGATIVE_RESULT_SUCCESS_CRITERIA.md`, `14_CLAIM_POLICY.md`.

## Coding implications

Reports should preserve contradictions and downgrade claims rather than hide results.

## Related entities

[[PCNA]], [[CryptoBench]]

## Related raw crawl/source paths

Governance first; evidence paths depend on the result.

## Related implementation files, if any

None canonical yet.

## Verification questions Codex should ask

- Does the result force a stop, downgrade, or registry update?

## Open questions

- No unexpected Phase 2 results are registered yet.

## Provenance

- Source paths: governance docs above
- Confidence level: high
- Date last updated: 2026-05-27
