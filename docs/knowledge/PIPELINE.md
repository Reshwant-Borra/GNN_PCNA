# Pipeline

## Stage 1 — Data Ingestion
- **Input**: PDB files (PCNA structures + cryptic pocket training set)
- **Steps**:
  - Download PDB: `1W60` (apo), `8GLA` (holo/AOH1996-bound)
  - Optional: ensemble from MD snapshots
  - Strip waters, ligands (except AOH1996 for labeling)
  - Standardize chain IDs (PCNA has chains A, B, C)
- **Output**: Cleaned `.pdb` files in `data/raw/`

## Stage 2 — Graph Construction
- **Node features** (per residue):
  - Amino acid one-hot (20 dims)
  - B-factor (crystallographic flexibility)
  - Secondary structure (helix/sheet/coil, 3 dims)
  - Solvent accessible surface area (SASA)
  - Relative position in sequence (normalized)
- **Edge construction**:
  - Distance cutoff: 8–10 Å (Cα–Cα)
  - Optional: contact map from MD ensemble
- **Edge features**:
  - Euclidean distance (Cα–Cα)
  - Sequence separation (|i − j|)
  - Bond type (peptide / spatial)
- **Output**: PyG `Data` objects in `data/graphs/`

## Stage 3 — Labeling
- For supervised training: residues within 6 Å of AOH1996 in 8GLA = positive class
- For novel prediction: all residues are unlabeled (inference mode)
- Label imbalance: ~5–15% positive residues → use focal loss or weighted BCE

## Stage 4 — GNN Model
- Architecture: see `docs/knowledge/MODELS.md`
- Input: node features + edge features + graph topology
- Output: per-residue scalar (cryptic pocket probability ∈ [0, 1])

## Stage 5 — Pocket Clustering
- Threshold per-residue scores (e.g., > 0.5)
- Cluster adjacent high-scoring residues into pocket candidates
- Rank by: mean score, cluster size, geometric volume estimate

## Stage 6 — Flexibility Validation (ANM — COMPLETED)

> **Method: Anisotropic Network Model (ANM)** on apo PCNA (1W60).
> Full MD trajectory (GROMACS/OpenMM) is not yet run. ANM is a validated fast alternative
> that correlates with MD-RMSF at r~0.6–0.8 (Eyal et al. 2006, Proteins 63:1072).
> Results: `data/results/nma_1W60.json`, `data/results/nma_1W60_dccm.npy`
> Script: `scripts/run_nma.py`

**ANM Results (1W60, cutoff=7.5 Å, 20 non-trivial modes):**

| Metric | Value | Interpretation |
|--------|-------|----------------|
| AOH1996 pocket RMSF (norm) | 0.8685 | 14% less flexible than background |
| Background RMSF (norm) | 1.0137 | Reference |
| Fold-change (pocket/bg) | 0.857 | Pocket is rigidly packed in apo state |
| Internal pocket DCCM | 0.0995 | Mild positive — residues move coherently |

**Scientific interpretation:** A fold-change < 1 is the expected signature of a buried cryptic
pocket. The site is rigidly packed and inaccessible in the apo state; ligand binding (AOH1996
in 8GLA) induces the conformational opening. This distinguishes it from an allosteric pocket,
which would show elevated apo RMSF (fold-change > 1).

**Full MD validation (future):**
- Generate 50–100 ns GROMACS/OpenMM trajectory of 1W60
- Run `src/md/parse_trajectory.py` for per-frame RMSF, DCCM, volume
- Positive result: transient volume opening > 100 Å³ at the AOH1996 site

## Stage 7 — Output
- Ranked list of cryptic pocket candidates
- Per-pocket: residue list, mean GNN score, ANM-RMSF, ANM-DCCM
- Export: JSON + PDB with B-factors replaced by pocket scores

---

## Related

[[MODELS]] · [[DATASETS]] · [[VALIDATION]] · [[DATA_SCHEMA]] · [[FILE_GUIDE]] · [[EXPERIMENT_INDEX]] · [[SYSTEM_OVERVIEW]]
