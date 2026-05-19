# PDB_STRUCTURES.md — PDB Files in Use

→ Links: [[DATASETS]] | [[DATA_INVENTORY]] | [[BIOLOGY_PCNA]] | [[PIPELINE]]

---

## Primary PCNA Structures

### 1W60 — PCNA Apo

| Property | Value |
|---|---|
| PDB ID | 1W60 |
| Organism | Homo sapiens |
| Resolution | 2.35 Å |
| Chains | A, B, C (homotrimer) |
| Ligand | None |
| Use | Apo baseline; graph construction; MD simulation start |
| Known issue | Crystal contacts may mask surface residues |
| Download | `wget https://files.rcsb.org/download/1W60.pdb -O data/raw/1W60.pdb` |

### 8GLA — PCNA + AOH1996

| Property | Value |
|---|---|
| PDB ID | 8GLA |
| Organism | Homo sapiens |
| Resolution | Needs NotebookLM extraction |
| Chains | A, B, C (homotrimer) |
| Ligand | AOH1996 (one or more per trimer) |
| Use | Ground truth pocket labeling; positive control |
| Binding site | IDCL region |
| Download | `wget https://files.rcsb.org/download/8GLA.pdb -O data/raw/8GLA.pdb` |

### 1AXC — PCNA + p21 PIP-box peptide

| Property | Value |
|---|---|
| PDB ID | 1AXC |
| Chains | A, B, C + peptide |
| Ligand | p21 PIP-box peptide |
| Use | Alternative holo form; PIP-box interface context |
| Priority | Low — supplementary reference |

### ~~1W61~~ — EXCLUDED (not PCNA)

| Property | Value |
|---|---|
| PDB ID | 1W61 |
| Actual protein | Proline racemase (*Trypanosoma cruzi*) |
| Status | **Rejected contamination** — mistakenly included in early versions |
| Action | Do not use; `data/raw/1W61.pdb` present but excluded from all analysis |

---

## Download Commands

```bash
# Create raw data directory
mkdir -p data/raw

# Download primary structures
wget https://files.rcsb.org/download/1W60.pdb -O data/raw/1W60.pdb
wget https://files.rcsb.org/download/8GLA.pdb -O data/raw/8GLA.pdb

# Optional
wget https://files.rcsb.org/download/1AXC.pdb -O data/raw/1AXC.pdb
# 1W61 is NOT PCNA — do not download or use
```

---

## AlphaFold Structure

| Property | Value |
|---|---|
| UniProt | P12004 (human PCNA) |
| Source | AlphaFold Database |
| Use | Alternative to 1W60 for predictions; no crystal contacts |
| Note | May have different IDCL conformation — verify before use |
| Download | `https://alphafold.ebi.ac.uk/files/AF-P12004-F1-model_v4.pdb` |

---

## PDB Metadata Notes

- PCNA residue numbering: 1–261 per chain (needs verification per structure)
- IDCL region: approximately residues 119–164 (Needs NotebookLM extraction for exact range)
- AOH1996 residue name in 8GLA: Needs NotebookLM extraction
- Crystal space group for 1W60: Needs verification

---

## Preprocessing Checklist (per structure)

- [ ] Download to `data/raw/`
- [ ] Strip waters: `parse_pdb.strip_heteroatoms()`
- [ ] Standardize chain IDs: `parse_pdb.standardize_chains()`
- [ ] Save cleaned to `data/processed/`
- [ ] Build graph: `graph_construction.build_graph()`
- [ ] Save graph to `data/graphs/`
- [ ] For 8GLA: generate labels → `data/labels/8GLA_labels.npy`
- [ ] Update `DATA_INVENTORY.md`
