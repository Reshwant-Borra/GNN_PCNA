# EXPERIMENT_INDEX.md — Master Experiment Log

→ Links: [[RESEARCH_QUESTION]] | [[VALIDATION]] | [[PIPELINE]]

> Update this after every experiment. Never delete rows — mark status instead.

---

## Index

| ID | Name | Status | Goal | Data | Model | Result |
|---|---|---|---|---|---|---|
| E001 | Baseline GNN | Planned | Verify CrypticGNN forward pass works on PCNA graph | 1W60 (apo) | CrypticGNN (untrained) | — |
| E002 | PCNA Pocket Prediction | Planned | Recover AOH1996 pocket from 8GLA | 8GLA (holo) | CrypticGNN (fine-tuned) | — |
| E003 | MD Validation | smoketest complete | RMSF + DCCM on AOH1996 pocket, apo 1W60 | 6.4 ns DCD (636 frames, 10 ps/frame) | MDAnalysis 2.10 | fold-change 0.832, DCCM 0.3018 — pipeline PASS, full 100 ns pending |
| E004 | [[E004_homology_clean_benchmark\|Homology-clean benchmark remediation]] | completed | Replace contaminated random split claims with MMseqs2 30% clean split, provenance, ablations, and AUPRC-first evaluation | CryptoSite-derived graphs | small_geometry, xl_geometry, xl_esm_zero, xl_esm_full | Final clean split: best `xl_esm_full` AUPRC 0.2513 (95% CI 0.1267-0.3815), AUROC 0.8649; geometry-only XL AUPRC 0.1923; ESM2 contribution is a major confound |
| E005 | [[E005_pcna_xl_esm_full_regeneration\|PCNA xl_esm_full regeneration and final framing]] | completed | Regenerate PCNA per-structure reports with the clean-split `xl_esm_full` checkpoint and audit final claims | 59 PCNA structures | `xl_esm_full` seed 42 checkpoint | Top `1W60` cluster rank 1, mean 0.710175, 4 residues, 3 AOH/MD overlaps; full AOH1996 pocket not recovered; final framing downgraded to residue prioritization/hypothesis generation |

---

## Experiment Statuses

- `planned` — defined but not started
- `blocked` — waiting on dependency (data, model, compute)
- `in_progress` — actively running
- `completed` — finished, result logged
- `abandoned` — stopped, reason noted

---

## What Blocks E001

- [ ] `src/data_processing/parse_pdb.py` must be implemented
- [ ] `src/data_processing/graph_construction.py` must be implemented
- [ ] PDB 1W60 downloaded to `data/raw/`

## What Blocks E002

- [ ] E001 must pass (graph construction working)
- [ ] `src/training/train.py` and `loss.py` and `dataset.py` implemented
- [ ] PDB 8GLA downloaded to `data/raw/`
- [ ] Labels generated for 8GLA (residues within 6 Å of AOH1996)
- [ ] Pre-training on CryptoSite completed (or skip to direct fine-tuning)

## What Blocks E003

- [ ] E002 must pass (model predicts pockets)
- [ ] MD trajectory of 1W60 (apo) available in `data/trajectories/`
- [ ] `src/md/parse_trajectory.py` implemented
- [ ] `src/evaluation/score_pockets.py` implemented
