# Agent Interaction Model

## Purpose

This document defines how agents communicate, review each other, fail gates, and propose memory updates.

## Lifecycle

1. Orchestrator creates context packet.
2. Agent runs task.
3. Agent returns structured output.
4. Orchestrator validates output.
5. Provenance Agent records artifacts.
6. Contradiction Agent checks conflicts when needed.
7. Context Agent proposes memory updates.
8. Orchestrator applies approved updates or blocks.

## Status Values

- `pass`: Checks passed.
- `warning`: Work can continue with documented limitations.
- `fail`: Work should not continue until fixed.
- `blocked`: Missing input, environment, or approval.
- `inconclusive`: Evidence is insufficient.
- `not_applicable`: Agent domain not relevant.

## Severity Values

- `critical`: Invalidates result or blocks claim.
- `high`: Must fix before publication or expensive compute.
- `medium`: Fix or disclose before strong claims.
- `low`: Minor issue.
- `info`: Context.

## Producer-Reviewer Pairs

| Producer | Reviewer |
|---|---|
| Code Builder | Scientific Code Review, Testing |
| Model Training | Metrics, Leakage, Provenance |
| Metrics | Contradiction, Provenance |
| Validation | Biological Realism, Claim |
| Paper Claim | Reviewer, Contradiction |
| Visual Evidence | Claim, Metrics |
| Compute Planning | Human for expensive runs |

## Conflict Resolution

When agents disagree:

1. Record the disagreement.
2. Ask Contradiction Agent to analyze evidence.
3. Use weaker claim by default.
4. Ask human if the disagreement affects claims, compute, or submission.

## Memory Updates

Agents do not directly overwrite canonical memory. They propose updates:

```json
{
  "target_file": "memory/CURRENT_CLAIMS.md",
  "update_type": "downgrade_claim",
  "summary": "Change validated-pocket wording to candidate-region wording.",
  "evidence": ["reports/md_validation_100ns_2026-05-23/md_validation_summary.json"],
  "requires_human_approval": true
}
```

## Global Failure Modes

Agents must guard against:

- Model score being treated as biological mechanism.
- Residue-level n being treated as protein-level n.
- Apo/holo leakage.
- Positive-control recovery being called independent validation.
- MD stability being called pocket-opening validation.
- Old figures being treated as current.
- Critical tests being skipped.
