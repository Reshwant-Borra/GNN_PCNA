# ResearchOS — Metric Verification

_Generated 2026-05-26T14-17-39Z_

## Request

> Independently verify metrics in the repo.

- intents: ['source_of_truth_query', 'metric_verification', 'split_or_leakage', 'code_review', 'contradiction_hunt']
- risk level: **high**
- agents executed: context_source_truth, provenance_artifacts, contradiction_hunter, metrics_statistics, leakage_split, dataset_integrity, scientific_code_review, testing_environment, paper_claim
- gates evaluated: leakage, evaluation, dataset, code

## Verdict

- blocked: **True**
- block reason: leakage_split flagged a blocker: Leakage gate cannot pass without a split protocol.
- human review required: **False**

## Gate status

| Gate | Status |
| --- | --- |
| leakage | `not_started` |
| evaluation | `not_started` |
| dataset | `not_started` |
| code | `not_started` |
| claim | `pass` |

## Agent outputs

### Context and Source-of-Truth

- status: **warning** (confidence 0.9)
- summary: 9 of 9 canonical files present; 4 need review. git= branch= dirty=False.
- findings: 4
  - **[MEDIUM]** DATASET_REGISTRY.md status=needs_review — _Have an authoritative agent refresh DATASET_REGISTRY.md and set status=current._
  - **[MEDIUM]** MODEL_REGISTRY.md status=needs_review — _Have an authoritative agent refresh MODEL_REGISTRY.md and set status=current._
  - **[MEDIUM]** COMPUTE_REGISTRY.md status=needs_review — _Have an authoritative agent refresh COMPUTE_REGISTRY.md and set status=current._
  - **[MEDIUM]** REVIEWER_RISK_REGISTER.md status=needs_review — _Have an authoritative agent refresh REVIEWER_RISK_REGISTER.md and set status=current._

### Provenance, Versioning and Artifact

- status: **warning** (confidence 0.85)
- summary: Reviewed 5 artifact entries; 1 provenance findings; 0 artifacts should be marked stale.
- findings: 1
  - **[HIGH]** Artifact ART-0001 missing provenance fields: ['git_commit'] — _Update artifact ART-0001 with full provenance._

### Contradiction and Error Hunter

- status: **pass** (confidence 0.85)
- summary: Contradiction sweep produced 0 findings.

### Metrics, Statistics and Uncertainty

- status: **pass** (confidence 0.75)
- summary: Metrics audit: scanned 0 files; 0 findings.
- gate updates: evaluation→pass

### Leakage and Split Design

- status: **blocked** (confidence 0.9)
- summary: Leakage gate cannot pass without a split protocol.
- findings: 1
  - **[CRITICAL]** No documented split protocol — _Document chain-/homology-/apo-holo-blocked splits._
- gate updates: leakage→blocked

### Dataset and Label Integrity

- status: **warning** (confidence 0.8)
- summary: Dataset registry audit: 0 missing, 5 pending.
- findings: 5
  - **[MEDIUM]** DATASET_REGISTRY.md section 'Datasets in use' still pending — _Replace 'pending' content with the actual definition._
  - **[MEDIUM]** DATASET_REGISTRY.md section 'Label definition' still pending — _Replace 'pending' content with the actual definition._
  - **[MEDIUM]** DATASET_REGISTRY.md section 'Missing-data policy' still pending — _Replace 'pending' content with the actual definition._
  - **[MEDIUM]** DATASET_REGISTRY.md section 'Residue/chain mapping rules' still pending — _Replace 'pending' content with the actual definition._
  - **[MEDIUM]** DATASET_REGISTRY.md section 'Split protocol' still pending — _Replace 'pending' content with the actual definition._
- gate updates: dataset→warning

### Scientific Code Review

- status: **pass** (confidence 0.65)
- summary: Scanned 0 Python files; 0 flagged; 0 findings.
- gate updates: code→pass

### Testing and Fresh Environment

- status: **warning** (confidence 0.8)
- summary: No tests/ directory; testing gate degraded.
- findings: 1
  - **[MEDIUM]** No tests/ directory found — _Create at least smoke tests under tests/._
- gate updates: code→warning

### Paper, Claim and Documentation

- status: **pass** (confidence 0.8)
- summary: Paper/Claim audit: scanned 0 draft files; 0 findings.
- gate updates: claim→pass

## Git state at report time

- branch: 
- commit:  (clean)

## Workflow notes

Headline metrics are only valid when the Leakage gate passes and the Metrics agent independently reproduces the numbers with appropriate uncertainty.
