# Claude Code Full Session Handoff

## Status

- Handoff created: 2026-05-28
- Workspace: `C:\Users\reshw\Desktop\GNN_PCNA`
- Current state: `raw_unverified`, `not_adopted`, `not_ready_for_training`
- Training readiness: `false`
- Dataset adoption: none
- Split freeze: not done
- Label freeze: not done
- Graph generation: not done
- MD: not run
- Scientific claims: not authorized

Claude Code must start by reading:

- `AGENTS.md`
- `wiki/index.md`
- `wiki/analyses/coding_agent_context.md`
- relevant files under `docs/scientific_governance/`

Binding rule: implement only documented science. If a scientific assumption is missing, stop and document it instead of inventing it.

## Hard Prohibitions

Do not:

- train models
- generate final graphs
- run MD
- freeze labels
- freeze splits
- tune architectures
- make scientific claims
- treat CryptoBench as adopted
- treat auxiliary datasets as cryptic-pocket truth
- use PCNA records for model development

## What Was Done

Two non-training tracks were completed.

Track A: CryptoBench remediation and split redesign planning.

Track B: auxiliary dataset acquisition and role classification.

All work stayed in audit/planning/quarantine mode.

## Track A Outputs

Primary reports:

- `reports/phase2/cryptobench_schema_deep_audit.md`
- `reports/phase2/cryptobench_split_risk_audit.md`
- `reports/phase2/cryptobench_label_semantics.md`
- `reports/phase2/cryptobench_structure_inventory.md`
- `reports/phase2/pcna_contamination_screen.md`
- `reports/phase2/cryptobench_adoption_decision.md`
- `reports/phase2/pcna_isolation_policy.md`
- `reports/phase2/cryptobench_leakage_remediation.md`
- `reports/phase2/label_supervision_risks.md`
- `reports/phase2/proposed_label_policy.md`
- `reports/phase2/residue_mapping_failure_analysis.md`
- `reports/phase2/proposed_phase2_split_strategy.md`
- `reports/phase2/cryptobench_candidate_cleaned_registry.md`

Machine-readable registries:

- `data/registries/cryptobench_schema_summary.json`
- `data/registries/cryptobench_fold_summary.json`
- `data/registries/cryptobench_structure_index.json`
- `data/registries/potential_homolog_risks.json`
- `data/registries/residue_mapping_failures.json`
- `data/registries/cryptobench_candidate_cleaned_registry.json`

Scripts:

- `scripts/cryptobench_deep_audit.py`
- `scripts/phase2_remediation_packet.py`

## Track A Findings

CryptoBench structure:

- `dataset.json`: 1,107 apo PDB keys.
- `dataset.json`: 5,493 apo-holo cryptic pocket records.
- Cryptic records reference 5,005 unique CIF structures.
- All 5,005 cryptic referenced CIFs are present and readable.
- `noncryptic-pockets.json`: 14,493 auxiliary noncryptic records.
- `noncryptic-pockets.json` references 8,440 unique structures.
- 6,915 noncryptic auxiliary structures are missing from the local `cif-files.zip`.

Label semantics:

- Labels are pocket-selection residue tokens inside apo-holo records.
- They are proxy benchmark cryptic pocket-region labels.
- They are not dense residue truth.
- Unlisted residues are not safe true negatives by default.
- Noncryptic auxiliary records are not safe negative supervision as-is.

PCNA contamination:

- Exact human PCNA contamination exists.
- Apo: `5e0v`
- Holo: `3vkx`
- UniProt: `P12004`
- Fold: official CryptoBench `test`
- Ligand: `T3`, ligand index `301`
- Additional sliding-clamp/PCNA text hits: `2xur`, `3bep`, `3vkx`, `5e0v`

Leakage risks:

- Official fold files match `folds.json` by apo ID.
- No exact apo ID overlap across folds.
- No exact UniProt overlap across folds was detected.
- 6 holo PDB IDs repeat across official folds:
  - `2fzc`
  - `2fzg`
  - `4f04`
  - `5qya`
  - `6a5y`
  - `7fo6`
- Homolog safety is unresolved because no approved sequence clustering has been run.
- PCNA-like/sliding-clamp homolog risk is unresolved.

Residue mapping:

- 409,944 selected residue tokens were checked against present CIF atom-site residue IDs.
- 721 mapping failures were found.
- Failure reasons:
  - 420 `matches_label_seq_id_not_auth_seq_id`
  - 297 `residue_token_absent_from_atom_site`
  - 4 `residue_token_exists_on_other_chain`
- 180,488 noncryptic selection tokens were skipped because referenced auxiliary CIFs are missing.

Candidate cleaned registry:

- Total cryptic records: 5,493.
- Exclusion/review-required records: 158.
- PCNA holdout records: 1.
- Recommendation: cryptic-only benchmark candidate with exclusions and a new homolog-aware split.

## CryptoBench Adoption Decision

Current decision: `not_adopted`.

Recommended path:

`cryptic_only_benchmark_candidate_with_exclusions_and_split_redesign`

Do not adopt full CryptoBench as-is.

Possible later adoption requires:

- PCNA isolation
- repeated-holo grouping or exclusion
- residue mapping remediation or masking
- sequence/homolog clustering
- label policy approval
- human dataset review

## PCNA Isolation Policy

PCNA must be fully isolated from model development.

PCNA and PCNA-like sliding-clamp records must not be used for:

- training
- validation
- threshold selection
- feature-scaler fitting
- architecture selection
- split tuning
- model selection

Allowed later uses, only after governance gates:

- external blind target
- held-out family
- positive-control only
- inference-only target

The exact PCNA record `5e0v`/`3vkx`/`P12004` should be excluded or held out pending human review.

## Proposed Label Policy

Policy status: `draft_not_frozen`.

Proposed supervision contract:

- Positive label source: CryptoBench `dataset.json` `apo_pocket_selection`, mapped to resolved apo residues.
- Label type: proxy benchmark cryptic pocket-region positive.
- Negative label source: none frozen.
- Unlisted residues: background/unlabeled, not true negatives.
- Ambiguous residues: mask until residue mapping and missing-residue policy pass.
- Noncryptic pockets: audit/reference only until missing structures and semantics are resolved.
- PCNA labels: holdout or positive-control only.
- Dense residue classification: not scientifically justified until partial-label or background-negative policy is approved.

## Proposed Split Strategy

Strategy status: `draft_not_frozen`.

Candidate split path:

1. Start from CryptoBench cryptic `dataset.json` only.
2. Remove or isolate exact PCNA and PCNA-like sliding-clamp records.
3. Build system groups using UniProt, apo/holo pair, ligand variants, repeated holo structures, sequence cluster, and structural review flags.
4. Assign train/validation/test by group, never by residue or graph.
5. Keep PCNA and external targets out of model development.

Split freeze is blocked until:

- sequence clustering tool and threshold are chosen
- clustering is run and registered
- repeated holo PDB IDs are grouped or excluded
- PCNA isolation is approved
- label policy is approved
- human split review is recorded

## Track B Outputs

Reports:

- `reports/phase2/auxiliary_dataset_audit.md`
- `reports/phase2/benchmark_role_classification.md`
- `reports/phase2/auxiliary_acquisition_status_summary.md`
- `reports/phase2/dataset_footprint_summary.md`

Machine-readable:

- `data/registries/auxiliary_dataset_role_summary.json`
- `data/registries/dataset_inventory.json`
- `data/registries/dataset_inventory.csv`
- `data/registries/download_manifest.jsonl`

## Track B Acquisition State

All assets remain quarantined or linked-only. No auxiliary dataset is adopted.

Source status:

| Source | Status | Recommended role |
|---|---|---|
| CryptoBench | downloaded/quarantined | primary benchmark candidate after remediation |
| BioLiP/Q-BioLiP | linked-only | auxiliary ligand-contact context only |
| scPDB | linked-only | possible binding-pocket proxy source; terms/bulk unresolved |
| ASD | linked-only | allosteric context/reference only |
| PocketMiner | metadata downloaded + DOI linked | baseline/method reference |
| fpocket/P2Rank | GitHub metadata downloaded | baseline tool planning |
| BioGRID | linked-only | PCNA interaction context only |
| STRING | linked-only | PCNA functional association context only |
| AlphaFold P12004 | metadata downloaded | predicted-structure context only |
| PDBbind | not acquired | exclude from primary Phase 2 benchmark role |

Downloaded or linked auxiliary assets are represented in:

- `data/registries/download_manifest.jsonl`
- `data/registries/dataset_inventory.json`
- `reports/phase2/auxiliary_acquisition_status_summary.md`

## Auxiliary Dataset Decisions

Keep for possible later use:

- BioLiP/Q-BioLiP as ligand-contact/proxy context after terms/schema review.
- scPDB only if terms, size, schema, and label meaning are acceptable.
- ASD as allosteric reference/context, not default labels.
- PocketMiner for baseline and method comparison after overlap audit.
- fpocket/P2Rank for baseline planning after installation/output schema verification.
- BioGRID/STRING for PCNA context only.
- AlphaFold P12004 for context only if justified.

Exclude from primary benchmark use:

- PDBbind, because it is affinity/protein-ligand centered and not a cryptic-pocket benchmark.

## Validation Commands Run

The following checks passed:

```powershell
python scripts/cryptobench_deep_audit.py
python scripts/phase2_remediation_packet.py
python -m py_compile scripts/phase2_remediation_packet.py scripts/cryptobench_deep_audit.py
python -m json.tool data/registries/potential_homolog_risks.json
python -m json.tool data/registries/residue_mapping_failures.json
python -m json.tool data/registries/cryptobench_candidate_cleaned_registry.json
python -m json.tool data/registries/auxiliary_dataset_role_summary.json
python scripts/validate_dataset_intake.py
python scripts/phase2_foundation_check.py --json
```

Foundation check result:

```json
{
  "foundation_scaffold_complete": true,
  "ready_for_dataset_planning": true,
  "ready_for_training": false,
  "training_blockers": [
    "No accepted dataset.",
    "No frozen split.",
    "No frozen label definition.",
    "No biological data sanity PASS.",
    "No human review approvals.",
    "No graph audit."
  ]
}
```

## Direct Answers For Claude Code

1. Can CryptoBench be used safely?
   Not yet. It can remain a cryptic-only benchmark candidate after remediation.

2. What exclusions/remediation are required?
   PCNA isolation, repeated-holo grouping/exclusion, residue mapping remediation/masking, sequence clustering, split redesign, and human review.

3. Must PCNA be fully isolated?
   Yes. PCNA and PCNA-like sliding-clamp records must be isolated from model development.

4. What supervision strategy is defensible?
   Partial/proxy positive pocket-region supervision. Unlisted residues are background/unlabeled, not true negatives.

5. What leakage risks remain unresolved?
   Homolog leakage, PCNA-like structural homolog leakage, repeated holo PDB cross-fold leakage, apo/holo grouping, and ligand-variant grouping.

6. Which auxiliary datasets are worth keeping?
   BioLiP/Q-BioLiP, scPDB, ASD, PocketMiner, fpocket/P2Rank, BioGRID/STRING, and AlphaFold as context/baseline/supporting sources only.

7. What datasets should be excluded?
   PDBbind from primary benchmark use. Noncryptic auxiliary CryptoBench records from training until missing structures and semantics are resolved.

8. Is Phase 2 ready for split freeze planning?
   Yes, planning only. Not freeze.

9. Is Phase 2 ready for label freeze planning?
   Yes, planning only. Not freeze.

10. Is Phase 2 ready for graph-construction planning?
   Yes, planning only. Not graph generation.

11. What still blocks training?
   No accepted dataset, no frozen split, no frozen label definition, no biological sanity PASS, no human approvals, no graph audit, unresolved homolog risk, unresolved residue mapping failures, unresolved PCNA isolation decision.

## Recommended Next Claude Code Tasks

1. Read this file plus `AGENTS.md`, `wiki/index.md`, and `wiki/analyses/coding_agent_context.md`.
2. Do not train or generate graphs.
3. Prepare a human review packet for:
   - CryptoBench cryptic-only adoption with exclusions
   - PCNA isolation policy
   - label supervision policy
   - sequence clustering tool/threshold
4. If asked to continue technical planning, implement only:
   - sequence extraction audit scripts
   - clustering preparation manifests
   - residue mapping remediation analysis
   - split draft generators that output `draft_not_frozen`
5. Keep every output `raw_unverified`, `not_adopted`, and `not_ready_for_training`.

## Files Most Likely Needed Next

- `reports/phase2/cryptobench_adoption_decision.md`
- `reports/phase2/pcna_isolation_policy.md`
- `reports/phase2/cryptobench_leakage_remediation.md`
- `reports/phase2/proposed_label_policy.md`
- `reports/phase2/residue_mapping_failure_analysis.md`
- `reports/phase2/proposed_phase2_split_strategy.md`
- `reports/phase2/cryptobench_candidate_cleaned_registry.md`
- `data/registries/potential_homolog_risks.json`
- `data/registries/residue_mapping_failures.json`
- `data/registries/cryptobench_candidate_cleaned_registry.json`
- `data/registries/auxiliary_dataset_role_summary.json`
- `data/registries/dataset_inventory.json`

## Provenance

- Source paths: `AGENTS.md`, `wiki/index.md`, `wiki/analyses/coding_agent_context.md`, `docs/scientific_governance/`, `reports/phase2/`, `data/registries/`, `data/raw_intake/`
- Confidence: high for local artifact summary; medium for remediation recommendations; low for homolog safety until clustering is run.
- Evidence status: verified for local files and generated registries; inferred for planning recommendations; uncertain for final scientific usability.
