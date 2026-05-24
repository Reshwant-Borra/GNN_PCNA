# Memory File Design

## Canonical Markdown Files

Implement these files in the runtime memory folder:

```text
PROJECT_CANONICAL_STATUS.md
CURRENT_CLAIMS.md
KNOWN_BUGS_AND_RISKS.md
HUMAN_DECISIONS.md
VALIDATION_STATUS.md
DATASET_REGISTRY.md
MODEL_REGISTRY.md
COMPUTE_REGISTRY.md
REVIEWER_RISK_REGISTER.md
```

## PROJECT_CANONICAL_STATUS.md

Required sections:

- Project goal.
- Current research question.
- Current hypothesis.
- Current status summary.
- Dataset status.
- Model status.
- Validation status.
- Paper status.
- Current blockers.
- Next steps.

## CURRENT_CLAIMS.md

Required sections:

- Accepted claims.
- Partially supported claims.
- Hypothesis-generating claims.
- Unsupported claims.
- Contradicted claims.
- Allowed wording.
- Disallowed wording.
- Claims requiring human approval.

Every claim must map to `claim_registry.json`.

## KNOWN_BUGS_AND_RISKS.md

Required sections:

- Critical bugs.
- Open bugs.
- Resolved bugs.
- Scientific risks.
- Stale artifacts caused by bugs.
- Artifacts requiring regeneration.

## HUMAN_DECISIONS.md

Append-only. Each decision needs:

- Decision ID.
- Date.
- Decision maker.
- Request.
- Options.
- Decision.
- Rationale.
- Evidence.
- Affected artifacts/claims.
- Follow-up.

## VALIDATION_STATUS.md

Required sections:

- Validation question.
- Structural evidence.
- MD evidence.
- Metrics used.
- Evidence classification.
- Contradictions.
- Safe interpretation.
- Disallowed interpretation.
- Required follow-up.

## File Header Standard

Every memory file should begin:

```markdown
# <Title>

Last updated: <ISO timestamp>
Updated by: <agent or human>
Status: current|needs_review|stale
```
