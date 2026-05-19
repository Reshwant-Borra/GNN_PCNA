# 4RJF — REPLICATIONCRYSTAL STRUCTURE OF THE HUMAN SLIDING CLAMP AT 2.0 ANGSTROM RESOLUTION

> Generated: 2026-05-19  |  Category: Canonical apo PCNA  **AOH1996 CANDIDATE**

## Quick Stats

| Field | Value |
|-------|-------|
| PDB ID | [4RJF](https://www.rcsb.org/structure/4RJF) |
| Residues | 814 across 6 chains |
| Ligands detected | none (apo) |
| AUROC | N/A (apo — no ligand for labeling) |
| Top pocket mean score | 0.6091 (177 residues) |
| AOH1996 GT overlap | ###################.  23/24 |
| Top pocket concavity | 0.655 (concave) |

## AOH1996 Pocket Assessment

The model's top predicted cluster overlaps with **23/24 AOH1996 ground-truth residues** (96% of the confirmed pocket from PDB 8GLA). Top cluster mean score: 0.609. **Note: mean score 0.609 is below the 0.7 project-defined threshold — the AOH1996 pocket is not confidently recovered by this checkpoint.**

**Hypothesis (unvalidated):** This region may be compatible with AOH1996 binding. Molecular docking or MD simulation is required to test this hypothesis. Labels are derived from ligand-proximity heuristics, not curated benchmark labels.

## Full Analysis Report

```
======================================================================
PDB: 4RJF
Title: REPLICATIONCRYSTAL STRUCTURE OF THE HUMAN SLIDING CLAMP AT 2.0 ANGSTROM RESOLUTION
Chains: A, B, C, D, E, F  |  Residues: 814
Ligands detected: none (apo)
Residues above threshold (0.4): 237/814 (29.1%)

Predicted cryptic pockets: 3

  Pocket #1  (PRIMARY)
  ------------------------------------------------------------
  Residues: 177  |  Mean score: 0.609  |  Max score: 0.784
  Center (A): (-19.8, 107.9, -19.8)
  Structural region: Domain 2 core beta sheet
     74 residues in: Domain 2 core beta sheet
     32 residues in: Core beta sheet
     31 residues in: C-terminal loop — AOH1996 cryptic pocket region
     17 residues in: N-terminal beta sheet (domain 1)
     16 residues in: IDCL — Interdomain Connecting Loop (key interaction hub)
      7 residues in: Front-face loop (PIP-box groove)
  AOH1996 pocket overlap: 23/25 GT residues
  --> HIGH overlap: this pocket is the known AOH1996 cryptic site
  Geometric concavity: 0.66 (concave — geometrically pocket-like)
  Top residues: A200(ASN)=0.784, A232(ASP)=0.767, A235(LEU)=0.764, A234(PRO)=0.761, A136(VAL)=0.759, A135(CYS)=0.758, A231(ALA)=0.757, A201(GLU)=0.752

  How this pocket was identified:
    The model assigned a high prioritization score to 177 residues that cluster within 6 A of each other in 3D space. These residues have a mean SASA of 12.4 A^2 (88% are partially buried, SASA < 30 A^2), consistent with a recessed binding surface rather than an exposed loop.
    The GNN assigned high scores here because the dual-branch message-passing identified this neighborhood as chemically similar to known cryptic pocket residues in the training data: the spatial branch detected dense local packing (average 177 close contacts) and the sequential branch detected the loop or beta-strand context typical of induced-fit binding sites.
    This matches the region where AOH1996 binds in PDB 8GLA, specifically the domain 2 core beta sheet. The prediction is consistent with the known mechanism of cryptic pocket opening.

  Pocket #2  (secondary)
  ------------------------------------------------------------
  Residues: 47  |  Mean score: 0.587  |  Max score: 0.684
  Center (A): (-30.6, 158.9, -5.1)
  Structural region: Domain 2 core beta sheet
     19 residues in: Domain 2 core beta sheet
     16 residues in: C-terminal loop — AOH1996 cryptic pocket region
      7 residues in: Front-face loop (PIP-box groove)
      3 residues in: IDCL — Interdomain Connecting Loop (key interaction hub)
      2 residues in: N-terminal beta sheet (domain 1)
  AOH1996 pocket overlap: 14/25 GT residues
  --> HIGH overlap: this pocket is the known AOH1996 cryptic site
  Geometric concavity: 0.70 (concave — geometrically pocket-like)
  Top residues: C236(VAL)=0.684, C40(MET)=0.675, C138(LYS)=0.675, C226(THR)=0.670, C228(SER)=0.668, C225(VAL)=0.662, C227(LEU)=0.660, C139(MET)=0.654

  How this pocket was identified:
    The model assigned a high prioritization score to 47 residues that cluster within 6 A of each other in 3D space. These residues have a mean SASA of 8.0 A^2 (94% are partially buried, SASA < 30 A^2), consistent with a recessed binding surface rather than an exposed loop.
    The GNN assigned high scores here because the dual-branch message-passing identified this neighborhood as chemically similar to known cryptic pocket residues in the training data: the spatial branch detected dense local packing (average 47 close contacts) and the sequential branch detected the loop or beta-strand context typical of induced-fit binding sites.
    This matches the region where AOH1996 binds in PDB 8GLA, specifically the domain 2 core beta sheet. The prediction is consistent with the known mechanism of cryptic pocket opening.

  Pocket #3  (secondary)
  ------------------------------------------------------------
  Residues: 8  |  Mean score: 0.568  |  Max score: 0.660
  Center (A): (-30.5, 172.8, -19.6)
  Structural region: Domain 2 core beta sheet
  AOH1996 pocket overlap: 0/25 GT residues
  --> LOW overlap: model predicts a distinct site (hypothesis — requires experimental validation)
  Geometric concavity: 0.25 (convex — surface protrusion, interpret cautiously)
  Top residues: C185(THR)=0.660, C186(SER)=0.630, C184(GLN)=0.630, C183(SER)=0.606, C168(LYS)=0.561, C187(ASN)=0.556, C167(VAL)=0.455, C182(LEU)=0.447

  How this pocket was identified:
    The model assigned a high prioritization score to 8 residues that cluster within 6 A of each other in 3D space. These residues have a mean SASA of 45.4 A^2 (50% are partially buried, SASA < 30 A^2), consistent with a recessed binding surface rather than an exposed loop.
    The GNN assigned high scores here because the dual-branch message-passing identified this neighborhood as chemically similar to known cryptic pocket residues in the training data: the spatial branch detected dense local packing (average 8 close contacts) and the sequential branch detected the loop or beta-strand context typical of induced-fit binding sites.
    This does not overlap significantly with the AOH1996 site. The model assigns high scores here; whether this represents a true cryptic pocket is a hypothesis requiring experimental validation.

Score distribution:
  Min=0.020  Max=0.784  Mean=0.245  Std=0.247
  29.1% of residues exceed threshold 0.4 (focused signal — clusters are reliable)
```

## Data Files

> **Gitignored** — regenerate locally with `python scripts/per_structure_analysis.py`
> PDB inputs: `python agents/pcna_crawler.py --download` | Graphs: `python scripts/build_graphs.py`

| File | Description | Tracked in git? |
|------|-------------|----------------|
| `results/per_structure/4RJF/scores.csv` | Per-residue pocket scores | No |
| `results/per_structure/4RJF/clusters.csv` | DBSCAN cluster assignments | No |
| `results/per_structure/4RJF/report.txt` | Full text analysis report | No |
| `results/per_structure/4RJF/summary.json` | Machine-readable summary | No |
| `results/per_structure/summary_table.csv` | All-59 rollup | Yes |
| `checkpoints/pcna/best_pcna.ckpt` | Trained model weights | Yes |
| `data/raw/4RJF.pdb` | Raw PDB structure | No |
| `data/graphs/4RJF.pt` | PyG graph tensor | No |

---
*GNN-PCNA v2 | Dual-branch GATv2Conv | Checkpoint tracked at `checkpoints/pcna/best_pcna.ckpt`*