# Agent Output Schema

Every agent must return structured output.

```json
{
  "agent": "",
  "agent_id": "",
  "task": "",
  "status": "pass|warning|fail|blocked|inconclusive|not_applicable",
  "confidence": 0.0,
  "summary": "",
  "evidence_used": [
    {
      "type": "memory|registry|source_code|artifact|literature|human_decision|experiment|log",
      "id": "",
      "path": "",
      "description": ""
    }
  ],
  "findings": [
    {
      "finding_id": "",
      "severity": "critical|high|medium|low|info",
      "title": "",
      "description": "",
      "evidence": [],
      "affected_claims": [],
      "affected_artifacts": [],
      "required_action": "",
      "blocks_pipeline": false
    }
  ],
  "risks": [],
  "required_actions": [],
  "gate_updates": [],
  "artifacts_created": [],
  "artifacts_updated": [],
  "artifacts_to_mark_stale": [],
  "claims_supported": [],
  "claims_weakened": [],
  "claims_contradicted": [],
  "human_review_required": false,
  "human_review_reason": "",
  "updates_to_memory": [],
  "next_recommended_agents": [],
  "machine_readable_notes": {}
}
```

## Required Fields

- `agent`
- `agent_id`
- `task`
- `status`
- `confidence`
- `summary`
- `evidence_used`
- `findings`
- `required_actions`
- `human_review_required`
- `updates_to_memory`

## Validation Rules

- Status must be allowed.
- Confidence must be 0 to 1.
- Severity values must be allowed.
- Human review reason must be present when human review is true.
- Referenced claims and artifacts should resolve when registries exist.
