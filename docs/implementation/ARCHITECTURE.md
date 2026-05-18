# ARCHITECTURE.md — Repo Architecture + Design Decisions

→ Links: [[MODELS]] | [[PIPELINE]] | [[FILE_GUIDE]]

---

## Design Philosophy

- **Per-residue output**: No global pooling at the scoring stage — we need per-residue probabilities to localize pockets.
- **Residue-level graph**: Nodes = residues (Cα), edges = Cα–Cα spatial contacts < 8 Å.
- **Edge features included**: Distance + sequence separation at every message-passing step.
- **Residual connections**: Between each GATv2Conv layer to prevent over-smoothing.
- **Symmetric treatment**: PCNA homotrimer chains A/B/C share model weights.
- **Transfer learning**: Pre-train on CryptoSite, fine-tune on 8GLA-specific labels.

---

## Module Responsibilities

| Module | Location | Responsibility |
|---|---|---|
| PDB Parser | `src/data_processing/parse_pdb.py` | Parse PDB → `Residue` list; label pocket residues |
| Graph Builder | `src/data_processing/graph_construction.py` | `Residue` list → PyG `Data` object |
| GNN Model | `src/models/cryptic_gnn.py` | Graph → per-residue pocket probabilities |
| Loss | `src/training/loss.py` | Focal loss for class imbalance |
| Dataset | `src/training/dataset.py` | PyG `Dataset` / `InMemoryDataset` |
| Trainer | `src/training/train.py` | Training loop, checkpointing, early stopping |
| Scorer | `src/evaluation/score_pockets.py` | Cluster high-score residues → ranked pockets |
| MD Parser | `src/md/parse_trajectory.py` | RMSF, DCCM, volume from MD trajectory — **STUB, no trajectory data exists** |

---

## Data Flow Through Code

```
data/raw/1W60.pdb
  → parse_pdb.parse_pdb()           → list[Residue]
  → graph_construction.build_graph() → torch_geometric.data.Data
  → data/graphs/1W60.pt

training/dataset.py                  → PCNADataset (loads .pt graphs)
training/train.py                    → trains CrypticGNN
  → checkpoints/best_model.pt

models/cryptic_gnn.py (CrypticGNN)
  .forward(x, edge_index, edge_attr) → (N,) pocket scores

evaluation/score_pockets.py
  → threshold + DBSCAN clustering
  → ranked pocket list + scored .pdb

data/trajectories/1W60_apo.xtc   ← DOES NOT EXIST (MD not yet run)
  → md/parse_trajectory.py         ← stub only
  → RMSF, DCCM, volume per pocket  ← no values exist
```

---

## Key Architectural Decisions

| Decision | Choice | Rationale |
|---|---|---|
| GNN layer type | GATv2Conv | Dynamic attention captures long-range interactions better than GCN |
| Edge features | Concatenated at every layer | Distance + seq_sep encode spatial + sequential context |
| Layers | 4 | >5 risks over-smoothing; 3–4 is empirical sweet spot |
| Hidden dim | 256 | Sufficient capacity for 26-dim node input; benchmarked in PocketMiner class |
| Loss function | Focal loss (γ=2, α=0.25) | Handles 5–15% positive fraction; avoids trivial all-negative prediction |
| Scoring head | MLP 256→64→1 + sigmoid | Per-residue; no global pooling |

---

## Extension Points (not yet implemented)

| Feature | Where to add | Notes |
|---|---|---|
| MD ensemble graphs | `graph_construction.py` | Add MD snapshot graphs to training set |
| PCA on MD trajectory | `md/parse_trajectory.py` | Project trajectory onto PCs |
| AlphaFold structure support | `parse_pdb.py` | May need SASA recalculation (no B-factors) |
| Multi-structure inference | `evaluation/score_pockets.py` | Score ensemble, average predictions |
| Enhanced sampling integration | `md/` new file | PLUMED + GROMACS metadynamics output |
