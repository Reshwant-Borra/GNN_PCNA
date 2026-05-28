---
type: agent-handoff
handoff_date: 2026-05-27
from_agent: claude-code (Reshwant's session)
to_agent: codex
status: complete
phase: Phase 2 COMPLETE → Phase 3 AUTHORIZED
---

# Codex Handoff — GNN-PCNA Phase 2 (2026-05-27)

Read this document first, then `.memory/PROJECT_STATE.md` (current state snapshot),
then `.memory/INDEX.md` (task routing table). Do NOT scan `wiki/` or `reports/phase2/`
randomly — use the routing table to find the right files for your task.

---

## Project in One Paragraph

This is a governed, scientifically audited rebuild of a GNN-based residue-level cryptic
pocket predictor for PCNA (Proliferating Cell Nuclear Antigen). The end goal is a model
that predicts which residues form cryptic binding pockets, trained on CryptoBench, evaluated
rigorously, and eventually applied to PCNA for novel biology. The project is in **Phase 2**
(foundation): dataset investigation, governance, and data pipeline implementation. No training,
graph generation, or MD runs have happened yet. Phase 3 framework code was built by a
collaborating agent but is not yet the critical path.

---

## Authority Rules (non-negotiable)

1. `docs/scientific_governance/` is **binding law**. Every numbered doc is a scientific
   constraint that overrides all other sources — including this document. Read the relevant
   numbered doc before touching datasets, splits, labels, graphs, models, or claims.
2. Authority order: `docs/scientific_governance/` > primary sources > `crawls/` > `wiki/` > `reports/`
3. Before ANY implementation: read `docs/scientific_governance/16_CODING_AGENT_RULES.md`.
4. Use `docs/scientific_governance/00_COMPACT_INDEX.md` (~420 tokens) to find the right
   numbered doc without loading the full `00_README.md` (~1,850 tokens).
5. If a required scientific assumption is not in `docs/scientific_governance/` or
   `data/registries/assumption_registry.json`, **stop and record it in
   `wiki/open_questions/open-questions.md`** before proceeding.

---

## What Was Completed This Session

### Governance Decisions (all approved by Rishi 2026-05-27)

| Decision | Status | What Was Decided |
|---|---|---|
| 1 — CryptoBench adoption | APPROVED | Cryptic-only, with specific exclusions |
| 2 — PCNA isolation | APPROVED | Full isolation: 5e0v/3vkx excluded; 2xur/3bep held pending clustering |
| 3 — Label supervision | APPROVED | Positive-unlabeled (PU) framing — unlisted residues ≠ true negatives |
| 4a — Residue remap | APPROVED | Class 1 (420 failures): remap via label_seq_id fallback |
| 4b — Residue mask | APPROVED | Class 2 (297 failures): mask as unlabeled (label = -1) |
| 4c — Exclusion threshold | APPROVED | >=50% masked → exclude structure. Only 1lx7 qualifies (79%, P12758) |
| 4d — Wrong-chain exclude | APPROVED | Class 3 (4 failures): exclude those 4 records |

**Source documents:**
- `reports/phase2/human_review_packet.md` (decisions 1/2/3 — status: APPROVED)
- `reports/phase2/residue_mapping_resolution_policy.md` (decisions 4a/4b/4c/4d — status: APPROVED)

### Infrastructure Built

| What | Where | Purpose |
|---|---|---|
| Claude Code entry point | `CLAUDE.md` | Hard rules + startup sequence |
| Codex entry point | `AGENTS.md` (modified) | Fast-path + governance rules |
| Current state snapshot | `.memory/PROJECT_STATE.md` | Phase, blockers, next tasks |
| Task routing table | `.memory/INDEX.md` | Which files to read for which task |
| Memory write protocol | `.memory/MEMORY_RULES.md` | Write permissions matrix |
| Session handoff template | `.memory/AGENT_HANDOFF_TEMPLATE.md` | Handoff schema |
| Governance 1-page map | `docs/scientific_governance/00_COMPACT_INDEX.md` | Fast nav for 40 docs |
| Collaboration boundaries | `COLLABORATION.md` | Reshwant/Friend ownership |
| `.gitignore` | `.gitignore` | Excludes 1.09 GB CIF archive from git |

### Data Available

| Asset | Location | Status |
|---|---|---|
| CryptoBench (5,005 CIF files) | `data/raw_intake/cryptobench/` | Quarantined; ADOPTED (cryptic-only) |
| CryptoBench dataset.json | `data/raw_intake/cryptobench/metadata_files/` | 1,107 apo / 5,493 cryptic records |
| CryptoBench folds.json | same dir | 5 folds: test / train-0..train-3 |
| Friend's crawl (72 structures) | `data/raw_intake/friend_sample/` | 27 PDB + ESM pairs present |
| Friend's registry | `data/registries/friend_crawl_registry.json` | 72 JSONL records; PCNA-focused |
| Friend's feature schema | `data/registries/friend_feature_schema.json` | ESM-2 (Nx480), PyG graphs, pocket scores |

### Scripts Written

| Script | Purpose | Status |
|---|---|---|
| `scripts/sequence_clustering.py` | RCSB API clustering at 30% identity | **RUNNING NOW** |
| `scripts/generate_labels.py` | Full label generation (4a/4b/4c/4d) | **WRITTEN, ready to run** |
| `scripts/residue_mapping_impact_analysis.py` | Per-structure 4c impact analysis | Complete — ran successfully |
| `scripts/phase2_foundation_check.py` | Foundation readiness gate | Complete — passes |
| `scripts/dataset_intake.py` | Data intake infrastructure | Complete |

---

## Current State of All Blockers

| # | Blocker | Status | Next Action |
|---|---|---|---|
| 1 | CryptoBench adoption | ~~CLEARED~~ | — |
| 2 | PCNA isolation | ~~CLEARED~~ | — |
| 3 | **Sequence clustering** | **IN PROGRESS** (script running) | Complete run, review output |
| 4 | Residue mapping | ~~CLEARED~~ | Implement label script (4 decisions approved) |
| 5 | Label supervision | ~~CLEARED~~ | — |
| 6 | Split freeze | **BLOCKED by 3** | After clustering: draft split manifest |

**Blocker 3 is the only remaining Phase 2 data blocker.**

---

## Clustering Results (COMPLETE)

`scripts/sequence_clustering.py` ran successfully. RCSB API, 30% identity, 1,179 structures.

**PCNA cluster ID = 1168** (anchor: 5e0v/P12004)

| Finding | Result |
|---|---|
| 2xur PCNA homolog? | **NO** — cluster 1415 (DNA Pol III Beta). Retained. |
| 3bep PCNA homolog? | **NO** — chain A is DNA; no protein cluster found. Retained pending manual check. |
| PCNA members in CryptoBench | Only 5e0v (already excluded) — zero new contamination |
| PCNA members in friend's crawl | 51/72 structures (expected — PCNA-focused crawl) |

**Repeated holo pairs:**
- 2air↔9atc: **SAME cluster (219)** — confirmed sequence homologs → group together in split
- 3e9p↔4ilg: different clusters (216 vs 381) — structural coincidence → shared holo stays in one fold only
- 4n5g↔6hl0: different clusters (1190 vs 2228) — same policy

**Cross-fold cluster risks (5 actionable):**
| Cluster | Train | Test | Action |
|---|---|---|---|
| 885 | 8oqp | 7o1i | Reassign to same fold |
| 150 | 6g0s | 2rfj | Reassign to same fold |
| 219 | 2air, 4c6b | 9atc | Reassign all to train (also resolves 2fzc/2fzg/4f04 repeated holo) |
| 5192 | 6cy1 | 6n5j | Reassign to same fold |
| 3396 | 6a45 | 6w10 | Reassign to same fold |

Cluster 365 (1lx7↔6f52) is non-actionable: 1lx7 excluded by decision 4c.

Output files:
- `data/registries/sequence_cluster_assignments.json` — per-structure cluster IDs
- `data/registries/cross_fold_cluster_risks.json` — 5 actionable risks
- `reports/phase2/sequence_clustering_report.md` — human-readable summary

## Label Generation Results (COMPLETE)

`scripts/generate_labels.py` ran successfully. All 4 decisions applied.

| Metric | Value |
|---|---|
| Structures labeled | 1,101 |
| Excluded | 6 (5e0v, 2b23/4gpi/8hc1/8oqp, 1lx7) |
| Total positive labels | 16,335 |
| Masked labels | 3,704 |
| Class 1 remaps | 0 (auth_seq_id succeeded for all resolvable tokens) |

Outputs: `data/labels/labels_{apo}.json` + `data/labels/label_manifest.json` (hash-verified)

---

## Phase 2 Status: COMPLETE

**All Phase 2 tasks are done. Split and label manifests are FROZEN. Phase 3 is authorized.**

### What Was Completed After Original Handoff Draft

| Task | Status | Output |
|---|---|---|
| Split redesign (5 clusters → train) | APPROVED by Rishi 2026-05-27 | `reports/phase2/split_manifest_approval_20260527.md` |
| Split manifest frozen | FROZEN | `data/registries/split_manifest_frozen.json` (hash: 24dd5e347d880108) |
| Label manifest frozen | FROZEN | `data/labels/label_manifest.json` |
| Phase 2 completion declared | COMPLETE | `wiki/log.md` — 3 final entries appended |

### Frozen Split Manifest

**File:** `data/registries/split_manifest_frozen.json`  
**Hash:** 24dd5e347d880108  
**Total structures:** 1,101  
**Distribution:** test=214, train-0=220, train-1=223, train-2=222, train-3=222

Split redesign applied:
- 7o1i: test → train-1 (cluster 885)
- 2rfj: test → train-2 (cluster 150)
- 9atc: test → train-1 (cluster 219)
- 6n5j: test → train-0 (cluster 5192)
- 6w10: test → train-2 (cluster 3396)

### Frozen Label Manifest

**File:** `data/labels/label_manifest.json`  
**Structures:** 1,101 | **Positives:** 16,335 | **Masked:** 3,704 | **Remaps:** 0

---

## Immediate Next Tasks for Codex — PHASE 3

### Task 1: Remove dry-run guard (READY)

```
Authorization: reports/phase2/split_manifest_approval_20260527.md

In src/phase3_training/, remove or conditionalize the --dry-run blocker guard.
The guard was intentionally blocking real training until Phase 2 split + label freeze
were approved. That approval is now recorded.

Before touching src/phase3_*:
  - Owner is Friend per COLLABORATION.md
  - Codex should coordinate with Friend before modifying Phase 3 code
  - Read docs/scientific_governance/16_CODING_AGENT_RULES.md first
```

### Task 2: Implement data pipeline connecting frozen Phase 2 outputs to Phase 3 training

```
Governance: docs/scientific_governance/07_PREPROCESSING_AND_GRAPH_RULES.md
             docs/scientific_governance/08_MODEL_ARCHITECTURE_CONSTRAINTS.md

Inputs (all frozen):
  data/registries/split_manifest_frozen.json   — fold assignments
  data/labels/labels_{apo_pdb_id}.json         — per-residue labels (label=1 positive, label=-1 masked)
  data/raw_intake/cryptobench/cif-files/       — 5,005 CIF structures (gitignored, present locally)
  data/registries/excluded_records.json        — 6 structures to skip

The pipeline must:
  - Respect PU framing: label=-1 means masked, NOT negative. Exclude from loss.
  - Respect fold assignments in split_manifest_frozen.json (not the original folds.json)
  - Exclude all 6 records in excluded_records.json
  - Not generate graphs or train until pipeline is verified correct

Output target:
  src/phase2_intake/ or new src/phase3_data/ — dataset loader for Phase 3 trainer
```

### Task 3: Run Phase 3 training (after Task 2 pipeline verified)

```
Governance:
  docs/scientific_governance/08_MODEL_ARCHITECTURE_CONSTRAINTS.md
  docs/scientific_governance/09_EVALUATION_PROTOCOL.md
  docs/scientific_governance/10_BASELINE_REQUIREMENTS.md
  docs/scientific_governance/19_STOP_CONDITIONS.md

Prerequisites:
  - dry-run guard removed (Task 1)
  - data pipeline verified (Task 2)
  - human sign-off on pipeline correctness before first real training run

PCNA structures are holdout-only (cluster_id_30=1168).
Do NOT include PCNA structures in training or validation.
```

---

## Key File Paths (do not assume — verify before using)

### Governance (binding)
```
docs/scientific_governance/00_COMPACT_INDEX.md    ← 1-page map for all 40 docs
docs/scientific_governance/04_DATASET_CONSTRAINTS.md
docs/scientific_governance/05_SPLIT_PROTOCOL.md   ← clustering + split rules
docs/scientific_governance/06_LABELING_RULES.md   ← label generation rules
docs/scientific_governance/16_CODING_AGENT_RULES.md ← ALWAYS read before coding
docs/scientific_governance/26_HUMAN_REVIEW_GATES.md ← when to stop for human review
```

### Data registries (machine-readable ground truth)
```
data/registries/dataset_inventory.json
data/registries/download_manifest.jsonl
data/registries/cryptobench_candidate_cleaned_registry.json
data/registries/cryptobench_fold_summary.json
data/registries/potential_homolog_risks.json
data/registries/residue_mapping_failures.json
data/registries/residue_mapping_per_structure_impact.json
data/registries/friend_crawl_registry.json            ← 72 PCNA structures
data/registries/sequence_cluster_assignments.json     ← NEW (from clustering)
data/registries/cross_fold_cluster_risks.json         ← NEW (from clustering)
```

### Reports (permanent audit trail — never overwrite, new files only)
```
reports/phase2/human_review_packet.md               ← decisions 1/2/3 APPROVED
reports/phase2/residue_mapping_resolution_policy.md ← decisions 4a/4b/4c/4d APPROVED
reports/phase2/residue_mapping_4c_impact_analysis.md ← 1lx7 is the only 4c exclusion
reports/phase2/sequence_clustering_report.md         ← NEW (from clustering)
reports/phase2/label_generation_report.md            ← NEW (after labels run)
reports/phase2/handoff_20260527.md                   ← session handoff
```

---

## Phase 3 — What Friend Built

Friend's agent ran Prompt 2 and built a full Phase 3 GNN framework locally:
- `src/phase3_model/` — GNN model architecture
- `src/phase3_training/` — trainer with `--dry-run` blocker guard
- `src/phase3_evaluation/` — evaluation pipeline
- `src/baselines/` — PocketMiner/fpocket/P2Rank baseline wrappers
- 58 tests passing

**The `--dry-run` guard prevents real training until Phase 2 split + label freeze are
approved by a human reviewer.** Friend will push this to the `main` branch separately.

Codex should NOT touch `src/phase3_*` — that is friend's ownership per `COLLABORATION.md`.
When Phase 2 is complete and human approves the split/label freeze, the guard can be removed
with explicit sign-off.

---

## What Codex Must NOT Do

- Do NOT train, fine-tune, or initiate any gradient computation
- Do NOT freeze splits or labels without human sign-off (governance 26)
- Do NOT modify `docs/scientific_governance/` (binding law — human-only)
- Do NOT modify `CLAUDE.md`, `AGENTS.md`, `.memory/INDEX.md`, `.memory/MEMORY_RULES.md`
- Do NOT overwrite existing `reports/phase2/*.md` files (create new ones only)
- Do NOT treat unlisted residues as true negatives in any label logic
- Do NOT run MD simulations
- Do NOT make scientific claims about PCNA from model outputs

---

## Memory Update Protocol (end of every session)

1. Update `.memory/PROJECT_STATE.md` — move completed tasks to "What Is Done", clear
   resolved blockers (after logging to wiki/log.md), refresh "Next Tasks", update
   `updated` frontmatter date and `updated_by`.
2. Append to `wiki/log.md` — one entry per durable decision with date, source path,
   governance path, confidence, evidence status. **Never edit or delete existing entries.**
3. Append to `wiki/open_questions/open-questions.md` if a new blocking question arose.
4. Save a handoff file — fill `.memory/AGENT_HANDOFF_TEMPLATE.md` schema and save as
   `reports/phase2/handoff_YYYYMMDD.md` (use the actual date).

---

## Collaboration Context

| Person | Role | Owns |
|---|---|---|
| Reshwant | Phase 2 lead | `data/`, `docs/`, `reports/phase2/`, `scripts/`, `src/phase2_intake/`, governance |
| Friend | Phase 3 builder | `src/phase3_model/`, `src/phase3_training/`, `src/phase3_evaluation/`, `src/baselines/` |

Both work on `main` branch. Friend must not touch governance docs or Phase 2 data files.
Full ownership table: `COLLABORATION.md`.

---

## Provenance

- All decisions cited here are documented in the files referenced
- No counts or findings are inferred or hallucinated
- Confidence: high for all decision outcomes (verified human approvals);
  high for script status (verified by running); medium for Phase 3 framework
  details (reported by friend, not yet in remote repo)
- Generated: 2026-05-27 by claude-code (Reshwant's session)
