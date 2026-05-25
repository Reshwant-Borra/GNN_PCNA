"""Shared helper for workflow runners.

`run_workflow` takes a synthesized prompt + an optional override of intents
and agents, runs the orchestrator, and writes a report.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional

from research_os.orchestrator import Orchestrator, WorkflowResult
from research_os.reports import ReportPaths, write_workflow_report
from research_os.routing.agents import select_agents
from research_os.routing.context_builder import build_context_packet
from research_os.routing.gates import determine_required_gates
from research_os.schemas.context import OrchestrationPlan


@dataclass
class WorkflowOutcome:
    name: str
    result: WorkflowResult
    report: ReportPaths


def run_workflow(
    name: str,
    *,
    repo_root: Path | str = ".",
    prompt: str = "",
    intents: Optional[Iterable[str]] = None,
    risk_level: str = "high",
    extra_agents: Optional[Iterable[str]] = None,
    extra_gates: Optional[Iterable[str]] = None,
    title: str = "",
    extra_markdown: str = "",
    bootstrap: bool = True,
) -> WorkflowOutcome:
    """Run a workflow end-to-end and write the report."""
    orch = Orchestrator(repo_root=repo_root)
    if bootstrap:
        orch.bootstrap()
    intent_list = list(intents) if intents else None
    if intent_list is None:
        plan = orch.route(prompt or f"workflow:{name}")
    else:
        agents = select_agents(intent_list, risk_level)
        if extra_agents:
            for a in extra_agents:
                if a not in agents:
                    agents.append(a)
        gates = determine_required_gates(intent_list)
        if extra_gates:
            for g in extra_gates:
                if g not in gates:
                    gates.append(g)
        packet = build_context_packet(
            task=prompt or f"workflow:{name}",
            intents=intent_list,
            risk_level=risk_level,
            memory_store=orch.memory_store,
            registry_store=orch.registry_store,
        )
        plan = OrchestrationPlan(
            request_summary=prompt or f"workflow:{name}",
            intents=intent_list,
            risk_level=risk_level,
            selected_agents=agents,
            required_gates=gates,
            context_packet=packet,
        )
        plan.validate()
    result = orch.execute_plan(plan)
    report = write_workflow_report(
        reports_root=orch.reports_dir,
        workflow=name,
        result=result.to_dict(),
        title=title or f"ResearchOS workflow: {name}",
        extra_markdown=extra_markdown,
    )
    return WorkflowOutcome(name=name, result=result, report=report)


__all__ = ["WorkflowOutcome", "run_workflow"]
