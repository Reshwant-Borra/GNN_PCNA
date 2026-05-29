# Human Intervention Model

## Principle

The human acts as principal investigator, not manual coder.

The system should automate routine planning, code work, audits, metrics, figures, claim checks, and reviewer simulation. It should escalate only when scientific judgment, cost, irreversibility, or disagreement requires PI decision.

## Approval Required

Human approval is mandatory for:

- Final research question.
- Final hypothesis.
- Dataset and split protocol.
- Major compute runs.
- Cloud spending.
- MD launch.
- Irreversible artifact deletion.
- Major claim changes.
- Contradictory validation interpretation.
- Biological claim with weak evidence.
- Final paper submission.
- Final figures.
- Any decision where agents materially disagree.

## Approval Not Normally Required

No human approval is normally needed for:

- Reading files.
- Creating audit reports.
- Running lightweight tests.
- Drafting plans.
- Drafting safe wording.
- Proposing memory updates.
- Computing hashes.
- Marking suspected stale artifacts.

## Approval Request Format

```text
Human approval required: <decision>

Why:
- <reason>

Evidence:
- <artifact or memory reference>

Options:
- Approve
- Reject
- Revise

Default if no approval:
- Do not proceed.
```

## Escalation Levels

- Level 0: no human needed.
- Level 1: notify human.
- Level 2: approval required.
- Level 3: adjudication required due to disagreement or contradiction.
- Level 4: human stop required for submission, public strong claim, or deletion.

## Decision Registry

Every human decision should record:

- Decision ID.
- Date.
- Decision maker.
- Request.
- Options.
- Decision.
- Rationale.
- Evidence.
- Affected claims/artifacts.
- Follow-up.
