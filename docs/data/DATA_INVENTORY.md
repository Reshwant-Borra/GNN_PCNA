# DATA_INVENTORY.md — What Data Exists and Where

→ Links: [[DATASETS]] | [[PIPELINE]] | [[DATA_SCHEMA]] | [[DATA_PROVENANCE]]

> Update this whenever new data is acquired or processed.

---

## Raw Data (`data/raw/`)

| File | Type | Status | Source | Notes |
|---|---|---|---|---|
| `1W60.pdb` | PDB structure | Not downloaded | RCSB PDB | PCNA apo, 2.35 Å |
| `8GLA.pdb` | PDB structure | Not downloaded | RCSB PDB | PCNA + AOH1996 |
| `1AXC.pdb` | PDB structure | Not downloaded | RCSB PDB | PCNA + p21 PIP-box |
| `1W61.pdb` | PDB structure | Not downloaded | RCSB PDB | PCNA + RFC fragment |

---

## Processed Data (`data/processed/`)

| File | Type | Status | Created by | Notes |
|---|---|---|---|---|
| `1W60_clean.pdb` | Cleaned PDB | Not generated | `parse_pdb.py` | Waters stripped, chains standardized |
| `8GLA_clean.pdb` | Cleaned PDB | Not generated | `parse_pdb.py` | Keep AOH1996 for labeling |

---

## Graph Data (`data/graphs/`)

| File | Type | Status | Created by | Notes |
|---|---|---|---|---|
| `1W60.pt` | PyG Data | Not generated | `graph_construction.py` | Apo PCNA graph |
| `8GLA.pt` | PyG Data | Not generated | `graph_construction.py` | Holo PCNA graph |

---

## Label Data (`data/labels/`)

| File | Type | Status | Created by | Notes |
|---|---|---|---|---|
| `8GLA_labels.npy` | numpy array, shape (N,) | Not generated | `parse_pdb.label_pocket_residues()` | 1 = within 6 Å of AOH1996 |

---

## Trajectory Data (`data/trajectories/`)

| File | Type | Status | Notes |
|---|---|---|---|
| `1W60_apo_100ns.xtc` | MD trajectory | Not generated | 100 ns explicit solvent |
| `1W60_apo.gro` | Topology | Not generated | CHARMM36m |

---

## External Datasets

| Dataset | Use | Availability | Status |
|---|---|---|---|
| CryptoSite (~93 pairs) | Pre-training | Supplement of Cimermancic 2016 | Not acquired |
| sc-PDB | Pre-training | `http://bioinfo-pharma.u-strasbg.fr/scPDB/` | Not acquired |
| PCNA homologs | Structural diversity | PDB search for UniProt P12004 | Not acquired |

---

## Git Ignore Rules

The following should NOT be committed to git (add to `.gitignore`):

```
data/raw/*.pdb
data/processed/
data/graphs/
data/labels/
data/trajectories/
```

Use git-lfs if you need to version large files.
Document what was acquired and how in `DATA_PROVENANCE.md`.
