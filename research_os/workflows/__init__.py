"""Workflow runners: pre-built orchestration recipes.

Each workflow:

1. instantiates an `Orchestrator`,
2. constructs an `OrchestrationPlan` (either via routing or via a fixed
   intent set tailored to the workflow),
3. runs the plan, and
4. writes a markdown + JSON report under `reports/research_os/<workflow>/<ts>/`.
"""
from research_os.workflows.runner import run_workflow
from research_os.workflows.full_audit import run_full_audit
from research_os.workflows.training_eval import run_training_eval
from research_os.workflows.md_validation import run_md_validation
from research_os.workflows.claim_audit import run_claim_audit
from research_os.workflows.submission_readiness import run_submission_readiness
from research_os.workflows.metric_verification import run_metric_verification

WORKFLOWS = {
    "full_audit": run_full_audit,
    "training_eval": run_training_eval,
    "md_validation": run_md_validation,
    "claim_audit": run_claim_audit,
    "metric_verification": run_metric_verification,
    "submission_readiness": run_submission_readiness,
}

__all__ = [
    "WORKFLOWS",
    "run_claim_audit",
    "run_full_audit",
    "run_md_validation",
    "run_metric_verification",
    "run_submission_readiness",
    "run_training_eval",
    "run_workflow",
]
