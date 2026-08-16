# Scientific Governance Expansion Report

## Purpose

This report documents the second governance expansion requested after the initial Phase 2 governance layer. The expansion makes biological plausibility, human review, adversarial audit, null baselines, uncertainty, benchmark quality, and AI hallucination control first-class gates.

## Files Added

| File | Purpose |
|---|---|
| `docs/scientific_governance/24_PROJECT_SCOPE.md` | Prevents drift into drug discovery, therapy, clinical prediction, or treatment claims. |
| `25_BIOLOGICAL_DATA_SANITY_REVIEW.md` | Requires manual pre-training biological plausibility review. |
| `26_HUMAN_REVIEW_GATES.md` | Requires human signoff for scientific freeze points. |
| `27_RED_TEAM_AUDIT.md` | Forces adversarial attempts to disprove the project. |
| `28_NULL_HYPOTHESIS_BASELINES.md` | Requires trivial biological heuristic baselines. |
| `29_BENCHMARK_LIMITATIONS.md` | Audits CryptoBench and any benchmark before adoption. |
| `30_NEGATIVE_RESULT_SUCCESS_CRITERIA.md` | Defines success even for negative, mixed, or inconclusive results. |
| `31_DATA_LIFECYCLE_TRACKING.md` | Tracks why data are accepted, removed, quarantined, or deprecated. |
| `32_INTERPRETABILITY_BEFORE_CLAIMS.md` | Requires attribution and ablation review before PCNA claims. |
| `33_PRE_MD_REALITY_CHECK.md` | Forces a falsifiable biological hypothesis before MD interpretation. |
| `34_AI_HALLUCINATION_DETECTION.md` | Requires source references or uncertainty markers for AI-generated science. |
| `35_SCIENTIFIC_UNCERTAINTY_REGISTER.md` | Makes uncertainty a first-class artifact. |
| `36_PUBLICATION_READINESS.md` | Defines final external-facing readiness. |
| `37_PHASE2_IMPLEMENTATION_PLAN.md` | Handoff plan for a new chat or implementation agent. |

## Governance Files Updated

- `00_README.md`: added new reading order, index rows, and minimum required files before training, claims, and MD interpretation.
- `18_VERIFICATION_PIPELINE.md`: added pre-training biology, benchmark, red-team, null-baseline, human-review, interpretability, pre-MD, hallucination, uncertainty, and publication gates.
- `19_STOP_CONDITIONS.md`: added stop conditions for scope drift, missing human gates, failed biological data sanity, red-team blockers, null-baseline failures, benchmark-quality gaps, hallucination, missing uncertainty, missing interpretability, and missing pre-MD reality check.
- `20_PHASE2_BUILD_CHECKLIST.md`: expanded build order to include all new gates.
- `21_READINESS_GATE.md`: added readiness categories for scope, uncertainty, benchmark, lifecycle, human review, biological sanity, red-team, null baselines, interpretability, pre-MD, hallucination, and publication.
- `23_FINAL_PROJECT_AUDIT_TEMPLATE.md`: added final audit sections for the new gates.

## Why This Matters

The original governance layer prevented leakage, stale artifacts, overclaims, bad MD interpretation, and agent-invented science. The expansion adds protections against earlier and subtler failure modes:

- training on biologically nonsensical labels,
- automation-driven scientific drift,
- fake rigor from a noisy benchmark,
- GNN claims that are actually solvent accessibility, conservation, B-factor, or geometry,
- pressure to force positive outcomes,
- black-box PCNA claims,
- MD without a specific hypothesis,
- AI-generated biological hallucinations,
- confidence without characterized uncertainty.

## Context Available Now

- Local `crawls/` source/context corpus.
- SARC proposal: `BORRA_#1_SARC.pdf`.
- Governance docs under `docs/scientific_governance/`.
- Report from initial governance creation: `reports/research_os/scientific_governance_docs_report.md`.
- Crawl leads for CryptoBench, BioLiP/BioLiP2, scPDB, ASD, PocketMiner, fpocket, P2Rank, DeepAllo, GROMACS, CHARMM36m, PCNA PDB structures, P12004, AOH1996/8GLA, PIP-box/APIM, and BioGRID.

## Context Still Needed Before Implementation

- Local checkout or selected branch for the actual Phase 2 source implementation.
- Decision on whether to port ResearchOS code from GitHub `main` or implement lightweight Phase 2 gates fresh.
- Downloaded CryptoBench file inventory, license, and label schema.
- Download/access decision for BioLiP/BioLiP2/scPDB/PDBbind auxiliary data.
- Sequence clustering tool and identity threshold.
- Structural similarity audit method.
- PCNA structure list for final holdout and positive controls.
- Human reviewer name or role for mandatory gates.
- Whether ESM/pLM features are deferred or included in governed graph MVP.

## Recommended Next Step

Open a new chat with `docs/scientific_governance/37_PHASE2_IMPLEMENTATION_PLAN.md` as the primary handoff. The first implementation task should be governance scaffolding and registries only: source registry, assumption registry, uncertainty register, benchmark limitations template, data lifecycle registry, human review log, and readiness gate. Do not train.
