---
type: graph-release-audit
date: 2026-05-28
status: PENDING_HUMAN_REVIEW
manifest_hash: 8c22e46f524d5f1d
policy_decision_id: phase3_graph_policy_20260528
agent: claude-sonnet-4-6
---

# Phase 3 Graph Release Audit — 2026-05-28

## Status

**PENDING_HUMAN_REVIEW.** No training, baseline execution, evaluation, PCNA prediction
interpretation, or scientific claims have been performed. Training remains blocked under
`docs/scientific_governance/26_HUMAN_REVIEW_GATES.md` until this release receives explicit
human sign-off and a separate first-training approval is recorded.

## Provenance

| Field | Value |
|---|---|
| Manifest file | `data/graphs/graph_release_manifest_8c22e46f524d5f1d.json` |
| Manifest hash (16-char prefix) | `8c22e46f524d5f1d` |
| Policy approval record | `reports/phase3/graph_policy_human_decision_20260528.md` |
| Policy decision ID | `phase3_graph_policy_20260528` |
| Policy hash SHA-256 (prefix) | `513586cc44df97928228764a02038844...` |
| Feature definition hash (prefix) | `80049e38d0f6ccf6c59f045bf977b69b...` |
| Split manifest hash (prefix) | `24dd5e347d880108` |
| Git commit | `c8c0f81` |
| Generated at | 2026-05-28 |
| PYTHONPATH | `src/` |

Policy hash and feature definition hash are **identical across all 1,101 graph entries**
(1 unique policy hash, 1 unique feature hash), confirming no per-structure policy drift.

## Approved Policy Applied

| Policy element | Approved value |
|---|---|
| Node definition | One node per target-chain residue (ATOM + polymer HETATM) |
| Spatial edges | Undirected CA-CA, cutoff **8.0 Å** (approved) |
| Sequential edges | Undirected, consecutive `label_seq_id` (diff=1), same chain, no gap bridging |
| Node features | 25-dim float32: 22 one-hot residue identity + 3 binary flags |
| AltLoc resolution | Highest occupancy; tie-break lexicographic (`.`/`?` > letters; `A` < `B`) |
| ESM features | NOT INCLUDED |
| Normalization | NONE APPLIED |
| Chain metadata | Not trainable features (metadata sidecar only) |

---

## Collection Summary

| Metric | Count |
|---|---|
| Structures generated | **1,101** |
| Structures failed | **0** |
| Total residue nodes | **371,651** |
| Total positive labels (`label=1`) | **16,335** |
| Total masked labels in nodes (`label=-1`) | **3,696** |
| Total masked labels without nodes | **8** (all in `4hr7`, documented below) |
| Total background/unlabeled nodes (`label=0`) | **351,620** |
| Total spatial edge pairs (undirected) | **1,849,858** |
| Total sequential edge pairs (undirected) | **369,620** |
| Nodes without CA atom | **22** |
| Nodes with altloc records | **4,380** |
| Structures with altloc tiebreaks applied | **436** |

Cross-checks against `data/registries/phase3_residue_audit_manifest_20260528.json`:

| Expected | Observed | Match |
|---|---|---|
| 1,101 structures | 1,101 | ✓ |
| 16,335 positives | 16,335 | ✓ |
| 3,704 masked total (3,696 in nodes + 8 without nodes) | 3,696 + 8 = 3,704 | ✓ |
| 22 no-CA residues | 22 | ✓ |
| 4,380 altloc residues | 4,380 | ✓ |
| 351,620 background | 351,620 | ✓ |

All counts are **exact matches** to the Phase 2 residue audit. No leakage, no inflation,
no label alignment errors.

---

## Fold Distribution

| Fold | Structures |
|---|---|
| test | 214 |
| train-0 | 220 |
| train-1 | 223 |
| train-2 | 222 |
| train-3 | 222 |
| **Total** | **1,101** |

Matches frozen split manifest (`24dd5e347d880108`). PCNA cluster `1168` (structure `5e0v`)
is absent — it was excluded in Phase 2 and is not present in any fold.

---

## Node Count Distribution

| Statistic | Residues per structure |
|---|---|
| Minimum | 52 |
| Maximum | 2,598 |
| Mean | 337.6 |
| Median | 295.0 |
| 10th percentile | 149.0 |
| 90th percentile | 580.0 |

The size range (52–2,598) is expected for CryptoBench, which spans small domains to
multi-domain complexes.

---

## Spatial Edge Statistics

| Statistic | Value |
|---|---|
| Min spatial edge pairs (per structure) | 219 |
| Max spatial edge pairs (per structure) | 13,287 |
| Mean spatial edge pairs (per structure) | 1,680.2 |
| Average spatial degree (contacts/residue) | **9.95** |
| Total spatial pairs (undirected) | 1,849,858 |
| Total directed spatial edges stored | 3,699,716 |

Average spatial degree of ~10 contacts per residue is typical for an 8 Å CA-CA
cutoff on globular protein structures. This is not a training-derived value.

---

## Sequential Edge Statistics

| Statistic | Value |
|---|---|
| Total sequential edge pairs (undirected) | 369,620 |
| Total directed sequential edges stored | 739,240 |

Sequential edges connect residues with consecutive `label_seq_id` integers (diff=1)
within the same chain. Gap bridging is not performed — residues separated by missing
loops are not connected. The total (369,620) is slightly less than the total nodes
minus structures (371,651 − 1,101 = 370,550), reflecting genuine missing-residue gaps
across the dataset.

---

## Masked-Label Handling

### Masked labels in nodes (162 structures)

162 structures contain one or more `label=-1` residues (masked from loss per the
positive-unlabeled supervision contract). These residues are included as graph nodes
with `loss_mask=False`. They are never used in the loss computation.

### Masked labels without nodes — `4hr7` (8 labels)

The single structure with masked labels that have no corresponding resolved residue
is **`4hr7`**, which has 8 masked label entries on chain D that are absent from
`_atom_site`. These were identified and documented in the Phase 2 residue audit.

| Label key | Reason |
|---|---|
| `D_117`, `D_122`, `D_124` | Absent from atom_site; masked per decision 4b |
| `D_92`, `D_94`, `D_95`, `D_96`, `D_97` | Absent from atom_site; masked per decision 4b |

These 8 labels are recorded in `4hr7`'s manifest entry as
`masked_label_entries_without_nodes: 8` and `masked_label_keys_without_nodes`.
They are excluded from the loss and have no nodes in the graph.

---

## Missing-CA Handling (22 residues across 14 structures)

22 residues across 14 structures have no CA atom in the CIF file. Per the approved
policy:

- The residue is retained as a graph node.
- The `missing_ca` binary flag is set to `1.0` in the feature vector.
- The residue is excluded from spatial CA-CA edge computation.
- Sequential edges are included when adjacency can be established without gap bridging.

No special treatment affects the label or loss mask.

---

## AltLoc Handling (4,380 nodes with altloc across 481 structures)

481 structures contain one or more residues with alternate location records. 436 of
these required an altloc tiebreak. The approved resolution policy was applied:

1. Select the CA atom record with the highest occupancy.
2. On occupancy ties: prefer `.`/`?` (no-altloc sentinel) over lettered alternates;
   among letters, prefer alphabetically earlier (`A` < `B` < ...).

Selected altloc IDs are recorded per-node in the JSON sidecar under
`selected_altloc`. Structures with tiebreaks list the affected residues under
`altloc_tiebreaks_applied` in the manifest entry.

---

## What Is NOT Present in These Graphs

Per the approved policy and governance constraints, the following are **explicitly
absent** and must not be added before separate governance approval:

- ESM / protein-language-model embeddings
- Normalization statistics of any kind
- Raw chain ID, residue number, fold ID, or cluster ID as trainable node features
- Cross-chain, symmetry, or PCNA-trimer-specific edges
- DNA/RNA, ligand, or partner-protein edges
- Any training, gradient computation, baseline run, or evaluation result

---

## File Layout

```
data/graphs/
├── <pdb_id>.npz                 # NumPy arrays: node_features, node_labels,
│                                #   loss_mask, edge_index, edge_type, edge_distance
├── <pdb_id>_meta.json           # Per-structure metadata: node_metadata, manifest_entry
└── graph_release_manifest_8c22e46f524d5f1d.json  # Collection-level provenance
```

Per-structure NPZ arrays:

| Array | Shape | dtype | Description |
|---|---|---|---|
| `node_features` | (N, 25) | float32 | 22 one-hot + 3 binary flags |
| `node_labels` | (N,) | int32 | {-1, 0, 1} |
| `loss_mask` | (N,) | bool | True = participates in loss |
| `edge_index` | (2, E) | int64 | Source and destination node indices (both directions) |
| `edge_type` | (E,) | int8 | 0=spatial, 1=sequential |
| `edge_distance` | (E,) | float32 | Angstrom for spatial; inf for sequential |

---

## Governance Compliance

| Check | Status |
|---|---|
| Policy approved before graph generation | ✓ `phase3_graph_policy_20260528` |
| Policy hash consistent across all graphs | ✓ (1 unique hash) |
| Feature hash consistent across all graphs | ✓ (1 unique hash) |
| Split manifest hash matches frozen | ✓ `24dd5e347d880108` |
| Positive counts match Phase 2 audit | ✓ 16,335 |
| Masked counts match Phase 2 audit | ✓ 3,696 nodes + 8 without nodes = 3,704 |
| No-CA counts match Phase 2 audit | ✓ 22 |
| Altloc counts match Phase 2 audit | ✓ 4,380 |
| PCNA cluster `1168` absent | ✓ `5e0v` excluded |
| 6 excluded records absent | ✓ |
| `NO_TRAINING_PERFORMED` in all entries | ✓ |
| ESM features absent | ✓ |
| Normalization absent | ✓ |
| 0 generation failures | ✓ |

---

## Next Required Step

**Human review of this graph release is required before real training may begin.**

Governance: `docs/scientific_governance/26_HUMAN_REVIEW_GATES.md`

The reviewer should confirm:

1. Node counts, edge counts, and label counts are plausible.
2. Average spatial degree (~10) is reasonable for 8 Å CA-CA cutoff.
3. The 4hr7 masked-without-nodes case is correctly handled (8 labels, no nodes, excluded from loss).
4. Altloc tiebreak policy was applied (436 structures, documented in manifest).
5. No ESM features, no normalization, no training occurred.
6. Policy hash and feature hash are stable across all 1,101 graphs.

Upon approval, record a `first_training_approval_YYYYMMDD.md` in `reports/phase3/`
and remove the dry-run guard in `src/phase3_training/gates.py` to unblock real training.
