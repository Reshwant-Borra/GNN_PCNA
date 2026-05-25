# ResearchOS Local Monitoring Dashboard

## Overview

A local browser dashboard that visualises the ResearchOS agent workflow in real time. It reads from the event log emitted by the orchestrator and requires no changes to the MCP bridge, CLI, or Telegram gateway.

```
orchestrator.py  ──emit()──►  data/dashboard_events.ndjson    (live SSE feed)
                          \─► reports/research_os/runs/<wf>/<ts>/transcript.jsonl
                                       │
                              dashboard/server.py  (FastAPI, port 7765)
                              ├── GET /events/stream            SSE tail
                              ├── GET /api/state
                              ├── GET /api/runs
                              ├── GET /api/run/{workflow}/{ts}
                              ├── GET /api/transcripts          (list)
                              ├── GET /api/transcripts/{workflow}/{ts}
                              ├── GET /api/agent-registry       (parsed AGENT_REGISTRY.md)
                              ├── GET /api/workflow-registry
                              ├── GET /api/claims
                              ├── GET /api/artifacts
                              └── GET /api/graph                (nodes + edges payload)
                                       │
                              dashboard/static/index.html
                              (D3.js force-simulation + Tailwind, no build step)
```

The 2026-05 upgrade replaced the rigid 5-column layout with an Obsidian-style force-directed graph:

- **Center node**: `master_orchestrator` (pinned).
- **Halo**: 21 agents arranged by D3 force simulation (`forceLink` + `forceManyBody` + `forceCollide`). Drag to reposition; nodes stay where you drop them.
- **Additional node types** (toggleable via filter chips): `memory`, `registry`, `gate`, `workflow`.
- **Tabs**: Graph · Logs / Transcript · Memory · Runs. The Logs tab streams the per-run JSONL transcript; the Memory tab browses `research_os_memory/*.md`.
- **Routing strip**: surfaces the live `routing_decision` / `routing_confidence` / `routing_reason` and shows the `claude-fallback` badge when set.

## Quick Start

```bash
python dashboard/start.py
# open http://127.0.0.1:7765
```

Options:

```
--port      Port to listen on (default: 7765)
--host      Bind host (default: 127.0.0.1)
--repo-root Path to ResearchOS repo root (default: cwd)
```

## Files

| Path | Purpose |
|------|---------|
| `research_os/events/__init__.py` | Package; exports `emit`, `init_emitter` |
| `research_os/events/emitter.py` | Thread-safe NDJSON append singleton |
| `dashboard/server.py` | FastAPI backend |
| `dashboard/start.py` | CLI entry point (argparse + uvicorn) |
| `dashboard/static/index.html` | Single-file D3.js + Tailwind frontend |
| `data/dashboard_events.ndjson` | Append-only event log (created at runtime) |

## Event Log

The emitter appends one JSON line per event to `data/dashboard_events.ndjson`. Each line has the shape:

```json
{
  "ts": "2026-05-24T23:00:00.123456+00:00",
  "type": "<event_type>",
  "workflow_id": "a1b2c3d4",
  ...event-specific fields...
}
```

### Event Types

| `type` | When emitted | Key fields |
|--------|-------------|------------|
| `workflow_started` | Start of `execute_plan()` | `workflow_name`, `selected_agents`, `required_gates`, `risk_level` |
| `agent_started` | Before each `agent.run()` | `agent_id`, `agent_index`, `total_agents` |
| `agent_completed` | After each `agent.run()` | `agent_id`, `status`, `confidence`, `summary`, `findings[]`, `gate_updates[]`, `human_review_required`, `blocks_pipeline` |
| `agent_error` | On agent crash | `agent_id`, `error_message` |
| `gate_updated` | After each gate-status merge | `gate`, `new_status`, `old_status`, `updated_by_agent`, `reason` |
| `workflow_completed` | End of `execute_plan()` | `blocked`, `block_reason`, `gate_status{}`, `applied_updates_count`, `pending_updates_count` |

The file is never truncated — it accumulates across runs. The SSE endpoint replays the full history on every (re)connect so the browser always reconstructs correct state.

## Backend API

All endpoints served on the same port as the frontend.

| Method | Path | Returns |
|--------|------|---------|
| `GET` | `/events/stream` | `text/event-stream` — SSE tail of `dashboard_events.ndjson` |
| `GET` | `/api/state` | Current gate status, memory file headers, registry entry counts |
| `GET` | `/api/runs` | List of up to 50 recent workflow runs (newest first) |
| `GET` | `/api/run/{workflow}/{ts}` | Full `result.json` for one run |
| `GET` | `/api/run/{workflow}/{ts}/plan` | `plan.json` for one run |
| `GET` | `/api/memory/{filename}` | Raw content of a canonical memory file |

## Frontend

Single HTML file with no build step. CDN dependencies:
- **Tailwind CSS** (`cdn.tailwindcss.com`) — styling
- **D3.js v7** (`d3js.org/d3.v7.min.js`) — agent workflow graph

### Layout

```
┌──────────────────────────────────────────────────────────┐
│  ResearchOS Dashboard  [workflow name]  [● LIVE / ○ off] │
│  Progress bar                                            │
├────────────────────────┬─────────────────────────────────┤
│  Agent Workflow Graph  │  10 Gate badges                  │
│  (D3 SVG, 5 columns)   ├─────────────────────────────────┤
│  Click node = details  │  Selected / active agent detail  │
├────────────────────────┴─────────────────────────────────┤
│  Blockers / Human Approval strip (hidden when empty)     │
├──────────────────────────────────────────────────────────┤
│  Run History (collapsible table)                         │
└──────────────────────────────────────────────────────────┘
```

### Agent Graph

21 agents laid out in 5 static columns (no force simulation):

| Column | Group |
|--------|-------|
| 0 | Context & Audit (3 agents) |
| 1 | Data & Code Audit (5 agents) |
| 2 | Science & Evaluation (7 agents) |
| 3 | Communication & Paper (5 agents) |
| 4 | Orchestrator (1 agent) |

Node colours by status:

| Status | Colour |
|--------|--------|
| `not_started` | slate (gray) |
| `queued` | blue |
| `active` | yellow + pulsing ring |
| `pass` | green |
| `warning` | orange |
| `fail` | red |
| `blocked` | dark red |
| `inconclusive` | violet |

Cubic-Bezier arrows connect the selected agents for the current run, showing the exact workflow path chosen by the router.

### Page Reload / Late Join

The SSE endpoint always replays the entire event log before tailing. The frontend state machine reconstructs full graph state from history, so reloading mid-run (or after) always shows correct status.

## Orchestrator Changes

`research_os/orchestrator.py` was modified to import and call the emitter. No logic was changed — only telemetry calls were added:

1. `import uuid` added at top
2. `from research_os.events import emit, init_emitter` added
3. `init_emitter(self.repo_root)` called in `__init__`
4. 6 `emit()` calls in `execute_plan()`: workflow_started, agent_started, agent_error, agent_completed, gate_updated (per gate), workflow_completed

## Dependencies

No new packages required. FastAPI (`0.136.1`) and uvicorn (`0.47.0`) were already installed in the Python 3.11 environment.
