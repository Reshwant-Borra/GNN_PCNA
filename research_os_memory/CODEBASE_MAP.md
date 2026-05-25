# Codebase Map

Last updated: 2026-05-25T00:00:00Z
Updated by: research_os.bootstrap
Status: current

A compact map of the ResearchOS repo. **Read this before scanning source files** — most questions can be answered from this map plus `AGENT_REGISTRY.md` and `ROUTING_GUIDE.md`. Only escalate to reading code when the map is insufficient.

Regenerate the auto-discoverable parts with:
```
python -m research_os refresh-memory
python -m research_os update-codebase-map
```

---

## Top-level layout

```
ResearchOS/
├── research_os/                 # Scientific orchestrator package (THE core)
├── agents/                      # Compute gateway (DIFFERENT — see below)
├── dashboard/                   # FastAPI + D3 monitoring dashboard
├── research_os_memory/          # Markdown KB (this file lives here)
├── research_os_registries/      # JSON registries (artifact, claim, experiment, source, issue, decision, environment)
├── reports/research_os/         # Per-workflow run output (plan.json, result.json, report.md, summary.md, transcript.jsonl)
├── data/                        # dashboard_events.ndjson + research data
├── tests/                       # pytest suite
├── configs/                     # YAML configs (e.g. telegram_gateway.yaml — NOT touched this phase)
├── docs/                        # Architecture docs
└── .mcp.json                    # MCP server registration for Claude Code
```

**Critical distinction:**
- `research_os/orchestrator.py` = SCIENTIFIC orchestrator. Routes agents, enforces gates, applies memory updates. **Use this for `route_request` / `run_request`.**
- `agents/orchestrator.py` = COMPUTE gateway. Subprocess task dispatcher with role gates / approval queue. **Use this for `submit_compute_intent` / `approve_or_deny`.**

These are two different layers — never replace one with the other.

---

## research_os/ — scientific orchestrator package

| Module | Purpose |
|---|---|
| `__main__.py` | CLI entry point. Subcommands: `route`, `run`, `audit`, `training-eval`, `verify-metrics`, `validate-md`, `claim-audit`, `readiness`, `bootstrap`, `inspect-memory`, `inspect-registries`, `refresh-memory`, `query-memory`. |
| `orchestrator.py` | `Orchestrator` class. `route()` → `OrchestrationPlan`; `execute_plan()` → `WorkflowResult`. Enforces gates, no self-approval, emits events. |
| `routing/router.py` | `Router.route(message)` — top-level routing entry point. Calls `_semantic_route()` (Ollama) then merges with keyword fallback. |
| `routing/semantic_router.py` | `OllamaSemanticRouter` — primary classifier. Reads `AGENT_REGISTRY.md` + `ROUTING_GUIDE.md`. |
| `routing/claude_fallback.py` | Claude fallback: flag-only by default, optional Anthropic API mode. |
| `routing/intent.py` | Keyword/regex intent classifier (18 patterns). Used as deterministic guardrail. |
| `routing/agents.py` | `_AGENT_MAP`: intent → agent tuple. Guardrail seed. |
| `routing/gates.py` | Per-intent gate requirements. |
| `routing/risk.py` | Risk classifier (low/medium/high/critical). |
| `routing/human.py` | `requires_human_review()` — PI approval triggers. |
| `routing/context_builder.py` | `build_context_packet()` — assembles `ContextPacket` for agents. |
| `routing/_llm_json.py` | Shared LLM-JSON extraction helper (used by semantic_router). |
| `agents/__init__.py` | `AGENT_REGISTRY` dict — source of truth for the 21 agent IDs. |
| `agents/base.py` | `BaseAgent`, `AgentContext`, helpers. |
| `agents/context_provenance.py` | ContextSourceTruth, ContradictionHunter, ProvenanceArtifacts. |
| `agents/science_evaluation.py` | ResearchDesign, BiologicalRealism, LiteratureWeb, MetricsStatistics, ModelTraining, ComputePlanning, ValidationSkeptic. |
| `agents/data_audit.py` | DatasetIntegrity, LeakageSplit, PreprocessingAuditor, ScientificCodeReview, TestingEnvironment. |
| `agents/communication.py` | CodeBuilder, PaperClaim, VisualEvidence, ReviewerCollaboration, DocumentKnowledgeIngestion. |
| `agents/orchestrator_role.py` | MasterResearchOrchestrator (graph-view role only, not directly routed). |
| `schemas/vocab.py` | Closed vocabularies: STATUSES, INTENT_CLASSES (18), AGENT_IDS (21), GATE_STATUSES, EVENT_TYPES, etc. |
| `schemas/core.py` | `AgentOutput`, `Finding`, `GateUpdate`, `MemoryUpdate`, `EvidenceRef`. |
| `schemas/context.py` | `ContextPacket`, `OrchestrationPlan`. |
| `schemas/gates.py` | `GateName` constants (10 gates), `GateStatus`. |
| `memory/store.py` | `MemoryStore`, `MemoryUpdateProposal`, `apply_memory_update`. 9 canonical files. |
| `memory/codebase_indexer.py` | Auto-generates this file's repo map section. |
| `memory/registry_loader.py` | Parses `AGENT_REGISTRY.md` + `ROUTING_GUIDE.md` for the semantic router. |
| `registries/store.py` | `RegistryStore`. 7 registries: artifact, claim, decision, environment, experiment, issue, source. |
| `transcripts/writer.py` | Per-run JSONL transcript writer. |
| `events/emitter.py` | NDJSON event emitter (`init_emitter`, `emit`). |
| `tools/git.py` | `capture_git_state()` |
| `tools/env.py` | Environment snapshotting (Python version, pip freeze, GPU). |
| `tools/hashing.py` | File / directory content hashing. |
| `tools/provenance.py` | Artifact lineage helpers. |
| `workflows/__init__.py` | `WORKFLOWS` dict: 6 prebuilt workflows. |
| `workflows/runner.py` | Common `run_workflow()` helper. |
| `workflows/full_audit.py` | Full pipeline audit. |
| `workflows/training_eval.py` | Training + evaluation audit. |
| `workflows/md_validation.py` | MD validation. |
| `workflows/claim_audit.py` | Claim/paper audit. |
| `workflows/metric_verification.py` | Metric verification. |
| `workflows/submission_readiness.py` | End-to-end submission readiness. |
| `reports/writer.py` | Writes markdown + JSON reports. |
| `integrations/claude_code/mcp_server.py` | Dependency-free stdio MCP server. |
| `integrations/claude_code/service.py` | Implements 6 MCP tool functions. |

---

## agents/ — compute gateway (separate layer)

| Module | Purpose |
|---|---|
| `orchestrator.py` | Task dispatcher: `Intent`, `Task`, role gates, approval queue. CLI: list-intents, run, approve, deny, status. |
| `intent_parser.py` | Ollama Gemma 3:4b NLP classifier for Telegram messages → registered INTENTS. |
| `ingest.py` | Document ingestion pipeline (PDFs, markdown, transcripts → source_registry). |
| `docker_packager.py` | Docker image + repo bundling. |
| `telegram_gateway.py` | Telegram bot frontend. **Out of scope this phase.** |
| `wormhole_client.py` | Wormhole secure file transfer. |

---

## dashboard/ — FastAPI + D3 monitoring

| File | Purpose |
|---|---|
| `server.py` | FastAPI app. SSE endpoint (`/events/stream`), REST API (`/api/state`, `/api/runs`, etc.). Port 7765 default. |
| `start.py` | argparse + uvicorn launcher. |
| `static/index.html` | D3 force-simulation graph. Center: master_orchestrator. Halo: 21 agents + memory/registry/gate/workflow/report/artifact/claim nodes. Tabs: Graph, Logs/Transcript, Memory, Runs. |

---

## tests/ — pytest

| File | Purpose |
|---|---|
| `conftest.py` | Fixtures: `MemoryStore`, `RegistryStore`, `Orchestrator`. |
| `test_memory.py` | Memory store init + updates. |
| `test_orchestrator.py` | Orchestrator bootstrap + intent dispatch. |
| `test_registries.py` | Registry CRUD + schema validation. |
| `test_router.py` | Routing logic (intent classification, agent selection order). |
| `test_schemas.py` | Data model validation. |
| `test_scientific_guardrails.py` | Claim wording, leakage checks, stale artifacts. |
| `test_stale_propagation.py` | Issue → artifact invalidation chain. |
| `test_claude_code_integration.py` | Claude Code MCP harness integration. |
| `test_semantic_router.py` | Ollama router with mocked HTTP. |
| `test_routing_semantic_cases.py` | End-to-end routing for PubMed/MD/leakage/claim/compound prompts. |
| `test_transcripts.py` | Per-run JSONL transcript creation + readback. |
| `test_memory_kb.py` | Verify AGENT_REGISTRY/CODEBASE_MAP/ROUTING_GUIDE/WORKFLOW_REGISTRY exist and cover all agents/workflows. |

---

## Key entry points

| Command | What it does |
|---|---|
| `python -m research_os route "<prompt>"` | Show routing plan, no execution. |
| `python -m research_os run "<prompt>"` | Route + execute, write transcript. |
| `python -m research_os audit` | Run full_audit workflow. |
| `python -m research_os bootstrap` | Create memory + registry files if missing. |
| `python -m research_os inspect-memory` | Show canonical memory headers. |
| `python -m research_os inspect-registries` | Validate registries + show counts. |
| `python -m research_os refresh-memory` | Regenerate `CODEBASE_MAP.md`, `WORKFLOW_REGISTRY.md` from code. |
| `python -m research_os query-memory "<topic>"` | Grep across memory KB. |
| `python dashboard/start.py` | Start dashboard on 127.0.0.1:7765. |
| `python -m pytest tests -q` | Run test suite. |

---

## MCP tools (exposed to Claude Code via `.mcp.json`)

| Tool name | Backend | What it does |
|---|---|---|
| `mcp__researchos__route_request(prompt, repo_root?)` | `service.route_request()` | Return plan without executing. |
| `mcp__researchos__run_request(prompt, repo_root?, force_if_human_required?)` | `service.run_request()` | Route + execute + write transcript. |
| `mcp__researchos__run_workflow(name, args?, repo_root?)` | `service.run_named_workflow()` | Run one of the 6 prebuilt workflows. |
| `mcp__researchos__get_report(path_or_id, repo_root?, max_chars?)` | `service.get_report()` | Retrieve a saved report. |
| `mcp__researchos__submit_compute_intent(intent, args?, user?, role?, auto_approve?)` | `agents/orchestrator.py` | Submit a compute task (different layer). |
| `mcp__researchos__approve_or_deny(task_id, decision, user?, reason?)` | `agents/orchestrator.py` | Approve/deny a queued compute task. |

These signatures are stable — additive changes only.

---

## Constraints (carry these in mind)

- `research_os.orchestrator` and `agents/orchestrator.py` stay separate. Never collapse them.
- All `OrchestrationPlan` fields added in the semantic-router upgrade are **optional with defaults** so older callers and tests don't break.
- New event types extend the `EVENT_TYPES` vocab; the existing 6 (workflow_started, agent_started, agent_completed, agent_error, gate_updated, workflow_completed) keep their schemas.
- Memory updates always go through `apply_memory_update()` — never write canonical files directly from agents.
- Don't touch `agents/telegram_gateway.py` or `configs/telegram_gateway.yaml`.

## Auto-discovered Python modules

<!-- BEGIN AUTOGEN -->
> Auto-generated by `research_os.memory.codebase_indexer`. Hand-edits between the BEGIN/END markers will be overwritten on the next refresh.

### `research_os/`

| Path | First docstring line |
|---|---|
| `research_os/__init__.py` | GNN ResearchOS — conservative research operating system. |
| `research_os/__main__.py` | Command-line interface. |
| `research_os/agents/__init__.py` | Concrete agent implementations. |
| `research_os/agents/base.py` | BaseAgent + AgentContext. |
| `research_os/agents/communication.py` | Communication agents: CodeBuilder, PaperClaim, VisualEvidence, ReviewerCollaboration. |
| `research_os/agents/context_provenance.py` | Context source-of-truth, Provenance, and Contradiction Hunter agents. |
| `research_os/agents/data_audit.py` | Data + leakage + preprocessing + code-review + testing agents. |
| `research_os/agents/orchestrator_role.py` | Master Research Orchestrator Agent (the role-agent, distinct from the |
| `research_os/agents/science_evaluation.py` | Science / evaluation agents: ResearchDesign, BiologicalRealism, Literature, |
| `research_os/eval/__init__.py` | Routing evaluation harness. |
| `research_os/eval/routing_benchmark.py` | Hand-curated routing benchmark for ResearchOS. |
| `research_os/eval/routing_eval.py` | Routing evaluator — run benchmark cases through the Router and grade them. |
| `research_os/events/__init__.py` | — |
| `research_os/events/emitter.py` | Thread-safe NDJSON event emitter for the ResearchOS dashboard. |
| `research_os/integrations/__init__.py` | External integration surfaces for ResearchOS. |
| `research_os/integrations/claude_code/__init__.py` | Claude Code integration for ResearchOS. |
| `research_os/integrations/claude_code/mcp_server.py` | Dependency-free MCP stdio server for Claude Code. |
| `research_os/integrations/claude_code/service.py` | Claude-facing ResearchOS actions. |
| `research_os/memory/__init__.py` | Markdown memory layer. |
| `research_os/memory/codebase_indexer.py` | Auto-generate the repo-layout section of CODEBASE_MAP. |
| `research_os/memory/registry_loader.py` | Parse the KB memory files (AGENT_REGISTRY. |
| `research_os/memory/store.py` | Markdown memory store. |
| `research_os/orchestrator.py` | Orchestrator: the live, gate-enforcing runtime that turns a router plan |
| `research_os/registries/__init__.py` | Registry layer: append-only JSON stores with closed-vocabulary validation. |
| `research_os/registries/store.py` | RegistryStore: atomic JSON storage for ResearchOS registries. |
| `research_os/reports/__init__.py` | Workflow report writers: markdown + JSON. |
| `research_os/reports/writer.py` | Workflow report writers. |
| `research_os/routing/__init__.py` | Routing layer: classify, score, plan. |
| `research_os/routing/_llm_json.py` | Shared helper for extracting a JSON object from LLM output. |
| `research_os/routing/agents.py` | Agent selector. |
| `research_os/routing/claude_fallback.py` | Claude fallback layer for routing. |
| `research_os/routing/context_builder.py` | Context packet builder. |
| `research_os/routing/gates.py` | Gate resolver. |
| `research_os/routing/human.py` | Human-approval classifier. |
| `research_os/routing/intent.py` | Rule-based intent classifier. |
| `research_os/routing/risk.py` | Risk classifier. |
| `research_os/routing/router.py` | Top-level Router: glue semantic + keyword classifiers, risk, gates, human, context. |
| `research_os/routing/semantic_router.py` | Ollama-backed semantic router for ResearchOS. |
| `research_os/schemas/__init__.py` | Dataclasses and validation for ResearchOS structured outputs. |
| `research_os/schemas/context.py` | Context packet (input to an agent) and orchestration plan (output of router). |
| `research_os/schemas/core.py` | Core agent-output dataclasses: Finding, Risk, GateUpdate, MemoryUpdate, AgentOutput. |
| `research_os/schemas/gates.py` | Gate names and per-gate status records. |
| `research_os/schemas/registries.py` | Registry entry dataclasses: artifact, claim, experiment, issue, source, environment, decision. |
| `research_os/schemas/vocab.py` | Closed vocabularies used by registries, agents, and the router. |
| `research_os/tools/__init__.py` | Filesystem, git, hashing, environment, and dependency-graph helpers. |
| `research_os/tools/dependency_graph.py` | Stale-propagation graph for the artifact registry. |
| `research_os/tools/environment.py` | Capture the current Python/OS environment for provenance. |
| `research_os/tools/git.py` | Git state capture without depending on GitPython. |
| `research_os/tools/hashing.py` | Content-addressed hashing for files, directories, and arbitrary text. |
| `research_os/tools/provenance.py` | Provenance capture: bundle git + environment + hashes + command into one record. |
| `research_os/transcripts/__init__.py` | Per-run transcript writer. |
| `research_os/transcripts/writer.py` | Per-run JSONL transcript writer. |
| `research_os/workflows/__init__.py` | Workflow runners: pre-built orchestration recipes. |
| `research_os/workflows/claim_audit.py` | Claim and Paper audit workflow. |
| `research_os/workflows/full_audit.py` | Full audit workflow: runs every audit-class agent on the current repo. |
| `research_os/workflows/md_validation.py` | MD validation workflow. |
| `research_os/workflows/metric_verification.py` | Metric verification workflow. |
| `research_os/workflows/runner.py` | Shared helper for workflow runners. |
| `research_os/workflows/submission_readiness.py` | Submission readiness workflow. |
| `research_os/workflows/training_eval.py` | Training + Evaluation workflow. |

### `agents/`

| Path | First docstring line |
|---|---|
| `agents/docker_packager.py` | Docker / Environment Packaging Agent. |
| `agents/ingest.py` | Document and Knowledge Ingestion Agent (Agent 21) |
| `agents/intent_parser.py` | Natural-language → Orchestrator intent parser. |
| `agents/orchestrator.py` | ResearchOS Orchestrator — permission-aware task dispatcher. |
| `agents/telegram_gateway.py` | Telegram Remote Research Gateway — frontend for ResearchOS. |
| `agents/wormhole_client.py` | Wormhole Client — runs on Advay's machine. |

### `dashboard/`

| Path | First docstring line |
|---|---|
| `dashboard/__init__.py` | — |
| `dashboard/server.py` | ResearchOS monitoring dashboard — FastAPI backend. |
| `dashboard/start.py` | Launch the ResearchOS monitoring dashboard. |

### `tests/`

| Path | First docstring line |
|---|---|
| `tests/__init__.py` | — |
| `tests/conftest.py` | Shared pytest fixtures for ResearchOS. |
| `tests/test_claude_code_integration.py` | Claude Code integration tests. |
| `tests/test_memory.py` | Memory loader and update protocol. |
| `tests/test_memory_kb.py` | Tests for the memory / knowledge base files used by the semantic router. |
| `tests/test_orchestrator.py` | Orchestrator integration: gate enforcement, blocking, no self-approval. |
| `tests/test_registries.py` | Registry atomic write, append, update, validate, dup-reject. |
| `tests/test_router.py` | Router prompt classification + gate + human escalation tests. |
| `tests/test_routing_regressions.py` | Deterministic regression tests for the 10 critical routing behaviors. |
| `tests/test_routing_semantic_cases.py` | End-to-end Router tests with the semantic backend mocked. |
| `tests/test_schemas.py` | Schema validation: closed vocabularies, required fields, dataclass shape. |
| `tests/test_scientific_guardrails.py` | Scientific guardrail tests. |
| `tests/test_semantic_router.py` | Unit tests for OllamaSemanticRouter. |
| `tests/test_stale_propagation.py` | Stale propagation: downstream artifacts should be marked stale when upstream changes. |
| `tests/test_transcripts.py` | Tests for per-run transcript writing. |

<!-- END AUTOGEN -->
