---
updated: 2026-05-27
updated_by: claude-code
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
| Training | **BLOCKED** |
| Graph generation | **BLOCKED** |
| Molecular dynamics | **BLOCKED** |
| Scientific claims | **BLOCKED** |
| Split freeze | **BLOCKED** |
| Label freeze | **BLOCKED** |

No dataset has been adopted. All raw data is quarantined in `data/raw_intake/`.

---

## What Is Done (as of 2026-05-27)

- **Governance scaffold:** 40 binding docs in `docs/scientific_governance/` — complete
- **Wiki scaffold:** 59 pages in `wiki/` (concepts, entities, analyses, log, open-questions) — complete
- **Intake infrastructure:** `scripts/dataset_intake.py` + `src/phase2_intake/` adapters and IO — complete
- **CryptoBench download:** All raw files quarantined in `data/raw_intake/cryptobench/`; 5,005 CIF structures present in ZIP archive; not adopted
- **CryptoBench schema audit:** `reports/phase2/cryptobench_schema_deep_audit.md` — complete
- **CryptoBench deep audit:** PCNA contamination confirmed (apo 5e0v, holo 3vkx, UniProt P12004); PCNA-like hits (2xur, 3bep); 721 residue token mismatches; 6 repeated holo PDB IDs across folds — complete
- **Track A remediation planning:** `cryptobench_adoption_decision.md`, `pcna_isolation_policy.md`, `proposed_phase2_split_strategy.md`, `proposed_label_policy.md` — **complete, awaiting human review**
- **Track B auxiliary acquisition:** 9 sources linked or metadata-downloaded (AlphaFold P12004, ASD, BioGrid, BioLiP, PocketMiner, P2Rank, fpocket, scPDB, PDBbind); none adopted
- **Machine-readable registries:** `cryptobench_candidate_cleaned_registry.json`, `cryptobench_fold_summary.json`, `potential_homolog_risks.json`, `residue_mapping_failures.json`, `auxiliary_dataset_role_summary.json` — complete
- **Foundation check:** `python scripts/phase2_foundation_check.py` → `ready_for_dataset_planning: true`

---

## Current Blockers (numbered priority order)

1. ~~**CLEARED 2026-05-27** — CryptoBench adoption~~
   Approved by Rishi: cryptic-only with exclusions (5e0v/3vkx/PCNA records excluded,
   2xur/3bep held pending clustering, 6 repeated holos must be grouped).

2. ~~**CLEARED 2026-05-27** — PCNA isolation policy~~
   Approved by Rishi: full isolation. 5e0v/3vkx excluded from model development.
   2xur/3bep held pending clustering results.

3. **SEQUENCE_CLUSTERING_REQUIRED** ← primary remaining blocker
   Tool not chosen (MMseqs2 vs CD-HIT), threshold not set; 6 repeated holo PDB IDs
   unresolved; homolog safety unconfirmed.
   → `data/registries/potential_homolog_risks.json`

4. **RESIDUE_MAPPING — partially cleared**
   4a (remap), 4b (mask), 4d (exclude 4 records) approved by Rishi.
   4c (exclusion threshold) DEFERRED — per-structure analysis complete, 1 structure
   (1lx7, 79% masked) exceeds the suggested 50% threshold. Awaiting Rishi threshold
   decision. See `reports/phase2/residue_mapping_4c_impact_analysis.md`.

5. ~~**CLEARED 2026-05-27** — label supervision policy~~
   Approved by Rishi: positive-unlabeled framing; unlisted residues = background not
   true negative; absent residues = masked; PCNA = holdout.

6. **SPLIT_FREEZE_BLOCKED**
   Depends on blocker 3 (clustering) and blocker 4c (threshold decision).

---

## Known Unregistered Asset — Friend's Crawl

Friend has a local 40GB raw protein structure crawl:
- ~23,771 RCSB mmCIF files (PCNA-related search)
- ~20,000 AlphaFold predicted structures (human proteome subset)
- Parsed feature JSON/numpy arrays (B-factors, ligands, pocket heuristic scores)
- STRING/BioGRID network data

**Do NOT transfer the full 40GB yet.** Request from Friend (see `COLLABORATION.md`):
- `data/registries/friend_crawl_registry.json` — per-structure metadata
- `reports/phase2/friend_crawl_stats.md` — summary statistics
- `data/registries/friend_crawl_homolog_groups.json` — homolog clusters (if computed)
- `data/registries/friend_feature_schema.json` — parsed feature schema descriptions
- `data/raw_intake/friend_sample/` — 20–50 sample structures

These small artifacts directly help unblock clustering (blocker 3) and filtering policy.

## Next Tasks (priority order)

1. **[IMMEDIATE — can decide now]** Decision 4c: only 1 structure (1lx7, 79% masked) exceeds
   the suggested 50% threshold. Approve: exclude 1lx7, mask all others.
   See `reports/phase2/residue_mapping_4c_impact_analysis.md`.

2. **[START NOW — no wait needed]** Choose clustering tool (MMseqs2 recommended) and run
   sequence clustering on CryptoBench cryptic candidates. Can run on local CIF files
   immediately. Will re-run combined with friend's crawl when Prompt 1 finishes.

3. **[WAITING — friend's Prompt 1]** Ingest friend's crawl metadata registry once Prompt 1
   completes. Inspect homolog groups artifact if friend's clustering was already run.

4. **[AFTER 2 + 3]** Draft split manifest (`draft_not_frozen`) grouping structures by
   UniProt / apo-holo pair / sequence cluster, with PCNA records flagged.

5. **[AFTER 4]** Implement label generation script (remap + mask + exclude per decisions
   4a/4b/4d/4c once threshold approved).

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
| `data/registries/auxiliary_dataset_role_summary.json` | Auxiliary dataset roles (context vs training) |
| `data/registries/assumption_registry.json` | Documented scientific assumptions |

---

## Last Session Summary

Rishi approved decisions 1, 2, 3 (human_review_packet) and 4a, 4b, 4d (residue mapping)
on 2026-05-27. Blockers 1, 2, 5 cleared. Blocker 4 partially cleared (4c deferred).
Per-structure impact analysis for 4c complete: only 1 structure (1lx7, UniProt P12758,
79% of 19 pocket residues absent) exceeds the suggested 50% threshold; 4 structures
exceed 25%. Recommendation: exclude 1lx7, mask all others. Awaiting Rishi threshold
confirmation. Friend running Prompt 1 (metadata extraction) and Prompt 2 (Phase 3
infrastructure) concurrently. Sequence clustering (blocker 3) is now the critical path.
