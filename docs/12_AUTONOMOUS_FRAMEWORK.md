# 12 — Autonomous Agent Framework (Phase 3)

Last updated: 2026-05-26
Status: implemented — see `research_os/autonomous/` + `research_os/tools/{registry,builtin,web,llm}.py`

This document describes the framework added in Phase 3 of the autonomy
upgrade. It is **purely additive** on top of the existing ResearchOS layers
documented in `01_SYSTEM_ARCHITECTURE.md` through `11_MCP_INTEGRATION.md`. No
existing agent, workflow, gate, or MCP signature was modified.

---

## 1. Why

The Phase 1 audit (`reports/research_os/current_agent_ecosystem_audit.md`)
found that the 21 scientific agents are single-pass deterministic scanners
with aggregate autonomy 2.3/10 and flexibility 1.8/10. The infrastructure
around them is strong (router, gates, transcripts, MCP, dashboard, memory,
registries) but the agents themselves can't plan, retry, choose tools, or
collaborate.

Phase 3 adds a goal-driven planning framework agents can opt into. Phase 4
will migrate the existing 21 agents onto it; Phase 5 will extend the
controller; Phase 7 will demonstrate the whole thing end-to-end on the
GNN-PCNA Phase 2 research campaign.

---

## 2. Design principles (carry forward to Phase 4+)

1. **Additive, not destructive.** With autonomy off, the system behaves
   exactly as it did before. `AutonomousAgent` subclasses `BaseAgent` and
   keeps the legacy `run(packet) -> AgentOutput` contract.
2. **Falls back everywhere.** If the planning loop crashes, the LLM is
   unreachable, the web is disabled, or any tool errors, the agent reverts
   to its deterministic scan.
3. **Bounded by budgets.** Every autonomous run carries explicit
   `max_iterations`, `max_tool_calls`, `max_failures`, and a wall-clock
   `max_seconds` cap. The first cap that trips ends the loop cleanly and
   emits `budget_exhausted`.
4. **Observable.** Every step, tool call, critique, replan, coverage check,
   and handoff emits a structured event. Transcripts capture them. The
   dashboard already supports the new event types.
5. **Profile-driven safety.** Each agent has an `AgentProfile` declaring
   its capabilities, allowed tools, autonomy level, default budget, and
   fallback behavior. The registry refuses tool calls outside the profile's
   allow-list.
6. **Two-orchestrator separation preserved.** The controller (Phase 3
   scaffold; Phase 5 full implementation) calls the scientific orchestrator
   for scientific sub-tasks and the compute orchestrator for compute
   sub-tasks. It never collapses them.
7. **Closed vocabularies extended, never reshaped.** New event types and
   step kinds are appended to the existing tuples in
   `research_os/schemas/vocab.py`. Existing values keep their positions.

---

## 3. Module layout

```
research_os/
  autonomous/
    __init__.py            # public exports
    schemas.py             # Budget, Goal, Plan, Step, StepResult, SuccessCriterion,
                           # StopCondition, CritiqueResult, CoverageCategory,
                           # CoverageResult, HandoffRequest, StepStatus
    profile.py             # AgentProfile, AutonomyLevel, DEFAULT_PROFILES (21),
                           # profile_for(agent_id)
    memory.py              # AgentMemory — append-only per-agent JSONL state
    events.py              # Typed wrappers around emit() for each new event
    coverage.py            # CoverageEstimator
    critique.py            # Critic protocol, simple_critic, make_coverage_critic,
                           # confidence_critic
    planner.py             # DeterministicPlanner, LLMPlanner
    agent.py               # AutonomousAgent + AutonomousRunResult
    controller.py          # AutonomousController + CampaignResult (scaffold)
    reference_agent.py     # ReferenceAutonomousAgent (framework demo + test target)
  tools/
    registry.py            # Tool, ToolRegistry, ToolResult
    builtin.py             # register_builtin(): memory/registry/file/glob/git/env/hash
    web.py                 # register_web(): web_fetch, web_search (PubMed/arXiv),
                           # pubmed_abstract  — gated on RESEARCHOS_ENABLE_WEB
    llm.py                 # register_llm(): llm_chat (Ollama)
                           # gated on RESEARCHOS_ENABLE_LLM_AGENTS
```

Plus 17 new event types appended to `schemas/vocab.py:EVENT_TYPES`:

```
goal_started, goal_completed, plan_created, plan_revised,
step_started, step_completed, step_failed, step_retried,
critique_started, critique_completed, replan_started, replan_completed,
coverage_evaluated, fallback_triggered, handoff_requested,
budget_exhausted, campaign_started, campaign_completed
```

---

## 4. The autonomous loop

`AutonomousAgent.run(packet)` either delegates to the deterministic scan or
runs the loop below. The decision is made by `_autonomy_enabled()`:

- profile autonomy level must be > `DETERMINISTIC`
- `RESEARCHOS_AUTONOMY_OFF` must not be set
- every env var in `profile.requires_env` must be set

If any check fails, the agent runs `_deterministic_run(packet)` and returns
that `AgentOutput` directly — autonomy is purely additive.

When the loop runs:

```
build_goal(packet)                       # subclass-specific Goal
emit goal_started + record to AgentMemory
planner.plan(goal, ...)                  # produces a Plan of Steps
emit plan_created + record

while True:
    if budget.is_exhausted(...): emit budget_exhausted; break
    next_step = pick first runnable step (honors depends_on)
    if next_step is None:
        if criteria_met or no critics: break
        run critics; if they spawned steps → replan; else break

    execute_step(next_step):
        - tool_call:        registry.call_for_profile(...)  → ToolResult
        - deterministic:    invoke subclass scan → AgentOutput → ctx_state
        - critique:         run attached critics → CritiqueResults
        - evaluate_coverage same as critique
        - sub_goal/handoff: emit handoff_requested; defer to controller
        - noop:             skip
    update ctx_state, iterations, tool_calls, failures
    emit step_started/step_completed (+ step_failed on failure)

    if next_step was critique and critique requires_replan:
        replan(...) emits replan_started/completed
```

Outputs are composed back into a valid `AgentOutput` (the orchestrator's
contract) with the full plan/step trace stored under
`machine_readable_notes.autonomous`. The status rolls up from the
deterministic scan (if it ran) or is synthesized from criteria + failure
counts. **Existing gate enforcement and no-self-approval logic are
unaffected.**

---

## 5. Critique → planner feedback loop

`make_coverage_critic` turns coverage gaps into *new tool-call steps* with
the recommended query baked in. `simple_critic` turns failed steps into
*retry steps*. The default `DeterministicPlanner.replan()` appends every
new critic-spawned step to the plan, deduped by description and filtered
through the agent profile's allow-list. The plan's `revision` increments;
events `replan_started`/`replan_completed` capture the change.

This is the critical "findings become tasks, not inert report items"
behavior the user called out in Phase 2 sign-off.

---

## 6. Agent Capability Profiles

`AgentProfile` records:

| Field | Purpose |
|---|---|
| `agent_id` | Stable identifier — same as the existing 21 |
| `capabilities` | Free-form labels (e.g. `literature_search`) |
| `allowed_tools` | Hard allow-list. The registry refuses anything else. |
| `domain_areas` | Free-form domain tags for controller dispatch |
| `autonomy_level` | `DETERMINISTIC` (0), `GUIDED` (1), `ASSISTED` (2), `FULL` (3) |
| `confidence_model` | `fixed` / `evidence_weighted` / `calibrated` |
| `handoff_targets` | Which other agents this one can hand off to |
| `failure_modes` | Known failure patterns for the planner to avoid |
| `default_budget` | `Budget` used if the caller doesn't supply one |
| `fallback_behavior` | `scan_only` / `skip` / `human` |
| `requires_env` | Env vars that must be set for the loop to run |

All 21 existing agents have a default profile in
`autonomous/profile.py:DEFAULT_PROFILES`. They ship at autonomy level
`DETERMINISTIC` so opting in is an explicit per-agent decision in Phase 4.

---

## 7. Tool registry

`ToolRegistry` enforces:

- **Unique names.** Re-registration raises.
- **Env-var gating.** Disabled tools return a clean
  `ToolResult(ok=False, error="...")` rather than raising. The planner can
  react.
- **Profile allow-list.** `call_for_profile(allowed, name, inputs)` rejects
  tools the agent's profile doesn't declare.

The registry never raises during a normal call — every error path returns
a `ToolResult`. This keeps the autonomous loop simple: any tool failure is
a step failure, not a crash.

### Built-in tools (always on)

`memory_read`, `memory_list`, `memory_propose_update`, `registry_read`,
`registry_query`, `file_read`, `glob`, `git_state`, `env_snapshot`,
`hash_file`. Memory writes flow through the existing `apply_memory_update`,
so the no-self-approval and human-approval boundaries still hold.

### Web tools (opt-in via `RESEARCHOS_ENABLE_WEB=1`)

`web_fetch`, `web_search` (PubMed / arXiv), `pubmed_abstract`. Stdlib-only
(no requests/aiohttp), best-effort, returns `{ok: False, error: ...}` on
network failures.

### LLM tool (opt-in via `RESEARCHOS_ENABLE_LLM_AGENTS=1`)

`llm_chat` over local Ollama, shares the `OLLAMA_HOST` /
`RESEARCHOS_OLLAMA_MODEL` envvars with the semantic router. Test backends
plug in via `set_llm_backend(callable)` so CI never hits real Ollama.

---

## 8. AgentMemory

Each agent gets its own append-only JSONL log at
`research_os_memory/agent_state/<agent_id>.jsonl`. Separate from the 9
canonical human-curated memory files so autonomous activity never pollutes
the project source-of-truth pages.

API: `record(type, payload)`, `recent(limit)`, `for_goal(goal_id)`,
`recent_goals(limit)`, `failure_pattern(last_n)`. The last one summarizes
recent step failures by signature so a planner can adapt ("we've tried
this tool 3 times, try a different approach").

Writes are silent on failure — corrupt or unwritable files never block
the agent.

---

## 9. Controller (Phase 3 scaffold)

`AutonomousController.pursue_goal(goal, sub_goals=?)`:

1. Decomposes the top-level goal into sub-goals (Phase 3: trivial; Phase 5
   wires real decomposition).
2. For each sub-goal, looks up an `AgentFactory` by `agent_id`
   (`sub_goal.inputs["target_agent"]`, else `default_agent_id`).
3. Instantiates the agent, runs it, collects the `AgentOutput`.
4. Records `SubGoalOutcome`s; missing factories are `skipped`,
   crashes are `error`ed, both surfaced in the `CampaignResult`.
5. Rolls up to an aggregate status (`pass` / `warning` / `fail`).
6. Emits `campaign_started` / `campaign_completed`.

The controller never spawns subprocesses — compute sub-goals are surfaced
as `HandoffRequest` payloads for the caller to forward to
`agents/orchestrator.py`. The two-orchestrator boundary is preserved.

---

## 10. Tests (72 new)

| File | Coverage |
|---|---|
| `test_autonomous_schemas.py` | Budget exhaustion (each dimension), Goal / SuccessCriterion evaluation, Plan / Step round-trip |
| `test_autonomous_memory.py` | Append, persist, load, filter, failure_pattern, corrupt-line skip, silent failure |
| `test_autonomous_tools.py` | Registry uniqueness, env-gating, profile gating, input mismatch, runner exceptions, built-in memory/registry/glob/file_read, LLM injected backend, LLM fallback, web disabled-by-default, sandboxed file_read |
| `test_autonomous_planner.py` | Deterministic shape, replan append, allow-list drop, LLM fallback when disabled, LLM uses backend when enabled, malformed-JSON fallback, disallowed-tool drop |
| `test_autonomous_critique_coverage.py` | CoverageEstimator score/gaps/full-coverage, simple_critic happy/failure/no-success, coverage_critic spawns targeted follow-ups, confidence_critic thresholds |
| `test_autonomous_agent.py` | Deterministic profile skip, kill switch, requires_env gate, full loop end-to-end, plan trace in notes, agent memory writes, tool_called events, max_iterations budget, loop-crash fallback, double-fail clean error, missing _deterministic_run raises |
| `test_autonomous_controller.py` | Default agent run, missing factory, crashed factory, crashed agent run, multiple sub-goals with one orphan |

`python -m pytest tests -q` — **208 passed in ~5s** (136 existing + 72 new).
Zero regressions.

---

## 11. What did NOT change

To minimize blast radius:

- `research_os/orchestrator.py` — untouched.
- `agents/orchestrator.py` (compute gateway) — untouched.
- The 21 scientific agents — untouched (Phase 4 migrates them).
- The 6 prebuilt workflows — untouched.
- `research_os/integrations/claude_code/{service,mcp_server}.py` — untouched.
  MCP signatures are stable; a `pursue_goal` MCP tool will be added in
  Phase 5 alongside the controller upgrade.
- `research_os/routing/*` — untouched. The semantic router still emits
  `OrchestrationPlan`s with the same fields.
- `research_os/memory/store.py` — untouched. Per-agent autonomous memory
  lives in a new `agent_state/` subdir, never in the canonical 9 files.
- `research_os/tools/__init__.py` — untouched. New tool modules are
  imported directly by the autonomous layer; no re-export changes.
- All existing tests — pass unchanged.

---

## 12. Phase 4 / 5 / 7 forward references

- **Phase 4** migrates the 21 agents onto `AutonomousAgent`, starting with
  the three currently dead/vacuous ones (`literature_web`,
  `document_knowledge_ingestion`, `code_builder`) where the upgrade is
  pure win. Each migration:
  1. Subclasses `AutonomousAgent`.
  2. Implements `_deterministic_run(packet)` = the existing scan.
  3. Bumps `autonomy_level` in the profile (and `allowed_tools`).
  4. Adds agent-specific critics + an optional override of `build_goal`.
- **Phase 5** replaces the controller scaffold with a real goal
  decomposer + dynamic agent selector + multi-agent verification pass.
  Adds a `pursue_goal` MCP tool that takes a `Goal` payload and returns a
  `CampaignResult` reference.
- **Phase 6** adds long-running task tests, resilience tests against
  missing workflows / files, and a `goal_pursuit_benchmark` alongside the
  existing routing benchmark.
- **Phase 7** runs an autonomous GNN-PCNA Phase 2 research-and-engineering
  campaign: 200+ source corpus + synthesis + multi-agent verification +
  self-healing infrastructure scaffolding + Phase 2 readiness assessment.
  The campaign exercises every framework feature documented here.
