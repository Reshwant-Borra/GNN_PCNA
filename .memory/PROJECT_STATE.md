---
updated: 2026-06-12
updated_by: codex-gpt-5 (phase5-human-decisions-resolved-zqz-minus1-opc-policy)
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

**Phase 5 - WAVE 1 PRE-LAUNCH AUDITED. NOT READY FOR MD LAUNCH. PRODUCTION LAUNCH BLOCKED FAIL-CLOSED.**

| System | Status |
|---|---|
| Training (full model) | **COMPLETE**. 12/12 runs. Val macro-AUPRC: **0.1876 ± 0.0113**. |
| Training (spatial-only) | **COMPLETE** (Option B). 12/12 runs. Val macro-AUPRC: **0.1897 ± 0.0091**. Best: fold=1 seed=1 → 0.2047. |
| Baselines | **COMPLETE** (GATE 3). GNN baselines done. External tools (fpocket/P2Rank/PocketMiner): stubs only. |
| Test evaluation | **COMPLETE — ONE-SHOT USED** (GATE 5 cleared 2026-05-29). Test macro-AUPRC: **0.2034** [0.1825, 0.2275] 95% CI. Micro-AUPRC: 0.0973. Macro-AUROC: 0.6902. Top-20 recovery: 0.2179. 214 structures, 177 with valid AUPRC. Lock: `reports/phase3/.test_evaluation_lock`. Report: `reports/phase3/test_evaluation_20260529.md`. |
| Molecular dynamics | **PACKAGE PREPARATION READY / PRODUCTION BLOCKED FAIL-CLOSED.** Human review resolved ZQZ and force-field/water policy on 2026-06-12. Active ligand package is deprotonated ZQZ `-nc -1`; official Wave 1 policy is ff19SB + OPC + Joung-Cheatham OPC-compatible ions. Production remains blocked because `do_not_run_md: true` is still present and no Phase 5 launch authorization exists. No protein system setup, minimization, equilibration, production, trajectories, analysis, interpretation, or claims run. |
| Scientific claims | BLOCKED — external baselines (fpocket/P2Rank/PocketMiner) not yet run; superiority claims require them per doc 10. |
| PCNA inference | **COMPLETE (GATE 6 cleared 2026-05-29)**. 103/103 structures scored. 5 governance reports generated. |
| Graph generation | **FIRST GRAPH RELEASE APPROVED**. 1,101 graphs, 0 failures. Approval: `reports/phase3/first_graph_release_approval_20260528.md`. |
| Split freeze | **FROZEN** - `data/registries/split_manifest_frozen.json` (hash: 24dd5e347d880108) |
| Label freeze | **FROZEN** - `data/labels/label_manifest.json` |

All Phase 2, Phase 3, and Phase 4 gates cleared. Phase 4 inference complete. GATE 7 Wave 1 package exists. The 2026-06-12 human decisions resolved the ZQZ charge-state and force-field/water policy blockers, and follow-up artifacts were completed. MD production remains blocked fail-closed until `do_not_run_md: true` is explicitly superseded by a future launch authorization record. No protein setup, minimization, equilibration, production, trajectory analysis, interpretation, or claims have been run.

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
- **Phase 5 Wave 1 adversarial pre-launch audit handoff documented (2026-06-12):** `reports/phase2/handoff_20260612.md` records the independent audit verdict `NOT READY FOR MD LAUNCH`, launch blockers, revised confidence levels for feasibility estimates, and a Claude Code handoff prompt. Key blockers: ZQZ protonation/net-charge decision missing, `ff19SB + TIP3P` rationale missing, no prepared systems or benchmarks, stale 1AXC pre-registration context, and no MD execution/provenance artifacts. No MD setup, minimization, equilibration, production, trajectory analysis, interpretation, launch authorization, or claims were run.
- **Phase 5 Wave 1 chemistry and force-field/water decision records documented and wired to preflight fail-closed (2026-06-13):** `reports/phase5/zqz_chemistry_decision_20260611.md` and `reports/phase5/force_field_water_policy_decision_20260611.md` document the two open launch blockers. ZQZ structural evidence from SDF connectivity (atoms 28/33/34 and H63) and sqm.in geometry confirms a free side-chain carboxylic acid; current neutral `-nc 0` GAFF2/AM1-BCC package is flagged as not justified for pH 7.4 absent a documented bound-state pKa shift. Force-field/water-model record recommends ff19SB + OPC as the scientific default and treats ff19SB + TIP3P as a documented deviation if explicitly justified. `src/phase5_md/wave1.py` `preflight_status` now adds explicit blockers when either decision record is absent or open; `tests/phase5/test_wave1_preflight.py` adds 2 tests for the new behavior and all 7 tests pass. Registry, reports, and readiness assessment were regenerated; package preparation status is now `READY_FOR_HUMAN_REVIEW` (was `LAUNCH_READY_AWAITING_AUTHORIZATION`) because the chemistry and force-field blockers exceed launch-hold blockers. A project-wide scientific accuracy verification (read-only) was run for Phases 2-5: no critical or governance issues were found on the verified path. No protein setup, minimization, equilibration, production, trajectory analysis, interpretation, launch authorization, or claims were run.
- **Phase 5 human decisions resolved and follow-up artifacts completed (2026-06-12):** `reports/phase5/human_review_decision_package_20260612.md` records approval of deprotonated ZQZ net charge `-1` and ff19SB + OPC + Joung-Cheatham OPC-compatible ions. Generated active replacement ZQZ package at `outputs/phase5_md/official_wave1_20260609/inputs/ligand_params/zqz_minus1/`; audit report `reports/phase5/zqz_minus1_parameter_audit_20260612.md`; neutral `-nc 0` package marked superseded by `outputs/phase5_md/official_wave1_20260609/inputs/ligand_params/zqz/SUPERSEDED_FOR_PRODUCTION_USE.md`. Decision records now have status `APPROVED_HUMAN_REVIEW_RESOLVED`. Manifest templates, registry, readiness report, and fail-closed checks were updated. `pytest tests/phase5/test_wave1_preflight.py -v` passes 8/8. Production preflight fails closed only on `do_not_run_md: true` and absent future launch authorization. No protein setup, minimization, equilibration, production, trajectory generation, trajectory analysis, interpretation, launch authorization, or claims were run.
- **Phase 5 GPU time estimates documented after approved policy (2026-06-12):** `reports/phase5/wave1_gpu_time_estimates_20260612.md` records planning-only runtime estimates for RTX 4070, L4, L40S, A100, H100, H200, and B200-class GPUs under the approved ff19SB + OPC + Joung-Cheatham OPC-compatible ion policy and active ZQZ net-charge `-1` package. Estimates remain inferred until prepared systems and a short benchmark exist. No protein setup, minimization, equilibration, production, trajectory generation, trajectory analysis, interpretation, launch authorization, or claims were run.

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
- **GATE 7 - PACKAGE PREPARATION READY / PRODUCTION BLOCKED FAIL-CLOSED.** Phase 5 official MD Wave 1 package exists: `reports/phase5/official_wave1_execution_package_20260609.md`. Wave 1 targets: 8GLA positive control (118-122) holo/apo-from-holo; 1AXC Tier 1A top-3 (239-243, 28-32, 206-210); 1AXC interface-adjacent control (134-138). Tier 1B (170-174, 175-179, 152-156) deferred to Wave 2. ZQZ protonation/net-charge decision is resolved as deprotonated `-nc -1`; force-field/water policy is resolved as ff19SB + OPC + Joung-Cheatham OPC-compatible ions. Active ZQZ package: `outputs/phase5_md/official_wave1_20260609/inputs/ligand_params/zqz_minus1/`. Production remains fail-closed; exact current blockers are the official package `do_not_run_md: true` hold and absent future explicit Phase 5 launch authorization. No protein system setup, minimization, equilibration, production, trajectory analysis, interpretation, or claims have been run.
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

1. **[PHASE 5 - DO NOT RUN MD UNTIL FUTURE LAUNCH AUTHORIZATION]** Final readiness verdict is `LAUNCH_READY_AWAITING_AUTHORIZATION_PRODUCTION_BLOCKED`. Package-preparation blockers are resolved, but production remains fail-closed because `reports/phase5/official_wave1_execution_package_20260609.md` still records `do_not_run_md: true` and `reports/phase5/phase5_wave1_launch_authorization.md` is absent. Do not start protein system setup, minimization, equilibration, production, trajectory generation, trajectory analysis, interpretation, or claims.

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
| `reports/phase5/wave1_gpu_time_estimates_20260612.md` | Planning-only GPU runtime estimates after approved ZQZ -1 and ff19SB/OPC policy |
| `reports/phase2/handoff_20260612.md` | Phase 5 adversarial pre-launch audit verdict, blockers, and Claude Code handoff prompt |
| `reports/phase2/handoff_20260613.md` | Phase 5 Wave 1 chemistry and force-field/water decision continuation handoff |
| `reports/phase5/zqz_chemistry_decision_20260611.md` | ZQZ protonation/net-charge decision record (RESOLVED — deprotonated `-nc -1`) |
| `reports/phase5/force_field_water_policy_decision_20260611.md` | Force-field/water-model policy decision record (RESOLVED — ff19SB + OPC + Joung-Cheatham OPC-compatible ions) |
| `reports/phase5/human_review_decision_package_20260612.md` | Human review package recording the resolved ZQZ and force-field/water decisions |
| `reports/phase5/zqz_minus1_parameter_audit_20260612.md` | Active ZQZ deprotonated `-nc -1` GAFF2/AM1-BCC audit report |
| `reports/phase5/manifest_provenance_templates_20260610.md` | Phase 5 manifest/provenance template report |
| `data/registries/phase5_wave1_preparation_audit_20260610.json` | Machine-readable Phase 5 Wave 1 audit/preflight registry |
| `outputs/phase5_md/official_wave1_20260609/` | Manifest templates and audited ZQZ ligand parameter package; no protein setup, trajectories, or MD outputs |
| `outputs/phase5_md/official_wave1_20260609/inputs/ligand_params/zqz/PARAMETER_AUDIT.md` | Human-readable ZQZ parameter audit |
| `outputs/phase5_md/official_wave1_20260609/inputs/ligand_params/zqz/SUPERSEDED_FOR_PRODUCTION_USE.md` | Neutral `-nc 0` package supersession marker |
| `outputs/phase5_md/official_wave1_20260609/inputs/ligand_params/zqz_minus1/PARAMETER_AUDIT.md` | Active deprotonated ZQZ `-nc -1` parameter audit |
| `scripts/phase5_zqz_parameterize.py` | Reproducible ZQZ AmberTools26 GAFF2/AM1-BCC parameter generator |
| `src/phase5_md/wave1.py` | Phase 5 audit/preflight implementation |
| `scripts/phase5_wave1_preflight.py` | Phase 5 Wave 1 preflight/report generator |
| `reports/phase4/gate7_md_decision_draft_20260529.md` | GATE 7 MD decision package — evidence packet for authorization |
| `src/phase4_inference/` | Phase 4 inference package (chain_selector, graph_builder, interface_audit, cif_utils) |
| `scripts/phase4_infer.py` | Main Phase 4 inference script |

---

## Last Session Summary

Session 2026-06-12 (codex-gpt-5, Phase 5 GPU time estimates and GitHub publish preparation): Added `reports/phase5/wave1_gpu_time_estimates_20260612.md` with planning-only runtime estimates for RTX 4070, L4, L40S, A100, H100, H200, and B200-class GPUs under the approved ff19SB + OPC + Joung-Cheatham OPC-compatible ion policy and active ZQZ `-nc -1` package. Updated readiness deliverables and project memory. Estimates remain inferred until prepared systems and a short benchmark exist. `do_not_run_md: true` and `launch_authorized: false` remain in force; no protein setup, minimization, equilibration, production, trajectory generation, trajectory analysis, interpretation, launch authorization, or claims were run.

Session 2026-06-12 (codex-gpt-5, Phase 5 human decisions resolved and follow-up artifacts completed): Recorded human approval in `reports/phase5/human_review_decision_package_20260612.md`: ZQZ is deprotonated net charge `-1`; ff19SB + OPC + Joung-Cheatham OPC-compatible ions is the official Wave 1 policy. Updated `reports/phase5/zqz_chemistry_decision_20260611.md` and `reports/phase5/force_field_water_policy_decision_20260611.md` to `APPROVED_HUMAN_REVIEW_RESOLVED`. Generated active ligand-only GAFF2/AM1-BCC package at `outputs/phase5_md/official_wave1_20260609/inputs/ligand_params/zqz_minus1/` with report `reports/phase5/zqz_minus1_parameter_audit_20260612.md`; marked neutral `-nc 0` package superseded for production use. Updated `src/phase5_md/wave1.py`, `scripts/phase5_zqz_parameterize.py`, manifest templates, registry, readiness report, and `tests/phase5/test_wave1_preflight.py`. Verification: `pytest tests/phase5/test_wave1_preflight.py -v` passed 8/8; production preflight fails closed only on `do_not_run_md: true` and missing future launch authorization. No protein system setup, minimization, equilibration, production, trajectory generation, trajectory analysis, interpretation, launch authorization, or claims were run.

Session 2026-06-13 (claude-code-opus-4-7, Phase 5 chemistry and force-field/water decisions and project-wide accuracy verification): Authored `reports/phase5/zqz_chemistry_decision_20260611.md` and `reports/phase5/force_field_water_policy_decision_20260611.md` to record the two open Wave 1 launch blockers. Verified from local SDF connectivity and sqm.in geometry that ZQZ contains a free side-chain carboxylic acid (atoms `C28`, `O33` double-bonded, `O34`-`H63` single-bonded), so the current neutral `-nc 0` GAFF2/AM1-BCC package is not independently justified for pH 7.4 without a documented bound-state pKa shift; recommended `-nc -1` as default. Force-field/water-model decision recommends ff19SB + OPC as default with ff19SB + TIP3P allowed only as a documented deviation. Wired both decisions into `src/phase5_md/wave1.py` `preflight_status` as fail-closed blockers with frontmatter status detection; added 2 new tests; 7/7 tests pass. Regenerated registry and reports. Wave 1 package preparation status is now `READY_FOR_HUMAN_REVIEW` because the decision blockers exceed launch-hold blockers. Ran a project-wide read-only scientific accuracy verification across Phase 2/3/4/5: no critical numeric, methodology, or governance issues were found. Final verdict remains `STILL_NOT_READY_FOR_LAUNCH`; exact remaining blockers are `do_not_run_md: true`, the two open decision records, and absent future explicit human launch authorization. No protein system setup, minimization, equilibration, production, trajectories, trajectory analysis, interpretation, launch authorization, or claims were run.

Session 2026-06-12 (codex-gpt-5, Phase 5 adversarial pre-launch audit handoff): Documented the adversarial Wave 1 pre-launch audit handoff at `reports/phase2/handoff_20260612.md` and updated project memory. Final verdict: `NOT READY FOR MD LAUNCH`. The handoff records verified chain/window facts, questionable ZQZ and force-field/water assumptions, stale 1AXC context, assumption-based feasibility estimates, missing controls, and a Claude Code prompt for continuation. GitHub/main push requested by user; no MD setup, minimization, equilibration, production, trajectories, trajectory analysis, interpretation, launch authorization, or claims were run.

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
