# Plan: Telegram Remote Research Gateway + Docker Packaging Agent

**Date:** 2026-05-23
**Status:** v1.5/v2 scaffolding — implemented, **not** wired into `scripts/run_pipeline.py`
**Experiment:** N/A — infrastructure feature

---

## Goal

Let approved collaborators submit research tasks to GNN-PCNA from Telegram, routed through a permission-aware Orchestrator (never directly into Claude Code). Risky/long-running intents queue for owner approval; progress + artifacts stream back to chat. Also ship a Docker / Environment Packaging Agent so collaborators can replicate the project environment.

---

## Brain Files Read

- `CLAUDE.md` — workflow rules, role separation
- `AGENTS.md` — multi-agent handoff protocol (gateway respects it)
- `REPO_MAP.md` — directory layout (this plan adds `configs/`)
- `agents/local_agent.py`, `agents/gemma_verifier.py`, `agents/obsidian_writer.py` — agent style baseline
- `scripts/run_pipeline.py` — canonical subprocess entrypoints per stage
- `requirements.txt` — optional-dep convention (`# mcp==1.0.0` pattern)

---

## Files Created

| File | Purpose |
|---|---|
| `agents/orchestrator.py` | Permission-aware task dispatcher. Roles (owner/collaborator/viewer), intent registry, approval queue, threaded subprocess runner, event bus, artifact dir per task. Includes CLI. |
| `agents/telegram_gateway.py` | python-telegram-bot v20 long-polling frontend. Loads YAML whitelist, parses `/run /approve /deny /cancel /status /pending /get /help /whoami`, subscribes to orchestrator events, streams updates + artifacts back. Owner DM'd on approval requests. |
| `agents/docker_packager.py` | Two subcommands: `docker` (writes a Dockerfile, CPU or CUDA; optional `--build`) and `bundle` (stripped repo .zip excluding raw data, graphs, trajectories, `.git`, large checkpoints). Writes `manifest.json`. |
| `configs/telegram_gateway.yaml` | Example whitelist with one owner placeholder + commented collaborator/viewer examples. Token read from `TELEGRAM_BOT_TOKEN` env var. |

## Files Modified

| File | Change |
|---|---|
| `REPO_MAP.md` | Added `agents/orchestrator.py`, `agents/telegram_gateway.py`, `agents/docker_packager.py`, `configs/telegram_gateway.yaml`. New top-level `configs/` directory entry. Source File Status table updated. |
| `requirements.txt` | Added commented optional deps: `python-telegram-bot>=20.0`, `pyyaml>=6.0`, `docker>=7.0`. |

---

## Architecture

```
Telegram user
   │ /run train epochs=50
   ▼
agents/telegram_gateway.py            (python-telegram-bot v20, long-polling)
   │ submit(user, role, "train", {epochs: 50})
   ▼
agents/orchestrator.py                (in-process, thread-per-task)
   │ resolve intent → check role → risky? queue : start
   │ build_cmd → subprocess.Popen
   ▼
scripts/run_pipeline.py stages        (existing — unchanged)
src/training/train.py, scripts/build_graphs.py, ...
   │ stdout → orchestrator event bus → telegram_gateway → chat
   ▼
data/artifacts/<task_id>/{run.log, status.json, Dockerfile, *.zip, manifest.json}
```

Key invariants:
- Gateway **never** imports or invokes the `claude` CLI.
- Gateway depends only on orchestrator; orchestrator depends only on stdlib + existing pipeline scripts.
- Whitelist is enforced at the gateway boundary AND re-checked in the orchestrator (defense in depth).
- Risky/long-running intents from collaborators always queue. Owner-submitted risky intents auto-run (the owner has already self-approved by submitting).

---

## Intent Registry

| Intent | Role | Risky | Long | Subprocess |
|---|---|---|---|---|
| `status` | viewer | n | n | in-process snapshot |
| `crawl` | collaborator | n | Y | `agents/pcna_crawler.py` |
| `verify` | collaborator | n | Y | `agents/gemma_verifier.py` |
| `vault` | collaborator | n | n | `agents/obsidian_writer.py` |
| `fetch` | collaborator | n | Y | `src.data_processing.fetch_structures` |
| `graphs` | collaborator | n | Y | `scripts/build_graphs.py` |
| `split` | collaborator | **Y** | n | `scripts/make_split.py` (invalidates claims) |
| `train` | collaborator | **Y** | Y | `src.training.train` (overwrites checkpoints, invalidates claims) |
| `eval` | collaborator | n | n | `src.evaluation.score_pockets` |
| `inference` | collaborator | n | Y | `scripts/bulk_inference.py` |
| `verify_claims` | collaborator | n | Y | `scripts/verify_all_claims.py` |
| `pipeline` | collaborator | **Y** | Y | `scripts/run_pipeline.py` (full end-to-end) |
| `docker_build` | collaborator | n | Y | `agents/docker_packager.py docker` |
| `bundle` | collaborator | n | Y | `agents/docker_packager.py bundle` |

"Risky" = re-runs splits, re-trains, overwrites checkpoints, or otherwise invalidates the held-out AUROC claim tracked in `docs/experiments/` + `scripts/verify_all_claims.py`.

---

## Risks / Edge Cases

| Risk | Mitigation |
|---|---|
| Bot token leaked into git | Token only read from env (`bot_token_env`); YAML never holds it. |
| Unauthorized Telegram user submits a task | Whitelist check at gateway; orchestrator also enforces `min_role`. |
| Collaborator triggers expensive train run | Marked `risky` → queued for owner approval; owner DM'd automatically. |
| `python-telegram-bot` not installed | Gateway raises a clean `SystemExit` with the install command. |
| `pyyaml` not installed | Same — explicit `SystemExit` with install command. |
| Subprocess hangs forever | Owner can `/cancel <task_id>`; orchestrator `proc.terminate()`s. |
| Long log stream floods chat | Each log line emitted as a chat message; rate-limit / batching is a v2 follow-up. |
| Orchestrator state lost on restart | Acceptable for v1.5 — in-memory tasks + on-disk artifacts only. v2: SQLite. |
| Docker bundle accidentally ships `data/raw/` | Hard-coded exclude list in `docker_packager.py` (`EXCLUDE_DIRS` + `EXCLUDE_GLOBS`). |
| Bundle inflates from small `.pt` graph tensors | All `.pt` files excluded; collaborators regenerate via `scripts/build_graphs.py`. |

---

## Tests / Validation (manual, post-merge)

| Test | Expected |
|---|---|
| `python agents/orchestrator.py list-intents` | Prints 14 intents with role/risky/long flags |
| `python agents/orchestrator.py run --user advay --role owner --intent status --wait` | Writes `data/artifacts/<id>/status.json`, state=`succeeded` |
| `python agents/orchestrator.py run --user bob --role collaborator --intent train` | State=`awaiting_approval`, owner notified via event bus |
| `python agents/docker_packager.py docker --out data/artifacts/_test` | Writes `Dockerfile` + `manifest.json` |
| `python agents/docker_packager.py bundle --out data/artifacts/_test` | Writes `gnn-pcna-bundle-*.zip` (under ~5 MB), excludes `data/raw/` |
| Gateway start without `TELEGRAM_BOT_TOKEN` set | Clean `SystemExit` naming the missing env var |
| Gateway start without `python-telegram-bot` installed | Clean `SystemExit` with pip install command |

---

## Out of Scope (v2 follow-ups)

- Webhook mode (currently long-polling only)
- Persistent task DB (currently in-memory + on-disk artifacts)
- Wiring intents into `scripts/run_pipeline.py` as a new stage (deliberately deferred — the gateway is an alternative entry point, not a pipeline stage)
- Per-intent rate limiting on log streaming
- Multi-tenant artifact sandboxing

---

## === GEMINI TASK ===

```
Project: GNN-PCNA — Telegram Remote Research Gateway (v1.5/v2)
Stack:   Python 3.10+, stdlib, python-telegram-bot>=20 (optional), pyyaml (optional)

Context to read first:
- agents/orchestrator.py        (existing — DO NOT modify intent registry without owner sign-off)
- agents/telegram_gateway.py    (existing)
- agents/docker_packager.py     (existing)
- configs/telegram_gateway.yaml (existing example)
- docs/plans/2026-05-23_telegram_remote_gateway.md (this plan)

Possible follow-up tasks (only on explicit user instruction):
1. Add /logs <task_id> [tail=N] command that streams the last N lines of run.log.
2. Add per-user concurrency cap (default: 1 running task per non-owner).
3. Add webhook mode behind --webhook flag (FastAPI + ngrok pattern).

Requirements:
- Match the existing agent style (module docstring with usage, `from __future__ import annotations`, REPO_ROOT pattern).
- Do NOT call the `claude` CLI from any new code path.
- Do NOT remove or relax the risky/long-running approval gate.
- Keep python-telegram-bot, pyyaml, docker SDK as OPTIONAL deps (commented in requirements.txt).
- Add type hints on all public functions; no decorative comments.

Return: changed files + one-paragraph change summary.
```

---

## === CHATGPT REVIEW TASK ===

```
Project: GNN-PCNA — Telegram Remote Research Gateway

Files to review:
- agents/orchestrator.py
- agents/telegram_gateway.py
- agents/docker_packager.py
- configs/telegram_gateway.yaml

[paste each complete file]

Known-bug context: KNOWN_BUGS.md
[paste KNOWN_BUGS.md]

Review checklist (prioritize these):
1. Auth bypass — can an unwhitelisted Telegram id reach the orchestrator? Trace every command handler.
2. Privilege escalation — can a collaborator self-approve a risky intent, or bypass the queue by re-submitting?
3. Command injection — does any intent's build_cmd interpolate user input into shell? (We use subprocess argv lists; flag any string-built commands.)
4. Path traversal — task_id is uuid4-derived; can `--out` for docker_packager escape the repo? Should it be clamped?
5. Subprocess hygiene — are subprocess.Popen handles closed? Are zombie processes possible if the thread dies?
6. Race condition — Orchestrator._lock / _listeners_lock — any double-locking, missing locks on `self.tasks` mutation?
7. Bundle exclude correctness — does docker_packager.cmd_bundle ever include `data/raw/`, `data/graphs/`, `.git/`, or `*.dcd/.xtc` files? Test the glob logic on edge cases like `data/raw_extra/`.
8. Token leak — is the bot token ever logged, written to disk, or echoed in error messages?
9. Telegram error handling — what happens on network blip? Does the event pump die silently?
10. Scientific integrity — does any intent re-run train/split/build_graphs WITHOUT requiring owner approval?

For each issue:
- Severity: critical | warning | suggestion
- Location: file:line or function name
- Description: what's wrong
- Fix: minimal correction

Return: numbered list of issues only. No redesign.
```

---

## Related

[[CLAUDE]] · [[AGENTS]] · [[REPO_MAP]] · [[KNOWN_BUGS]] · [[plan_template]] · [[GEMINI_IMPLEMENTER_PROMPTS]] · [[CHATGPT_REVIEW_PROMPTS]]
