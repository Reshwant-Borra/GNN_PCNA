"""Schema-shape tests for the autonomous-framework dataclasses.

These check round-tripping + the small bits of behavior baked into the
schemas (Budget exhaustion, SuccessCriterion evaluation, Goal.criteria).
"""
from __future__ import annotations

import time

import pytest

from research_os.autonomous.schemas import (
    Budget,
    CoverageCategory,
    Goal,
    Plan,
    Step,
    StepResult,
    StepStatus,
    SuccessCriterion,
)


def test_budget_dimensions_independent():
    b = Budget(max_iterations=3, max_tool_calls=10, max_failures=2, max_seconds=None)
    started = time.time()
    assert b.is_exhausted(iterations=0, tool_calls=0, failures=0, started_at=started) is None
    assert b.is_exhausted(iterations=3, tool_calls=0, failures=0, started_at=started) == "max_iterations"
    assert b.is_exhausted(iterations=0, tool_calls=10, failures=0, started_at=started) == "max_tool_calls"
    assert b.is_exhausted(iterations=0, tool_calls=0, failures=2, started_at=started) == "max_failures"


def test_budget_seconds_dimension():
    b = Budget(max_iterations=999, max_tool_calls=999, max_failures=999, max_seconds=0.001)
    started = time.time() - 1.0  # 1 second ago
    assert b.is_exhausted(iterations=0, tool_calls=0, failures=0, started_at=started) == "max_seconds"


def test_success_criterion_numeric_ops():
    c = SuccessCriterion(name="count_ge", check_key="n", op=">=", check_value=5)
    assert c.evaluate({"n": 5}) is True
    assert c.evaluate({"n": 4}) is False
    assert c.evaluate({}) is False


def test_success_criterion_contains():
    c = SuccessCriterion(name="has_pcna", check_key="topics", op="contains", check_value="pcna")
    assert c.evaluate({"topics": ["pcna", "md"]}) is True
    assert c.evaluate({"topics": ["foo"]}) is False
    assert c.evaluate({}) is False


def test_success_criterion_predicate_takes_precedence():
    c = SuccessCriterion(
        name="custom", check_key="n", op=">=", check_value=999,
        predicate=lambda ctx: ctx.get("n", 0) > 0,
    )
    assert c.evaluate({"n": 1}) is True       # predicate wins over numeric
    assert c.evaluate({}) is False


def test_goal_unmet_criteria():
    g = Goal(
        objective="test",
        success_criteria=[
            SuccessCriterion(name="a", check_key="n", op=">=", check_value=10),
            SuccessCriterion(name="b", check_key="n", op="<", check_value=100),
        ],
    )
    unmet = g.unmet_criteria({"n": 5})
    assert [c.name for c in unmet] == ["a"]
    assert g.all_criteria_met({"n": 50}) is True
    assert g.all_criteria_met({"n": 5}) is False


def test_goal_with_no_criteria_is_never_complete():
    g = Goal(objective="x")
    # Per the schema: empty criteria => all_criteria_met returns False
    assert g.all_criteria_met({"anything": True}) is False


def test_plan_step_management():
    p = Plan(goal_id="g-1")
    s1 = Step(description="one")
    s2 = Step(description="two")
    p.append(s1)
    p.append(s2)
    assert p.step(s1.step_id) is s1
    assert p.step("does-not-exist") is None


def test_plan_to_dict_includes_steps():
    p = Plan(goal_id="g-1", steps=[Step(description="x")])
    d = p.to_dict()
    assert d["goal_id"] == "g-1"
    assert len(d["steps"]) == 1
    assert d["steps"][0]["description"] == "x"


def test_step_result_carries_retried_from():
    r = StepResult(step_id="s-2", status=StepStatus.SUCCEEDED, retried_from="s-1",
                   confidence=0.7)
    assert r.retried_from == "s-1"
    d = r.to_dict()
    assert d["retried_from"] == "s-1"
    assert d["confidence"] == 0.7


def test_coverage_category_matches_by_keyword():
    cat = CoverageCategory(name="pcna", keywords=["pcna", "AOH1996"], min_items=2)
    assert cat.matches("Title mentions PCNA structure") is True
    assert cat.matches("Aoh1996 binding site analysis") is True
    assert cat.matches("Unrelated paper about RNA folding") is False
