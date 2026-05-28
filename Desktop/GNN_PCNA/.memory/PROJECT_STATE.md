---
updated: 2026-05-27
updated_by: claude-code (reshwant-session-phase2-complete)
---

# Project State — GNN-PCNA

This file is the single authoritative current-state snapshot. Agents update it at every
session close. Read it immediately after `CLAUDE.md` or `AGENTS.md`.

**Staleness check:** If `updated` in the frontmatter above is >7 days before today's date,
treat this file as potentially stale. Reconstruct current state from
`wiki/analyses/coding_agent_context.md` and the most recent
`reports/phase2/handoff_YYYYMMDD.md`, then update this file before starting any task.

---

## Phase

**Phase 2 COMPLETE → Phase 3 AUTHORIZED**

| System | Status |
|---|---|
| Training | **AUTHORIZED** — split + label freeze approved 2026-05-27 |
| Graph generation | **AUTHORIZED** — split frozen |
| Molecular dynamics | BLOCKED (Phase 3+ scope) |
| Scientific claims | BLOCKED (model must first complete Phase 3) |
| Split freeze | **FROZEN** — `data/registries/split_manifest_frozen.json` (hash: 24dd5e347d880108) |
| Label freeze | **FROZEN** — `data/labels/label_manifest.json` |

All Phase 2 blockers cleared as of 2026-05-27. Phase 3 training authorized.

---

## What Is Done (as of 2026-05-27)

- **Governance scaffold:** 40 binding docs in `docs/scientific_governance/` — complete
- **Wiki scaffold + memory system:** 59 wiki pages + `.memory/` layer + `CLAUDE.md` + `00_COMPACT_INDEX.md` — complete
- **Intake infrastructure:** `scripts/dataset_intake.py` + `src/phase2_intake/` — complete
- **CryptoBench ADOPTED (cryptic-only):** Rishi approved 2026-05-27. Exclusions applied.
- **PCNA isolation policy:** Approved. 5e0v/3vkx excluded. 2xur/3bep confirmed NOT PCNA homologs at 30% — retained.
- **Label supervision contract (PU learning):** Approved. Positive-unlabeled framing.
- **Residue mapping — ALL APPROVED:** 4a (remap), 4b (mask), 4c (exclude 1lx7), 4d (exclude 4 wrong-chain).
- **Sequence clustering:** RCSB API at 30% identity; PCNA cluster = 1168; 5 cross-fold risks found and resolved.
- **Label generation:** 1,101 structures labeled; 16,335 positives; 3,704 masked; 0 remaps. Files: `data/labels/labels_{apo_pdb_id}.json`.
- **Split redesign APPROVED:** 7o1i→train-1, 2rfj→train-2, 9atc→train-1, 6n5j→train-0, 6w10→train-2.
- **Split manifest FROZEN:** `data/registries/split_manifest_frozen.json` — hash 24dd5e347d880108. Distribution: test=214, train-0=220, train-1=223, train-2=222, train-3=222.
- **Label manifest FROZEN:** `data/labels/label_manifest.json` — status=frozen.
- **Approval record:** `reports/phase2/split_manifest_approval_20260527.md` — authorizes Phase 3 dry-run guard removal.
- **Friend's crawl (Prompt 1):** 5 metadata artifacts in repo; 51/72 structures in PCNA cluster (holdout-only).
- **Phase 3 framework (friend's Prompt 2):** model + trainer + evaluation + baselines; 58 tests. `--dry-run` guard authorized for removal per approval record.

---

## Current Blockers

**NONE — Phase 2 complete.**

All previous blockers cleared:
1. ~~CryptoBench adoption — CLEARED 2026-05-27~~
2. ~~PCNA isolation policy — CLEARED 2026-05-27~~
3. ~~Sequence clustering — CLEARED 2026-05-27~~
4. ~~Residue mapping policy — CLEARED 2026-05-27~~
5. ~~Label supervision policy — CLEARED 2026-05-27~~
6. ~~Split freeze — CLEARED 2026-05-27~~
7. ~~Label freeze — CLEARED 2026-05-27~~

---

## Friend's Crawl — Fully Ingested

5 metadata artifacts in repo; full 40GB archive stays local. 51/72 structures are PCNA
cluster members — all are holdout-only per isolation policy.

---

## Next Tasks (Phase 3)

1. **Remove `--dry-run` guard** in `src/phase3_training/`.
   Authorization: `reports/phase2/split_manifest_approval_20260527.md`.
   Owner: Friend (per `COLLABORATION.md`).

2. **Implement data pipeline** connecting frozen labels/splits to Phase 3 training:
   - Read `data/registries/split_manifest_frozen.json` for fold assignments
   - Read `data/labels/labels_{apo_pdb_id}.json` for per-residue labels
   - Build graph loader using `data/raw_intake/cryptobench/cif-files/` CIF structures
   - Governance: `docs/scientific_governance/07_PREPROCESSING_AND_GRAPH_RULES.md`

3. **Run Phase 3 training** (with real data, not dry-run).
   Governance: `docs/scientific_governance/08_MODEL_ARCHITECTURE_CONSTRAINTS.md`, `09_EVALUATION_PROTOCOL.md`.

4. **Baseline evaluation** (PocketMiner, fpocket, P2Rank).
   Governance: `docs/scientific_governance/10_BASELINE_REQUIREMENTS.md`.

---

## Key Registry Paths

| Registry | Purpose |
|---|---|
| `data/registries/split_manifest_frozen.json` | **FROZEN** split assignments — 1,101 structures |
| `data/labels/label_manifest.json` | **FROZEN** label manifest |
| `data/registries/sequence_cluster_assignments.json` | RCSB 30% identity clusters |
| `data/registries/cross_fold_cluster_risks.json` | 5 resolved cross-fold risks |
| `data/registries/cryptobench_candidate_cleaned_registry.json` | Remediated candidate list |
| `data/registries/excluded_records.json` | 6 excluded structures with reasons |
| `data/registries/residue_remap_log.json` | 0 remaps (auth_seq_id succeeded for all) |
| `data/registries/friend_crawl_registry.json` | Friend's 72 PCNA structures |
| `data/labels/labels_{apo_pdb_id}.json` | Per-structure label files (1,101 files) |

---

## Last Session Summary

Session 2026-05-27 (Reshwant + Claude Code): Phase 2 complete. Split redesign approved
(7o1i, 2rfj, 9atc, 6n5j, 6w10 moved to train). Split manifest frozen (hash: 24dd5e347d880108,
1,101 structures, distribution: test=214/train-0=220/train-1=223/train-2=222/train-3=222).
Label manifest frozen (1,101 structures, 16,335 positives, 3,704 masked). Approval record
at `reports/phase2/split_manifest_approval_20260527.md`. Phase 3 training now authorized.
Friend may remove dry-run guard and begin real training.
