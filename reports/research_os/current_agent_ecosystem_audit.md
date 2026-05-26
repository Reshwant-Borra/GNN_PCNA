# ResearchOS — Current Agent Ecosystem Audit

Last updated: 2026-05-25
Updated by: Claude (Phase 1 discovery pass)
Status: current

This report is the Phase 1 deliverable of the autonomy upgrade. It maps **everything that exists today** in ResearchOS so the redesign that follows is grounded in reality, not speculation. The audit is read-only and changes nothing in the running system.

---

## 0. TL;DR — what the system actually is right now

ResearchOS today is **two orthogonal layers wired together by a router and an MCP shim**:

1. **Scientific layer** (`research_os/`) — 21 agents, 10 gates, 6 workflows, 9 canonical memory files, 7 registries, an Ollama-backed semantic router, a gate-enforcing orchestrator, a per-run transcript writer, and an FastAPI/D3 dashboard.
2. **Compute layer** (`agents/`) — 16 named *intents*, each a thin subprocess dispatcher around an existing pipeline script (`scripts/run_pipeline.py`, `src.training.train`, MD scripts, packagers, etc.) with role gates and an approval queue.

The infrastructure surrounding the agents — routing, gates, transcripts, MCP, dashboard, registries — is **substantial and well-built**. The agents themselves are not.

> **Core finding.** Every "scientific agent" is a single-pass deterministic regex/heuristic scanner. None call an LLM, none plan, none retry, none choose tools, none collaborate. They walk memory + registries + repo files in one function and emit findings. The router decides which inert scanners to run, the orchestrator runs them in order, and the gates filter the result. The intelligence in the system lives in the **router**, not in the agents. The user's intuition is correct: today's agents are thin Python-script wrappers, not autonomous specialists.

This is fixable without touching the scientific model code, without breaking MCP contracts, and without collapsing the two-orchestrator design. The redesign should build a **goal-driven agent framework** that the existing 21 agents migrate onto incrementally, plus a **higher-level controller** that decomposes broad research goals into sub-tasks and dispatches the existing scientific orchestrator as one of several executors.

---

## 1. Discovered ecosystem inventory

### 1.1 Scientific agents (21, in `research_os/agents/`)

All 21 share the `BaseAgent` contract: receive an `AgentContext` (memory + registry stores) + a `ContextPacket` (task + intents + risk + selected memory files), return an `AgentOutput` (status + confidence + findings + risks + gate updates + memory update proposals + next-agent hints). All `run(packet)` methods are **synchronous, single-pass, no I/O loops, no LLM calls, no subprocess spawning**.

| # | agent_id | File | Pattern (what `run()` actually does) | Autonomy | Flexibility |
|---|---|---|---|---|---|
| 1 | `master_orchestrator` | `orchestrator_role.py` | Builds a short summary of the routing decision + a couple of `info` findings if a claim is in play. Never invoked via routing — graph-view only. | 1/10 | 1/10 |
| 2 | `context_source_truth` | `context_provenance.py` | Iterates the 9 canonical memory files, checks presence + `status` header, captures git state, emits one finding per missing/needs-review file. | 2/10 | 2/10 |
| 3 | `research_design` | `science_evaluation.py` | Substring-checks `PROJECT_CANONICAL_STATUS.md` for required headings (hypothesis, null, success/failure, falsification, controls, baselines). | 2/10 | 1/10 |
| 4 | `biological_realism` | `science_evaluation.py` | Iterates `claim_registry`, regex-matches a hard-coded `_BIO_DISALLOWED` list, flags strongly_supported claims without evidence. | 2/10 | 2/10 |
| 5 | `literature_web` | `science_evaluation.py` | Counts `source_registry` entries. **No external search.** Returns one finding if the registry is empty. | 1/10 | 1/10 |
| 6 | `dataset_integrity` | `data_audit.py` | Reads `DATASET_REGISTRY.md`, checks for 5 hard-coded section headings, looks for `pending` markers. | 2/10 | 2/10 |
| 7 | `leakage_split` | `data_audit.py` | Reads the "Split protocol" section of `DATASET_REGISTRY.md`, looks for 6 hard-coded leakage-check tokens. Cross-checks artifact_registry metrics → split-artifact dependency. | 3/10 | 2/10 |
| 8 | `preprocessing_auditor` | `data_audit.py` | Finds graph artifacts in registry, flags stale/invalid ones. | 2/10 | 2/10 |
| 9 | `code_builder` | `communication.py` | **Stub.** Returns a static "patch plan deferred" `AgentOutput`. Never edits code. | 1/10 | 1/10 |
| 10 | `scientific_code_review` | `data_audit.py` | Walks `*.py`, regex-matches 5 suspicious patterns (NotImplementedError, hardcoded markers, swallowed exceptions, skipped tests) + 2 stale-checkpoint patterns. | 3/10 | 2/10 |
| 11 | `testing_environment` | `data_audit.py` | Checks `tests/` exists; if `run_pytest` in `allowed_actions`, shells out to pytest and tails the output. **Only agent that runs an external subprocess.** | 3/10 | 3/10 |
| 12 | `model_training` | `science_evaluation.py` | Reads `MODEL_REGISTRY.md`, checks for "Current canonical checkpoint" heading, finds checkpoints with status=current. | 2/10 | 1/10 |
| 13 | `metrics_statistics` | `science_evaluation.py` | Globs `**/*metric*.json`, flattens, regex-checks for AUROC/AUPRC/CI keys. Cross-checks claim_registry for AUROC mentions. | 3/10 | 2/10 |
| 14 | `compute_planning` | `science_evaluation.py` | Regex `\b100\s*ns|\d{2,}\s*ns|cloud|gpu|expensive|budget\b` on the prompt itself; sets `human_review_required=True` for big compute. | 2/10 | 1/10 |
| 15 | `validation_skeptic` | `science_evaluation.py` | Extracts one regex-matched "Evidence classification" line from `VALIDATION_STATUS.md`. **Cannot actually classify MD evidence** — only reads what a human wrote. | 2/10 | 1/10 |
| 16 | `contradiction_hunter` | `context_provenance.py` | Cross-references `VALIDATION_STATUS.md` classification ↔ `claim_registry.claim_strength`. Greps paper drafts for 9 hard-coded disallowed phrases. Walks artifact_registry for current-but-dependency-is-stale. | 4/10 | 3/10 |
| 17 | `provenance_artifacts` | `context_provenance.py` | Walks `artifact_registry`, checks paper-grade entries have `git_commit`, `command`, `created_at`. Flags current-but-upstream-stale. | 3/10 | 2/10 |
| 18 | `paper_claim` | `communication.py` | Globs `**/*.md` matching paper hints, regex-matches `_DISALLOWED_PAPER_WORDING`. Checks claim_registry for `allowed_wording`/`disallowed_wording` lists. | 3/10 | 2/10 |
| 19 | `visual_evidence` | `communication.py` | Globs `**/*.{png,pdf,svg,jpg}`, diffs against `artifact_registry` figure entries → flags unregistered figures. | 2/10 | 2/10 |
| 20 | `reviewer_collaboration` | `communication.py` | Returns a hard-coded list of 12 reviewer questions. Extracts "Open reviewer risks" section from memory file. | 1/10 | 1/10 |
| 21 | `document_knowledge_ingestion` | `communication.py` | Checks `agents/ingest.py` exists and `source_registry` is readable. **Does not actually ingest** — that's done by `agents/ingest.py` invoked through the compute layer. | 2/10 | 1/10 |

**Aggregate autonomy score: 2.3 / 10. Aggregate flexibility score: 1.8 / 10.**

What this *means* in practice:
- An agent told "research GNN architectures" cannot pull a paper, summarize it, or update a memory file beyond a fixed-shape append.
- An agent told "verify the AUROC" cannot recompute the AUROC from a checkpoint + dataset — it can only check that a JSON file *mentions* AUROC + AUPRC keys.
- An agent told "did MD validate the pocket?" cannot read trajectories — it reads a memory file that a human wrote that contains an "Evidence classification" line.
- No agent can detect its own failure and re-plan. Failures surface as `status="fail"` + a `blocks_pipeline=True` finding, and the workflow stops.

### 1.2 Compute-gateway intents (16, in `agents/orchestrator.py:INTENTS`)

These are a different layer entirely: subprocess dispatchers with role gates and an approval queue, fronted by an Ollama-backed natural-language intent parser for Telegram.

| Intent | Risk | Long-running | Underlying script |
|---|---|---|---|
| `status` | low | no | in-process snapshot |
| `crawl` | medium | yes | `agents/pcna_crawler.py` *(not in tree on this branch)* |
| `verify` | medium | yes | `agents/gemma_verifier.py` *(not in tree on this branch)* |
| `vault` | medium | no | `agents/obsidian_writer.py` *(not in tree on this branch)* |
| `fetch` | medium | yes | `src.data_processing.fetch_structures` |
| `graphs` | medium | yes | `scripts/build_graphs.py` |
| `split` | high (risky) | no | `scripts/make_split.py` |
| `train` | high (risky) | yes | `src.training.train` |
| `eval` | medium | no | `src.evaluation.score_pockets` |
| `inference` | medium | yes | `scripts/bulk_inference.py` |
| `verify_claims` | medium | yes | `scripts/verify_all_claims.py` |
| `pipeline` | high (risky) | yes | `scripts/run_pipeline.py` |
| `docker_build` | medium | yes | `agents/docker_packager.py` |
| `bundle` | medium | yes | `agents/docker_packager.py` bundle |
| `shell` | critical (risky) | yes | arbitrary bash |
| `ingest` | medium | no | `agents/ingest.py` |

**Pattern.** Each intent has a `build_cmd` lambda that returns an argv. The orchestrator either starts a thread (`subprocess.Popen` + stream stdout into an `Event` bus + write `run.log`) or holds the task in `AWAITING_APPROVAL` until the OWNER approves.

This layer has *more* runtime autonomy than the scientific layer (subprocesses, threading, event bus, approval queue, cancellable tasks, artifact directory) but it is **still single-shot per intent** — no chaining, no replanning, no awareness of the scientific gates or memory.

Several referenced scripts (`agents/pcna_crawler.py`, `agents/gemma_verifier.py`, `agents/obsidian_writer.py`) are **not present** on the current branch — those intents are dangling. Worth verifying before the demo phase.

### 1.3 Workflows (6, in `research_os/workflows/`)

| Workflow | Agents (count) | Gates required | Replanning? | Recovery? |
|---|---|---|---|---|
| `full_audit` | 18 | all 9 standard gates | no — fixed agent list | no |
| `training_eval` | 9 | dataset, leakage, preprocessing, code, evaluation | no | no |
| `md_validation` | 6 | validation | no | no |
| `claim_audit` | 8 | claim, validation | no | no |
| `metric_verification` | 5 | evaluation, leakage | no | no |
| `submission_readiness` | 12 | all 10 incl. submission | no | no |

Every workflow is a **fixed intent set + extra_agents tuple → `run_workflow()`** which builds an `OrchestrationPlan` and hands it to the orchestrator's `execute_plan()`. The orchestrator iterates agents in order, applies/holds memory updates, rolls up gate statuses, blocks on `blocks_pipeline=True`, and writes the bundle. **There is no loop. There is no "this agent's output was insufficient, run it again with more context."** If `dataset_integrity` reports `blocked`, the workflow exits with `blocked=True`.

### 1.4 Routing layer (`research_os/routing/`)

Surprisingly sophisticated for what it feeds:

- **Keyword classifier** (`intent.py`): 18 regex patterns mapping to `INTENT_CLASSES`. Always runs, deterministic guardrail.
- **Semantic router** (`semantic_router.py`): Ollama `gemma3:4b` via `/api/chat`. Reads `AGENT_REGISTRY.md` + `ROUTING_GUIDE.md` once per process, builds a structured prompt with a per-agent block + a routing-guide block + the user prompt, asks for strict JSON, validates and coerces. Returns `SemanticRouterResult` or `None`.
- **Claude fallback** (`claude_fallback.py`): flag-only by default; opt-in Anthropic API mode.
- **Merge + prune** (`router.py`): union of semantic + keyword agent lists, then `_prune_inappropriate_agents` strips out-of-scope picks (e.g. `validation_skeptic` on a literature query). Confidence floor 0.55, high 0.75, triggers Claude fallback flag.
- **Risk classifier** (`risk.py`), **gate resolver** (`gates.py`), **human classifier** (`human.py`), **context-packet builder** (`context_builder.py`).
- **Eval harness** (`eval/routing_benchmark.py` + `eval/routing_eval.py`): ~70 hand-curated cases across 20 categories, including destructive and compound prompts. Real benchmark — not a toy.

**Strength.** This is the only part of the system that *thinks*. The Ollama prompt is well-engineered with rules + few-shot.

**Weakness.** The router's output is consumed *only* to select which inert agents to run. The decision is "which scanners to fire", not "what plan should we execute". The semantic router's free-form `reasoning_summary` is thrown away beyond logging — no agent ever reads it.

### 1.5 Memory & registries

- **9 canonical markdown memory files** (`research_os_memory/`): `PROJECT_CANONICAL_STATUS.md`, `CURRENT_CLAIMS.md`, `KNOWN_BUGS_AND_RISKS.md`, `HUMAN_DECISIONS.md`, `VALIDATION_STATUS.md`, `DATASET_REGISTRY.md`, `MODEL_REGISTRY.md`, `COMPUTE_REGISTRY.md`, `REVIEWER_RISK_REGISTER.md`. Each has a standard header (`Last updated`, `Updated by`, `Status: current|needs_review|stale`).
- **7 JSON registries** (`research_os_registries/`): `artifact`, `claim`, `decision`, `environment`, `experiment`, `issue`, `source`. Append-only with closed-vocab validation.
- **Memory update protocol.** Agents emit `MemoryUpdate` proposals; the orchestrator runs them through `apply_memory_update()`, which either writes (if `requires_human_approval=False`) or queues in `pending_memory_updates`. Hard guarantee: agents never touch the disk directly.
- **KB-as-context layer** (`research_os_memory/`): `CODEBASE_MAP.md`, `AGENT_REGISTRY.md`, `ROUTING_GUIDE.md`, `WORKFLOW_REGISTRY.md`, `TOOL_REGISTRY.md`, `RECENT_RUN_SUMMARY.md`. Token-efficient summaries the router and humans both read.

This is the **most reusable part of the codebase** for the autonomy upgrade. The append-only registries + canonical files + standardized headers already give us state, history, and provenance — three things autonomous agents need.

### 1.6 Transcripts & events

- **NDJSON event stream** (`data/dashboard_events.ndjson`): live SSE feed for the dashboard.
- **Per-run transcripts** (`reports/research_os/runs/<workflow>/<ts>/transcript.jsonl` + `summary.md` + `result.json`): created by `TranscriptWriter`, registered with the global emitter for the duration of a run, then unregistered. The transcript is the audit trail.
- **Event vocabulary** (`schemas/vocab.py:EVENT_TYPES`): 24 types including the original 6 + routing, ollama_router_started/completed, claude_fallback, agent_queued, tool_called/tool_result, subtask_started/completed, memory_update_proposed/applied, blocker_detected, human_approval_requested.

`tool_called`, `tool_result`, `subtask_started`, `subtask_completed` are **already in the vocabulary but never emitted by any agent** — the schema is ready for the autonomy upgrade.

### 1.7 MCP integration

- `.mcp.json` registers a stdio MCP server (`research_os.integrations.claude_code.mcp_server`).
- Dependency-free: pure stdlib, custom Content-Length frame parser, 6 tools (`route_request`, `run_request`, `run_workflow`, `get_report`, `submit_compute_intent`, `approve_or_deny`).
- All tools return compact dicts; per-run transcripts are referenced by path.
- MCP signatures are stable; the project's CLAUDE.md explicitly says "additive changes only."

### 1.8 Dashboard

- FastAPI + D3 force-simulation graph on port 7765.
- Center node = `master_orchestrator`. Halo = 21 agents. Filter chips for memory/registry/gate/workflow nodes.
- Tabs: Graph, Logs/Transcript, Memory, Runs.
- API: `/api/state`, `/api/runs`, `/api/transcripts/{workflow}/{ts}`, `/events/stream` (SSE).

Already wired for streaming events — a strong substrate for visualizing autonomous-agent activity.

### 1.9 Tests

15 pytest files. ~119 tests run in ~6s. Coverage:

| Test file | Surface |
|---|---|
| `test_memory.py` | Memory store init + updates |
| `test_orchestrator.py` | Gate enforcement, blocking, no self-approval |
| `test_registries.py` | CRUD + validation + dup-reject |
| `test_router.py` | Routing logic |
| `test_schemas.py` | Closed-vocab + dataclass shape |
| `test_scientific_guardrails.py` | Disallowed wording, leakage checks, stale artifacts |
| `test_stale_propagation.py` | Issue → artifact invalidation chain |
| `test_claude_code_integration.py` | MCP harness |
| `test_semantic_router.py` | Ollama with mocked HTTP |
| `test_routing_semantic_cases.py` | End-to-end routing |
| `test_transcripts.py` | Per-run JSONL creation + readback |
| `test_memory_kb.py` | KB completeness for the semantic router |
| `test_routing_regressions.py` | 10 critical routing behaviors |

`conftest.py` sets `RESEARCHOS_DISABLE_SEMANTIC=1` so the keyword path is exercised by default; semantic tests use injected fake backends so CI never hits real Ollama.

**Coverage gap.** No tests for autonomy (because no autonomy exists). No tests for retry, memory-aware multi-step reasoning, handoff, or long-running task recovery — these will need to be added with the framework in Phase 6.

### 1.10 External tool surfaces (current and theoretical)

| Tool | Where wired | Notes |
|---|---|---|
| `git` | `tools/git.py`, `agents/orchestrator.py` | State capture, repo bundling |
| `pytest` | `agents/orchestrator.py`, `testing_environment` agent | Already shelled out by one agent |
| `docker` | `agents/docker_packager.py` | Optional build step |
| `wormhole` | `agents/wormhole_client.py` | Secure file transfer, Telegram side |
| `ollama` (`/api/chat`) | semantic router, intent parser | Local LLM, `OLLAMA_HOST` envvar |
| `nvidia-smi` | env capture, intent parser | GPU snapshot |
| `openmm` | MD workflows (external) | Not called by scientific agents — only via compute intent |
| `pdfplumber`, `bs4` | `agents/ingest.py` | Optional deps for PDF/HTML |

**No agent currently calls an LLM during its `run()`.** No agent crawls the web. No agent uses a browser. No agent invokes another agent. Tool integration exists at the system boundary, not inside agent reasoning.

---

## 2. What the system does well today

These are real strengths that the redesign should **preserve and build on**, not replace:

1. **Closed-vocabulary contracts everywhere.** Every status, severity, intent, gate, artifact type, claim strength, evidence classification, and event type is enumerated in `schemas/vocab.py` with a runtime validator. New code that produces invalid values fails immediately. This is what makes registries safe to append to.
2. **Gate enforcement with no self-approval.** `Orchestrator._agent_is_self_approving` enforces that producer agents (`code_builder`, `model_training`, `metrics_statistics`, `validation_skeptic`, `paper_claim`, `visual_evidence`) cannot upgrade their own gates to `pass` until a reviewer agent has run. This is the right safety primitive — autonomous agents will inherit it.
3. **Append-only registries + structured memory updates.** Agents propose updates; the orchestrator applies. Updates that require human approval are *held* in `pending_memory_updates`, not silently dropped. Human-approval boundary is real.
4. **Per-run transcripts.** Every run produces a self-contained `transcript.jsonl + summary.md + result.json` bundle the dashboard and MCP can read after the fact. The event vocabulary already includes `tool_called`, `tool_result`, `subtask_started`, `subtask_completed` — wired for autonomy.
5. **Routing benchmark.** ~70 hand-curated cases across 20 categories — this is real test infrastructure for behavioral changes.
6. **MCP contract is clean.** 6 tools, dependency-free stdio server, compact return payloads. Adding fields is allowed; removing them is not. The autonomy upgrade can add `goal`, `plan`, `step`, `confidence`, `coverage` keys to existing responses without breaking the Claude Code integration.
7. **Two-orchestrator separation.** The scientific orchestrator handles routing + gates; the compute orchestrator handles subprocess execution + approval queue. Both have a place. The redesign **must not collapse them**.
8. **Semantic router with falls-back-everywhere design.** Ollama unavailable → keyword path. JSON malformed → keyword path. Confidence low → keyword union + Claude flag. No silent failure.
9. **KB-as-context discipline.** `CODEBASE_MAP.md` + `AGENT_REGISTRY.md` + `ROUTING_GUIDE.md` are token-efficient summaries that the semantic router and humans both read. This is the right pattern for an autonomous controller to consume.
10. **Provenance hooks are everywhere** — `git`, env snapshot, file hashes, lineage walker. Autonomous agents that produce artifacts can lean on these immediately.

---

## 3. Where the system is weak

### 3.1 Per-agent weaknesses

Universal across the 21 scientific agents:

- **No goal-driven execution.** Every agent's `run(packet)` accepts a `ContextPacket` and produces an `AgentOutput`. There is no "objective", no "success criterion", no "until-condition". The agent does one fixed-shape pass and exits.
- **No internal planning.** No agent decomposes its task into sub-steps.
- **No multi-step reasoning.** No `for step in plan: act; observe; evaluate` loop anywhere.
- **No tool selection.** No agent ever picks between options ("should I read memory or shell pytest?"). The `testing_environment` agent is the closest — it gates on `"run_pytest" in packet.allowed_actions` — but that's a yes/no flag set upstream, not a tool choice.
- **No intermediate evaluation.** Findings are emitted at the end. There is no "this result is suspicious, let me re-check it" pattern.
- **No retry / recovery.** A try/except in `Orchestrator.execute_plan` catches agent crashes and converts them to `status="fail"` with `human_review_required=True`. The workflow continues with the *next* agent — no re-attempt, no alternate strategy.
- **No persistent state across runs.** Each agent run is independent. The transcript captures it, but the agent itself starts fresh.
- **Structured output is shape-only.** `AgentOutput` is a real dataclass with validation, but the *content* is whatever the agent's `_output(...)` call passed in. Most agents return summary strings that are reconstructions of `len(findings)` counts.
- **No handoff.** `next_recommended_agents` exists on `AgentOutput` but the orchestrator ignores it — agents run in the order the router specified, full stop.
- **No confidence estimation.** `confidence` is a hard-coded float per agent (`0.6`, `0.7`, `0.85`...). It does not vary by evidence quality.
- **No coverage scoring.** Agents do not ask "did I look at enough evidence?" The audit either finishes or it doesn't.
- **No self-critique.** Agents have no notion of "this finding might be wrong because…"
- **No final validation.** The orchestrator's "blocked" / "pass" verdict is a roll-up of gate statuses. No agent checks "was the goal actually accomplished?"

### 3.2 Workflow weaknesses

- **Fixed agent lists.** Each workflow is a tuple. If the dataset registry is empty, `full_audit` still runs `model_training` and `metrics_statistics` — both of which produce vacuous findings.
- **No replanning.** If `dataset_integrity` reports `blocked` and the workflow exits, there is no "let me look at why and try with a different scope" — the workflow just stops.
- **No conditional branching.** Workflows are pure sequences. A claim-audit that needed a literature search to resolve a contradiction cannot kick one off.
- **Static gate requirements.** Gates are computed from the keyword intents at routing time. If a workflow discovers mid-run that it needs an additional gate, there is no path to add it.
- **No long-running task support.** Workflows are designed to finish in one pass; nothing in the scientific layer can pause/resume.

### 3.3 Routing weaknesses

- **Router output is discarded after agent selection.** The `routing_reason` and `ollama_response_raw` make it to the transcript but **no agent ever consumes them**. The LLM's understanding of the request stops at the agent list.
- **No dynamic re-routing.** If during execution an agent surfaces "actually, this needs the leakage_split agent", there is no path back to the router to revise the plan.
- **`requires_claude_fallback=True` is a flag, not an action.** It surfaces via MCP but nothing in the running workflow waits for or consumes the Claude response.

### 3.4 Cross-cutting failure modes

- **Missing referenced files.** `agents/orchestrator.py` references `agents/pcna_crawler.py`, `agents/gemma_verifier.py`, `agents/obsidian_writer.py` — none present on this branch. The intents are dangling.
- **`inspect-registries` schema mismatch.** Per `CLAUDE.md`: pre-existing `artifact_registry.json` uses `"artifacts"` key, validator expects `"entries"`. Not introduced by recent work, but a live papercut.
- **Empty source_registry.** `literature_web` always finds zero sources because nothing has been ingested.
- **No external knowledge ingestion in any agent.** "Research GNN architectures" prompts route correctly but the agents that get fired (`literature_web`, `document_knowledge_ingestion`) do nothing except count what's already in the registry.
- **Compute-gateway approval queue is in-process only.** No persistence. If the MCP server restarts, pending approvals are lost.
- **`code_builder` is a no-op stub.** Any code-build intent ends with "patch plan deferred" — useful as a placeholder but blocks the autonomy goal.

### 3.5 Risks the audit found (not the project's scientific risks — the *system's* risks)

| Risk | Why it matters for the upgrade |
|---|---|
| Hard-coded regex lists for disallowed wording, leakage tokens, suspicious code patterns | Brittle to phrasing variants. Any LLM-backed equivalent must keep these as a regex *backstop* — never replace. |
| Single-threaded synchronous workflow execution | A long-running autonomous agent will block the workflow. Need async/streaming. |
| In-memory compute task state | Restarts lose pending approvals. Needs persistence if autonomous workflows are queued across sessions. |
| Telegram + intent_parser uses `gemma3:4b` over `http://host.docker.internal:11434` | Local-only; cannot run on a machine without Ollama. Autonomous agents that need LLM reasoning must inherit the same falls-back-everywhere discipline. |
| MCP server is stdio, not HTTP | Fine for Claude Code; harder to multiplex if multiple clients need access. Out of scope this phase. |

---

## 4. Opportunities for the autonomy upgrade

These rank by leverage — what gives the biggest jump in autonomy with the least disruption.

### Tier 1 — high leverage, low disruption

1. **Add an `AutonomousAgent` base class** in `research_os/agents/autonomous.py` that wraps a planning loop (`plan → act → observe → evaluate → revise`) and exposes the same `run(packet) -> AgentOutput` interface, so it can be slotted into the existing orchestrator without changing `execute_plan()`. This is the central enabler.
2. **Add a `ToolRegistry`** in `research_os/tools/registry.py` that surfaces existing helpers (`git`, `env`, `hashing`, `provenance`) + new ones (memory read/write, registry read/write, web_search, web_fetch, llm_chat, run_workflow, run_compute_intent) as named, structured-input/structured-output tools. The autonomous agent picks tools from this registry.
3. **Add an `AgentMemory` layer** keyed by `agent_id` that records goals, sub-tasks, prior findings, retry attempts, and confidence trajectories across runs. Stored under `research_os_memory/agent_state/<agent_id>.jsonl`.
4. **Emit `subtask_started` / `subtask_completed` / `tool_called` / `tool_result` events** from the autonomous loop. The vocabulary is already there; the dashboard will visualize them with no code changes once it sees them in the transcript.
5. **Add a `Goal` schema** alongside `ContextPacket` that captures what the agent is trying to achieve, success criteria, and stop conditions.

### Tier 2 — high leverage, moderate disruption

6. **Migrate the 21 agents one-by-one** to the autonomous base. Preserve current behavior as the "fast path" (single-pass scan still runs by default); enable the planning loop only when the prompt or workflow asks for depth. Start with `literature_web` (currently the most vacuous) and `document_knowledge_ingestion` (currently a no-op) — those have the biggest immediate win.
7. **Add an `AutonomousController` on top of the scientific orchestrator** that accepts a *goal* (not a prompt), decomposes it into sub-tasks, dispatches the existing `Orchestrator` for each sub-task, monitors progress, and re-plans on failure. The controller is *additive* — existing MCP tools (`route_request`, `run_request`) keep working unchanged; we add a new tool (`pursue_goal`) for goal-driven entry.
8. **Add a `WorkflowGraph` schema** so workflows can be defined as a DAG of agent invocations with conditional edges, replacing the fixed-list `_FULL_AUDIT_AGENTS` tuple pattern. Existing fixed workflows compile down to trivial linear graphs.
9. **Wire `next_recommended_agents` into the orchestrator** so an agent can request a follow-up agent be added to the plan (subject to gate / risk rules).

### Tier 3 — strategic, larger changes

10. **External knowledge tools.** Wire `literature_web` to PubMed / arXiv / Semantic Scholar via web_fetch; have `document_knowledge_ingestion` actually call `agents/ingest.py` and update `source_registry` end-to-end inside the agent's run.
11. **Browser/crawler integration** for `literature_web` follow-ups (deferred — needs a Playwright/Selenium harness; not a Phase 2 deliverable).
12. **Long-running task support.** Async agents; a separate persistent task table; the autonomous controller can re-enter a paused workflow.
13. **Confidence calibration.** Confidence becomes a function of evidence count, classifier agreement, and retry success — not a hard-coded float.

---

## 5. Per-component opportunity table

| Component | Current state | Opportunity | Risk if not done |
|---|---|---|---|
| `BaseAgent` | One-shot `run()`, no loop | Add `AutonomousAgent` subclass with `plan/act/observe` loop | No autonomy; every agent stays a script |
| 21 agents | Deterministic scanners | Migrate to autonomous base; keep current scan as fallback | Agents stay inert |
| `Orchestrator.execute_plan` | Linear iteration | Add `WorkflowGraph` support for conditional edges + re-planning | Workflows stay brittle |
| Router | Selects agents; output discarded | Pass `routing_reason` + `ollama_response_raw` to agents as part of `ContextPacket` | Agents miss the LLM's framing |
| `ContextPacket` | Input only | Add `goal`, `success_criteria`, `stop_conditions`, `budget` (steps/time/tokens) | No way for agents to know when "enough" |
| `AgentOutput` | Output only | Add `next_subgoals`, `tools_called`, `evidence_coverage`, `self_critique`, `confidence_trajectory` | Structured outputs stay shallow |
| `Memory` (canonical files) | Fact pages | Add per-agent state under `agent_state/<id>.jsonl` (separate from canonical 9 files) | Agents forget across runs |
| `Registries` | Append-only JSON | Keep as-is; add `agent_state` registry for cross-run agent memory | Already well-suited |
| Transcripts | Per-run JSONL | Already supports new event types — start emitting them | Dashboard misses autonomy activity |
| Dashboard | D3 graph + transcripts | Add a "subtask tree" view for autonomous-agent runs | Less visibility into agent reasoning |
| MCP | 6 tools | Add `pursue_goal(goal, budget?, repo_root?)` + `get_agent_state(agent_id)` | Claude Code can't drive autonomous flows |
| Compute gateway | Subprocess dispatcher | Keep as-is; expose as a `tool` to autonomous agents | Autonomous agent can't run training/inference |
| Workflows (6) | Fixed agent lists | Recompile to `WorkflowGraph`s with conditional edges + fallbacks | Workflows can't adapt |
| Tests | 119 tests, all single-shot | Add autonomy / retry / memory-persistence / handoff suites | Regressions silent |
| Eval harness | Routing benchmark (~70 cases) | Add `goal_pursuit_benchmark` (corpus build, gap analysis, synthesis) | No way to measure autonomy gains |
| `code_builder` | No-op stub | Implement as autonomous patch-plan-then-apply with reviewer hand-off | Code-build intents stay dead |
| `literature_web` | Counts registry | Implement as autonomous corpus builder over PubMed/arXiv → ingest | Literature gate stays unfillable |
| `document_knowledge_ingestion` | Checks `ingest.py` exists | Wrap the ingest CLI as a tool the agent actually calls | Source registry stays empty |
| `validation_skeptic` | Reads human-written classification | Read MD trajectories + compute its own classification | Validation stays human-bottlenecked |
| `metrics_statistics` | Greps JSON files for keys | Optionally recompute metrics from `checkpoint + split + dataset` | Metric verification is shallow |
| `master_orchestrator` agent | Graph-view-only role | Could become the entry point for goal-driven flows | Underused as designed |

---

## 6. Demonstration target (Phase 7 preview)

The user's stated demo is a **GNN-PCNA Phase 2 corpus build + synthesis**. The audit suggests this can be done with the existing infrastructure plus the autonomy upgrade:

1. **Goal** → "Build a deep corpus on cryptic pocket detection, GNN protein-pocket methods, MD-evidence interpretation standards, and AOH1996 chemistry. Synthesize what's known, identify gaps for Phase 2, and produce a structured research artifact."
2. **Autonomous controller** decomposes into: (a) literature sweep, (b) ingest, (c) gap analysis vs. `CURRENT_CLAIMS.md` + `REVIEWER_RISK_REGISTER.md`, (d) synthesis draft, (e) self-critique, (f) reviewer-simulation pass.
3. **Specialized agents** do the work: upgraded `literature_web` + `document_knowledge_ingestion` for the sweep, `biological_realism` + `validation_skeptic` for the gap analysis, a new `synthesis_writer` agent for the draft, `contradiction_hunter` + `reviewer_collaboration` for the critique.
4. **Recovery surfaces:** If PubMed search returns 0 results for a query, the agent re-formulates. If a fetched PDF won't parse, the agent tries the abstract from the API metadata.
5. **Outputs:** `research_corpus/PHASE2_CORPUS.md`, `research_corpus/gap_analysis.md`, `research_corpus/synthesis_draft.md`, plus `source_registry` entries for every paper, plus a transcript bundle.
6. **Constraints:** No scientific model code is touched. No MD is run. No claims are upgraded above `moderately_supported` without human approval.

This is feasible with the current `agents/ingest.py`, the existing source registry, and the autonomy framework. It needs (a) an actual external search tool (web_fetch + a PubMed/arXiv query strategy), (b) the autonomous-agent loop, (c) a new `synthesis_writer` agent or an upgraded `paper_claim`.

---

## 7. Constraints that must be preserved (carry into Phase 2+)

These come from `CLAUDE.md` and the audit. The redesign must not break any of them:

1. **Do not collapse the two orchestrators.** `research_os/orchestrator.py` (scientific) and `agents/orchestrator.py` (compute) stay separate.
2. **MCP tool signatures are additive only.** Add fields; never remove.
3. **`apply_memory_update` is the only path to canonical memory.** Autonomous agents inherit this.
4. **No self-approval.** `_PRODUCER_REVIEWERS` map holds. Autonomous agents that override gates must respect it.
5. **Disallowed paper wording is enforced by `paper_claim` + `biological_realism`.** Autonomous synthesis must not bypass.
6. **Claims above `moderately_supported` require human approval.** No autonomous escalation.
7. **Don't touch Telegram** (`agents/telegram_gateway.py`, `configs/telegram_gateway.yaml`).
8. **Don't modify scientific model code** (per user instruction). The autonomy upgrade is *around* the model, not inside it.
9. **Closed vocabularies in `schemas/vocab.py`** are the source of truth. New event types extend the tuple — existing entries do not move.
10. **Falls-back-everywhere.** Ollama down → keyword path. Web search down → cached registry. LLM JSON malformed → deterministic fallback. The autonomous framework inherits this discipline.

---

## 8. Recommended next steps (handoff to Phase 2)

The audit recommends the redesign be sequenced as:

1. **Phase 2 (design):** Draft the `AutonomousAgent` interface, `Goal` / `Plan` / `Step` schemas, `ToolRegistry` API, `AgentMemory` layer, `WorkflowGraph` schema, and `AutonomousController` interface. Get user sign-off on the shape **before** writing implementation code, because (a) MCP-stability matters and (b) the framework will be inherited by 21 agents.
2. **Phase 3 (framework):** Implement the framework end-to-end with one trivial reference agent that demonstrates the planning loop, retries, tool selection, memory persistence, and transcript emission.
3. **Phase 4 (migration):** Migrate agents in waves — start with `literature_web` and `document_knowledge_ingestion` (highest immediate value), then the high-traffic agents (`paper_claim`, `validation_skeptic`, `contradiction_hunter`), then the rest.
4. **Phase 5 (controller):** Build the `AutonomousController` and the `pursue_goal` MCP tool, leaving the existing `route_request` / `run_request` unchanged.
5. **Phase 6 (tests + resilience):** Add the autonomy / retry / memory / handoff / long-running test suites. Verify the system survives missing workflows, missing files, incompatible interfaces.
6. **Phase 7 (demo):** Run the GNN-PCNA Phase 2 corpus build end-to-end; produce structured artifacts; capture the run as the reference autonomous workflow.

---

## Appendix A — Files inspected during this audit

`research_os/agents/{base,__init__,context_provenance,science_evaluation,data_audit,communication,orchestrator_role}.py`, `research_os/orchestrator.py`, `research_os/routing/{router,semantic_router,intent}.py`, `research_os/schemas/{core,context,vocab}.py`, `research_os/memory/store.py`, `research_os/transcripts/writer.py`, `research_os/workflows/{__init__,runner,full_audit,training_eval,md_validation,claim_audit,metric_verification,submission_readiness}.py`, `research_os/integrations/claude_code/{service,mcp_server}.py`, `research_os/eval/routing_benchmark.py`, `agents/{orchestrator,intent_parser,ingest,docker_packager}.py`, plus `research_os_memory/*.md`, `tests/*.py`, `reports/research_os/**`, `.mcp.json`.

## Appendix B — What the audit deliberately did *not* examine

- Telegram gateway (`agents/telegram_gateway.py`, `configs/telegram_gateway.yaml`) — out of scope per CLAUDE.md.
- Wormhole client (`agents/wormhole_client.py`) — file-transfer only, not part of agent logic.
- Scientific model code (`src/`, `scripts/`, `checkpoints/`) — out of scope per user instruction.
- Dashboard frontend (`dashboard/static/index.html`) — surface only, no logic to redesign.
