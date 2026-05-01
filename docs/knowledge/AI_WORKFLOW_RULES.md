# AI_WORKFLOW_RULES.md — The System in Plain Language

→ Links: [[NOTEBOOKLM_WORKFLOW]] | [[VISUALIZATION_SYSTEM]]

> Read this when you forget how the system works. Written to be human-readable.

---

## 1. What NotebookLM Does

NotebookLM is connected via MCP (Model Context Protocol) and reads your research papers and documents.

**You use it to:**
- Extract exact information from papers (methods, datasets, metrics, limitations)
- Summarize a paper in bullet points
- Compare two papers side-by-side
- Find specific claims that are grounded in a source

**It does NOT:**
- Edit code
- Navigate the repo
- Make implementation decisions

**Output:** Bullet-point facts, method summaries, citations.

**After extraction:** Save to `docs/notebooklm/distilled_notes/` and merge into `docs/knowledge/`.

---

## 2. What Obsidian Markdown Does

Obsidian is used as a **knowledge graph viewer** for the `docs/` folder.

The files in `docs/knowledge/`, `docs/experiments/`, `docs/data/`, etc. are all Obsidian-compatible Markdown files with `[[wikilinks]]`.

**This creates a graph of interconnected knowledge:**
- `INDEX.md` links to all knowledge files
- `EXPERIMENT_INDEX.md` links to all experiments
- Each experiment links to the pipeline stage it relates to

**Why this saves Claude tokens:**
- Claude reads compact, structured files instead of scanning the whole repo
- Claude follows `[[links]]` to find related info without searching
- Distilled notes replace re-reading raw papers

---

## 3. What Claude Code Does

Claude is the **planner and architect**. Claude does NOT write implementation code by default.

**Claude's job:**
1. Read the brain files (minimal relevant subset)
2. Understand the task
3. Create a plan file: `docs/plans/YYYY-MM-DD_task_slug.md`
4. Include a GEMINI TASK block and CHATGPT REVIEW TASK block

**Claude does NOT:**
- Scan the whole repo
- Re-read raw papers
- Write implementation code (unless explicitly asked)
- Make claims about biology without source-grounded evidence

---

## 4. What Gemini / Antigravity Does

Gemini is the **implementer**. Gemini takes Claude's plan and writes the code.

**Gemini's job:**
1. Read the GEMINI TASK block from Claude's plan
2. Read the relevant `src/` stubs and knowledge files
3. Implement exactly what the plan says
4. Return the completed file + a change summary

**Gemini does NOT:**
- Redesign the architecture
- Modify files not in the plan
- Make decisions Claude didn't make

---

## 5. What ChatGPT / Codex Does

ChatGPT is the **reviewer**. ChatGPT reviews Gemini's implementation.

**ChatGPT's job:**
1. Read the CHATGPT REVIEW TASK block from Claude's plan
2. Read the changed files
3. Check for bugs, data leakage, scientific logic errors, API misuse
4. Return a numbered list of issues with severity

**ChatGPT does NOT:**
- Redesign features
- Add new functionality

---

## 6. How the Tools Pass Work to Each Other

```
Step 1: You ask Claude to plan a task
         → Claude reads docs/knowledge/ (minimal set)
         → Claude writes docs/plans/YYYY-MM-DD_task.md

Step 2: You copy GEMINI TASK block → paste into Gemini
         → Gemini implements the code
         → You apply the code to src/

Step 3: You copy CHATGPT REVIEW TASK block → paste into ChatGPT
         → ChatGPT reviews
         → You apply fixes

Step 4: You update the experiment log
         → docs/experiments/EXPERIMENT_INDEX.md
         → docs/experiments/E0XX_name.md
```

---

## 7. How This Saves Claude Credits

| Without this system | With this system |
|---|---|
| Claude scans repo every session | Claude reads 2–3 compact brain files |
| Claude re-reads paper content | Info pre-extracted into Markdown |
| Claude writes full implementations | Claude writes plan files only |
| Claude re-derives architecture every time | Architecture documented in MODELS.md |
| Claude guesses paper facts | NotebookLM extracts ground truth |

**Estimated savings: 60–80% fewer tokens per session.**

---

## 8. What NOT to Do

| Don't | Why |
|---|---|
| Ask Claude to implement code without a plan | Wastes tokens if wrong approach |
| Paste raw NotebookLM output into docs/knowledge/ | Creates bloated, unstructured files |
| Ask Claude to read the whole codebase | Wastes context budget |
| Mix experiment logs from different runs | Confusing; use separate E0XX files |
| Let Claude guess biology facts | Always use NotebookLM for paper-specific facts |
| Commit large binary data files | Use git-lfs or keep in data/ (gitignored) |

---

## 9. Daily Workflow

### Morning session start:
1. Open Obsidian → review `docs/knowledge/INDEX.md` and `docs/experiments/EXPERIMENT_INDEX.md`
2. Note what status changed overnight (if running a job)
3. Decide the day's task

### Research extraction session:
1. Load papers into NotebookLM
2. Use prompts from `docs/prompts/NOTEBOOKLM_EXTRACTION_PROMPTS.md`
3. Save outputs to `docs/notebooklm/distilled_notes/`
4. Merge relevant facts into `docs/knowledge/BIOLOGY_PCNA.md`, `MODELS.md`, etc.

### Implementation session:
1. Tell Claude: "Create a plan for [task]"
2. Claude reads brain → writes `docs/plans/YYYY-MM-DD_task.md`
3. Copy GEMINI TASK block → implement in Gemini
4. Apply code changes to `src/`
5. Copy CHATGPT REVIEW TASK block → review in ChatGPT
6. Apply fixes

### Experiment logging:
1. Create `docs/experiments/E0XX_short_name.md` from template
2. Add entry to `docs/experiments/EXPERIMENT_INDEX.md`
3. Update `docs/knowledge/INDEX.md` quick status table

---

## 10. Example: Building a Feature from Scratch

**Task:** Implement `parse_pdb.py`

1. **Claude reads:** `docs/knowledge/PIPELINE.md` (Stage 1), `docs/knowledge/DATASETS.md`, `src/data_processing/parse_pdb.py` (stub)
2. **Claude creates:** `docs/plans/2026-04-30_parse_pdb.md`
   - Goal: implement PDB parser
   - Inputs: .pdb file path
   - Outputs: list of Residue objects
   - Steps: strip HETATM → extract CA coords → compute SASA → secondary structure
   - Risks: handling non-standard residues, missing CA atoms
   - GEMINI TASK block
   - CHATGPT REVIEW TASK block
3. **Gemini implements:** full `parse_pdb.py`
4. **ChatGPT reviews:** checks BioPython API usage, edge cases for PCNA
5. **Claude approves** (optional)
6. **Experiment log updated** (if this was tested end-to-end)
