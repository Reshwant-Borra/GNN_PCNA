# Plan: Full System Architecture Scope

**Date:** 2026-05-15
**Status:** draft
**Experiment:** N/A — architecture scoping only

---

## Goal

Define the complete end-to-end architecture for GNN-PCNA: from parallel web scraping through Gemma-powered credibility verification, Obsidian vault storage, and into the GNN training pipeline — and surface every gap blocking progress.

---

## Brain Files Read

- `CLAUDE.md` — workflow rules, role separation
- `README.md` — pipeline overview, validation targets
- `AGENTS.md` — agent roles, handoff protocol
- `docs/implementation/ARCHITECTURE.md` — GNN design decisions
- `docs/knowledge/RESEARCH_QUESTION.md` — sub-questions, success criteria
- `agents/pcna_crawler.py` — 13-source crawler + 5-layer validation
- `agents/local_agent.py` — Ollama LLM agent (currently Qwen2.5:7b)
- `src/models/cryptic_gnn.py` — CrypticGNN model
- `src/data_processing/fetch_structures.py` — PDB downloader
- `src/training/dataset.py` — PocketDataset

---

## Complete System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                  LAYER 1: PARALLEL DATA COLLECTION              │
│                                                                 │
│  agents/pcna_crawler.py  (13 sources, ThreadPoolExecutor)       │
│  ├── RCSBSource       ├── PDBESource      ├── AlphaFoldSource  │
│  ├── SIFTSSource      ├── UniProtSource   ├── NCBISource       │
│  ├── InterProSource   ├── ZenodoSource    ├── GitHubSource     │
│  ├── PubMedSource     ├── BioRxivSource   ├── PubChemSource   │
│  └── ChEMBLSource                                              │
│                    ↓  SourceRecord objects                      │
└─────────────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│              LAYER 2: CREDIBILITY VERIFICATION                  │
│                                                                 │
│  Existing: ValidationPipeline (5 heuristic layers)             │
│    L1 Network → L2 Format → L3 Structural → L4 Biological      │
│    → L5 Provenance                                              │
│                                                                 │
│  NEW (L6): agents/gemma_verifier.py                            │
│    Gemma 3:4b via Ollama (localhost:11434)                      │
│    Input:  paper abstract/title OR PDB metadata                 │
│    Prompt: "Is this directly relevant to PCNA cryptic pocket   │
│             prediction or GNN protein structure analysis?       │
│             Score 1-10 with one-line reason."                   │
│    Threshold: score < 6 → drop; ≥ 6 → pass to vault           │
│    Applies to: record_type == "paper" | "dataset"              │
│    Skips:  pdb_structure records (L3 structural already strict) │
└─────────────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│              LAYER 3: OBSIDIAN VAULT STORAGE                    │
│                                                                 │
│  NEW: agents/obsidian_writer.py                                 │
│                                                                 │
│  pdb_structure → docs/knowledge/data/structures/{PDB_ID}.md    │
│    (frontmatter: uid, source, resolution, chains, relevance,   │
│     validation scores, download_url)                            │
│                                                                 │
│  paper → docs/knowledge/literature/{PMID_or_DOI}.md           │
│    (frontmatter: title, authors, pmid/doi, gemma_score,        │
│     gemma_reason, query that found it, url)                     │
│                                                                 │
│  dataset → docs/knowledge/data/datasets/{uid}.md              │
│    (frontmatter: title, source, doi, download_url)              │
│                                                                 │
│  compound → docs/knowledge/compounds/{uid}.md                  │
│    (frontmatter: name, smiles, cid, relevance)                  │
│                                                                 │
│  Also updates docs/knowledge/INDEX.md with wikilinks            │
│  Output: data/catalog/pcna_data_catalog.json (unchanged)        │
│           + data/catalog/download_queue.txt (unchanged)         │
└─────────────────────────────────────────────────────────────────┘
                         ↓
          ┌──────────────┴──────────────┐
          ↓                             ↓
┌─────────────────┐          ┌──────────────────────┐
│  PDB STRUCTURES │          │  PAPERS & DATASETS   │
│                 │          │                      │
│ fetch_structures│          │ Manual step:         │
│ .py             │          │ NotebookLM MCP       │
│  ↓ data/raw/    │          │  → distilled_notes/  │
│  ↓ data/processed/        │  → docs/knowledge/   │
└─────────────────┘          └──────────────────────┘
          ↓
┌─────────────────────────────────────────────────────────────────┐
│              LAYER 4: GRAPH CONSTRUCTION PIPELINE               │
│                                                                 │
│  src/data_processing/parse_pdb.py                               │
│    Input:  data/processed/{PDB_ID}_clean.pdb                   │
│    Output: list[Residue]  (26 features per residue)             │
│    Labels: residues within 6Å of AOH1996 in 8GLA → y=1        │
│                                                                 │
│  src/data_processing/graph_construction.py                      │
│    Input:  list[Residue]                                        │
│    Output: torch_geometric.data.Data                            │
│      x:          (N, 26)  node features                         │
│      edge_index: (2, E)   Cα–Cα pairs within 8Å               │
│      edge_attr:  (E, 2)   [distance, seq_separation]           │
│      y:          (N,)     pocket label float32                  │
│    Written to: data/graphs/{PDB_ID}.pt                         │
│                                                                 │
│  Split (at protein level, NOT residue level):                   │
│    data/cryptosite/train/*.pt   (~80 proteins)                 │
│    data/cryptosite/val/*.pt     (~10 proteins)                 │
│    data/cryptosite/test/*.pt    (~10 proteins, held-out)       │
│    data/pcna/1W60.pt            apo PCNA inference             │
│    data/pcna/8GLA.pt            holo PCNA positive control     │
└─────────────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│              LAYER 5: GNN MODEL (CrypticGNN)                    │
│                                                                 │
│  src/models/cryptic_gnn.py                                      │
│                                                                 │
│  NodeEmbedding: Linear(26→256) + ReLU + LayerNorm              │
│  4 × GATv2Conv(256, heads=4, edge_dim=2, concat=True)          │
│    + residual: LayerNorm(h + conv(h))                           │
│  Scoring head: Linear(256→64) → ReLU → Dropout → Linear(64→1) │
│  Output: sigmoid → (N,) prioritization score ∈ [0,1]             │
│                                                                 │
│  Training: src/training/train.py                                │
│    Loss:    focal loss (γ=2, α=0.25) — src/training/loss.py   │
│    Dataset: PocketDataset — src/training/dataset.py            │
│    Checkpoint: checkpoints/best_model.pt                        │
└─────────────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│              LAYER 6: EVALUATION + MD VALIDATION                │
│                                                                 │
│  src/evaluation/score_pockets.py                                │
│    Input:  (N,) scores on 8GLA                                  │
│    Step 1: threshold at 0.5 → candidate residues               │
│    Step 2: DBSCAN spatial clustering → pocket candidates        │
│    Step 3: rank by mean cluster score                           │
│    Gate:   AOH1996 pocket mean score > 0.7 before trusting     │
│                                                                 │
│  src/md/parse_trajectory.py                                     │
│    Input:  data/trajectories/1W60_apo.xtc                      │
│    Computes: RMSF per residue, DCCM, transient pocket volumes  │
│    Validates: predicted pockets show RMSF > 1.5Å + DCCM block  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Gemma 3:4b Integration

| Capability | Use in this project |
|---|---|
| 4.3B params Q4_K_M, 128K context | Fast local inference, no API cost |
| Vision (multimodal) | Future: read protein structure figures from papers |
| Ollama OpenAI-compatible API | Drop-in with existing `local_agent.py` pattern |

**Immediate changes:**

1. Update `agents/local_agent.py` line 24:
   ```python
   MODEL = "gemma3:4b"   # was: "qwen2.5:7b"
   ```

2. Create `agents/gemma_verifier.py` — Gemma as L6 credibility scorer:
   ```python
   # Input: SourceRecord with title + description
   # Output: gemma_score (1-10), gemma_reason (str)
   # Prompt template stored in: docs/prompts/GEMMA_VERIFIER_PROMPT.md
   ```

3. Add `gemma_score` and `gemma_reason` fields to `SourceRecord` dataclass.

---

## Gaps Blocking Progress (Critical)

| # | Gap | Severity | Location |
|---|---|---|---|
| G1 | No PyG `.pt` graph files exist — training is completely blocked | **CRITICAL** | `data/cryptosite/train/` (empty) |
| G2 | `fetch_from_catalog` reads `catalog["pdb_entries"]` but catalog writes `catalog["passed"]` — silent bug, returns 0 structures | **CRITICAL** | `fetch_structures.py:229` |
| G3 | `agents/gemma_verifier.py` doesn't exist — Gemma 3:4b unused | high | new file needed |
| G4 | `agents/obsidian_writer.py` doesn't exist — scraped data never reaches `docs/knowledge/` | high | new file needed |
| G5 | `local_agent.py` MODEL still set to `qwen2.5:7b` — will fail (model not pulled) | high | `agents/local_agent.py:24` |
| G6 | `data/trajectories/` doesn't exist — MD validation blocked | medium | need MD run (GROMACS/OpenMM) |
| G7 | No pipeline runner script — each stage must be invoked manually | medium | new `scripts/run_pipeline.py` |

---

## Files to Create (ordered by dependency)

| Priority | File | Blocks |
|---|---|---|
| 1 | Fix `fetch_structures.py:229` key bug | catalog→fetch integration |
| 2 | Fix `local_agent.py:24` model name | local LLM agent |
| 3 | `agents/gemma_verifier.py` | L6 credibility layer |
| 4 | `agents/obsidian_writer.py` | vault storage |
| 5 | Build graph pipeline: `parse_pdb.py` → `graph_construction.py` → write `.pt` files | training |
| 6 | `scripts/run_pipeline.py` — orchestrates full crawl→fetch→graph→train | end-to-end |

---

## Data Flow Summary (Concrete Paths)

```
agents/pcna_crawler.py
  → data/catalog/pcna_data_catalog.json
  → data/catalog/download_queue.txt

agents/gemma_verifier.py   [NEW]
  reads: data/catalog/pcna_data_catalog.json
  writes: gemma_score into catalog (in-place update)

agents/obsidian_writer.py  [NEW]
  reads: data/catalog/pcna_data_catalog.json (verified + gemma-scored)
  writes: docs/knowledge/data/structures/*.md
          docs/knowledge/literature/*.md
          docs/knowledge/data/datasets/*.md

src/data_processing/fetch_structures.py
  reads: data/catalog/download_queue.txt
  writes: data/raw/*.pdb  →  data/processed/*_clean.pdb

src/data_processing/parse_pdb.py
  reads: data/processed/*_clean.pdb
  output: list[Residue]

src/data_processing/graph_construction.py
  reads: list[Residue]
  writes: data/cryptosite/train/*.pt
          data/cryptosite/val/*.pt
          data/pcna/1W60.pt
          data/pcna/8GLA.pt

src/training/train.py
  reads: data/cryptosite/train/*.pt  data/cryptosite/val/*.pt
  writes: checkpoints/best_model.pt

src/evaluation/score_pockets.py
  reads: checkpoints/best_model.pt + data/pcna/8GLA.pt
  writes: docs/experiments/E{NNN}_*.md results
```

---

## Risks / Edge Cases

| Risk | Mitigation |
|---|---|
| Gemma 3:4b hallucinating relevance scores | Prompt with concrete examples; require numeric score + one-line reason; cross-check against L4 keyword score |
| Obsidian writer creating duplicate notes | Wikilink slug = uid hash; check file existence before writing |
| CryptoSite split leakage (same protein in train + val) | Split at PDB ID level before building graphs; write split manifest to `data/splits/cryptosite_split.json` |
| `data/cryptosite/` subdir expected by `PocketDataset` but doesn't exist yet | Build graph pipeline first (G1 fix) |
| fetch_from_catalog bug returns 0 → no new PDB downloads | Fix key from `pdb_entries` → `passed` (G2 fix) |
| Gemma Ollama endpoint not running | Wrap `gemma_verifier.py` with health-check; log warning and skip L6 if endpoint down |

---

## Implementation Steps (for Gemini)

### Stage A — Critical bug fixes (do first, 15 min)
1. `fetch_structures.py:229`: change `catalog.get("pdb_entries", [])` → `catalog.get("passed", [])`; also add filter for `r["record_type"] == "pdb_structure"` since `passed` includes papers/datasets too.
2. `local_agent.py:24`: change `MODEL = "qwen2.5:7b"` → `MODEL = "gemma3:4b"`

### Stage B — Gemma verifier (new file)
3. Create `agents/gemma_verifier.py`:
   - Reuse `local_agent.py` OpenAI client pattern
   - `verify_record(record: dict) -> tuple[int, str]` — returns (score, reason)
   - `verify_catalog(catalog_path: Path) -> Path` — updates catalog JSON in-place with `gemma_score` + `gemma_reason` fields on each record
   - Only runs on `record_type in ("paper", "dataset")`; pdb_structure records auto-pass with score=7

### Stage C — Obsidian writer (new file)
4. Create `agents/obsidian_writer.py`:
   - `write_structure_note(record: dict) -> Path`
   - `write_paper_note(record: dict) -> Path`
   - `write_dataset_note(record: dict) -> Path`
   - `update_index(new_links: list[str])` — appends to `docs/knowledge/INDEX.md` under `## Auto-indexed`
   - Reads catalog, filters `passed=True` AND `gemma_score >= 6` (or `record_type == "pdb_structure"`)

### Stage D — Graph pipeline (unblocks training)
5. Verify `parse_pdb.py` is complete (has .pyc, likely ok)
6. Verify `graph_construction.py` is complete
7. Run: `python -m src.data_processing.fetch_structures --cryptosite --strip`
8. Build a `scripts/build_graphs.py` that iterates `data/processed/*.pdb` → `data/graphs/*.pt`
9. Create train/val/test split script: `scripts/make_split.py` — writes symlinks or copies to `data/cryptosite/train/`, `data/cryptosite/val/`, `data/cryptosite/test/`

---

## === GEMINI TASK (Stage A — Bug Fixes) ===

```
Project: GNN-PCNA cryptic pocket prediction
Stack: Python 3.10+

Fix 1: src/data_processing/fetch_structures.py line 229
  Change: entries  = [e for e in catalog.get("pdb_entries", [])]
  To:     entries  = [e for e in catalog.get("passed", [])
                      if e.get("record_type") == "pdb_structure"]

  Also update line 232 to use e.get("uid") instead of e.get("pdb_id"):
  pdb_ids = [e["uid"].split("_")[0].upper()[:4] for e in entries]

Fix 2: agents/local_agent.py line 24
  Change: MODEL = "qwen2.5:7b"
  To:     MODEL = "gemma3:4b"

Return: both complete fixed files + one-line summary per file.
```

---

## === GEMINI TASK (Stage B — Gemma Verifier) ===

```
Project: GNN-PCNA cryptic pocket prediction
Stack: Python 3.10+, openai (Ollama-compatible), pathlib, json

Create: agents/gemma_verifier.py

Context:
- Ollama runs Gemma 3:4b at localhost:11434 (OpenAI-compatible API)
- Catalog file: data/catalog/pcna_data_catalog.json
- Schema: catalog["passed"] is a list of SourceRecord dicts
  Each record has: uid, record_type, title, description, source, relevance, url
  After this script: also has gemma_score (int 1-10), gemma_reason (str)

Requirements:
- Function: verify_record(record: dict, client: OpenAI) -> tuple[int, str]
    Prompt template:
      "You are evaluating training data sources for a graph neural network
       predicting cryptic binding pockets on the protein PCNA.
       Title: {title}
       Abstract/Description: {description[:400]}
       Score the relevance of this source to PCNA cryptic pocket research on
       a scale of 1-10, where 10=directly reports PCNA structure/binding/pocket
       data and 1=completely unrelated. Reply with ONLY: <score>\n<one-line reason>"
    Parse response: first line = int score, second line = reason string
    On parse error: return (5, "parse error")
    Temperature: 0.1 (deterministic)

- Function: verify_catalog(catalog_path: Path, min_gemma: int = 6) -> Path
    Loads catalog JSON
    For each record in catalog["passed"]:
      if record_type == "pdb_structure": set gemma_score=7, gemma_reason="structural data auto-approved"
      else: call verify_record
    Writes updated catalog back to same path
    Returns path

- CLI: python agents/gemma_verifier.py [--catalog path] [--min-score 6]
    Prints per-record: uid | type | gemma_score | reason
    Summary: X approved, Y dropped (below min)

Do NOT apply min_gemma filtering inside this script — just score and write.
Filtering happens in obsidian_writer.py.

Return: complete implemented file.
```

---

## === CHATGPT REVIEW TASK ===

```
Project: GNN-PCNA (Python, Ollama/OpenAI SDK, pathlib, json)
Changed files: agents/gemma_verifier.py (new), fetch_structures.py (bug fix)

[paste both files here]

Known bugs: none currently in KNOWN_BUGS.md

Review checklist:
1. Does verify_record handle Ollama returning non-numeric first line? (parse error path)
2. Does verify_catalog handle catalog JSON with no "passed" key gracefully?
3. Is the catalog written atomically (write to temp then rename) to avoid corrupt JSON on crash?
4. fetch_structures.py fix: does the new uid parsing handle AlphaFold IDs like "AF-P12004" correctly?
5. Is the Ollama client initialized once (not per-record)?
6. Does the CLI print progress so a long catalog run doesn't look hung?

Return: numbered issues (severity: critical | warning | suggestion) only.
```

---

## Related

[[CLAUDE]] · [[AGENTS]] · [[ARCHITECTURE]] · [[PIPELINE]] · [[MODELS]] · [[KNOWN_BUGS]] · [[EXPERIMENT_INDEX]]
