# NOTEBOOKLM_WORKFLOW.md — NotebookLM MCP Usage Guide

→ Links: [[AI_WORKFLOW_RULES]] | [[BIOLOGY_PCNA]] | [[MODELS]] | [[VALIDATION]]

---

## What NotebookLM Is For

NotebookLM is a source-grounded research tool. It reads your loaded documents and answers questions based only on those sources.

**Use it when:**
- You need exact facts from a paper (method details, dataset specs, reported metrics)
- You want to summarize a paper without hallucinating
- You want to compare two papers side-by-side
- You need to extract dataset details, model architecture, evaluation metrics, or limitations

**Do NOT use it when:**
- You need to navigate the repo
- You need to write code
- You need an architecture decision not grounded in a paper

---

## Output Pipeline

```
NotebookLM extraction
  → docs/notebooklm/raw_extractions/   (if output is long — optional)
  → docs/notebooklm/distilled_notes/   (always create a distilled version)
  → merge into docs/knowledge/          (when relevant to project brain)
```

**Rule:** Raw NLM output is NOT the brain. Distilled Markdown is the brain.

Do not paste huge raw extractions into `docs/knowledge/`. Distill first.

---

## Prompt Templates

### Extract method details

```
Extract the exact method used in [PAPER TITLE] for [SPECIFIC ASPECT].

Format as bullet points:
- Architecture: ...
- Input features: ...
- Output: ...
- Training setup: ...
- Loss function: ...
- Key hyperparameters: ...

Only use information from the loaded source. Do not speculate.
Cite the source for each claim (e.g., "Section 3.2").
```

---

### Extract dataset details

```
Extract all dataset information from [PAPER TITLE].

Format as bullet points:
- Dataset name: ...
- Number of proteins/examples: ...
- Source/availability: ...
- Train/val/test split: ...
- Features used: ...
- Labels/annotations: ...
- Any known limitations mentioned: ...

Only use information from the loaded source.
```

---

### Extract validation metrics

```
Extract all evaluation metrics reported in [PAPER TITLE].

Format as a table:
| Metric | Value | Dataset | Notes |

Include:
- Primary metrics (AUROC, AUPRC, accuracy, etc.)
- Baselines compared against
- Ablation study results if reported
- Statistical significance if reported

Only use information from the loaded source.
```

---

### Compare two papers

```
Compare [PAPER A] and [PAPER B] on the following dimensions.

Format as a comparison table:
| Dimension | Paper A | Paper B |
|---|---|---|
| Task | | |
| Architecture | | |
| Dataset | | |
| Key metric | | |
| Limitations | | |
| Relevance to PCNA project | | |

Only use information from the loaded sources.
```

---

### Produce Obsidian-ready notes

```
Summarize [PAPER TITLE] as a compact set of bullet points for a research knowledge base.

Format:
## Method
- [bullet points]

## Dataset
- [bullet points]

## Results
- [bullet points]

## Limitations
- [bullet points]

## Relevance to GNN-PCNA project
- [bullet points]

Keep each bullet under 20 words.
Do not speculate. Only use information from the loaded source.
```

---

## Output Rules

| Rule | Reason |
|---|---|
| Always save distilled version to `docs/notebooklm/distilled_notes/` | Prevents re-extraction next session |
| For long outputs (> 500 words): save raw to `raw_extractions/` too | Preserves full detail without bloating knowledge/ |
| Mark uncertain claims: `Needs verification` | Maintains scientific rigor |
| Always note which source was queried | Traceability |
| Merge into `docs/knowledge/` only when relevant | Keeps brain compact |

---

## Distilled Notes → Knowledge Merge Rules

| Source file | Merge target |
|---|---|
| `pocketminer_notes.md` | `docs/knowledge/MODELS.md` (baselines section) |
| `deepallo_notes.md` | `docs/knowledge/MODELS.md` (baselines section) |
| `pcna_biology_notes.md` | `docs/knowledge/BIOLOGY_PCNA.md` |
| `md_validation_notes.md` | `docs/knowledge/VALIDATION.md` |

---

## Files in This System

| File | Purpose |
|---|---|
| `docs/notebooklm/README.md` | Overview of the extraction system |
| `docs/notebooklm/extraction_template.md` | Blank template for a new extraction session |
| `docs/notebooklm/raw_extractions/` | Long raw outputs (do not scan by default) |
| `docs/notebooklm/distilled_notes/pocketminer_notes.md` | PocketMiner paper extraction |
| `docs/notebooklm/distilled_notes/deepallo_notes.md` | DeepAllo paper extraction |
| `docs/notebooklm/distilled_notes/pcna_biology_notes.md` | PCNA biology extraction |
| `docs/notebooklm/distilled_notes/md_validation_notes.md` | MD validation methods extraction |
