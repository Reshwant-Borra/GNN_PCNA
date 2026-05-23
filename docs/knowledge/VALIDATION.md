# VALIDATION.md - Validation System

-> Links: [[EXPERIMENT_INDEX]] | [[KNOWN_LIMITATIONS]] | [[PIPELINE]] | [[MODELS]]

---

## Current Status

The previous random CryptoSite split is superseded. Homology leakage was found across the old train and held-out sets, so those AUROC/AUPRC values must not be used as headline benchmark claims.

Final clean-split benchmark status:

- `data/splits/cryptosite_homology30_split.json` created by `scripts/make_homology_split.py`.
- `data/results/homology30_audit.json` with zero train-to-val/test MMseqs2 cluster overlap at 30% identity.
- Three seeds (`42`, `43`, `44`) completed for all four conditions: `small_geometry`, `xl_geometry`, `xl_esm_zero`, `xl_esm_full`.
- `data/results/clean_split_evaluation.json` and `data/results/clean_split_summary.md` contain the final all-condition results.
- AUPRC as the primary metric, with bootstrap confidence intervals over structures.
- Degenerate-label structures (<5 positives) listed individually and excluded from aggregate claims.

| Condition | Seeds | Test AUPRC mean | 95% CI | Test AUROC mean | Degenerate test structures |
|---|---:|---:|---|---:|---:|
| small_geometry | 3 | 0.1551 | 0.0549-0.2426 | 0.7626 | 2 |
| xl_geometry | 3 | 0.1923 | 0.1161-0.2682 | 0.8325 | 2 |
| xl_esm_zero | 3 | 0.1071 | 0.0465-0.1773 | 0.6815 | 2 |
| xl_esm_full | 3 | 0.2513 | 0.1267-0.3815 | 0.8649 | 2 |

Interpretation: `xl_esm_full` is the strongest condition, but the large gap versus `xl_esm_zero` means the result is ESM2-augmented and sequence context is a major confound. `xl_geometry` is stronger than `small_geometry`, supporting some architecture/geometry signal, but not enough to claim a validated cryptic-pocket predictor.

## PCNA Final Reporting Checkpoint

Use `checkpoints/clean_split/xl_esm_full/seed_42/best.ckpt` as the final PCNA reporting checkpoint.

All regenerated PCNA outputs must be labeled:

> ESM2-augmented GNN prioritization results.

Regenerated PCNA audit summary:

| Item | Result |
|---|---:|
| Structures regenerated | 59 |
| Structures with thresholded clusters | 22 |
| Top-ranked structure | `1W60` |
| Top `1W60` cluster mean score | 0.710175 |
| Top `1W60` cluster size | 4 residues |
| Top `1W60` AOH/MD-region overlap | 3 residues |
| `8GLA` thresholded clusters | 0 |
| Maximum top-cluster AOH overlap across structures | 3 residues |

The full AOH1996/MD pocket is not recovered as a ranked cluster. The top `1W60` cluster is biologically locatable near the front-face/PIP-box groove, but it is a sparse residue-prioritization signal and must not be called a discovered pocket.

## Positive Control

8GLA is a positive-control sanity check only because it is used in PCNA fine-tuning. Never report 8GLA AUROC as independent performance.

Use wording:

- "GNN-prioritized candidate residue cluster"
- not "validated cryptic pocket"

## Required Commands

```bash
python scripts/check_env.py
python scripts/make_homology_split.py
python scripts/validate_split_integrity.py --split data/splits/cryptosite_homology30_split.json --graph-dir data/graphs --feature-dim 40
python scripts/validate_split_integrity.py --split data/splits/cryptosite_homology30_split.json --graph-dir data/graphs_xl --feature-dim 520
python scripts/train_ablation_suite.py
python scripts/evaluate_clean_split.py
```

## Split Rules

- Split structure-level connected components, never residues or individual chains.
- MMseqs2 is the required homology backend at 30% sequence identity.
- Training must fail if the homology audit reports leakage.
- Keep 40-dim geometry graphs and 520-dim XL/ESM2 graphs separate; never infer feature mode from a mixed directory.

## Metric Rules

| Metric | Role |
|---|---|
| AUPRC | Primary metric for imbalanced residue labels |
| AUROC | Secondary metric only |
| MCC | Threshold selection metric, selected on validation only |
| AUPRC baseline | Positive residue fraction |
| Bootstrap CI | Resample structures, not residues |

## Dynamics Evidence

Current MD/ANM evidence is preliminary only. The current MD fold-change <1.0 is not supportive of enhanced apo pocket flexibility, so it should not be framed as validation of pocket opening.

---

## Related

[[KNOWN_LIMITATIONS]] | [[EXPERIMENT_INDEX]] | [[BUG_LOG]]
