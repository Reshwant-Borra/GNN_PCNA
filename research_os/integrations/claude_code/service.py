"""Claude-facing ResearchOS actions.

This module keeps the Claude Code integration thin: Claude supplies a prompt,
ResearchOS routes and runs the appropriate agents/workflows, and the result is
returned as compact structured data for conversational explanation.
"""
from __future__ import annotations

import json
import os
import uuid
from pathlib import Path
from typing import Any, Callable, Dict

from research_os.orchestrator import Orchestrator, WorkflowResult
from research_os.reports.writer import ReportPaths, write_workflow_report
from research_os.transcripts import finalize_transcript, init_transcript_for_run
from research_os.workflows import WORKFLOWS


def _repo_root(repo_root: str | Path | None = None) -> Path:
    raw = repo_root or os.environ.get("RESEARCH_OS_REPO") or os.environ.get(
        "CLAUDE_PROJECT_DIR"
    )
    return Path(raw or ".").resolve()


def _new_orchestrator(repo_root: str | Path | None = None) -> Orchestrator:
    root = _repo_root(repo_root)
    orch = Orchestrator(
        repo_root=root,
        memory_dir=root / "research_os_memory",
        registries_dir=root / "research_os_registries",
        reports_dir=root / "reports" / "research_os",
    )
    orch.bootstrap()
    return orch


def _paths_to_dict(paths: ReportPaths) -> Dict[str, str]:
    def normalize(path: Path) -> str:
        return str(path if path.is_absolute() else (Path.cwd() / path).resolve())

    return {
        "base": normalize(paths.base),
        "plan_json": normalize(paths.plan_json),
        "result_json": normalize(paths.result_json),
        "markdown": normalize(paths.markdown),
    }


def _compact_agent(agent: Dict[str, Any]) -> Dict[str, Any]:
    findings = agent.get("findings", [])
    return {
        "agent_id": agent.get("agent_id"),
        "agent": agent.get("agent"),
        "status": agent.get("status"),
        "confidence": agent.get("confidence"),
        "summary": agent.get("summary"),
        "finding_count": len(findings),
        "top_findings": [
            {
                "severity": f.get("severity"),
                "title": f.get("title"),
                "required_action": f.get("required_action", ""),
                "blocks_pipeline": f.get("blocks_pipeline", False),
            }
            for f in findings[:5]
        ],
    }


def compact_result(result: WorkflowResult) -> Dict[str, Any]:
    data = result.to_dict()
    plan = data.get("plan", {})
    return {
        "request_summary": plan.get("request_summary"),
        "intents": plan.get("intents", []),
        "risk_level": plan.get("risk_level"),
        "selected_agents": plan.get("selected_agents", []),
        "required_gates": plan.get("required_gates", []),
        "blocked": data.get("blocked", False),
        "block_reason": data.get("block_reason", ""),
        "human_review_required": data.get("human_review_required", False),
        "human_review_reasons": data.get("human_review_reasons", []),
        "gate_status": data.get("gate_status", {}),
        "applied_memory_update_count": len(data.get("applied_memory_updates", [])),
        "pending_memory_update_count": len(data.get("pending_memory_updates", [])),
        "git": data.get("git", {}),
        "agents": [_compact_agent(agent) for agent in data.get("agent_outputs", [])],
    }


def route_request(prompt: str, repo_root: str | Path | None = None) -> Dict[str, Any]:
    """Return the ResearchOS route for a Claude prompt without executing agents."""
    orch = _new_orchestrator(repo_root)
    plan = orch.route(prompt)
    plan_dict = plan.to_dict()
    return {
        "status": "routed",
        "plan": plan_dict,
        "routing_decision": plan.routing_decision,
        "routing_confidence": plan.routing_confidence,
        "routing_reason": plan.routing_reason,
        "requires_claude_fallback": plan.requires_claude_fallback,
        "selected_workflow": plan.selected_workflow,
        "conversation_guidance": {
            "should_run_researchos": bool(
                plan.selected_agents
                and (
                    len(plan.selected_agents) > 1
                    or plan.required_gates
                    or plan.risk_level in ("high", "critical")
                )
            ),
            "approval_required": plan.human_review_required,
            "approval_reason": plan.human_review_reason,
            "claude_fallback_required": plan.requires_claude_fallback,
            "explain_fields": [
                "intents",
                "risk_level",
                "selected_agents",
                "required_gates",
                "human_review_required",
                "routing_decision",
                "routing_confidence",
                "requires_claude_fallback",
            ],
        },
    }


def run_request(
    prompt: str,
    repo_root: str | Path | None = None,
    *,
    force_if_human_required: bool = False,
) -> Dict[str, Any]:
    """Route and execute a Claude prompt through ResearchOS.

    If routing requires human approval, execution is held unless
    force_if_human_required=True. This keeps Claude conversational control from
    silently crossing a PI approval boundary.

    A per-run transcript is always written to
    ``reports/research_os/runs/claude_request/<ts>/transcript.jsonl``.
    """
    orch = _new_orchestrator(repo_root)
    wf_id = str(uuid.uuid4())[:8]
    transcript = init_transcript_for_run(orch.reports_dir, workflow_name := "claude_request")
    plan = None
    result = None
    try:
        plan = orch.route(prompt, workflow_id=wf_id)
        if plan.human_review_required and not force_if_human_required:
            response = {
                "status": "approval_required",
                "plan": plan.to_dict(),
                "summary": {
                    "blocked": True,
                    "block_reason": "ResearchOS routing requires human approval before execution.",
                    "human_review_required": True,
                    "human_review_reason": plan.human_review_reason,
                },
                "routing_decision": plan.routing_decision,
                "routing_confidence": plan.routing_confidence,
                "requires_claude_fallback": plan.requires_claude_fallback,
                "transcript_path": str(transcript.transcript_path),
            }
            return response

        result = orch.execute_plan(
            plan,
            workflow_id=wf_id,
            workflow_name=workflow_name,
            transcript=transcript,
        )
        report = write_workflow_report(
            reports_root=orch.reports_dir,
            workflow=workflow_name,
            result=result.to_dict(),
            title="ResearchOS - Claude Request",
            extra_markdown=(
                "This report was generated from a Claude Code conversational prompt. "
                "Claude should explain the structured result, blockers, gates, and next actions."
            ),
        )
        return {
            "status": "completed",
            "summary": compact_result(result),
            "report": _paths_to_dict(report),
            "routing_decision": plan.routing_decision,
            "routing_confidence": plan.routing_confidence,
            "requires_claude_fallback": plan.requires_claude_fallback,
            "transcript_path": str(transcript.transcript_path),
        }
    finally:
        try:
            finalize_transcript(
                transcript,
                plan_dict=plan.to_dict() if plan is not None else {},
                result_dict=result.to_dict() if result is not None else {},
            )
        except Exception:
            pass


def run_named_workflow(
    name: str,
    args: Dict[str, Any] | None = None,
    repo_root: str | Path | None = None,
) -> Dict[str, Any]:
    """Run a prebuilt ResearchOS workflow by name."""
    if name not in WORKFLOWS:
        return {
            "status": "error",
            "error": f"unknown workflow: {name}",
            "available_workflows": sorted(WORKFLOWS),
        }
    root = _repo_root(repo_root)
    kwargs = dict(args or {})
    func = WORKFLOWS[name]
    call_kwargs = _workflow_kwargs(name, kwargs)
    outcome = func(repo_root=root, **call_kwargs)
    return {
        "status": "completed",
        "workflow": name,
        "summary": compact_result(outcome.result),
        "report": _paths_to_dict(outcome.report),
    }


def _workflow_kwargs(name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    if name == "training_eval":
        return {"prompt": args["prompt"]} if "prompt" in args else {}
    if name == "metric_verification":
        value = args.get("metrics_path") or args.get("metrics")
        return {"metrics_path": value} if value else {}
    if name == "md_validation":
        value = args.get("md_report_dir") or args.get("report")
        return {"md_report_dir": value} if value else {}
    if name in ("claim_audit", "submission_readiness"):
        value = args.get("paper_path") or args.get("paper")
        return {"paper_path": value} if value else {}
    return {}


def get_report(
    path_or_id: str,
    repo_root: str | Path | None = None,
    *,
    max_chars: int = 4000,
) -> Dict[str, Any]:
    """Return a compact report summary from a path or report directory name."""
    root = _repo_root(repo_root)
    candidate = Path(path_or_id)
    if not candidate.is_absolute():
        candidate = root / candidate
    if not candidate.exists():
        matches = list((root / "reports" / "research_os").rglob(path_or_id))
        if not matches:
            matches = [
                p
                for p in (root / "reports" / "research_os").rglob("*")
                if path_or_id in str(p)
            ]
        if matches:
            candidate = matches[0]
    if candidate.is_dir():
        result_json = candidate / "result.json"
        markdown = candidate / "report.md"
    else:
        result_json = candidate if candidate.name == "result.json" else candidate.with_name("result.json")
        markdown = candidate if candidate.suffix == ".md" else candidate.with_name("report.md")
    if result_json.exists():
        data = json.loads(result_json.read_text(encoding="utf-8"))
        return {
            "status": "found",
            "path": str(result_json),
            "summary": _compact_result_dict(data),
        }
    if markdown.exists():
        text = markdown.read_text(encoding="utf-8", errors="replace")
        return {
            "status": "found",
            "path": str(markdown),
            "markdown_excerpt": text[:max_chars],
            "truncated": len(text) > max_chars,
        }
    return {"status": "not_found", "path_or_id": path_or_id}


def _compact_result_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    plan = data.get("plan", {})
    return {
        "request_summary": plan.get("request_summary"),
        "intents": plan.get("intents", []),
        "risk_level": plan.get("risk_level"),
        "selected_agents": plan.get("selected_agents", []),
        "required_gates": plan.get("required_gates", []),
        "blocked": data.get("blocked", False),
        "block_reason": data.get("block_reason", ""),
        "human_review_required": data.get("human_review_required", False),
        "human_review_reasons": data.get("human_review_reasons", []),
        "gate_status": data.get("gate_status", {}),
        "agents": [_compact_agent(agent) for agent in data.get("agent_outputs", [])],
    }


_COMPUTE_ORCH = None


def _compute_orchestrator() -> Any:
    global _COMPUTE_ORCH
    if _COMPUTE_ORCH is None:
        from agents.orchestrator import Orchestrator as ComputeOrchestrator

        _COMPUTE_ORCH = ComputeOrchestrator()
    return _COMPUTE_ORCH


def submit_compute_intent(
    intent: str,
    args: Dict[str, Any] | None = None,
    *,
    user: str = "claude",
    role: str = "collaborator",
    auto_approve: bool = False,
) -> Dict[str, Any]:
    """Submit an optional compute intent through the existing task dispatcher."""
    from agents.orchestrator import Role

    orch = _compute_orchestrator()
    task = orch.submit(
        user=user,
        role=Role(role),
        intent=intent,
        args=args or {},
        auto_approve=auto_approve,
    )
    return {"status": "submitted", "task": task.to_public()}


def approve_or_deny(
    task_id: str,
    decision: str,
    *,
    user: str = "claude",
    reason: str = "",
) -> Dict[str, Any]:
    """Approve or deny a pending compute task in the in-process dispatcher."""
    from agents.orchestrator import Role

    orch = _compute_orchestrator()
    normalized = decision.strip().lower()
    if normalized == "approve":
        task = orch.approve(task_id, user, Role.OWNER)
    elif normalized == "deny":
        task = orch.deny(task_id, user, Role.OWNER, reason)
    else:
        return {"status": "error", "error": "decision must be 'approve' or 'deny'"}
    return {"status": normalized + "d", "task": task.to_public()}


def pursue_goal(
    objective: str,
    repo_root: str | Path | None = None,
    *,
    rationale: str = "",
    budget: Dict[str, Any] | None = None,
    sub_goals: list[Dict[str, Any]] | None = None,
    heal_first: bool = False,
    heal_dry_run: bool = True,
    run_verification: bool = True,
) -> Dict[str, Any]:
    """Run an autonomous-campaign for a high-level goal.

    The controller decomposes the goal (or uses ``sub_goals`` if supplied),
    dispatches sub-goals across the migrated ``AutonomousAgent`` variants,
    optionally runs the multi-agent verification suite, and returns a
    compact ``CampaignResult`` dict.

    All web/LLM tools remain env-gated; this MCP tool does NOT toggle them.
    """
    from research_os.agents.base import AgentContext
    from research_os.autonomous import AUTONOMOUS_AGENTS
    from research_os.autonomous.controller import AutonomousController
    from research_os.autonomous.schemas import Budget, Goal

    root = _repo_root(repo_root)
    # Ensure memory + registries exist so the verification suite has state to read.
    orch = _new_orchestrator(root)
    ctx = AgentContext(
        repo_root=root,
        memory_store=orch.memory_store,
        registry_store=orch.registry_store,
        reports_root=orch.reports_dir,
    )
    budget_obj = Budget(**(budget or {})) if budget else Budget()
    goal = Goal(objective=objective, rationale=rationale, budget=budget_obj)
    sg_list = None
    if sub_goals:
        sg_list = [
            Goal(
                objective=str(sg.get("objective", "")),
                rationale=str(sg.get("rationale", "")),
                budget=budget_obj,
                inputs=dict(sg.get("inputs") or {}),
                parent_goal_id=goal.goal_id,
            )
            for sg in sub_goals
        ]
    controller = AutonomousController(
        ctx,
        agent_factories=dict(AUTONOMOUS_AGENTS),
    )
    try:
        result = controller.pursue_goal(
            goal,
            sub_goals=sg_list,
            heal_first=heal_first,
            heal_dry_run=heal_dry_run,
            run_verification=run_verification,
        )
    except Exception as exc:
        return {"status": "error", "error": f"{type(exc).__name__}: {exc}"}
    payload = result.to_dict()
    payload["status"] = "completed"
    payload["routing_hint"] = "autonomous_controller"
    payload["counts"] = payload.get("counts") or {
        "succeeded": result.succeeded_count,
        "failed": result.failed_count,
        "skipped": result.skipped_count,
    }
    return payload


TOOLS: Dict[str, Callable[..., Dict[str, Any]]] = {
    "route_request": route_request,
    "run_request": run_request,
    "run_workflow": run_named_workflow,
    "get_report": get_report,
    "submit_compute_intent": submit_compute_intent,
    "approve_or_deny": approve_or_deny,
    "pursue_goal": pursue_goal,
}


__all__ = [
    "TOOLS",
    "approve_or_deny",
    "get_report",
    "pursue_goal",
    "route_request",
    "run_named_workflow",
    "run_request",
    "submit_compute_intent",
]
