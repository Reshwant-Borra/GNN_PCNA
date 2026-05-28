---
updated: 2026-05-27
updated_by: claude-code (reshwant-session-end)
---

# Project State — GNN-PCNA Phase 2

This file is the single authoritative current-state snapshot. Agents update it at every
session close. Read it immediately after `CLAUDE.md` or `AGENTS.md`.

**Staleness check:** If `updated` in the frontmatter above is >7 days before today's date,
treat this file as potentially stale. Reconstruct current state from
`wiki/analyses/coding_agent_context.md` sections 17–24 and the most recent
`reports/phase2/handoff_YYYYMMDD.md`, then update this file before starting any task.

---

## Phase

**Phase 2 / Foundation — Dataset Investigation and Remediation Planning**

| System | Status |
|---|---|
| Training | **BLOCKED — sequence clustering not complete** |
| Graph generation | **BLOCKED — split not frozen** |
| Molecular dynamics | **BLOCKED** |
| Scientific claims | **BLOCKED** |
| Split freeze | **BLOCKED — sequence clustering required first** |
| Label freeze | **READY TO IMPLEMENT** — all 4 label decisions approved |

CryptoBench has been adopted (cryptic-only with exclusions). Raw data quarantined in `data/raw_intake/`.
Phase 3 framework (model + trainer + evaluation + baselines) is built locally by friend — not yet pushed.

---

## What Is Done (as of 2026-05-27)

- **Governance scaffold:** 40 binding docs in `docs/scientific_governance/` — complete
- **Wiki scaffold:** 59 pages in `wiki/` — complete
- **Persistent memory system:** `.memory/` (PROJECT_STATE, INDEX, MEMORY_RULES, handoff template), `CLAUDE.md`, `00_COMPACT_INDEX.md`, `COLLABORATION.md` — complete
- **Intake infrastructure:** `scripts/dataset_intake.py` + `src/phase2_intake/` adapters and IO — complete
- **CryptoBench download + audit:** All 5,005 CIF files quarantined; deep audit complete; PCNA contamination confirmed (5e0v/3vkx/P12004); 721 residue failures; 6 repeated holo IDs — complete
- **CryptoBench ADOPTED (cryptic-only):** Rishi approved 2026-05-27. Exact exclusions: 5e0v/3vkx excluded; 2xur/3bep held pending clustering; 6 repeated holos must be grouped. See `reports/phase2/human_review_packet.md`.
- **PCNA isolation policy:** Approved 2026-05-27. Full isolation — 5e0v/3vkx out of all model development; 2xur/3bep held.
- **Label supervision contract (PU learning):** Approved 2026-05-27. Positives from `apo_pocket_selection`; unlisted = background/unlabeled; absent = masked; PCNA = holdout.
- **Residue mapping policy — ALL DECISIONS APPROVED:**
  - 4a: remap 420 Class 1 failures via label_seq_id fallback — APPROVED
  - 4b: mask 297 Class 2 absent residues as unlabeled — APPROVED
  - 4c: exclude structures with >=50% pocket residues absent. Only 1 qualifies: 1lx7 (79%, P12758) — APPROVED 2026-05-27
  - 4d: exclude 4 Class 3 wrong-chain records — APPROVED
  - See `reports/phase2/residue_mapping_resolution_policy.md` (status: APPROVED)
- **Track B auxiliary acquisition:** 9 sources linked/metadata-downloaded; none adopted — complete
- **Machine-readable registries:** cryptobench_candidate_cleaned_registry.json, cryptobench_fold_summary.json, potential_homolog_risks.json, residue_mapping_failures.json, residue_mapping_per_structure_impact.json, auxiliary_dataset_role_summary.json — complete
- **Friend's crawl artifacts (Prompt 1 complete):** friend_crawl_registry.json (72 structures), friend_crawl_stats.md, friend_crawl_homolog_groups.json (not_computed), friend_feature_schema.json, data/raw_intake/friend_sample/ (27 PDB + ESM pairs) — in repo
- **Phase 3 framework (friend's Prompt 2 complete):** `src/phase3_model/`, `src/phase3_training/` (trainer with --dry-run blocker guard), `src/phase3_evaluation/`, `src/baselines/`, 58 tests passing — built locally, not yet pushed

---

## Current Blockers (numbered priority order)

1. ~~**CLEARED 2026-05-27** — CryptoBench adoption~~
   Approved: cryptic-only with exclusions.

2. ~~**CLEARED 2026-05-27** — PCNA isolation policy~~
   Approved: full isolation. 5e0v/3vkx excluded; 2xur/3bep held pending clustering.

3. **SEQUENCE_CLUSTERING_REQUIRED** ← sole remaining Phase 2 data blocker
   Tool not chosen (MMseqs2 recommended); identity threshold not set; 6 repeated holo PDB
   IDs (2fzc, 2fzg, 4f04, 5qya, 6a5y, 7fo6) must be grouped; homolog safety for 2xur/3bep
   unconfirmed. Friend's homolog groups artifact is `not_computed` — no clustering pre-done.
   → `data/registries/potential_homolog_risks.json`
   → `data/registries/friend_crawl_registry.json` (72 structures to include in clustering run)

4. ~~**CLEARED 2026-05-27** — Residue mapping policy~~
   All 4 decisions approved (4a remap, 4b mask, 4c exclude 1lx7, 4d exclude 4 wrong-chain).
   Label generation script can now be implemented.

5. ~~**CLEARED 2026-05-27** — label supervision policy~~
   Approved: positive-unlabeled framing.

6. **SPLIT_FREEZE_BLOCKED**
   Depends only on blocker 3 (clustering). Once clustering is done, split manifest can be
   drafted and frozen.

---

## Friend's Crawl — Fully Ingested

Metadata artifacts in repo. Full 40GB archive stays local (do NOT transfer).

| Artifact | Path | Notes |
|---|---|---|
| Registry | `data/registries/friend_crawl_registry.json` | 72 PCNA-focused structures |
| Stats | `reports/phase2/friend_crawl_stats.md` | Resolution distribution, ligand presence, ESM coverage |
| Homolog groups | `data/registries/friend_crawl_homolog_groups.json` | status: not_computed |
| Feature schema | `data/registries/friend_feature_schema.json` | ESM-2 Nx480, PyG graphs, pocket scores |
| Sample | `data/raw_intake/friend_sample/` | 27 PDB + ESM pairs |

---

## Next Tasks (priority order)

1. **[CRITICAL PATH — start now]** Run sequence clustering on CryptoBench cryptic candidates
   (from `cryptobench_candidate_cleaned_registry.json`) + friend's 72 structures
   (from `friend_crawl_registry.json`). Tool: MMseqs2 (recommended) or CD-HIT.
   Threshold: start at 30% identity (conservative for fold-level leakage prevention).
   Goal: group 6 repeated holo IDs, confirm 2xur/3bep status, verify homolog safety.
   Output: updated `data/registries/cryptobench_fold_summary.json` with cluster assignments.

2. **[CAN START NOW — independent of clustering]** Implement label generation script.
   All 4 residue mapping decisions are approved. Script must:
   - Remap Class 1 (420) via label_seq_id fallback; log to `residue_remap_log.json`
   - Mask Class 2 absent residues (label = -1); exclude 1lx7 entirely
   - Exclude Class 3 (4 wrong-chain records); log to `excluded_records.json`
   - Output: deterministic label file per `docs/scientific_governance/06_LABELING_RULES.md`

3. **[AFTER 1]** Draft split manifest (`draft_not_frozen`) grouping structures by UniProt /
   apo-holo pair / sequence cluster; PCNA records flagged as holdout.

4. **[AFTER 1 + 3]** Freeze split (requires human sign-off via governance 26_HUMAN_REVIEW_GATES.md).

5. **[AFTER 2 + 4]** Freeze label file. Phase 2 complete. Friend's Phase 3 framework can begin
   real training runs (remove dry-run guard with human approval).

---

## Key Registry Paths (machine-readable ground truth)

| Registry | Purpose |
|---|---|
| `data/registries/dataset_inventory.json` | Master dataset status registry |
| `data/registries/download_manifest.jsonl` | Append-only download action log |
| `data/registries/cryptobench_candidate_cleaned_registry.json` | Homolog/leakage-remediated candidate list |
| `data/registries/cryptobench_fold_summary.json` | Train/test fold distribution and split risks |
| `data/registries/potential_homolog_risks.json` | Homologous contamination risk flags |
| `data/registries/residue_mapping_failures.json` | 721 residue coordinate mapping failures |
| `data/registries/residue_mapping_per_structure_impact.json` | Per-structure Class 2 impact (fraction masked) |
| `data/registries/friend_crawl_registry.json` | Friend's 72 PCNA structure metadata |
| `data/registries/friend_crawl_homolog_groups.json` | Friend's clustering (not_computed) |
| `data/registries/auxiliary_dataset_role_summary.json` | Auxiliary dataset roles (context vs training) |
| `data/registries/assumption_registry.json` | Documented scientific assumptions |

---

## Last Session Summary

Reshwant (2026-05-27): Decision 4c approved — exclude 1lx7 (79% pocket residues absent,
UniProt P12758), mask all others below 50% threshold. All residue mapping decisions now
fully approved. Blocker 4 cleared. Merged friend's Prompt 1 artifacts (5 metadata files,
27 sample PDB+ESM pairs). Resolved PROJECT_STATE.md merge conflict preserving both
Rishi approval records and friend's crawl artifact records. Pushed to main.

Friend (2026-05-27): Prompt 1 complete — 5 Phase 2 artifacts from 72-structure PCNA crawl
(no AlphaFold; ESM-2 features, PyG graphs, pocket scores; homolog groups not computed).
Prompt 2 complete — full Phase 3 GNN framework built: model, trainer with --dry-run blocker
guard, evaluation pipeline, baselines, 58 tests passing. Phase 3 code local only, not yet pushed.

Sole remaining Phase 2 blocker: sequence clustering (blocker 3). Label generation script
can be implemented in parallel (all decisions approved). Phase 3 training remains blocked
by the --dry-run guard until Phase 2 split + label freeze are approved.
