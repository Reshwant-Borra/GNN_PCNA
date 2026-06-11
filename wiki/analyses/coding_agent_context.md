---
type: analysis
status: active
created: 2026-05-27
updated: 2026-05-27
tags: [codex, startup, phase2, governance]
aliases: [Coding Agent Context]
confidence: high
evidence_status: verified
---

# Coding Agent Context

## 1. Project goal

Build a fresh governed Phase 2 GNN-PCNA workflow for residue-level PCNA candidate cryptic/allosteric/pocket-like region prediction and auditing.

## 2. What Phase 2 means

Phase 2 means governance-first rebuild, not V1 continuation. Data, labels, splits, graphs, baselines, MD, and claims must pass documented gates.

## 3. What V1 mistakes must not repeat

Leakage, stale artifacts, overclaims, weak provenance, hallucinated assumptions, weak biological realism, MD overinterpretation, and coding agents inventing science.

## 4. What files define scientific law

`docs/scientific_governance/` defines binding rules. Start with `00_README.md`, `16_CODING_AGENT_RULES.md`, and `37_PHASE2_IMPLEMENTATION_PLAN.md`.

## 5. How to use the wiki

Read `wiki/index.md`, then relevant entity/concept/analysis pages. Use the wiki as a memory map, not final evidence.

## 6. How to use crawls/

Use `crawls/` as raw evidence and source leads. Follow [[Crawl Map]] to targeted paths. Do not treat crawl summaries as verified truth.

## 7. How to use V1

Historical reference only. Audit any V1 component before reuse. Do not copy V1 artifacts into Phase 2.

## 8. What cannot be invented

Biology, labels, split rules, graph science, model methodology, MD interpretation, claim language, or missing assumptions.

## 9. What must exist before training

Dataset registry, lifecycle registry, split audit, label freeze, graph audit, provenance manifests, red-team audit, null-baseline plan, human gates, and readiness gate.

## 10. What must exist before claims

Evaluation, baselines, biological realism audit, PCNA-specific audit, interpretability audit, uncertainty register, provenance, claim audit, and human review.

## 11. What must exist before MD interpretation

Pre-MD reality check, pre-registered question, setup provenance, comparison policy, and allowed positive/negative claim language.

## 12. Allowed claim language

Use cautious computational structural biology language: "candidate region", "hypothesis-generating", "consistent with", "requires follow-up", "exploratory".

## 13. Forbidden claim language

Do not say validated target, therapeutic target, clinically actionable, confirmed mechanism, drug discovery success, treatment relevance, or MD validated binding.

## 14. Required gates

Follow `21_READINESS_GATE.md`, `26_HUMAN_REVIEW_GATES.md`, and `19_STOP_CONDITIONS.md`.

## 15. What to do when uncertain

Stop if uncertainty is scientific. Record the gap in [[Open Questions]] and, when relevant, update the governance-linked context.

## 16. How to update wiki memory

Follow [[Wiki Update Rules]]. Log decisions in [[Log]] and update relevant entity/concept pages with source path, confidence, date, and evidence status.

## 17. Current Phase 2 foundation status

Data-foundation scaffolding exists under `reports/phase2/`, `data/registries/`, `data/splits/`, `data/labels/`, and `docs/scientific_governance/DATASET_REGISTRY.md`.

Use `python scripts/phase2_foundation_check.py` to verify scaffold completeness. Current readiness is dataset planning only; training remains blocked.

## 18. Dataset investigation status

Dataset Investigation + Freeze phase has started, but no dataset is frozen. Local `data/` contains templates and registries only; no canonical CryptoBench, BioLiP/BioLiP2, scPDB, PDBbind, ASD, or PocketMiner-related structure/label files are adopted. CryptoBench is the leading primary benchmark candidate, but local file inventory, hashes, license resolution, schema audit, PCNA/homolog contamination checks, split audit, and human dataset/split/label review are still required.

## 19. Local dataset discovery status

As of 2026-05-27, local discovery found no usable dataset archives, coordinate files, CSV/TSV/Parquet registries, residue labels, split assignments, or processed dataset artifacts under `crawls/`, `raw/`, or `data/`. `raw/` is placeholder-only. `data/` is governance scaffolding only. Crawl hits for CryptoBench, PocketMiner, BioLiP/BioLiP2, scPDB, ASD, and PDBbind are acquisition leads, not local datasets.

## 20. Dataset intake agent implementation status

As of 2026-05-27, governed dataset/source intake infrastructure exists under `scripts/dataset_intake.py`, `scripts/validate_dataset_intake.py`, and `src/phase2_intake/`. The agent supports dry-run discovery, source adapters, quarantined `data/raw_intake/<source_name>/` paths, append-only `data/registries/download_manifest.jsonl`, inventory generation, report generation, SHA-256 hashing for completed downloads, explicit license/schema/trust statuses, and stop gates for single files over 500 MB or source totals over 20 GB. Dry-run checks were run for CryptoBench and targeted PCNA structures `8GLA`/`1W60`; no raw files were downloaded, and no dataset was adopted.

## 21. Current raw intake status

As of 2026-05-27, official small CryptoBench OSF/GitHub metadata, nested OSF file listings, MIT license metadata, under-500 MB CryptoBench JSON/code/model-support files, and targeted RCSB PCNA files for `8GLA` and `1W60` have been downloaded under `data/raw_intake/` with manifest rows and SHA-256 hashes. The files remain `raw_unverified` and `not_adopted`. The CryptoBench `cif-files.zip` archive is about 1.145 GB and was correctly skipped with `HUMAN_APPROVAL_REQUIRED_FOR_BULK_DOWNLOAD`; approval is required before downloading that archive. Training, graph generation, split freeze, label freeze, MD, evaluation, and claims remain blocked.

## 22. CryptoBench bulk archive status

As of 2026-05-27, the user approved the official OSF CryptoBench `cif-files.zip` bulk download. The archive was downloaded to `data/raw_intake/cryptobench/files/672a0171eae0bff252ba9ea3_cif-files.zip`, kept quarantined, and recorded in the download manifest with SHA-256 `8d15f897bfdfdf61c7d97a29f5f6ca2c5e03d73d8fb89be7da5bbc245cf56ae4`. The schema-first audit at `reports/phase2/cryptobench_schema_first_audit.md` inspected JSON top-level structure and ZIP inventory only; the archive opens safely with Python `zipfile` and contains 5,005 `.cif` files. CryptoBench is ready for formal schema audit, not training.

## 23. CryptoBench deep audit status

As of 2026-05-27, the full local CryptoBench audit artifacts exist at `reports/phase2/cryptobench_schema_deep_audit.md`, `reports/phase2/cryptobench_split_risk_audit.md`, `reports/phase2/cryptobench_label_semantics.md`, `reports/phase2/cryptobench_structure_inventory.md`, `reports/phase2/pcna_contamination_screen.md`, and `data/registries/cryptobench_*summary/index.json`. Key findings: `dataset.json` has 1,107 apo keys and 5,493 apo-holo cryptic records; all 5,005 cryptic referenced CIFs are present/readable; `noncryptic-pockets.json` references 6,915 structures missing from the local ZIP; labels are pocket-selection residue tokens, not explicit true negatives; fold files match `folds.json` by apo ID but lack sequence/homolog proof and have 6 repeated holo PDB IDs across folds; exact human PCNA contamination exists in the test fold via apo `5e0v`, holo `3vkx`, UniProt `P12004`; 721 selected residue tokens are absent from parsed atom-site residue IDs. CryptoBench remains `not_adopted`; graph generation, split freeze, label freeze, training, MD, evaluation, and claims remain blocked.

## 24. Track A/B remediation packet status

As of 2026-05-27, Track A/B planning artifacts exist. The explicit CryptoBench adoption recommendation is `cryptic_only_benchmark_candidate_with_exclusions_and_split_redesign`, not full adoption. PCNA policy requires full isolation from model development, with `5e0v`/`3vkx`/`P12004` held out or excluded and sliding-clamp text hits requiring homolog/structure review. Potential homolog risk registry records 6 repeated holo PDB IDs across folds and unresolved sequence clustering. Residue mapping failure registry records 721 failures: 420 label-seq/auth-seq mismatches, 297 absent atom-site residue tokens, and 4 tokens on another chain. The candidate cleaned registry marks 158 cryptic records as exclusion/review-required and 1 PCNA holdout. Auxiliary intake linked BioLiP/Q-BioLiP, scPDB, ASD, BioGRID, and STRING; downloaded PocketMiner GitHub metadata, fpocket/P2Rank GitHub metadata, and targeted AlphaFold `P12004` metadata. PDBbind is classified as excluded from primary Phase 2 benchmark use. Claude Code handoff is `reports/phase2/phase2_claude_code_handoff.md`.

## Provenance

- Source paths: `AGENTS.md`, `docs/scientific_governance/00_README.md`, `16_CODING_AGENT_RULES.md`, `37_PHASE2_IMPLEMENTATION_PLAN.md`, `reports/phase2/readiness_gate.md`, `reports/phase2/dataset_investigation_report.md`, `reports/phase2/proposed_split_strategy.md`, `reports/phase2/proposed_label_strategy.md`, `reports/phase2/local_dataset_discovery_report.md`, `docs/dataset_intake_crawler_prompt.md`, `scripts/dataset_intake.py`, `scripts/validate_dataset_intake.py`, `scripts/cryptobench_schema_first_audit.py`, `scripts/cryptobench_deep_audit.py`, `scripts/phase2_remediation_packet.py`, `src/phase2_intake/`, `data/registries/download_manifest.jsonl`, `data/registries/dataset_inventory.json`, `data/registries/bulk_download_approvals.json`, `data/registries/cryptobench_schema_summary.json`, `data/registries/cryptobench_fold_summary.json`, `data/registries/cryptobench_structure_index.json`, `data/registries/potential_homolog_risks.json`, `data/registries/residue_mapping_failures.json`, `data/registries/cryptobench_candidate_cleaned_registry.json`, `data/registries/auxiliary_dataset_role_summary.json`, `data/raw_intake/cryptobench/`, `data/raw_intake/pcna_structures/`, `data/raw_intake/pocketminer/`, `data/raw_intake/baseline_tools/`, `data/raw_intake/alphafold/`, `reports/phase2/friend_dataset_acquisition_report.md`, `reports/phase2/cryptobench_schema_first_audit.md`, `reports/phase2/cryptobench_schema_deep_audit.md`, `reports/phase2/cryptobench_split_risk_audit.md`, `reports/phase2/cryptobench_label_semantics.md`, `reports/phase2/cryptobench_structure_inventory.md`, `reports/phase2/pcna_contamination_screen.md`, `reports/phase2/cryptobench_adoption_decision.md`, `reports/phase2/pcna_isolation_policy.md`, `reports/phase2/cryptobench_leakage_remediation.md`, `reports/phase2/label_supervision_risks.md`, `reports/phase2/proposed_label_policy.md`, `reports/phase2/residue_mapping_failure_analysis.md`, `reports/phase2/proposed_phase2_split_strategy.md`, `reports/phase2/cryptobench_candidate_cleaned_registry.md`, `reports/phase2/auxiliary_dataset_audit.md`, `reports/phase2/benchmark_role_classification.md`, `reports/phase2/auxiliary_acquisition_status_summary.md`, `reports/phase2/dataset_footprint_summary.md`, `reports/phase2/phase2_claude_code_handoff.md`
- Confidence level: high
- Date last updated: 2026-05-27

## 25. Phase 2 completion and Phase 3 handoff correction

As of 2026-05-28, Phase 2 is complete: split and label manifests are frozen and
human-approved. The frozen split manifest is `data/registries/split_manifest_frozen.json`
with hash `24dd5e347d880108`; labels are in `data/labels/labels_{apo_pdb_id}.json`.

Local repo inspection found no `src/phase3_model/`, `src/phase3_training/`,
`src/phase3_evaluation/`, `src/baselines/`, `tests/phase3/`, or `reports/phase3/` in this
checkout. Treat Friend's full Phase 3 framework as reported but unverified until the branch
or files are inspected directly. Friend's Phase 2 crawl metadata artifacts are present and
verified.

The Friend/40GB crawl must not be used for Phase 3 supervised benchmark training. Frozen
CryptoBench remains the authoritative v2 supervised training/evaluation dataset. The crawl
is suitable for Phase 4 external inference/discovery after model freeze, and possibly future
pretraining/expansion only after a separate governed pipeline with deduplication, clustering,
benchmark-contamination checks, lifecycle changes, labeling or self-supervision policy, and
human approval.

Provenance:
- date: 2026-05-28
- source: `.memory/PROJECT_STATE.md`, `COLLABORATION.md`, `reports/phase2/handoff_20260528.md`, `reports/phase2/friend_crawl_stats.md`, `data/registries/friend_crawl_registry.json`
- governance: `docs/scientific_governance/04_DATASET_CONSTRAINTS.md`, `05_SPLIT_PROTOCOL.md`, `06_LABELING_RULES.md`, `07_PREPROCESSING_AND_GRAPH_RULES.md`, `16_CODING_AGENT_RULES.md`, `26_HUMAN_REVIEW_GATES.md`, `31_DATA_LIFECYCLE_TRACKING.md`
- confidence: high for local repo state; medium for off-repo Friend framework status
- evidence_status: verified for local files; inferred for crawl role recommendation

## 26. Phase 3 governed data pipeline rebuild status

As of 2026-05-28, Codex rebuilt the local Phase 3 framework skeleton because Friend's
reported Phase 3 code was not present in this checkout. The new implementation is scoped to
governed data preparation and fail-closed scaffolding:

- `src/phase3_data/` reads frozen split/label/exclusion/cluster manifests, validates
  frozen counts and hashes, rejects original `folds.json`, rejects Friend crawl paths for
  supervised Phase 3, extracts/verifies the approved CryptoBench CIF zip, builds split-aware
  dataset indexes, and audits residue-label alignment.
- `src/phase3_training/` is dry-run-only and refuses real training without human pipeline
  sign-off. Even with future sign-off, real training is not implemented in this skeleton.
- `src/phase3_model/`, `src/phase3_evaluation/`, and `src/baselines/` are interfaces/stubs
  only. No model science, baselines, metrics, or claims were implemented.
- `tests/phase3/` plus the existing Phase 2 intake tests pass: `16 passed`.

Generated artifacts:

- `data/registries/phase3_input_validation_20260528.json` - PASS, CIF status READY.
- `data/registries/phase3_cif_extraction_manifest_20260528.json` - PASS, approved zip hash
  `8d15f897bfdfdf61c7d97a29f5f6ca2c5e03d73d8fb89be7da5bbc245cf56ae4`, 5,005 CIF files.
- `data/registries/phase3_dataset_index_20260528.json` - PASS, 1,101 non-excluded entries,
  no PCNA cluster `1168` entries.
- `data/registries/phase3_residue_audit_manifest_20260528.json` - PASS, 1,101 structures
  audited, 371,651 residue nodes, 16,335 positives aligned, 3,696 masked labels on nodes,
  8 masked labels without nodes, 351,620 PU/background residues, 4,380 residues with altlocs,
  and 22 residues without CA.
- `reports/phase3/phase3_framework_rebuild_20260528.md` - human-readable report and
  provenance packet.

Remaining gates: edge definition, atom basis, cutoff, feature policy, graph tensor format,
coordinate altloc policy, missing-residue sequence-edge policy, and train-only normalization
policy are not approved. Graph tensor generation and real training remain blocked until
human review/sign-off.

Provenance:
- date: 2026-05-28
- source: `reports/phase3/phase3_framework_rebuild_20260528.md`, `data/registries/phase3_input_validation_20260528.json`, `data/registries/phase3_cif_extraction_manifest_20260528.json`, `data/registries/phase3_dataset_index_20260528.json`, `data/registries/phase3_residue_audit_manifest_20260528.json`
- governance: `docs/scientific_governance/04_DATASET_CONSTRAINTS.md`, `05_SPLIT_PROTOCOL.md`, `06_LABELING_RULES.md`, `07_PREPROCESSING_AND_GRAPH_RULES.md`, `08_MODEL_ARCHITECTURE_CONSTRAINTS.md`, `09_EVALUATION_PROTOCOL.md`, `10_BASELINE_REQUIREMENTS.md`, `15_PROVENANCE_AND_REPRODUCIBILITY.md`, `16_CODING_AGENT_RULES.md`, `19_STOP_CONDITIONS.md`, `26_HUMAN_REVIEW_GATES.md`
- confidence: high for local artifacts and tests
- evidence_status: verified

## 27. Phase 3 graph policy approval packet status

As of 2026-05-28, `reports/phase3/graph_edge_feature_policy_approval_packet_20260528.md`
has been approved by human decision record
`reports/phase3/graph_policy_human_decision_20260528.md`. It reviews the Phase 3
data/residue audit artifacts and approves the first graph-generation node, edge,
coordinate/altloc, feature, and graph-manifest policy.

The packet proposes a conservative initial policy for review:

- one node per audited target-chain protein residue, including polymer-positioned modified
  residues;
- CA-CA undirected spatial edges at 8.0 Angstrom and sequential same-chain edges that do not
  bridge missing-residue gaps;
- highest-occupancy CA altloc selection with deterministic tie-breaks;
- residue identity plus limited binary flags as trainable node features;
- chain ID, residue number, fold, cluster, label counts, split, and PCNA flags as metadata
  only, not trainable features;
- no ESM/protein-language-model features in the first graph release.

This policy is approved for graph-generation implementation only. No `data/graphs` or
Phase 3 graph output directory existed at approval-record creation, and no graph tensors or
training outputs were generated by the approval-record step. Training, baselines,
evaluation claims, PCNA prediction interpretation, MD interpretation, and scientific claims
remain blocked. The first graph release still requires human review before real training.

Provenance:
- date: 2026-05-28
- source: `reports/phase3/graph_edge_feature_policy_approval_packet_20260528.md`, `reports/phase3/graph_policy_human_decision_20260528.md`, `reports/phase3/phase3_framework_rebuild_20260528.md`, `data/registries/phase3_dataset_index_20260528.json`, `data/registries/phase3_residue_audit_manifest_20260528.json`
- governance: `docs/scientific_governance/04_DATASET_CONSTRAINTS.md`, `05_SPLIT_PROTOCOL.md`, `06_LABELING_RULES.md`, `07_PREPROCESSING_AND_GRAPH_RULES.md`, `08_MODEL_ARCHITECTURE_CONSTRAINTS.md`, `15_PROVENANCE_AND_REPRODUCIBILITY.md`, `19_STOP_CONDITIONS.md`, `26_HUMAN_REVIEW_GATES.md`
- confidence: high for packet creation, local artifact status, and recorded approval
- evidence_status: verified for local artifacts and human graph-policy decision record

## 28. Gate 7 Wave 1 authorization and official MD package status

As of 2026-06-09, Reshwant-Borra approved official Phase 5 MD Wave 1 based on
`reports/phase4/gate7_md_decision_draft_20260529.md` and binding governance. The formal
authorization record is `reports/phase4/gate7_authorization_20260609.md`; the official
pre-execution package is `reports/phase5/official_wave1_execution_package_20260609.md`.

Scope: 8GLA holo with ZQZ, 8GLA apo-from-holo, and 1AXC apo-from-p21 for windows
239-243, 28-32, 206-210, and 134-138. Tier 1B trimer-interface candidates remain
deferred to Wave 2 and require a separate enhanced-sampling pre-registration and human
authorization.

Execution status: authorization and package only. Do not run MD yet. No setup,
ligand parameterization, minimization, equilibration, production, trajectory analysis,
interpretation, or claims have been run. Next implementation task is official Wave 1
setup/preflight work: 8GLA biological assembly mapping, 1AXC apo-from-p21 preparation
policy, ZQZ ligand parameterization workflow, setup manifests, and stop-condition checks.

Provenance:
- date: 2026-06-09
- source: `reports/phase4/gate7_authorization_20260609.md`, `reports/phase5/official_wave1_execution_package_20260609.md`, `reports/phase4/gate7_md_decision_draft_20260529.md`
- governance: `docs/scientific_governance/12_PCNA_SPECIFIC_CHECKS.md`, `13_MD_VALIDATION_RULES.md`, `14_CLAIM_POLICY.md`, `15_PROVENANCE_AND_REPRODUCIBILITY.md`, `26_HUMAN_REVIEW_GATES.md`
- confidence: high for authorization and execution-package scope
- evidence_status: verified for local artifacts; no MD outcome evidence exists

## 29. Phase 5 Wave 1 prelaunch audit and fail-closed setup status

As of 2026-06-10, official Phase 5 Wave 1 setup infrastructure is prepared for human
review but production launch is blocked fail-closed. Codex added `src/phase5_md/wave1.py`
and `scripts/phase5_wave1_preflight.py` to regenerate preparation audits, manifests, and
preflight status. Focused tests are in `tests/phase5/test_wave1_preflight.py`.

Generated artifacts:

- `reports/phase5/wave1_readiness_report_20260610.md`
- `reports/phase5/8gla_preparation_audit_20260610.md`
- `reports/phase5/1axc_preparation_audit_20260610.md`
- `reports/phase5/zqz_parameterization_plan_20260610.md`
- `reports/phase5/manifest_provenance_templates_20260610.md`
- `data/registries/phase5_wave1_preparation_audit_20260610.json`
- `outputs/phase5_md/official_wave1_20260609/` manifest templates

Key verified setup facts:

- 8GLA official Wave 1 assembly is RCSB biological assembly 1, PCNA auth chains A/B/C.
  Deposited chain D is excluded because it belongs to assembly 2. 8GLA chain C is missing
  residue 122 in PC-118; chains A/B have 118-122 complete.
- ZQZ is formal charge 0 in the RCSB ligand record and appears as six Assembly 1
  instances assigned to chains A/B in deposited coordinates. Production remains blocked
  until audited GAFF2/AM1-BCC parameters exist.
- 1AXC biological assembly 1 is PCNA trimer A/C/E plus p21 peptide chains B/D/F. The
  apo-from-p21 setup must remove B/D/F and record that transformation. Wave 1 windows
  239-243, 28-32, 206-210, and 134-138 are complete on A/C/E.

Current fail-closed blockers:

- `reports/phase5/official_wave1_execution_package_20260609.md` still records
  `do_not_run_md: true`.
- `outputs/phase5_md/official_wave1_20260609/inputs/ligand_params/zqz/PARAMETER_AUDIT.md`
  is absent by design.
- Future explicit launch authorization `reports/phase5/phase5_wave1_launch_authorization.md`
  is absent.

Verification run:

- `pytest tests/phase5/test_wave1_preflight.py` -> 4 passed.
- `python scripts/phase5_wave1_preflight.py --preflight-stage production` -> fail-closed
  with the blockers above.

Provenance:
- date: 2026-06-10
- source: reports and registry paths listed above; `data/raw_intake/pcna_structures/8GLA.cif`;
  `data/raw_intake/pcna_structures/1AXC.cif`; RCSB ligand page for ZQZ formal charge;
  AmberTools26 official page for tool/version selection.
- governance: `docs/scientific_governance/12_PCNA_SPECIFIC_CHECKS.md`,
  `13_MD_VALIDATION_RULES.md`, `14_CLAIM_POLICY.md`,
  `15_PROVENANCE_AND_REPRODUCIBILITY.md`, `16_CODING_AGENT_RULES.md`,
  `19_STOP_CONDITIONS.md`, `26_HUMAN_REVIEW_GATES.md`
- confidence: high for audited local structure facts and fail-closed state
- evidence_status: verified preparation/provenance infrastructure only; no MD outcomes
