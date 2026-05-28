---
type: parallel-track-handoff
date: 2026-05-28
author: Reshwant-Borra
for: Advay
status: authorized
phase3_dependency: NONE — all tasks here are fully independent of Phase 3
---

# Advay Parallel Track — Work Independent of Phase 3

Reshwant is handling all of Phase 3 (training, baselines, model freeze, test evaluation).
**You do not touch Phase 3 at all.** This document defines work you can do in parallel
that will be ready and waiting when Phase 3 completes.

---

## Completion Log

**Fill this in as you finish each task.** One entry per task — what you built, what files
changed, any decisions made, and the date.

| Date | Task | What you did | Key files |
|------|------|--------------|-----------|
| | | | |

---

## What Is and Is Not on GitHub

| Artifact | On GitHub? | Notes |
|---|---|---|
| `data/registries/friend_crawl_registry.json` | YES | 72 PCNA structures, metadata, heuristic scores |
| `data/registries/friend_feature_schema.json` | YES | ESM-2 feature schema |
| `data/registries/friend_crawl_homolog_groups.json` | YES | not yet computed |
| All `docs/scientific_governance/` | YES | Binding rules — read before anything |
| All `wiki/` | YES | Project knowledge base |
| `.memory/PROJECT_STATE.md` | YES | Start here every session |
| `GNN_PNCA_crawled_data.zip` | **NO** | Your local machine only (`C:/Users/advay/`) |
| ESM-2 `.npy` files | **NO** | Inside your local zip |
| PyG `.pt` graph files | **NO** | Inside your local zip |
| Phase 3 graph tensors | **NO** | Reshwant's machine only |
| Phase 3 model checkpoints | **NO** | Reshwant's machine only |

---

## Startup Sequence (every session)

```
1. git pull origin main
2. Read .memory/PROJECT_STATE.md
3. Read docs/scientific_governance/16_CODING_AGENT_RULES.md   ← always first
4. Read this file (docs/advay_parallel_track.md)
```

No test suite required for your tasks (pure documentation and data analysis).
If you write any Python scripts, test them before committing.

---

## Dependencies to Install (only if writing scripts)

```bash
pip install numpy pandas matplotlib seaborn biopython
```

---

## Track 1 — PCNA Biology Wiki Pages

**What it is:** Enrich the wiki with PCNA-specific scientific content. Pure markdown.
No code. No data. Completely self-contained.

**Why it matters:** Phase 4 results will need to be interpreted against known PCNA
biology. This reference material needs to exist before predictions are made.

**Governance:** `docs/scientific_governance/12_PCNA_SPECIFIC_CHECKS.md`,
`docs/scientific_governance/14_CLAIM_POLICY.md`

**Tasks:**

**1a — PCNA Structural Biology Page** (`wiki/entities/pcna_structure.md`)

Write a reference page covering:
- PCNA as a homotrimeric sliding clamp (not a monomer)
- Canonical UniProt P12004 residue numbering
- The three main functional regions: PIP-box binding site, APIM site, IDCL
  (interdomain connecting loop, residues ~119–133)
- Trimer interface residues (which residues form the ring contacts)
- AOH1996/8GLA: what it is, which residues it contacts, why it is a positive control
  (NOT proof of a novel site)
- ATX-101: evidence framing — APIM-derived, what that means and does not mean
- Allowed and forbidden claim language (copy from governance doc 12)

Sources to use: PDB entries 5E0V (apo PCNA), 8GLA (AOH1996 complex), published
PCNA review papers you know of. Do not invent biology. Only include what you can
cite.

**1b — Known Binding Partners Catalog** (`wiki/entities/pcna_binding_partners.md`)

Table of known PCNA interaction partners:
- Partner protein name
- Interaction motif type (PIP-box / APIM / other)
- PCNA residues involved
- PDB ID if structure available
- Relevance to cryptic pocket hypothesis (known site vs. unknown)

This will be used in Phase 4 to check whether model predictions overlap known sites
or predict genuinely new ones.

**1c — Literature Synthesis** (`wiki/analyses/cryptic_pocket_pcna_literature.md`)

Concise synthesis (not copied text) of published work on:
- Cryptic pockets in PCNA or similar sliding clamps
- MD studies of PCNA conformational dynamics
- AOH1996 mechanism papers
- Any experimental validation of PCNA surface pockets beyond the PIP-box region

Format: one paragraph per paper/finding, citation, evidence type, confidence.

---

## Track 2 — PCNA Crawl Data Quality Audit

**What it is:** Audit your 72-structure crawl against the Phase 4 requirements, produce
a ranked candidate list, and write a governance-compliant manifest.

**Why it matters:** When Phase 3 model is frozen, the first thing Reshwant will do is
run inference on your crawl data. This manifest is the input to that step.

**Governance:** `docs/scientific_governance/12_PCNA_SPECIFIC_CHECKS.md`,
`docs/scientific_governance/04_DATASET_CONSTRAINTS.md`,
`docs/scientific_governance/15_PROVENANCE_AND_REPRODUCIBILITY.md`

**What you have:**
- `data/registries/friend_crawl_registry.json` — 72 entries with resolution,
  chain count, organism, `heuristic_pocket_score`, `has_parsed_features`, notes
- Your local zip: raw PDB files + ESM-2 `.npy` arrays + PyG `.pt` graphs

**Tasks:**

**2a — Structure Quality Filter** (`scripts/audit_crawl_data.py`)

Write a Python script that reads `data/registries/friend_crawl_registry.json` and
flags each structure against these criteria:
- Resolution ≤ 3.5 Å (flag anything worse)
- Organism = "Homo sapiens" (flag non-human)
- Chain count ≥ 3 (PCNA is a trimer; monomer structures may be crystal artifacts)
- `has_parsed_features = true` (flag structures without ESM-2 arrays)
- `file_path` not null (flag structures without PDB files)

Output: `data/registries/phase4_crawl_audit.json` with one entry per structure:
pdb_id, passes_filter (bool), failure_reasons (list of strings), resolution,
chain_count, heuristic_pocket_score.

**2b — Candidate Ranking** (`scripts/rank_pcna_candidates.py`)

From the audit, produce a ranked list of Phase 4 inference candidates:
- Exclude structures that fail quality filter
- Rank by: (1) has_ligand + heuristic_pocket_score descending; (2) resolution ascending
- Flag the AOH1996 structure (8GLA) as positive control — it must be in the list
- Flag 5E0V (apo PCNA) as reference structure

Output: `data/registries/phase4_candidate_manifest.json` — ranked list with rank,
pdb_id, inclusion_reason, heuristic_pocket_score, notes.

**2c — ESM-2 Feature Validation** (`scripts/validate_esm_features.py`)

For each structure with `has_parsed_features = true`, load the `.npy` array from
your local zip and check:
- Shape: (N_residues, 480) as specified in `friend_feature_schema.json`
- dtype: float32
- No NaN or Inf values
- N_residues matches the `residue_count` in the registry (or explain the discrepancy)

Output: `data/registries/phase4_esm_validation.json` with pass/fail per structure
and any anomalies.

Note: the registry says 146 `.npy` files exist for 72 catalog records — investigate
this discrepancy and document what the extra IDs are.

---

## Track 3 — MD Pre-Registration Documents

**What it is:** Write MD pre-registration templates for the top PCNA candidate
structures before any simulation is run. This is a governance requirement
(doc 13) — simulations cannot be claimed as validation without prior registration.

**Why it matters:** Phase 4 will involve MD simulations to test GNN predictions.
Pre-registrations must exist before simulations start. Writing them now costs nothing
and removes a bottleneck later.

**Governance:** `docs/scientific_governance/13_MD_VALIDATION_RULES.md`

The template is already defined in governance doc 13 (`## MD Pre-Registration Template`).

**Tasks:**

**3a — AOH1996/8GLA Positive Control Pre-Registration**
(`reports/phase4/md/8gla/pre_registration.md`)

Fill in the template for the 8GLA system (AOH1996 + PCNA complex). This is the
positive control — the GNN should predict the AOH1996 binding region as a high-score
site. The MD hypothesis: does the cryptic pocket remain open/accessible in apo PCNA
simulation (5E0V) if we remove the ligand?

**3b — Apo PCNA Reference Pre-Registration**
(`reports/phase4/md/5e0v/pre_registration.md`)

Fill in the template for 5E0V (apo PCNA). This is the reference simulation.
Hypothesis: characterize baseline conformational dynamics of the interdomain
connecting loop (IDCL) and trimer interface regions.

**3c — Top Candidate Pre-Registration**
(`reports/phase4/md/<pdb_id>/pre_registration.md`)

After completing Track 2 (candidate ranking), pick the top non-positive-control
candidate from your ranked list and pre-register an MD hypothesis for it.

---

## Track 4 — Known Interface Residue Map

**What it is:** A machine-readable JSON file mapping PCNA functional regions to
canonical UniProt P12004 residue numbers. Used in Phase 4 to automatically check
whether GNN predictions overlap known biology.

**Why it matters:** Without this, interpreting Phase 4 predictions requires manual
biology lookup every time. With it, any prediction can be cross-referenced instantly.

**Governance:** `docs/scientific_governance/12_PCNA_SPECIFIC_CHECKS.md`

**Task:**

**4a — PCNA Interface Map** (`data/registries/pcna_interface_map.json`)

```json
{
  "schema_version": "1.0",
  "uniprot_id": "P12004",
  "canonical_pdb": "5E0V",
  "regions": {
    "pip_box_binding_site": {
      "residues": [...],
      "description": "...",
      "source_pdb": "...",
      "pmid": "..."
    },
    "apim_site": { ... },
    "idcl": {
      "residues": [...],
      "description": "Interdomain connecting loop, residues ~119-133",
      ...
    },
    "trimer_interface": { ... },
    "aoh1996_contact_region": {
      "residues": [...],
      "description": "Residues contacting AOH1996 in 8GLA",
      ...
    }
  }
}
```

Source each region from PDB structures or published papers. Include the PMID or
PDB ID for every residue list. Do not invent residue numbers — only include what
you can cite.

Also write a companion script (`scripts/check_prediction_overlap.py`) that takes
a list of predicted residues and returns a report of which known regions they
overlap with, using this JSON.

---

## Track 5 — Heuristic Score Analysis

**What it is:** Analyze the `heuristic_pocket_score` field from your crawl registry.
These scores (0.05–0.18 range from the registry) are a weak signal already available.
Understanding them validates or contextualizes the Phase 4 inference later.

**Why it matters:** If the GNN's predictions correlate with heuristic scores, that's
useful context. If they don't, that's equally interesting. Either way, you need to
know what the heuristic scores actually represent before Phase 4.

**Tasks:**

**5a — Score Distribution Analysis** (`scripts/analyze_heuristic_scores.py`)

From `data/registries/friend_crawl_registry.json`:
- Distribution plot of heuristic_pocket_score across all 72 structures
- Score vs. resolution scatter plot
- Score vs. chain_count scatter plot
- Flag AOH1996 (8GLA) score — is it in the top quartile? (It should be if the
  heuristic is meaningful.)
- Identify structures with null scores and explain why they might be missing

Output: `reports/phase4/heuristic_score_analysis.md` + figures in
`reports/phase4/figures/`

**5b — Document What the Heuristic Score Represents**

Look at the source code in your crawl pipeline (or recall how you generated it) and
document in `reports/phase4/heuristic_score_analysis.md`:
- What algorithm/tool generated it
- What inputs it used
- What score = 0.0 means vs. score = 1.0
- Whether it is per-structure or per-residue aggregated
- Known limitations

This is important for Phase 4 claim framing — we need to know exactly what this
score measures before comparing it to GNN output.

---

## Hard Rules — Apply to Everything

1. **Do not touch Phase 3** — no edits to `src/phase3_*/`, `scripts/train_*.py`,
   `scripts/run_all_training.py`, `scripts/summarize_training.py`, or any training manifests.

2. **Do not evaluate on test data** — never load the "test" split.

3. **Do not make scientific claims** — no "PCNA site X is druggable," no "model
   outperforms baselines." Document findings as observations only.

4. **Authority order:** `docs/scientific_governance/` > everything else. If you're
   unsure whether something is allowed, read the governance doc first.

5. **No invented biology** — every residue number, binding partner, or biological
   claim must be citable.

6. **Update this file's completion log** (the table at the top) after finishing each
   task. Write what you did, what files changed, and the date.

7. **Update `wiki/log.md`** with a dated entry for every durable decision made
   during your session.

8. **Update `.memory/PROJECT_STATE.md`** under "What Is Done" at the end of
   each session.

9. **Do not touch:** `CLAUDE.md`, `AGENTS.md`, `.memory/INDEX.md`,
   `.memory/MEMORY_RULES.md`, `docs/scientific_governance/` (read only)

---

## What to Commit

- `wiki/entities/pcna_structure.md`
- `wiki/entities/pcna_binding_partners.md`
- `wiki/analyses/cryptic_pocket_pcna_literature.md`
- `scripts/audit_crawl_data.py`
- `scripts/rank_pcna_candidates.py`
- `scripts/validate_esm_features.py`
- `scripts/check_prediction_overlap.py`
- `scripts/analyze_heuristic_scores.py`
- `data/registries/phase4_crawl_audit.json`
- `data/registries/phase4_candidate_manifest.json`
- `data/registries/phase4_esm_validation.json`
- `data/registries/pcna_interface_map.json`
- `reports/phase4/md/8gla/pre_registration.md`
- `reports/phase4/md/5e0v/pre_registration.md`
- `reports/phase4/md/<top_candidate>/pre_registration.md`
- `reports/phase4/heuristic_score_analysis.md`
- `reports/phase4/figures/`
- Updated `docs/advay_parallel_track.md` (completion log filled in)
- Updated `wiki/log.md`
- Updated `.memory/PROJECT_STATE.md`

Do **not** commit: anything in `data/raw_intake/`, `data/graphs/`, `checkpoints/`,
or your local zip file.
