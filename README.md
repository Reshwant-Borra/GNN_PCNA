# GNN-PCNA: Cryptic Pocket Detection on PCNA via Graph Neural Network

**Authors:** Reshwant Borra · Advay (advay.awesomer@gmail.com)

---

## What This Project Does

PCNA (Proliferating Cell Nuclear Antigen) is a homotrimeric protein ring essential for DNA replication and repair. It is overexpressed in cancer, making it a drug target. The experimental compound **AOH1996** binds a cryptic pocket on PCNA (PDB: 8GLA) that is absent in the apo structure (PDB: 1W60).

**Cryptic pockets** are binding sites invisible in the static crystal but open transiently during protein motion. This pipeline:

1. Crawls 13 biological databases and builds a 160-node Obsidian knowledge graph
2. Represents a protein structure as a dual-view graph (spatial contacts + backbone connectivity)
3. Trains a 10.4M-parameter dual-branch GNN (PocketGNN v2) to score per-residue pocket probability
4. Visualises predictions in a Streamlit UI with PyMOL-ready export
5. Validates predictions via molecular dynamics (RMSF, DCCM, transient volume)

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
PocketGNN v2  (src/models/cryptic_gnn.py)
  Branch 1: 4× GATv2Conv on spatial contact graph (8 Å)
  Branch 2: 3× GATv2Conv on backbone sequential graph (|i−j| ≤ 2)
  → gated fusion → 4-layer MLP head → per-residue sigmoid score
  ↓
Streamlit UI  (src/ui/app.py)
  → sequence heatmap, top-residue table, chain symmetry check
  → B-factor PDB export (PyMOL) + CSV
  ↓
MD Validation  (src/md/parse_trajectory.py)
  → RMSF, DCCM, transient volume analysis
```

---

## Model Architecture — PocketGNN v2

| Component | Detail |
|---|---|
| Node features | 40 dims: aa_onehot(20), SASA, SS(3), B-factor, rel_pos, hydrophobicity, charge, volume, flexibility, sin/cos pseudo-dihedrals(4), local_density_5Å, local_density_10Å, interface_flag, chain_onehot(3) |
| Edge features | 6 dims: dist_norm, inv_dist, seq_sep_norm, same_chain, is_backbone, cross_chain |
| Pre-encoder | Linear(40→256→512→768) + LayerNorm |
| Branch 1 (spatial) | 4× GATv2Conv(768, heads=8, edge_dim=6) with residuals |
| Branch 2 (sequential) | 3× GATv2Conv(768, heads=8, edge_dim=6) with residuals |
| Fusion | Learned gate per residue: `gate * h_spatial + (1-gate) * h_seq` |
| Scoring head | Linear(768→384→192→96→1) + ReLU + Dropout at each layer |
| Output | Per-residue pocket probability ∈ [0, 1] |
| Parameters | ~10.4M (large) · ~3.6M (medium) · ~907k (small) |
| Loss | Focal(γ=2, α=0.25) + 0.05×Ranking(margin=0.2) + 0.10×Symmetry (finetune only) |

CrypticGNN v1 (~850k params, single-branch, 26-dim nodes) is preserved for comparison.

---

## Scientific Ground Truth

| Item | Detail |
|---|---|
| Apo structure | PDB **1W60** — no AOH1996 pocket visible |
| Holo structure | PDB **8GLA** — AOH1996 bound, cryptic pocket open |
| Ground truth labels | Residues within 6 Å of AOH1996 in 8GLA |
| Validation gate | Model MUST score AOH1996 pocket residues > 0.7 before trusting novel predictions |
| Pre-training data | CryptoSite benchmark (87 known cryptic pocket proteins) |
| PCNA UniProt | P12004 · homotrimer (chains A, B, C) |

---

## Quick Start

```bash
# 1. Install dependencies
pip install torch torch_geometric
pip install -r requirements-ui.txt
pip install streamlit pandas matplotlib requests mcp scikit-learn

# 2. Fetch PCNA structures
python src/data_processing/fetch_structures.py

# 3. Run the Streamlit UI
streamlit run src/ui/app.py

# 4. Train (pre-train on CryptoSite)
python -m src.training.train \
  --train_dir data/cryptosite/train \
  --val_dir   data/cryptosite/val \
  --model_size large \
  --phase pretrain \
  --checkpoint_dir checkpoints/pretrain/ \
  --epochs 100 --lr 1e-3 --patience 15

# 5. Fine-tune on PCNA (enables symmetry loss)
python -m src.training.train \
  --train_dir data/pcna/train \
  --val_dir   data/pcna/val \
  --model_size large \
  --phase finetune \
  --resume checkpoints/pretrain/best.ckpt \
  --checkpoint_dir checkpoints/finetune/ \
  --epochs 50 --lr 3e-4 --patience 10

# 6. Start the MCP server (connects Obsidian vault to Claude)
python agents/mcp_server.py
```

---

## MCP Server

`agents/mcp_server.py` exposes the Obsidian vault and model inference to Claude Code via FastMCP.

Tools: `list_structures`, `get_structure`, `search_vault`, `list_papers`, `list_datasets`, `get_knowledge_graph`, `run_inference`, `get_pipeline_status`

Add to Claude Code via `.claude/mcp.json` (already configured in this repo).

---

## Stack

| Tool | Purpose |
|---|---|
| Python 3.10+ | Language |
| PyTorch Geometric | GNN (GATv2Conv) |
| MDAnalysis | MD trajectory parsing |
| BioPython / ProDy | PDB structure parsing |
| scikit-learn | AUROC evaluation |
| Streamlit | Interactive UI |
| FastMCP | Claude Code MCP server |

---

## Validation Targets

| Metric | Minimum bar | Strong result |
|---|---|---|
| AOH1996 pocket mean score on 8GLA | > 0.7 | — |
| AOH1996 pocket rank | top-3 | top-1 |
| AUROC on CryptoSite held-out | > 0.65 | > 0.80 |
| Novel pocket RMSF | — | > 1.5 Å |
| Novel pocket transient volume | — | > 100 Å³ |

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
