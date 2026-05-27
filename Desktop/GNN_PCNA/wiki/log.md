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
