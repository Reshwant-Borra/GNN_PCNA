# E{NNN}: {Short Name}

**Status:** planned | blocked | in_progress | completed | abandoned
**Date started:** YYYY-MM-DD
**Date completed:** YYYY-MM-DD

→ Links: [[EXPERIMENT_INDEX]] | [[PIPELINE]] | [[VALIDATION]]

---

## Hypothesis

_What do you expect to happen, and why?_

---

## Goal

_Single sentence: what does success look like for this experiment?_

---

## Pipeline Stage

_Which stage(s) of [[PIPELINE]] does this test?_

---

## Data Used

| Type | Source | Path | Notes |
|---|---|---|---|
| PDB structure | PDB 1W60 | `data/raw/1W60.pdb` | Apo |
| Processed graph | — | `data/graphs/` | — |

---

## Code Files

| File | Role in this experiment |
|---|---|
| `src/data_processing/...` | ... |
| `src/models/cryptic_gnn.py` | ... |

---

## Config / Hyperparameters

```python
lr = 1e-3
epochs = 100
batch_size = 16
distance_cutoff = 8.0  # Å
dropout = 0.2
```

---

## Results

### Metrics

| Metric | Value | Notes |
|---|---|---|
| AUROC | — | — |
| AUPRC | — | — |
| 8GLA pocket rank | — | — |
| Top-5 pocket recovery | — | — |

### Figures / Outputs

_Paths to output files:_
- `results/...`

---

## Interpretation

_What do the results mean? Does the hypothesis hold?_

---

## Limitations of This Experiment

_What can't we conclude from this run?_

---

## Bugs Found

_Any issues discovered during this experiment. Copy to KNOWN_BUGS.md._

---

## Next Action

_What should happen next as a result of this experiment?_
