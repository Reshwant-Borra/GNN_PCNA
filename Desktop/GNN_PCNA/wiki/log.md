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
