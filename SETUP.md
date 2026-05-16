# GNN-PCNA — Replication Setup Guide

Step-by-step instructions to run the full pipeline from scratch on a new machine.

---

## Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| Python | 3.10 – 3.12 | 3.12 tested |
| pip | ≥ 23.0 | `pip install --upgrade pip` |
| Git | any | for cloning |
| RAM | ≥ 8 GB | 16 GB recommended for large complexes |
| GPU | optional | CPU works; GPU speeds training 5–10× |
| Disk | ≥ 2 GB | raw PDB files are ~111 MB for 59 structures |

---

## 1. Clone the repo

```bash
git clone https://github.com/Reshwant-Borra/GNN_PCNA.git
cd GNN_PCNA
```

---

## 2. Create a virtual environment

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

---

## 3. Install PyTorch

Install the build that matches your hardware **before** anything else.

### CPU only (works everywhere, slower training)
```bash
pip install torch==2.1.0 --index-url https://download.pytorch.org/whl/cpu
```

### NVIDIA GPU (CUDA 11.8)
```bash
pip install torch==2.1.0 --index-url https://download.pytorch.org/whl/cu118
```

### NVIDIA GPU (CUDA 12.1)
```bash
pip install torch==2.1.0 --index-url https://download.pytorch.org/whl/cu121
```

### Apple Silicon (MPS)
```bash
pip install torch==2.1.0
```

Verify:
```bash
python -c "import torch; print(torch.__version__, torch.cuda.is_available())"
```

---

## 4. Install PyTorch Geometric

PyG sparse ops must match your PyTorch + CUDA version exactly.

```bash
pip install torch-geometric

# torch-scatter and torch-sparse (replace cu118 with your CUDA tag, or cpu)
pip install torch-scatter torch-sparse \
  -f https://data.pyg.org/whl/torch-2.1.0+cu118.html
```

For CPU:
```bash
pip install torch-scatter torch-sparse \
  -f https://data.pyg.org/whl/torch-2.1.0+cpu.html
```

---

## 5. Install all other dependencies

```bash
pip install -r requirements.txt
```

This installs: biopython, scikit-learn, scipy, numpy, requests, beautifulsoup4, streamlit, matplotlib, pandas, tqdm.

---

## 6. Verify the install

```bash
python -c "
import torch, torch_geometric, Bio, sklearn, streamlit
print('torch:', torch.__version__)
print('pyg:', torch_geometric.__version__)
print('biopython OK')
print('sklearn OK')
print('streamlit OK')
"
```

---

## 7. Download PDB structures

The raw `.pdb` files are not tracked in git. Download them via the crawler:

```bash
python agents/pcna_crawler.py --download --sources rcsb --download-limit 100
```

This downloads up to 100 verified PCNA structures to `data/raw/`.

The 59 PCNA structures used in this study are listed in `results/per_structure/summary_table.csv`.

To download a specific structure manually:
```bash
# Example: 8GLA (AOH1996 holo)
curl -o data/raw/8GLA.pdb https://files.rcsb.org/download/8GLA.pdb
```

---

## 8. Build graph tensors

Convert raw PDB files into PyG graph tensors:

```bash
python scripts/build_graphs.py
```

Output: `data/graphs/*.pt` (one file per structure, gitignored).

---

## 9. Use the pre-trained checkpoint

The trained model is tracked in git at `checkpoints/pcna/best_pcna.ckpt`.
No training required to run inference.

Verify it loads:
```bash
python -c "
import torch
from src.models import PocketGNN
model = PocketGNN.small()
model.load_state_dict(torch.load('checkpoints/pcna/best_pcna.ckpt', map_location='cpu', weights_only=True))
print('Checkpoint loaded OK — params:', sum(p.numel() for p in model.parameters()))
"
```

Expected output: `Checkpoint loaded OK — params: 850000` (approximately).

---

## 10. Run per-structure analysis (all 59 PCNA structures)

```bash
python scripts/per_structure_analysis.py
```

Output: `results/per_structure/{PDB_ID}/` for each structure.
This takes ~5–15 minutes on CPU depending on machine.

---

## 11. Generate the analysis figure

```bash
python scripts/make_final_figure.py
```

Output: `results/per_structure/full_analysis.png` (5-panel figure).

---

## 12. Launch the Streamlit UI

```bash
streamlit run src/ui/app.py
```

Opens at `http://localhost:8501`. Upload any PDB file or select a pre-analyzed structure.

---

## 13. Regenerate protein documentation

```bash
python scripts/generate_protein_docs.py
```

Output: `docs/proteins/*.md` — one doc per structure + `docs/proteins/aoh1996_candidates.md`.

---

## Full pipeline (automated)

Runs all stages in sequence:

```bash
python scripts/run_pipeline.py --stages crawl download graphs split train eval
```

Flags:
- `--stages` — which stages to run (default: all)
- `--cutoff 8.0` — spatial graph edge cutoff in Angstroms
- `--download-limit 100` — max PDB files to download
- `--epochs 100` — training epochs

---

## Optional: MD validation

Requires MDAnalysis and a trajectory file (`.xtc` or `.dcd`):

```bash
pip install mdanalysis prody
python -m src.md.analyze --topology data/raw/8GLA.pdb --trajectory path/to/traj.xtc
```

---

## Optional: MCP server (Claude Code integration)

```bash
pip install mcp
python agents/mcp_server.py
```

Then add to your Claude Code MCP config:
```json
{
  "mcpServers": {
    "gnn-pcna": {
      "command": "python",
      "args": ["agents/mcp_server.py"]
    }
  }
}
```

---

## Troubleshooting

| Error | Fix |
|---|---|
| `ModuleNotFoundError: torch_scatter` | Re-run step 4 with correct CUDA tag |
| `UnicodeEncodeError: cp1252` | Run with `PYTHONIOENCODING=utf-8 python ...` |
| `FileNotFoundError: best_pcna.ckpt` | Run `git pull` — checkpoint is tracked in git |
| `FileNotFoundError: data/raw/8GLA.pdb` | Run step 7 (crawler download) |
| `AUROC = 0.5` on a structure | Check if drug-like HETATM exists — apo structures have no labeling signal |
| Streamlit not found | `pip install streamlit` |
| Out of memory during analysis | Reduce batch size or run structures one at a time |

---

## Key files at a glance

| File | Purpose |
|---|---|
| `checkpoints/pcna/best_pcna.ckpt` | Pre-trained model (tracked in git) |
| `results/per_structure/summary_table.csv` | All-59 results rollup (tracked in git) |
| `results/per_structure/full_analysis.png` | 5-panel figure (tracked in git) |
| `docs/proteins/aoh1996_candidates.md` | AOH1996 candidate extract |
| `data/raw/*.pdb` | Raw structures (gitignored — download via crawler) |
| `data/graphs/*.pt` | Graph tensors (gitignored — build via build_graphs.py) |
| `data/catalog/pcna_data_catalog.json` | Crawler output catalog (tracked) |

---

*GNN-PCNA v2 | Python 3.12 | PyTorch 2.1 | PyTorch Geometric 2.4*
