# Project Scope Audit

Date: 2026-05-27
Created by: Codex
Status: DRAFT - scope frozen for data-foundation work

## Scope Decision

Phase 2 remains a computational structural biology project for governed residue-level prediction and auditing of PCNA candidate cryptic, allosteric, or pocket-like regions.

## In Scope For This Milestone

- Source and scope freeze artifacts.
- Assumption and uncertainty registry scaffolding.
- Source registry from `crawls/`.
- Benchmark limitations review template.
- Dataset and lifecycle registry templates.
- Split and label freeze plans.
- Human-review gate records.
- Biological data sanity review template.
- Readiness/audit checks.

## Out Of Scope For This Milestone

- GNN model implementation.
- Training.
- MD.
- Docking or drug-discovery workflows.
- PCNA prediction interpretation.
- Scientific or therapeutic claims.

## Forbidden Claim Boundary

No current artifact may be used to claim therapeutic validation, clinical actionability, treatment benefit, drug discovery success, confirmed mechanism, or PCNA site validation.

## Checks

| Check | Result | Notes |
|---|---|---|
| Scope matches governance | PASS | See `24_PROJECT_SCOPE.md`. |
| No model code requested | PASS | This milestone is data-foundation only. |
| No training allowed | PASS | Readiness gate remains FAIL for training. |
| Claims allowed | FAIL | No scientific claims are authorized. |

## Related Governance

- `docs/scientific_governance/24_PROJECT_SCOPE.md`
- `docs/scientific_governance/14_CLAIM_POLICY.md`
- `docs/scientific_governance/37_PHASE2_IMPLEMENTATION_PLAN.md`

## Conclusion

Scope is frozen for governed data-foundation work only. The project is ready for dataset planning, not training or claims.
