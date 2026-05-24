# Experiment Schema

## Experiment Entry

```json
{
  "experiment_id": "EXP-0001",
  "created_at": "",
  "updated_at": "",
  "created_by_agent": "",
  "title": "",
  "purpose": "",
  "hypothesis_tested": "",
  "null_hypothesis": "",
  "expected_outcome": "",
  "input_artifacts": [],
  "output_artifacts": [],
  "script_or_workflow": "",
  "command": "",
  "parameters": {},
  "environment_id": "",
  "git_commit": "",
  "status": "planned|approved|running|completed|failed|invalid|superseded",
  "metrics": {},
  "actual_outcome": "",
  "interpretation": "",
  "failure_modes": [],
  "evidence_classification": "supports_claim|partially_supports_claim|inconclusive|weakens_claim|contradicts_claim|does_not_address_claim",
  "associated_claims": [],
  "gate_results": {},
  "human_approval": {
    "required": false,
    "decision_id": "",
    "status": "not_required|pending|approved|rejected"
  },
  "notes": ""
}
```

## Required Before Running

- Purpose.
- Hypothesis.
- Null hypothesis.
- Inputs.
- Script or workflow.
- Parameters.
- Expected output.
- Interpretation plan.
- Failure criteria.
- Human approval if expensive.

## Completion Rule

An experiment is not complete until:

- Outputs are registered.
- Metrics are interpreted.
- Gates updated.
- Claim impact recorded.
- Follow-up actions listed.
