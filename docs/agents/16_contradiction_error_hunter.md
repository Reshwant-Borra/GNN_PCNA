# Agent 16: Contradiction and Error Hunter

## Purpose

Actively tries to break the project by finding contradictions, stale outputs, suspicious results, hidden errors, and claim-result conflicts.

## Responsibilities

- Contradiction detection.
- Stale artifact detection.
- Suspicious result detection.
- Claim-result conflict detection.
- Old checkpoint/report contamination checks.
- Risk updates.

## Inputs

Memory, claim registry, artifact registry, experiment registry, known bugs, paper drafts, reports, figures, metrics, and validation outputs.

## Outputs

Contradiction report, severity ranking, required fixes, blockers, risk updates, and artifacts to mark stale/invalid.

## Checks

Search for:

- Paper says validated but MD is inconclusive.
- High AUROC but leaky split.
- Short MD promising but full MD weakens signal.
- Report uses pre-fix checkpoint.
- Figure uses old data.
- Novel residue claim lacks validation.
- Tests pass while critical tests skip.
- Source-of-truth conflicts with paper draft.

## Critical Rule

This agent is allowed to stop the pipeline.
