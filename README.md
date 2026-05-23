# GNN-PCNA: Cryptic Pocket Detection on PCNA via Graph Neural Network

**Authors:** Reshwant Borra · Advay (advay.awesomer@gmail.com)

---

## What This Project Does

This project develops a residue-level GNN scoring pipeline for PCNA and related protein structures. It uses ligand-proximity labels, including the ZQZ/AOH1996-1LE ligand-contact region in PDB 8GLA as a PCNA positive control. **Previous random-split benchmark numbers are superseded because homology leakage was detected. The current clean-split benchmark is an MMseqs2 30% homology-clean, three-seed ablation suite. The best condition is ESM2-augmented XL (`xl_esm_full`): test AUPRC 0.2513 (95% CI 0.1267-0.3815), AUROC 0.8649. Geometry-only XL is weaker but above the small model (AUPRC 0.1923), while ESM-zero XL drops to 0.1071, so sequence/ESM2 contribution is a major confound. The current evidence supports using the model to prioritize candidate residue clusters for follow-up study, but it does not yet establish novel cryptic pockets, druggability, docking readiness, apo-to-holo opening, or AOH1996 mechanism.**

Human PCNA (UniProt P12004) is a homotrimeric sliding clamp involved in DNA replication and repair. PDB 8GLA contains PCNA bound to AOH1996 derivative AOH1996-1LE (ligand ZQZ, resolution 3.77 Å, chains A–D in asymmetric unit) and is used here as a positive-control ligand-contact region. PDB 1W60 is apo/native PCNA (chains A/B in asymmetric unit, resolution 3.15 Å).

This pipeline:

1. Crawls 13 biological databases and builds a 160-node Obsidian knowledge graph
2. Represents a protein structure as a dual-view graph (spatial contacts + backbone connectivity)
3. Trains a dual-branch GNN (PocketGNN v2; ~907k–10.4M params depending on variant) to score per-residue prioritization likelihood
4. Visualises predictions in a Streamlit UI with PyMOL-ready export
5. **Preliminary dynamics checks** exist for apo PCNA (1W60), but they do not validate pocket opening. Current final reporting treats PCNA outputs as residue prioritization / hypothesis generation.

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
PocketGNNXL  (src/models/cryptic_gnn.py — final reporting checkpoint: checkpoints/clean_split/xl_esm_full/seed_42/best.ckpt)
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
  → RMSF, DCCM, transient volume analysis  [preliminary only; current MD fold-change <1.0 is not supportive of enhanced apo pocket flexibility]
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
| Parameters | ~13.4M (XL) · ~10.4M (large) · ~3.6M (medium) · ~907k (small) — **final PCNA reporting uses `checkpoints/clean_split/xl_esm_full/seed_42/best.ckpt`** |
| Loss | Focal(γ=2, α=auto-calibrated from class balance) + 0.05×Ranking(margin=0.2) + 0.10×Symmetry (finetune only) |

CrypticGNN v1 (~556k params, single-branch, 26-dim nodes) is preserved for comparison.

**Architectural novelty:** GATv2Conv has not been applied to per-residue cryptic pocket scoring in any published paper as of early 2026. The dominant published baseline (PocketMiner, Meller et al. 2023, *Nature Communications*) uses GVP-GNN (equivariant geometric vector perceptrons). This pipeline's dual-branch GATv2Conv design is a novel contribution relative to that baseline.

---

## Benchmark Context

| Method | Architecture | Dataset | AUROC | PR-AUC / AUPRC | Reference |
|---|---|---|---|---|---|
| CryptoSite | SVM + coevolution features | 93 proteins | 0.83 | not reported | Cimermancic et al. 2016, JMB |
| PocketMiner | GVP-GNN (equivariant) | 39 proteins (test) | **0.87** | **0.44** (5-fold CV) | Meller et al. 2023, Nat Comms |
| 3D-CNN baseline | 3D CNN | same | 0.79 | 0.41 | Meller et al. 2023 |
| **This work (clean split)** | Dual-branch GATv2Conv + ESM2 | MMseqs2 30% homology-clean split | 0.8649 | 0.2513 (95% CI 0.1267-0.3815) | This repo |
| Random baseline | — | any, ~5–10% pos | 0.50 | ~pos_fraction | — |

**Important caveats for this comparison:**
- AUPRC is only directly comparable between datasets with the same positive residue fraction. PocketMiner's positive rate (~5–10% of residues) may differ from ours (~5–15%). A fair comparison requires evaluating on the same benchmark split.
- Our training labels use Cα-proximity heuristics; PocketMiner uses curated experimentally confirmed cryptic pockets. This makes our task harder to evaluate but easier to scale.
- Earlier 5-protein and 13-protein random-split results are superseded by the homology leakage audit and must not be used as headline benchmark claims.
- The best clean-split result is ESM2-augmented. Geometry-only XL is lower (AUPRC 0.1923), and ESM-zero XL is lower still (AUPRC 0.1071), so final framing must disclose ESM2/sequence contribution.
- A 2024 benchmark (CryptoBench, Skrhak et al., *Bioinformatics*) scales to 1,107 structures with a pLM-NN baseline outperforming PocketMiner — future work should evaluate on CryptoBench.

---

## Scientific Ground Truth

| Item | Detail |
|---|---|
| Apo structure | PDB **1W60** — no AOH1996 pocket visible |
| Holo structure | PDB **8GLA** — AOH1996 bound, cryptic pocket open |
| Ground truth labels | Residues whose Cα is within 6 Å of any heavy atom of ligand ZQZ (AOH1996) in PDB 8GLA |
| Positive-control check | Score > 0.7 on 8GLA AOH pocket confirms the checkpoint retained fine-tuning signal (8GLA was in fine-tuning data — this is a positive-control sanity check, not independent performance) |
| Pre-training data | Ligand-proximity labeled structures from a CryptoSite-derived set, labeled via Cα–ligand distance, **not** curated CryptoSite benchmark labels. Final clean-split metrics use `data/splits/cryptosite_homology30_split.json`. |
| PCNA UniProt | P12004 · homotrimer (chains A, B, C) |

---

## Current PCNA Reporting Result

Final PCNA reports use `xl_esm_full` as the clean-split reporting checkpoint and must be labeled:

> ESM2-augmented GNN prioritization results.

The regenerated PCNA outputs changed the old conclusion materially. The highest-ranked structure is `1W60`, but its top cluster is only four residues (`B42-B45`), with mean score 0.710175 and three overlaps with the MD/AOH-region residue set. The complete AOH1996/MD pocket is not recovered as a ranked cluster, and `8GLA` has no thresholded DBSCAN cluster under the regenerated clean-split checkpoint.

Final defensible conclusion: using the homology-clean `xl_esm_full` checkpoint, the PCNA analysis identifies sparse, biologically plausible residue-prioritization signals near the AOH/PIP-groove region, but does not robustly recover the known AOH1996 pocket and should be framed as hypothesis generation rather than hidden-pocket discovery.

Primary regenerated outputs:

- `results/per_structure/pcna_rankings.csv`
- `results/per_structure/pocket_score_summaries.csv`
- `results/per_structure/summary_table.csv`
- `results/per_structure/regeneration_manifest_xl_esm_full.json`
- `results/figures/pcna_xl_esm_full_*.png`

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

All 149 raw `.pdb` files (59 PCNA structures + 90 CryptoSite benchmark proteins) and graph `.pt` files are **committed to this repo** — no download step needed after cloning. SHA256 checksums are at `data/manifests/pdb_checksums.json`.

To verify checksums or re-download from scratch:

```bash
# Verify checksums of committed files
python scripts/download_data.py --verify

# Re-download all PDB files from RCSB (overwrites local)
python scripts/download_data.py --force
```

### 6. Run inference (pre-trained checkpoint included)

The primary checkpoint `checkpoints/pcna_reproduced/best.ckpt` is tracked in git — no training needed. It is a fully reproduced XL model (~13.4M params, node_in_dim=520 with ESM2 features, seed=42 end-to-end, AOH gate PASS 0.8676).

**Model variants and which scripts use them:**

| Script | Model | Checkpoint | Node dim | Notes |
|---|---|---|---|---|
| `aoh_gate_check.py` | XL (13.4M) | `pcna_reproduced/best.ckpt` | 520 | Uses pre-built XL graphs from `data/pcna_xl/` |
| `run_test_eval.py` | XL (13.4M) | `pcna_reproduced/best.ckpt` | 520 | Uses pre-built XL graphs from `data/graphs_xl/` |
| `per_structure_analysis.py` | small (907k) | `pcna/best_pcna.ckpt` | 40 | Uses `build_graph_v2` (no ESM2 required); suitable for all 59 PCNA structures |
| `src/ui/app.py` | XL (13.4M) | `pcna_reproduced/best.ckpt` | 520 | Interactive UI with pre-built graphs |

ESM2 (`facebook/esm2_t12_35M_UR50D`) is required only to build new XL graphs. Pre-built XL graphs are committed to this repo for the evaluation set and three PCNA structures.

```bash
# Validate AOH1996 positive-control recovery (XL checkpoint, pre-built XL graph)
python scripts/aoh_gate_check.py

# Evaluate XL checkpoint on all 13 held-out val+test proteins (XL graphs, labeled)
python scripts/run_test_eval.py --ckpt checkpoints/pcna_reproduced/best.ckpt --model xl --graphs data/graphs_xl

# Per-structure analysis on all 59 PCNA structures (small model, no ESM2 needed)
python scripts/per_structure_analysis.py

# Generate 5-panel analysis figure
python scripts/make_final_figure.py

# Launch Streamlit UI (XL model)
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
  --train_manifest data/splits/cryptosite_split.json \
  --graph_dir data/graphs \
  --model_size xl --phase pretrain \
  --checkpoint_dir checkpoints/pretrain/ \
  --epochs 100 --lr 3e-4 --patience 15

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

## Validation Status

### Positive-control sanity check (not independent validation)

| Metric | Threshold | Result |
|---|---|---|
| AOH1996 pocket mean score on 8GLA | > 0.7 | **PASS** — XL checkpoint: 0.8676, rank 1 |
| AOH1996 pocket rank | top-3 | **PASS** — rank 1 |

> **Note:** 8GLA was in the fine-tuning data. This is a sanity check that the model retained its training signal, not a performance metric. See `LIMITATIONS.md §4.1`.

### Homology-clean generalization

The earlier `data/splits/cryptosite_split.json` benchmark is superseded because homology leakage was detected across train and held-out structures. The clean split workflow is:

```
python scripts/make_homology_split.py
python scripts/train_ablation_suite.py
python scripts/evaluate_clean_split.py
```

Headline metrics are clean-split AUPRC with structure-bootstrap confidence intervals. AUROC is secondary. Degenerate structures with fewer than 5 positive residues are listed individually and excluded from aggregate claims.

| Condition | Seeds | Test AUPRC mean | 95% CI | Test AUROC mean | Degenerate test structures |
|---|---:|---:|---|---:|---:|
| small_geometry | 3 | 0.1551 | 0.0549-0.2426 | 0.7626 | 2 |
| xl_geometry | 3 | 0.1923 | 0.1161-0.2682 | 0.8325 | 2 |
| xl_esm_zero | 3 | 0.1071 | 0.0465-0.1773 | 0.6815 | 2 |
| xl_esm_full | 3 | 0.2513 | 0.1267-0.3815 | 0.8649 | 2 |

Interpretation: the best result is ESM2-augmented and exploratory. The ESM-zero ablation underperforms geometry-only XL, so ESM2/sequence context is a major contributor and must not be framed as pure structural learning.

### Structural dynamics validation

| Metric | Minimum bar | Strong result | Status |
|---|---|---|---|
| ANM apo/holo fold-change delta | > 0 | > 0.2 | **PASS** — delta = +0.300 (apo 0.857 → holo 1.157); consistent with flexibility difference hypothesis |
| Internal pocket DCCM (apo) | > 0 | > 0.3 | **Partial** — 0.0995 (mild positive coherent motion in predicted pocket region) |
| Novel pocket transient volume (MD RMSF/DCCM) | — | > 100 Å³ | **Pending** — 100 ns CHARMM36m trajectory running on collaborator NVIDIA GPU; analysis script ready (`scripts/run_md_analysis.py`) |

**ANM interpretation:** The Anisotropic Network Model (7.5 Å cutoff, 20 non-trivial modes) shows predicted pocket residues are 14% less flexible than background in apo PCNA (fold-change 0.857), rising to 16% *more* flexible than background in holo (fold-change 1.157). The +0.300 delta is consistent with a ligand-associated flexibility increase at this site. Both structures use 48 AOH residues on chains A+B only (ZQZ in 8GLA is on A+B; chain C carries no ligand). ANM correlates with full MD RMSF at r ~ 0.6–0.8 (Eyal et al. 2006) — this is hypothesis-supporting evidence, not MD confirmation.

**MD pipeline** (`scripts/run_md_analysis.py`): Computes per-residue Cα RMSF, DCCM correlation matrix, and convex-hull pocket volume from the 100 ns trajectory. Compares MD fold-change against ANM baseline (0.857) for AOH1996 pocket residues. Pre-built system files (`data/md/1W60_solvated.pdb`, `data/md/system.xml`) are committed; trajectory will be added when the collaborator run completes.

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
