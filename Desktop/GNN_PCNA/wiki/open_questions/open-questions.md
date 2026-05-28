---
type: open-question
status: active
created: 2026-05-27
updated: 2026-05-27
tags: [open-questions, phase2, memory]
aliases: [Open Questions]
confidence: high
evidence_status: inferred
---

# Open Questions

## Phase 2 Implementation Context

- What is the actual local path or branch for V1 / `project-version-1` if it must be audited?
- What is the canonical fresh Phase 2 implementation directory or branch?
- What dataset registry path/schema will Phase 2 use?
- What graph manifest schema will Phase 2 use?
- Who is the required human reviewer or reviewer role for Phase 2 source, dataset, split, label, and biological sanity gates?

## Dataset and Label Questions

- Required next action: human review of the CryptoBench deep audit packet before any graph construction, training, MD, split freeze, label freeze, or dataset adoption.
- Should CryptoBench be adopted as a primary benchmark after the deep audit, adopted with exclusions, or rejected?
- Should the exact PCNA record apo `5e0v` / holo `3vkx` / UniProt `P12004` be excluded, isolated as PCNA holdout, or treated only as a contamination finding?
- Should `noncryptic-pockets.json` be used when 6,915 referenced noncryptic auxiliary structures are missing from the local `cif-files.zip` archive?
- What approved missing-residue/insertion-code policy should handle the 721 selected residue tokens absent from parsed atom-site residue IDs?
- How should duplicate cryptic pair records and repeated holo PDB IDs across folds be handled before split freeze?
- Does human review accept the proposed path `cryptic_only_benchmark_candidate_with_exclusions_and_split_redesign`, or should CryptoBench remain benchmark-only/deferred?
- Should residue mapping failures that match label sequence IDs be remapped, masked, or excluded?
- Should the 158 CryptoBench records marked exclusion/review-required be removed entirely or grouped into special review/holdout buckets?
- What is the exact OSF data license name for CryptoBench, beyond the locally crawled license relationship ID and copyright holder/year?
- Which CryptoBench files are canonical for Phase 2: JSON labels, CIF files, train-test split files, PyMOL scripts, or a derived manifest?
- Does CryptoBench contain PCNA, PCNA homologs, PCNA-like sliding clamps, or any structure that should be isolated as a PCNA-related holdout?
- Which auxiliary datasets, if any, are approved for Phase 2 rather than background context?
- Which auxiliary linked-only sources should be advanced to terms/schema review next: BioLiP/Q-BioLiP, scPDB, ASD, BioGRID/STRING, or none?
- Which proxy ligand labels, if any, are approved?
- Should PDBbind be excluded from Phase 2 datasets because it is affinity-centered, or retained as background/context only?
- Should ASD allosteric-site entries ever become labels, or remain literature/database context only?
- Which candidate source should be verified first: CryptoBench, BioLiP/BioLiP2, scPDB, PDBbind, ASD, PocketMiner-related data, or PCNA PDB/UniProt records?
- What governed raw intake path and manifest naming convention should store official CryptoBench downloads?
- What exact OSF file endpoint or linked repository release should be used to acquire CryptoBench files?
- Are any dataset archives intentionally stored outside `crawls/`, `raw/`, `data/`, `archives/`, `datasets/`, `outputs/`, `cache/`, or `artifacts/`?

## Split and Leakage Questions

- Which sequence clustering tool and threshold are approved?
- Should Phase 2 use CryptoBench's official split after audit, or create a stricter de novo split from raw records?
- What exact apo/holo grouping policy and table will be used?
- How should repeated apo structures paired to multiple holo structures in CryptoBench be grouped?
- Which PCNA structures are final holdout, positive controls, or excluded?
- What leakage status applies to [[AOH1996]] and [[8GLA]]?

## Baseline and Evaluation Questions

- Which baseline set is mandatory for MVP?
- What exact top-k values and bootstrap parameters are approved?
- What metric hierarchy controls claims if AUROC and AUPRC disagree?

## MD and Claim Questions

- Is any Phase 2 MD analysis approved yet?
- What pre-registered MD question, if any, exists?
- What claims, if any, are currently allowed? Default: setup/context only.

## Source Navigation Questions

- Which crawl knowledge base should be promoted first into curated wiki source pages?
- Which crawl sources are excluded/noisy?

## Provenance

- Source paths: `docs/scientific_governance/37_PHASE2_IMPLEMENTATION_PLAN.md`, `wiki/sources/crawl-map.md`, `reports/phase2/scientific_uncertainty_register.md`, `reports/phase2/readiness_gate.md`, `reports/phase2/dataset_investigation_report.md`, `reports/phase2/proposed_split_strategy.md`, `reports/phase2/proposed_label_strategy.md`, `reports/phase2/local_dataset_discovery_report.md`, `reports/phase2/cryptobench_schema_deep_audit.md`, `reports/phase2/cryptobench_split_risk_audit.md`, `reports/phase2/cryptobench_label_semantics.md`, `reports/phase2/cryptobench_structure_inventory.md`, `reports/phase2/pcna_contamination_screen.md`, `reports/phase2/cryptobench_adoption_decision.md`, `reports/phase2/pcna_isolation_policy.md`, `reports/phase2/cryptobench_leakage_remediation.md`, `reports/phase2/proposed_label_policy.md`, `reports/phase2/residue_mapping_failure_analysis.md`, `reports/phase2/proposed_phase2_split_strategy.md`, `reports/phase2/phase2_claude_code_handoff.md`
- Confidence level: high for gaps; evidence status: verified for local audit findings and inferred for scientific decisions still needed
- Date last updated: 2026-05-27
