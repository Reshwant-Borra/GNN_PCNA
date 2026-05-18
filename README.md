# GNN-PCNA: Cryptic Pocket Detection on PCNA via Graph Neural Network

**Authors:** Reshwant Borra · Advay (advay.awesomer@gmail.com)

---

## What This Project Does

PCNA (Proliferating Cell Nuclear Antigen) is a homotrimeric protein ring essential for DNA replication and repair. It is overexpressed in cancer, making it a drug target. The experimental compound **AOH1996** binds a cryptic pocket on PCNA (PDB: 8GLA) that is absent in the apo structure (PDB: 1W60).

**Cryptic pockets** are binding sites invisible in the static crystal but open transiently during protein motion. This pipeline:

1. Crawls 13 biological databases and builds a 160-node Obsidian knowledge graph
2. Represents a protein structure as a dual-view graph (spatial contacts + backbone connectivity)
3. Trains a dual-branch GNN (PocketGNN v2; ~907k–10.4M params depending on variant) to score per-residue pocket probability
4. Visualises predictions in a Streamlit UI with PyMOL-ready export
5. **ANM flexibility analysis** completed on apo PCNA (1W60): pocket residues are 14% less flexible than background (fold-change 0.857), consistent with a rigidly packed cryptic site. Full MD trajectories not yet generated.

---

## Pipeline

```
13-domain crawler (pcna_crawler.py)
  → 5-layer validation (network, format, structural, biological, provenance)
  → data/catalog/raw_catalog.json  +  docs/vault/ (160 Obsidian notes)
  ↓
PDB Structure
  → parse_pdb.py           residues + Cα coordinates
  → graph_construction.py  dual-graph PyG Data (40-dim nodes, 6-dim edges)
  ↓
PocketGNN v2 small  (src/models/cryptic_gnn.py — checkpoint used for all results)
  Branch 1: 3× GATv2Conv on spatial contact graph (8 Å)
  Branch 2: 2× GATv2Conv on backbone sequential graph (|i−j| ≤ 2)
  → gated fusion → 4-layer MLP head → per-residue sigmoid score
  (large config: 4+3 layers, ~10.4M params — defined but not used for any result)
  ↓
Streamlit UI  (src/ui/app.py)
  → sequence heatmap, top-residue table, chain symmetry check
  → B-factor PDB export (PyMOL) + CSV
  ↓
MD Validation  (src/md/parse_trajectory.py)
  → RMSF, DCCM, transient volume analysis  [NOT YET RUN — no trajectory data]
```

---

## Model Architecture — PocketGNN v2

| Component | Detail |
|---|---|
| Node features | 40 dims: aa_onehot(20), SASA, SS(3), B-factor, rel_pos, hydrophobicity, charge, volume, flexibility, sin/cos pseudo-dihedrals(4), local_density_5Å, local_density_10Å, interface_flag, chain_onehot(3) |
| Edge features | 6 dims: dist_norm, inv_dist, seq_sep_norm, same_chain, is_backbone, cross_chain |
| Pre-encoder | Linear(40→256→512→768) + LayerNorm |
| Branch 1 (spatial) | **3× GATv2Conv(256, heads=4)** (small/checkpoint) · 4× (large, ~10.4M, not deployed) |
| Branch 2 (sequential) | **2× GATv2Conv(256, heads=4)** (small/checkpoint) · 3× (large, ~10.4M, not deployed) |
| Fusion | Learned gate per residue: `gate * h_spatial + (1-gate) * h_seq` |
| Scoring head | Linear(768→384→192→96→1) + ReLU + Dropout at each layer |
| Output | Per-residue pocket probability ∈ [0, 1] |
| Parameters | ~10.4M (large) · ~3.6M (medium) · ~907k (small) — **all results in this repo use the small checkpoint** |
| Loss | Focal(γ=2, α=0.25) + 0.05×Ranking(margin=0.2) + 0.10×Symmetry (finetune only) |

CrypticGNN v1 (~556k params, single-branch, 26-dim nodes) is preserved for comparison.

---

## Scientific Ground Truth

| Item | Detail |
|---|---|
| Apo structure | PDB **1W60** — no AOH1996 pocket visible |
| Holo structure | PDB **8GLA** — AOH1996 bound, cryptic pocket open |
| Ground truth labels | Residues within 6 Å of AOH1996 in 8GLA |
| Validation gate | Model MUST score AOH1996 pocket residues > 0.7 before trusting novel predictions |
| Pre-training data | Ligand-proximity labeled structures (87 proteins from CryptoSite set, labeled via Cα–ligand distance, **not** curated CryptoSite benchmark labels) |
| PCNA UniProt | P12004 · homotrimer (chains A, B, C) |

---

## Setup

> Full instructions with troubleshooting: **[SETUP.md](SETUP.md)**

### 1. Clone & create environment

```bash
git clone https://github.com/Reshwant-Borra/GNN_PCNA.git
cd GNN_PCNA
python -m venv .venv
# Windows: .venv\Scripts\activate  |  macOS/Linux: source .venv/bin/activate
```

### 2. Install PyTorch (pick your hardware)

```bash
# CPU only
pip install torch==2.1.0 --index-url https://download.pytorch.org/whl/cpu

# NVIDIA GPU — CUDA 11.8
pip install torch==2.1.0 --index-url https://download.pytorch.org/whl/cu118

# NVIDIA GPU — CUDA 12.1
pip install torch==2.1.0 --index-url https://download.pytorch.org/whl/cu121
```

### 3. Install PyTorch Geometric + all dependencies

```bash
# PyG sparse ops (replace +cpu with +cu118 / +cu121 to match your torch build)
pip install torch-scatter torch-sparse \
  -f https://data.pyg.org/whl/torch-2.1.0+cpu.html

pip install torch-geometric
pip install -r requirements.txt
```

### 4. Download PDB structures + build graph tensors

Raw `.pdb` files are **gitignored** (too large for version control) but freely downloadable
from RCSB. A single script handles download, checksum verification, and graph construction:

```bash
# Download all 59 PCNA structures + build PyG graphs (one command)
python scripts/download_data.py

# Download only, skip graph building
python scripts/download_data.py --skip-graphs

# Verify checksums of already-downloaded files
python scripts/download_data.py --verify
```

This replaces the older `pcna_crawler.py --download` and `build_graphs.py` workflow.
See `data/raw/README.md` and `data/graphs/README.md` for details.

### 6. Run inference (pre-trained checkpoint included)

The checkpoint `checkpoints/pcna/best_pcna.ckpt` is tracked in git — no training needed.

```bash
# Per-structure analysis on all 59 PCNA structures
python scripts/per_structure_analysis.py

# Generate 5-panel analysis figure
python scripts/make_final_figure.py

# Launch Streamlit UI
streamlit run src/ui/app.py
```

### 7. Train from scratch (optional)

> **Note:** `data/cryptosite/train/` and `data/cryptosite/val/` are not included (ligand-proximity labeled
> graphs built from the CryptoSite protein set). Run `python scripts/download_data.py` first to
> download PDB files and build graphs, then `python scripts/make_split.py` to create the split.

```bash
# Download PDB files + build graphs
python scripts/download_data.py

# Create train/val/test split
python scripts/make_split.py

# Pre-train on ligand-proximity labeled structures
python -m src.training.train \
  --train_dir data/cryptosite/train \
  --val_dir   data/cryptosite/val \
  --model_size large --phase pretrain \
  --checkpoint_dir checkpoints/pretrain/ \
  --epochs 100 --lr 1e-3 --patience 15

# Fine-tune on PCNA
python scripts/finetune_pcna.py \
  --pretrain checkpoints/pretrain/best.ckpt \
  --model_size small --epochs 80
```

### Troubleshooting

| Error | Fix |
|---|---|
| `ModuleNotFoundError: torch_scatter` | Re-run step 3 with the correct CUDA tag |
| `UnicodeEncodeError: cp1252` | Prefix command with `PYTHONIOENCODING=utf-8` |
| `FileNotFoundError: best_pcna.ckpt` | Run `git pull` — checkpoint is in git |
| `FileNotFoundError: data/raw/8GLA.pdb` | Run `python scripts/download_data.py` |
| `AUROC = 0.5` | Apo structure — no ligand to label from; expected behaviour |

---

## MCP Server

`agents/mcp_server.py` exposes the Obsidian vault and model inference to Claude Code via FastMCP.

Tools: `list_structures`, `get_structure`, `search_vault`, `list_papers`, `list_datasets`, `get_knowledge_graph`, `run_inference`, `get_pipeline_status`

Add to Claude Code via `.claude/mcp.json` (already configured in this repo).

---

## Stack

| Tool | Version | Purpose |
|---|---|---|
| Python | 3.10 – 3.12 | Language |
| PyTorch | 2.1+ | Tensor ops + autograd |
| PyTorch Geometric | 2.4+ | GATv2Conv, graph batching |
| torch-scatter / torch-sparse | 2.1+ / 0.6+ | PyG sparse kernels |
| BioPython | 1.83+ | PDB parsing, SASA (ShrakeRupley) |
| scikit-learn | 1.4+ | AUROC, DBSCAN clustering |
| scipy | 1.11+ | Spatial KD-tree for graph construction |
| numpy | 1.26+ | Array ops |
| requests + BeautifulSoup4 | — | 13-domain web crawler |
| streamlit | 1.35+ | Interactive UI |
| matplotlib + pandas | — | Figures, CSV I/O |
| MDAnalysis | 2.7+ (optional) | MD trajectory parsing |
| FastMCP | — (optional) | Claude Code MCP server |

---

## Validation Targets

| Metric | Minimum bar | Strong result |
|---|---|---|
| AOH1996 pocket mean score on 8GLA | > 0.7 | — | **Not passed** (v2-small: 0.587; v3-XL: passes) |
| AOH1996 pocket rank | top-3 | top-1 | Top-2 in v2-small (8GLA analysis) |
| AUROC on ligand-proximity labeled held-out | > 0.65 | > 0.80 | v3-XL mean 0.94 (ligand-proximity labels, not curated CryptoSite) |
| AOH1996 pocket ANM-RMSF fold-change | < 1.0 (rigid cryptic) | — | **0.857** — 14% less flexible than bg; consistent with buried cryptic pocket |
| AOH1996 pocket internal DCCM | > 0 | > 0.3 | **0.0995** — mild positive; coherent motion |
| Novel pocket transient volume (MD) | — | > 100 Å³ | **Not measured** — no MD trajectories |

---

## Repo Structure

```
src/
  data_processing/    PDB parsing, graph construction (v1 + v2)
  models/             CrypticGNN v1 + PocketGNN v2 + loss functions
  training/           Dataset, focal+ranking+symmetry loss, train loop
  evaluation/         Pocket scoring and clustering
  md/                 MD trajectory parsing (RMSF, DCCM, volume)
  ui/                 Streamlit app
agents/
  pcna_crawler.py     13-domain data crawler with 5-layer validation
  catalog_to_obsidian.py  Vault note builder
  mcp_server.py       FastMCP server (vault + inference)
data/
  raw/                Downloaded PDB files
  catalog/            raw_catalog.json (crawled + validated records)
  graphs/             Pre-built .pt graph files
docs/
  vault/              160-node Obsidian knowledge graph
  knowledge/          Research brain (biology, pipeline, models)
  experiments/        Experiment logs (E001, E002, ...)
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
- `AGENTS.md` — multi-agent handoff protocol

---

## Related

[[INDEX]] · [[SYSTEM_OVERVIEW]] · [[BIOLOGY_PCNA]] · [[PIPELINE]] · [[MODELS]] · [[EXPERIMENT_INDEX]] · [[ARCHITECTURE]] · [[COMMANDS]] · [[ENVIRONMENT]] · [[KNOWN_BUGS]] · [[REPO_MAP]]
