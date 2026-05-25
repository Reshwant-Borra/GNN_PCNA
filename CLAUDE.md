# Claude Code working notes for ResearchOS

You are working on **ResearchOS** — a gate-enforcing research operating system for the GNN-PCNA project. Your job is to route prompts through scientific agents, never silently cross PI approval boundaries, and keep the project's claims proportional to the evidence.

## Read these FIRST, before opening source files

Token-efficient knowledge base lives at `research_os_memory/`:

| File | When to read |
|---|---|
| `CODEBASE_MAP.md` | First. Tells you which module does what without scanning the package. |
| `AGENT_REGISTRY.md` | When choosing/explaining agents. 21 agents, one ~150-token entry each. |
| `ROUTING_GUIDE.md` | When asked "which agents will run?" or routing seems wrong. |
| `WORKFLOW_REGISTRY.md` | When invoking or explaining one of the 6 prebuilt workflows. |
| `TOOL_REGISTRY.md` | When you need internal helpers (git capture, hashing, Ollama, etc.). |
| `RECENT_RUN_SUMMARY.md` | When asked "what happened recently?" |
| `PROJECT_CANONICAL_STATUS.md` + `CURRENT_CLAIMS.md` + `VALIDATION_STATUS.md` + `KNOWN_BUGS_AND_RISKS.md` + `REVIEWER_RISK_REGISTER.md` | Project state. Read before answering scientific questions. |

> **Token-saving rule.** Before running `Grep` / `Read` on the package, check whether `CODEBASE_MAP.md` and the relevant registry already answer the question. They almost always do.

Refresh the auto-discoverable parts with:
```
python -m research_os refresh-memory
python -m research_os update-codebase-map
python -m research_os update-agent-registry
python -m research_os query-memory "<topic>"
```

## Two orchestrators — don't collapse them

| Module | Role |
|---|---|
| `research_os/orchestrator.py` (class `Orchestrator`) | **Scientific orchestrator.** Routes agents, enforces 10 gates, applies memory/registry updates. This is what `mcp__researchos__route_request` / `run_request` call. |
| `agents/orchestrator.py` (class `Orchestrator`) | **Compute gateway.** Subprocess task dispatcher with role gates + approval queue. This is what `mcp__researchos__submit_compute_intent` / `approve_or_deny` call. |

These are different layers. **Never replace one with the other.** `agents/` also contains the Telegram gateway (`agents/telegram_gateway.py`, `agents/intent_parser.py`); leave Telegram alone unless explicitly asked.

## Routing pipeline (post-upgrade)

`Router.route(message)` runs:

1. **Keyword classifier** — always runs (`research_os/routing/intent.py`). Deterministic guardrail.
2. **Ollama semantic router** — primary classifier (`research_os/routing/semantic_router.py`). Reads `AGENT_REGISTRY.md` + `ROUTING_GUIDE.md`. Returns structured JSON. Defaults to `gemma3:4b` via local Ollama at `OLLAMA_HOST` (default `http://localhost:11434`).
3. **Merge** — union of agent lists, `context_source_truth` always first, `contradiction_hunter` appended for high/critical risk.
4. **Claude fallback** — `requires_claude_fallback=true` is surfaced via MCP for the Claude Code session to act on. Anthropic API mode opt-in via `RESEARCHOS_CLAUDE_FALLBACK_API=1` + `ANTHROPIC_API_KEY`.
5. **Plan emission** — `OrchestrationPlan` includes new fields: `routing_decision`, `routing_confidence`, `routing_reason`, `ollama_response_raw`, `requires_claude_fallback`, `selected_workflow`. All optional with safe defaults.

Kill switches: `RESEARCHOS_DISABLE_SEMANTIC=1` → keyword-only path (tests use this).

## Transcripts

Every run writes:
```
reports/research_os/runs/<workflow>/<timestamp>/
    transcript.jsonl     # per-event log (routing, agents, gates, blockers, approvals)
    summary.md           # executive summary
    result.json          # full WorkflowResult
```

Event types in `research_os.schemas.vocab.EVENT_TYPES`. The dashboard's Logs/Transcript tab reads these files via `/api/transcripts/{workflow}/{ts}`.

## Dashboard

`python dashboard/start.py` → http://127.0.0.1:7765. Obsidian-style D3 force-simulation graph:
- Center: `master_orchestrator`
- Halo: 21 agents
- Other node types (filter chips): memory, registry, gate, workflow
- Click any node → right detail panel
- Tabs: Graph · Logs/Transcript · Memory · Runs

API surface added: `/api/graph`, `/api/agent-registry`, `/api/workflow-registry`, `/api/claims`, `/api/artifacts`, `/api/transcripts`, `/api/transcripts/{workflow}/{ts}`. Existing endpoints unchanged.

## MCP tools (don't change signatures)

| Tool | Backend |
|---|---|
| `mcp__researchos__route_request` | `research_os.integrations.claude_code.service.route_request` |
| `mcp__researchos__run_request` | …`run_request` — writes a transcript |
| `mcp__researchos__run_workflow` | …`run_named_workflow` |
| `mcp__researchos__get_report` | …`get_report` |
| `mcp__researchos__submit_compute_intent` | …→ `agents/orchestrator.py` |
| `mcp__researchos__approve_or_deny` | …→ `agents/orchestrator.py` |

Response payloads gained optional keys (`routing_decision`, `routing_confidence`, `requires_claude_fallback`, `transcript_path`). Never remove keys; only add.

## Hard rules

- No agent self-approves its own gate (see `_PRODUCER_REVIEWERS` in `orchestrator.py`).
- Memory mutations go through `apply_memory_update()` only.
- `requires_human_approval=true` → execution paused until a PI signs off, unless `force_if_human_required=true` is set on `run_request`.
- Disallowed paper wording (e.g. "validated cryptic pocket", "MD proves opening") is enforced by `paper_claim` and `biological_realism`. Don't add a claim above `moderately_supported` without explicit MD evidence classification.
- Don't touch Telegram (`agents/telegram_gateway.py`, `configs/telegram_gateway.yaml`).
- `inspect-registries` may crash on the pre-existing `artifact_registry.json` schema (uses `"artifacts"` key, validator expects `"entries"`) — pre-existing, not introduced here. Investigate before changing.

## When in doubt

1. Read `CODEBASE_MAP.md` and the relevant entry in `AGENT_REGISTRY.md`.
2. Run `python -m research_os route "<the user's prompt verbatim>"` and look at the JSON.
3. If `routing_decision == "keyword_only"`, Ollama is down — start it (`ollama serve`) or run with `RESEARCHOS_DISABLE_SEMANTIC=1` to skip semantic routing intentionally.
4. If `requires_claude_fallback == true`, the system is asking for your judgement. Respond in conversation; don't blindly call `run_request`.

## Tests

`python -m pytest tests -q` — full suite. 119 tests, ~6s. Mocks all external network calls (Ollama, etc.). Set `RESEARCHOS_DISABLE_SEMANTIC=1` in conftest so the keyword path is exercised by default; semantic router has dedicated tests using injected fake backends.
