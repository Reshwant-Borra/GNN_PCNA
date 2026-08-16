# Human Review Gates

## Purpose

Prevent automation-driven scientific drift. Agents and scripts may prepare evidence, but humans must approve major scientific freeze points.

## Hard Rules

- Human review is mandatory for split freeze, label freeze, first training run, first PCNA prediction interpretation, first MD interpretation, preliminary claims, and final claims.
- A human approval must cite the evidence packet reviewed.
- No agent can approve a gate that changes scientific meaning.
- Human approval does not override failed evidence; it records a reviewed decision.

## Mandatory Human Gates

| Gate | Required before | Evidence packet |
|---|---|---|
| Source-of-truth freeze | Any Phase 2 build | source audit, canonical paths |
| Dataset adoption | Graph generation | dataset registry, benchmark limitations, lifecycle log |
| Split freeze | Graph generation | split audit, leakage audit |
| Label freeze | Graph generation/training | label audit, biological data sanity review |
| First graph release | Training | graph audit, provenance manifest |
| First training run | Training | readiness gate, red-team pretraining audit, null baseline plan |
| First PCNA prediction | PCNA interpretation | evaluation audit, PCNA mapping, interpretability plan |
| First MD interpretation | MD conclusions | pre-MD reality check, MD manifest |
| Preliminary claims | Reports/figures | claim audit, uncertainty register |
| Final claims | External writing | publication readiness and final audit |

## Forbidden Actions

- Letting an agent mark these gates PASS alone.
- Treating a chat message as approval without recording date, reviewer, evidence, and decision.
- Approving a gate while unresolved FAIL items exist.

## Required Checks

- Review decision ID.
- Reviewer name or role.
- Date.
- Evidence packet paths.
- Decision: approved, approved with limitations, rejected.
- Limitations and follow-up actions.

## Examples Of Failure

- A split is frozen by a script even though homolog leakage is unresolved.
- First PCNA prediction is interpreted by a coding agent without human review.
- Final claims are generated from metrics and MD text without a human claim audit.

## Prevention

ResearchOS and any build scripts must require a human-decision record for mandatory gates.

## Compliance Artifact

`reports/phase2/human_review_log.md`.

## If The Rule Fails

Freeze downstream artifacts as `NO_HUMAN_GATE_DO_NOT_USE` until the gate is reviewed and recorded.
