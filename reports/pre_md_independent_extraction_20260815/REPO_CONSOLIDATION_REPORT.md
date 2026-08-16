# Repository Consolidation Report

Date: 2026-08-15
Branch: `final-consolidation-audit`
Base HEAD: `5b2ce676c790c4aac0caa10dc4226b5a924791c0`

## Source hierarchy

Tier 1 - original/authoritative project methodology:
`docs/research_base/sources/SOURCE_REGISTRY.md`, `reports/phase2/*`, `docs/00_EXECUTIVE_BUILD_PLAN.md`, `docs/08_PROJECT_SPECIFIC_GNN_MD_RULES.md`, source PDB/UniProt/literature records.

Tier 2 - explicit later decisions:
`docs/research_base/decisions/DECISION_REGISTRY.md`, `research_os_registries/decision_registry.json`, `PROJECT_STATE.md`.

Tier 3 - canonical current protocol:
root `src/`, root `scripts/`, `md_validation_4070/`, `docs/CANONICAL_PIPELINE.md`, `docs/REPO_STRUCTURE.md`, `scripts/independent_extraction_gate.py`.

Tier 4 - historical implementation:
`archive/historical_desktop_gnn_pcna_202605_phase2_phase4/`, previous reports under `reports/phase2`, old diagnostics under `artifacts/diagnostics`.

Tier 5 - agent inference:
`docs/research_base/inferences/INFERENCE_REGISTRY.md`; these are not facts.

## Duplicate tree disposition

The nested active-looking `Desktop/GNN_PCNA/` tree was found already staged as zero-content-preserving renames into `archive/historical_desktop_gnn_pcna_202605_phase2_phase4/`. The remaining `Desktop/` directory is empty.

Migrated active unique material:

- `scripts/derive_pcna_interface_contacts.py`
- `scripts/check_prediction_overlap.py`
- `data/registries/pcna_interface_map.json`
- `data/registries/pcna_interface_contacts_derived.json`

Archived material:

- historical `.memory/`, phase reports, wiki, labels, graphs, scripts, `src/`, and tests under `archive/historical_desktop_gnn_pcna_202605_phase2_phase4/`

Deleted material:

- none in this pass

Remaining ambiguity:

- historical archive still contains scientifically relevant provenance; it is intentionally not importable as active root code.

## ZIP disposition

`gnn_pcna_pre_md_v3.zip` was not found by repository search. No active workflow now depends on an unexplained ZIP. If the ZIP appears later, compare it against canonical root and record migration/deprecation before use.

## Active canonical paths

- GNN/model/data/evaluation code: `src/`
- GNN/data commands: `scripts/`
- MD prep/run/analyze/handoff: `md_validation_4070/`
- Scientific knowledge base: `docs/research_base/`
- Operational ResearchOS memory/registries: `research_os_memory/`, `research_os_registries/`
- Final pre-MD artifacts: `artifacts/pre_md_independent_extraction_20260815/`

## Cleanup checks

`Desktop/GNN_PCNA` remains only in provenance text/status output, archived path names, and historical reports. No active import path should require it.
