# ResearchOS — Full Audit

_Generated 2026-05-24T19-05-20Z_

## Request

> Run a complete ResearchOS audit on the current repo: context, provenance, leakage, preprocessing, metrics, validation, biology, claims, figures, reviewer risks, and contradictions.

- intents: ['source_of_truth_query', 'data_audit', 'split_or_leakage', 'preprocessing_audit', 'code_review', 'metric_verification', 'md_or_validation', 'claim_or_paper', 'figure_generation', 'contradiction_hunt', 'submission_readiness']
- risk level: **high**
- agents executed: context_source_truth, provenance_artifacts, contradiction_hunter, dataset_integrity, preprocessing_auditor, leakage_split, metrics_statistics, scientific_code_review, testing_environment, validation_skeptic, biological_realism, paper_claim, reviewer_collaboration, visual_evidence, model_training, research_design, literature_web, compute_planning
- gates evaluated: dataset, leakage, preprocessing, code, evaluation, validation, claim, figure, research_design, submission

## Verdict

- blocked: **True**
- block reason: leakage_split flagged a blocker: Leakage gate cannot pass without a split protocol.
- human review required: **False**

## Gate status

| Gate | Status |
| --- | --- |
| dataset | `not_started` |
| leakage | `not_started` |
| preprocessing | `not_started` |
| code | `not_started` |
| evaluation | `not_started` |
| validation | `fail` |
| claim | `not_started` |
| figure | `not_started` |
| research_design | `not_started` |
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

### Contradiction and Error Hunter

- status: **pass** (confidence 0.85)
- summary: Contradiction sweep produced 0 findings.

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

### Preprocessing and Feature Engineering Auditor

- status: **warning** (confidence 0.75)
- summary: Preprocessing audit found 1 issues among 0 graphs.
- findings: 1
  - **[MEDIUM]** No graph artifacts registered
- gate updates: preprocessing→warning

### Leakage and Split Design

- status: **blocked** (confidence 0.9)
- summary: Leakage gate cannot pass without a split protocol.
- findings: 1
  - **[CRITICAL]** No documented split protocol — _Document chain-/homology-/apo-holo-blocked splits._
- gate updates: leakage→blocked

### Metrics, Statistics and Uncertainty

- status: **pass** (confidence 0.75)
- summary: Metrics audit: scanned 0 files; 0 findings.
- gate updates: evaluation→pass

### Scientific Code Review

- status: **warning** (confidence 0.65)
- summary: Scanned 51 Python files; 2 flagged; 2 findings.
- findings: 2
  - **[LOW]** NotImplementedError left in code in research_os\agents\base.py — _Audit, document, or remove the marker._
  - **[LOW]** skipped test marker in tests\test_scientific_guardrails.py — _Audit, document, or remove the marker._
- gate updates: code→warning

### Testing and Fresh Environment

- status: **pass** (confidence 0.8)
- summary: Tests/ present; 0 findings; pytest_run=False.
- gate updates: code→pass

### Validation and Skeptic

- status: **warning** (confidence 0.8)
- summary: Validation classification: inconclusive; 1 findings.
- findings: 1
  - **[HIGH]** Validation classification is inconclusive — _Either downgrade claims, or generate validation evidence that classifies as supports_claim / partially_supports_claim._
- gate updates: validation→fail

### Biological and Scientific Realism

- status: **pass** (confidence 0.75)
- summary: Biological realism audit: 0 findings, 0 claims weakened.

### Paper, Claim and Documentation

- status: **pass** (confidence 0.8)
- summary: Paper/Claim audit: scanned 0 draft files; 0 findings.
- gate updates: claim→pass

### Reviewer and Collaboration

- status: **pass** (confidence 0.8)
- summary: Reviewer simulation: 12 canonical questions, 10 open risks tracked.

### Visual Evidence and Figure

- status: **pass** (confidence 0.6)
- summary: Figure audit: 0 files on disk, 0 unregistered.
- gate updates: figure→pass

### Model Development and Training

- status: **warning** (confidence 0.7)
- summary: Model training audit: 1 findings.
- findings: 1
  - **[INFO]** No canonical checkpoint accepted

### Research Design and Falsification

- status: **warning** (confidence 0.7)
- summary: Research design audit: 5 findings.
- findings: 5
  - **[MEDIUM]** Research design lacks 'Null hypothesis' — _Add explicit falsifier / control language._
  - **[MEDIUM]** Research design lacks 'Success criteria' — _Add explicit falsifier / control language._
  - **[MEDIUM]** Research design lacks 'Failure criteria' — _Add explicit falsifier / control language._
  - **[MEDIUM]** Research design lacks 'Falsification' — _Add explicit falsifier / control language._
  - **[MEDIUM]** Research design lacks 'Controls' — _Add explicit falsifier / control language._
- gate updates: research_design→warning

### Deep Literature and Web Research

- status: **warning** (confidence 0.6)
- summary: Literature audit: 0 sources registered.
- findings: 1
  - **[MEDIUM]** source_registry is empty — _Populate source_registry.json with the canonical references._

### Compute Planning and Execution

- status: **pass** (confidence 0.8)
- summary: Compute planning audit: 0 findings.

## Git state at report time

- branch: main
- commit: 3f44ad5 (dirty)

## Workflow notes

This audit is conservative by design. Pass status on any single agent does not imply the project is publication-ready. Submission readiness is a separate workflow.
