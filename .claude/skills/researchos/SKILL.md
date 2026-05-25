# ResearchOS Conversational Control

Use this skill whenever the user asks about ResearchOS, research validity,
claims, paper wording, metrics, MD validation, figures, training, leakage,
preprocessing, provenance, reviewer readiness, or project status.

## Workflow

1. Call the `researchos.route_request` MCP tool for the user's prompt.
2. If the route selects more than one agent, requires gates, or has high or
   critical risk, call `researchos.run_request` unless the route says human
   approval is required.
3. If human approval is required, explain the approval reason and do not execute
   the workflow unless the user explicitly approves.
4. Explain results conversationally from the structured fields:
   selected agents, gate status, blockers, human review, report path, and next
   actions.
5. Do not treat a pass from one agent as publication readiness. Respect blocked,
   failed, stale, or warning gate status.

## Explicit Commands

For named workflows, call `researchos.run_workflow`:

- `full_audit`
- `training_eval`
- `metric_verification`
- `md_validation`
- `claim_audit`
- `submission_readiness`

For long-running compute or subprocess work, use `researchos.submit_compute_intent`.
Do not bypass the approval queue for risky or long-running compute.

