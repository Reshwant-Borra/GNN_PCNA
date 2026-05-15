# REPO_MAP.md — GNN-PCNA Repository Map

> Read this before any task. Use it to navigate without scanning the repo.

## Directory Layout

```
GNN_PNCA/
├── CLAUDE.md                       # [READ FIRST] Agent behavior rules
├── REPO_MAP.md                     # [READ SECOND] This file
├── AGENTS.md                       # Multi-agent workflow + handoff protocol
├── KNOWN_BUGS.md                   # Active bugs — check before implementing
│
├── docs/
│   ├── knowledge/                  # PROJECT BRAIN — read selectively per task
│   │   ├── INDEX.md                # Root brain node — start here
│   │   ├── SYSTEM_OVERVIEW.md      # Goals, pipeline, stack
│   │   ├── RESEARCH_QUESTION.md    # Current question, success/failure criteria
│   │   ├── BIOLOGY_PCNA.md         # PCNA biology, AOH1996, known pockets
│   │   ├── PIPELINE.md             # End-to-end processing steps
│   │   ├── MODELS.md               # GNN architecture, baselines, hyperparams
│   │   ├── DATASETS.md             # Data sources, PDB IDs, directory conventions
│   │   ├── VALIDATION.md           # Validation criteria, RMSF/DCCM/volume
│   │   ├── KNOWN_LIMITATIONS.md    # What we can/cannot claim
│   │   ├── AI_WORKFLOW_RULES.md    # Full system rules in plain language
│   │   ├── NOTEBOOKLM_WORKFLOW.md  # How to use NotebookLM MCP
│   │   └── VISUALIZATION_SYSTEM.md # Visuals + how to render them
│   │
│   ├── experiments/                # Dated experiment logs
│   │   ├── EXPERIMENT_INDEX.md     # Master index of all experiments
│   │   ├── experiment_template.md  # Template for new experiments
│   │   ├── E001_baseline_gnn.md    # Baseline GNN run
│   │   ├── E002_pcna_pocket_prediction.md
│   │   └── E003_md_validation.md
│   │
│   ├── data/                       # Data documentation (not data files)
│   │   ├── DATA_INVENTORY.md       # What data exists and where
│   │   ├── DATA_SCHEMA.md          # Format specs for each data type
│   │   ├── PDB_STRUCTURES.md       # PDB files metadata
│   │   ├── PROCESSED_DATA.md       # What has been processed
│   │   └── DATA_PROVENANCE.md      # Source citations, download info
│   │
│   ├── implementation/             # Code documentation
│   │   ├── ARCHITECTURE.md         # Repo structure + design decisions
│   │   ├── FILE_GUIDE.md           # Per-file purpose + status
│   │   ├── COMMANDS.md             # CLI commands to run
│   │   ├── ENVIRONMENT.md          # Setup, dependencies
│   │   └── TESTING.md              # Test strategy
│   │
│   ├── plans/                      # Claude-generated implementation plans
│   │   ├── README.md               # How to use plan files
│   │   └── plan_template.md        # Template for new plans
│   │
│   ├── prompts/                    # Reusable prompts per agent
│   │   ├── CLAUDE_PLANNER_PROMPTS.md
│   │   ├── GEMINI_IMPLEMENTER_PROMPTS.md
│   │   ├── CHATGPT_REVIEW_PROMPTS.md
│   │   └── NOTEBOOKLM_EXTRACTION_PROMPTS.md
│   │
│   ├── notebooklm/                 # NotebookLM extraction outputs
│   │   ├── README.md               # How NLM outputs are stored
│   │   ├── extraction_template.md  # Template for extraction sessions
│   │   ├── raw_extractions/        # Raw NLM outputs (do not scan by default)
│   │   └── distilled_notes/        # Cleaned notes, ready to merge into knowledge/
│   │       ├── pocketminer_notes.md
│   │       ├── deepallo_notes.md
│   │       ├── pcna_biology_notes.md
│   │       └── md_validation_notes.md
│   │
│   ├── logs/                       # Decision logs + changelogs
│   │   ├── DECISIONS.md            # Architecture decisions + rationale
│   │   ├── BUG_LOG.md              # Bug history
│   │   ├── CHANGELOG.md            # What changed and when
│   │   └── RESEARCH_NOTES_LOG.md   # Informal running research log
│   │
│   ├── research/
│   │   └── paper_notes.md          # Literature summaries (existing)
│   │
│   └── visuals/                    # Mermaid + HTML diagrams
│       ├── README.md
│       ├── system_map.mmd          # Full AI + research system
│       ├── pipeline_map.mmd        # Pipeline stages
│       ├── data_flow.mmd           # Data flow
│       ├── experiment_flow.mmd     # Experiment lifecycle
│       ├── knowledge_graph_map.mmd # Obsidian brain structure
│       └── system_map.html         # Interactive canvas visualization
│
├── src/                            # Python source code
│   ├── data_processing/
│   │   ├── parse_pdb.py            # STUB — parse PDB, label residues
│   │   ├── graph_construction.py   # STUB — build PyG Data objects
│   │   └── __init__.py
│   ├── models/
│   │   ├── cryptic_gnn.py          # IMPLEMENTED — CrypticGNN model
│   │   └── __init__.py
│   ├── training/
│   │   ├── train.py                # STUB — training loop
│   │   ├── loss.py                 # STUB — focal loss
│   │   ├── dataset.py              # STUB — dataset loader
│   │   └── __init__.py
│   ├── evaluation/
│   │   ├── score_pockets.py        # STUB — pocket scoring + clustering
│   │   └── __init__.py
│   └── md/
│       ├── parse_trajectory.py     # STUB — RMSF, DCCM, volume tracking
│       └── __init__.py
│
└── data/                           # DO NOT SCAN — raw/binary data
    ├── raw/                        # Downloaded PDB files
    ├── processed/                  # Cleaned PDB (waters stripped)
    ├── graphs/                     # PyG .pt graph objects (binary)
    ├── labels/                     # Residue-level labels (.npy)
    └── trajectories/               # MD trajectories (.xtc, .gro)
```

---

## Do Not Scan By Default

| Directory | Reason |
|---|---|
| `data/raw/` | Large binary PDB files |
| `data/trajectories/` | Very large .xtc trajectory files (GB range) |
| `data/graphs/` | Binary PyTorch tensor files |
| `docs/notebooklm/raw_extractions/` | Long unprocessed NLM output |
| `.git/` | Git internals |
| `__pycache__/` | Python bytecode |
| `venv/` or `.venv/` | Python virtual environment |

---

## Task → Files Lookup

| Task | Read first | Then read |
|---|---|---|
| Understand the project | `docs/knowledge/INDEX.md` | `SYSTEM_OVERVIEW.md`, `PIPELINE.md` |
| GNN model work | `docs/knowledge/MODELS.md` | `src/models/cryptic_gnn.py` |
| Data processing task | `docs/knowledge/PIPELINE.md` | `src/data_processing/`, `DATASETS.md` |
| Training setup | `docs/knowledge/MODELS.md`, `DATASETS.md` | `src/training/` |
| MD validation | `docs/knowledge/VALIDATION.md` | `src/md/parse_trajectory.py` |
| Run/log experiment | `docs/experiments/EXPERIMENT_INDEX.md` | relevant `E0XX_*.md` |
| Debugging | `KNOWN_BUGS.md` | `docs/logs/BUG_LOG.md` |
| Extract from paper | `docs/knowledge/NOTEBOOKLM_WORKFLOW.md` | `docs/prompts/NOTEBOOKLM_EXTRACTION_PROMPTS.md` |
| Create plan | `docs/plans/plan_template.md` | relevant `docs/knowledge/` files |
| Send to Gemini | `AGENTS.md` | `docs/prompts/GEMINI_IMPLEMENTER_PROMPTS.md` |
| Send to ChatGPT | `AGENTS.md` | `docs/prompts/CHATGPT_REVIEW_PROMPTS.md` |
| Biology / context | `docs/knowledge/BIOLOGY_PCNA.md` | `docs/research/paper_notes.md` |

---

## Source File Status

| File | Status | Next Action |
|---|---|---|
| `src/models/cryptic_gnn.py` | **Implemented** | Ready for training |
| `src/data_processing/parse_pdb.py` | **Stub** | HIGH PRIORITY — implement first |
| `src/data_processing/graph_construction.py` | **Stub** | HIGH PRIORITY — implement second |
| `src/training/loss.py` | **Stub** | HIGH — focal loss |
| `src/training/dataset.py` | **Stub** | HIGH — PyG dataset loader |
| `src/training/train.py` | **Stub** | MEDIUM — training loop |
| `src/evaluation/score_pockets.py` | **Stub** | MEDIUM — clustering + ranking |
| `src/md/parse_trajectory.py` | **Stub** | LATER — needs MD data |

---

## Visual Entry Points

| File | How to open |
|---|---|
| `docs/visuals/system_map.html` | `start docs\visuals\system_map.html` (Windows) |
| Any `.mmd` file | Open in Obsidian with Mermaid plugin |
| Obsidian graph view | Open vault root in Obsidian, use Graph View |

---

## Related

[[CLAUDE]] · [[AGENTS]] · [[INDEX]] · [[FILE_GUIDE]] · [[VISUALIZATION_SYSTEM]] · [[KNOWN_BUGS]]
