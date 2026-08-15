# Project State

Date: 2026-08-15
Branch: final-consolidation-audit
Base HEAD: 5b2ce676c790c4aac0caa10dc4226b5a924791c0

## Current phase

Pre-MD release consolidation, independent extraction-policy freeze, final 1W60 three-seed stability gate, post-pass stronger internal robustness audit, MD structure/parameter preflight, frozen analysis protocol hashing, and infrastructure restart validation are complete.

Current source of truth: `PROJECT_STATUS.md`.

## Current scientific question

Can the already frozen 1W60 candidate pocket meet the new post-pass stronger internal robustness target before production MD, without tuning extraction on PCNA or retraining unnecessarily?

## Code status

- Canonical GNN code has been consolidated to root `src/` and `scripts/`.
- Canonical MD code is `md_validation_4070/`.
- Historical nested `Desktop/GNN_PCNA/` was archived after migrating active interface-map provenance.
- `scripts/independent_extraction_gate.py` is the canonical independent extraction-selection and final 1W60 pre-MD gate script.
- `scripts/strong_robustness_audit.py` is the canonical post-pass stronger robustness diagnostic script; it did not freeze a replacement policy or launch MD.

## Data status

- Official source mmCIF/metadata remain under `data/raw_intake/`.
- Large graph-branch artifacts/checkpoints were not imported wholesale into active tree; they remain generated/rebuildable or require artifact storage policy.
- `gnn_pcna_pre_md_v3.zip` was not found in this workspace; no active workflow depends on it.

## Model status

Frozen seed artifacts are present under `artifacts/go_prep/seed_{42,43,44}` with checkpoint hashes recorded in `best_meta.json`. No retraining was run in this task.

## Candidate status

The frozen extraction policy is `independent_mcc_rank_fraction_size_weighted_cluster`, selected on non-PCNA structures only. Final 1W60 PRE-MD STABILITY is `PASS` under the original exploratory gate with literal mean Jaccard 0.6792 and 16 >=2/3 consensus residues.

The later POST-PASS STRONGER INTERNAL ROBUSTNESS REQUIREMENT asks for mean literal pairwise Jaccard >=0.75 and minimum pairwise >=0.65 before production-MD release readiness. This stricter target was imposed after the 0.6792 result and is not a universal literature threshold. The strong-robustness audit found a shared physical pocket core with nontrivial boundary/fringe extension disagreement, did not identify a materially better independent extraction policy, and did not run a second 1W60 evaluation.

## MD status

NO-GO for production MD. The current legitimate next execution stage is the launcher-first 0.1 ns RTX 4070 smoke test. No legitimate human Gate-6 approval is recorded.

## Active blockers

1. Strong internal robustness target is not achieved: prior mean literal Jaccard is 0.6792 and minimum pairwise Jaccard is 0.6316.
2. No materially better extraction policy was independently justified by the five-protein benchmark.
3. Human Gate-6 approval is not recorded and must not be fabricated.
4. Runtime ML/MD packages are not active in this shell, so production MD prep/smoke tests were not run.
5. Large artifact tracking policy remains unresolved.

## Next action

Run the 0.1 ns RTX 4070 smoke test through `./md.sh smoke`. Do not run production or fabricate Gate-6 approval.

## Canonical command

```bash
cat artifacts/pre_md_independent_extraction_20260815/frozen_extraction_method.json
cat artifacts/pre_md_independent_extraction_20260815/final_consensus_pocket_handoff.json
cat reports/pre_md_independent_extraction_20260815/FINAL_1W60_THREE_SEED_STABILITY_REPORT.md
cat reports/strong_robustness_20260815/RETRAINING_NECESSITY_ASSESSMENT.md
cat md_validation_4070/gnn_pocket_search/GATE6_APPROVAL_TEMPLATE.md
```
