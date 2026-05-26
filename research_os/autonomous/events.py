"""Event-emission helpers for the autonomous framework.

Wraps ``research_os.events.emitter.emit`` with shape-checked helpers for each
autonomous event type. Keeps call sites in ``agent.py`` / ``controller.py``
short and makes the event payloads stable for transcript / dashboard
consumers.

All helpers are best-effort: if the global emitter is not initialized, the
underlying ``emit()`` is a silent no-op, so unit tests don't need to wire up
the dashboard.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from research_os.events import emit


def goal_started(workflow_id: str, *, goal_id: str, agent_id: str,
                 objective: str, parent_goal_id: Optional[str] = None,
                 budget: Optional[Dict[str, Any]] = None) -> None:
    emit("goal_started", workflow_id, {
        "goal_id": goal_id,
        "agent_id": agent_id,
        "objective": objective[:280],
        "parent_goal_id": parent_goal_id,
        "budget": dict(budget or {}),
    })


def goal_completed(workflow_id: str, *, goal_id: str, agent_id: str,
                   status: str, summary: str = "",
                   criteria_met: Optional[List[str]] = None,
                   criteria_unmet: Optional[List[str]] = None) -> None:
    emit("goal_completed", workflow_id, {
        "goal_id": goal_id,
        "agent_id": agent_id,
        "status": status,
        "summary": summary[:500],
        "criteria_met": list(criteria_met or []),
        "criteria_unmet": list(criteria_unmet or []),
    })


def plan_created(workflow_id: str, *, plan_id: str, goal_id: str, agent_id: str,
                 step_count: int, rationale: str = "") -> None:
    emit("plan_created", workflow_id, {
        "plan_id": plan_id,
        "goal_id": goal_id,
        "agent_id": agent_id,
        "step_count": step_count,
        "rationale": rationale[:280],
    })


def plan_revised(workflow_id: str, *, plan_id: str, goal_id: str, agent_id: str,
                 revision: int, step_count: int, reason: str = "") -> None:
    emit("plan_revised", workflow_id, {
        "plan_id": plan_id,
        "goal_id": goal_id,
        "agent_id": agent_id,
        "revision": revision,
        "step_count": step_count,
        "reason": reason[:280],
    })


def step_started(workflow_id: str, *, step_id: str, agent_id: str,
                 kind: str, description: str = "",
                 tool_name: Optional[str] = None) -> None:
    emit("step_started", workflow_id, {
        "step_id": step_id,
        "agent_id": agent_id,
        "kind": kind,
        "description": description[:280],
        "tool_name": tool_name,
    })


def step_completed(workflow_id: str, *, step_id: str, agent_id: str,
                   status: str, summary: str = "",
                   confidence: float = 0.0,
                   duration_seconds: float = 0.0) -> None:
    emit("step_completed", workflow_id, {
        "step_id": step_id,
        "agent_id": agent_id,
        "status": status,
        "summary": summary[:280],
        "confidence": confidence,
        "duration_seconds": duration_seconds,
    })


def step_failed(workflow_id: str, *, step_id: str, agent_id: str,
                error: str, will_retry: bool = False) -> None:
    emit("step_failed", workflow_id, {
        "step_id": step_id,
        "agent_id": agent_id,
        "error": error[:500],
        "will_retry": will_retry,
    })


def step_retried(workflow_id: str, *, step_id: str, agent_id: str,
                 retry_of: str, attempt: int) -> None:
    emit("step_retried", workflow_id, {
        "step_id": step_id,
        "agent_id": agent_id,
        "retry_of": retry_of,
        "attempt": attempt,
    })


def tool_called(workflow_id: str, *, tool_name: str, agent_id: str,
                step_id: Optional[str] = None,
                inputs_summary: str = "") -> None:
    emit("tool_called", workflow_id, {
        "tool_name": tool_name,
        "agent_id": agent_id,
        "step_id": step_id,
        "inputs_summary": inputs_summary[:280],
    })


def tool_result(workflow_id: str, *, tool_name: str, agent_id: str,
                step_id: Optional[str] = None,
                ok: bool = True, summary: str = "",
                duration_seconds: float = 0.0) -> None:
    emit("tool_result", workflow_id, {
        "tool_name": tool_name,
        "agent_id": agent_id,
        "step_id": step_id,
        "ok": ok,
        "summary": summary[:280],
        "duration_seconds": duration_seconds,
    })


def critique_started(workflow_id: str, *, agent_id: str, critic_name: str,
                     goal_id: str) -> None:
    emit("critique_started", workflow_id, {
        "agent_id": agent_id,
        "critic_name": critic_name,
        "goal_id": goal_id,
    })


def critique_completed(workflow_id: str, *, agent_id: str, critic_name: str,
                       goal_id: str, severity: str, issue_count: int,
                       spawned_step_count: int, requires_replan: bool) -> None:
    emit("critique_completed", workflow_id, {
        "agent_id": agent_id,
        "critic_name": critic_name,
        "goal_id": goal_id,
        "severity": severity,
        "issue_count": issue_count,
        "spawned_step_count": spawned_step_count,
        "requires_replan": requires_replan,
    })


def replan_started(workflow_id: str, *, agent_id: str, goal_id: str,
                   plan_id: str, reason: str = "") -> None:
    emit("replan_started", workflow_id, {
        "agent_id": agent_id,
        "goal_id": goal_id,
        "plan_id": plan_id,
        "reason": reason[:280],
    })


def replan_completed(workflow_id: str, *, agent_id: str, goal_id: str,
                     plan_id: str, revision: int, new_step_count: int) -> None:
    emit("replan_completed", workflow_id, {
        "agent_id": agent_id,
        "goal_id": goal_id,
        "plan_id": plan_id,
        "revision": revision,
        "new_step_count": new_step_count,
    })


def coverage_evaluated(workflow_id: str, *, agent_id: str, goal_id: str,
                       score: float, gaps: List[str],
                       total_items: int = 0) -> None:
    emit("coverage_evaluated", workflow_id, {
        "agent_id": agent_id,
        "goal_id": goal_id,
        "score": score,
        "gaps": list(gaps),
        "total_items": total_items,
    })


def fallback_triggered(workflow_id: str, *, agent_id: str, reason: str) -> None:
    emit("fallback_triggered", workflow_id, {
        "agent_id": agent_id,
        "reason": reason[:280],
    })


def handoff_requested(workflow_id: str, *, from_agent: str, to_agent: str,
                      reason: str = "") -> None:
    emit("handoff_requested", workflow_id, {
        "from_agent": from_agent,
        "to_agent": to_agent,
        "reason": reason[:280],
    })


def budget_exhausted(workflow_id: str, *, agent_id: str, dimension: str,
                     iterations: int, tool_calls: int, failures: int) -> None:
    emit("budget_exhausted", workflow_id, {
        "agent_id": agent_id,
        "dimension": dimension,
        "iterations": iterations,
        "tool_calls": tool_calls,
        "failures": failures,
    })


def campaign_started(workflow_id: str, *, campaign_id: str, goal_id: str,
                     sub_goal_count: int) -> None:
    emit("campaign_started", workflow_id, {
        "campaign_id": campaign_id,
        "goal_id": goal_id,
        "sub_goal_count": sub_goal_count,
    })


def campaign_completed(workflow_id: str, *, campaign_id: str, goal_id: str,
                       status: str, completed_sub_goals: int,
                       failed_sub_goals: int) -> None:
    emit("campaign_completed", workflow_id, {
        "campaign_id": campaign_id,
        "goal_id": goal_id,
        "status": status,
        "completed_sub_goals": completed_sub_goals,
        "failed_sub_goals": failed_sub_goals,
    })


__all__ = [
    "budget_exhausted",
    "campaign_completed",
    "campaign_started",
    "coverage_evaluated",
    "critique_completed",
    "critique_started",
    "fallback_triggered",
    "goal_completed",
    "goal_started",
    "handoff_requested",
    "plan_created",
    "plan_revised",
    "replan_completed",
    "replan_started",
    "step_completed",
    "step_failed",
    "step_retried",
    "step_started",
    "tool_called",
    "tool_result",
]
