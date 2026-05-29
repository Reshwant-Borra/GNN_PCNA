"""Workflow report writers.

Each workflow run writes to:

    reports/research_os/<workflow>/<timestamp>/
        plan.json
        result.json
        report.md

The markdown report is the human-readable summary; the JSONs are the canonical
inputs for any downstream automation.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")


@dataclass
class ReportPaths:
    base: Path
    plan_json: Path
    result_json: Path
    markdown: Path


def _ensure_report_dir(reports_root: Path, workflow: str) -> ReportPaths:
    folder = reports_root / workflow / _utc_now()
    folder.mkdir(parents=True, exist_ok=True)
    return ReportPaths(
        base=folder,
        plan_json=folder / "plan.json",
        result_json=folder / "result.json",
        markdown=folder / "report.md",
    )


def write_orchestration_plan(reports_root: Path, workflow: str, plan_dict: Dict[str, Any]) -> ReportPaths:
    paths = _ensure_report_dir(reports_root, workflow)
    paths.plan_json.write_text(json.dumps(plan_dict, indent=2, default=str), encoding="utf-8")
    return paths


def write_workflow_report(
    *,
    reports_root: Path,
    workflow: str,
    result: Dict[str, Any],
    title: str,
    extra_markdown: str = "",
) -> ReportPaths:
    paths = _ensure_report_dir(reports_root, workflow)
    paths.plan_json.write_text(
        json.dumps(result.get("plan", {}), indent=2, default=str), encoding="utf-8"
    )
    paths.result_json.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
    paths.markdown.write_text(
        _render_markdown(title=title, result=result, extra_markdown=extra_markdown),
        encoding="utf-8",
    )
    return paths


def _render_markdown(*, title: str, result: Dict[str, Any], extra_markdown: str) -> str:
    plan = result.get("plan", {})
    agents = result.get("agent_outputs", [])
    gate_status = result.get("gate_status", {})
    blocked = result.get("blocked")
    block_reason = result.get("block_reason", "")
    human = result.get("human_review_required")
    human_reasons = result.get("human_review_reasons", [])
    applied = result.get("applied_memory_updates", [])
    pending = result.get("pending_memory_updates", [])
    git = result.get("git", {})

    lines: List[str] = []
    lines.append(f"# {title}")
    lines.append("")
    lines.append(f"_Generated {_utc_now()}_")
    lines.append("")
    lines.append("## Request")
    lines.append("")
    lines.append(f"> {plan.get('request_summary', '(none)')}")
    lines.append("")
    lines.append(f"- intents: {plan.get('intents', [])}")
    lines.append(f"- risk level: **{plan.get('risk_level', 'unknown')}**")
    lines.append(f"- agents executed: {', '.join(plan.get('selected_agents', []))}")
    lines.append(f"- gates evaluated: {', '.join(plan.get('required_gates', [])) or '(none)'}")
    lines.append("")
    lines.append("## Verdict")
    lines.append("")
    lines.append(f"- blocked: **{blocked}**")
    if blocked:
        lines.append(f"- block reason: {block_reason}")
    lines.append(f"- human review required: **{human}**")
    for reason in human_reasons:
        lines.append(f"  - {reason}")
    lines.append("")
    lines.append("## Gate status")
    lines.append("")
    if gate_status:
        lines.append("| Gate | Status |")
        lines.append("| --- | --- |")
        for gate, status in gate_status.items():
            lines.append(f"| {gate} | `{status}` |")
    else:
        lines.append("_(no gates required by this plan)_")
    lines.append("")
    lines.append("## Agent outputs")
    lines.append("")
    for agent in agents:
        lines.append(f"### {agent.get('agent', agent.get('agent_id'))}")
        lines.append("")
        lines.append(f"- status: **{agent.get('status')}** (confidence {agent.get('confidence')})")
        lines.append(f"- summary: {agent.get('summary')}")
        findings = agent.get("findings", [])
        if findings:
            lines.append(f"- findings: {len(findings)}")
            for f in findings:
                tag = f.get("severity", "?").upper()
                lines.append(
                    f"  - **[{tag}]** {f.get('title')}"
                    + (f" — _{f.get('required_action')}_" if f.get("required_action") else "")
                )
        gate_updates = agent.get("gate_updates", [])
        if gate_updates:
            lines.append(f"- gate updates: {', '.join(g.get('gate') + '→' + g.get('new_status') for g in gate_updates)}")
        if agent.get("artifacts_to_mark_stale"):
            lines.append(f"- artifacts to mark stale: {', '.join(agent.get('artifacts_to_mark_stale'))}")
        lines.append("")
    if applied:
        lines.append("## Applied memory updates")
        lines.append("")
        for update in applied:
            lines.append(
                f"- {update.get('target_file')}: {update.get('update_type')} — "
                f"{update.get('summary')[:100]}"
            )
        lines.append("")
    if pending:
        lines.append("## Pending memory updates (require approval)")
        lines.append("")
        for update in pending:
            lines.append(
                f"- {update.get('target_file')}: {update.get('update_type')} — "
                f"{update.get('summary')[:100]}"
            )
            if update.get("error"):
                lines.append(f"  - error: {update.get('error')}")
        lines.append("")
    if git:
        lines.append("## Git state at report time")
        lines.append("")
        lines.append(f"- branch: {git.get('branch')}")
        lines.append(f"- commit: {git.get('short_commit')} ({'dirty' if git.get('dirty') else 'clean'})")
        lines.append("")
    if extra_markdown:
        lines.append("## Workflow notes")
        lines.append("")
        lines.append(extra_markdown.rstrip())
        lines.append("")
    return "\n".join(lines)
