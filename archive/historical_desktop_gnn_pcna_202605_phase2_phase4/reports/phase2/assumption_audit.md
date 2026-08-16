# Assumption Audit

Date: 2026-05-27
Created by: Codex
Status: DRAFT

## Registry

Machine-readable starter registry: `data/registries/assumption_registry.json`

## Scope

This audit covers only the governed data-foundation milestone. It does not authorize training, evaluation, MD, or claims.

## Active Starter Assumptions

| ID | Category | Confidence | Status | Summary |
|---|---|---|---|---|
| ASM-FOUNDATION-001 | dataset | high | proposed | Registry templates and audits may be created before dataset adoption. |
| ASM-CRAWL-001 | dataset | high | proposed | Crawls are source leads, not verified truth. |
| ASM-V1-001 | dataset | high | proposed | V1 artifacts are historical reference only until audited. |

## Blocking Missing Assumptions

| Missing assumption | Impact | Handling |
|---|---|---|
| CryptoBench label meaning | Blocks dataset adoption | Recorded in uncertainty register and benchmark limitations. |
| Sequence clustering threshold | Blocks split freeze | Recorded as open planning item. |
| PCNA final holdout list | Blocks PCNA split/claim planning | Recorded as open planning item. |
| Human reviewer role/name | Blocks freeze gates | Recorded in human review log. |

## Governance

- `docs/scientific_governance/02_ASSUMPTION_REGISTRY.md`
- `docs/scientific_governance/16_CODING_AGENT_RULES.md`

## Conclusion

Assumption scaffolding exists. No scientific assumption is approved for training or claims.
