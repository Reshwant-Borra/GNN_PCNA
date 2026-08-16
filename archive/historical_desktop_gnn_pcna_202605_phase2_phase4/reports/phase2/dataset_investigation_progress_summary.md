# Dataset Investigation Progress Summary

Date: 2026-05-27
Created by: Codex
Status: documentation snapshot before local dataset discovery

## What Was Done

- Started the governed Dataset Investigation + Freeze phase.
- Confirmed the task is limited to dataset evidence gathering and strategy documentation.
- Did not train, build the final GNN, generate graphs, freeze splits, freeze labels, or run MD.
- Read project startup context from `AGENTS.md`, `wiki/index.md`, and `wiki/analyses/coding_agent_context.md`.
- Read binding governance for datasets, splits, labels, evaluation, baselines, biological realism, PCNA-specific checks, claims, provenance, coding-agent rules, stop conditions, readiness, human gates, null baselines, benchmark limitations, and the Phase 2 implementation plan.
- Inspected existing Phase 2 scaffold reports and registries.
- Checked the local `data/` tree and found templates/registries only, not adopted dataset files.
- Inspected crawl/source leads for CryptoBench, BioLiP/BioLiP2, scPDB, PDBbind, ASD, and PocketMiner-related assets.
- Checked official/primary external source leads for CryptoBench, BioLiP/BioLiP2, scPDB, ASD, PocketMiner, and PDBbind context.

## Reports Created

- `reports/phase2/dataset_investigation_report.md`
- `reports/phase2/proposed_split_strategy.md`
- `reports/phase2/proposed_label_strategy.md`

## Wiki Updates

- `wiki/analyses/dataset_strategy.md`
- `wiki/analyses/benchmark_strategy.md`
- `wiki/analyses/benchmark_limitations.md`
- `wiki/open_questions/open-questions.md`
- `wiki/analyses/coding_agent_context.md`
- `wiki/log.md`

## Current Dataset Conclusions

- CryptoBench is the leading primary benchmark candidate, not an accepted dataset.
- BioLiP/BioLiP2 and scPDB are possible auxiliary proxy-label/background sources only.
- ASD is allosteric context/reference unless entry-level site mappings are audited.
- PocketMiner-related assets are baseline/method-context candidates only unless separately audited.
- PDBbind is not appropriate as a primary Phase 2 cryptic-pocket benchmark because it is affinity-centered.

## Current Blockers

- No locally adopted CryptoBench dataset files.
- No resolved exact CryptoBench data license.
- No parsed local CryptoBench schema.
- No local dataset hashes.
- No PCNA/homolog contamination screen.
- No apo/holo grouping table.
- No duplicate structure table.
- No human dataset adoption, split-freeze, or label-freeze decision.

## Verification

`python scripts/phase2_foundation_check.py --json` reported:

- `foundation_scaffold_complete: true`
- `ready_for_dataset_planning: true`
- `ready_for_training: false`

Training remains blocked by governance.

## Provenance

- Source paths: `AGENTS.md`, `wiki/index.md`, `wiki/analyses/coding_agent_context.md`, `docs/scientific_governance/`, `crawls/pcna-dataset-repositories-pass9/`, `crawls/pcna-curated-official-tools-data-structures-pass8/`, `crawls/pcna-gap-closure-datasets-tools-structures-pass6/`, `reports/phase2/dataset_investigation_report.md`, `reports/phase2/proposed_split_strategy.md`, `reports/phase2/proposed_label_strategy.md`
- Confidence: high for local workspace findings; medium for remote source-role assessment; low for final dataset suitability until actual files are inventoried and audited
- Evidence status: verified for local inventory, inferred for proposed roles, uncertain for freeze readiness
