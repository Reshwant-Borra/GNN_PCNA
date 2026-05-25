# ResearchOS — MD Validation Audit

_Generated 2026-05-24T19-05-41Z_

## Request

> Audit MD validation evidence and classify it explicitly.

- intents: ['source_of_truth_query', 'md_or_validation', 'metric_verification', 'contradiction_hunt']
- risk level: **high**
- agents executed: context_source_truth, provenance_artifacts, contradiction_hunter, validation_skeptic, biological_realism, metrics_statistics, leakage_split, paper_claim
- gates evaluated: validation, leakage, evaluation

## Verdict

- blocked: **True**
- block reason: leakage_split flagged a blocker: Leakage gate cannot pass without a split protocol.
- human review required: **False**

## Gate status

| Gate | Status |
| --- | --- |
| validation | `fail` |
| leakage | `not_started` |
| evaluation | `not_started` |
| code | `warning` |
| claim | `pass` |

## Agent outputs

### Context and Source-of-Truth

- status: **warning** (confidence 0.9)
- summary: 9 of 9 canonical files present; 9 need review. git=3f44ad5 branch=main dirty=True.
- findings: 10
  - **[MEDIUM]** PROJECT_CANONICAL_STATUS.md status=needs_review — _Have an authoritative agent refresh PROJECT_CANONICAL_STATUS.md and set status=current._
  - **[MEDIUM]** CURRENT_CLAIMS.md status=needs_review — _Have an authoritative agent refresh CURRENT_CLAIMS.md and set status=current._
  - **[MEDIUM]** KNOWN_BUGS_AND_RISKS.md status=needs_review — _Have an authoritative agent refresh KNOWN_BUGS_AND_RISKS.md and set status=current._
  - **[MEDIUM]** HUMAN_DECISIONS.md status=needs_review — _Have an authoritative agent refresh HUMAN_DECISIONS.md and set status=current._
  - **[MEDIUM]** VALIDATION_STATUS.md status=needs_review — _Have an authoritative agent refresh VALIDATION_STATUS.md and set status=current._
  - **[MEDIUM]** DATASET_REGISTRY.md status=needs_review — _Have an authoritative agent refresh DATASET_REGISTRY.md and set status=current._
  - **[MEDIUM]** MODEL_REGISTRY.md status=needs_review — _Have an authoritative agent refresh MODEL_REGISTRY.md and set status=current._
  - **[MEDIUM]** COMPUTE_REGISTRY.md status=needs_review — _Have an authoritative agent refresh COMPUTE_REGISTRY.md and set status=current._
  - **[MEDIUM]** REVIEWER_RISK_REGISTER.md status=needs_review — _Have an authoritative agent refresh REVIEWER_RISK_REGISTER.md and set status=current._
  - **[LOW]** Working tree is dirty

### Provenance, Versioning and Artifact

- status: **warning** (confidence 0.85)
- summary: Reviewed 0 artifact entries; 1 provenance findings; 0 artifacts should be marked stale.
- findings: 1
  - **[MEDIUM]** Artifact registry is empty — _Register checkpoints, predictions, metrics, MD outputs, and figures._
- gate updates: code→warning

### Contradiction and Error Hunter

- status: **pass** (confidence 0.85)
- summary: Contradiction sweep produced 0 findings.

### Validation and Skeptic

- status: **warning** (confidence 0.8)
- summary: Validation classification: inconclusive; 1 findings.
- findings: 1
  - **[HIGH]** Validation classification is inconclusive — _Either downgrade claims, or generate validation evidence that classifies as supports_claim / partially_supports_claim._
- gate updates: validation→fail

### Biological and Scientific Realism

- status: **pass** (confidence 0.75)
- summary: Biological realism audit: 0 findings, 0 claims weakened.

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

### Paper, Claim and Documentation

- status: **pass** (confidence 0.8)
- summary: Paper/Claim audit: scanned 0 draft files; 0 findings.
- gate updates: claim→pass

## Git state at report time

- branch: main
- commit: 3f44ad5 (dirty)

## Workflow notes

Stable RMSD validates simulation stability — not cryptic pocket opening. Every MD claim must be explicitly classified as supports / partially supports / inconclusive / weakens / contradicts.
