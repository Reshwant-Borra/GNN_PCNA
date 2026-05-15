# NotebookLM Extraction System

## Purpose

This directory stores all outputs from NotebookLM MCP research extraction sessions.

---

## Directory Structure

```
docs/notebooklm/
├── README.md                  # This file
├── extraction_template.md     # Template for a new extraction session
├── raw_extractions/           # Full unedited NLM outputs (do not scan by default)
│   └── *.md                   # Named by paper + date
└── distilled_notes/           # Cleaned, structured summaries ready to use
    ├── pocketminer_notes.md   # PocketMiner paper
    ├── deepallo_notes.md      # DeepAllo paper
    ├── pcna_biology_notes.md  # PCNA biology papers
    └── md_validation_notes.md # MD validation methods
```

---

## Workflow

### Step 1 — Extract
- Load papers into NotebookLM as sources
- Use prompts from `docs/prompts/NOTEBOOKLM_EXTRACTION_PROMPTS.md`
- Copy output from NotebookLM

### Step 2 — Save raw (optional, for long outputs)
- Save full output to `raw_extractions/PAPERNAME_YYYYMMDD.md`
- Keep for reference but don't reference in planning sessions

### Step 3 — Distill
- Create or update relevant file in `distilled_notes/`
- Use `extraction_template.md` as structure guide
- Keep each bullet under 25 words
- Mark anything uncertain as `Needs verification`

### Step 4 — Merge into brain
- Update relevant `docs/knowledge/` file with key facts
- Example: PocketMiner architecture → `docs/knowledge/MODELS.md` baselines section

---

## Rules

| Rule | Reason |
|---|---|
| Raw NLM output is NOT the brain | Raw output is often verbose and unstructured |
| Always distill before merging into knowledge/ | Keeps brain files lean |
| Mark uncertain claims | Maintains scientific integrity |
| Note the source notebook/paper in the distilled file | For traceability |
| Never paste multi-paragraph blocks into knowledge/ | Brain files must stay skimmable |

---

## What NotebookLM Cannot Do

- Read code files
- Navigate the repo
- Verify computational results
- Make architectural decisions

Use Claude for those.

---

## Related

[[NOTEBOOKLM_WORKFLOW]] · [[extraction_template]] · [[NOTEBOOKLM_EXTRACTION_PROMPTS]] · [[pocketminer_notes]] · [[deepallo_notes]] · [[pcna_biology_notes]] · [[md_validation_notes]] · [[AI_WORKFLOW_RULES]]
