# E002: PCNA Pocket Prediction â€” Recover AOH1996 Site

**Status:** planned
**Date started:** â€”
**Date completed:** â€”

â†’ Links: [[EXPERIMENT_INDEX]] | [[PIPELINE]] | [[MODELS]] | [[VALIDATION]] | [[BIOLOGY_PCNA]]

---

## Hypothesis

A CrypticGNN fine-tuned on labeled residues from PDB 8GLA (AOH1996 binding site) will recover the AOH1996 pocket as a top-3 ranked candidate when run on 8GLA in inference mode.

---

## Goal

Pass the positive control: the model must rank the AOH1996 pocket in the top-3 candidates. This is the minimum bar before any novel prediction is trusted.

See [[VALIDATION]] for the full positive control criteria.

---

## Pipeline Stage

- Stage 3: Labeling (8GLA residues within 6 Ã… of AOH1996 = positive)
- Stage 4: GNN Training / Fine-tuning
- Stage 5: Pocket Clustering + Ranking

---

## Data Used

| Type | Source | Path | Notes |
|---|---|---|---|
| Training structure | PDB 8GLA | `data/raw/8GLA.pdb` | Download required |
| Apo structure | PDB 1W60 | `data/raw/1W60.pdb` | Background negative |
| Pocket labels | Generated | `data/labels/8GLA_labels.npy` | 6 Ã… cutoff from AOH1996 |
| Graphs | Generated | `data/graphs/8GLA.pt`, `1W60.pt` | |
| External training | CryptoSite dataset | TBD | Pre-training only |

---

## Code Files

| File | Status | Role |
|---|---|---|
| `src/data_processing/parse_pdb.py` | Stub | PDB parsing + labeling |
| `src/data_processing/graph_construction.py` | Stub | Graph construction |
| `src/training/loss.py` | Stub | Focal loss |
| `src/training/dataset.py` | Stub | Dataset loader |
| `src/training/train.py` | Stub | Training loop |
| `src/evaluation/score_pockets.py` | Stub | Clustering + ranking |
| `src/models/cryptic_gnn.py` | Implemented | Model |

---

## Blocking Dependencies

- [ ] E001 passes
- [ ] 8GLA downloaded to `data/raw/8GLA.pdb`
- [ ] All training stubs implemented
- [ ] Pre-training on CryptoSite completed (or skip with direct fine-tuning on 8GLA)

---

## Config

```python
# Training
lr = 1e-3
weight_decay = 1e-4
epochs = 100
batch_size = 16
patience = 10       # early stopping
dropout = 0.2

# Loss
focal_gamma = 2.0
focal_alpha = 0.25

# Labeling
pocket_cutoff_angstrom = 6.0

# Clustering
score_threshold = 0.5
dbscan_eps = 6.0    # Ã…
dbscan_min_samples = 3
```

---

## Success Criteria

| Criterion | Target | Actual |
|---|---|---|
| AOH1996 pocket mean score | > 0.7 | â€” |
| AOH1996 pocket rank | Top 3 | â€” |
| AUROC (if CryptoSite used) | > 0.80 | â€” |
| AUPRC (if CryptoSite used) | > 0.50 | â€” |

---

## Results

_Not yet run._

---

## Interpretation

_Fill in after running._

---

## Limitations

- Only one PCNA holo structure available (8GLA) â€” very small fine-tuning set
- If pre-training skipped, generalization may be poor
- Chain leakage risk: all 3 chains of PCNA are near-identical â€” must not use them as separate test set members

---

## Next Action

If E002 passes â†’ proceed to E003 (MD validation of novel predicted pockets).
If E002 fails â†’ debug labeling, class imbalance, or training stability before claiming any result.
