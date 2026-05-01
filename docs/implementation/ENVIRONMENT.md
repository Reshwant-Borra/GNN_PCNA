# ENVIRONMENT.md — Environment Setup

→ Links: [[COMMANDS]] | [[ARCHITECTURE]]

---

## Python Version

- **Required:** Python 3.10+
- **Recommended:** Python 3.11 (better performance for PyTorch)

---

## Core Dependencies

| Package | Version | Purpose |
|---|---|---|
| `torch` | ≥ 2.0 | Deep learning framework |
| `torch_geometric` | ≥ 2.3 | Graph neural networks (PyG) |
| `torch_scatter` | Matching PyG version | PyG dependency |
| `torch_sparse` | Matching PyG version | PyG dependency |
| `mdanalysis` | ≥ 2.6 | MD trajectory analysis |
| `biopython` | ≥ 1.81 | PDB parsing, SASA calculation |
| `numpy` | ≥ 1.24 | Array operations |
| `scipy` | ≥ 1.10 | KD-tree for graph edges, stats |
| `scikit-learn` | ≥ 1.3 | DBSCAN clustering |
| `py3dmol` | ≥ 2.0 | 3D molecular visualization (Jupyter) |
| `matplotlib` | ≥ 3.7 | Plotting |
| `seaborn` | ≥ 0.12 | Statistical plots |

---

## Optional Dependencies

| Package | Purpose |
|---|---|
| `prody` | Alternative to BioPython; normal mode analysis |
| `fpocket` / `mdpocket` | Geometric pocket detection + volume tracking |
| `plumed` | Enhanced sampling (metadynamics) |
| `openmm` | MD simulation engine (alternative to GROMACS) |
| `gromacs` | MD simulation engine (command-line) |

---

## Installation (Needs verification)

```bash
# Create environment
conda create -n gnn_pcna python=3.11
conda activate gnn_pcna

# PyTorch (CUDA 12.x — adjust for your GPU)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# PyTorch Geometric
pip install torch_geometric
pip install torch_scatter torch_sparse -f https://data.pyg.org/whl/torch-2.1.0+cu121.html

# Bio + MD packages
pip install mdanalysis biopython numpy scipy scikit-learn

# Visualization
pip install py3dmol matplotlib seaborn

# Optional
pip install prody
```

---

## CUDA / GPU Notes

- CrypticGNN with PCNA trimer graph (~800 nodes, 8 Å cutoff): fits on 8 GB GPU
- Batch size may need to be 1–4 on 16 GB GPU if using multiple large graphs
- CPU training is possible but slow for 100+ epochs

---

## Key Environment Variables (if needed)

```bash
# Needs verification — set as appropriate
export PYTHONPATH="${PYTHONPATH}:/path/to/GNN_PNCA"
```

---

## File Encoding

All source files: UTF-8. No Windows CRLF line endings in Python files.
