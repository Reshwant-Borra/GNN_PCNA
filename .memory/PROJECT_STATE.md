---
updated: 2026-06-11
updated_by: codex-gpt-5 (phase5-md-feasibility-report)
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

**Phase 5 — OFFICIAL WAVE 1 LAUNCH-READY AWAITING AUTHORIZATION. PRODUCTION LAUNCH BLOCKED FAIL-CLOSED.**

| System | Status |
|---|---|
| Training (full model) | **COMPLETE**. 12/12 runs. Val macro-AUPRC: **0.1876 ± 0.0113**. |
| Training (spatial-only) | **COMPLETE** (Option B). 12/12 runs. Val macro-AUPRC: **0.1897 ± 0.0091**. Best: fold=1 seed=1 → 0.2047. |
| Baselines | **COMPLETE** (GATE 3). GNN baselines done. External tools (fpocket/P2Rank/PocketMiner): stubs only. |
| Test evaluation | **COMPLETE — ONE-SHOT USED** (GATE 5 cleared 2026-05-29). Test macro-AUPRC: **0.2034** [0.1825, 0.2275] 95% CI. Micro-AUPRC: 0.0973. Macro-AUROC: 0.6902. Top-20 recovery: 0.2179. 214 structures, 177 with valid AUPRC. Lock: `reports/phase3/.test_evaluation_lock`. Report: `reports/phase3/test_evaluation_20260529.md`. |
| Molecular dynamics | **LAUNCH-READY AWAITING AUTHORIZATION / PRODUCTION BLOCKED.** Gate 7 Wave 1 authorized; official setup audits/manifests/preflight added 2026-06-10; audited ZQZ GAFF2/AM1-BCC parameter package generated 2026-06-11. No protein system setup, minimization, equilibration, production, trajectories, analysis, interpretation, or claims run. |
| Scientific claims | BLOCKED — external baselines (fpocket/P2Rank/PocketMiner) not yet run; superiority claims require them per doc 10. |
| PCNA inference | **COMPLETE (GATE 6 cleared 2026-05-29)**. 103/103 structures scored. 5 governance reports generated. |
| Graph generation | **FIRST GRAPH RELEASE APPROVED**. 1,101 graphs, 0 failures. Approval: `reports/phase3/first_graph_release_approval_20260528.md`. |
| Split freeze | **FROZEN** - `data/registries/split_manifest_frozen.json` (hash: 24dd5e347d880108) |
| Label freeze | **FROZEN** - `data/labels/label_manifest.json` |

All Phase 2, Phase 3, and Phase 4 gates cleared. Phase 4 inference complete. GATE 7 Wave 1 is authorized. Official Wave 1 preparation audits, audited ZQZ parameters, and fail-closed preflight checks are complete, but MD execution remains on hold until a later explicit launch instruction.

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
- **Phase 5 Wave 1 prelaunch package prepared (2026-06-10):** `src/phase5_md/wave1.py` and `scripts/phase5_wave1_preflight.py` generate/verify official Wave 1 audits, manifest templates, and fail-closed checks. Reports: `reports/phase5/wave1_readiness_report_20260610.md`, `8gla_preparation_audit_20260610.md`, `1axc_preparation_audit_20260610.md`, `zqz_parameterization_plan_20260610.md`, `manifest_provenance_templates_20260610.md`; registry: `data/registries/phase5_wave1_preparation_audit_20260610.json`; templates: `outputs/phase5_md/official_wave1_20260609/`. Key findings: 8GLA assembly 1 uses PCNA chains A/B/C and excludes deposited chain D; 8GLA chain C is missing residue 122 in PC-118; 1AXC retains PCNA A/C/E and removes p21 B/D/F; 1AXC Wave 1 windows are complete on A/C/E. No MD was run.
- **Phase 5 ZQZ parameterization complete (2026-06-11):** AmberTools26 (`dacase::ambertools-dac=26.0.0`) generated audited GAFF2/AM1-BCC ZQZ parameters from the RCSB ideal SDF with explicit hydrogens, net charge 0, residue name ZQZ. Artifacts: `outputs/phase5_md/official_wave1_20260609/inputs/ligand_params/zqz/` including `zqz_gaff2_am1bcc.mol2`, `zqz_gaff2.frcmod`, `zqz_tleap.in`, `zqz_tleap.log`, `PARAMETER_AUDIT.md`, `zqz_parameter_audit.json`, and `zqz_package_hashes.json`; report: `reports/phase5/zqz_parameter_audit_20260611.md`; generator: `scripts/phase5_zqz_parameterize.py`. `tleap` check passed with Unit OK, errors 0, warnings 0. No protein setup, minimization, equilibration, production, analysis, interpretation, launch authorization, or claims were run.
- **Phase 5 Wave 1 MD execution feasibility documented (2026-06-11):** `reports/phase5/wave1_md_execution_feasibility_20260611.md` records the final execution feasibility assessment. Totals: 9 production simulations and 900 ns aggregate production MD. Recommendation: L40S is the preferred future execution platform after explicit launch authorization; local RTX 4070 workstation is not recommended for full Wave 1 because of 12 GB VRAM uncertainty and only about 52 GB free on C:. Production remains blocked fail-closed; no MD setup, minimization, equilibration, production, trajectory analysis, interpretation, launch authorization, or claims were run.

---

## Current Blockers

No Phase 2 blockers remain.

Phase 3 stop gates:
- **GATE 1 — CLEARED.** First graph release approved: `reports/phase3/first_graph_release_approval_20260528.md`.
- **GATE 2 — CLEARED.** First training sign-off: `reports/phase3/first_training_signoff_20260528.md`.
- **GATE 3 — CLEARED.** Baseline runs authorized by Reshwant on 2026-05-28. All GNN baselines complete 2026-05-29.
- **GATE 4 — CLEARED.** Model frozen 2026-05-29. Checkpoint: `checkpoints/phase3/spatial_only_fold1_seed1_best.pt`. Record: `reports/phase3/model_freeze_gate4_20260529.md`.
- **GATE 5 — CLEARED.** Test evaluation complete 2026-05-29. Macro-AUPRC: **0.2034** [0.1825, 0.2275]. Report: `reports/phase3/test_evaluation_20260529.md`. Test set one-shot used — cannot be re-run.
- **GATE 6 — CLEARED.** PCNA inference complete 2026-05-29. 103/103 structures OK (RTX 4070, 62s). Positive control sanity check passed (IDCL/AOH1996 region ranks #1, score=0.93). Authorization: `reports/phase4/gate6_authorization_20260529.md`. All 5 governance artifacts written to `reports/phase4/`.
- **GATE 7 — AUTHORIZED / LAUNCH-READY AWAITING AUTHORIZATION / PRODUCTION BLOCKED.** Phase 5 official MD Wave 1 authorized by Reshwant-Borra on 2026-06-09: `reports/phase4/gate7_authorization_20260609.md`. Official pre-execution package: `reports/phase5/official_wave1_execution_package_20260609.md`. Wave 1 targets: 8GLA positive control (118-122) holo/apo-from-holo; 1AXC Tier 1A top-3 (239-243, 28-32, 206-210); 1AXC interface-adjacent control (134-138). Tier 1B (170-174, 175-179, 152-156) deferred to Wave 2 (enhanced sampling required). Prelaunch reports/manifests generated 2026-06-10; audited ZQZ parameter package generated 2026-06-11. Production remains fail-closed until explicit launch authorization exists and `do_not_run_md: true` is intentionally changed by that future authorization. No protein system setup, minimization, equilibration, production, trajectory analysis, interpretation, or claims have been run.
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

1. **[PHASE 5 - WAIT FOR EXPLICIT LAUNCH AUTHORIZATION, DO NOT RUN MD YET]** Official Wave 1 is launch-ready at the preparation level. Production preflight is intentionally blocked only by `do_not_run_md: true` and absent future launch authorization. Next allowed major step is explicit human launch authorization that updates the launch hold; do not start protein system setup, minimization, equilibration, production, trajectory analysis, interpretation, or claims until that later explicit launch instruction.

2. **[RECOMMENDED] Install external baselines.** fpocket, P2Rank, PocketMiner stubs in `reports/phase3/baseline_runs/`. Required per doc 10 before any superiority claims over state-of-the-art tools. Run on the frozen test split (hash: 24dd5e347d880108) with the same label definition.

3. **[OPTIONAL] Interpret Phase 4 results.** Full per-residue scores in `reports/phase4/phase4_inference_results_20260529.json`. Interface overlap analysis in `phase4_interface_overlap_20260529.md`. The trimer_interface region (170-179, 152-156) scores very highly — consistent with known clamp geometry. Do not make druggability claims.

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
| `data/graphs/graph_release_manifest_8c22e46f524d5f1d.json` | First graph release — 1,101 structures, APPROVED |
| `reports/phase3/first_graph_release_approval_20260528.md` | GATE 1 cleared — human approval of first graph release |
| `reports/phase3/model_freeze_gate4_20260529.md` | GATE 4 cleared — frozen checkpoint: `spatial_only_fold1_seed1_best.pt` |
| `reports/phase3/test_evaluation_20260529.md` | GATE 5 cleared — FINAL test results (one-shot used) |
| `reports/phase3/.test_evaluation_lock` | One-shot guard — test set cannot be re-evaluated |
| `data/registries/phase4_candidate_manifest.json` | 54 ranked PCNA inference candidates (GATE 6 input) |
| `C:\Users\reshw\phase4_pcna_crawl\` | 103 PCNA/sliding-clamp mmCIF structures (primary inference dataset) |
| `reports/phase4/gate6_authorization_20260529.md` | GATE 6 cleared — Phase 4 inference authorization |
| `reports/phase4/phase4_inference_results_20260529.json` | Per-residue scores, all 103 structures |
| `reports/phase4/phase4_candidate_report_20260529.md` | Ranked candidate regions (human PCNA) |
| `reports/phase4/phase4_pcna_audit_20260529.md` | PCNA-specific governance audit |
| `reports/phase4/phase4_interface_overlap_20260529.md` | Interface overlap analysis |
| `reports/phase4/phase4_candidate_prioritization_20260529.md` | Tier 1A/1B/2/3 MD candidate list (reclassified 2026-05-29) |
| `reports/phase4/gate7_authorization_20260609.md` | GATE 7 Wave 1 authorization — execution still on hold |
| `reports/phase5/official_wave1_execution_package_20260609.md` | Official Wave 1 pre-execution package — do not run MD yet |
| `reports/phase5/wave1_readiness_report_20260610.md` | Phase 5 Wave 1 readiness/gap/launch assessment — launch-ready awaiting authorization, production blocked fail-closed |
| `reports/phase5/8gla_preparation_audit_20260610.md` | 8GLA assembly/chain/ZQZ/missing-residue preparation audit |
| `reports/phase5/1axc_preparation_audit_20260610.md` | 1AXC PCNA/p21/window preparation audit |
| `reports/phase5/zqz_parameterization_plan_20260610.md` | ZQZ GAFF2/AM1-BCC parameterization plan — completed by audited package |
| `reports/phase5/zqz_parameter_audit_20260611.md` | ZQZ GAFF2/AM1-BCC audited parameter report |
| `reports/phase5/wave1_md_execution_feasibility_20260611.md` | Final Wave 1 MD execution feasibility assessment; no MD authorization or execution |
| `reports/phase5/manifest_provenance_templates_20260610.md` | Phase 5 manifest/provenance template report |
| `data/registries/phase5_wave1_preparation_audit_20260610.json` | Machine-readable Phase 5 Wave 1 audit/preflight registry |
| `outputs/phase5_md/official_wave1_20260609/` | Manifest templates and audited ZQZ ligand parameter package; no protein setup, trajectories, or MD outputs |
| `outputs/phase5_md/official_wave1_20260609/inputs/ligand_params/zqz/PARAMETER_AUDIT.md` | Human-readable ZQZ parameter audit |
| `scripts/phase5_zqz_parameterize.py` | Reproducible ZQZ AmberTools26 GAFF2/AM1-BCC parameter generator |
| `src/phase5_md/wave1.py` | Phase 5 audit/preflight implementation |
| `scripts/phase5_wave1_preflight.py` | Phase 5 Wave 1 preflight/report generator |
| `reports/phase4/gate7_md_decision_draft_20260529.md` | GATE 7 MD decision package — evidence packet for authorization |
| `src/phase4_inference/` | Phase 4 inference package (chain_selector, graph_builder, interface_audit, cif_utils) |
| `scripts/phase4_infer.py` | Main Phase 4 inference script |

---

## Last Session Summary

Session 2026-06-11 (codex-gpt-5, Phase 5 MD feasibility documentation): Documented the final Wave 1 MD execution feasibility assessment at `reports/phase5/wave1_md_execution_feasibility_20260611.md` and updated project memory. Verified official Wave 1 totals: 3 systems x 3 replicates x 100 ns = 9 production simulations and 900 ns aggregate production MD. Checked local system: Alienware Aurora R16, Intel i7-14700F, ~31.7 GiB RAM, RTX 4070 with 12,282 MiB VRAM, NVIDIA driver 581.95/CUDA 13.0, and ~52.4 GiB free on C:. The report recommends L40S as the preferred future execution platform after explicit launch authorization, lists pricing under lowest-public, RunPod/Lambda-style, and major-cloud bases, and preserves production status as `BLOCKED_FAIL_CLOSED`. No protein setup, minimization, equilibration, production, trajectories, trajectory analysis, interpretation, launch authorization, or claims were run.

Session 2026-06-11 (codex-gpt-5, Phase 5 ZQZ parameter audit): Completed the final pre-MD ZQZ parameter task without launching MD. Installed/used AmberTools26 in WSL via `dacase::ambertools-dac=26.0.0`; added `scripts/phase5_zqz_parameterize.py`; generated audited GAFF2/AM1-BCC ZQZ ligand parameters under `outputs/phase5_md/official_wave1_20260609/inputs/ligand_params/zqz/`; wrote `reports/phase5/zqz_parameter_audit_20260611.md`; updated `reports/phase5/wave1_readiness_report_20260610.md`, `reports/phase5/zqz_parameterization_plan_20260610.md`, `data/registries/phase5_wave1_preparation_audit_20260610.json`, `src/phase5_md/wave1.py`, and `tests/phase5/test_wave1_preflight.py`. Production preflight now fails closed only because the official package records `do_not_run_md: true` and future explicit launch authorization is absent. Tests: `pytest tests/phase5/test_wave1_preflight.py` passed (5/5). Production preflight intentionally exits nonzero. No protein system setup, minimization, equilibration, production, trajectories, trajectory analysis, interpretation, launch authorization, or claims were run.

Session 2026-06-09 (codex-gpt-5, Gate 7 Wave 1 authorization package): Reshwant-Borra approved official Phase 5 MD Wave 1 based on `reports/phase4/gate7_md_decision_draft_20260529.md` and binding governance requirements. Created formal authorization record `reports/phase4/gate7_authorization_20260609.md` (decision_id: `phase5_gate7_wave1_authorization_20260609`) and official pre-execution package `reports/phase5/official_wave1_execution_package_20260609.md`. Scope: 8GLA holo with ZQZ, 8GLA apo-from-holo, and 1AXC apo-from-p21 for windows 239-243, 28-32, 206-210, and 134-138; Tier 1B remains deferred to Wave 2. The package explicitly excludes the time-crunch workflow and records `do_not_run_md: true`. No MD setup, ligand parameterization, production run, trajectory generation, analysis, interpretation, or claims were run.

Session 2026-05-29 (claude-sonnet-4-6, Phase 4 finalization + GATE 7 draft): Finalized Phase 4
interpretation artifacts. (1) Reclassified the candidate prioritization report: original Tier 1
incorrectly grouped trimer-interface candidates with no-overlap novel candidates. Corrected to
Tier 1A (15 novel, no interface), Tier 1B (8 trimer-interface, deferred Wave 2), Tier 2 (1
IDCL-adjacent), Tier 3 (6 positive control). No scores or residue ranges changed. (2) Drafted
full GATE 7 MD Validation Decision Package at `reports/phase4/gate7_md_decision_draft_20260529.md`:
per-candidate pre-registrations (doc-13 compliant), explicit Tier 1B include/exclude justification,
MD target selection rationale, candidate-to-PDB mapping table, governance compliance checklist.
Tier 1B (170-174 at 0.92, highest-scoring non-positive-control) explicitly deferred to Wave 2 —
not excluded. Wave 1: 5 candidates (118-122 positive control, 239-243/28-32/206-210 Tier 1A,
134-138 Tier 2 control). Primary PDB: 1AXC. GATE 7 awaits human decision.
