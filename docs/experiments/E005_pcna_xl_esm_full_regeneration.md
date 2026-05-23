# E005 - PCNA xl_esm_full Regeneration and Final Framing

**Date:** 2026-05-23  
**Status:** completed  
**Result label:** ESM2-augmented GNN prioritization results.  
**Checkpoint:** `checkpoints/clean_split/xl_esm_full/seed_42/best.ckpt`  
**Threshold:** `0.7001100182533264`  
**Scope:** PCNA per-structure regeneration and reporting audit only. No retraining was performed. No MD workflows were modified.

---

## Purpose

Regenerate and audit PCNA-specific per-structure reports using only the homology-clean `xl_esm_full` checkpoint, then determine the safest final framing after the regenerated outputs materially changed the previous PCNA conclusions.

This experiment supersedes PCNA reporting based on deprecated random-split or contaminated checkpoints.

---

## Inputs

| Input | Value |
|---|---|
| Final reporting checkpoint | `checkpoints/clean_split/xl_esm_full/seed_42/best.ckpt` |
| Benchmark provenance | E004 homology-clean split and ablation suite |
| PCNA structures regenerated | 59 |
| Selection threshold | Validation-selected MCC threshold, `0.7001100182533264` |
| Reporting label | `ESM2-augmented GNN prioritization results.` |
| Regeneration script | `scripts/regenerate_pcna_xl_esm_full_reports.py` |

---

## Clean-Split Benchmark Context

The final benchmark checkpoint is `xl_esm_full`, selected from the clean-split ablation suite:

| Condition | Test AUPRC mean | 95% CI | Test AUROC mean |
|---|---:|---|---:|
| small_geometry | 0.1551 | 0.0549-0.2426 | 0.7626 |
| xl_geometry | 0.1923 | 0.1161-0.2682 | 0.8325 |
| xl_esm_zero | 0.1071 | 0.0465-0.1773 | 0.6815 |
| xl_esm_full | 0.2513 | 0.1267-0.3815 | 0.8649 |

Interpretation: `xl_esm_full` is the strongest clean-split condition, but the ESM-zero ablation is weak. Final claims must describe the model as ESM2-augmented and exploratory, not as a pure structural cryptic-pocket detector.

---

## Regenerated PCNA Results

| Metric | Result |
|---|---:|
| PCNA structures regenerated | 59 |
| Structures with any thresholded cluster | 22 |
| Top-ranked structure | `1W60` |
| Top `1W60` cluster mean score | 0.710175 |
| Top `1W60` cluster max score | 0.716435 |
| Top `1W60` cluster size | 4 residues |
| Top `1W60` AOH/MD-region overlap | 3 residues |
| Maximum top-cluster AOH overlap across regenerated structures | 3 residues |
| `8GLA` rank | 52 |
| `8GLA` thresholded clusters | 0 |
| `8GLA` residues above threshold | 2 |
| `8GLA` max residue score | 0.704566 |

Top regenerated PCNA rankings:

| Rank | PDB | Top cluster mean | Top cluster residues | AOH overlap |
|---:|---|---:|---:|---:|
| 1 | 1W60 | 0.710175 | 4 | 3 |
| 2 | 8GL9 | 0.709677 | 3 | 0 |
| 3 | 5MAV | 0.709532 | 3 | 2 |
| 4 | 6EHT | 0.709295 | 4 | 3 |
| 5 | 4ZTD | 0.709274 | 4 | 3 |
| 6 | 4D2G | 0.709219 | 3 | 2 |
| 7 | 9GY0 | 0.709131 | 3 | 0 |
| 8 | 1VYM | 0.708992 | 4 | 3 |
| 9 | 6GIS | 0.708956 | 4 | 3 |
| 10 | 9EOA | 0.708627 | 3 | 0 |

The final top `1W60` cluster is:

| Residues | Mean score | Max score | Dominant annotation | AOH/MD overlap |
|---|---:|---:|---|---:|
| `B42(SER)`, `B43(SER)`, `B44(HIS)`, `B45(VAL)` | 0.710175 | 0.716435 | Front-face loop / PIP-box groove | 3 |

This cluster is biologically locatable near the front-face/PIP-box groove and overlaps part of the AOH contact region, but it is only a sparse 4-residue signal.

---

## Audit Answers

### Rank and score of the MD-validated pocket

The full MD/AOH1996 pocket is not recovered as a ranked cluster under the regenerated `xl_esm_full` outputs. It is therefore unranked as a complete pocket.

The only related signal is the top `1W60` cluster, which is global rank 1 with mean score 0.710175 and max score 0.716435, but it covers only four residues and overlaps only three residues from the MD/AOH-region residue set.

### Overlap with the final top `1W60` cluster

Yes, but only partially. The final top `1W60` cluster overlaps `B42`, `B44`, and `B45` from the MD/AOH-region residue set. It misses the broader AOH region, including the IDCL and C-terminal contact residues.

### Biological interpretation of the top `1W60` cluster

The top `1W60` cluster is biologically interpretable as a front-face/PIP-box-groove-adjacent signal, but it is too sparse to call a recovered pocket. It should be reported as residue prioritization, not pocket discovery.

### Recovery of the known AOH1996 region

No regenerated PCNA structure meaningfully recovers the known AOH1996 region. The maximum top-cluster AOH overlap is only three residues. The positive-control holo structure `8GLA` has no thresholded DBSCAN cluster under the regenerated clean-split checkpoint.

### Final claim downgrade

The project claim should be downgraded from hidden pocket discovery to ESM2-augmented residue prioritization and hypothesis generation.

---

## Material Change Relative to Previous Reports

The regenerated conclusions changed materially. Previous PCNA reports showed broad, high-overlap AOH-region clusters in several structures. The clean-split `xl_esm_full` regeneration collapses those broad clusters into sparse, near-threshold residue signals. The strongest signal is now a 4-residue `1W60` cluster rather than a recovered AOH1996 pocket.

Deprecated conclusion:

> The model discovered or recovered a hidden AOH1996 pocket in apo PCNA.

Current defensible conclusion:

> Using the homology-clean `xl_esm_full` checkpoint, the PCNA analysis identifies sparse, biologically plausible residue-prioritization signals near the AOH/PIP-groove region, but does not robustly recover the known AOH1996 pocket and should be framed as hypothesis generation rather than hidden-pocket discovery.

---

## Files Updated or Generated

Keep these regenerated clean-split PCNA outputs for final reporting:

- `results/per_structure/summary_table.csv`
- `results/per_structure/pcna_rankings.csv`
- `results/per_structure/pocket_score_summaries.csv`
- `results/per_structure/regeneration_manifest_xl_esm_full.json`
- `results/per_structure/ranked.png`
- `results/per_structure/profiles.png`
- `results/per_structure/score_vs_aoh_overlap.png`
- `results/per_structure/full_analysis.png`
- `results/figures/pcna_xl_esm_full_ranked.png`
- `results/figures/pcna_xl_esm_full_profiles.png`
- `results/figures/pcna_xl_esm_full_score_vs_aoh.png`
- `results/figures/pcna_xl_esm_full_full_analysis.png`
- Per-structure regenerated `scores.csv`, `clusters.csv`, `report.txt`, and `summary.json` under `results/per_structure/{PDB}/`.

Use these benchmark artifacts as the only benchmark reporting source:

- `data/splits/cryptosite_homology30_split.json`
- `data/results/homology30_audit.json`
- `data/results/split_integrity_40.json`
- `data/results/split_integrity_520.json`
- `data/results/clean_split_evaluation.json`
- `data/results/clean_split_summary.md`
- condition-specific clean summaries in `data/results/clean_split_summary_*.md`

---

## Figures and Tables to Remove or Archive From Final Reporting

Do not use these as final evidence:

- Old random-split or contaminated benchmark tables, including headline metrics from `data/results/EVALUATION_REPORT.md`, `data/results/extended_metrics.json`, and `data/results/test_split_eval*.json`.
- Old PCNA per-structure outputs from `results/v3/`.
- Old PCNA bulk inference outputs from `results/bulk_inference/`.
- Any figure that claims broad AOH-region recovery or hidden-pocket discovery from pre-clean-split checkpoints.
- Any MD figure used as validation of pocket opening; current MD evidence is preliminary and does not validate opening.

Architecture, pipeline, and data-flow figures may remain if their captions do not cite deprecated benchmark numbers or hidden-pocket discovery claims.

---

## Reporting Rule

Every final PCNA result table or figure caption should include:

> ESM2-augmented GNN prioritization results.

Do not reuse deprecated random-split or contaminated metrics in final PCNA reporting.
