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


## Auto-Indexed

- [[1AXC]]
- [[1W60]]
- [[8GLA]]
- [[1W61]]
- [[CHEMBL_CHEMBL2346488]]
- [[5E0U]]
- [[5MLO]]
- [[8F5Q]]
- [[1U7B]]
- [[9N3L]]
- [[CID_126718388]]
- [[4ZTD]]
- [[5E0V]]
- [[5MLW]]
- [[6HVO]]
- [[3VKX]]
- [[2ZVL]]
- [[2ZVM]]
- [[1VYM]]
- [[4RJF]]
- [[5YD8]]
- [[6K3A]]
- [[7KQ0]]
- [[5MOM]]
- [[5YCO]]
- [[CHEMBL_CHEMBL5574]]
- [[CHEMBL_CHEMBL5465218]]
- [[PMID_39693053]]
- [[8UMY]]
- [[1UL1]]
- [[8COB]]
- [[7NV0]]
- [[9GY0]]
- [[5E0T]]
- [[8UMU]]
- [[9EOA]]
- [[7M5N]]
- [[8UN0]]
- [[6FCM]]
- [[9CG4]]
- [[6GIS]]
- [[8UMT]]
- [[6CBI]]
- [[3TBL]]
- [[5MAV]]
- [[8GL9]]
- [[9B8T]]
- [[6QC0]]
- [[4D2G]]
- [[8GCJ]]
- [[6FCN]]
- [[6VVO]]
- [[8E84]]
- [[6QCG]]
- [[6GWS]]
- [[9CHM]]
- [[3WGW]]
- [[8UI8]]
- [[5IY4]]
- [[9NE6]]
- [[3P87]]
- [[7M5M]]
- [[2ZVK]]
- [[7EFA]]
- [[7M5L]]
- [[1U76]]
- [[1VYJ]]
- [[8UI9]]
- [[6TNY]]
- [[6EHT]]
- [[8UII]]
- [[7KQ1]]
- [[8ZWO]]
- [[9IIN]]
- [[9SRI]]
- [[9UIQ]]
- [[9VGW]]
- [[PMID_40216579]]
- [[NCBI_33239451]]
- [[NCBI_4505641]]
- [[NCBI_129694]]
- [[NCBI_31790138]]
- [[NCBI_31790136]]
- [[NCBI_31790134]]
- [[NCBI_119630835]]
- [[NCBI_119630834]]
- [[NCBI_119630833]]
- [[NCBI_38383150]]
- [[NCBI_12653441]]
- [[NCBI_387005]]
- [[NCBI_31790295]]
- [[NCBI_21902516]]
- [[NCBI_49456555]]
- [[NCBI_49168490]]
- [[PMID_40714812]]
