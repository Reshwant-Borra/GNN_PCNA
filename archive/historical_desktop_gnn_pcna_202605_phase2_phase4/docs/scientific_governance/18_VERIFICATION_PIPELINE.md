# Verification Pipeline

## Purpose

Define the end-to-end verification gates for Phase 2.

## Hard Rules

- Gates are ordered.
- A failed upstream gate blocks dependent downstream work.
- A report without gate status is incomplete.

## Before Implementation

- Source/context review.
- Project scope review.
- Assumption registry.
- Scientific uncertainty register.
- Dataset protocol.
- Benchmark limitations review.
- Data lifecycle registry.
- Split protocol.
- Human review gate setup.
- Claim policy.
- MD interpretation policy.

## During Implementation

- Code must map to documented rules.
- Provenance tracking.
- Artifact registration.
- No stale cache.
- Coding-agent checklist.

## After Dataset Creation

- Dataset audit.
- Benchmark quality audit.
- Data lifecycle audit.
- Split audit.
- Label audit.
- Biological data sanity review.
- Graph audit.

## Before Training

- Human split-freeze and label-freeze approval.
- Biological data sanity review PASS.
- Benchmark limitations accepted.
- Red-team pretraining audit.
- Null-hypothesis baseline plan.
- Readiness gate must allow first training run.
- Human first-training approval.

## After Training

- Metrics audit.
- Seed audit.
- Baseline audit.
- Null-hypothesis baseline audit.
- Calibration audit.
- Architecture and shortcut-feature audit.

## After Prediction

- Biological realism audit.
- PCNA-specific audit.
- Structural plausibility audit.
- Interpretability-before-claims audit.
- Human first-PCNA-prediction interpretation review.

## After MD

- Pre-MD reality check.
- Trajectory quality audit.
- Metric interpretation audit.
- Claim audit.
- Unexpected-results review if needed.
- Human MD interpretation review.

## Before Final Writing

- Contradiction audit.
- Overclaim audit.
- Reproducibility audit.
- AI hallucination audit.
- Negative-result success review.
- Publication readiness audit.
- Readiness gate.

## Required Checks

- Every stage has an audit artifact.
- Every artifact has provenance.
- Every claim has an evidence trace.
- Every unexpected result has an interpretation log.
- Every major uncertainty has a register entry.
- Every mandatory human gate has a decision record.

## Examples Of Failure

- Training starts before the graph audit.
- Training starts before biological data sanity review.
- MD is interpreted before pre-registration.
- MD is interpreted before a pre-MD reality check.
- Final writing begins before baseline and biological realism audits.

## Prevention

Use this pipeline as a dependency graph: downstream stages cannot mark PASS until upstream artifacts exist.

## Forbidden Actions

- Training before dataset/split/label/graph gates pass.
- Claims before baseline, biological, PCNA, MD, and claim gates pass.
- Final report before reproducibility gate passes.

## Compliance Artifact

`reports/phase2/verification_pipeline_status.md`.

## If The Pipeline Fails

Apply [19_STOP_CONDITIONS.md](19_STOP_CONDITIONS.md). Work resumes only after the failed gate is remediated and re-audited.
