---
# TEMPLATE — do not write here directly
# Fill this schema in working memory, then save the completed instance as:
#   reports/phase2/handoff_YYYYMMDD.md
# where YYYYMMDD is the session date.
handoff_date: YYYY-MM-DD
session_agent: claude-code | codex | human
task_completed: one-line description of the primary task this session completed
---

# Agent Handoff — [YYYYMMDD]

## What Was Done This Session

- [bullet: specific files created]
- [bullet: scripts run and their outcomes]
- [bullet: decisions made or policies drafted]
- [bullet: audit findings]
- [bullet: registries updated]

## What Changed in Project State

Blockers removed:
- [list any blockers that were resolved this session, or "none"]

New blockers discovered:
- [list any new blocking issues found, or "none"]

## Files Created or Modified

| Action | Path |
|---|---|
| created | [path] |
| modified | [path] |

## Blockers Remaining

[Copy the current `## Current Blockers` list from `.memory/PROJECT_STATE.md`, updated
to reflect this session's changes.]

## Next Task Recommendation

**Task:** [single sentence describing the most important next action]
**First file to read:** [exact path to the file that starts that work]
**Why:** [one sentence explaining why this is the highest priority]

## Validation Commands Run

| Command | Result |
|---|---|
| `python scripts/phase2_foundation_check.py` | PASS / FAIL / not run |
| `python scripts/validate_dataset_intake.py` | PASS / FAIL / not run |
| [other script] | [result] |

## Provenance

- Governance paths consulted: [list, e.g. docs/scientific_governance/16_CODING_AGENT_RULES.md]
- Wiki pages updated: [list, or "none"]
- Confidence: high / medium / low
- Evidence status: verified / inferred / uncertain / speculative
