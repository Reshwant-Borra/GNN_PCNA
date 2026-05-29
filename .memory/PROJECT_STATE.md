---
updated: 2026-05-29
updated_by: claude-sonnet-4-6 (gate5-test-evaluation-complete)
---

# Project State - GNN-PCNA

This file is the single authoritative current-state snapshot. Agents update it at every
session close. Read it immediately after `CLAUDE.md` or `AGENTS.md`.

**Staleness check:** If `updated` in the frontmatter above is >7 days before today's date,
treat this file as potentially stale. Reconstruct current state from
`wiki/analyses/coding_agent_context.md` and the most recent
`reports/phase2/handoff_YYYYMMDD.md`, then update this file before starting any task.

---

## Phase

**Phase 3 — TEST EVALUATION COMPLETE. GATE 5 CLEARED. GATE 6 (PCNA INFERENCE) BLOCKED.**

| System | Status |
|---|---|
| Training (full model) | **COMPLETE**. 12/12 runs. Val macro-AUPRC: **0.1876 ± 0.0113**. |
| Training (spatial-only) | **COMPLETE** (Option B). 12/12 runs. Val macro-AUPRC: **0.1897 ± 0.0091**. Best: fold=1 seed=1 → 0.2047. |
| Baselines | **COMPLETE** (GATE 3). GNN baselines done. External tools (fpocket/P2Rank/PocketMiner): stubs only. |
| Test evaluation | **COMPLETE — ONE-SHOT USED** (GATE 5 cleared 2026-05-29). Test macro-AUPRC: **0.2034** [0.1825, 0.2275] 95% CI. Micro-AUPRC: 0.0973. Macro-AUROC: 0.6902. Top-20 recovery: 0.2179. 214 structures, 177 with valid AUPRC. Lock: `reports/phase3/.test_evaluation_lock`. Report: `reports/phase3/test_evaluation_20260529.md`. |
| Molecular dynamics | BLOCKED (Phase 3+ scope) |
| Scientific claims | BLOCKED — external baselines (fpocket/P2Rank/PocketMiner) not yet run; superiority claims require them per doc 10. |
| PCNA inference | BLOCKED — GATE 6 requires separate human decision. |
| Graph generation | **FIRST GRAPH RELEASE APPROVED**. 1,101 graphs, 0 failures. Approval: `reports/phase3/first_graph_release_approval_20260528.md`. |
| Molecular dynamics | BLOCKED (Phase 3+ scope) |
| Scientific claims | BLOCKED (baselines not fully complete, test set not evaluated, claim gates not cleared) |
| Split freeze | **FROZEN** - `data/registries/split_manifest_frozen.json` (hash: 24dd5e347d880108) |
| Label freeze | **FROZEN** - `data/labels/label_manifest.json` |

All Phase 2 blockers cleared. GATE 1 (graph release) and GATE 2 (first-training sign-off)
cleared. First training complete. Baselines, model freeze, and test evaluation are all
blocked until human review approvals are recorded.

---

## What Is Done

- **Governance scaffold:** 40 binding docs in `docs/scientific_governance/` - complete.
- **Wiki scaffold + memory system:** wiki + `.memory/` layer + `CLAUDE.md` + `00_COMPACT_INDEX.md` - complete.
- **Intake infrastructure:** `scripts/dataset_intake.py` + `src/phase2_intake/` - complete.
- **CryptoBench adopted for v2 supervised benchmark use:** cryptic-only, with approved exclusions and limitations.
- **PCNA isolation policy:** approved. PCNA structures are holdout-only and must not enter train/validation/model selection.
- **Label supervision contract:** approved positive-unlabeled framing. `label=1` is positive; `label=-1` is masked/excluded from loss; unlisted residues are not true negatives.
- **Residue mapping:** all decisions approved. Mask absent residues; exclude records over the approved missing-residue threshold and wrong-chain records.
- **Sequence clustering:** RCSB 30% identity clustering complete; PCNA cluster ID = 1168; cross-fold risks resolved.
- **Split manifest frozen:** `data/registries/split_manifest_frozen.json`, hash `24dd5e347d880108`, 1,101 structures. Distribution: test=214, train-0=220, train-1=223, train-2=222, train-3=222.
- **Label manifest frozen:** `data/labels/label_manifest.json`; 1,101 structures, 16,335 positives, 3,704 masked residues.
- **Approval record:** `reports/phase2/split_manifest_approval_20260527.md` authorizes Phase 3 dry-run guard removal.
- **Friend crawl metadata artifacts:** present in repo: `data/registries/friend_crawl_registry.json`, `data/registries/friend_feature_schema.json`, `data/registries/friend_crawl_homolog_groups.json`, `reports/phase2/friend_crawl_stats.md`, and `data/raw_intake/friend_sample/`.
- **Phase 3 governed data pipeline skeleton:** rebuilt locally by Codex under `src/phase3_data/`, with tests in `tests/phase3/` and report `reports/phase3/phase3_framework_rebuild_20260528.md`.
- **Phase 3 CIF extraction:** approved CryptoBench zip extracted to `data/raw_intake/cryptobench/cif-files/`; manifest `data/registries/phase3_cif_extraction_manifest_20260528.json` records zip hash and 5,005 extracted CIFs.
- **Phase 3 dataset index:** `data/registries/phase3_dataset_index_20260528.json`, 1,101 non-excluded structures, no PCNA cluster `1168` entries.
- **Phase 3 residue audit:** `data/registries/phase3_residue_audit_manifest_20260528.json`, 1,101 structures audited, 16,335 positives aligned, 3,704 masked labels accounted for, graph edge/feature policy marked unapproved/not generated.
- **Phase 3 dry-run framework skeleton:** `src/phase3_training/`, `src/phase3_model/`, `src/phase3_evaluation/`, and `src/baselines/` exist as fail-closed interfaces/stubs only.
- **Phase 3 graph policy approval packet:** `reports/phase3/graph_edge_feature_policy_approval_packet_20260528.md` approved by `reports/phase3/graph_policy_human_decision_20260528.md`. No graph tensors were generated by the approval-record step.
- **Phase 3 graph generation implemented:** `src/phase3_graphs/` package complete — `constants.py`, `features.py`, `mmcif_coords.py`, `builder.py`, `manifest.py`, `cli.py`. Tests in `tests/phase3/test_phase3_graphs.py` (37 new tests, all passing; total suite 53/53).
- **Phase 3 first graph release complete and approved:** 1,101 structures, 0 failures. Artifacts in `data/graphs/`. Approval: `reports/phase3/first_graph_release_approval_20260528.md` (decision_id: `phase3_first_graph_release_20260528`). GATE 1 cleared.
- **Phase 3 model/training plan approved:** `reports/phase3/model_training_decision_20260528.md` (decision_id: `phase3_model_training_plan_20260528`). Authorizes implementation of GraphSAGE-3L + data loader + training loop + evaluation. Batch-isolation test required before real training (GATE 2).
- **Phase 3 training framework implemented:** `src/phase3_data/graph_loader.py`, `src/phase3_model/gnn.py`, `src/phase3_training/trainer.py`, `src/phase3_evaluation/metrics.py`, `tests/phase3/test_batch_isolation.py`, `tests/phase3/test_phase3_model_loader_metrics.py`. Full test suite 93/93 passing. Batch-isolation test: 4/4 PASSED (GATE 2 prerequisite). Dry-run guard in `gates.py` intact — real training blocked until human GATE 2 sign-off.
- **GATE 2 cleared:** `reports/phase3/first_training_signoff_20260528.md` (decision_id: `phase3_first_training_signoff_20260528`). `gates.py` conditionalized to pass when signoff file present.
- **Phase 3 first training complete:** 12/12 runs (4 folds × 3 seeds). GraphSAGE-3L, hidden_dim=128. Overall val macro-AUPRC: **0.1876 ± 0.0113** (range: [0.1719, 0.2042]). Best: fold=1 seed=2 → 0.2042. Checkpoints: `checkpoints/phase3/fold*_seed*_best.pt`. Report: `reports/phase3/first_training_results_20260528.md`. No test-set evaluation. No scientific claims.
- **Advay branch merged into main (2026-05-29):** fast-forward merge of `origin/advay-parallel-track`. All Phase-4 prep deliverables now on main. `phase3-model-framework` remote branch deleted (fully superseded by main).
- **Phase 3 baseline framework implemented (2026-05-29, GATE 3):** `src/baselines/random_baseline.py`, `src/baselines/structural_baseline.py`, `src/baselines/gnn_models.py` (GCN1L, GAT2L), `src/baselines/gnn_trainer.py`. Master script `scripts/run_baselines.py`. Report generator `scripts/generate_baseline_report.py`. GATE 3 record: `reports/phase3/baseline_gate3_authorization_20260529.md`. Random + degree baselines complete; GCN-1L/GAT-2L/SAGE-ablation training running in background. External tool stubs written for fpocket/P2Rank/PocketMiner.
- **Advay parallel track (Phase-4 prep, Phase-3-independent) — Tracks 1-5 complete (2026-05-28):**
  - Track 2: `scripts/audit_crawl_data.py` (53/72 pass quality filter), `scripts/rank_pcna_candidates.py` (54 ranked; 8GLA force-included positive control; top candidate 1AXC), `scripts/validate_esm_features.py` (60 ESM arrays valid, 146-vs-72 resolved). Outputs in `data/registries/phase4_*.json`.
  - Track 5: `scripts/analyze_heuristic_scores.py` + `reports/phase4/heuristic_score_analysis.md` (+figures). Heuristic = CSV `mean_score` from a prior GNN inference pass; only 4/72 scored.
  - Track 4: `data/registries/pcna_interface_map.json` (all residues cited to PDB+PMID) + `scripts/check_prediction_overlap.py` + reproducible `scripts/derive_pcna_interface_contacts.py`.
  - Track 1: `wiki/entities/pcna_structure.md`, `wiki/entities/pcna_binding_partners.md`, `wiki/analyses/cryptic_pocket_pcna_literature.md`.
  - Track 3: MD pre-registrations `reports/phase4/md/{8gla,5e0v,1axc}/pre_registration.md` (doc-13 template).
  - **Key findings flagged to Reshwant:** (1) 5E0V is NOT apo PCNA — it is the S228I variant + FEN1 peptide (PMID 26688547); a true-apo WT reference is needed before MD. (2) heuristic_pocket_score covers only 4/72 records. See `wiki/open_questions/open-questions.md`. No Phase 3 files touched; no training/graphs/MD/test access/claims.

---

## Current Blockers

No Phase 2 blockers remain.

Phase 3 stop gates:
- **GATE 1 — CLEARED.** First graph release approved: `reports/phase3/first_graph_release_approval_20260528.md`.
- **GATE 2 — CLEARED.** First training sign-off: `reports/phase3/first_training_signoff_20260528.md`.
- **GATE 3 — CLEARED.** Baseline runs authorized by Reshwant on 2026-05-28 after reviewing first training results (0.1876 ± 0.0113 overall val macro-AUPRC). All baselines complete 2026-05-29.
- **GATE 1 — CLEARED.** First graph release approved.
- **GATE 2 — CLEARED.** First training sign-off.
- **GATE 3 — CLEARED.** Baselines authorized and complete.
- **GATE 4 — CLEARED.** Model frozen 2026-05-29. Checkpoint: `checkpoints/phase3/spatial_only_fold1_seed1_best.pt`. Record: `reports/phase3/model_freeze_gate4_20260529.md`.
- **GATE 5 — CLEARED.** Test evaluation complete 2026-05-29. Macro-AUPRC: **0.2034** [0.1825, 0.2275]. Report: `reports/phase3/test_evaluation_20260529.md`. Test set one-shot used — cannot be re-run.
- **GATE 6 — BLOCKED.** PCNA inference requires separate human decision. Candidates: `data/registries/phase4_candidate_manifest.json`. Top candidate: 1AXC; positive control: 8GLA. Governance: docs/scientific_governance/12_PCNA_SPECIFIC_CHECKS.md, 14_CLAIM_POLICY.md.
- **PCNA cluster `cluster_id_30=1168` is holdout-only.** No PCNA/PCNA-cluster structure may enter train or validation.

---

## Friend Crawl / 40GB Crawl Guidance

Verified repo artifacts describe a PCNA-focused experimental subset: 72 JSONL records,
27 representative PDB/ESM sample pairs, estimated source archive size 5.68 GB, no AlphaFold
structures, and `friend_crawl_homolog_groups.json` marked `not_computed`. The broader
"40GB crawl" is not fully verified by committed metadata in this checkout.

Use policy:
- **Do not use the Friend/40GB crawl for Phase 3 supervised benchmark training.** It is not a governed, labeled, clustered, leakage-audited CryptoBench-equivalent dataset; many records are PCNA or PCNA-associated and must remain holdout-only.
- **Use it for Phase 4 external inference/discovery only after the Phase 3 model is frozen**, with provenance and PCNA isolation preserved.
- **Future pretraining/expansion is possible only after separate governance and human approval**, including deduplication, clustering, benchmark-contamination controls, lifecycle status changes, and an explicit labeling or self-supervision policy.

---

## Next Tasks

1. **[HUMAN — GATE 6] PCNA inference gate.** Separate human decision required before any PCNA prediction is made or interpreted. Read `docs/scientific_governance/12_PCNA_SPECIFIC_CHECKS.md` and `14_CLAIM_POLICY.md` first. Candidates in `data/registries/phase4_candidate_manifest.json`.

2. **[RECOMMENDED] Install external baselines.** fpocket, P2Rank, PocketMiner stubs in `reports/phase3/baseline_runs/`. Required per doc 10 before any superiority claims over state-of-the-art tools. Run on the frozen test split (hash: 24dd5e347d880108) with the same label definition.

3. **[OPTIONAL] Interpret test results.** Test macro-AUPRC = 0.2034 [0.1825, 0.2275]. Micro-AUPRC (0.0973) << macro (0.2034) — investigate whether a few large proteins dominate pooled metrics. Report must not make superiority claims until external baselines complete.

---

## Key Registry Paths

| Registry | Purpose |
|---|---|
| `data/registries/split_manifest_frozen.json` | Frozen split assignments - 1,101 structures |
| `data/labels/label_manifest.json` | Frozen label manifest |
| `data/registries/sequence_cluster_assignments.json` | RCSB 30% identity clusters |
| `data/registries/cross_fold_cluster_risks.json` | Resolved cross-fold risks |
| `data/registries/cryptobench_candidate_cleaned_registry.json` | Remediated candidate list |
| `data/registries/excluded_records.json` | 6 excluded structures with reasons |
| `data/registries/friend_crawl_registry.json` | Friend crawl metadata, 72 JSONL records |
| `data/labels/labels_{apo_pdb_id}.json` | Per-structure label files |
| `data/registries/phase3_input_validation_20260528.json` | Phase 3 frozen-input validation manifest |
| `data/registries/phase3_cif_extraction_manifest_20260528.json` | Governed CIF extraction manifest |
| `data/registries/phase3_dataset_index_20260528.json` | Phase 3 split-aware dataset index |
| `data/registries/phase3_residue_audit_manifest_20260528.json` | Phase 3 residue-label audit manifest |
| `reports/phase3/graph_edge_feature_policy_approval_packet_20260528.md` | Human approval packet for graph policy |
| `reports/phase3/graph_policy_human_decision_20260528.md` | Human decision record approving graph policy |
| `data/graphs/graph_release_manifest_8c22e46f524d5f1d.json` | First graph release — 1,101 structures, PENDING_HUMAN_REVIEW |
| `reports/phase3/graph_release_audit_20260528.md` | Graph release audit report for human review |
| `reports/phase3/handoff_20260528.md` | Session handoff for first graph release |
| `reports/phase3/first_graph_release_approval_20260528.md` | GATE 1 cleared — human approval of first graph release |
| `reports/phase3/model_training_approval_packet_20260528.md` | Model/training plan proposal — PENDING_HUMAN_REVIEW (GATE 2 prerequisite) |

---

## Last Session Summary

Session 2026-05-29 (claude-sonnet-4-6, GATE 4+5): Reshwant approved GATE 4, freezing
`checkpoints/phase3/spatial_only_fold1_seed1_best.pt` (spatial-only, val 0.2047, sequential
edges permanently removed). evaluate_test_set.py written and run once. GATE 5 cleared.
Test results: macro-AUPRC = 0.2034 [0.1825, 0.2275] 95% CI, micro-AUPRC = 0.0973,
macro-AUROC = 0.6902, top-20 recovery = 0.2179. 214 test structures, 177 with valid AUPRC.
One-shot lock written — test set cannot be re-evaluated. Reports:
`reports/phase3/test_evaluation_20260529.md`,
`reports/phase3/test_evaluation_manifest_20260529.json`.
Next: GATE 6 (PCNA inference) requires separate human decision.
External baselines (fpocket/P2Rank/PocketMiner) required before superiority claims.
