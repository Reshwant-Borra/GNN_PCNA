# Source Of Truth Audit

Date: 2026-05-27
Created by: Codex
Status: DRAFT - source/scope foundation only

## Decision

Canonical repository: `https://github.com/Reshwant-Borra/GNN_PCNA`

Canonical local workspace for this run: `C:\Users\reshw\Desktop\GNN_PCNA`

Canonical governance directory: `docs/scientific_governance/`

Canonical wiki memory layer: `wiki/`

Canonical Phase 2 reports directory: `reports/phase2/`

Canonical dataset registry path: `docs/scientific_governance/DATASET_REGISTRY.md`

Canonical source registry path: `data/registries/source_registry.json`

Canonical data lifecycle registry path: `data/registries/data_lifecycle_registry.json`

Canonical split freeze plan: `reports/phase2/split_freeze_plan.md`

Canonical label freeze plan: `reports/phase2/label_freeze_plan.md`

## Explicit Noncanonical Inputs

| Path/Area | Status | Reason |
|---|---|---|
| `crawls/` | source leads only | Raw evidence and prior context; not automatically verified truth. |
| `wiki/` | memory/navigation only | Useful for context, not stronger than governance or raw sources. |
| V1 / `project-version-1` / old artifacts | historical reference only | Must be audited before reuse. No local V1 path is confirmed in this checkout. |
| `BORRA_#1_SARC.pdf` | project intent candidate | May inform intent but does not validate scientific claims. |

## Hash/Commit Status

| Item | Value | Status |
|---|---|---|
| Git commit hash | not recorded | BLOCKER: workspace appears not to be a normal project checkout root. |
| Dataset hash | not available | Expected: no dataset adopted yet. |
| Split hash | not available | Expected: split not frozen yet. |
| Label hash | not available | Expected: labels not frozen yet. |
| Graph hash | not available | Expected: no graphs should exist yet. |

## Checks

| Check | Result | Evidence |
|---|---|---|
| Governance directory exists | PASS | `docs/scientific_governance/` |
| Phase 2 report directory exists | PASS | `reports/phase2/` |
| Dataset registry path created | PASS | `docs/scientific_governance/DATASET_REGISTRY.md` |
| Source registry path created | PASS | `data/registries/source_registry.json` |
| Lifecycle registry path created | PASS | `data/registries/data_lifecycle_registry.json` |
| Old artifacts excluded from truth | PASS WITH WARNING | V1 path not confirmed locally; reuse remains blocked. |
| Training readiness | FAIL | Dataset, split, labels, graph audit, human gates missing. |

## Blockers

- Actual Phase 2 implementation branch/path is not confirmed.
- Git commit hash was not captured because this workspace is not confirmed as a clean project checkout.
- No source has been adopted as a dataset.
- No split, label, graph, or training artifact exists or is authorized.

## Related Governance

- `docs/scientific_governance/01_SOURCE_OF_TRUTH.md`
- `docs/scientific_governance/15_PROVENANCE_AND_REPRODUCIBILITY.md`
- `docs/scientific_governance/37_PHASE2_IMPLEMENTATION_PLAN.md`

## Conclusion

Source-of-truth scaffolding exists. The project is ready to continue dataset planning and source verification, not training.
