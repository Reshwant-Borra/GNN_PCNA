# AGENTS.md — Multi-Agent Workflow

## System Map

```
NotebookLM MCP ──→ Obsidian Brain (docs/knowledge/)
                         ↓
                    Claude Code
                    (plan files)
                         ↓
               Gemini / Antigravity
                   (implementation)
                         ↓
                  ChatGPT / Codex
                     (review)
                         ↓
                   Claude (signoff)
```

---

## Agent Roles

| Agent | Role | Input | Output |
|---|---|---|---|
| **NotebookLM MCP** | Research extraction | Papers, PDFs, docs | Bullet-point facts, method summaries |
| **Obsidian Markdown Brain** | Persistent memory | Distilled NLM output + experiment results | Linked knowledge graph |
| **Claude Code** | Planner, architect | Brain files + user request | Plan file in `docs/plans/` |
| **Gemini / Antigravity** | Implementer | Claude plan file | Modified `src/` files |
| **ChatGPT / Codex** | Reviewer | Changed files + review prompt | Bug list + correction suggestions |

---

## Agent 1: NotebookLM MCP

**Purpose:** Source-grounded extraction of research information.

**Inputs:**
- Papers loaded as sources in NotebookLM notebook
- Extraction prompt (see `docs/prompts/NOTEBOOKLM_EXTRACTION_PROMPTS.md`)

**Outputs:**
- Bullet-point facts, method summaries, dataset details, metrics, limitations
- Stored in `docs/notebooklm/distilled_notes/`

**Rules:**
- Only extracts. Does not design or implement.
- Output is raw material — must be distilled before going into `docs/knowledge/`.
- Source-grounded: cites the source for each claim.

---

## Agent 2: Obsidian Markdown Brain

**Purpose:** Persistent project memory that Claude reads instead of the raw repo.

**Structure:**
```
docs/knowledge/     → canonical project facts
docs/experiments/   → experiment logs
docs/data/          → data documentation
docs/notebooklm/    → extracted research (raw + distilled)
```

**Rules:**
- This is the single source of truth for Claude.
- Update after every experiment, extraction, or decision.
- Use `[[WIKILINKS]]` to link related files (Obsidian-compatible).
- Never store implementation details here — those belong in `docs/implementation/`.

---

## Agent 3: Claude Code

**Purpose:** Planning, architecture decisions, risk analysis.

**Inputs:** Brain files from `docs/knowledge/`, user task description.

**Output:** Plan file at `docs/plans/YYYY-MM-DD_task_slug.md`

**Rules:**
- Reads the minimal relevant subset of the brain.
- Does NOT implement unless explicitly asked.
- Every plan includes a `=== GEMINI TASK ===` block and `=== CHATGPT REVIEW TASK ===` block.
- Flags risks, edge cases, data leakage concerns.

---

## Agent 4: Gemini / Antigravity

**Purpose:** Full implementation from Claude's plan.

**Inputs:** Claude plan file + relevant `src/` stubs + relevant `docs/knowledge/` files

**Rules:**
- Implements exactly what the plan specifies.
- Does NOT change architecture unless explicitly told to.
- Modifies only the files listed in the plan.
- Adds brief docstrings to all public functions.
- Returns a change summary when done.

**Prompt template:** `docs/prompts/GEMINI_IMPLEMENTER_PROMPTS.md`

---

## Agent 5: ChatGPT / Codex

**Purpose:** Focused review of changed files.

**Inputs:** Changed files + `=== CHATGPT REVIEW TASK ===` block from the plan

**Rules:**
- Reviews only changed files (not the entire codebase).
- Checks: bugs, scientific logic, data leakage, PyG API misuse, label handling.
- Does NOT redesign unless asked.
- Suggests minimal targeted fixes.
- Newly discovered bugs → add to `KNOWN_BUGS.md`.

**Prompt template:** `docs/prompts/CHATGPT_REVIEW_PROMPTS.md`

---

## Handoff Protocol

### Step 1: Claude creates a plan

1. Read relevant `docs/knowledge/` files.
2. Create `docs/plans/YYYY-MM-DD_task_slug.md` from template.
3. Include `=== GEMINI TASK ===` and `=== CHATGPT REVIEW TASK ===` blocks.
4. Share plan with user for approval.

### Step 2: Gemini implements

1. User copies `=== GEMINI TASK ===` block into Gemini.
2. Gemini receives: plan block + relevant `src/` stubs + relevant knowledge files.
3. Gemini returns: implemented files + change summary.
4. User applies changes to repo.

### Step 3: ChatGPT reviews

1. User copies `=== CHATGPT REVIEW TASK ===` block into ChatGPT.
2. ChatGPT receives: changed files + review instructions.
3. ChatGPT returns: bug list + correction suggestions.
4. User applies fixes or sends back to Gemini.

### Step 4: Experiment logged

1. Update or create `docs/experiments/E{NNN}_*.md`.
2. Update `docs/experiments/EXPERIMENT_INDEX.md`.
3. If bugs found, update `KNOWN_BUGS.md` and `docs/logs/BUG_LOG.md`.
4. If decisions made, update `docs/logs/DECISIONS.md`.

---

## Context Budget Guidelines

| Agent | What to send | What NOT to send |
|---|---|---|
| **Claude** | Plan template + relevant knowledge/ files (minimal set) | Full repo, raw data, all docs |
| **Gemini** | Plan file + relevant stubs + SYSTEM_OVERVIEW + PIPELINE | Large unrelated files |
| **ChatGPT** | Changed file(s) + review prompt + KNOWN_BUGS | Full codebase |
| **NotebookLM** | The exact extraction prompt + source loaded in notebook | Code, repo structure |

---

## Handoff Format (copy-pasteable example)

### Claude → Gemini (GEMINI TASK block format)

```
=== GEMINI TASK ===

Project: GNN-PCNA cryptic pocket prediction
Stack: PyTorch Geometric, MDAnalysis, BioPython, Python 3.10+

Context files (read before implementing):
- [paste SYSTEM_OVERVIEW.md]
- [paste relevant PIPELINE.md stage]

File to implement: src/[path/to/file.py]
Stub (preserve ALL function signatures):
[paste stub]

Requirements:
- PyTorch Geometric compatible
- Full type hints on all public functions
- No placeholder TODOs — implement fully
- Handle PCNA homotrimer (chains A/B/C)
- Document return shapes in docstrings
- Do NOT change function signatures

Return: complete implemented file + one-paragraph change summary.
=== END GEMINI TASK ===
```

### Gemini → ChatGPT (CHATGPT REVIEW TASK block format)

```
=== CHATGPT REVIEW TASK ===

Project: GNN-PCNA cryptic pocket prediction
Changed file: src/[path/to/file.py]

[paste complete changed file]

Known issues (check these first):
[paste KNOWN_BUGS.md content]

Review focus:
1. Off-by-one errors in graph/residue indexing
2. Data leakage (train/val/test split at protein level, not residue level)
3. Label imbalance handling (focal loss or weighted BCE correctness)
4. PyTorch Geometric API correctness
5. MD analysis assumptions (RMSF normalization, DCCM symmetry)
6. Scientific correctness for PCNA homotrimer

Return: numbered list of issues (severity: critical/warning/suggestion) + minimal fixes.
=== END CHATGPT REVIEW TASK ===
```
