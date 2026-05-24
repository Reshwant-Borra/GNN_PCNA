"""Router prompt classification + gate + human escalation tests."""
from __future__ import annotations

import pytest

from research_os.routing import Router


@pytest.fixture
def router() -> Router:
    return Router()


def _route(router, msg):
    return router.route(msg)


@pytest.mark.parametrize(
    "msg,expected_intent",
    [
        ("Can we say MD validated the cryptic pocket?", "claim_or_paper"),
        ("Run training on the latest split.", "training"),
        ("What is the latest AUROC?", "metric_verification"),
        ("Write the results section.", "claim_or_paper"),
        ("Make a pocket volume figure.", "figure_generation"),
        ("Check if our split leaks chains.", "split_or_leakage"),
        ("Review the metric script.", "code_review"),
        ("Run 100 ns MD on cloud.", "md_or_validation"),
        ("What should my friend pull?", "collaboration_sync"),
        ("Find hidden contradictions before submission.", "submission_readiness"),
    ],
)
def test_router_intent_inclusion(router, msg, expected_intent):
    plan = _route(router, msg)
    assert expected_intent in plan.intents, plan.intents


def test_context_agent_is_always_first(router):
    plan = _route(router, "What is the latest AUROC?")
    assert plan.selected_agents[0] == "context_source_truth"


def test_md_validation_gate_required_for_md_claim(router):
    plan = _route(router, "Can we say MD validated the pocket?")
    assert "validation" in plan.required_gates


def test_submission_requires_human(router):
    plan = _route(router, "Final paper submission to journal.")
    assert plan.human_review_required


def test_expensive_compute_requires_human(router):
    plan = _route(router, "Run 100 ns MD on cloud.")
    assert plan.human_review_required


def test_critical_risk_for_submission(router):
    plan = _route(router, "Submit the manuscript.")
    assert plan.risk_level == "critical"


def test_contradiction_hunter_runs_at_high_risk(router):
    plan = _route(router, "Run training on the new split.")
    assert "contradiction_hunter" in plan.selected_agents


def test_claim_or_paper_routes_to_validation_and_metrics(router):
    plan = _route(router, "Write the results section.")
    assert "validation_skeptic" in plan.selected_agents
    assert "metrics_statistics" in plan.selected_agents


def test_empty_message_routes_general(router):
    plan = _route(router, "")
    assert "general" in plan.intents
