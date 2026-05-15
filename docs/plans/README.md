# docs/plans/ — Implementation Plan Files

## Purpose

Every non-trivial implementation task starts with a Claude-generated plan file here.

This saves time and tokens because:
- Gemini gets clear, targeted instructions
- ChatGPT knows exactly what to review
- Plans are reusable if interrupted
- Mistakes are caught before code is written

---

## Naming Convention

```
YYYY-MM-DD_task_slug.md
```

Examples:
- `2026-04-30_parse_pdb.md`
- `2026-05-01_graph_construction.md`
- `2026-05-02_focal_loss_and_dataset.md`

---

## When to Create a Plan

Create a plan for:
- Implementing any stub in `src/`
- Designing a new evaluation script
- Adding a new data processing step
- Setting up a new training configuration

Do NOT create a plan for:
- One-line fixes
- Documentation updates
- Config file edits
- Simple variable renames

---

## How to Use a Plan

1. Claude creates the plan file based on brain files.
2. User reviews and approves.
3. User copies `=== GEMINI TASK ===` block → pastes into Gemini.
4. Gemini returns implementation.
5. User applies code to `src/`.
6. User copies `=== CHATGPT REVIEW TASK ===` block → pastes into ChatGPT.
7. ChatGPT returns review.
8. User applies fixes.
9. Update experiment log if applicable.

---

## Template

See `docs/plans/plan_template.md`.

---

## Related

[[CLAUDE]] · [[plan_template]] · [[EXPERIMENT_INDEX]] · [[AGENTS]] · [[CLAUDE_PLANNER_PROMPTS]]
