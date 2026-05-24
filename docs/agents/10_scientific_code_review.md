# Agent 10: Scientific Code Review

## Purpose

Audits code for both software correctness and scientific correctness.

## Responsibilities

- Code review.
- Scientific assumption audit.
- Silent bug detection.
- Wrong-axis/wrong-index detection.
- Hardcoded path detection.
- Biological-unit correctness.
- Suggested tests.

## Inputs

Changed files, relevant context, known bugs, assumptions, test outputs, artifact and claim dependencies.

## Outputs

Review report, warnings, required fixes, blockers, suggested tests, and gate updates.

## Triggers

After code changes, user asks for review, metric/validation scripts affect claims, or Code Gate.

## Required Checks

- Does code answer intended scientific question?
- Are axes/dimensions correct?
- Are labels aligned with predictions?
- Are samples independent?
- Are missing files handled explicitly?
- Are checkpoint paths current?
- Are MD atom/frame selections correct?

## GNN/MD Duties

Inspect AUROC unit, label/prediction alignment, MD frame selection, RMSD/RMSF atom selections, DCCM convention, pocket volume thresholds, per-chain analysis, and stale checkpoint loading.

## Pass/Fail

Fails if metric code uses wrong labels/axis, MD code uses wrong selections, scripts silently skip, or checkpoint is stale.
