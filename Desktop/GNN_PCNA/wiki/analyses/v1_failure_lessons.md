---
type: analysis
status: active
created: 2026-05-27
updated: 2026-05-27
tags: [v1, failures, historical-reference]
aliases: [V1 Failure Lessons]
confidence: high
evidence_status: verified
---

# V1 Failure Lessons

## Rule

V1 is historical reference only. It must not be copied blindly, treated as canonical, or reused without audit.

## Useful V1 parts

- old architecture ideas
- old MD experience
- old graph/model concepts
- old failure examples

## V1 risks

- leakage
- overclaims
- stale artifacts
- provenance gaps
- biological realism gaps
- unexpected MD interpretation problems

## Reuse rule

Any V1 component must be audited before reuse. If provenance or scientific assumptions are missing, do not reuse it.

## Current local status

No local `V1` or `project-version-1` directory was visible in the root workspace during inspection. If a branch or external path exists, record it before use.

## Provenance

- Source paths: `docs/scientific_governance/03_FAILURE_MODE_CATALOG.md`, `37_PHASE2_IMPLEMENTATION_PLAN.md`
- Confidence level: high for rule; uncertain for local V1 location
- Date last updated: 2026-05-27
