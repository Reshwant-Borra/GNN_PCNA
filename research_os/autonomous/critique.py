"""Critic abstraction for the autonomous loop.

A ``Critic`` looks at the current plan + step results + context state and
emits a ``CritiqueResult``. The crucial behavior is the **critique → planner
feedback loop**: critic-spawned ``Step``s feed back into the planner so
weaknesses become new tasks rather than inert findings in a report.

Three built-ins:

- ``simple_critic``      — generic check: any step failed? any required
                           criterion unmet? if so, suggest a retry.
- ``coverage_critic``    — built from a ``CoverageEstimator``; spawns
                           targeted follow-up steps for each coverage gap.
- ``confidence_critic``  — checks the rolling confidence trajectory and
                           flags when results are too thin to trust.

Agents wire their own domain critics by passing a ``critics=[...]`` list to
the ``AutonomousAgent`` constructor.
"""
from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Protocol

from research_os.autonomous.coverage import CoverageEstimator
from research_os.autonomous.schemas import (
    CoverageResult,
    CritiqueResult,
    Plan,
    Step,
    StepResult,
    StepStatus,
)


class Critic(Protocol):
    """Protocol every critic implements."""
    name: str

    def __call__(
        self,
        plan: Plan,
        results: List[StepResult],
        ctx_state: Dict[str, Any],
    ) -> CritiqueResult: ...


# ---------------------------------------------------------------------------
# simple_critic
# ---------------------------------------------------------------------------

class _SimpleCritic:
    name = "simple_critic"

    def __call__(self, plan: Plan, results: List[StepResult], ctx_state: Dict[str, Any]) -> CritiqueResult:
        issues: List[str] = []
        spawned: List[Step] = []
        severity = "info"

        failed = [r for r in results if r.status == StepStatus.FAILED]
        if failed:
            severity = "medium"
            issues.append(f"{len(failed)} steps failed")
            for f in failed[:3]:
                # Spawn a retry step pointing at the original.
                original = plan.step(f.step_id)
                if original is None:
                    continue
                retry = Step(
                    kind=original.kind,
                    description=f"Retry of {f.step_id}: {original.description}",
                    tool_name=original.tool_name,
                    tool_input=dict(original.tool_input),
                    target_agent=original.target_agent,
                    rationale=f"Retry suggested by simple_critic; previous failure: {f.error[:120]}",
                    spawned_by=self.name,
                )
                spawned.append(retry)

        # If no steps succeeded, escalate
        succeeded = [r for r in results if r.status == StepStatus.SUCCEEDED]
        if results and not succeeded:
            severity = "high"
            issues.append("no steps succeeded so far")

        return CritiqueResult(
            critic_name=self.name,
            severity=severity,
            summary=("ok" if not issues else "; ".join(issues))[:280],
            issues=issues,
            spawned_steps=spawned,
            requires_replan=bool(spawned),
            confidence=0.7 if not issues else 0.5,
        )


simple_critic: Critic = _SimpleCritic()


# ---------------------------------------------------------------------------
# coverage_critic factory
# ---------------------------------------------------------------------------

def make_coverage_critic(
    *,
    estimator: CoverageEstimator,
    items_key: str = "collected_items",
    min_score: float = 0.7,
    spawn_tool: Optional[str] = None,
    spawn_input_template: Optional[Dict[str, Any]] = None,
    name: str = "coverage_critic",
) -> Critic:
    """Build a critic that pulls items out of ``ctx_state[items_key]`` and
    evaluates coverage. For each gap, optionally spawns a tool-call step
    using ``spawn_tool`` with the gap's recommended query.
    """
    class _CoverageCritic:
        def __init__(self) -> None:
            self.name = name

        def __call__(self, plan: Plan, results: List[StepResult], ctx_state: Dict[str, Any]) -> CritiqueResult:
            items = ctx_state.get(items_key)
            if not isinstance(items, list):
                return CritiqueResult(
                    critic_name=self.name, severity="low",
                    summary=f"no collected items at ctx_state[{items_key!r}]",
                    issues=[f"missing key: {items_key}"],
                )
            cov: CoverageResult = estimator.evaluate(items)
            # Store the coverage result for the agent loop to surface.
            ctx_state["coverage_result"] = cov.to_dict()
            ctx_state["coverage_score"] = cov.score
            spawned: List[Step] = []
            severity = "info" if cov.score >= min_score else "high"
            if cov.gaps and spawn_tool:
                template = dict(spawn_input_template or {})
                for gap, query in zip(cov.gaps, cov.suggested_queries):
                    spawned.append(Step(
                        kind="tool_call",
                        description=f"Fill coverage gap: {gap}",
                        tool_name=spawn_tool,
                        tool_input={**template, "query": query},
                        rationale=f"coverage_critic: {gap} below threshold",
                        spawned_by=self.name,
                    ))
            return CritiqueResult(
                critic_name=self.name,
                severity=severity,
                summary=f"coverage score={cov.score:.2f}, gaps={len(cov.gaps)}",
                issues=[f"gap: {g}" for g in cov.gaps],
                spawned_steps=spawned,
                requires_replan=bool(spawned),
                confidence=cov.score,
            )

    return _CoverageCritic()


# ---------------------------------------------------------------------------
# confidence_critic
# ---------------------------------------------------------------------------

class _ConfidenceCritic:
    name = "confidence_critic"

    def __init__(self, min_average: float = 0.5):
        self.min_average = min_average

    def __call__(self, plan: Plan, results: List[StepResult], ctx_state: Dict[str, Any]) -> CritiqueResult:
        if not results:
            return CritiqueResult(critic_name=self.name, severity="info",
                                  summary="no results yet", confidence=0.5)
        confidences = [r.confidence for r in results if r.status == StepStatus.SUCCEEDED]
        if not confidences:
            return CritiqueResult(critic_name=self.name, severity="high",
                                  summary="no successful results to score",
                                  confidence=0.0,
                                  issues=["no successes"])
        avg = sum(confidences) / len(confidences)
        ctx_state["average_confidence"] = round(avg, 3)
        if avg >= self.min_average:
            return CritiqueResult(critic_name=self.name, severity="info",
                                  summary=f"avg confidence {avg:.2f} OK", confidence=avg)
        return CritiqueResult(
            critic_name=self.name, severity="medium",
            summary=f"avg confidence {avg:.2f} below {self.min_average:.2f}",
            issues=[f"low average confidence: {avg:.2f}"],
            confidence=avg,
        )


def confidence_critic(min_average: float = 0.5) -> Critic:
    return _ConfidenceCritic(min_average)


__all__ = [
    "Critic",
    "confidence_critic",
    "make_coverage_critic",
    "simple_critic",
]
