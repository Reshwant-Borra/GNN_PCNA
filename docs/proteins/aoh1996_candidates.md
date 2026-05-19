# AOH1996 Candidate Structures — Cryptic Pocket Extract

> Generated: 2026-05-16
> Criteria: AOH1996 GT overlap >= 18/24 residues AND top cluster mean >= 0.55 AND no co-factor contamination

## What This Means

AOH1996 (molecular weight ~900 Da) targets a cryptic pocket at the PCNA A-B subunit interface, engaging residues in the C-terminal loop (231-253) and IDCL (119-134). Structures listed here have GNN-predicted pockets that spatially overlap >75% with the experimentally confirmed binding site from PDB 8GLA.

These represent PCNA conformations in which the cryptic pocket is **at least partially pre-opened** — the most accessible states for AOH1996 binding.

## Tier 1 — Highest Confidence (overlap >= 22, score >= 0.60)

| PDB | Description | AOH GT overlap | Top score | AUROC | Concavity | Category |
|-----|-------------|---------------|-----------|-------|-----------|----------|
| **3VKX** | DNA BINDING | 24/24 | 0.674 | 0.9042 | 0.477 | Other PCNA structure |
| **1UL1** | HYDROLASE/DNA BINDING | 24/24 | 0.604 | 0.0000 | 0.522 | Other PCNA structure |
| **9CHM** |  | 23/24 | 0.652 | 0.0000 | 0.456 | Other PCNA structure |
| **4RJF** | REPLICATIONCRYSTAL STRUCTURE OF THE HUMAN SLIDING CLAMP | 23/24 | 0.609 | 0.0000 | 0.655 | Canonical apo PCNA |
| **9N3L** | DNA BINDING | 22/24 | 0.670 | 0.8602 | 0.472 | Other PCNA structure |
| **1W60** | DNA BINDING | 22/24 | 0.665 | 0.0000 | 0.442 | Canonical apo PCNA |
| **8GL9** | DNA BINDING | 22/24 | 0.611 | 0.8129 | 0.567 | AOH1996 holo (confirmed binder) |
| **7KQ0** | REPLICATIONPCNA BOUND TO PEPTIDE MIMETIC | 22/24 | 0.609 | 0.0000 | 0.612 | Other PCNA structure |

## Tier 2 — Moderate Confidence (overlap >= 18, score >= 0.55)

| PDB | Description | AOH GT overlap | Top score | AUROC | Category |
|-----|-------------|---------------|-----------|-------|----------|
| 6CBI | CELL CYCLEPCNA IN COMPLEX WITH INHIBITOR | 24/24 | 0.597 | 0.5219 | Other PCNA structure |
| 5YCO | DNA BINDING | 24/24 | 0.592 | N/A | Other PCNA structure |
| 8GCJ | REPLICATIONPCNA | 24/24 | 0.589 | N/A | AOH1996 holo (confirmed binder) |
| 1VYJ | DNA BINDING | 24/24 | 0.578 | N/A | Other PCNA structure |
| 2ZVL | TRANSFERASECRYSTAL STRUCTURE OF PCNA IN COMPLEX WITH DN | 23/24 | 0.587 | N/A | Other PCNA structure |
| 1AXC | COMPLEX (DNA-BINDING | 22/24 | 0.592 | N/A | Other PCNA structure |
| 5MLO | HYDROLASECRYSTAL STRUCTURE OF HUMAN PCNA IN COMPLEX WIT | 22/24 | 0.579 | N/A | Other PCNA structure |
| 3P87 | HYDROLASE/DNA BINDING | 22/24 | 0.577 | N/A | Other PCNA structure |
| 5MOM | DNA BINDING | 22/24 | 0.572 | N/A | Other PCNA structure |
| 1U76 | REPLICATIONCRYSTAL STRUCTURE OF HPCNA BOUND TO RESIDUES | 22/24 | 0.569 | N/A | Other PCNA structure |
| 6FCN | NUCLEAR | 21/24 | 0.688 | N/A | Other PCNA structure |
| 6K3A | REPLICATIONCRYSTAL STRUCTURE OF HUMAN PCNA IN COMPLEX W | 21/24 | 0.592 | N/A | Other PCNA structure |
| 7NV0 | REPLICATIONHUMAN POL KAPPA HOLOENZYME WITH WT PCNA | 21/24 | 0.590 | 0.6388 | Other PCNA structure |
| 8GLA | DNA BINDING | 21/24 | 0.587 | 0.8661 | AOH1996 holo (confirmed binder) |
| 5E0T | DNA BINDING | 21/24 | 0.571 | N/A | Other PCNA structure |
| 5YD8 | DNA BINDING | 20/24 | 0.587 | N/A | Other PCNA structure |
| 8COB | DNA BINDING | 20/24 | 0.584 | N/A | Other PCNA structure |
| 5MLW | HYDROLASECRYSTAL STRUCTURE OF HUMAN PCNA IN COMPLEX WIT | 20/24 | 0.576 | N/A | Other PCNA structure |
| 6FCM | NUCLEAR | 20/24 | 0.565 | N/A | Other PCNA structure |
| 8F5Q | DNA BINDING | 19/24 | 0.604 | N/A | Other PCNA structure |
| 5MAV | TRANSCRIPTIONCRYSTAL STRUCTURE OF HUMAN PCNA IN COMPLEX | 19/24 | 0.589 | N/A | Other PCNA structure |
| 6QC0 | REPLICATIONPCNA COMPLEX WITH CDT2 C-TERMINAL PIP-BOX PE | 19/24 | 0.589 | N/A | Other PCNA structure |
| 6QCG | CELL CYCLEPCNA COMPLEX WITH CDT1 N-TERMINAL PIP-BOX PEP | 19/24 | 0.583 | N/A | Other PCNA structure |
| 6GIS | DNA BINDING | 19/24 | 0.583 | N/A | Other PCNA structure |
| 5E0V | DNA BINDING | 19/24 | 0.563 | N/A | Other PCNA structure |

## Structural Basis for Candidacy

### Why these structures are targetable

1. **PCNA forms a homotrimeric ring** — each monomer presents an identical AOH1996 pocket.
   Structures with 3 or 6 chains (trimers / dimers-of-trimers) get 3x or 6x binding opportunities.

2. **The cryptic pocket opens via induced fit** — AOH1996 itself induces the open conformation.
   High GNN scores on apo structures (e.g. 1W60, 4RJF) indicate the pocket is near-open even without ligand.

3. **Concavity >= 0.45** = geometrically pocket-like (inward-pointing surface). These predictions
   are not artifacts of convex surface protrusions.

### Key residues to target (from 8GLA co-crystal)

| Region | Residues | Role |
|--------|----------|------|
| C-terminal loop | 231-234, 250-253 | Primary AOH1996 contacts |
| IDCL | 123, 125-126, 128 | Induced-fit hinge |
| Front-face loop | 38-47 | PIP-box groove overlap |
| Domain 1 surface | 25-27 | Electrostatic anchoring |

### Structures confirmed NOT to be AOH1996 targets

- **9B8T**: Top pocket at Pol epsilon-PCNA interface — novel site, different drug needed
- **8UN0, 8UMY, 8UMU, 8UMT, 6VVO, 8UI8, 8UI9**: CTF18-RFC/ATAD5-RFC replication complexes;
  AGS/ADP cofactor contamination makes AUROC unreliable for pocket labeling
- **7M5L**: Low AOH overlap (6/24), ligand TME/NH2 is not at AOH site

## Recommended Priority for Docking

```
Priority 1 (highest-scoring candidates — follow-up with MD/docking required):  3VKX, 9N3L, 1W60, 4RJF
Priority 2 (apo, good):      1AXC, 9CHM, 6FCN, 7KQ0
Priority 3 (complex, check): 1VYJ, 3P87, 6QCG, 5MAV
Confirmed holo (reference):  8GLA, 8GL9, 8GCJ
```

---
*GNN-PCNA v2  |  Dual-branch GATv2Conv  |  PCNA-chain filtered AUROC  |  2026-05-16*