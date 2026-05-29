# Memory Update Protocol

## Rule

Agents do not directly overwrite canonical memory. They propose updates; the Orchestrator validates and applies them only after required checks and approvals.

## Flow

1. Agent completes task.
2. Agent emits update proposal.
3. Orchestrator validates schema and evidence.
4. Contradiction Agent checks conflicts when needed.
5. Human approval is requested if required.
6. Context Agent applies approved update.
7. Provenance Agent records update if relevant.

## Update Proposal

```json
{
  "target_file": "memory/CURRENT_CLAIMS.md",
  "update_type": "downgrade_claim",
  "summary": "Change validated-pocket wording to candidate-region wording.",
  "evidence": ["reports/md_validation_100ns_2026-05-23/md_validation_summary.json"],
  "affected_claim_ids": ["CLAIM-0001"],
  "affected_artifact_ids": ["ART-0001"],
  "requires_human_approval": true,
  "reason_human_approval_required": "Major claim change caused by validation evidence."
}
```

## Update Types

- `add_fact`
- `revise_fact`
- `deprecate_fact`
- `add_claim`
- `downgrade_claim`
- `upgrade_claim`
- `reject_claim`
- `add_artifact`
- `mark_artifact_stale`
- `mark_artifact_invalid`
- `add_human_decision`
- `add_bug`
- `resolve_bug`
- `add_reviewer_risk`
- `update_validation_status`

## Human Approval Required

- Claim strength upgrades.
- Major claim downgrades affecting paper direction.
- Dataset/split protocol changes.
- Contradictory validation interpretation.
- Compute approvals.
- Submission approval.

## Stale Propagation Triggers

- Data changes.
- Split changes.
- Preprocessing code changes.
- Feature definition changes.
- Model code changes.
- Checkpoint changes.
- Metric code changes.
- MD analysis code changes.
- Known bug affecting outputs.
- Claim wording changes affecting figures or paper.
