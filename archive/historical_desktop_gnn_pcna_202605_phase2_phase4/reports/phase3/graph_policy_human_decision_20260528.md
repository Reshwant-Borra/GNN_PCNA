---
type: human-decision-record
date: 2026-05-28
decision_id: phase3_graph_policy_20260528
status: approved
gate: graph_edge_feature_policy_before_graph_generation
reviewer_role: human_project_owner_user_in_codex_session
---

# Phase 3 Graph Policy Human Decision - 2026-05-28

## Decision

Decision: `approved`.

The human project owner approved `reports/phase3/graph_edge_feature_policy_approval_packet_20260528.md`
in the active Codex session on 2026-05-28 with the approval note: "i approve of the markdown file."

This approval authorizes Codex to implement graph-generation scaffolding exactly as specified in
the approved packet and to emit graph artifacts, manifests, and provenance for human graph-release
review.

This approval does not authorize training, baseline execution, evaluation claims, PCNA prediction
interpretation, MD interpretation, or scientific claims.

## Evidence Packet Reviewed

- `reports/phase3/phase3_framework_rebuild_20260528.md`
- `reports/phase3/graph_edge_feature_policy_approval_packet_20260528.md`
- `data/registries/phase3_input_validation_20260528.json`
- `data/registries/phase3_dataset_index_20260528.json`
- `data/registries/phase3_residue_audit_manifest_20260528.json`
- `docs/scientific_governance/07_PREPROCESSING_AND_GRAPH_RULES.md`
- `docs/scientific_governance/08_MODEL_ARCHITECTURE_CONSTRAINTS.md`
- `docs/scientific_governance/15_PROVENANCE_AND_REPRODUCIBILITY.md`
- `docs/scientific_governance/19_STOP_CONDITIONS.md`
- `docs/scientific_governance/26_HUMAN_REVIEW_GATES.md`

## Approved Graph Policy

- Node policy: approved as written in `reports/phase3/graph_edge_feature_policy_approval_packet_20260528.md`.
- Edge policy: approved as written, including undirected CA-CA spatial edges with cutoff `8.0 Angstrom`
  and same-chain sequential edges that do not bridge missing-residue gaps.
- Coordinate/altloc policy: approved as written, including highest-occupancy CA selection and
  deterministic tie-breaks.
- Feature policy: approved as written, including residue identity one-hot plus binary flags for
  modified residue, missing CA, and has-altloc; chain ID, residue number, fold, cluster, label counts,
  split assignment, and PCNA/holdout flags remain metadata only.
- Manifest requirements: approved as written, including source hashes, policy hashes, graph hashes,
  command, timestamp, environment, and explicit `NO_TRAINING_PERFORMED` status.

## Limitations And Follow-Up

- First graph release still requires human review before any real training.
- Graph-generation implementation must fail closed on graph-label mismatch, nonnumeric coordinates,
  missing provenance, or policy/hash mismatch.
- No ESM/protein-language-model features are approved for the first graph release.
- No normalization statistics may be fit on validation or test structures.
- Real training remains blocked under `docs/scientific_governance/26_HUMAN_REVIEW_GATES.md`.

## Provenance

- source path: `reports/phase3/graph_edge_feature_policy_approval_packet_20260528.md`
- governance path: `docs/scientific_governance/07_PREPROCESSING_AND_GRAPH_RULES.md`,
  `docs/scientific_governance/08_MODEL_ARCHITECTURE_CONSTRAINTS.md`,
  `docs/scientific_governance/15_PROVENANCE_AND_REPRODUCIBILITY.md`,
  `docs/scientific_governance/19_STOP_CONDITIONS.md`,
  `docs/scientific_governance/26_HUMAN_REVIEW_GATES.md`
- confidence level: high for approval record content
- evidence status: verified for local evidence packet paths; human decision recorded from active session
