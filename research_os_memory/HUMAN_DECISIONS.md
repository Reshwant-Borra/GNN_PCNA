# HUMAN_DECISIONS.md

Last updated: 2026-05-24T00:00:00Z
Updated by: human (initial bootstrap)
Status: current

Append-only. Do not edit or delete existing entries.
Full machine-readable record: `../research_os_registries/decision_registry.json`

---

## DEC-0001

- **Decision ID**: DEC-0001
- **Date**: 2026-05-19
- **Decision maker**: Advay
- **Request**: Confirm corrected ANM numbers after chain fix
- **Options**: Use old numbers (1.104/+0.247) | Use corrected numbers (1.157/+0.300)
- **Decision**: Use corrected numbers. Old numbers are invalid and must not appear in paper.
- **Rationale**: ZQZ is absent from chain C of 8GLA. Including chain C in fold-change calculation inflates the apo denominator incorrectly.
- **Evidence**: `data/results/nma_apo_holo_comparison.json` (updated 2026-05-19)
- **Affected artifacts**: paper section 3.8, any ANM figure, `best_meta.json`
- **Follow-up**: Ensure paper draft uses 1.157/+0.300; old values must not appear anywhere in submitted manuscript

---

## DEC-0002

- **Decision ID**: DEC-0002
- **Date**: 2026-05-21
- **Decision maker**: Reshwant Borra + Advay
- **Request**: Switch MD compute from local RTX 4070 to Google Cloud L4
- **Options**: Continue on RTX 4070 (~35 ns/day) | Switch to L4 (~140 ns/day)
- **Decision**: Switch to L4 for 4× speedup
- **Rationale**: 100 ns target would take ~3 days on RTX 4070; L4 completes in <1 day
- **Evidence**: Observed throughput on both platforms
- **Affected artifacts**: `data/md/1W60_production.dcd`
- **Follow-up**: Transfer DCD from cloud after simulation completes

---

## Template for new decisions

```
## DEC-{NNN}

- **Decision ID**: DEC-{NNN}
- **Date**: YYYY-MM-DD
- **Decision maker**: 
- **Request**: 
- **Options**: 
- **Decision**: 
- **Rationale**: 
- **Evidence**: 
- **Affected artifacts/claims**: 
- **Follow-up**: 
```
