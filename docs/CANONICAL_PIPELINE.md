# Canonical Pipeline

Canonical branch for this consolidation: `final-consolidation-audit` from `main` HEAD `5b2ce676c790c4aac0caa10dc4226b5a924791c0`.

Current reconciliation verdict: **NO-GO** for full historical reproducibility. Active forward MD paths are reconciled, but the 520-dim GNN provenance chain remains incomplete. See `REPRODUCIBILITY_MANIFEST.json` and `artifacts/provenance/FROZEN_GNN_PROVENANCE.json`.

## End-to-end map

| Stage | Canonical implementation | Inputs | Outputs/provenance |
|---|---|---|---|
| Raw PCNA structures | `data/raw_intake/pcna_structures/`, `scripts/acquire_phase2_governed.py` | RCSB/PDB mmCIF/API | official-source mmCIF/metadata |
| PDB/raw conversion for GNN | historical production package; current committed helper is MISSING | RCSB structures | `data/raw/*.pdb` generated/rebuildable; full retrieval path unresolved |
| Parsing | `src/data_processing/parse_pdb.py` | PDB/mmCIF-derived PDB | residue list, Cα coords, ligand coords |
| Features | `src/data_processing/graph_construction.py` | residues | 40-dim node features, 6-dim edge features |
| ESM embeddings | `scripts/build_esm_features.py` | residue sequence | `data/esm_features/*.npy` generated artifact |
| Graph construction | `scripts/build_graphs.py`, `scripts/build_graphs_xl.py` | features + ESM | `data/graphs*/*.pt` generated artifact |
| Split/homology controls | `scripts/make_homology_split.py`, `scripts/validate_split_integrity.py`, recovered `data/splits/cryptosite_homology30_split.json` | datasets/graphs | split and audit JSON |
| Model training | `scripts/finetune_v3_fixed.py`; base model in `src/models/cryptic_gnn.py` | 8GLA/apo graphs + ESM | seed-specific checkpoint + hash |
| Checkpoint selection | `scripts/evaluate_clean_split.py` and runbook policy | checkpoints + validation metrics | selected checkpoint metadata; durable checkpoint retrieval unresolved |
| Independent extraction selection | `scripts/independent_extraction_gate.py select-policy` | non-PCNA calibration scores for 1GQY/2HNX/2K1V/2WER/3FU8 | `artifacts/pre_md_independent_extraction_20260815/frozen_extraction_method.json` |
| Final 1W60 pre-MD stability | `scripts/independent_extraction_gate.py apply-1w60` | frozen policy + frozen seed 42/43/44 1W60 scores | PASS/FAIL report; consensus handoff JSON |
| Inference | `scripts/run_v3_inference.py` | checkpoint, PDB, ESM | per-residue scores, v3 summary |
| Pocket clustering | `scripts/run_v3_inference.py`, `src/evaluation/score_pockets.py` | scores + Cα coords | DBSCAN clusters |
| Candidate handoff | `md_validation_4070/gnn_pocket_search/export_handoff.py`, `handoff_to_pocket.py` | clusters/scores | pocket JSON matching schema |
| MD pocket config | `md_validation_4070/pockets/*.json` | candidate residues | MD-ready pocket config |
| MD launcher | `md.sh` | frozen pocket config and MD scripts | tmux-first smoke/control/benchmark/production/analyze stages |
| MD biological assembly/prep | `md_validation_4070/run_md.py` via `md.sh` | 1W60/8GLA/candidate PDB IDs | repaired minimized/equil systems; logs |
| Control MD | `./md.sh smoke`, then `./md.sh control5`, then gated production | 8GLA ligand-stripped | control trajectories |
| Apo MD | `./md.sh production` after Gate-6 | 1W60 | apo/candidate trajectories |
| Analysis | `./md.sh analyze` / `md_validation_4070/analyze_md.py` | trajectories | RMSD/RMSF/SASA/DCCM/openness report |
| Interpretation | `PROJECT_STATUS.md`, `docs/research_base/`, `PROJECT_STATE.md` | GNN + MD reports | scoped scientific conclusions |

## Current executable next step

The final independent extraction/stability gate has been run from frozen seed artifacts and classified `PRE-MD STABILITY: PASS` under the original exploratory gate.

A later POST-PASS STRONGER INTERNAL ROBUSTNESS REQUIREMENT asks for mean literal pairwise Jaccard >=0.75 and minimum pairwise >=0.65 before production-MD release readiness. The current result remains mean 0.6792 and minimum pairwise 0.6316, so this stronger target is not achieved. Production MD must not start until a legitimate human Gate-6 decision explicitly accepts or resolves this remaining robustness risk.

Current status is summarized in `PROJECT_STATUS.md`. The current executable next stage is:

```bash
./md.sh smoke
```

Production remains blocked until smoke, analysis validation, 3 x 5 ns control-first validation, and human Gate-6 approval are complete.
