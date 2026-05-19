# FILE_GUIDE.md — Per-File Purpose and Status

→ Links: [[ARCHITECTURE]] | [[PIPELINE]]

> Update status column when implementation changes.

---

## Source Files

### `src/data_processing/parse_pdb.py`
- **Status:** Stub
- **Purpose:** Parse PDB files into `Residue` objects; strip HETATM; standardize chains; label pocket residues (6 Å from AOH1996)
- **Key functions:** `parse_pdb()`, `strip_heteroatoms()`, `standardize_chains()`, `label_pocket_residues()`
- **Dependencies:** BioPython or ProDy (for SASA + secondary structure); numpy
- **Gemini-ready:** Yes — stubs exist with type hints and docstrings
- **Plan needed:** Yes — create plan before implementing (`parse_pdb` is critical path)
- **Tests needed:** Unit test with known PDB; check residue count, B-factor, SASA values

---

### `src/data_processing/graph_construction.py`
- **Status:** Stub
- **Purpose:** Build PyG `Data` objects from `Residue` lists; compute node + edge features; apply distance cutoff
- **Key functions:** TBD (stub needs to be read — needs inspection)
- **Dependencies:** PyTorch Geometric; numpy; scipy (for KD-tree)
- **Gemini-ready:** Partially — needs Claude plan for feature encoding details
- **Plan needed:** Yes — depends on `parse_pdb.py` being done first
- **Tests needed:** Check shapes: x=(N,26), edge_attr=(E,2), edge_index=(2,E)

---

### `src/models/cryptic_gnn.py`
- **Status:** Implemented
- **Purpose:** CrypticGNN — 4-layer GATv2Conv + MLP scoring head; per-residue prioritization score
- **Key classes:** `NodeEmbedding`, `CrypticGNN`
- **Input:** `x (N,26)`, `edge_index (2,E)`, `edge_attr (E,2)`
- **Output:** `scores (N,)` ∈ [0, 1]
- **Plan needed:** No
- **Tests needed:** Forward pass smoke test with synthetic graph

---

### `src/training/loss.py`
- **Status:** Stub
- **Purpose:** Focal loss implementation (γ=2, α=0.25) for binary imbalanced classification
- **Dependencies:** PyTorch
- **Gemini-ready:** Yes — standard implementation, well-documented in literature
- **Plan needed:** Minimal — standard focal loss

---

### `src/training/dataset.py`
- **Status:** Stub
- **Purpose:** PyG `InMemoryDataset` or `Dataset` wrapper that loads pre-built `.pt` graph files from `data/graphs/` and labels from `data/labels/`
- **Dependencies:** PyTorch Geometric
- **Plan needed:** Yes — design split logic (protein-level, not residue-level)

---

### `src/training/train.py`
- **Status:** Partially implemented
- **Implemented:** `train_epoch()` — full training loop with optimizer, focal loss, device handling; `main()` — CLI args, DataLoader, model, optimizer, scheduler, early stopping, checkpointing
- **Stub remaining:** `eval_epoch()` — needs AUROC computation
- **Dependencies:** PyTorch, PyG, loss.py, dataset.py, cryptic_gnn.py, sklearn (for AUROC)
- **Plan needed:** Minimal — only `eval_epoch` needs implementing

---

### `src/evaluation/score_pockets.py`
- **Status:** Stub
- **Purpose:** Load pocket scores from model; threshold; cluster via DBSCAN; rank clusters; export JSON + scored PDB
- **Dependencies:** sklearn (DBSCAN); BioPython (PDB write); numpy
- **Plan needed:** Yes — clustering parameters (ε, min_samples) need validation

---

### `src/md/parse_trajectory.py`
- **Status:** Stub
- **Purpose:** Compute RMSF, DCCM, pocket volume from MD trajectory
- **Dependencies:** MDAnalysis; numpy; scipy; fpocket (optional)
- **Plan needed:** Yes — DCCM computation is non-trivial; volume tracking needs fpocket
- **Priority:** Lower — needed only after E002 passes

---

## Priority Execution Order

```
1. parse_pdb.py              → unblocks E001 (critical path)
2. graph_construction.py     → unblocks E001 (critical path)
3. loss.py                   → unblocks E002 training
4. dataset.py                → unblocks E002 training
5. train.py (eval_epoch)     → unblocks E002 evaluation
6. score_pockets.py          → unblocks E002 pocket ranking
7. parse_trajectory.py       → unblocks E003 (later)
```

## Key Observation: train.py Status

`train.py` is further along than it looks:
- `train_epoch()` — fully implemented (optimizer, focal loss, device)
- `main()` — fully implemented (CLI, DataLoader, checkpointing, early stopping)
- Only `eval_epoch()` is a stub (needs AUROC from sklearn)

This means the training pipeline is ~80% complete once loss.py and dataset.py are done.
