# Scientific Knowledge Audit

Date: 2026-08-15

## Facts and observations

- Root `src/`, `scripts/`, `tests`, `docs/research_base`, and `md_validation_4070` are canonical.
- `gnn_pcna_pre_md_v3.zip` was not found in this workspace.
- Frozen checkpoints exist for seeds 42, 43, and 44 with hashes in `research_os_memory/MODEL_REGISTRY.md`.
- Independent extraction selection used non-PCNA structures 1GQY, 2HNX, 2K1V, 2WER, and 3FU8.
- Final 1W60 pre-MD stability passed under frozen policy with literal mean Jaccard 0.6792 and 16 consensus residues.

## Assumptions

Key active assumptions are recorded in `docs/research_base/assumptions/ASSUMPTION_REGISTRY.md`, including:

- PCNA residue/chain mapping assumptions.
- ESM-to-graph row-order alignment assumptions.
- DBSCAN eps/min_samples as methodological choices, not source facts.
- Rank-fraction extraction as a scale-insensitive pre-MD gate method.
- Eligibility of the five non-PCNA extraction-selection structures.

## Decisions

Key active decisions are recorded in `docs/research_base/decisions/DECISION_REGISTRY.md`, including:

- Root canonicalization and historical archive disposition.
- Independent frozen extraction policy `independent_mcc_rank_fraction_size_weighted_cluster`.
- No production MD without human Gate-6 approval.

## Inferences

Key active inferences are recorded in `docs/research_base/inferences/INFERENCE_REGISTRY.md`, including:

- Seed score-scale sensitivity makes absolute thresholds fragile.
- Seed 44's lower absolute 1W60 score scale is not, by itself, evidence of unrelated raw-ranking behavior.
- Symmetry-normalized PCNA agreement is supplementary only.
- 8GLA chain-B validation is insufficiently independent for final extraction-method selection.

## Hypotheses and claims

`CLAIM-PCNA-001` is hypothesis-generating/computational: the frozen workflow prioritizes a seed-stable candidate 1W60 residue region. It does not claim a proven pocket, binding, druggability, mechanism, or in-vivo opening.

## Known limitations

- Small non-PCNA extraction benchmark.
- GNN scores are prioritization scores, not binding probabilities.
- PRE-MD PASS is not Gate-6 human approval.
- MD evidence remains inconclusive because production MD was not run.

## Governance instruction for future agents

Before reporting a suspected scientific or methodological issue, query the canonical methodology, source registry, decisions, assumptions, inference registry, known risks, and provenance. Determine whether the observed behavior is an implementation defect, documented methodological choice, intentional refinement, supported inference, unresolved scientific assumption, or genuine contradiction.

Do not label documented choices/assumptions/inferences as software bugs merely because they differ from generic defaults. Do not suppress a real contradiction merely because a decision has been documented.
