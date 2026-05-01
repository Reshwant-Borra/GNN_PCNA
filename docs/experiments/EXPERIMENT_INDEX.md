# EXPERIMENT_INDEX.md — Master Experiment Log

→ Links: [[RESEARCH_QUESTION]] | [[VALIDATION]] | [[PIPELINE]]

> Update this after every experiment. Never delete rows — mark status instead.

---

## Index

| ID | Name | Status | Goal | Data | Model | Result |
|---|---|---|---|---|---|---|
| E001 | Baseline GNN | Planned | Verify CrypticGNN forward pass works on PCNA graph | 1W60 (apo) | CrypticGNN (untrained) | — |
| E002 | PCNA Pocket Prediction | Planned | Recover AOH1996 pocket from 8GLA | 8GLA (holo) | CrypticGNN (fine-tuned) | — |
| E003 | MD Validation | Planned | RMSF + DCCM on predicted novel pockets | MD trajectory (TBD) | — | — |

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
