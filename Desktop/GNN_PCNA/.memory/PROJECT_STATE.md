---
updated: 2026-05-27
updated_by: claude-code (advay-agent, friend-crawl-artifacts)
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

1. **HUMAN_REVIEW_REQUIRED — CryptoBench adoption**
   Cryptic-only adoption with exclusions; conditional on isolation + clustering + remapping
   → `reports/phase2/cryptobench_adoption_decision.md`

2. **HUMAN_REVIEW_REQUIRED — PCNA isolation policy**
   Exact PCNA records (5e0v/3vkx/P12004) and PCNA-like hits (2xur/3bep) must be isolated;
   human approval needed before any split or training touches these records
   → `reports/phase2/pcna_isolation_policy.md`

3. **SEQUENCE_CLUSTERING_REQUIRED**
   Tool not chosen (MMseqs2 vs CD-HIT), threshold not set; homolog safety cannot be
   confirmed until clustering is run; 6 repeated holo PDB IDs also unresolved
   → `data/registries/potential_homolog_risks.json`

4. **RESIDUE_MAPPING_FAILURES — 721 failures unresolved**
   721 residue token mismatches between RCSB PDB sequences and CIF coordinate records;
   policy for handling these (mask / exclude / remap) not yet approved
   → `data/registries/residue_mapping_failures.json`

5. **HUMAN_REVIEW_REQUIRED — label supervision policy**
   Proxy-ligand label policy and handling of missing residues not approved
   → `reports/phase2/proposed_label_policy.md`

6. **SPLIT_FREEZE_BLOCKED**
   Depends on resolving blockers 1–5; split manifest cannot be written until adoption,
   PCNA isolation, clustering, and label policy are all approved

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

1. **[IMMEDIATE]** Ask Friend to send metadata registry + summary stats + feature schemas (see `COLLABORATION.md` — Friend's Immediate Phase 2 Contribution section)
2. **[READY FOR RISHI]** Send `reports/phase2/human_review_packet.md` to Rishi — consolidates blockers 1, 2, 5 into one sign-off document
3. **[READY FOR RISHI]** Send `reports/phase2/residue_mapping_resolution_policy.md` to Rishi — resolves blocker 4 (decisions 4a–4d)
4. Choose sequence clustering tool (MMseqs2 or CD-HIT) and identity threshold; run clustering on CryptoBench candidate structures (blocker 3)
5. Draft split manifest (status: `draft_not_frozen`) once clustering and human review approvals land

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

Reshwant (2026-05-27): Two blocking documents prepared — `reports/phase2/human_review_packet.md`
consolidates blockers 1, 2, and 5 (CryptoBench adoption, PCNA isolation, label policy) with
YES/NO/DEFER checkboxes; `reports/phase2/residue_mapping_resolution_policy.md` addresses blocker
4 (420 remap / 297 mask / 4 exclude). Both draft_not_frozen, awaiting Rishi sign-off.

Friend (2026-05-27): Generated 5 Phase 2 support artifacts from `GNN_PNCA_crawled_data.zip`
(PCNA-focused crawl, 72 experimental structures, 146 ESM-2 .npy, 88 PyG graphs, 90 pocket scores;
no AlphaFold). Artifacts: `friend_crawl_registry.json`, `friend_crawl_stats.md`,
`friend_crawl_homolog_groups.json` (not_computed), `friend_feature_schema.json`,
`data/raw_intake/friend_sample/` (27 PDB + ESM pairs). Blocker 3 now has crawl metadata
available; clustering tool and threshold decision still pending.
