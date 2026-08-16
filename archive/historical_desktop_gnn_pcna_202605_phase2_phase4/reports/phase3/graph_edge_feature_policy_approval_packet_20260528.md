---
type: human-approval-packet
date: 2026-05-28
agent: codex
status: APPROVED_BY_HUMAN_DECISION_RECORD
gate: graph_edge_feature_policy_before_graph_generation
---

# Phase 3 Graph Edge/Feature Policy Approval Packet - 2026-05-28

## Purpose

This packet is for human review of the Phase 3 data/residue audit and for approval or
revision of graph construction policy before any graph tensors are generated. Codex has not
generated graph tensors, selected trainable model science, run baselines, run evaluation, or
trained.

## Evidence Reviewed

| Evidence | Path | Status |
|---|---|---|
| Phase 3 rebuild report | `reports/phase3/phase3_framework_rebuild_20260528.md` | PASS |
| Input validation manifest | `data/registries/phase3_input_validation_20260528.json` | PASS |
| CIF extraction manifest | `data/registries/phase3_cif_extraction_manifest_20260528.json` | PASS |
| Dataset index | `data/registries/phase3_dataset_index_20260528.json` | PASS |
| Residue audit manifest | `data/registries/phase3_residue_audit_manifest_20260528.json` | PASS |
| Phase 3 tests | `tests/phase3/` | PASS, 16 tests total with Phase 2 intake tests |

Governance references:

- `docs/scientific_governance/04_DATASET_CONSTRAINTS.md`
- `docs/scientific_governance/05_SPLIT_PROTOCOL.md`
- `docs/scientific_governance/06_LABELING_RULES.md`
- `docs/scientific_governance/07_PREPROCESSING_AND_GRAPH_RULES.md`
- `docs/scientific_governance/08_MODEL_ARCHITECTURE_CONSTRAINTS.md`
- `docs/scientific_governance/15_PROVENANCE_AND_REPRODUCIBILITY.md`
- `docs/scientific_governance/19_STOP_CONDITIONS.md`
- `docs/scientific_governance/26_HUMAN_REVIEW_GATES.md`

## Audit Findings

- Frozen split hash: `24dd5e347d880108`.
- Dataset index: `1,101` non-excluded structures.
- Fold distribution: test=214, train-0=220, train-1=223, train-2=222, train-3=222.
- Exclusions: all 6 excluded records skipped.
- PCNA isolation: no `cluster_id_30=1168` records in the Phase 3 dataset index.
- Residue audit: `1,101` structures PASS.
- Residue nodes audited: `371,651`.
- Positives aligned: `16,335`.
- Masked labels accounted for: `3,704`.
- Masked labels on audited nodes: `3,696`.
- Masked labels without nodes: `8`, all in `4hr7`, recorded explicitly as loss-excluded masked labels.
- Background/unlisted residues: `351,620`, treated as PU/background, not true negatives.
- Residues with alternate location records: `4,380`.
- Residues without CA atom: `22`.

## Recommended Human Decision

Decision requested: approve, revise, or reject the following initial graph policy for the
first graph-generation implementation. This is a conservative policy intended to satisfy
governance without using PCNA-specific assumptions, validation/test distributions, or
unapproved external features.

### Node Policy

- One graph node per audited target-chain protein residue from `_atom_site`.
- Include standard `ATOM` residues and polymer-positioned modified residues encoded as
  `HETATM` when `_atom_site.label_seq_id` exists.
- Exclude waters, free ligands, ions, DNA/RNA, partner chains, and non-target protein chains
  from graph nodes.
- Preserve chain ID, auth residue number, insertion code, label sequence ID, entity ID,
  residue name, atom names, altloc IDs, and source CIF hash in graph metadata.
- Keep `label=-1` residues as nodes when present, but set `loss_mask=false`.
- Do not add nodes for the 8 masked labels without resolved target-chain residues in `4hr7`;
  record them in the graph manifest as masked labels without nodes and exclude them from loss.
- Fail closed if any non-masked positive label cannot align to a node.

### Edge Policy

- Spatial edges: undirected CA-CA contact edges with cutoff `8.0 Angstrom`.
- Sequential edges: undirected edges between adjacent residues only when they are consecutive
  in the same target chain and both residues are present; do not bridge missing-residue gaps.
- Edge attributes for MVP graph tensors: edge type (`spatial` or `sequential`) and distance
  for spatial edges. Do not expose raw residue numbers as model features.
- For the 22 residues without CA atoms: keep the node, omit spatial CA edges for that residue,
  allow sequential edges only when adjacency can be established without bridging a gap, and
  record the count and residue IDs in the graph manifest.
- Cross-chain, symmetry, DNA/RNA, ligand, partner-protein, and PCNA-trimer-specific edges are
  not approved for the MVP graph release.

### Coordinate and AltLoc Policy

- Coordinate basis for spatial edges: CA atom only.
- If a residue has multiple CA altlocs, use the CA coordinate with highest occupancy; tie-break
  lexicographically by altloc ID, with `.`/`?` preferred over lettered alternates when occupancy
  ties.
- Record per-graph counts of altloc residues and any selected altloc tie-breaks.
- Fail closed if an atom row needed for graph construction has nonnumeric coordinates.

### Feature Policy

- MVP trainable node features: residue identity one-hot from `auth_comp_id`/`label_comp_id`,
  plus binary flags for modified residue, missing CA, and has-altloc.
- Metadata-only, not trainable features: chain ID, auth residue number, insertion code, label
  sequence ID, entity ID, source file hash, fold, cluster ID, and label provenance.
- Do not include raw chain ID, raw residue number, fold ID, cluster ID, structure size, label
  count, label mask, split assignment, or PCNA/holdout flags as model input features.
- Do not include ESM/protein-language-model embeddings in the first graph release. Any later
  ESM use requires model name, version, input sequence, sequence hash, feature hash, and
  train-only normalization policy.
- Do not fit normalization statistics on validation or test structures.

### Graph Manifest Requirements

Every graph manifest entry must include:

- structure ID, fold, split hash, label hash, source CIF hash, graph-construction code hash,
  feature-definition hash, graph hash, command, timestamp, environment, and seed where
  applicable;
- included/excluded chains;
- residue identifiers for every node;
- node count, label count, positive count, masked count, background count;
- missing-CA count, altloc count, masked-label-without-node count;
- edge policy and feature policy hashes;
- explicit `NO_TRAINING_PERFORMED` status for graph generation runs.

## Risks and Required Follow-Up

- The CA-CA `8.0 Angstrom` cutoff is a proposed first graph policy, not a result-derived
  threshold. It must be human-approved before implementation.
- Residue identity features may learn protein-family or sequence-composition shortcuts; this
  requires later shortcut audits and ablations before claims.
- Chain ID and residue number must remain metadata only unless a separate ablation-backed
  approval permits them as trainable inputs.
- The 22 no-CA residues and 4,380 altloc residues require manifest-level reporting in the
  first graph release.
- First graph release still requires human review before real training.

## Human Review Decision Form

Decision ID: `phase3_graph_policy_20260528`

Reviewer: human project owner/user in Codex session

Date: 2026-05-28

Decision: `approved`

Evidence packet reviewed:

- `reports/phase3/phase3_framework_rebuild_20260528.md`
- `reports/phase3/graph_edge_feature_policy_approval_packet_20260528.md`
- `data/registries/phase3_input_validation_20260528.json`
- `data/registries/phase3_dataset_index_20260528.json`
- `data/registries/phase3_residue_audit_manifest_20260528.json`

Approved graph policy:

- Node policy: approved as written in this packet.
- Edge policy: approved as written in this packet.
- Coordinate/altloc policy: approved as written in this packet.
- Feature policy: approved as written in this packet.
- Manifest requirements: approved as written in this packet.

Limitations: first graph release still requires human review before real training; no training,
baseline execution, evaluation claims, PCNA prediction interpretation, MD interpretation, or
scientific claims are approved by this graph-policy decision.

Follow-up actions: implement graph-generation scaffolding exactly as approved, emit graph artifacts
and manifests/provenance, then prepare first graph release for human review.

Signature / approval note: human project owner wrote in the active Codex session on 2026-05-28,
"i approve of the markdown file."

Formal decision record: `reports/phase3/graph_policy_human_decision_20260528.md`

## Current Status

Status: `APPROVED_BY_HUMAN_DECISION_RECORD`.

Codex may implement graph generation according to the approved policy and emit graph manifests
and provenance. No real training may start until the first graph release receives human review
and the training gate is separately approved.

Confidence: high for artifact review and audit counts. Evidence status: verified for local
artifacts; pending human decision for graph policy.
