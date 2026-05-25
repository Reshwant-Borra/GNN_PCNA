# Tool Registry

Last updated: 2026-05-25T00:00:00Z
Updated by: research_os.bootstrap
Status: current

Internal Python helpers and external utilities available to ResearchOS agents. Agents should call these instead of shelling out where possible — the helpers add provenance + capture for transcripts.

---

## Provenance / state capture (`research_os/tools/`)

| Helper | Used by | Purpose |
|---|---|---|
| `tools.git.capture_git_state(repo_root)` | orchestrator, provenance_artifacts | Snapshot branch, HEAD, dirty status, last commit. Returned in every `WorkflowResult`. |
| `tools.env.snapshot_python_env()` | provenance_artifacts, testing_environment | Capture Python version, `pip freeze`, conda env (if present). |
| `tools.hashing.file_sha256(path)` | provenance_artifacts, dataset_integrity | Stable hash for artifact entries. |
| `tools.hashing.directory_sha256(path)` | provenance_artifacts | Aggregate hash over a directory tree (sorted, excludes ignore-patterns). |
| `tools.provenance.lineage_for_artifact(art_id)` | provenance_artifacts | Walk artifact_registry → upstream sources / commit / dataset. |
| `tools.provenance.detect_stale_artifacts(store)` | provenance_artifacts | Mark artifacts whose source hash no longer matches. |

---

## LLM clients

| Helper | Used by | Purpose |
|---|---|---|
| `routing.semantic_router.OllamaSemanticRouter` | router | Ollama Gemma 3:4b for prompt routing. Reads `AGENT_REGISTRY.md` + `ROUTING_GUIDE.md` once per process. |
| `routing.claude_fallback.FlagOnlyFallback` | router | Default fallback: annotate plan with `requires_claude_fallback=true`, let Claude Code handle it. |
| `routing.claude_fallback.AnthropicAPIFallback` | router | Optional: call Anthropic Claude API directly when `RESEARCHOS_CLAUDE_FALLBACK_API=1` is set. Adds an `anthropic` SDK dependency only when this mode is activated. |
| `routing._llm_json.extract_json(text)` | router, intent_parser | Pull first balanced JSON object out of model output. |

---

## External executables (called via subprocess by gateway, not by scientific agents)

| Tool | Where used | Notes |
|---|---|---|
| `git` | `tools.git`, `agents/orchestrator.py` | State capture, repo bundling. |
| `python` / `pytest` | `agents/orchestrator.py` | Run training, tests. |
| `docker` | `agents/orchestrator.py`, `agents/docker_packager.py` | Bundle the repo for transport. |
| `wormhole` | `agents/wormhole_client.py` | Secure file transfer (not used by scientific agents). |
| `ollama` (HTTP) | `routing.semantic_router`, `agents/intent_parser.py` | Local LLM at `OLLAMA_HOST` (defaults to host.docker.internal:11434 or localhost:11434). |
| `nvidia-smi` | `tools.env`, `agents/intent_parser.py` | GPU snapshot. |
| `openmm` | (MD workflows only) | Molecular dynamics simulations — gated by `compute_planning` approval. |

---

## Memory / registry access (the ONLY way agents persist state)

| Helper | Purpose |
|---|---|
| `memory.store.MemoryStore.read(name)` | Read a canonical markdown memory file. |
| `memory.store.MemoryStore.read_all()` | Return all 9 canonical memory files. |
| `memory.store.apply_memory_update(store, proposal, applied_by)` | Apply an approved `MemoryUpdateProposal`. Raises if `requires_human_approval=True`. |
| `memory.registry_loader.load_agent_registry()` | Parse `AGENT_REGISTRY.md` → dict for the semantic router. |
| `memory.registry_loader.load_routing_guide()` | Parse `ROUTING_GUIDE.md` → dict of category→examples for the semantic router. |
| `memory.codebase_indexer.regenerate_codebase_map(repo_root)` | Rebuild the auto-discoverable parts of `CODEBASE_MAP.md`. |
| `registries.store.RegistryStore.read(name)` | Read a JSON registry. |
| `registries.store.RegistryStore.add_entry(name, entry)` | Append-only entry insert. |
| `registries.store.RegistryStore.update_entry(name, entry_id, fields)` | Update an existing entry (rejected if validation fails). |
| `registries.store.RegistryStore.validate(name)` | Run schema validation; return list of issues. |

---

## Event / transcript

| Helper | Purpose |
|---|---|
| `events.emitter.init_emitter(repo_root, workflow_id=None)` | Idempotently configure the NDJSON sink + optional per-run JSONL transcript. |
| `events.emitter.emit(event_type, workflow_id, data)` | Append one event record. Silent no-op if not initialized. |
| `transcripts.writer.TranscriptWriter(repo_root, workflow, ts)` | Per-run transcript writer. Used by `service.run_request()`. |

---

## When NOT to call a tool

- Don't shell out for git status — use `tools.git.capture_git_state`.
- Don't read memory files with `open()` — use `MemoryStore.read()`.
- Don't write registry JSON directly — use `RegistryStore.add_entry()`.
- Don't `pip install anthropic` unless the user explicitly turns on `AnthropicAPIFallback` via the env var. The flag-only fallback is sufficient for the Claude Code interactive case.
