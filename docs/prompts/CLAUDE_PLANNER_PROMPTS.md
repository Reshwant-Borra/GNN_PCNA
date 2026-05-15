# CLAUDE_PLANNER_PROMPTS.md — Reusable Claude Planning Prompts

---

## Standard Planning Prompt

```
You are a computational biology engineer and AI planning specialist.

Project: GNN-PCNA — Graph neural network for cryptic binding-site prediction on human PCNA.

Before planning, read these brain files (minimal subset):
- docs/knowledge/INDEX.md
- docs/knowledge/PIPELINE.md (relevant stage only)
- docs/knowledge/MODELS.md (if model-related)
- docs/knowledge/DATASETS.md (if data-related)
- KNOWN_BUGS.md

Task: {describe task}

Output format:
1. Create a plan file at docs/plans/YYYY-MM-DD_{slug}.md using the template at docs/plans/plan_template.md.
2. Include a GEMINI TASK block (copy-pasteable).
3. Include a CHATGPT REVIEW TASK block (copy-pasteable).
4. Do NOT write implementation code unless explicitly asked.
5. Keep the plan file concise — use tables and bullets, not paragraphs.
```

---

## Architecture Decision Prompt

```
You are a computational biology engineer.

Project context:
- Target: PCNA (PDB 1W60 apo, 8GLA holo with AOH1996)
- Stack: PyTorch Geometric, MDAnalysis, BioPython, Python 3.10+
- Read docs/knowledge/MODELS.md and docs/knowledge/KNOWN_LIMITATIONS.md before answering.

Decision needed: {describe decision}

Output format:
- Chosen approach: one sentence
- Rationale: 2–3 bullets
- Alternatives considered: table of 2–3 alternatives with tradeoff column
- Risks: bullet list
- DO NOT implement. Just decide and document.

Save the decision to docs/logs/DECISIONS.md.
```

---

## NotebookLM Orchestration Prompt

```
You are coordinating research extraction from NotebookLM MCP.

I need information about: {topic}

Step 1: Check docs/notebooklm/distilled_notes/ for existing notes on this topic.
Step 2: If not available, generate an extraction prompt using the template at docs/prompts/NOTEBOOKLM_EXTRACTION_PROMPTS.md.
Step 3: After extraction, tell me:
  - Which distilled_notes file to update
  - Which docs/knowledge/ file to merge into
  - The 5 most important bullet points from the extraction

Do NOT paste raw NLM output into docs/knowledge/. Always distill first.
```

---

## Experiment Planning Prompt

```
I want to run experiment E{NNN}: {name}.

Before planning:
- Read docs/experiments/EXPERIMENT_INDEX.md
- Read docs/experiments/experiment_template.md
- Read docs/knowledge/VALIDATION.md (for success criteria)
- Read docs/knowledge/PIPELINE.md (for relevant stage)

Output:
1. Create docs/experiments/E{NNN}_{slug}.md from template.
2. List all blocking dependencies (what must be implemented first).
3. List the 3 most critical tests to run.
4. Update docs/experiments/EXPERIMENT_INDEX.md with the new entry.
5. Do NOT implement anything — only plan.
```

---

## Bug Triage Prompt

```
Bug: {description}
Error output or traceback: {paste here}
File: {file path}

Before analyzing:
- Read KNOWN_BUGS.md
- Read docs/logs/BUG_LOG.md
- Read the relevant src/ file (do NOT scan the whole repo)

Output:
1. Root cause (one sentence)
2. Minimal fix (code block)
3. Is this a known bug? (check KNOWN_BUGS.md)
4. If new: add entry to KNOWN_BUGS.md and docs/logs/BUG_LOG.md
5. Does this require a plan file? (only if fix is non-trivial)
```

---

## Related

[[CLAUDE]] · [[AI_WORKFLOW_RULES]] · [[AGENTS]] · [[plan_template]] · [[KNOWN_BUGS]]
