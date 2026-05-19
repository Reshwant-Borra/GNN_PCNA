# data/graphs/ — PyG Graph Tensors

All graph `.pt` files are **committed directly to this repo** and can be cloned without rebuilding.

## What goes here

PyTorch Geometric `Data` objects saved as `{PDB_ID}.pt`, one per PCNA structure.

Each `.pt` file contains:
- `x`: node features, shape `[N_residues, 40]` — hand-crafted geometric + chemical features
- `edge_index`: spatial edges (Cα–Cα distance < 8 Å)
- `edge_attr`: edge features, shape `[E, 6]`
- `seq_edge_index`: sequential backbone edges (i → i+1 within each chain)
- `y`: binary pocket labels (1 = within 6 Å of ligand heavy atom)
- `pos`: Cα coordinates, shape `[N_residues, 3]`
- `resid`: residue sequence numbers
- `chain_id`: chain identity integers

## How to reproduce

```bash
# Build all graph tensors from downloaded PDB files
python scripts/download_data.py

# Or if PDB files already exist in data/raw/
python scripts/download_data.py --skip-graphs  # skips download
# then just run:
python scripts/download_data.py               # builds graphs from existing PDBs
```

Alternatively, build graphs directly:
```python
from src.data_processing.parse_pdb import parse_pdb
from src.data_processing.graph_construction import build_graph_v2
import torch

residues = parse_pdb("data/raw/8GLA.pdb")
data = build_graph_v2(residues)
torch.save(data, "data/graphs/8GLA.pt")
```

## Graph construction details

- **Spatial edges**: Cα–Cα distance < 8 Å
- **Sequential edges**: backbone i → i+1 (same chain only)
- **Labels**: residues within 6 Å of any ligand heavy atom → y=1 (ligand-proximity labels, NOT curated CryptoSite annotations)
- **Node features**: 40-dim hand-crafted (see `src/data_processing/graph_construction.py`)

## ESM2 features (optional, V3 only)

For PocketGNNXL (V3), an additional 480-dim ESM2 embedding is concatenated at runtime, making `node_in_dim=520`. ESM2 features are not stored in the `.pt` files — they are computed on-the-fly during inference.

To pre-compute and cache ESM2 features:
```bash
python scripts/download_data.py --esm
```
