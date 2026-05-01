# docs/knowledge/INDEX.md — Brain Root

> This is the first file Claude reads. It maps the entire knowledge system.
> Read only what you need for the current task. Links are Obsidian-compatible.

---

## How to Use This Brain

1. Identify your task type from the table below.
2. Read only the listed files — skip the rest.
3. After experiments or decisions, update the relevant file(s).
4. Never delete entries from experiment logs — append or create new.

---

## Brain File Map

| File | What it contains | Read when |
|---|---|---|
| [[SYSTEM_OVERVIEW]] | Project goals, pipeline sketch, stack | Starting a new session |
| [[RESEARCH_QUESTION]] | Current question, success/failure criteria | Planning experiments |
| [[BIOLOGY_PCNA]] | PCNA structure, AOH1996, cryptic pocket context | Biology-adjacent tasks |
| [[PIPELINE]] | End-to-end processing steps with I/O specs | Data or training tasks |
| [[MODELS]] | GNN architecture, baselines, hyperparams | Model-related tasks |
| [[DATASETS]] | PDB IDs, data sources, directory conventions | Data tasks |
| [[VALIDATION]] | RMSF, DCCM, volume criteria, positive control | Validation tasks |
| [[KNOWN_LIMITATIONS]] | What the model can/cannot claim | Before any claims |
| [[AI_WORKFLOW_RULES]] | Full system in plain language | When confused about workflow |
| [[NOTEBOOKLM_WORKFLOW]] | How to use NotebookLM MCP | Research extraction tasks |
| [[VISUALIZATION_SYSTEM]] | Mermaid diagrams, how to render | Visualization tasks |

---

## Experiment Index

→ See [[EXPERIMENT_INDEX]] in `docs/experiments/EXPERIMENT_INDEX.md`

---

## Data Documentation

→ See `docs/data/DATA_INVENTORY.md` for what data exists and where.

---

## Implementation Documentation

→ See `docs/implementation/FILE_GUIDE.md` for per-file status.

---

## What to Update After Each Session

| Event | Update this file |
|---|---|
| New experiment run | `docs/experiments/EXPERIMENT_INDEX.md` + new `E0XX_*.md` |
| Architecture decision | `docs/logs/DECISIONS.md` + `docs/implementation/ARCHITECTURE.md` |
| Bug found or fixed | `KNOWN_BUGS.md` + `docs/logs/BUG_LOG.md` |
| Paper extracted via NLM | `docs/notebooklm/distilled_notes/` + merge into `docs/knowledge/` |
| New data acquired | `docs/data/DATA_INVENTORY.md` + `docs/data/DATA_PROVENANCE.md` |
| Significant limitation discovered | `docs/knowledge/KNOWN_LIMITATIONS.md` |

---

## Quick Status (update manually)

| Item | Status |
|---|---|
| CrypticGNN model | Implemented |
| Data processing stubs | Pending implementation |
| Training loop | Pending implementation |
| NotebookLM setup | Ready to use |
| First experiment (E001) | Planned |
| MD trajectory available | Not yet |
