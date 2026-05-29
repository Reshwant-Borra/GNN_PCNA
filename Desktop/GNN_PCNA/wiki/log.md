---
type: log
status: active
created: 2026-05-27
updated: 2026-05-27
tags: [log, decisions, memory]
aliases: [Log]
confidence: high
evidence_status: verified
---

# Log

Append-only record of maintained wiki operations and durable project decisions.

## [2026-05-27] setup | LLM wiki scaffold

- Added initial root `AGENTS.md` operating schema for the GNN/PCNA LLM wiki.
- Created the maintained `wiki/` layer with index, overview, source map, open questions, and empty category folders.
- Established `raw/` and `raw/assets/` as immutable source intake locations.

## [2026-05-27] decision | Codex memory system replaces ResearchOS-style workflow

- Decision: Codex is the primary working agent for Phase 2.
- Decision: `wiki/` is the Obsidian-style memory/navigation layer.
- Decision: `docs/scientific_governance/` is binding scientific law.
- Decision: `crawls/` is raw evidence/source context, not automatically verified truth.
- Decision: V1 / `project-version-1` / old artifacts are historical reference only.
- Source path: user task, `AGENTS.md`, `docs/scientific_governance/16_CODING_AGENT_RULES.md`, `37_PHASE2_IMPLEMENTATION_PLAN.md`
- Confidence: high
- Evidence status: verified

## [2026-05-27] maintenance | Obsidian memory system upgrade

- Upgraded `AGENTS.md` into a Codex-specific startup and governance contract.
- Upgraded `wiki/index.md` into the main Phase 2 knowledge-base dashboard.
- Added crawl navigation, source trust levels, entity pages, concept pages, implementation context, risk tracking, and update rules.
- Added `reports/research_os/obsidian_memory_system_report.md`.
- Source path: user task and local workspace inspection
- Confidence: high
- Evidence status: verified

## [2026-05-27] implementation | Governed data-foundation scaffold

- Created Phase 2 data-foundation artifacts for checklist items 1-7.
- Added source/scope freeze reports, assumption and uncertainty registries, crawl source registry, benchmark limitations review, dataset/lifecycle registries, split/label freeze plans, human review log, biological sanity review template, readiness gate, and read-only foundation checker.
- Current decision: ready for dataset planning and source verification only.
- Current block: not ready for graph generation, GNN implementation, training, evaluation, MD, or claims.
- Source path: `reports/phase2/foundation_milestone_status.md`, `reports/phase2/readiness_gate.md`, `scripts/phase2_foundation_check.py`
- Confidence: high
- Evidence status: verified

## [2026-05-27] dataset investigation | Dataset Investigation + Freeze phase started

- Decision: No dataset is frozen yet. The workspace contains dataset templates, registries, crawl metadata, and source leads, but no adopted canonical benchmark structure/label files.
- Decision: CryptoBench is the leading primary benchmark candidate for human review, not an accepted benchmark. BioLiP/BioLiP2, scPDB, ASD, and PocketMiner-related data remain auxiliary/background/baseline candidates. PDBbind is risky for Phase 2 and should not be a primary cryptic-pocket benchmark.
- Block: split + label freeze is not ready because local CryptoBench files, exact data license, hashes, schema audit, leakage tables, PCNA/homolog screen, and human review records are missing.
- Source path: `reports/phase2/dataset_investigation_report.md`, `reports/phase2/proposed_split_strategy.md`, `reports/phase2/proposed_label_strategy.md`, `wiki/analyses/dataset_strategy.md`, `wiki/analyses/benchmark_strategy.md`, `wiki/analyses/benchmark_limitations.md`
- Confidence: high for local inventory; medium for remote dataset-role assessment
- Evidence status: verified for no local adopted files; inferred for proposed roles; uncertain for freeze readiness

## [2026-05-27] local discovery | Dataset assets not present locally

- Discovery: `raw/` is placeholder-only and `data/` contains only registries/templates.
- Discovery: no compressed dataset archives, PDB/mmCIF/CIF coordinate files, ligand structure files, CSV/TSV/Parquet registries, usable split assignments, residue-label files, benchmark manifests with hashes, or processed dataset artifacts were found under `crawls/`, `raw/`, or `data/`.
- Decision: crawl records for CryptoBench, PocketMiner, BioLiP/BioLiP2, scPDB, ASD, and PDBbind remain candidate evidence/acquisition leads only. They are not adopted Phase 2 datasets.
- Next governed step: acquire official CryptoBench files into a checksum-backed raw intake, then perform license, schema, label, and leakage audits before any freeze.
- Source path: `reports/phase2/local_dataset_discovery_report.md`, `crawls/`, `raw/`, `data/`, `docs/scientific_governance/04_DATASET_CONSTRAINTS.md`, `05_SPLIT_PROTOCOL.md`, `06_LABELING_RULES.md`, `15_PROVENANCE_AND_REPRODUCIBILITY.md`
- Confidence: high
- Evidence status: verified for local absence of usable assets; uncertain for external acquisition details

## [2026-05-27] next action | CryptoBench governed intake required

- Required next action: acquire official CryptoBench files into a governed raw intake and create a checksum-backed intake manifest before dataset adoption continues.
- Required manifest fields: source URL, retrieval date, license evidence, file name, file size, SHA-256 hash, file role, schema notes, and whether the file provides data, labels, splits, structures, scripts, or documentation.
- Stop condition: if official files, license evidence, label schema, split metadata, or structure coordinates are missing or unclear, do not adopt the dataset; update open questions and require human review.
- Source path: `wiki/analyses/dataset_strategy.md`, `wiki/open_questions/open-questions.md`, `reports/phase2/local_dataset_discovery_report.md`, `docs/scientific_governance/04_DATASET_CONSTRAINTS.md`, `05_SPLIT_PROTOCOL.md`, `06_LABELING_RULES.md`, `15_PROVENANCE_AND_REPRODUCIBILITY.md`, `26_HUMAN_REVIEW_GATES.md`
- Confidence: high
- Evidence status: inferred from local absence of usable dataset assets and governance requirements

## 2026-05-27 - Governed Dataset Intake Agent Implemented

- Source path: `scripts/dataset_intake.py`, `scripts/validate_dataset_intake.py`, `src/phase2_intake/`, `docs/dataset_intake_crawler_prompt.md`
- Governance path: `docs/scientific_governance/04_DATASET_CONSTRAINTS.md`, `15_PROVENANCE_AND_REPRODUCIBILITY.md`, `16_CODING_AGENT_RULES.md`, `19_STOP_CONDITIONS.md`, `21_READINESS_GATE.md`, `26_HUMAN_REVIEW_GATES.md`, `31_DATA_LIFECYCLE_TRACKING.md`
- Confidence level: high
- Evidence status: verified
- Decision/update: Implemented a fail-closed dataset/source intake CLI with source adapters, dry-run mode, quarantined raw intake paths, append-only download manifest, inventories, reports, validation script, and tests. The approved source-total cap is 20 GB; single files/archives over 500 MB still require human approval. Dry-run checks for CryptoBench and targeted PCNA structures recorded manifest/report rows without downloading raw files or adopting data.

## 2026-05-27 - CryptoBench and PCNA Raw Intake Acquired

- Source path: `data/raw_intake/cryptobench/`, `data/raw_intake/pcna_structures/`, `data/registries/download_manifest.jsonl`, `data/registries/dataset_inventory.json`, `reports/phase2/friend_dataset_acquisition_report.md`
- Governance path: `docs/scientific_governance/04_DATASET_CONSTRAINTS.md`, `15_PROVENANCE_AND_REPRODUCIBILITY.md`, `19_STOP_CONDITIONS.md`, `21_READINESS_GATE.md`, `26_HUMAN_REVIEW_GATES.md`, `31_DATA_LIFECYCLE_TRACKING.md`
- Confidence level: high for local acquisition/provenance; uncertain for scientific usability until schema, leakage, and human review audits.
- Evidence status: verified for downloaded files, manifest rows, hashes, and the skipped bulk archive record; uncertain for dataset adoption.
- Decision/update: Acquired official under-limit CryptoBench OSF/GitHub assets and targeted RCSB assets for `8GLA`/`1W60` into quarantined raw intake. The `cif-files.zip` CryptoBench archive was skipped because it is about 1.145 GB and requires human approval under the 500 MB single-file gate. No dataset was adopted and no downstream readiness was granted.

## 2026-05-27 - CryptoBench CIF Archive Approved And Downloaded

- Source path: `data/registries/bulk_download_approvals.json`, `data/raw_intake/cryptobench/files/672a0171eae0bff252ba9ea3_cif-files.zip`, `data/registries/download_manifest.jsonl`, `reports/phase2/cryptobench_schema_first_audit.md`
- Governance path: `docs/scientific_governance/04_DATASET_CONSTRAINTS.md`, `15_PROVENANCE_AND_REPRODUCIBILITY.md`, `19_STOP_CONDITIONS.md`, `21_READINESS_GATE.md`, `26_HUMAN_REVIEW_GATES.md`, `31_DATA_LIFECYCLE_TRACKING.md`
- Confidence level: high for local download, hash, manifest, and ZIP inventory; uncertain for scientific usability until schema/leakage/human audits.
- Evidence status: verified for file acquisition and inventory; inferred for schema meaning; uncertain for dataset adoption.
- Decision/update: User approved the official OSF CryptoBench `cif-files.zip` bulk download despite the 500 MB single-file gate. The archive was downloaded under quarantined raw intake, SHA-256 hashed as `8d15f897bfdfdf61c7d97a29f5f6ca2c5e03d73d8fb89be7da5bbc245cf56ae4`, and inspected by ZIP inventory only. The archive contains 5,005 `.cif` files. CryptoBench is ready for formal schema audit, not training.

## 2026-05-27 - CryptoBench Deep Schema And Biological Audit Completed

- Source path: `scripts/cryptobench_deep_audit.py`, `reports/phase2/cryptobench_schema_deep_audit.md`, `reports/phase2/cryptobench_split_risk_audit.md`, `reports/phase2/cryptobench_label_semantics.md`, `reports/phase2/cryptobench_structure_inventory.md`, `reports/phase2/pcna_contamination_screen.md`, `data/registries/cryptobench_schema_summary.json`, `data/registries/cryptobench_fold_summary.json`, `data/registries/cryptobench_structure_index.json`
- Governance path: `docs/scientific_governance/04_DATASET_CONSTRAINTS.md`, `05_SPLIT_PROTOCOL.md`, `06_LABELING_RULES.md`, `07_PREPROCESSING_AND_GRAPH_RULES.md`, `12_PCNA_SPECIFIC_CHECKS.md`, `14_CLAIM_POLICY.md`, `15_PROVENANCE_AND_REPRODUCIBILITY.md`, `19_STOP_CONDITIONS.md`, `21_READINESS_GATE.md`, `26_HUMAN_REVIEW_GATES.md`, `29_BENCHMARK_LIMITATIONS.md`
- Confidence level: high for local file/schema/split/CIF checks; medium for label-semantics interpretation; low for homolog exclusion.
- Evidence status: verified for local audit findings; inferred for biological meaning; uncertain for final scientific usability.
- Decision/update: Completed the requested audit without training, graph generation, split freeze, label freeze, or MD. Key findings: `dataset.json` has 1,107 apo keys and 5,493 apo-holo cryptic records; all 5,005 cryptic CIFs are present/readable; `noncryptic-pockets.json` references 6,915 missing auxiliary structures; labels are pocket-selection residue tokens, not true-negative residue labels; official fold files match `folds.json` by apo ID but lack homolog-cluster proof and have 6 repeated holo PDB IDs across folds; exact PCNA contamination is present in the test fold via apo `5e0v`, holo `3vkx`, UniProt `P12004`; graph-building appears feasible in principle for cryptic records but is blocked pending human review, split/label freeze, and residue-policy resolution.

## 2026-05-27 - Rishi Approved Decisions 1, 2, 3, 4a, 4b, 4d — Blockers 1, 2, 5 Cleared

- Source path: `reports/phase2/human_review_packet.md`, `reports/phase2/residue_mapping_resolution_policy.md`
- Governance path: `docs/scientific_governance/04_DATASET_CONSTRAINTS.md`, `05_SPLIT_PROTOCOL.md`, `06_LABELING_RULES.md`, `12_PCNA_SPECIFIC_CHECKS.md`, `26_HUMAN_REVIEW_GATES.md`
- Confidence level: high — explicit human reviewer approval recorded.
- Evidence status: verified (human decision).
- Decision/update:
  - **Decision 1 — YES:** CryptoBench adopted as cryptic-only benchmark candidate with exclusions. Exact PCNA records (5e0v/3vkx) excluded from model development. 2xur/3bep held pending clustering. 6 repeated holo PDB IDs must be grouped before split assignment.
  - **Decision 2 — YES:** Full PCNA isolation approved. 5e0v and 3vkx excluded from training, validation, and all model selection. May only be used as PCNA positive-control inference targets after model is frozen.
  - **Decision 3 — YES:** Label supervision contract approved. Positive labels from `apo_pocket_selection`; unlisted residues = background/unlabeled (not true negatives); absent residues = masked; PCNA records = holdout.
  - **Decision 4a — APPROVED:** Class 1 (420 failures) — remap via label_seq_id fallback.
  - **Decision 4b — APPROVED:** Class 2 (297 failures) — mask as unlabeled; per-structure exclusion threshold deferred (4c).
  - **Decision 4c — DEFERRED:** Threshold pending per-structure impact analysis. Analysis complete: 1 structure (1lx7, 79% masked) exceeds suggested 50% threshold. Awaiting Rishi threshold confirmation.
  - **Decision 4d — APPROVED:** Class 3 (4 failures) — exclude the 4 wrong-chain records.
  - Blockers 1, 2, 5 cleared. Blocker 4 partially cleared. Blocker 3 (sequence clustering) is now critical path.

## 2026-05-27 - Decision 4c Per-Structure Impact Analysis Complete

- Source path: `scripts/residue_mapping_impact_analysis.py`, `data/registries/residue_mapping_failures.json`, `data/raw_intake/cryptobench/metadata_files/66c328c87352852f68dbeac4_dataset.json`
- Governance path: `docs/scientific_governance/06_LABELING_RULES.md`, `07_PREPROCESSING_AND_GRAPH_RULES.md`
- Confidence level: high for counts and fractions (computed from verified registries); medium for threshold recommendation.
- Evidence status: verified for all numeric outputs; inferred for suggested 50% threshold.
- Decision/update: Ran per-structure analysis of Class 2 cryptic failures (residue_token_absent_from_atom_site). 28 unique apo structures affected out of 53 with any cryptic failure (52.8%). Only 1 structure (1lx7, P12758) has >=50% of pocket residues absent (79% = 15/19 tokens). 4 structures exceed 25%. Recommendation: exclude 1lx7; mask individual absent residues for all other 27 affected structures. Full table in `reports/phase2/residue_mapping_4c_impact_analysis.md`. Registry at `data/registries/residue_mapping_per_structure_impact.json`.

## 2026-05-27 - Human Review Packet Prepared (Blockers 1, 2, 5)

- Source path: `reports/phase2/cryptobench_adoption_decision.md`, `reports/phase2/pcna_isolation_policy.md`, `reports/phase2/proposed_label_policy.md`, `reports/phase2/pcna_contamination_screen.md`, `reports/phase2/cryptobench_leakage_remediation.md`
- Governance path: `docs/scientific_governance/04_DATASET_CONSTRAINTS.md`, `05_SPLIT_PROTOCOL.md`, `06_LABELING_RULES.md`, `12_PCNA_SPECIFIC_CHECKS.md`, `14_CLAIM_POLICY.md`, `26_HUMAN_REVIEW_GATES.md`
- Confidence level: high — all factual claims derived directly from machine-generated audit registry counts and existing report content; no new inferences introduced.
- Evidence status: verified for all structure counts, hit IDs, and failure counts cited; inferred for remediation pathway recommendations.
- Decision/update: Created `reports/phase2/human_review_packet.md` consolidating all three human-review-required decisions (CryptoBench adoption, PCNA isolation policy, label supervision contract) into a single sign-off document for Rishi. Each decision has a YES/NO/DEFER checkbox and signature line. Document is ready to send for review. No decisions were made — this is a review request only.

## 2026-05-27 - Residue Mapping Resolution Policy Drafted (Blocker 4)

- Source path: `data/registries/residue_mapping_failures.json`, `reports/phase2/residue_mapping_failure_analysis.md`
- Governance path: `docs/scientific_governance/06_LABELING_RULES.md`, `05_SPLIT_PROTOCOL.md`, `07_PREPROCESSING_AND_GRAPH_RULES.md`, `15_PROVENANCE_AND_REPRODUCIBILITY.md`
- Confidence level: high for failure class definitions and counts; medium for proposed remediation approaches; low for impact of Class 2 masking on cryptic record completeness until per-structure analysis is run.
- Evidence status: verified for all counts (420 label/auth mismatch, 297 absent from atom_site, 4 wrong chain); inferred for resolution approach per class; uncertain for Class 2 per-structure impact.
- Decision/update: Created `reports/phase2/residue_mapping_resolution_policy.md` proposing three class-specific resolution approaches: Class 1 (420 mismatch) → remap via label_seq_id fallback; Class 2 (297 absent) → mask as unlabeled with per-structure impact analysis required; Class 3 (4 wrong chain) → exclude the 4 records. Policy is `draft_not_frozen` and requires human sign-off (decisions 4a–4d) before implementation. No code was written. No labels were generated.

## 2026-05-27 - Phase 2 Track A/B Remediation Packet And Auxiliary Intake Completed

- Source path: `scripts/phase2_remediation_packet.py`, `reports/phase2/cryptobench_adoption_decision.md`, `reports/phase2/pcna_isolation_policy.md`, `reports/phase2/cryptobench_leakage_remediation.md`, `reports/phase2/label_supervision_risks.md`, `reports/phase2/proposed_label_policy.md`, `reports/phase2/residue_mapping_failure_analysis.md`, `reports/phase2/proposed_phase2_split_strategy.md`, `reports/phase2/cryptobench_candidate_cleaned_registry.md`, `reports/phase2/auxiliary_dataset_audit.md`, `reports/phase2/benchmark_role_classification.md`, `reports/phase2/auxiliary_acquisition_status_summary.md`, `reports/phase2/dataset_footprint_summary.md`, `reports/phase2/phase2_claude_code_handoff.md`, `data/registries/potential_homolog_risks.json`, `data/registries/residue_mapping_failures.json`, `data/registries/cryptobench_candidate_cleaned_registry.json`, `data/registries/auxiliary_dataset_role_summary.json`, `data/registries/download_manifest.jsonl`, `data/registries/dataset_inventory.json`
- Governance path: `docs/scientific_governance/04_DATASET_CONSTRAINTS.md`, `05_SPLIT_PROTOCOL.md`, `06_LABELING_RULES.md`, `07_PREPROCESSING_AND_GRAPH_RULES.md`, `12_PCNA_SPECIFIC_CHECKS.md`, `15_PROVENANCE_AND_REPRODUCIBILITY.md`, `19_STOP_CONDITIONS.md`, `21_READINESS_GATE.md`, `26_HUMAN_REVIEW_GATES.md`, `29_BENCHMARK_LIMITATIONS.md`
- Confidence level: high for local artifact generation and intake manifest state; medium for remediation recommendations; low for homolog safety until clustering is run.
- Evidence status: verified for local files/manifests; inferred for planning recommendations; uncertain for final scientific usability.
- Decision/update: Continued Phase 2 on two non-training tracks. Track A recommends CryptoBench as a cryptic-only benchmark candidate with exclusions and split redesign, not full adoption. PCNA must be isolated from model development; `5e0v`/`3vkx`/`P12004` is a holdout/exclusion candidate. Homolog risk remains unresolved; 6 holo PDB IDs repeat across folds. Residue mapping failures were classified: 420 label-seq/auth-seq mismatches, 297 absent atom-site residue tokens, and 4 tokens on another chain. Track B linked BioLiP/Q-BioLiP, scPDB, ASD, BioGRID, and STRING; downloaded PocketMiner metadata, fpocket/P2Rank metadata, and targeted AlphaFold `P12004` metadata. PDBbind is excluded from the primary benchmark role. All sources remain `raw_unverified` and `not_adopted`; training, graph generation, MD, split freeze, label freeze, and claims remain blocked.

## [2026-05-27] artifact generation | Friend crawl metadata artifacts produced

- Produced 5 Phase 2 support artifacts from `GNN_PNCA_crawled_data.zip` (4.4GB, PCNA-focused crawl).
- Crawl contains: 72 experimental PDB structures (all PCNA P12004 or interactors), 149 raw PDB files, 146 ESM-2 feature arrays, 88 PyG graph .pt files, 90 heuristic pocket scores. No AlphaFold structures present.
- Artifacts: `data/registries/friend_crawl_registry.json` (72 JSONL records), `reports/phase2/friend_crawl_stats.md`, `data/registries/friend_crawl_homolog_groups.json` (not_computed), `data/registries/friend_feature_schema.json`, `data/raw_intake/friend_sample/` (27 structures, 54 files).
- Source path: `GNN_PNCA_crawled_data.zip`, `data/catalog/pcna_data_catalog.json`, `data/catalog/fetch_session.json`, `data/results/all_structures_scores.csv`
- Confidence: high for counts and schema; medium for ligand IDs (HETATM detected but not individually parsed); low for AlphaFold coverage (none present).
- Evidence status: verified from zip archive contents.

## 2026-05-27 - Decision 4c Approved — Blocker 4 Fully Cleared

- Source path: `reports/phase2/residue_mapping_4c_impact_analysis.md`, `data/registries/residue_mapping_per_structure_impact.json`
- Governance path: `docs/scientific_governance/06_LABELING_RULES.md`, `07_PREPROCESSING_AND_GRAPH_RULES.md`, `26_HUMAN_REVIEW_GATES.md`
- Confidence level: high — explicit human approval.
- Evidence status: verified (counts from machine registry; threshold approved by Rishi).
- Decision/update:
  - **Decision 4c — APPROVED:** Threshold set at >=50% of pocket residues absent from atom_site. Only 1 structure qualifies for exclusion: **1lx7** (UniProt P12758, train-2 fold, 79% = 15/19 pocket residues absent). All other 27 affected structures below threshold are masked individually per decision 4b.
  - Blocker 4 (residue mapping) fully cleared. All four decisions approved: 4a (remap 420), 4b (mask), 4c (exclude 1lx7), 4d (exclude 4 wrong-chain).
  - Label generation script is now unblocked and can be implemented.
  - `reports/phase2/residue_mapping_resolution_policy.md` status updated to APPROVED.

## 2026-05-27 - Friend's Prompt 2 Complete — Phase 3 Framework Built

- Source path: `COLLABORATION.md`, friend's local repo (not yet pushed)
- Governance path: `docs/scientific_governance/16_CODING_AGENT_RULES.md`, `37_PHASE2_IMPLEMENTATION_PLAN.md`, `26_HUMAN_REVIEW_GATES.md`
- Confidence level: high for existence; medium for implementation details (not yet reviewed).
- Evidence status: verified by friend's report; files not yet in remote repo.
- Decision/update:
  - Friend's Prompt 2 produced full Phase 3 GNN framework: `src/phase3_model/`, `src/phase3_training/`, `src/phase3_evaluation/`, `src/baselines/`.
  - Trainer includes `--dry-run` blocker guard that prevents actual training until Phase 2 split + label freeze are approved.
  - 58 tests passing locally.
  - **Phase 3 code is NOT yet pushed to main.** Friend will push once Phase 2 unblocks or after review.
  - Phase 3 training remains blocked until blocker 3 (clustering) and subsequent split/label freeze complete.

## 2026-05-27 - Merge Conflict Resolved — Project State Synchronized

- Source path: `.memory/PROJECT_STATE.md`, `data/registries/friend_crawl_registry.json`
- Confidence level: high.
- Evidence status: verified.
- Decision/update:
  - Resolved merge conflict in PROJECT_STATE.md between Reshwant's approval records and friend's crawl artifact records. Both preserved. Removed stale "~23,771 mmCIF + ~20,000 AlphaFold" description — actual crawl is 72 PCNA structures with ESM-2 features, no AlphaFold.
  - Unstaged `../../context/` files that were accidentally staged by friend's agent outside the repo boundary.
  - Pushed merged state to main.

## 2026-05-27 - Sequence Clustering Complete — Blocker 3 Resolved

- Source path: `scripts/sequence_clustering.py`, `data/registries/sequence_cluster_assignments.json`, `data/registries/cross_fold_cluster_risks.json`
- Governance path: `docs/scientific_governance/05_SPLIT_PROTOCOL.md`
- Confidence level: high — RCSB pre-computed clusters; verified API.
- Evidence status: verified for all cluster IDs and cross-fold flags.
- Decision/update:
  - **Method:** RCSB pre-computed sequence clusters at 30% identity. PCNA anchor: 5e0v cluster_id_30 = 1168.
  - **2xur:** cluster 1415 (DNA Pol III Beta subunit) — NOT a PCNA homolog at 30%. Policy: retain in candidate set.
  - **3bep:** no cluster found (chain A is DNA; entity fallbacks found no protein cluster). Not confirmed as PCNA homolog. Policy: retain pending manual protein chain verification.
  - **Repeated holo 2fzc/2fzg/4f04:** apos 2air and 9atc ARE in same cluster (219) — confirmed homologs. Must be in same split group.
  - **Repeated holo 5qya/7fo6:** apos 3e9p (cluster 216) and 4ilg (cluster 381) — NOT homologs. Shared holo is structural coincidence. Assign shared holo to single split only.
  - **Repeated holo 6a5y:** apos 4n5g (cluster 1190) and 6hl0 (cluster 2228) — NOT homologs. Same policy.
  - **Cross-fold cluster risks (6 detected, 5 actionable):** Clusters 885 (8oqp↔7o1i), 150 (6g0s↔2rfj), 219 (2air+4c6b↔9atc), 5192 (6cy1↔6n5j), 3396 (6a45↔6w10). Cluster 365 (1lx7↔6f52) is non-actionable since 1lx7 is excluded (decision 4c). **Split redesign required for 5 clusters.**
  - **PCNA cluster in CryptoBench:** only 5e0v (already excluded). Zero additional contamination found.
  - **PCNA cluster in friend's crawl:** 51/72 structures (expected — crawl is PCNA-focused; all are holdout-only).
  - **Blocker 3 status:** Technical clustering complete. Human sign-off required for split redesign (governance 26_HUMAN_REVIEW_GATES.md).

## 2026-05-27 - Label Generation Complete

- Source path: `scripts/generate_labels.py`, `data/labels/label_manifest.json`, `reports/phase2/label_generation_report.md`
- Governance path: `docs/scientific_governance/06_LABELING_RULES.md`, `07_PREPROCESSING_AND_GRAPH_RULES.md`
- Confidence level: high — all counts from local CIF parsing of verified files.
- Evidence status: verified.
- Decision/update:
  - **1,101 structures labeled** (of 1,107 candidate apos); 6 excluded.
  - Excluded: 5e0v (PCNA decision 2), 2b23/4gpi/8hc1/8oqp (Class 3 wrong-chain decision 4d), 1lx7 (Class 4c >=50% masked).
  - **16,335 positive labels** (residues in pocket selection present in atom_site).
  - **3,704 masked labels** (residues absent from atom_site; excluded from loss per decision 4b).
  - **0 remaps** (Class 1 remap decision 4a): auth_seq_id direct lookup succeeded for all resolvable tokens. The 420 Class 1 failures from the audit script were resolved by our more complete CIF parser (all atoms, not CA-only).
  - Label files written to `data/labels/labels_{apo_pdb_id}.json`; hash-verified manifest at `data/labels/label_manifest.json`.
  - **Label generation is implementation-complete.** Label freeze requires human sign-off (governance 26).

## 2026-05-27 - Split Manifest Frozen — Rishi Approved (Blocker 3 + 6 Cleared)

- Source path: `data/registries/split_manifest_frozen.json`, `reports/phase2/split_manifest_approval_20260527.md`
- Governance path: `docs/scientific_governance/05_SPLIT_PROTOCOL.md`, `26_HUMAN_REVIEW_GATES.md`
- Confidence level: high — explicit human approval.
- Evidence status: verified (explicit Rishi sign-off 2026-05-27).
- Decision/update:
  - **Split redesign approved by Rishi.** 5 test structures moved to train so each 30%-identity cluster falls within a single split group.
  - Assignments: 7o1i → train-1 (cluster 885), 2rfj → train-2 (cluster 150), 9atc → train-1 (cluster 219), 6n5j → train-0 (cluster 5192), 6w10 → train-2 (cluster 3396).
  - Final fold distribution: test=214, train-0=220, train-1=223, train-2=222, train-3=222. Total=1,101 structures.
  - Split manifest written to `data/registries/split_manifest_frozen.json`, status=frozen, hash=24dd5e347d880108.
  - Approval record: `reports/phase2/split_manifest_approval_20260527.md`.
  - **Blockers 3 and 6 fully cleared.**

## 2026-05-27 - Label Manifest Frozen — Rishi Approved (Blocker 7 Cleared)

- Source path: `data/labels/label_manifest.json`, `reports/phase2/split_manifest_approval_20260527.md`
- Governance path: `docs/scientific_governance/06_LABELING_RULES.md`, `26_HUMAN_REVIEW_GATES.md`
- Confidence level: high — explicit human approval; hash-verified files.
- Evidence status: verified.
- Decision/update:
  - Label manifest frozen in same sign-off event as split manifest (2026-05-27, Rishi).
  - `data/labels/label_manifest.json` status set to frozen; frozen_at=2026-05-27; split_manifest_ref=24dd5e347d880108.
  - Labels: 1,101 structures, 16,335 positives, 3,704 masked (-1), 0 remaps, 6 excluded.
  - PU learning contract intact: unlisted residues are background/unlabeled, not true negatives.
  - **Blocker 7 (label freeze) cleared.**

## 2026-05-27 - Phase 2 Complete — All Blockers Cleared

- Source path: `reports/phase2/split_manifest_approval_20260527.md`, `data/registries/split_manifest_frozen.json`, `data/labels/label_manifest.json`
- Governance path: `docs/scientific_governance/21_READINESS_GATE.md`, `26_HUMAN_REVIEW_GATES.md`, `37_PHASE2_IMPLEMENTATION_PLAN.md`
- Confidence level: high.
- Evidence status: verified.
- Decision/update:
  - **Phase 2 Foundation is complete.** All governance decisions documented, approved, and implemented.
  - All 7 Phase 2 blockers cleared as of 2026-05-27.
  - Frozen artifacts: split manifest (24dd5e347d880108) + label manifest (1,101 structures, 16,335 positives).
  - Phase 3 prerequisites met. Friend's `--dry-run` guard may be removed per approval in `reports/phase2/split_manifest_approval_20260527.md`.
  - **Phase 3 is authorized to begin real training.**

## 2026-05-28 - Phase 3 Handoff Corrected And Crawl Use Policy Clarified

- Source path: `.memory/PROJECT_STATE.md`, `COLLABORATION.md`, `reports/phase2/handoff_20260528.md`, `reports/phase2/friend_crawl_stats.md`, `data/registries/friend_crawl_registry.json`, `data/registries/friend_feature_schema.json`, `data/registries/friend_crawl_homolog_groups.json`
- Governance path: `docs/scientific_governance/04_DATASET_CONSTRAINTS.md`, `05_SPLIT_PROTOCOL.md`, `06_LABELING_RULES.md`, `07_PREPROCESSING_AND_GRAPH_RULES.md`, `15_PROVENANCE_AND_REPRODUCIBILITY.md`, `16_CODING_AGENT_RULES.md`, `19_STOP_CONDITIONS.md`, `26_HUMAN_REVIEW_GATES.md`, `29_BENCHMARK_LIMITATIONS.md`, `31_DATA_LIFECYCLE_TRACKING.md`
- Confidence level: high for local repo inspection and committed crawl metadata; medium for off-repo Friend Phase 3 framework status.
- Evidence status: verified for local file presence/absence; inferred for recommended crawl role.
- Decision/update:
  - Corrected context so future agents do not assume the full Phase 3 framework is already present on local `main`. `src/phase3_*`, `src/baselines`, `tests/phase3`, and `reports/phase3` were absent during Codex inspection.
  - Recorded that Friend's Phase 2 crawl metadata artifacts are present, but Friend's finalized Phase 3 implementation/framework is not confirmed as pushed to `main`.
  - Recorded that Friend is currently unavailable per Reshwant's handoff note; Reshwant may authorize Codex to continue or rebuild Phase 3 pieces independently if needed.
  - Clarified crawl use policy: frozen CryptoBench remains the supervised v2 benchmark; the Friend/40GB crawl is not approved for Phase 3 supervised training, is suitable for Phase 4 external inference/discovery after model freeze, and may support future pretraining/expansion only after separate governance and human approval.
  - Reframed first real training as still gated by data-pipeline verification and human sign-off, even though dry-run guard removal is authorized by `reports/phase2/split_manifest_approval_20260527.md`.

## 2026-05-28 - Phase Map Updated With Dataset Role Separation

- Source path: `wiki/analyses/phase2_build_map.md`, `.memory/PROJECT_STATE.md`, `COLLABORATION.md`, `reports/phase2/handoff_20260528.md`
- Governance path: `docs/scientific_governance/04_DATASET_CONSTRAINTS.md`, `05_SPLIT_PROTOCOL.md`, `06_LABELING_RULES.md`, `07_PREPROCESSING_AND_GRAPH_RULES.md`, `26_HUMAN_REVIEW_GATES.md`, `31_DATA_LIFECYCLE_TRACKING.md`
- Confidence level: high for project planning state and local file paths; medium for broader off-repo 40GB crawl contents.
- Evidence status: verified for committed metadata and frozen CryptoBench artifacts; inferred for future crawl use role.
- Decision/update:
  - Updated the phase/build map to state that Phase 3 supervised training/evaluation uses frozen CryptoBench only.
  - Documented the Friend/40GB crawl as Phase 4 external inference/discovery context after model freeze, or future pretraining/expansion only after a separate governed approval path.
  - Explicitly kept first real training gated on Phase 3 data-pipeline audit and human review.

## 2026-05-28 - Governed Phase 3 Data Pipeline Rebuilt Locally

- Source path: `src/phase3_data/`, `src/phase3_training/`, `src/phase3_model/`, `src/phase3_evaluation/`, `src/baselines/`, `tests/phase3/`, `reports/phase3/phase3_framework_rebuild_20260528.md`, `data/registries/phase3_input_validation_20260528.json`, `data/registries/phase3_cif_extraction_manifest_20260528.json`, `data/registries/phase3_dataset_index_20260528.json`, `data/registries/phase3_residue_audit_manifest_20260528.json`
- Governance path: `docs/scientific_governance/04_DATASET_CONSTRAINTS.md`, `05_SPLIT_PROTOCOL.md`, `06_LABELING_RULES.md`, `07_PREPROCESSING_AND_GRAPH_RULES.md`, `08_MODEL_ARCHITECTURE_CONSTRAINTS.md`, `09_EVALUATION_PROTOCOL.md`, `10_BASELINE_REQUIREMENTS.md`, `15_PROVENANCE_AND_REPRODUCIBILITY.md`, `16_CODING_AGENT_RULES.md`, `19_STOP_CONDITIONS.md`, `26_HUMAN_REVIEW_GATES.md`
- Confidence level: high for local artifacts and tests.
- Evidence status: verified.
- Decision/update:
  - Rebuilt the missing local Phase 3 framework as governed scaffolding, not as Friend's unverified methodology.
  - Extracted the approved CryptoBench CIF zip as non-training data preparation with provenance; 5,005 `.cif` files now exist under `data/raw_intake/cryptobench/cif-files/`.
  - Built a frozen-source Phase 3 dataset index with 1,101 entries; all 6 exclusions are skipped and no PCNA cluster `1168` entries appear.
  - Completed a full residue-label audit across 1,101 structures: 16,335 positives aligned, 3,704 masked labels accounted for, unlisted residues preserved as PU/background not true negatives.
  - Added tests for frozen split usage, forbidden `folds.json`, exclusions, masked labels, PCNA train/validation blocking, residue-label mismatch failure, CIF remediation, Friend crawl rejection, and real-training refusal.
  - No real training, graph tensor generation, edge cutoff selection, feature policy, baseline run, test evaluation, or claims were performed.

## 2026-05-28 - Phase 3 Graph Policy Approval Packet Prepared

- Source path: `reports/phase3/graph_edge_feature_policy_approval_packet_20260528.md`, `reports/phase3/phase3_framework_rebuild_20260528.md`, `data/registries/phase3_dataset_index_20260528.json`, `data/registries/phase3_residue_audit_manifest_20260528.json`
- Governance path: `docs/scientific_governance/04_DATASET_CONSTRAINTS.md`, `05_SPLIT_PROTOCOL.md`, `06_LABELING_RULES.md`, `07_PREPROCESSING_AND_GRAPH_RULES.md`, `08_MODEL_ARCHITECTURE_CONSTRAINTS.md`, `15_PROVENANCE_AND_REPRODUCIBILITY.md`, `19_STOP_CONDITIONS.md`, `26_HUMAN_REVIEW_GATES.md`
- Confidence level: high for artifact review and packet creation.
- Evidence status: verified for local artifacts; pending human decision for graph policy.
- Decision/update:
  - Prepared a human approval packet for graph edge/feature policy before graph tensor generation.
  - Packet summarizes the data/residue audit and proposes a conservative initial graph policy for human approval or revision.
  - No graph tensors, training, baseline runs, evaluation, or claims were generated.
  - Verified no `data/graphs` or Phase 3 graph output directory exists and tests still pass (`16 passed`).

## 2026-05-28 - Phase 3 Graph Policy Approved By Human Decision

- Source path: `reports/phase3/graph_policy_human_decision_20260528.md`, `reports/phase3/graph_edge_feature_policy_approval_packet_20260528.md`
- Governance path: `docs/scientific_governance/07_PREPROCESSING_AND_GRAPH_RULES.md`, `08_MODEL_ARCHITECTURE_CONSTRAINTS.md`, `15_PROVENANCE_AND_REPRODUCIBILITY.md`, `19_STOP_CONDITIONS.md`, `26_HUMAN_REVIEW_GATES.md`
- Confidence level: high for recorded approval and local evidence paths.
- Evidence status: verified for local artifacts; human decision recorded from active Codex session.
- Decision/update:
  - Human project owner approved the Phase 3 graph edge/feature policy packet on 2026-05-28.
  - Approval record: `reports/phase3/graph_policy_human_decision_20260528.md`.
  - Codex may implement graph-generation scaffolding exactly as approved and emit graph artifacts, manifests, and provenance.
  - No training, baseline execution, evaluation claims, PCNA prediction interpretation, MD interpretation, or scientific claims are approved by this decision.
  - First graph release still requires human review before real training.


## 2026-05-28 - Phase 3 Graph Generation Package Implemented

- Source path: `src/phase3_graphs/` (constants.py, features.py, mmcif_coords.py, builder.py, manifest.py, cli.py), `tests/phase3/test_phase3_graphs.py`
- Governance path: `docs/scientific_governance/07_PREPROCESSING_AND_GRAPH_RULES.md`, `08_MODEL_ARCHITECTURE_CONSTRAINTS.md`, `15_PROVENANCE_AND_REPRODUCIBILITY.md`, `19_STOP_CONDITIONS.md`, `26_HUMAN_REVIEW_GATES.md`
- Approval record: `reports/phase3/graph_policy_human_decision_20260528.md` (decision_id: phase3_graph_policy_20260528)
- Confidence level: high — implementation matches approved policy exactly; 53/53 tests passing.
- Evidence status: verified.
- Decision/update:
  - Implemented graph generation scaffolding exactly as approved by human decision record.
  - Node features: 25-dim float32 (22 one-hot residue identity + 3 binary flags: is_modified, missing_ca, has_altloc).
  - Spatial edges: undirected CA-CA contact, cutoff 8.0 Å (approved value), both directions stored.
  - Sequential edges: undirected, consecutive label_seq_id integers (diff=1), same chain only, no gap bridging.
  - AltLoc resolution: highest occupancy wins; tie-break lexicographic with ./?  preferred over lettered alternates.
  - Fail-closed: non-numeric/NaN coordinates, positive-label mismatch, duplicate residue keys all raise Phase3DataError.
  - Output format: per-structure .npz (arrays) + _meta.json sidecar; collection graph_release_manifest_<hash>.json with status PENDING_HUMAN_REVIEW.
  - Feature definition hash and policy hash recorded in every manifest entry for provenance.
  - 37 new tests added; total suite 53/53 passing.
  - No graph tensors written to disk yet. CLI must be run separately.
  - Training remains blocked — first graph release requires human review per governance/26_HUMAN_REVIEW_GATES.md.

## 2026-05-28 - Phase 3 First Graph Release Complete

- Source path: `data/graphs/graph_release_manifest_8c22e46f524d5f1d.json`, `data/graphs/*.npz` (1,101), `data/graphs/*_meta.json` (1,101), `reports/phase3/graph_release_audit_20260528.md`, `reports/phase3/handoff_20260528.md`
- Governance path: `docs/scientific_governance/07_PREPROCESSING_AND_GRAPH_RULES.md`, `docs/scientific_governance/15_PROVENANCE_AND_REPRODUCIBILITY.md`, `docs/scientific_governance/19_STOP_CONDITIONS.md`, `docs/scientific_governance/26_HUMAN_REVIEW_GATES.md`
- Approval record: `reports/phase3/graph_policy_human_decision_20260528.md` (decision_id: phase3_graph_policy_20260528)
- Confidence level: high — 0 failures; all counts verified against Phase 2 residue audit.
- Evidence status: verified.
- Decision/update:
  - Smoke test (5 structures): passed. NPZ shapes, manifest provenance, hash consistency, NO_TRAINING_PERFORMED flag all confirmed.
  - Full run (1,101 structures): 1,101/1,101 generated, 0 failures.
  - Exact match to Phase 2 residue audit: 16,335 positives, 3,696 masked nodes + 8 masked-without-nodes (4hr7), 22 no-CA nodes, 4,380 altloc nodes, 351,620 background.
  - Avg spatial degree: ~10 contacts/residue (expected for 8 Å CA-CA cutoff).
  - Policy hash and feature hash are identical across all 1,101 graphs (1 unique each).
  - Status: PENDING_HUMAN_REVIEW. No training, no evaluation, no claims.
  - Next gate: human review of `reports/phase3/graph_release_audit_20260528.md` and manifest, then record `reports/phase3/first_training_approval_YYYYMMDD.md`.

## 2026-05-28 - First Graph Release Approved (GATE 1 Cleared)

- Source path: `reports/phase3/first_graph_release_approval_20260528.md`
- Governance path: `docs/scientific_governance/26_HUMAN_REVIEW_GATES.md`
- Confidence level: high — human decision recorded from active session.
- Evidence status: verified.
- Decision/update:
  - Human project owner reviewed graph release audit and manifest; approved first graph release.
  - Decision ID: `phase3_first_graph_release_20260528`.
  - All 1,101 structures approved. Counts verified against Phase 2 residue audit (exact match).
  - GATE 1 cleared. Real training still requires GATE 2.
  - Approved artifacts: `data/graphs/` (1,101 .npz, 1,101 _meta.json, manifest).

## 2026-05-28 - Phase 3 Model/Training Approval Packet Prepared

- Source path: `reports/phase3/model_training_approval_packet_20260528.md`
- Governance path: `docs/scientific_governance/08_MODEL_ARCHITECTURE_CONSTRAINTS.md`, `09_EVALUATION_PROTOCOL.md`, `10_BASELINE_REQUIREMENTS.md`, `14_CLAIM_POLICY.md`, `19_STOP_CONDITIONS.md`, `26_HUMAN_REVIEW_GATES.md`
- Confidence level: high for proposal structure; subject to human approval before implementation.
- Evidence status: proposal only; no training performed.
- Decision/update:
  - Prepared model/training packet for human review as GATE 2 prerequisite.
  - Proposed architecture: GraphSAGE mean aggregation, 3 message-passing layers, 25-dim input, BCEWithLogitsLoss with pos_weight from train only, no virtual node (batch isolation risk), no final sigmoid during training.
  - Training: 4-fold CV on frozen split, 3-5 seeds, early stopping on validation macro-AUPRC, hyperparameters tuned on validation only.
  - Baselines required: random, solvent exposure, fpocket, P2Rank, PocketMiner (run on our split), basic GCN, GAT, no-edge-type ablation.
  - Primary evaluation metric: macro-AUPRC (pre-specified). Secondary: micro-AUPRC, macro/micro-AUROC, top-k recovery (k=5,10,20), bootstrap 95% CI, calibration, per-protein table.
  - Shortcut safeguards: chain-ID/residue-number already excluded; required ablations post-training: no-sequential-edges, no-spatial-edges, residue-identity shuffled, graph-size correlation, per-protein inspection.
  - Status: PENDING_HUMAN_REVIEW. Human must approve before implementation begins.

## 2026-05-28 - Phase 3 Training Framework Implemented

- Source path: `src/phase3_data/graph_loader.py`, `src/phase3_model/gnn.py`, `src/phase3_training/trainer.py`, `src/phase3_evaluation/metrics.py`
- Tests: `tests/phase3/test_batch_isolation.py`, `tests/phase3/test_phase3_model_loader_metrics.py`
- Governance path: `docs/scientific_governance/08_MODEL_ARCHITECTURE_CONSTRAINTS.md`, `09_EVALUATION_PROTOCOL.md`, `16_CODING_AGENT_RULES.md`
- Approval record: `reports/phase3/model_training_decision_20260528.md` (decision_id: `phase3_model_training_plan_20260528`)
- Confidence level: high
- Evidence status: verified (93/93 tests passing)
- Decision/update:
  - Implemented graph_loader: PyG DataLoader over data/graphs/*.npz, frozen-split-aware (hash-validated), PCNA holdout excluded from train/val, sorted deterministic ordering, compute_pos_weight from training-fold nodes only.
  - Implemented GraphSAGE-3L (gnn.py): SAGEConv(25→H)+ReLU+Dropout ×2, SAGEConv(H→H)+ReLU, Linear(H→1). No sigmoid. No virtual node. hidden_dim locked to {64,128} at construction time.
  - Implemented trainer.py: BCEWithLogitsLoss with train-only pos_weight, Adam optimizer, early stopping on val macro-AUPRC (patience=10). Gate check at entry — raises TrainingGateError until GATE 2 cleared.
  - Implemented metrics.py: macro-AUPRC (primary), micro-AUPRC, macro/micro-AUROC, top-k recovery (k=5,10,20), precision@k, bootstrap 95% CI (N=1000 over proteins), per-protein table, seed mean±SD.
  - GATE 2 prerequisite (batch-isolation test): 4/4 PASSED. Proteins A and B logits in batches [A,B] and [B,A] match single-protein inference within atol=1e-5.
  - Full test suite: 93/93 passing (up from 57).
  - Dry-run guard in gates.py intact. No training performed. No model weights. No scientific claims.
  - Next step: human GATE 2 first-training sign-off, then remove dry-run guard.

## 2026-05-28 - GATE 2 Cleared — First Training Sign-Off And Gates.py Conditionalized

- Source path: `reports/phase3/first_training_signoff_20260528.md`, `src/phase3_training/gates.py`
- Governance path: `docs/scientific_governance/08_MODEL_ARCHITECTURE_CONSTRAINTS.md`, `09_EVALUATION_PROTOCOL.md`, `26_HUMAN_REVIEW_GATES.md`
- Approval record: `reports/phase3/first_training_signoff_20260528.md` (decision_id: `phase3_first_training_signoff_20260528`)
- Confidence level: high — human decision recorded from active session.
- Evidence status: verified.
- Decision/update:
  - Human project owner signed off on GATE 2 first-training sign-off record.
  - `src/phase3_training/gates.py` conditionalized: raises `TrainingGateError` if signoff file absent/missing; returns `GATE_CLEARED` dict if signoff file present. Gate test suite 4/4 still passing.
  - Real training authorized for 4-fold CV × 3 seeds under the conditions stated in signoff record.
  - No test-set evaluation performed. No scientific claims made.

## 2026-05-28 - Phase 3 First Training Run Complete (12/12 Runs)

- Source path: `reports/phase3/training_runs/fold*_seed*_manifest.json` (12 files), `checkpoints/phase3/*.pt` (12 files), `reports/phase3/training_runs/all_runs_summary.json`, `reports/phase3/first_training_results_20260528.md`
- Scripts: `scripts/train_phase3.py`, `scripts/run_all_training.py`, `scripts/summarize_training.py`
- Governance path: `docs/scientific_governance/08_MODEL_ARCHITECTURE_CONSTRAINTS.md`, `09_EVALUATION_PROTOCOL.md`, `19_STOP_CONDITIONS.md`
- Approval record: `reports/phase3/first_training_signoff_20260528.md` (decision_id: `phase3_first_training_signoff_20260528`)
- Confidence level: high — all 12 manifests written with gate_status=GATE_CLEARED; no exceptions.
- Evidence status: verified (all runs terminated via early stopping; no errors).
- Decision/update:
  - All 12 training runs completed successfully (4 folds × 3 seeds). No failures, no interruptions.
  - Architecture: GraphSAGE-3L, hidden_dim=128, dropout=0.1, lr=1e-3, patience=10, max_epochs=200.
  - pos_weight computed from training fold only (~21.0 across folds; background/positive ratio).
  - Split manifest hash validated at load time: 24dd5e347d880108.
  - PCNA holdout (cluster 1168) confirmed excluded from all train and val splits.
  - Per-fold validation macro-AUPRC: fold-0=0.1730, fold-1=0.2035, fold-2=0.1872, fold-3=0.1866.
  - **Overall val macro-AUPRC: 0.1876 ± 0.0113** (range: [0.1719, 0.2042]).
  - Best single run: fold=1, seed=2, val_macro_auprc=0.2042 at epoch 17.
  - All results are validation-only. No test-set evaluation performed. No scientific claims made.
  - Next gates: (1) human reviews these validation results; (2) authorize baselines; (3) human model freeze decision; (4) human test-set evaluation gate; (5) human PCNA inference gate.

## 2026-05-28 - Advay Parallel Track: Phase-4-prep deliverables (Tracks 1-5)

- Source paths: `scripts/audit_crawl_data.py`, `scripts/rank_pcna_candidates.py`, `scripts/validate_esm_features.py`, `scripts/analyze_heuristic_scores.py`, `scripts/check_prediction_overlap.py`, `scripts/derive_pcna_interface_contacts.py`; `data/registries/phase4_crawl_audit.json`, `phase4_candidate_manifest.json`, `phase4_esm_validation.json`, `pcna_interface_map.json`, `pcna_interface_contacts_derived.json`; `wiki/entities/pcna_structure.md`, `wiki/entities/pcna_binding_partners.md`, `wiki/analyses/cryptic_pocket_pcna_literature.md`; `reports/phase4/heuristic_score_analysis.md` (+figures); `reports/phase4/md/{8gla,5e0v,1axc}/pre_registration.md`.
- Governance: `docs/scientific_governance/12_PCNA_SPECIFIC_CHECKS.md`, `13_MD_VALIDATION_RULES.md`, `14_CLAIM_POLICY.md`, `15_PROVENANCE_AND_REPRODUCIBILITY.md`, `16_CODING_AGENT_RULES.md`.
- Confidence: high. Evidence status: verified against primary sources (PDB/UniProt/PMIDs) and against the local crawl zip + committed registries.
- Decisions / durable findings:
  - **Heuristic score provenance resolved.** `friend_crawl_registry.json:heuristic_pocket_score` == `mean_score` column of `data/results/all_structures_scores.csv` (inside local zip), exact match for all 4 scored IDs (1AXC, 1W60, 8GLA, 1W61). It is the per-structure mean of per-residue scores from a PRIOR, non-frozen GNN inference pass — NOT the Phase 3 model. Only 4/72 registry records are scored (the 4 CSV `is_pcna=True` rows); the other 68 are null. Brief's "0.05-0.18 across all 72" is incorrect.
  - **146-vs-72 ESM discrepancy resolved.** 146 `.npy` = 60 registry structures with `has_parsed_features=true` + 86 extended-set (CryptoSite) extras not in the 72-record PCNA catalog. 60/60 ESM arrays valid (N,480) float32, zero NaN/Inf; 13 have N_residues < registry residue_count (always ≤; consistent with per-CA-residue embeddings vs a broader residue_count). Recorded as alignment flag, not corruption.
  - **8GLA fails the ≤3.5 Å quality filter (3.77 Å)** but is force-included as positive control via a documented override in `rank_pcna_candidates.py` (not a silent threshold change). 8GLA ligand = ZQZ (AOH1996-1LE), PMID 37531956.
  - **5E0V is NOT apo PCNA.** It is the PCNA **S228I disease variant + FEN1 peptide** (Duffy et al. 2016, *J Mol Biol* 428:1023-1040, PMID 26688547). The Track-3b "apo reference" assumption is wrong; flagged in the 5E0V pre-registration, candidate manifest, interface map, and open-questions. A true-apo WT reference must be confirmed before MD.
  - **Interface map residues are all cited.** PIP-box pocket 40-44/117-135/230-235/251-253 (Müller 2019, PMID 31134302; 1AXC PMID 8861913); APIM same pocket (5YD8, PMID 29633969); IDCL 117-135; trimer interface + AOH1996/ZQZ region structurally derived (1AXC / 8GLA, reproducible). AOH1996 site overlaps PIP-box/IDCL → positive-control overlap, not a novel site (doc 12).
  - No Phase 3 files touched. No training, graphs, MD, test-set access, or scientific claims. Markdown/scripts/registries only.

## 2026-05-29 - Advay Branch Merged + Phase3 Baseline Framework Implemented (GATE 3)

- Source paths: `src/baselines/random_baseline.py`, `src/baselines/structural_baseline.py`, `src/baselines/gnn_models.py`, `src/baselines/gnn_trainer.py`, `scripts/run_baselines.py`, `scripts/generate_baseline_report.py`, `reports/phase3/baseline_gate3_authorization_20260529.md`
- Governance: `docs/scientific_governance/10_BASELINE_REQUIREMENTS.md`, `09_EVALUATION_PROTOCOL.md`, `16_CODING_AGENT_RULES.md`
- Gate: `reports/phase3/baseline_gate3_authorization_20260529.md` (GATE 3 cleared by Reshwant 2026-05-28)
- Confidence: high. Evidence status: implementation verified; GNN training results pending.
- Decisions / durable findings:
  - **Advay's branch (`origin/advay-parallel-track`) fast-forward merged into main.** All Phase-4-prep deliverables now on main. No conflicts.
  - **`phase3-model-framework` remote branch deleted.** Contained 8 commits not in main (old scaffolding / v2-megaprompt work), all superseded by current main. Verified each commit was old scaffolding before deleting.
  - **GATE 3 authorization record written:** `reports/phase3/baseline_gate3_authorization_20260529.md` documenting Reshwant's 2026-05-28 authorization to run baselines.
  - **Baseline implementations complete:** random (3 seeds), degree/structural (no training), GCN-1L (4 folds × 3 seeds), GAT-2L (4 folds × 3 seeds), SAGE-no-spatial ablation (4 folds × 3 seeds), SAGE-no-sequential ablation (4 folds × 3 seeds). External tool stubs written for fpocket/P2Rank/PocketMiner.
  - **GNN baseline training in progress** (background, ~2-3 hours CPU). Manifests written to `reports/phase3/baseline_runs/`. Run `python scripts/generate_baseline_report.py` after training completes.
  - **Model freeze recommendation (GATE 4 input, provisional):** Best single run = fold=1 seed=2 (val macro-AUPRC 0.2042). Pending final baseline comparison from `reports/phase3/baseline_comparison_report_20260529.md`. Human decision required before freeze.
  - No test-set evaluation. No scientific claims.
