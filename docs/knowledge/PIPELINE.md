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

## Stage 6 — MD Validation
- Run short MD (50–100 ns) on apo PCNA
- For each predicted pocket cluster:
  - Compute **RMSF** of pocket residues (high = flexible = cryptic)
  - Compute **DCCM** (dynamic cross-correlation) — pocket residues should move coherently
  - Track pocket **volume over time** (fpocket or MDAnalysis-based)
- A pocket is validated if: RMSF > background + volume opens transiently

## Stage 7 — Output
- Ranked list of cryptic pocket candidates
- Per-pocket: residue list, mean score, RMSF, DCCM signature, representative open snapshot
- Export: JSON + PDB with B-factors replaced by pocket scores
