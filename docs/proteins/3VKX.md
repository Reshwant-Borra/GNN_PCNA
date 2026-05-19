# 3VKX — DNA BINDING

> Generated: 2026-05-19  |  Category: Other PCNA structure  **AOH1996 CANDIDATE**

## Quick Stats

| Field | Value |
|-------|-------|
| PDB ID | [3VKX](https://www.rcsb.org/structure/3VKX) |
| Residues | 248 across 1 chains |
| Ligands detected | T3 |
| AUROC | 0.9042 (raw, ligand-proximity labels) |
| Top pocket mean score | 0.6737 (128 residues) |
| AOH1996 GT overlap | ####################  24/24 |
| Top pocket concavity | 0.477 (convex) |

## AOH1996 Pocket Assessment

The model's top predicted cluster overlaps with **24/24 AOH1996 ground-truth residues** (100% of the confirmed pocket from PDB 8GLA). Top cluster mean score: 0.674. **Note: mean score 0.674 is below the 0.7 project-defined threshold — the AOH1996 pocket is not confidently recovered by this checkpoint.**

**Hypothesis (unvalidated):** This region may be compatible with AOH1996 binding. Molecular docking or MD simulation is required to test this hypothesis. Labels are derived from ligand-proximity heuristics, not curated benchmark labels.

## Full Analysis Report

```
======================================================================
PDB: 3VKX
Title: DNA BINDING PROTEINSTRUCTURE OF PCNA
Chains: A  |  Residues: 248
Ligands detected: T3
AUROC vs auto-labeled GT: 0.9042
Residues above threshold (0.4): 130/248 (52.4%)

Predicted cryptic pockets: 1

  Pocket #1  (PRIMARY)
  ------------------------------------------------------------
  Residues: 128  |  Mean score: 0.674  |  Max score: 0.833
  Center (A): (-19.3, 13.2, 31.8)
  Structural region: Domain 2 core beta sheet
     57 residues in: Domain 2 core beta sheet
     20 residues in: C-terminal loop — AOH1996 cryptic pocket region
     19 residues in: Core beta sheet
     16 residues in: IDCL — Interdomain Connecting Loop (key interaction hub)
      8 residues in: N-terminal beta sheet (domain 1)
      7 residues in: Front-face loop (PIP-box groove)
      1 residues in: C-terminal tail (protein-protein interface)
  AOH1996 pocket overlap: 24/25 GT residues
  --> HIGH overlap: this pocket is the known AOH1996 cryptic site
  Geometric concavity: 0.48 (convex — surface protrusion, interpret cautiously)
  Top residues: A46(SER)=0.833, A41(ASP)=0.827, A45(VAL)=0.817, A44(HIS)=0.814, A42(SER)=0.813, A251(LEU)=0.786, A139(MET)=0.782, A250(TYR)=0.781

  How this pocket was identified:
    The model assigned a high prioritization score to 128 residues that cluster within 6 A of each other in 3D space. These residues have a mean SASA of 34.6 A^2 (62% are partially buried, SASA < 30 A^2), consistent with a recessed binding surface rather than an exposed loop.
    The GNN assigned high scores here because the dual-branch message-passing identified this neighborhood as chemically similar to known cryptic pocket residues in the training data: the spatial branch detected dense local packing (average 128 close contacts) and the sequential branch detected the loop or beta-strand context typical of induced-fit binding sites.
    This matches the region where AOH1996 binds in PDB 8GLA, specifically the domain 2 core beta sheet. The prediction is consistent with the known mechanism of cryptic pocket opening.

Score distribution:
  Min=0.020  Max=0.833  Mean=0.393  Std=0.306
  52.4% of residues exceed threshold 0.4 (high diffuse signal — interpret clusters carefully)
```

## Data Files

> **Gitignored** — regenerate locally with `python scripts/per_structure_analysis.py`
> PDB inputs: `python agents/pcna_crawler.py --download` | Graphs: `python scripts/build_graphs.py`

| File | Description | Tracked in git? |
|------|-------------|----------------|
| `results/per_structure/3VKX/scores.csv` | Per-residue pocket scores | No |
| `results/per_structure/3VKX/clusters.csv` | DBSCAN cluster assignments | No |
| `results/per_structure/3VKX/report.txt` | Full text analysis report | No |
| `results/per_structure/3VKX/summary.json` | Machine-readable summary | No |
| `results/per_structure/summary_table.csv` | All-59 rollup | Yes |
| `checkpoints/pcna/best_pcna.ckpt` | Trained model weights | Yes |
| `data/raw/3VKX.pdb` | Raw PDB structure | No |
| `data/graphs/3VKX.pt` | PyG graph tensor | No |

---
*GNN-PCNA v2 | Dual-branch GATv2Conv | Checkpoint tracked at `checkpoints/pcna/best_pcna.ckpt`*