---
type: analysis
status: active
created: 2026-05-27
updated: 2026-05-27
tags: [evaluation, metrics]
aliases: [Evaluation Strategy]
confidence: high
evidence_status: verified
---

# Evaluation Strategy

## Strategy

Evaluate residue-level predictions with per-protein metrics, AUROC, AUPRC, top-k recovery, calibration where applicable, bootstrap confidence intervals, and biological realism checks.

## Claim control

AUROC alone cannot support strong claims. If metrics and scientific validity conflict, downgrade claims.

## Governance

`09_EVALUATION_PROTOCOL.md`, `28_NULL_HYPOTHESIS_BASELINES.md`, `36_PUBLICATION_READINESS.md`.

## Provenance

- Source paths: governance docs above
- Confidence level: high
- Date last updated: 2026-05-27
