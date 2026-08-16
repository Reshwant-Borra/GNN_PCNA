# Final Repository Audit

## Repository cleanup

Files before: tracked 1868; untracked 1034; ignored 25 at Phase 0. Full inventory: `file_inventory.csv`.

Files after: see `git status` and `FILE_CLASSIFICATION.csv`.

Duplicated trees found: `Desktop/GNN_PCNA/` nested historical project tree.

Migrated files:

- `scripts/derive_pcna_interface_contacts.py`
- `scripts/check_prediction_overlap.py`
- `data/registries/pcna_interface_map.json`
- `data/registries/pcna_interface_contacts_derived.json`
- root GNN package/scripts/tests from `origin/graph-leakage-fix`

Archived files:

- `archive/historical_desktop_gnn_pcna_202605_phase2_phase4/`

Deleted files: none.

Remaining intentional duplication: archive retains historical project tree until provenance extraction is complete.

## Canonical implementation

- Branch: `final-consolidation-audit`
- Base commit: `5b2ce676c790c4aac0caa10dc4226b5a924791c0`
- Canonical GNN path: `src/`, `scripts/`
- Canonical MD path: `md_validation_4070/`

## Research base

- Source facts: 17
- Assumptions: 16
- Decisions: 6
- Inferences: 5
- Hypotheses: 3
- Unresolved questions: 5

## Audit results

Confirmed active bugs: none reproduced in current shell.

Data defects: `gnn_pcna_pre_md_v3.zip` not found; required production artifacts not all present in active tree.

Documentation gaps fixed: canonical pipeline, repo structure, research base, assumption/decision/inference/source registries, project state.

Methodology choices: DBSCAN eps/min_samples, cluster ranking, ESM2 inclusion, MD HMR/timestep/metric thresholds.

Latent issues: current shell lacks runtime deps; large artifact policy unresolved; imported graph-branch tests require production env.

False positives disproved: `Desktop/GNN_PCNA/` was not required as an active executable path after interface-map migration; it was historical/provenance, not current pipeline.

## Previous-six-fix verification

1. Inference prior `auroc` KeyError: STATIC PASS; runtime NOT RUN due missing deps/artifacts.
2. Stale checkpoint rejection: STATIC PASS; runtime NOT RUN due missing torch/checkpoint.
3. Seeded training: STATIC PASS; production determinism NOT RUN due missing deps.
4. Apo/control SASA atom parity: STATIC PASS; runtime NOT RUN due missing mdtraj.
5. Invalid 8GLA long covalent bonds cannot occur silently: STATIC PASS; runtime NOT RUN due missing OpenMM.
6. Checkpoint selection respects configured criteria: UNKNOWN/PARTIAL; code present, full selection regression not run.

## Seed stability

NOT YET RUN. Current environment cannot run production-quality training.

## Production MD readiness

NO-GO.

## Exact next action

Run production-quality 3-seed GNN retraining and seed-stability gate in the correct conda environment, after locating or regenerating required data/raw + ESM artifacts and verifying any `gnn_pcna_pre_md_v3` package against Git.
