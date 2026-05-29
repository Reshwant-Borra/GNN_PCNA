---
type: phase3-handoff
date: 2026-05-29
author: claude-sonnet-4-6
session: gate4-gate5-complete
status: GATE_5_CLEARED
---

# Phase 3 Handoff — Test Evaluation Complete

## What Was Done This Session

| Step | Status | Artifact |
|---|---|---|
| GATE 4 draft (Option B, v2) | DONE | `reports/phase3/model_freeze_gate4_DRAFT_20260529.md` (now renamed) |
| Option B authorization recorded | DONE | `reports/phase3/spatial_only_retrain_authorization_20260529.md` |
| Spatial-only retrain (12 runs) | DONE | `checkpoints/phase3/spatial_only_fold*_seed*_best.pt`, `reports/phase3/spatial_only_training_runs/` |
| PyTorch upgraded to CUDA | DONE | torch 2.9.1+cpu → 2.11.0+cu128; RTX 4070 active |
| GATE 4 approved by Reshwant | DONE | `reports/phase3/model_freeze_gate4_20260529.md` (decision: APPROVED) |
| evaluate_test_set.py written | DONE | `scripts/evaluate_test_set.py` |
| GATE 5 — test evaluation run | DONE | `reports/phase3/test_evaluation_20260529.md` |
| One-shot lock written | DONE | `reports/phase3/.test_evaluation_lock` |
| PROJECT_STATE.md updated | DONE | `.memory/PROJECT_STATE.md` |
| wiki/log.md updated | DONE | `wiki/log.md` |

## Frozen Model

| Property | Value |
|---|---|
| Checkpoint | `checkpoints/phase3/spatial_only_fold1_seed1_best.pt` |
| Architecture | GraphSAGE-3L, spatial edges only (edge_type==0) |
| Val macro-AUPRC at freeze | 0.2047 (fold=1, seed=1) |
| Sequential edges | **Permanently removed** |
| GATE 4 record | `reports/phase3/model_freeze_gate4_20260529.md` |
| decision_id | `phase3_model_freeze_20260529` |

## Test Results (FINAL — one-shot, cannot be re-run)

| Metric | Value | 95% CI |
|---|---|---|
| **Macro-AUPRC (primary)** | **0.2034** | [0.1825, 0.2275] |
| Micro-AUPRC | 0.0973 | — |
| Macro-AUROC | 0.6902 | [0.6652, 0.7143] |
| Micro-AUROC | 0.6832 | — |
| Top-5 recovery | 0.0726 | — |
| Top-10 recovery | 0.1220 | — |
| Top-20 recovery | 0.2179 | — |
| Precision@5 | 0.2009 | — |
| Precision@10 | 0.1771 | — |
| Precision@20 | 0.1523 | — |
| n_test structures | 214 | — |
| n_proteins valid AUPRC | 177 / 214 | — |

## Notable Findings for Next Agent / Review

1. **Test > val average:** Test macro-AUPRC (0.2034) exceeds the spatial-only
   overall validation mean (0.1897 ± 0.0091). This is a healthy result — no
   overfitting. The test partition appears similarly challenging to fold-1,
   which was the strongest validation fold.

2. **Macro/micro gap:** micro-AUPRC (0.0973) is substantially below macro
   (0.2034). This is expected: pooling all residues across 214 proteins
   introduces heavy class imbalance (~4.6% positive rate globally) and
   may be dominated by a few large proteins with many negative residues.
   Macro is the pre-specified primary metric and is the reportable number.

3. **37 proteins with no valid AUPRC:** These have only one class in their
   masked-label evaluation (all positives or all negatives after applying
   loss_mask). This is a known property of the PU-framing label set; it
   is not a bug. Future work may investigate imputing scores for these.

4. **External baselines still missing:** fpocket, P2Rank, PocketMiner not
   run. Superiority language is blocked until these are run on the same
   frozen split (hash: 24dd5e347d880108). Stubs:
   `reports/phase3/baseline_runs/{fpocket,p2rank,pocketminer}_manifest.json`.

5. **GATE 6 is the next gate:** PCNA inference on candidates from
   `data/registries/phase4_candidate_manifest.json` requires a separate
   human decision. Top candidate: 1AXC. Positive control: 8GLA (note: 5E0V
   is NOT apo PCNA — see open question in `wiki/open_questions/open-questions.md`).

## What Is Left

| Gate | Status | Who |
|---|---|---|
| GATE 6 — PCNA inference | BLOCKED — human decision required | Reshwant |
| External baselines | Not run — install required | Reshwant / agent |
| Phase 3 conclusions report | Not written — awaits external baselines | Agent |
| Phase 4 (PCNA discovery) | Blocked on GATE 6 | Reshwant |

## Key File Locations

```
reports/phase3/test_evaluation_20260529.md          — FINAL test report
reports/phase3/test_evaluation_manifest_20260529.json — machine-readable
reports/phase3/.test_evaluation_lock                 — one-shot guard
reports/phase3/model_freeze_gate4_20260529.md        — GATE 4 record
checkpoints/phase3/spatial_only_fold1_seed1_best.pt  — frozen model
reports/phase3/spatial_only_training_runs/           — Option B manifests
.memory/PROJECT_STATE.md                             — current state
```
