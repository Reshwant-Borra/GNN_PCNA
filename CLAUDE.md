# CLAUDE.md — GNN-PCNA Research Repo

## Read Order (mandatory before any task)

1. `REPO_MAP.md` — directory layout + task-to-file lookup + do-not-scan list
2. `docs/knowledge/INDEX.md` — root brain node, links all knowledge files
3. Only the **smallest relevant subset** of `docs/knowledge/` for the task at hand
4. `KNOWN_BUGS.md` — before any implementation

Do NOT scan the entire repo. Use `REPO_MAP.md` to find files.

---

## Default Behavior

### Context loading
- Read `docs/knowledge/INDEX.md` first — it tells you what to read next.
- Load only files directly relevant to the task. Do not preload everything.
- Task is about models → read `MODELS.md`, skip `BIOLOGY_PCNA.md` unless asked.
- Task is about data → read `PIPELINE.md` + `DATASETS.md`.
- Task is about experiments → read `EXPERIMENT_INDEX.md` + relevant `E0XX_*.md`.
- Task is about MD → read `VALIDATION.md`.

### Repo navigation
- Never run `find . -type f` or list all files unless explicitly asked.
- Treat `REPO_MAP.md` as the authoritative directory map.
- If a file is not in `REPO_MAP.md`, ask before creating it.

### Response style
- Concise and structured: tables, bullets, input/output specs over paragraphs.
- Do not repeat large summaries already in `docs/knowledge/`.
- If uncertain about biology/paper facts, mark: `Needs NotebookLM extraction`.
- Do not speculate on paper-specific results or metrics.

---

## Planning Rules (CRITICAL)

**For every implementation task: create a plan file FIRST, unless the user explicitly says "implement" or "code this now".**

### Plan file location
```
docs/plans/YYYY-MM-DD_task_slug.md
```

### Plan file template
Use `docs/plans/plan_template.md`. Each plan must include:
- Goal
- Brain files read
- Code files to inspect
- Inputs / outputs
- Step-by-step implementation
- Risks + edge cases
- Tests / validation
- `=== GEMINI TASK ===` block — copy-pasteable for Gemini
- `=== CHATGPT REVIEW TASK ===` block — copy-pasteable for ChatGPT

### When NOT to create a plan
- Simple one-liner fixes
- Documentation-only tasks
- User explicitly says "just do it" or "implement directly"

---

## Cost-Saving Rules

| Rule | Reason |
|---|---|
| Never re-read raw papers | Info is distilled in `docs/knowledge/` and `docs/research/paper_notes.md` |
| Never repeat summaries already in brain | Wastes tokens, no added value |
| Load the smallest relevant subset of knowledge/ | Use `INDEX.md` to navigate |
| Prefer compact Markdown updates over pasting full text | Keeps context lean |
| Split large tasks into staged plan files | One plan per implementation stage |
| Use NotebookLM for paper facts, not inference | Source-grounded extraction only |
| For simple questions, answer directly | Do not load docs unless truly needed |

---

## Role Separation

| Agent | Responsibility | Does NOT do |
|---|---|---|
| **Claude** | Planning, architecture, research reasoning, risk analysis, plan files | Implementation, code writing |
| **Gemini** | Implementation from Claude plan, fill stubs, edit code | Architecture decisions, redesign |
| **ChatGPT/Codex** | Review changed files, bugs, scientific logic, data leakage | New features, redesign |
| **NotebookLM** | Research extraction from papers + sources | Repo navigation, coding |

Claude's default output for a coding request is a **plan file**, not code.

---

## NotebookLM MCP Usage

**USE NotebookLM MCP for:**
- Extracting exact claims, methods, metrics from papers
- Summarizing research sources
- Comparing two papers
- Extracting dataset details, evaluation metrics, limitations

**DO NOT use NotebookLM MCP for:**
- Navigating the repo
- Writing code
- Architecture decisions not grounded in a paper

**Output pipeline:**
```
NotebookLM MCP output
  → docs/notebooklm/raw_extractions/   (if long)
  → docs/notebooklm/distilled_notes/   (always distill)
  → merge into docs/knowledge/          (when ready)
```

See `docs/knowledge/NOTEBOOKLM_WORKFLOW.md` for exact prompt templates.

---

## Experiment Logging

- All experiments: `docs/experiments/E{NNN}_short_name.md`
- Index: `docs/experiments/EXPERIMENT_INDEX.md` — update after each experiment
- Template: `docs/experiments/experiment_template.md`
- **Never overwrite** an existing experiment log — append or create new file

---

## Key Scientific Constraints

| Constraint | Detail |
|---|---|
| PCNA structure | Homotrimeric ring, 3 identical chains (A, B, C) |
| Apo structure | PDB 1W60 — no AOH1996 pocket visible |
| Holo structure | PDB 8GLA — AOH1996 bound, cryptic pocket open |
| Ground truth | Residues within 6 Å of AOH1996 in 8GLA |
| Validation requirement | Model MUST recover 8GLA pocket before trusting novel predictions |
| MD requirement | RMSF + DCCM + volume evidence required to validate a pocket |
| Stack | Python 3.10+, PyTorch Geometric, MDAnalysis, BioPython/ProDy |

---

## Workflow Model

```
NotebookLM MCP
  → extracts research facts from papers
  ↓
docs/knowledge/ + docs/experiments/   (Obsidian Markdown Brain)
  → stores distilled context
  ↓
Claude Code
  → reads brain, creates docs/plans/YYYY-MM-DD_*.md
  ↓
Gemini / Antigravity
  → implements from plan (modifies src/ only as specified)
  ↓
ChatGPT / Codex
  → reviews changed files
  ↓
Claude
  → final signoff if needed
```

See `AGENTS.md` for detailed handoff protocol.
See `docs/knowledge/AI_WORKFLOW_RULES.md` for the full plain-language explanation.
See `docs/prompts/` for copy-pasteable prompt templates per agent.

---

## Related

[[REPO_MAP]] · [[AGENTS]] · [[INDEX]] · [[KNOWN_BUGS]] · [[EXPERIMENT_INDEX]] · [[plan_template]] · [[AI_WORKFLOW_RULES]]
