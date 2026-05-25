# Workflow Registry

Last updated: 2026-05-25T00:00:00Z
Updated by: research_os.bootstrap
Status: current

The 6 prebuilt workflow recipes. Each workflow constructs an `OrchestrationPlan` (either via the router or via a fixed intent set), runs the agents in order through the gate-enforcing orchestrator, and writes a markdown + JSON + transcript bundle under `reports/research_os/<workflow>/<timestamp>/`.

Workflow definitions live in `research_os/workflows/<name>.py` and are registered in `research_os/workflows/__init__.py:WORKFLOWS`.

---

## full_audit

- entry: `research_os.workflows.full_audit:run_full_audit`
- CLI: `python -m research_os audit`
- MCP: `run_workflow("full_audit")`
- agents (typical): `context_source_truth, research_design, dataset_integrity, leakage_split, preprocessing_auditor, scientific_code_review, testing_environment, model_training, metrics_statistics, validation_skeptic, biological_realism, paper_claim, visual_evidence, contradiction_hunter, provenance_artifacts, reviewer_collaboration, document_knowledge_ingestion`
- required gates: research_design, dataset, leakage, preprocessing, code, evaluation, validation, claim, figure
- outputs: full audit report, all gate statuses, applied memory updates
- risk_level: high
- when_to_use: comprehensive audit before any release; user asks "audit the repo" / "run the full audit"

---

## training_eval

- entry: `research_os.workflows.training_eval:run_training_eval`
- CLI: `python -m research_os training-eval`
- MCP: `run_workflow("training_eval")`
- agents: `context_source_truth, leakage_split, dataset_integrity, preprocessing_auditor, scientific_code_review, model_training, metrics_statistics, provenance_artifacts, contradiction_hunter`
- required gates: dataset, leakage, preprocessing, code, evaluation
- outputs: training audit, verified metrics, experiment_registry entry
- risk_level: high
- when_to_use: before accepting a checkpoint; after retraining; verifying metrics

---

## md_validation

- entry: `research_os.workflows.md_validation:run_md_validation`
- CLI: `python -m research_os validate-md [--report DIR]`
- MCP: `run_workflow("md_validation", {"md_report_dir": "..."})`
- agents: `context_source_truth, validation_skeptic, biological_realism, metrics_statistics, provenance_artifacts, contradiction_hunter`
- required gates: validation
- outputs: MD evidence classification (supports/partial/inconclusive/weakens/contradicts)
- risk_level: critical
- when_to_use: interpreting MD trajectories; deciding whether MD supports a pocket-opening claim

---

## claim_audit

- entry: `research_os.workflows.claim_audit:run_claim_audit`
- CLI: `python -m research_os claim-audit [--paper FILE]`
- MCP: `run_workflow("claim_audit", {"paper_path": "..."})`
- agents: `context_source_truth, paper_claim, metrics_statistics, validation_skeptic, biological_realism, provenance_artifacts, contradiction_hunter, reviewer_collaboration`
- required gates: claim, validation
- outputs: claim audit report; safe-wording replacements
- risk_level: critical
- when_to_use: reviewing CURRENT_CLAIMS.md or a paper draft before publication

---

## metric_verification

- entry: `research_os.workflows.metric_verification:run_metric_verification`
- CLI: `python -m research_os verify-metrics [--metrics FILE]`
- MCP: `run_workflow("metric_verification", {"metrics_path": "..."})`
- agents: `context_source_truth, metrics_statistics, leakage_split, provenance_artifacts, contradiction_hunter`
- required gates: evaluation, leakage
- outputs: verified metrics JSON with confidence intervals
- risk_level: high
- when_to_use: numerical verification of headline metrics; confidence interval recomputation

---

## submission_readiness

- entry: `research_os.workflows.submission_readiness:run_submission_readiness`
- CLI: `python -m research_os readiness [--paper FILE]`
- MCP: `run_workflow("submission_readiness", {"paper_path": "..."})`
- agents: `context_source_truth, provenance_artifacts, leakage_split, preprocessing_auditor, metrics_statistics, biological_realism, validation_skeptic, paper_claim, visual_evidence, reviewer_collaboration, testing_environment, contradiction_hunter`
- required gates: ALL (research_design, dataset, leakage, preprocessing, code, evaluation, validation, claim, figure, submission)
- outputs: readiness matrix; PI signoff prompt
- risk_level: critical
- when_to_use: before submitting / preprinting / publishing
- always: `requires_human_approval: true`

---

## Outputs produced by every workflow

```
reports/research_os/<workflow>/<timestamp>/
├── plan.json         # OrchestrationPlan (input)
├── result.json       # WorkflowResult (full output)
├── report.md         # human-readable report
├── summary.md        # short executive summary
└── transcript.jsonl  # event-by-event log (new in this upgrade)
```

The dashboard reads from this layout. The MCP `get_report(path_or_id)` tool can retrieve any of these files.
