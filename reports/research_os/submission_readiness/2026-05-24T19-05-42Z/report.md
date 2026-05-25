# ResearchOS — Submission Readiness

_Generated 2026-05-24T19-05-42Z_

## Request

> Run submission readiness audit. PI approval required to submit.

- intents: ['submission_readiness', 'contradiction_hunt']
- risk level: **critical**
- agents executed: context_source_truth, provenance_artifacts, leakage_split, preprocessing_auditor, metrics_statistics, biological_realism, validation_skeptic, paper_claim, visual_evidence, reviewer_collaboration, testing_environment, contradiction_hunter
- gates evaluated: research_design, dataset, leakage, preprocessing, code, evaluation, validation, claim, figure, submission

## Verdict

- blocked: **True**
- block reason: leakage_split flagged a blocker: Leakage gate cannot pass without a split protocol.
- human review required: **False**

## Gate status

| Gate | Status |
| --- | --- |
| research_design | `not_started` |
| dataset | `not_started` |
| leakage | `not_started` |
| preprocessing | `not_started` |
| code | `not_started` |
| evaluation | `not_started` |
| validation | `not_started` |
| claim | `warning` |
| figure | `not_started` |
| submission | `not_started` |

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

### Leakage and Split Design

- status: **blocked** (confidence 0.9)
- summary: Leakage gate cannot pass without a split protocol.
- findings: 1
  - **[CRITICAL]** No documented split protocol — _Document chain-/homology-/apo-holo-blocked splits._
- gate updates: leakage→blocked

### Preprocessing and Feature Engineering Auditor

- status: **warning** (confidence 0.75)
- summary: Preprocessing audit found 1 issues among 0 graphs.
- findings: 1
  - **[MEDIUM]** No graph artifacts registered
- gate updates: preprocessing→warning

### Metrics, Statistics and Uncertainty

- status: **pass** (confidence 0.75)
- summary: Metrics audit: scanned 0 files; 0 findings.
- gate updates: evaluation→pass

### Biological and Scientific Realism

- status: **pass** (confidence 0.75)
- summary: Biological realism audit: 0 findings, 0 claims weakened.

### Validation and Skeptic

- status: **warning** (confidence 0.8)
- summary: Validation classification: inconclusive; 1 findings.
- findings: 1
  - **[HIGH]** Validation classification is inconclusive — _Either downgrade claims, or generate validation evidence that classifies as supports_claim / partially_supports_claim._
- gate updates: validation→fail

### Paper, Claim and Documentation

- status: **pass** (confidence 0.8)
- summary: Paper/Claim audit: scanned 0 draft files; 0 findings.
- gate updates: claim→pass

### Visual Evidence and Figure

- status: **pass** (confidence 0.6)
- summary: Figure audit: 0 files on disk, 0 unregistered.
- gate updates: figure→pass

### Reviewer and Collaboration

- status: **pass** (confidence 0.8)
- summary: Reviewer simulation: 12 canonical questions, 10 open risks tracked.

### Testing and Fresh Environment

- status: **pass** (confidence 0.8)
- summary: Tests/ present; 0 findings; pytest_run=False.
- gate updates: code→pass

### Contradiction and Error Hunter

- status: **pass** (confidence 0.85)
- summary: Contradiction sweep produced 0 findings.

## Git state at report time

- branch: main
- commit: 3f44ad5 (dirty)


### Readiness matrix

| Item | Status |
| --- | --- |
| Code reproducible | `no` |
| Fresh environment validated | `no` |
| Critical tests skipped | `no` |
| Dataset documented | `no` |
| Split leakage checked | `no` |
| Preprocessing verified | `no` |
| Metrics independently verified | `no` |
| Statistical uncertainty reported | `no` |
| Biological realism checked | `yes` |
| MD validation classified | `no` |
| Claims audited | `yes` |
| Figures audited | `no` |
| Artifact provenance complete | `no` |
| Paper consistent with claim registry | `no` |
| Human approvals recorded | `yes` |

### Verdict: `not_ready`
