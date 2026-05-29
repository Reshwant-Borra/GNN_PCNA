---
type: phase3-handoff
date: 2026-05-29
author: claude-sonnet-4-6
status: GATE_4_AWAITING_HUMAN
---

# Phase 3 Handoff — Baselines Complete, GATE 4 Ready

## What Is Done (Phase 3)

| Step | Status | Artifact |
|---|---|---|
| Graph generation (1,101 structures) | DONE | `data/graphs/` |
| First training (GraphSAGE-3L, 4 folds × 3 seeds) | DONE | `checkpoints/phase3/`, `reports/phase3/training_runs/` |
| Random baseline | DONE | `reports/phase3/baseline_runs/random_manifest.json` — 0.0861 ± 0.0011 |
| Degree baseline | DONE | `reports/phase3/baseline_runs/degree_manifest.json` — 0.0813 |
| GCN-1L baseline | DONE | `reports/phase3/baseline_runs/gcn_1l_manifest.json` — 0.1601 ± 0.0089 |
| GAT-2L baseline | DONE | `reports/phase3/baseline_runs/gat_2l_manifest.json` — 0.1739 ± 0.0090 |
| SAGE no-spatial ablation | DONE | `reports/phase3/baseline_runs/sage_no_spatial_manifest.json` — 0.1556 ± 0.0114 |
| SAGE no-sequential ablation | DONE | `reports/phase3/baseline_runs/sage_no_sequential_manifest.json` — 0.1897 ± 0.0089 |
| Baseline comparison report | DONE | `reports/phase3/baseline_comparison_report_20260529.md` |

## What Is Left (Phase 3)

### GATE 4 — Model Freeze (HUMAN REQUIRED FIRST)

**Reshwant must write:** `reports/phase3/model_freeze_gate4_20260529.md`

Minimum content:
```
decision_id: phase3_model_freeze_20260529
checkpoint: checkpoints/phase3/fold1_seed2_best.pt
val_macro_auprc: 0.2042
authorized_by: Reshwant
date: 2026-05-29
```

Recommended checkpoint: `checkpoints/phase3/fold1_seed2_best.pt` (val 0.2042, fold-1 mean 0.2035).

Critical flag: `sage_no_sequential` (spatial-only edges) scored 0.1897 vs full SAGE 0.1876 (Δ=+0.0021, within 1 SD). Sequential edges appear non-contributory. Reshwant decides whether to freeze the full model as-is or investigate further.

---

### GATE 5 — Test-Set Evaluation (AGENT, after GATE 4)

Once `reports/phase3/model_freeze_gate4_20260529.md` exists, run once only:

```bash
python scripts/evaluate_test_set.py \
  --checkpoint checkpoints/phase3/fold1_seed2_best.pt \
  --split test \
  --output reports/phase3/test_evaluation_20260529.md
```

**This script does not exist yet and must be written.** It must:
- Load the frozen checkpoint
- Load test-split structures (split=`test`, 214 structures)
- Compute macro-AUPRC, micro-AUPRC, macro/micro-AUROC, top-k recovery (k=5,10,20) with bootstrap 95% CI
- Write results to `reports/phase3/test_evaluation_YYYYMMDD.md`
- Never re-run (governance: one-shot evaluation only)
- Governance ref: `docs/scientific_governance/09_EVALUATION_PROTOCOL.md`

---

### GATE 6 — PCNA Inference (HUMAN REQUIRED, after GATE 5)

Separate human authorization required before any PCNA prediction is made or interpreted.
- PCNA candidates: `data/registries/phase4_candidate_manifest.json`
- Top candidate: 1AXC; positive control: 8GLA
- Governance ref: `docs/scientific_governance/12_PCNA_SPECIFIC_CHECKS.md`, `14_CLAIM_POLICY.md`

---

## Key Numbers

| Model | Val Macro-AUPRC |
|---|---|
| GraphSAGE-3L (primary) | 0.1876 ± 0.0113 |
| Best single run (fold=1 seed=2) | 0.2042 |
| Random baseline | 0.0861 |
| SAGE over random | +0.1015 |

## Key Files for Next Agent

```
.memory/PROJECT_STATE.md          ← current phase/blockers/next tasks
.memory/INDEX.md                  ← task routing table
docs/scientific_governance/09_EVALUATION_PROTOCOL.md   ← test eval rules
docs/scientific_governance/19_STOP_CONDITIONS.md        ← stop gates
docs/scientific_governance/26_HUMAN_REVIEW_GATES.md     ← gate requirements
reports/phase3/baseline_comparison_report_20260529.md   ← full baseline results
reports/phase3/training_runs/all_runs_summary.json      ← per-run training results
checkpoints/phase3/fold1_seed2_best.pt                  ← recommended freeze checkpoint
src/phase3_evaluation/metrics.py                        ← metrics implementation (reuse for test eval)
src/phase3_data/graph_loader.py                         ← data loader (reuse for test eval)
```
