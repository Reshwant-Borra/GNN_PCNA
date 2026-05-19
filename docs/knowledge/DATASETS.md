# Datasets

## Primary Structures

| PDB ID | Description | Use |
|---|---|---|
| 1W60 | PCNA apo (human, 2.35 Å) | Baseline graph; no AOH1996 pocket visible |
| 8GLA | PCNA + AOH1996 (cryptic pocket open) | Ground truth pocket labeling |
| 1AXC | PCNA + p21 PIP-box peptide | Alternative holo form |
| ~~1W61~~ | ~~PCNA + RFC clamp loader fragment~~ | **EXCLUDED** — proline racemase (*T. cruzi*), not PCNA |

## Training Data (Transfer Learning / External)

- **CryptoSite** dataset: ~93 protein pairs (apo/holo with cryptic pockets), used in PocketMiner
  - Available: supplementary of Cimermancic et al. 2016
- **sc-PDB**: binding site database, can be used for pre-training pocket scoring
- **PDB-wide PCNA homologs**: search for UniProt P12004 across species for structural diversity

## MD Trajectories

- Self-generated: GROMACS or OpenMM simulation of 1W60
- Recommended: CHARMM36m force field, TIP3P water, 150 mM NaCl
- Trajectory format: `.xtc` (compressed), topology `.gro` or `.psf`
- Store in: `data/trajectories/`

## Data Directory Structure

```
data/
├── raw/           # Downloaded PDB files
├── processed/     # Cleaned PDB (waters stripped, chains standardized)
├── graphs/        # PyG Data objects (.pt files)
├── labels/        # Residue-level pocket labels (.npy or .json)
└── trajectories/  # MD trajectory files
```

## Notes
- PCNA is a symmetric homotrimer: chains A/B/C are nearly identical
- Data augmentation: use all 3 chains as independent training examples
- Watch for crystal contacts in 1W60 — may mask surface residues

---

## Related

[[PIPELINE]] · [[BIOLOGY_PCNA]] · [[DATA_INVENTORY]] · [[PDB_STRUCTURES]] · [[DATA_PROVENANCE]] · [[MODELS]] · [[KNOWN_LIMITATIONS]]
