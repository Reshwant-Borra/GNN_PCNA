# Phase 2 Build Checklist

## Purpose

Step-by-step build order for Phase 2.

## Hard Rules

- Checklist order is mandatory for scientific work.
- A checkbox is complete only when its artifact exists.
- Exploratory work must be labeled exploratory if gates are not complete.

## Checklist

1. [ ] Freeze source of truth. Artifact: `reports/phase2/source_of_truth_audit.md`
2. [ ] Freeze project scope. Artifact: `reports/phase2/project_scope_audit.md`
3. [ ] Read governance docs. Artifact: signed/dated checklist.
4. [ ] Create assumption registry. Artifact: assumption audit.
5. [ ] Create scientific uncertainty register. Artifact: `reports/phase2/scientific_uncertainty_register.md`
6. [ ] Create source registry from `crawls/`. Artifact: source registry and source audit.
7. [ ] Create benchmark limitations review. Artifact: `reports/phase2/benchmark_limitations.md`
8. [ ] Create dataset registry. Artifact: `docs/scientific_governance/DATASET_REGISTRY.md`
9. [ ] Create data lifecycle registry. Artifact: `data/registries/data_lifecycle_registry.json`
10. [ ] Freeze split protocol with human review. Artifact: `data/splits/phase2_split_<hash>.json` plus human decision.
11. [ ] Define and freeze labeling rules with human review. Artifact: `data/labels/phase2_labels_<hash>.json` plus human decision.
12. [ ] Run biological data sanity review. Artifact: `reports/phase2/biological_data_sanity_review.md`
13. [ ] Build preprocessing pipeline. Artifact: preprocessing tests and manifest.
14. [ ] Generate graphs from frozen splits. Artifact: `data/graphs/phase2_graph_manifest_<hash>.json`
15. [ ] Verify graph/label alignment. Artifact: `reports/phase2/graph_audit.md`
16. [ ] Run red-team pretraining audit. Artifact: `reports/phase2/red_team_audit.md`
17. [ ] Run null-hypothesis baselines or freeze the null-baseline plan. Artifact: `reports/phase2/null_hypothesis_baselines.md`
18. [ ] Implement architecture constraints. Artifact: `reports/phase2/architecture_audit.md`
19. [ ] Obtain human first-training approval. Artifact: `reports/phase2/human_review_log.md`
20. [ ] Train only after gates pass. Artifact: training manifest.
21. [ ] Evaluate validation only. Artifact: validation report.
22. [ ] Freeze model. Artifact: checkpoint manifest.
23. [ ] Test once. Artifact: test-used-once log and evaluation report.
24. [ ] Run tool baselines. Artifact: `reports/phase2/baseline_audit.md`
25. [ ] Run PCNA positive control. Artifact: AOH1996/8GLA status report.
26. [ ] Run biological realism audit. Artifact: `reports/phase2/biological_realism_audit.md`
27. [ ] Run PCNA-specific audit. Artifact: `reports/phase2/pcna_specific_audit.md`
28. [ ] Run interpretability-before-claims audit. Artifact: `reports/phase2/interpretability_before_claims.md`
29. [ ] Obtain human first-PCNA-prediction interpretation approval.
30. [ ] Run pre-MD reality check. Artifact: `reports/phase2/md/<system_id>/pre_md_reality_check.md`
31. [ ] Run MD validation carefully. Artifact: MD pre-registration and interpretation audit.
32. [ ] Obtain human first-MD-interpretation approval.
33. [ ] Run AI hallucination audit. Artifact: `reports/phase2/ai_hallucination_audit.md`
34. [ ] Run negative-result success review. Artifact: `reports/phase2/negative_result_success_review.md`
35. [ ] Run claim audit with human review. Artifact: `reports/phase2/claim_audit.md`
36. [ ] Run publication readiness. Artifact: `reports/phase2/publication_readiness.md`
37. [ ] Produce final readiness report. Artifact: completed [23_FINAL_PROJECT_AUDIT_TEMPLATE.md](23_FINAL_PROJECT_AUDIT_TEMPLATE.md)

## Forbidden Actions

- Skipping ahead to training, MD, figures, or claims.
- Marking an item done without the artifact.

## Required Checks

- Artifact link present for each completed item.
- Readiness gate updated after each major stage.
- Stop conditions reviewed before moving downstream.

## Examples Of Failure

- Running baselines after final claims are drafted.
- Creating graphs before split hash exists.
- Running MD before biological realism audit.
- Starting training before biological data sanity review or human label freeze.

## Prevention

Treat this checklist as the single build queue. Do not start a later item until all prerequisite artifacts are present.

## Compliance Artifact

The completed checklist plus linked artifacts.

## If A Checklist Item Fails

Invoke [19_STOP_CONDITIONS.md](19_STOP_CONDITIONS.md) and do not proceed to downstream items.
