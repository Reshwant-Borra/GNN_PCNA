---
type: concept
status: active
created: 2026-05-27
updated: 2026-05-27
tags: [concept, claims, governance]
aliases: [Scientific Claim Control]
confidence: high
evidence_status: verified
---

# Scientific Claim Control

## Definition

Governed limits on what Phase 2 can say based on evidence, gates, uncertainty, and scope.

## Why it matters for GNN-PCNA

Prevents model outputs, MD, or PCNA context from becoming overclaims.

## How it can go wrong

Reports can call predictions validated, therapeutic, actionable, or mechanistically confirmed without evidence.

## Governance rules that apply

`14_CLAIM_POLICY.md`, `19_STOP_CONDITIONS.md`, `24_PROJECT_SCOPE.md`, `34_AI_HALLUCINATION_DETECTION.md`, `35_SCIENTIFIC_UNCERTAINTY_REGISTER.md`.

## Coding implications

Generated reports must include evidence traces, uncertainty, and allowed language only.

## Related entities

[[PCNA]], [[AOH1996]], [[ATX-101]]

## Related raw crawl/source paths

Governance docs first; crawl evidence only when source-specific claims are made.

## Related implementation files, if any

None canonical yet.

## Verification questions Codex should ask

- Does the claim cite evidence?
- Does the weakest gate support the wording?

## Open questions

- What claims, if any, are currently allowed? Default: none beyond setup/context.

## Provenance

- Source paths: governance docs above
- Confidence level: high
- Date last updated: 2026-05-27
