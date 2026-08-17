# paper_engine

Research-paper generation subsystem for GNN ResearchOS. Builds a competition-grade
Word manuscript for the GNN-PCNA project from **real** experimental data, runs
entirely on a local CPU (Ollama), and obeys the project's integrity guardrails.

## Install

```bash
pip install -e ".[paper]"          # adds python-docx, matplotlib, MDAnalysis, rank-bm25, pdfplumber, ...
ollama pull gemma3:4b              # default writer model (already present)
```

## Commands

```bash
# 1. Render the publication figures from real Phase-3 run manifests, register them.
python -m research_os paper-figures

# 2. Generate the full competition draft (figures + manuscript.docx) and self-review.
python -m research_os paper --author "Your Name" --date 2026-05-30

# 3. Build a legal open-access literature corpus (discover / download / index).
python -m research_os paper-corpus --discover-only            # list OA sources
python -m research_os paper-corpus --max-gb 30 --index        # crawl + BM25 index
```

Outputs land in `paper/`: `manuscript.docx`, `manuscript.md`, `figures/`,
`build_manifest.json`. The corpus lands in `data/literature/`.

## What it does

- **Figures** (`paper_engine/figures/`): loads real validation metrics, baselines,
  ablations, label/split stats from the run manifests and renders journal-grade
  figures. Numbers are never hardcoded — the loaders reproduce the published values
  and raise if a manifest is missing. MD figures (RMSD/RMSF/DCCM) render only when
  the trajectory topology is available.
- **Manuscript** (`paper_engine/manuscript/`): a grounding fact sheet → judge-flow
  narrative plan → voice-conditioned, anti-overclaim LLM drafting → real-citation
  bibliography → docx assembly → self-review via the existing ResearchOS claim audit.
- **Corpus** (`paper_engine/corpus/`): legal open-access discovery (OpenAlex,
  Unpaywall), a resumable rate-limited robots-aware downloader, pdfplumber
  extraction, and a BM25 index for citation grounding.

## Integrity model (non-negotiable)

- **Real data only.** Every figure and statistic comes from a real run manifest. The
  held-out test set was **not** evaluated; the engine never reports test results.
- **Anti-overclaim.** The writer is forbidden the project's banned phrases (e.g.
  "validated cryptic pocket"); output is scanned and regenerated/sanitised if any slip
  through. Self-review runs the existing `claim-audit` over the draft.
- **Human sign-off stays.** The output is an explicitly-marked DRAFT. ResearchOS never
  auto-approves a final manuscript or submission.
- **Legal corpus only.** Downloads only files an open-access location exposes; respects
  robots.txt and per-host rate limits. No paywall bypass.

## Configuration (environment variables)

| Variable | Default | Purpose |
| --- | --- | --- |
| `PAPER_ENGINE_MODEL` | `gemma3:4b` | Writer model. For sharper prose: `ollama pull qwen2.5:14b-instruct` then set this. |
| `PAPER_ENGINE_MD_TOPOLOGY` | (auto) | Path to the solvated-system PDB/PSF for the MD trajectory. |
| `PAPER_ENGINE_MAILTO` | advay's email | Contact for the OpenAlex/Unpaywall polite pool. |
| `PAPER_ENGINE_OLLAMA_THREADS` | (unset) | Pin Ollama threads. **Leave unset** — forcing all cores oversubscribes hybrid CPUs (~9× slower). |
| `PAPER_ENGINE_DRAFT_WORKERS` | `4` | Sections drafted concurrently. This is how the engine saturates a hybrid CPU: a single Ollama stream uses only ~35% (the P-cores), but 4 parallel streams reach ~90%+ and cut wall-clock. Use a model small enough that N copies fit in RAM (gemma3:4b ≈ 3.3 GB each). Set to 1 for sequential. |

## Known data caveats

1. **MD topology missing.** `data/md/1W60_production.dcd` is a solvated 356,789-atom
   system, but its topology (OpenMM PDB/PSF) is not in the repo, so MD figures are
   skipped until you provide it (drop it in `data/md/` or set `PAPER_ENGINE_MD_TOPOLOGY`).
2. **Trajectory length.** The DCD on disk is **636 frames ≈ 6.35 ns** (10 ps/frame),
   not 100 ns. Captions report the real length read from the file header.

## Quality tips for prestigious judging

- Use a stronger local model for the prose (`PAPER_ENGINE_MODEL=qwen2.5:14b-instruct`),
  then **revise every section yourself** — you must be able to defend each figure and
  claim to judges, and the draft is a starting point, not a submission.
- Run `python -m research_os paper-corpus --max-gb 30 --index` first so the writer can
  ground citations in a real literature index (RAG).
- Provide the MD topology to unlock the RMSD/RMSF/DCCM figures.
