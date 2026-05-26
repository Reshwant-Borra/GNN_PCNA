"""Tests for critics + CoverageEstimator."""
from __future__ import annotations

import pytest

from research_os.autonomous.coverage import CoverageEstimator
from research_os.autonomous.critique import (
    confidence_critic,
    make_coverage_critic,
    simple_critic,
)
from research_os.autonomous.schemas import (
    CoverageCategory,
    Plan,
    Step,
    StepResult,
    StepStatus,
)


# ---------------------------------------------------------------------------
# CoverageEstimator
# ---------------------------------------------------------------------------

def _cats():
    return [
        CoverageCategory(name="pcna", keywords=["pcna", "AOH1996"], min_items=2),
        CoverageCategory(name="md", keywords=["MD", "molecular dynamics", "RMSF"], min_items=1),
        CoverageCategory(name="gnn", keywords=["graph neural", "GNN"], min_items=1),
    ]


def test_coverage_estimator_score_and_gaps():
    items = [
        {"title": "PCNA pocket dynamics", "abstract": "MD analysis"},
        {"title": "AOH1996 binding study", "abstract": ""},
        # No GNN items.
    ]
    est = CoverageEstimator(_cats())
    result = est.evaluate(items)
    # pcna: 2 of 2 needed → 1.0. md: 1 of 1 → 1.0. gnn: 0 of 1 → 0.0.
    assert result.per_category_counts["pcna"] == 2
    assert result.per_category_counts["md"] == 1
    assert result.per_category_counts["gnn"] == 0
    assert "gnn" in result.gaps
    assert result.score < 1.0
    assert any("graph neural" in q for q in result.suggested_queries)


def test_coverage_estimator_full_coverage():
    items = [
        {"title": "PCNA + GNN review", "abstract": "with MD"},
        {"title": "AOH1996 mechanism via molecular dynamics"},
    ]
    est = CoverageEstimator(_cats())
    result = est.evaluate(items)
    # All categories now have at least min_items.
    assert result.score == 1.0
    assert not result.gaps


def test_coverage_estimator_requires_at_least_one_category():
    with pytest.raises(ValueError):
        CoverageEstimator([])


# ---------------------------------------------------------------------------
# simple_critic
# ---------------------------------------------------------------------------

def test_simple_critic_no_findings_when_all_ok():
    plan = Plan(steps=[Step(description="x")])
    results = [StepResult(step_id="s-1", status=StepStatus.SUCCEEDED, confidence=0.9)]
    out = simple_critic(plan, results, {})
    assert out.severity == "info"
    assert not out.spawned_steps
    assert not out.requires_replan


def test_simple_critic_spawns_retry_on_failure():
    s1 = Step(description="fetch", kind="tool_call", tool_name="memory_list", tool_input={})
    plan = Plan(steps=[s1])
    results = [StepResult(step_id=s1.step_id, status=StepStatus.FAILED, error="bad")]
    out = simple_critic(plan, results, {})
    assert out.severity in ("medium", "high")
    assert out.requires_replan is True
    assert len(out.spawned_steps) == 1
    assert out.spawned_steps[0].rationale.startswith("Retry suggested")


def test_simple_critic_escalates_when_no_successes():
    s1 = Step(description="x")
    plan = Plan(steps=[s1])
    results = [StepResult(step_id=s1.step_id, status=StepStatus.FAILED, error="x")]
    out = simple_critic(plan, results, {})
    assert out.severity == "high"


# ---------------------------------------------------------------------------
# coverage_critic
# ---------------------------------------------------------------------------

def test_coverage_critic_spawns_targeted_followups():
    est = CoverageEstimator(_cats())
    critic = make_coverage_critic(
        estimator=est,
        items_key="collected_items",
        min_score=0.99,
        spawn_tool="web_search",
        spawn_input_template={"source": "pubmed", "limit": 5},
    )
    plan = Plan()
    ctx = {"collected_items": [{"title": "GNN review"}]}  # missing pcna + md
    out = critic(plan, [], ctx)
    assert out.requires_replan is True
    # One spawned step per gap, each carrying the suggested query as input.
    queries = [s.tool_input.get("query") for s in out.spawned_steps]
    assert all(s.tool_name == "web_search" for s in out.spawned_steps)
    # Source template propagated.
    assert all(s.tool_input.get("source") == "pubmed" for s in out.spawned_steps)
    assert all(q for q in queries)
    # The coverage result was written back to ctx_state.
    assert "coverage_result" in ctx
    assert ctx["coverage_result"]["total_items"] == 1


def test_coverage_critic_missing_items_key_returns_low_severity():
    est = CoverageEstimator(_cats())
    critic = make_coverage_critic(estimator=est, items_key="missing_key")
    out = critic(Plan(), [], {})
    assert out.severity == "low"
    assert "missing key" in out.summary or "missing key" in (out.issues[0] if out.issues else "")


# ---------------------------------------------------------------------------
# confidence_critic
# ---------------------------------------------------------------------------

def test_confidence_critic_ok_when_above_threshold():
    crit = confidence_critic(min_average=0.5)
    plan = Plan()
    results = [
        StepResult(step_id="s-1", status=StepStatus.SUCCEEDED, confidence=0.8),
        StepResult(step_id="s-2", status=StepStatus.SUCCEEDED, confidence=0.6),
    ]
    out = crit(plan, results, {})
    assert out.severity == "info"


def test_confidence_critic_flags_low_average():
    crit = confidence_critic(min_average=0.7)
    plan = Plan()
    results = [
        StepResult(step_id="s-1", status=StepStatus.SUCCEEDED, confidence=0.2),
        StepResult(step_id="s-2", status=StepStatus.SUCCEEDED, confidence=0.3),
    ]
    out = crit(plan, results, {})
    assert out.severity == "medium"
    assert "below" in out.summary


def test_confidence_critic_no_successes_is_high():
    crit = confidence_critic()
    plan = Plan()
    results = [StepResult(step_id="s-1", status=StepStatus.FAILED, error="x")]
    out = crit(plan, results, {})
    assert out.severity == "high"
