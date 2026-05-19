# GNN-PCNA: Cryptic Pocket Detection on PCNA via Graph Neural Network

**Authors:** Reshwant Borra · Advay (advay.awesomer@gmail.com)

---

## What This Project Does

This project develops a residue-level GNN scoring pipeline for PCNA and related protein structures. It uses ligand-proximity labels, including the ZQZ/AOH1996-1LE ligand-contact region in PDB 8GLA as a PCNA positive control, and reports high AUROC but mixed precision-recall behavior on a small held-out ligand-proximity-labeled benchmark. **The current evidence supports using the model to prioritize candidate residue clusters for follow-up study, but it does not yet establish novel cryptic pockets, druggability, docking readiness, apo-to-holo opening, or AOH1996 mechanism.**

Human PCNA (UniProt P12004) is a homotrimeric sliding clamp involved in DNA replication and repair. PDB 8GLA contains PCNA bound to AOH1996 derivative AOH1996-1LE (ligand ZQZ, resolution 3.77 Å, chains A–D in asymmetric unit) and is used here as a positive-control ligand-contact region. PDB 1W60 is apo/native PCNA (chains A/B in asymmetric unit, resolution 3.15 Å).

This pipeline:

1. Crawls 13 biological databases and builds a 160-node Obsidian knowledge graph
2. Represents a protein structure as a dual-view graph (spatial contacts + backbone connectivity)
3. Trains a dual-branch GNN (PocketGNN v2; ~907k–10.4M params depending on variant) to score per-residue prioritization likelihood
4. Visualises predictions in a Streamlit UI with PyMOL-ready export
5. **ANM flexibility analysis** completed on apo PCNA (1W60): pocket residues are 14% less flexible than background (fold-change 0.857), consistent with a rigidly packed cryptic site. Full MD trajectories not yet generated.

> **Read before interpreting results:** [LIMITATIONS.md](LIMITATIONS.md) documents every known constraint — labeling approximations, asymmetric-unit caveats, metric interpretation, and what the model can and cannot claim.

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
PocketGNNXL  (src/models/cryptic_gnn.py — primary checkpoint: checkpoints/pcna/best_pcna_v3_fixed.ckpt)
  Branch 1: 5× GATv2Conv on spatial contact graph (8 Å)
  Branch 2: 4× GATv2Conv on backbone sequential graph (|i−j| ≤ 2)
  → gated fusion → virtual-node → MLP head → per-residue sigmoid score
  (small config: 3+2 layers, ~907k params — available as checkpoints/reproduced/best.ckpt)
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
| Output | Per-residue prioritization score (not a calibrated probability) ∈ [0, 1] |
| Parameters | ~13.4M (XL) · ~10.4M (large) · ~3.6M (medium) · ~907k (small) — **primary results use `checkpoints/pcna/best_pcna_v3_fixed.ckpt` (fully reproduced, seed=42 end-to-end)** |
| Loss | Focal(γ=2, α=auto-calibrated from class balance) + 0.05×Ranking(margin=0.2) + 0.10×Symmetry (finetune only) |

CrypticGNN v1 (~556k params, single-branch, 26-dim nodes) is preserved for comparison.

---

## Scientific Ground Truth

| Item | Detail |
|---|---|
| Apo structure | PDB **1W60** — no AOH1996 pocket visible |
| Holo structure | PDB **8GLA** — AOH1996 bound, cryptic pocket open |
| Ground truth labels | Residues whose Cα is within 6 Å of any heavy atom of ligand ZQZ (AOH1996) in PDB 8GLA |
| Positive-control check | Score > 0.7 on 8GLA AOH pocket confirms the checkpoint retained fine-tuning signal (8GLA was in fine-tuning data — this is a sanity check, not independent validation) |
| Pre-training data | Ligand-proximity labeled structures (87 proteins from a CryptoSite-derived set, labeled via Cα–ligand distance, **not** curated CryptoSite benchmark labels) |
| PCNA UniProt | P12004 · homotrimer (chains A, B, C) |

---

## Setup

> Full instructions with troubleshooting: **[SETUP.md](SETUP.md)**

> **IMPORTANT FOR AUTOMATED REVIEW / CI:** Do NOT run `pip install -r requirements.txt` directly.
> `torch-scatter` and `torch-sparse` require a wheel URL that matches your CUDA build.
> Use the provided install script instead (see Step 2).

### 1. Clone & create environment

```bash
git clone https://github.com/Reshwant-Borra/GNN_PCNA.git
cd GNN_PCNA
python -m venv .venv
# Windows: .venv\Scripts\activate  |  macOS/Linux: source .venv/bin/activate
```

### 2. Install all dependencies (use the install script — not pip install -r directly)

```bash
# CPU-only (default — works on any machine)
bash install.sh

# NVIDIA GPU — CUDA 11.8
bash install.sh cu118

# NVIDIA GPU — CUDA 12.1
bash install.sh cu121

# Windows
install.bat        # CPU
install.bat cu118  # NVIDIA GPU
```

Why: `torch-scatter` and `torch-sparse` must be installed from the PyG wheel server with
a tag matching your torch+CUDA build. A plain `pip install -r requirements.txt` will fail
or install incompatible binaries — see comments in `requirements.txt`.

### 4. PDB structures + graph tensors (already in repo)

All 150 raw `.pdb` files (59 PCNA structures + 91 CryptoSite benchmark proteins) and graph `.pt` files are **committed to this repo** — no download step needed after cloning. SHA256 checksums are at `data/manifests/pdb_checksums.json`.

To verify checksums or re-download from scratch:

```bash
# Verify checksums of committed files
python scripts/download_data.py --verify

# Re-download all PDB files from RCSB (overwrites local)
python scripts/download_data.py --force
```

### 6. Run inference (pre-trained checkpoint included)

The primary checkpoint `checkpoints/pcna/best_pcna_v3_fixed.ckpt` is tracked in git — no training needed. It is a fully reproduced XL model (seed=42 end-to-end, pretrain → PCNA fine-tune).

```bash
# Validate AOH1996 pocket recovery gate
python scripts/aoh_gate_check.py --ckpt checkpoints/pcna/best_pcna_v3_fixed.ckpt --model xl

# Per-structure analysis on all 59 PCNA structures
python scripts/per_structure_analysis.py

# Generate 5-panel analysis figure
python scripts/make_final_figure.py

# Launch Streamlit UI
streamlit run src/ui/app.py
```

### 7. Train from scratch (optional)

> **Note:** The train/val/test split is defined in `data/splits/cryptosite_split.json` (42/8/5 proteins).
> Graphs are in `data/graphs/` with ligand-proximity labels (Cα–ligand distance, **not** curated CryptoSite benchmark annotations).
> To rebuild from scratch: `python scripts/download_data.py` then `python scripts/make_split.py`.

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

| Metric | Minimum bar | Strong result | Status |
|---|---|---|---|
| AOH1996 pocket mean score on 8GLA | > 0.7 | — | **PASS** — reproduced fine-tuned XL: 0.8676, rank 1 (small: FAIL 0.5998) |
| AOH1996 pocket rank | top-3 | top-1 | **PASS** — rank 1 (reproduced fine-tuned XL) |
| Test AUROC, protein-level held-out (5 proteins, 3 different families) | > 0.65 | > 0.80 | **PASS** — reproduced fine-tuned XL: 0.9390; note AUROC inflated by class imbalance |
| Test AUPRC (average precision), same 5 proteins | > trivial baseline (~0.08) | > 0.40 | **Partial** — 0.3706 (4.6× above trivial baseline of ~0.08; not strong absolute performance) |
| ANM apo/holo fold-change delta | > 0 | > 0.2 | **PASS** — delta = +0.247 (apo 0.857 → holo 1.104); consistent with flexibility difference, not proof of opening |
| Internal pocket DCCM (apo) | > 0 | > 0.3 | **Partial** — 0.0995 (mild positive coherent motion) |
| Novel pocket transient volume (MD) | — | > 100 Å³ | Not measured — no MD trajectories |

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
