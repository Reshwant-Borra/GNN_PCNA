---
type: human-decision-record
date: 2026-05-28
decision_id: phase3_first_graph_release_20260528
gate: first_graph_release
governance: docs/scientific_governance/26_HUMAN_REVIEW_GATES.md
status: approved
reviewer_role: human_project_owner
---

# Phase 3 First Graph Release — Human Approval Record

## Decision

**Decision: `approved`**

The human project owner has reviewed the graph release audit report and the
collection-level manifest and approves the first graph release as correctly
implementing the approved policy (`phase3_graph_policy_20260528`).

This approval:
- Clears **GATE 1** (First graph release) under
  `docs/scientific_governance/26_HUMAN_REVIEW_GATES.md`.
- Does **not** authorize real training, baseline execution, evaluation on test,
  PCNA prediction interpretation, MD runs, or scientific claims.
- Real training (GATE 2) requires a separate first-training sign-off once the
  model/training approval packet has been reviewed.

## Evidence Packet Reviewed

| Artifact | Path | Check |
|---|---|---|
| Graph release audit report | `reports/phase3/graph_release_audit_20260528.md` | reviewed |
| Collection-level manifest | `data/graphs/graph_release_manifest_8c22e46f524d5f1d.json` | reviewed |
| Graph policy approval | `reports/phase3/graph_policy_human_decision_20260528.md` | verified reference |
| Phase 2 residue audit | `data/registries/phase3_residue_audit_manifest_20260528.json` | count-verified |
| Smoke test (5 structures) | NPZ shapes, manifest fields, hash consistency | pass |
| Full run (1,101 structures) | 0 failures, all counts match | pass |

## Verification Checklist

| Check | Expected | Observed | Pass |
|---|---|---|---|
| Structures generated | 1,101 | 1,101 | ✓ |
| Failures | 0 | 0 | ✓ |
| Positives | 16,335 | 16,335 | ✓ |
| Masked nodes | 3,696 | 3,696 | ✓ |
| Masked-without-nodes | 8 (4hr7) | 8 (4hr7) | ✓ |
| Background nodes | 351,620 | 351,620 | ✓ |
| No-CA nodes | 22 | 22 | ✓ |
| Altloc nodes | 4,380 | 4,380 | ✓ |
| Policy hash unique | 1 | 1 | ✓ |
| Feature hash unique | 1 | 1 | ✓ |
| `NO_TRAINING_PERFORMED` in all entries | true | true | ✓ |
| ESM features absent | absent | absent | ✓ |
| Normalization absent | absent | absent | ✓ |
| PCNA cluster 1168 absent | absent | absent | ✓ |
| Status | PENDING_HUMAN_REVIEW | PENDING_HUMAN_REVIEW | ✓ |

## Approved Artifacts

- `data/graphs/graph_release_manifest_8c22e46f524d5f1d.json`
- `data/graphs/*.npz` (1,101 files)
- `data/graphs/*_meta.json` (1,101 files)

These artifacts are approved for use as model training inputs once GATE 2
(first-training approval) is separately recorded.

## Limitations and Follow-Up

- Average spatial degree (~10 contacts/residue) is plausible for 8 Å CA-CA
  cutoff on globular proteins. It is not a result-derived or tuned value.
- The 4hr7 masked-without-nodes case (8 labels absent from atom_site) is
  correctly handled and excludes those residues from the loss.
- 436 structures used altloc tiebreaks; affected residues are documented in
  per-structure manifest entries.
- No shortcut audit has been run yet. Chain ID and residue number are absent
  from trainable features, but graph-size and sequence-composition shortcuts
  remain possible and must be ablated after first training.
- First training run still requires GATE 2: a separate human sign-off after
  reviewing `reports/phase3/model_training_approval_packet_20260528.md`.

## Provenance

- decision_id: `phase3_first_graph_release_20260528`
- manifest_hash: `8c22e46f524d5f1d`
- policy_hash_sha256 (prefix): `513586cc44df97928228764a02038844...`
- feature_definition_hash_sha256 (prefix): `80049e38d0f6ccf6c59f045bf977b69b...`
- split_manifest_hash: `24dd5e347d880108`
- governance: `docs/scientific_governance/26_HUMAN_REVIEW_GATES.md`
- confidence: high
- evidence_status: verified
