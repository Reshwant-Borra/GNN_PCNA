# DATA_SCHEMA.md — Format Specifications

→ Links: [[DATASETS]] | [[PIPELINE]] | [[DATA_INVENTORY]]

---

## PDB Files (`data/raw/`, `data/processed/`)

Standard PDB format (ATOM records only after cleaning).

**Conventions:**
- Chain IDs: A, B, C for PCNA homotrimer chains
- Residue numbering: as in original PDB (do not renumber)
- Waters removed (HOH records stripped)
- HETATM records: stripped except AOH1996 (for 8GLA labeling)
- Alternate conformations: use first (A) conformation only

---

## Residue Object (`src/data_processing/parse_pdb.py`)

```python
@dataclass
class Residue:
    chain: str           # 'A', 'B', or 'C'
    resid: int           # residue number from PDB
    resname: str         # 3-letter amino acid code (e.g., 'ALA')
    ca_coord: np.ndarray # shape (3,) — Cα coordinates in Angstrom
    b_factor: float      # crystallographic B-factor
    secondary_structure: str  # 'H' (helix), 'E' (sheet), 'C' (coil)
    sasa: float          # solvent accessible surface area in Å²
```

---

## Node Feature Vector (per residue, shape `(26,)`)

| Dimension | Feature | Encoding |
|---|---|---|
| 0–19 | Amino acid type | One-hot (20 standard AA) |
| 20 | SASA | Normalized float (÷ max SASA of residue type) |
| 21–23 | Secondary structure | One-hot: [helix, sheet, coil] |
| 24 | B-factor | Normalized float (÷ mean B-factor of chain) |
| 25 | Sequence position | float in [0, 1] (position ÷ chain length) |

---

## Edge Feature Vector (per edge, shape `(2,)`)

| Dimension | Feature | Notes |
|---|---|---|
| 0 | Cα–Cα distance (Å) | Normalized by cutoff (÷ 8.0) |
| 1 | Sequence separation \|i−j\| | Normalized by chain length |

---

## PyG Data Object (`data/graphs/*.pt`)

```python
from torch_geometric.data import Data

data = Data(
    x=torch.tensor(...),          # shape (N, 26) — node features
    edge_index=torch.tensor(...), # shape (2, E) — long tensor
    edge_attr=torch.tensor(...),  # shape (E, 2) — edge features
    y=torch.tensor(...),          # shape (N,) — pocket labels (0/1), training only
    num_nodes=N,
    pdb_id='1W60',
    chain='A',                    # or 'all' for full trimer
)
```

---

## Label Array (`data/labels/*.npy`)

```
Shape: (N,)
Dtype: float32
Values: 0.0 (background) or 1.0 (pocket residue)
Definition: residue Cα within 6 Å of any heavy atom of AOH1996 in 8GLA
```

---

## MD Trajectory (`data/trajectories/`)

| File | Format | Tool | Notes |
|---|---|---|---|
| `*.xtc` | GROMACS compressed trajectory | MDAnalysis, GROMACS | Frame data |
| `*.gro` | GROMACS topology | MDAnalysis, GROMACS | Atom types, bonds |
| `*.psf` | NAMD/CHARMM topology | MDAnalysis | Alternative topology |
| `*.dcd` | NAMD/CHARMM trajectory | MDAnalysis | Alternative format |

MDAnalysis reads both GROMACS and NAMD formats.

---

## RMSF Output

```
Shape: (N,) per chain (N = residues in chain)
Units: Angstrom
Tool: MDAnalysis.analysis.rms.RMSF
```

---

## DCCM Output

```
Shape: (N, N) symmetric matrix
Values: [-1, 1]
Computed: from displacement covariance over trajectory frames
```

---

## Pocket Score Output (`results/pockets/`)

```python
# JSON format
{
    "pockets": [
        {
            "id": 1,
            "residues": [{"chain": "A", "resid": 119, "resname": "GLU"}, ...],
            "mean_score": 0.82,
            "cluster_size": 12,
            "rank": 1
        },
        ...
    ],
    "pdb_id": "8GLA",
    "model_checkpoint": "checkpoints/best_model.pt"
}
```
