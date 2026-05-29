# Scientific Governance README

## Purpose

This folder is the scientific law for GNN-PCNA Phase 2. It exists because Version 1 showed that working code, impressive AUROC, a positive-looking PCNA control, or an agent saying "done" can still leave the project scientifically unsafe.

Phase 2 must build a residue-level GNN workflow for PCNA cryptic, allosteric, and candidate pocket prediction without dataset leakage, bad splits, stale artifacts, overclaims, hallucinated biology, or MD overinterpretation.

## V1 Risk Summary

The `project-version-1` GitHub branch and SARC proposal show the correct project direction but also the risks Phase 2 must control:

- 8GLA/AOH1996 was useful as a positive-control gate, but it was not independent validation if used for fine-tuning or threshold selection.
- V1 labels included C-alpha ligand-proximity labels, not necessarily curated cryptic-pocket labels.
- PCNA asymmetric-unit and biological-assembly issues affected interpretation of trimer biology.
- Chain identity, residue numbering, and non-PCNA chains created opportunities for shortcut features and wrong annotations.
- Val/test and combined held-out reporting could be overread without frozen test-use rules and confidence intervals.
- ANM or MD-looking results could be mistaken for proof of cryptic pocket opening, binding, druggability, or therapeutic relevance.
- Code could run while implementing the wrong scientific method.

## Phase 2 Rule

No implementation work should begin until:

- project scope is accepted under [24_PROJECT_SCOPE.md](24_PROJECT_SCOPE.md)
- assumptions are documented in [02_ASSUMPTION_REGISTRY.md](02_ASSUMPTION_REGISTRY.md)
- uncertainty is documented in [35_SCIENTIFIC_UNCERTAINTY_REGISTER.md](35_SCIENTIFIC_UNCERTAINTY_REGISTER.md)
- dataset rules are defined in [04_DATASET_CONSTRAINTS.md](04_DATASET_CONSTRAINTS.md)
- benchmark limitations are documented in [29_BENCHMARK_LIMITATIONS.md](29_BENCHMARK_LIMITATIONS.md)
- split protocol is frozen under [05_SPLIT_PROTOCOL.md](05_SPLIT_PROTOCOL.md)
- biological data sanity review exists under [25_BIOLOGICAL_DATA_SANITY_REVIEW.md](25_BIOLOGICAL_DATA_SANITY_REVIEW.md)
- human review gates are accepted under [26_HUMAN_REVIEW_GATES.md](26_HUMAN_REVIEW_GATES.md)
- claim policy is accepted under [14_CLAIM_POLICY.md](14_CLAIM_POLICY.md)
- MD interpretation policy is accepted under [13_MD_VALIDATION_RULES.md](13_MD_VALIDATION_RULES.md)
- verification pipeline exists under [18_VERIFICATION_PIPELINE.md](18_VERIFICATION_PIPELINE.md)

## Hard Rules

- This folder overrides informal notes, prompts, and generated summaries.
- A task that conflicts with these docs must stop unless the governance docs are explicitly updated and reviewed.
- Missing governance evidence means the result cannot support Phase 2 science.

## Required Reading Order

1. [00_README.md](00_README.md)
2. [01_SOURCE_OF_TRUTH.md](01_SOURCE_OF_TRUTH.md)
3. [02_ASSUMPTION_REGISTRY.md](02_ASSUMPTION_REGISTRY.md)
4. [03_FAILURE_MODE_CATALOG.md](03_FAILURE_MODE_CATALOG.md)
5. [04_DATASET_CONSTRAINTS.md](04_DATASET_CONSTRAINTS.md)
6. [05_SPLIT_PROTOCOL.md](05_SPLIT_PROTOCOL.md)
7. [06_LABELING_RULES.md](06_LABELING_RULES.md)
8. [07_PREPROCESSING_AND_GRAPH_RULES.md](07_PREPROCESSING_AND_GRAPH_RULES.md)
9. [08_MODEL_ARCHITECTURE_CONSTRAINTS.md](08_MODEL_ARCHITECTURE_CONSTRAINTS.md)
10. [09_EVALUATION_PROTOCOL.md](09_EVALUATION_PROTOCOL.md)
11. [10_BASELINE_REQUIREMENTS.md](10_BASELINE_REQUIREMENTS.md)
12. [11_BIOLOGICAL_REALISM_RULES.md](11_BIOLOGICAL_REALISM_RULES.md)
13. [12_PCNA_SPECIFIC_CHECKS.md](12_PCNA_SPECIFIC_CHECKS.md)
14. [13_MD_VALIDATION_RULES.md](13_MD_VALIDATION_RULES.md)
15. [14_CLAIM_POLICY.md](14_CLAIM_POLICY.md)
16. [15_PROVENANCE_AND_REPRODUCIBILITY.md](15_PROVENANCE_AND_REPRODUCIBILITY.md)
17. [16_CODING_AGENT_RULES.md](16_CODING_AGENT_RULES.md)
18. [17_RESEARCHOS_AGENT_RULES.md](17_RESEARCHOS_AGENT_RULES.md)
19. [18_VERIFICATION_PIPELINE.md](18_VERIFICATION_PIPELINE.md)
20. [19_STOP_CONDITIONS.md](19_STOP_CONDITIONS.md)
21. [20_PHASE2_BUILD_CHECKLIST.md](20_PHASE2_BUILD_CHECKLIST.md)
22. [21_READINESS_GATE.md](21_READINESS_GATE.md)
23. [22_UNEXPECTED_RESULTS_POLICY.md](22_UNEXPECTED_RESULTS_POLICY.md)
24. [23_FINAL_PROJECT_AUDIT_TEMPLATE.md](23_FINAL_PROJECT_AUDIT_TEMPLATE.md)
25. [24_PROJECT_SCOPE.md](24_PROJECT_SCOPE.md)
26. [25_BIOLOGICAL_DATA_SANITY_REVIEW.md](25_BIOLOGICAL_DATA_SANITY_REVIEW.md)
27. [26_HUMAN_REVIEW_GATES.md](26_HUMAN_REVIEW_GATES.md)
28. [27_RED_TEAM_AUDIT.md](27_RED_TEAM_AUDIT.md)
29. [28_NULL_HYPOTHESIS_BASELINES.md](28_NULL_HYPOTHESIS_BASELINES.md)
30. [29_BENCHMARK_LIMITATIONS.md](29_BENCHMARK_LIMITATIONS.md)
31. [30_NEGATIVE_RESULT_SUCCESS_CRITERIA.md](30_NEGATIVE_RESULT_SUCCESS_CRITERIA.md)
32. [31_DATA_LIFECYCLE_TRACKING.md](31_DATA_LIFECYCLE_TRACKING.md)
33. [32_INTERPRETABILITY_BEFORE_CLAIMS.md](32_INTERPRETABILITY_BEFORE_CLAIMS.md)
34. [33_PRE_MD_REALITY_CHECK.md](33_PRE_MD_REALITY_CHECK.md)
35. [34_AI_HALLUCINATION_DETECTION.md](34_AI_HALLUCINATION_DETECTION.md)
36. [35_SCIENTIFIC_UNCERTAINTY_REGISTER.md](35_SCIENTIFIC_UNCERTAINTY_REGISTER.md)
37. [36_PUBLICATION_READINESS.md](36_PUBLICATION_READINESS.md)
38. [37_PHASE2_IMPLEMENTATION_PLAN.md](37_PHASE2_IMPLEMENTATION_PLAN.md)

## Index

| File | Governs |
|---|---|
| [01_SOURCE_OF_TRUTH.md](01_SOURCE_OF_TRUTH.md) | Canonical repo, dataset, splits, context pack, results, stale artifact controls |
| [02_ASSUMPTION_REGISTRY.md](02_ASSUMPTION_REGISTRY.md) | Required assumption template and examples |
| [03_FAILURE_MODE_CATALOG.md](03_FAILURE_MODE_CATALOG.md) | Known ways Phase 2 can become scientifically invalid |
| [04_DATASET_CONSTRAINTS.md](04_DATASET_CONSTRAINTS.md) | Dataset registry, inclusion, chain, ligand, normalization rules |
| [05_SPLIT_PROTOCOL.md](05_SPLIT_PROTOCOL.md) | Leakage-free train/val/test design |
| [06_LABELING_RULES.md](06_LABELING_RULES.md) | Residue label definitions and audits |
| [07_PREPROCESSING_AND_GRAPH_RULES.md](07_PREPROCESSING_AND_GRAPH_RULES.md) | Structure preprocessing and graph construction |
| [08_MODEL_ARCHITECTURE_CONSTRAINTS.md](08_MODEL_ARCHITECTURE_CONSTRAINTS.md) | Batch safety, logits, shortcut controls, ablations |
| [09_EVALUATION_PROTOCOL.md](09_EVALUATION_PROTOCOL.md) | Metrics, seeds, CIs, test-use rules |
| [10_BASELINE_REQUIREMENTS.md](10_BASELINE_REQUIREMENTS.md) | PocketMiner, fpocket, P2Rank, simple and ablation baselines |
| [11_BIOLOGICAL_REALISM_RULES.md](11_BIOLOGICAL_REALISM_RULES.md) | Structural plausibility and literature consistency |
| [12_PCNA_SPECIFIC_CHECKS.md](12_PCNA_SPECIFIC_CHECKS.md) | PCNA trimer, PIP-box, APIM, AOH1996, ATX-101 checks |
| [13_MD_VALIDATION_RULES.md](13_MD_VALIDATION_RULES.md) | MD pre-registration and cautious interpretation |
| [14_CLAIM_POLICY.md](14_CLAIM_POLICY.md) | Allowed and forbidden wording |
| [15_PROVENANCE_AND_REPRODUCIBILITY.md](15_PROVENANCE_AND_REPRODUCIBILITY.md) | Artifact manifest and hashes |
| [16_CODING_AGENT_RULES.md](16_CODING_AGENT_RULES.md) | Codex, Claude Code, and coding-agent limits |
| [17_RESEARCHOS_AGENT_RULES.md](17_RESEARCHOS_AGENT_RULES.md) | ResearchOS evidence, critique, and replanning flow |
| [18_VERIFICATION_PIPELINE.md](18_VERIFICATION_PIPELINE.md) | End-to-end gates |
| [19_STOP_CONDITIONS.md](19_STOP_CONDITIONS.md) | Mandatory pause conditions |
| [20_PHASE2_BUILD_CHECKLIST.md](20_PHASE2_BUILD_CHECKLIST.md) | Build sequence and artifact links |
| [21_READINESS_GATE.md](21_READINESS_GATE.md) | PASS/WARNING/FAIL scoring |
| [22_UNEXPECTED_RESULTS_POLICY.md](22_UNEXPECTED_RESULTS_POLICY.md) | How to treat surprising evidence |
| [23_FINAL_PROJECT_AUDIT_TEMPLATE.md](23_FINAL_PROJECT_AUDIT_TEMPLATE.md) | Final audit format and decisions |
| [24_PROJECT_SCOPE.md](24_PROJECT_SCOPE.md) | Scientific scope boundaries and out-of-scope claims |
| [25_BIOLOGICAL_DATA_SANITY_REVIEW.md](25_BIOLOGICAL_DATA_SANITY_REVIEW.md) | Pre-training biological plausibility review |
| [26_HUMAN_REVIEW_GATES.md](26_HUMAN_REVIEW_GATES.md) | Mandatory human signoff gates |
| [27_RED_TEAM_AUDIT.md](27_RED_TEAM_AUDIT.md) | Adversarial scientific audit |
| [28_NULL_HYPOTHESIS_BASELINES.md](28_NULL_HYPOTHESIS_BASELINES.md) | Trivial biological heuristic baselines |
| [29_BENCHMARK_LIMITATIONS.md](29_BENCHMARK_LIMITATIONS.md) | CryptoBench and benchmark-quality limitations |
| [30_NEGATIVE_RESULT_SUCCESS_CRITERIA.md](30_NEGATIVE_RESULT_SUCCESS_CRITERIA.md) | Successful negative and inconclusive outcomes |
| [31_DATA_LIFECYCLE_TRACKING.md](31_DATA_LIFECYCLE_TRACKING.md) | Data inclusion, exclusion, quarantine, and removal reasons |
| [32_INTERPRETABILITY_BEFORE_CLAIMS.md](32_INTERPRETABILITY_BEFORE_CLAIMS.md) | Attribution and ablation requirements before PCNA claims |
| [33_PRE_MD_REALITY_CHECK.md](33_PRE_MD_REALITY_CHECK.md) | Hypothesis-first MD planning |
| [34_AI_HALLUCINATION_DETECTION.md](34_AI_HALLUCINATION_DETECTION.md) | Source or uncertainty requirements for AI-generated science |
| [35_SCIENTIFIC_UNCERTAINTY_REGISTER.md](35_SCIENTIFIC_UNCERTAINTY_REGISTER.md) | First-class uncertainty tracking |
| [36_PUBLICATION_READINESS.md](36_PUBLICATION_READINESS.md) | Final external-facing readiness |
| [37_PHASE2_IMPLEMENTATION_PLAN.md](37_PHASE2_IMPLEMENTATION_PLAN.md) | Handoff plan and remaining context needs |

## How Coding Agents Must Use This

Every coding prompt must include: "Implement only documented science. If a scientific assumption is missing, stop and document the assumption instead of inventing it."

Coding agents must read [16_CODING_AGENT_RULES.md](16_CODING_AGENT_RULES.md), then check the specific governing file for the component they are editing. They may implement rules, validators, tests, manifests, and reports. They may not invent PCNA biology, relabel data, alter split rules, weaken gates, tune on test data, or reinterpret MD.

## How ResearchOS Must Use This

ResearchOS agents must use [17_RESEARCHOS_AGENT_RULES.md](17_RESEARCHOS_AGENT_RULES.md) and must separate source evidence from inference. Source count is not evidence quality. A ResearchOS pass is not final authority unless the critic, planner, biology, evaluation, and provenance checks converge.

## Minimum Required Files Before Training

- [ ] Project scope audit.
- [ ] Assumption registry with all active assumptions and owners.
- [ ] Scientific uncertainty register.
- [ ] Dataset registry with source, chains, labels, splits, hashes, and leakage risks.
- [ ] Benchmark limitations report.
- [ ] Data lifecycle registry.
- [ ] Frozen split assignment file and split hash.
- [ ] Human split-freeze and label-freeze review records.
- [ ] Label audit report.
- [ ] Biological data sanity review.
- [ ] Graph audit report.
- [ ] Red-team pretraining audit.
- [ ] Null-hypothesis baseline plan or completed null-baseline report.
- [ ] Architecture audit and batch-isolation audit.
- [ ] Readiness gate with dataset, split, label, graph, and training readiness marked PASS.

## Minimum Required Files Before Claims

- [ ] Test-once evaluation report with macro/micro metrics, CIs, seed variance, calibration, and top-k recovery.
- [ ] Baseline comparison on the same split and label definition.
- [ ] Null-hypothesis baseline comparison.
- [ ] Biological realism audit.
- [ ] PCNA-specific audit.
- [ ] Interpretability-before-claims audit.
- [ ] Scientific uncertainty register updated for the claim.
- [ ] AI hallucination audit for generated scientific text.
- [ ] Human claim review record.
- [ ] Claim audit with allowed wording.
- [ ] Reproducibility manifest for every artifact supporting the claim.

## Minimum Required Files Before MD Interpretation

- [ ] Pre-MD reality check from [33_PRE_MD_REALITY_CHECK.md](33_PRE_MD_REALITY_CHECK.md).
- [ ] MD pre-registration from [13_MD_VALIDATION_RULES.md](13_MD_VALIDATION_RULES.md).
- [ ] MD provenance manifest.
- [ ] Trajectory quality audit.
- [ ] Apo and ligand-bound setup comparison.
- [ ] Explicit interpretation table covering positive, negative, unstable, and unexpected outcomes.
- [ ] Scientific uncertainty register updated for MD setup and interpretation.
- [ ] Human MD interpretation review record.
- [ ] Claim audit confirming MD is supportive evidence only.

## Forbidden Actions

- Starting implementation before the minimum required governance files exist.
- Treating V1 artifacts, SARC prose, or ResearchOS summaries as proof.
- Claiming training, evaluation, MD, or writing is "done" without compliance artifacts.

## Required Checks

- Confirm all files in the index exist.
- Confirm the relevant minimum checklist is complete before training, claims, or MD interpretation.
- Confirm any coding or ResearchOS agent was given the required instruction.

## Examples Of Failure

- A model is trained before `DATASET_REGISTRY.md` or a frozen split exists.
- A report cites SARC project intent as evidence that a predicted PCNA site is therapeutic.
- A coding agent starts from a stale graph cache because it exists locally.

## Prevention

Use [20_PHASE2_BUILD_CHECKLIST.md](20_PHASE2_BUILD_CHECKLIST.md) as the work order and [21_READINESS_GATE.md](21_READINESS_GATE.md) as the permission gate.

## Compliance Artifact

The proof that this README was obeyed is a completed [20_PHASE2_BUILD_CHECKLIST.md](20_PHASE2_BUILD_CHECKLIST.md), a PASS/WARNING/FAIL [21_READINESS_GATE.md](21_READINESS_GATE.md), and a final [23_FINAL_PROJECT_AUDIT_TEMPLATE.md](23_FINAL_PROJECT_AUDIT_TEMPLATE.md) instance.

## If This Fails

If any contributor starts training, claims, or MD interpretation without the required governance artifacts, the result is invalid for Phase 2. Freeze the artifact, label it `NONCOMPLIANT_DO_NOT_USE`, and restart from the missing gate.
