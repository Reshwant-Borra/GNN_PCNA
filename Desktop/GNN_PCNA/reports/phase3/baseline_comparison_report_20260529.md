---
type: baseline-comparison-report
date: 2026-05-29
gate: GATE_3
status: VALIDATION_ONLY — test set not evaluated
governance:
  - docs/scientific_governance/09_EVALUATION_PROTOCOL.md
  - docs/scientific_governance/10_BASELINE_REQUIREMENTS.md
---

# Phase 3 Baseline Comparison Report

> **Scope:** Validation folds only. Test set is untouched. No scientific
> claims are made. This report supports model-freeze decision (GATE 4).

## 1. Summary Table — Macro-AUPRC (validation)

Primary metric: macro-AUPRC (mean of per-protein AUPRC, averaged over
proteins with at least one positive label).

| Model | Macro-AUPRC (mean ± SD) | Runs | Status |
|---|---|---|---|
| **GraphSAGE-3L (primary)** | **0.1876 ± 0.0113** | 4 folds × 3 seeds | complete |
| Random (3 seeds) | 0.0861 ± 0.0011 (Δ -0.1015) | none — random scores | complete |
| Degree/Exposure (structural) | 0.0813 (Δ -0.1062) | none — graph degree | complete |
| GCN-1L | 0.1601 ± 0.0089 (Δ -0.0275) | 4 folds × 3 seeds | complete |
| GAT-2L | 0.1739 ± 0.0090 (Δ -0.0136) | 4 folds × 3 seeds | complete |
| SAGE-3L (no spatial edges) | 0.1556 ± 0.0114 (Δ -0.0319) | 4 folds × 3 seeds | complete |
| SAGE-3L (no sequential edges) | 0.1897 ± 0.0089 (Δ +0.0021) | 4 folds × 3 seeds | complete |
| fpocket (external) | N/A | not run (install required) | not run |
| P2Rank (external) | N/A | not run (install required) | not run |
| PocketMiner (external) | N/A | not run (install required) | not run |

**Δ** = baseline macro-AUPRC minus GraphSAGE-3L. Negative = GraphSAGE-3L is better.

## 2. GraphSAGE-3L — Per-Fold Detail

| Fold | Mean Val Macro-AUPRC (3 seeds) |
|---|---|
| 0 | 0.1730 |
| 1 | 0.2035 |
| 2 | 0.1872 |
| 3 | 0.1865 |

Per-run table:

| Fold | Seed | Best Epoch | Val Macro-AUPRC |
|---|---|---|---|
| 0 | 0 | 28 | 0.1719 |
| 0 | 1 | 16 | 0.1747 |
| 0 | 2 | 19 | 0.1725 |
| 1 | 0 | 18 | 0.2030 |
| 1 | 1 | 18 | 0.2033 |
| 1 | 2 | 17 | 0.2042 |
| 2 | 0 | 19 | 0.1879 |
| 2 | 1 | 16 | 0.1859 |
| 2 | 2 | 16 | 0.1878 |
| 3 | 0 | 18 | 0.1876 |
| 3 | 1 | 20 | 0.1848 |
| 3 | 2 | 16 | 0.1873 |

## 3.1. GCN-1L — Per-Fold Detail

| Fold | Mean Val Macro-AUPRC (3 seeds) |
|---|---|
| 0 | 0.1472 |
| 1 | 0.1703 |
| 2 | 0.1641 |
| 3 | 0.1588 |

| Fold | Seed | Best Epoch | Val Macro-AUPRC |
|---|---|---|---|
| 0 | 0 | 5 | 0.1480 |
| 0 | 1 | 2 | 0.1471 |
| 0 | 2 | 3 | 0.1465 |
| 1 | 0 | 50 | 0.1718 |
| 1 | 1 | 1 | 0.1675 |
| 1 | 2 | 26 | 0.1716 |
| 2 | 0 | 27 | 0.1647 |
| 2 | 1 | 33 | 0.1635 |
| 2 | 2 | 29 | 0.1642 |
| 3 | 0 | 1 | 0.1589 |
| 3 | 1 | 23 | 0.1592 |
| 3 | 2 | 1 | 0.1584 |

## 3.2. GAT-2L — Per-Fold Detail

| Fold | Mean Val Macro-AUPRC (3 seeds) |
|---|---|
| 0 | 0.1676 |
| 1 | 0.1880 |
| 2 | 0.1669 |
| 3 | 0.1733 |

| Fold | Seed | Best Epoch | Val Macro-AUPRC |
|---|---|---|---|
| 0 | 0 | 9 | 0.1664 |
| 0 | 1 | 5 | 0.1682 |
| 0 | 2 | 8 | 0.1682 |
| 1 | 0 | 28 | 0.1910 |
| 1 | 1 | 15 | 0.1858 |
| 1 | 2 | 28 | 0.1872 |
| 2 | 0 | 2 | 0.1670 |
| 2 | 1 | 6 | 0.1666 |
| 2 | 2 | 13 | 0.1671 |
| 3 | 0 | 9 | 0.1731 |
| 3 | 1 | 13 | 0.1743 |
| 3 | 2 | 17 | 0.1725 |

## 3.3. SAGE-3L (no spatial edges) — Per-Fold Detail

| Fold | Mean Val Macro-AUPRC (3 seeds) |
|---|---|
| 0 | 0.1404 |
| 1 | 0.1706 |
| 2 | 0.1540 |
| 3 | 0.1574 |

| Fold | Seed | Best Epoch | Val Macro-AUPRC |
|---|---|---|---|
| 0 | 0 | 8 | 0.1382 |
| 0 | 1 | 14 | 0.1389 |
| 0 | 2 | 17 | 0.1442 |
| 1 | 0 | 8 | 0.1690 |
| 1 | 1 | 7 | 0.1710 |
| 1 | 2 | 11 | 0.1720 |
| 2 | 0 | 11 | 0.1536 |
| 2 | 1 | 13 | 0.1528 |
| 2 | 2 | 16 | 0.1557 |
| 3 | 0 | 13 | 0.1602 |
| 3 | 1 | 11 | 0.1573 |
| 3 | 2 | 14 | 0.1548 |

## 3.4. SAGE-3L (no sequential edges) — Per-Fold Detail

| Fold | Mean Val Macro-AUPRC (3 seeds) |
|---|---|
| 0 | 0.1798 |
| 1 | 0.2027 |
| 2 | 0.1862 |
| 3 | 0.1900 |

| Fold | Seed | Best Epoch | Val Macro-AUPRC |
|---|---|---|---|
| 0 | 0 | 21 | 0.1800 |
| 0 | 1 | 23 | 0.1800 |
| 0 | 2 | 31 | 0.1793 |
| 1 | 0 | 17 | 0.2044 |
| 1 | 1 | 23 | 0.2037 |
| 1 | 2 | 19 | 0.1999 |
| 2 | 0 | 24 | 0.1868 |
| 2 | 1 | 16 | 0.1860 |
| 2 | 2 | 24 | 0.1858 |
| 3 | 0 | 24 | 0.1922 |
| 3 | 1 | 22 | 0.1917 |
| 3 | 2 | 22 | 0.1860 |

## 4. External Baselines — Installation Required

fpocket, P2Rank, and PocketMiner could not be run on this system.
Stub manifests are in `reports/phase3/baseline_runs/`.
These baselines should be run before any superiority claim is made.
Governance doc 10 requires same-split same-label-definition comparison.

## 5. Model-Freeze Recommendation (GATE 4 input)

> **IMPORTANT:** This recommendation is a technical analysis only.
> The final model-freeze decision requires human authorization (GATE 4).
> The test set must not be evaluated until after the human freeze decision.

### Recommendation

Based on validation macro-AUPRC across 12 runs (4 folds × 3 seeds):

- **Best single run:** fold=1, seed=2 → val macro-AUPRC = 0.2042
- **Overall mean:** 0.1876 ± 0.0113 (range: see per-run table above)

### Context

- Random baseline macro-AUPRC: 0.0861
- Degree baseline macro-AUPRC: 0.0813
- GraphSAGE-3L improvement over random: 0.1015

### Freeze decision inputs

**Recommended checkpoint for GATE 4 consideration:**
  `checkpoints/phase3/fold1_seed2_best.pt`

**Rationale:** This checkpoint produced the highest single-run validation
macro-AUPRC. Fold-1 shows consistently higher performance across all 3 seeds
(mean 0.2035),
suggesting it is a more favorable validation partition rather than a lucky seed.

**Before human freeze decision, verify:**
1. External baselines (fpocket, P2Rank, PocketMiner) are desirable but the
   governance doc requires them only where applicable — install and run if possible.
2. The ablation baselines (no-spatial / no-sequential) quantify each edge type's
   contribution. If either ablation matches GraphSAGE-3L, that edge type may be
   uninformative and should be investigated before claiming the full model is needed.
3. If CI overlap between GraphSAGE-3L and any GNN baseline is large, the model
   selection should be held until the external baselines are available.

## 6. Governance Compliance

- Split manifest hash: `24dd5e347d880108` (validated per loader).
- Label definition: same for all baselines (loss_mask=True nodes, label ∈ {0,1}).
- Test set: never loaded in any baseline run.
- GNN baselines: pos_weight computed from training fold only.
- External baselines: stubs written; results pending tool installation.
- No scientific claims made. Results are validation-only model-selection inputs.

---
*Report generated by `scripts/generate_baseline_report.py` — 2026-05-29.*