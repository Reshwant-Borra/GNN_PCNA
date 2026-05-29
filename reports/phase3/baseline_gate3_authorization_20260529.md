---
type: human-gate-record
gate: GATE_3
decision_id: phase3_baseline_gate3_20260529
date: 2026-05-29
authorized_by: Reshwant-Borra
status: AUTHORIZED
---

# GATE 3 — Baseline Runs Authorization

## Decision

Baseline runs are authorized for all required baselines listed below, on the
frozen validation splits only. No test-set evaluation is performed at this stage.
No scientific claims are made from baseline results alone.

## Authorization Context

- GATE 1 cleared: first graph release (1,101 graphs, 0 failures).
- GATE 2 cleared: first training sign-off (`first_training_signoff_20260528.md`).
- First training complete: 12/12 runs, overall val macro-AUPRC 0.1876 ± 0.0113.
- This GATE 3 record authorizes the agent to implement and run all required baselines.

## Authorized Baselines

| Baseline | Type | Note |
|---|---|---|
| random | statistical | 3 seeds, no training |
| degree (structural) | structural | negative spatial degree, no training |
| GCN-1L | GNN | 4 folds × 3 seeds |
| GAT-2L | GNN | 4 folds × 3 seeds |
| sage_no_spatial | ablation | GraphSAGE-3L, sequential edges only, 4 folds × 3 seeds |
| sage_no_sequential | ablation | GraphSAGE-3L, spatial edges only, 4 folds × 3 seeds |
| fpocket | external | stub only — requires fpocket binary install |
| P2Rank | external | stub only — requires Java + P2Rank install |
| PocketMiner | external | stub only — requires PocketMiner install |

## Hard Constraints

- All baselines use the frozen split manifest (hash: 24dd5e347d880108).
- All baselines use the same label definition (loss_mask=True nodes only).
- Validation folds only — test set is never loaded.
- No scientific claims from this session.
- GNN baselines: val-fold × seed structure mirrors the main GraphSAGE-3L runs.
- External baselines: scripts created, results pending tool installation.

## Output Targets

- Per-baseline manifests: `reports/phase3/baseline_runs/<baseline>_manifest.json`
- Per-run manifests: `reports/phase3/baseline_runs/<baseline>_fold*_seed*_manifest.json`
- Comparison report: `reports/phase3/baseline_comparison_report_20260529.md`

## Governance

- `docs/scientific_governance/10_BASELINE_REQUIREMENTS.md`
- `docs/scientific_governance/09_EVALUATION_PROTOCOL.md`
- `docs/scientific_governance/19_STOP_CONDITIONS.md`
- `docs/scientific_governance/16_CODING_AGENT_RULES.md`
