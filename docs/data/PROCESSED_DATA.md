# PROCESSED_DATA.md — Processing Pipeline State

→ Links: [[DATA_INVENTORY]] | [[PIPELINE]] | [[DATA_SCHEMA]]

---

## Processing Status

| Input | Step | Output | Status | Script |
|---|---|---|---|---|
| `data/raw/1W60.pdb` | Strip HETATM, standardize chains | `data/processed/1W60_clean.pdb` | Not done | `parse_pdb.strip_heteroatoms` |
| `data/raw/8GLA.pdb` | Strip waters, keep AOH1996 | `data/processed/8GLA_clean.pdb` | Not done | `parse_pdb.strip_heteroatoms(keep_resname='AOH')` |
| `data/processed/1W60_clean.pdb` | Build residue graph | `data/graphs/1W60.pt` | Not done | `graph_construction.build_graph` |
| `data/processed/8GLA_clean.pdb` | Build residue graph | `data/graphs/8GLA.pt` | Not done | `graph_construction.build_graph` |
| `data/processed/8GLA_clean.pdb` + AOH1996 coords | Label pocket residues | `data/labels/8GLA_labels.npy` | Not done | `parse_pdb.label_pocket_residues` |

---

## Processing Notes

### HETATM removal
- Strip all HETATM except AOH1996 when processing 8GLA
- AOH1996 residue name in PDB: `Needs verification` (check `grep HETATM data/raw/8GLA.pdb`)
- After stripping: verify residue count matches expected ~261 × 3 = 783 (trimer)

### Chain standardization
- PCNA trimer chains should be labeled A, B, C
- Check that all 3 chains are present: `grep "^ATOM" 1W60_clean.pdb | awk '{print $5}' | sort -u`

### Graph construction
- Distance cutoff: 8 Å (Cα–Cα)
- Include edges between different chains (inter-chain contacts)
- Expected: ~800 nodes (trimer), ~267 nodes (monomer)

### Label generation
- Positive label: residue Cα within 6 Å of any heavy atom of AOH1996
- Label is per-residue, per-chain
- Expected positive fraction: ~5–15% of residues

---

## Verification Checks

After each processing step:

```python
# After graph construction
import torch
data = torch.load('data/graphs/1W60.pt')
assert data.x.shape[1] == 26, "Wrong node feature dim"
assert data.edge_attr.shape[1] == 2, "Wrong edge feature dim"
assert data.x.shape[0] > 200, "Too few nodes"
print(f"Nodes: {data.num_nodes}, Edges: {data.edge_index.shape[1]}")

# After labeling
import numpy as np
labels = np.load('data/labels/8GLA_labels.npy')
print(f"Positive fraction: {labels.mean():.3f}")  # expect 0.05–0.15
```
