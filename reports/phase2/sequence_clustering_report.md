---
type: analysis-report
status: complete_with_lookup_gaps
created: 2026-05-27
blocker_addressed: 3
method: RCSB_precomputed_sequence_clusters_30pct_identity
---

# Sequence Clustering Report — Phase 2

**Method:** RCSB pre-computed sequence clusters at 30% identity  
**PCNA anchor:** 5e0v/chain A → cluster_id_30 = **1168**  
**Governance:** `docs/scientific_governance/05_SPLIT_PROTOCOL.md`

---

## Summary

| Metric | Value |
|---|---|
| CryptoBench apo structures clustered | 1107 |
| Friend crawl structures clustered | 72 |
| Null cluster lookups (API or no entity) | 3 |
| Cross-fold cluster risks (sequence leakage) | 6 |
| PCNA cluster members in CryptoBench | 1 |
| PCNA cluster members in friend crawl | 51 |

---

## Sliding Clamp Candidates

PCNA (5e0v) cluster ID at 30%: **1168**

| PDB | cluster_id_30 | PCNA Homolog? | Description | Policy |
|---|---|---|---|---|
| 2xur | 1415 | No → Retain | DNA POLYMERASE III SUBUNIT BETA | RETAIN |
| 3bep | None | No → Retain |  | RETAIN |

---

## Repeated Holo PDB Pair Resolution

6 holo PDB IDs appear in multiple official folds. The apo structures they connect
must be in the same split group — either because they are sequence homologs OR
because splitting them would let the test set see the same holo structure twice.

| Group | Apos | Shared Holos | Same Cluster? | Action |
|---|---|---|---|---|
| holo_2fzc_2fzg_4f04 | 2air 9atc | 2fzc 2fzg 4f04 | YES ([219, 219]) | GROUP_IN_SAME_SPLIT |
| holo_5qya_7fo6 | 3e9p 4ilg | 5qya 7fo6 | NO ([216, 381]) | KEEP_SHARED_HOLO_IN_ONE_SPLIT |
| holo_6a5y | 4n5g 6hl0 | 6a5y | NO ([1190, 2228]) | KEEP_SHARED_HOLO_IN_ONE_SPLIT |

---

## Cross-Fold Sequence Leakage Risks

**6 clusters** span both train and test folds at >=30% identity.
All apo structures within each cluster must be assigned to the same fold.

| Cluster ID | Train apos (sample) | Test apos (sample) |
|---|---|---|
| 150 | 6g0s | 2rfj |
| 219 | 2air, 4c6b | 9atc |
| 365 | 1lx7 | 6f52 |
| 885 | 8oqp | 7o1i |
| 3396 | 6a45 | 6w10 |
| 5192 | 6cy1 | 6n5j |

---

## PCNA Cluster Members

**Cluster ID:** 1168

CryptoBench (1): 5e0v
Friend crawl (51): 1AXC, 1U76, 1U7B, 1VYJ, 1VYM, 1W60, 2ZVK, 2ZVL, 2ZVM, 3P87, 3TBL, 3VKX, 3WGW, 4D2G, 4RJF, 4ZTD, 5E0T, 5E0U, 5E0V, 5IY4, 5MAV, 5MLO, 5MLW, 5MOM, 5YCO, 5YD8, 6CBI, 6EHT, 6FCM, 6FCN, 6GIS, 6GWS, 6HVO, 6K3A, 6QC0, 6QCG, 7EFA, 7KQ0, 7KQ1, 7M5L, 7M5M, 7M5N, 8COB, 8E84, 8F5Q, 8GCJ, 8GL9, 8GLA, 9CG4, 9N3L, 9VGW

All PCNA cluster members excluded from training/validation per decision 2 (2026-05-27).

---

## Provenance

- RCSB REST API: `polymer_entity_instance` → entity_id; `polymer_entity` → `rcsb_cluster_membership`
- Cluster IDs are RCSB's sequence-identity-based groupings recomputed each UniProt release
- identity=30 corresponds to SCOP superfamily / conservative homolog level
- Governance: `docs/scientific_governance/05_SPLIT_PROTOCOL.md`
- Evidence status: verified (RCSB pre-computed, not ad-hoc)
- Generated: 2026-05-27T23:41:53.065543
