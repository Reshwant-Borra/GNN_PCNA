# GNN-PCNA: Cryptic Pocket Detection on PCNA via Graph Neural Network

**Authors:** Reshwant Borra · Advay (advay.awesomer@gmail.com)

---

## What This Project Does

PCNA (Proliferating Cell Nuclear Antigen) is a homotrimeric protein ring essential for DNA replication and repair. It is overexpressed in cancer, making it a drug target. The experimental compound **AOH1996** binds a known site on PCNA (PDB: 8GLA).

**Cryptic pockets** are binding sites that are invisible in the static crystal structure but open transiently during protein motion. This project builds a GNN-based pipeline to:

1. Represent a protein structure as a graph (residues = nodes, spatial contacts = edges)
2. Train a GNN to score each residue's likelihood of belonging to a cryptic pocket
3. Validate predictions using molecular dynamics (MD) simulation
4. Discover novel druggable sites on PCNA beyond the known AOH1996 site

---

## Pipeline

```
PDB Structure (1W60 apo / 8GLA holo)
  → Graph Construction   src/data_processing/graph_construction.py
      residues as nodes (26 features each)
      edges by Cα–Cα distance + contact type (2 edge features)
  → CrypticGNN           src/models/cryptic_gnn.py
      4-layer GATv2 with residual connections
      per-residue sigmoid pocket score
  → Pocket Scoring       src/evaluation/score_pockets.py
  → MD Validation        src/md/parse_trajectory.py
      RMSF, DCCM, transient volume analysis
  → Ranked novel cryptic sites
```

---

## Model Architecture

`CrypticGNN` (`src/models/cryptic_gnn.py`):

| Component | Detail |
|---|---|
| Node embedding | Linear(26 → 256) + ReLU + LayerNorm |
| Message passing | 4 × GATv2Conv (256-dim, 4 heads, edge features) |
| Residuals | LayerNorm(h + conv(h)) at every layer |
| Scoring head | Linear(256→64) → ReLU → Dropout → Linear(64→1) → Sigmoid |
| Output | Per-residue pocket probability ∈ [0, 1] |

Training uses **focal loss** (`src/training/loss.py`) to handle the severe class imbalance between pocket and non-pocket residues.

---

## Scientific Ground Truth

| Item | Detail |
|---|---|
| Apo structure | PDB **1W60** — no AOH1996 pocket visible |
| Holo structure | PDB **8GLA** — AOH1996 bound, cryptic pocket open |
| Ground truth labels | Residues within 6 Å of AOH1996 in 8GLA |
| Validation gate | Model MUST score AOH1996 pocket residues > 0.7 before trusting novel predictions |
| Pre-training data | CryptoSite benchmark (known cryptic pocket proteins) |

---

## Stack

| Tool | Purpose |
|---|---|
| Python 3.10+ | Language |
| PyTorch Geometric | GNN (GATv2Conv) |
| MDAnalysis | Molecular dynamics trajectory parsing |
| BioPython / ProDy | PDB structure parsing |
| scikit-learn | AUROC evaluation |
| py3Dmol | 3D visualization |

---

## Running

```bash
python -m src.training.train \
  --train_dir data/cryptosite/train \
  --val_dir   data/cryptosite/val \
  --checkpoint_dir checkpoints/ \
  --epochs 100 \
  --batch_size 16 \
  --lr 1e-3 \
  --patience 10
```

Data must be pre-built as PyG `.pt` graph files (see `src/data_processing/`).

---

## Validation Targets

| Metric | Minimum bar | Strong result |
|---|---|---|
| AOH1996 pocket mean score on 8GLA | > 0.7 | — |
| AOH1996 pocket rank | top-3 | top-1 |
| AUROC on CryptoSite held-out | > 0.65 | > 0.80 |
| Novel pocket RMSF | — | > 1.5 Å |
| Novel pocket volume | — | > 100 Å³ transiently |

---

## Repo Structure

```
src/
  data_processing/    PDB parsing + graph construction
  models/             CrypticGNN architecture
  training/           Dataset, focal loss, train loop
  evaluation/         Pocket scoring
  md/                 MD trajectory parsing
docs/
  knowledge/          Research brain (biology, pipeline, models)
  experiments/        Experiment logs (E001, E002, ...)
  data/               Data inventory and schema
  plans/              Implementation plan files
  prompts/            AI agent prompt templates
```

---

## Key Docs

- `docs/knowledge/SYSTEM_OVERVIEW.md` — high-level system description
- `docs/knowledge/BIOLOGY_PCNA.md` — PCNA biology background
- `docs/knowledge/PIPELINE.md` — data pipeline details
- `docs/knowledge/MODELS.md` — model design decisions
- `docs/experiments/EXPERIMENT_INDEX.md` — all experiments
- `KNOWN_BUGS.md` — known issues
- `CLAUDE.md` — AI agent workflow rules

---

## Related

[[INDEX]] · [[SYSTEM_OVERVIEW]] · [[BIOLOGY_PCNA]] · [[PIPELINE]] · [[MODELS]] · [[EXPERIMENT_INDEX]] · [[ARCHITECTURE]] · [[COMMANDS]] · [[ENVIRONMENT]] · [[KNOWN_BUGS]] · [[REPO_MAP]]
