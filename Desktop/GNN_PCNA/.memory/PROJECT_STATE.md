---
updated: 2026-05-27
updated_by: claude-code (reshwant-session-end-final)
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
| Training | **BLOCKED — split + label freeze not approved** |
| Graph generation | **BLOCKED — split not frozen** |
| Molecular dynamics | **BLOCKED** |
| Scientific claims | **BLOCKED** |
| Split freeze | **PENDING HUMAN REVIEW** — split redesign needed for 5 cross-fold clusters |
| Label freeze | **PENDING HUMAN REVIEW** — labels generated; need sign-off |

CryptoBench adopted (cryptic-only). Labels generated. Split redesign required for 5 cluster groups.

---

## What Is Done (as of 2026-05-27)

- **Governance scaffold:** 40 binding docs in `docs/scientific_governance/` — complete
- **Wiki scaffold + memory system:** 59 wiki pages + `.memory/` layer (PROJECT_STATE, INDEX, MEMORY_RULES, handoff template) + `CLAUDE.md` + `00_COMPACT_INDEX.md` — complete
- **Intake infrastructure:** `scripts/dataset_intake.py` + `src/phase2_intake/` — complete
- **CryptoBench ADOPTED (cryptic-only):** Rishi approved 2026-05-27. Exclusions applied.
- **PCNA isolation policy:** Approved. 5e0v/3vkx excluded. 2xur/3bep confirmed NOT PCNA homologs at 30% — retained.
- **Label supervision contract (PU learning):** Approved. Positive-unlabeled framing.
- **Residue mapping — ALL APPROVED:** 4a (remap), 4b (mask), 4c (exclude 1lx7), 4d (exclude 4 wrong-chain).
- **Sequence clustering (blocker 3 — technical complete):**
  - RCSB API at 30% identity; PCNA cluster = 1168 (anchor: 5e0v)
  - 2xur/3bep: NOT PCNA homologs → retained
  - 6 cross-fold cluster risks found; 5 actionable (cluster 365/1lx7 is excluded)
  - Full results: `data/registries/sequence_cluster_assignments.json`, `cross_fold_cluster_risks.json`
  - Report: `reports/phase2/sequence_clustering_report.md`
- **Label generation — implementation complete:**
  - 1,101 structures labeled; 6 excluded (5e0v, 2b23/4gpi/8hc1/8oqp, 1lx7)
  - 16,335 positive labels; 3,704 masked; 0 remaps
  - Files: `data/labels/labels_{apo_pdb_id}.json`; manifest: `data/labels/label_manifest.json`
- **Friend's crawl (Prompt 1):** 5 metadata artifacts in repo; 51/72 structures in PCNA cluster (expected)
- **Phase 3 framework (friend's Prompt 2):** model + trainer (--dry-run guard) + evaluation + baselines; 58 tests; local only, not yet pushed to remote

---

## Current Blockers

1. ~~**CLEARED 2026-05-27** — CryptoBench adoption~~
2. ~~**CLEARED 2026-05-27** — PCNA isolation policy~~
3. **SPLIT_REDESIGN_REQUIRED — human review needed**
   5 cross-fold clusters identified at 30% identity threshold. Each must be assigned to a
   single split group. Draft split manifest needed before human sign-off.
   - Cluster 885: 8oqp (train) ↔ 7o1i (test)
   - Cluster 150: 6g0s (train) ↔ 2rfj (test)
   - Cluster 219: 2air+4c6b (train) ↔ 9atc (test) [also resolves repeated holo 2fzc/2fzg/4f04]
   - Cluster 5192: 6cy1 (train) ↔ 6n5j (test)
   - Cluster 3396: 6a45 (train) ↔ 6w10 (test)
   → `data/registries/cross_fold_cluster_risks.json`
   → `docs/scientific_governance/05_SPLIT_PROTOCOL.md`
4. ~~**CLEARED 2026-05-27** — Residue mapping policy (all 4 decisions approved)~~
5. ~~**CLEARED 2026-05-27** — Label supervision policy~~
6. **SPLIT_FREEZE_BLOCKED — pending blocker 3 resolution + human sign-off**
   Governance: `docs/scientific_governance/26_HUMAN_REVIEW_GATES.md`
7. **LABEL_FREEZE_PENDING — pending human sign-off**
   Labels are generated and hash-verified. Need Rishi sign-off before labels are frozen.
   Governance: `docs/scientific_governance/06_LABELING_RULES.md`, `26_HUMAN_REVIEW_GATES.md`

---

## Friend's Crawl — Fully Ingested

5 metadata artifacts in repo; full 40GB archive stays local. 51/72 structures are PCNA
cluster members — all are holdout-only per isolation policy.

---

## Next Tasks (priority order)

1. **[HUMAN DECISION — can decide now]** Split redesign for 5 cross-fold clusters.
   For each affected cluster, decide: move all affected structures to train OR test.
   Recommendation: move to train (keep test set clean), then re-run split balance check.
   See `data/registries/cross_fold_cluster_risks.json`.

2. **[AFTER 1]** Draft split manifest `data/registries/split_manifest_draft.json`:
   - All 1,107 apo IDs with fold assignment, cluster_id_30, pcna_holdout flag
   - 5 cross-fold clusters reassigned per human decision
   - Repeated holo structures grouped per clustering results
   Reference: `docs/scientific_governance/05_SPLIT_PROTOCOL.md`

3. **[AFTER 2 — HUMAN SIGN-OFF]** Freeze split manifest. Update status to `frozen`.
   Governance: `docs/scientific_governance/26_HUMAN_REVIEW_GATES.md`

4. **[SIMULTANEOUS WITH 3]** Freeze label manifest.
   Labels are implementation-complete; just needs Rishi sign-off.

5. **[AFTER 3 + 4]** Phase 2 complete. Friend can begin Phase 3 real training.
   Remove dry-run guard in `src/phase3_training/` with explicit human approval.

---

## Key Registry Paths

| Registry | Purpose |
|---|---|
| `data/registries/dataset_inventory.json` | Master dataset status |
| `data/registries/download_manifest.jsonl` | Append-only download log |
| `data/registries/cryptobench_candidate_cleaned_registry.json` | Remediated candidate list |
| `data/registries/sequence_cluster_assignments.json` | NEW: RCSB 30% identity clusters |
| `data/registries/cross_fold_cluster_risks.json` | NEW: 5 cross-fold leakage risks |
| `data/registries/potential_homolog_risks.json` | Known contamination flags |
| `data/registries/residue_mapping_failures.json` | 721 mapping failures (audit) |
| `data/registries/residue_mapping_per_structure_impact.json` | Per-structure 4c impact |
| `data/registries/friend_crawl_registry.json` | Friend's 72 PCNA structures |
| `data/registries/assumption_registry.json` | Scientific assumptions |
| `data/labels/label_manifest.json` | NEW: Hash-verified label manifest |

---

## Last Session Summary

Session 2026-05-27 (Reshwant + Claude Code): All Phase 2 technical work complete.
Sequence clustering ran via RCSB API on 1,107 CryptoBench + 72 friend structures.
PCNA cluster confirmed (1168); 2xur/3bep NOT PCNA homologs → retained. 5 cross-fold
cluster risks found requiring split redesign. Label generation ran successfully: 1,101
structures labeled, 16,335 positives, 3,704 masked, 0 remaps. Labels
hash-verified. Codex handoff document created at `reports/phase2/codex_handoff_20260527.md`.
Phase 2 is now pending human review for split redesign (5 clusters) + split/label freeze sign-off.
