# Recent Run Summary

Last updated: 2026-05-25T00:00:00Z
Updated by: research_os.bootstrap
Status: current

Rolling log of the most recent ResearchOS runs. Auto-updated by `transcripts/writer.py` at workflow completion; capped at the last 20 entries (oldest at the bottom).

Use this file to quickly see what's been happening recently without scanning `reports/research_os/`. The dashboard also surfaces this via the Runs tab.

---

## Schema

Each entry follows this template:

```
### <UTC timestamp>  ·  <workflow>  ·  <run_id>

- prompt: "<truncated prompt>"
- routing_decision: semantic | keyword_only | merged | low_confidence
- routing_confidence: 0.00 — 1.00
- selected_agents: <count> (`agent_a, agent_b, ...`)
- gate_status: <pass>/<fail>/<blocked>/<warning>
- blocked: true|false  ·  reason: <...>
- human_review_required: true|false  ·  reason: <...>
- artifacts_created: <count>
- memory_updates_applied: <count>
- transcript: reports/research_os/<workflow>/<ts>/transcript.jsonl
- next_action: <one-line>
```

---

## Recent runs

(none yet — first run will appear here)
