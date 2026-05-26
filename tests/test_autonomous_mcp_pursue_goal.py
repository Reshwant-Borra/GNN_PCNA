"""Tests for the pursue_goal MCP tool (Phase 5)."""
from __future__ import annotations

from pathlib import Path

import pytest

from research_os.integrations.claude_code.mcp_server import TOOL_DEFS
from research_os.integrations.claude_code.service import TOOLS, pursue_goal


def test_pursue_goal_in_service_tools():
    assert "pursue_goal" in TOOLS


def test_pursue_goal_in_mcp_tool_defs():
    names = [t["name"] for t in TOOL_DEFS]
    assert "pursue_goal" in names
    pg = next(t for t in TOOL_DEFS if t["name"] == "pursue_goal")
    assert "objective" in pg["inputSchema"]["required"]


def test_pursue_goal_returns_completed_for_simple_corpus(tmp_path: Path, monkeypatch):
    monkeypatch.delenv("RESEARCHOS_AUTONOMY_OFF", raising=False)
    result = pursue_goal(
        objective="Build a small literature corpus for PCNA",
        repo_root=str(tmp_path),
        run_verification=False,
    )
    assert result["status"] == "completed"
    assert "sub_outcomes" in result
    assert result["counts"]["succeeded"] + result["counts"]["failed"] + result["counts"]["skipped"] >= 1


def test_pursue_goal_handles_explicit_sub_goals(tmp_path: Path, monkeypatch):
    monkeypatch.delenv("RESEARCHOS_AUTONOMY_OFF", raising=False)
    result = pursue_goal(
        objective="custom campaign",
        repo_root=str(tmp_path),
        sub_goals=[
            {"objective": "ref", "inputs": {"target_agent": "literature_web"}},
        ],
        run_verification=False,
    )
    assert result["status"] == "completed"
    assert len(result["sub_outcomes"]) == 1


def test_pursue_goal_with_heal_first_emits_report(tmp_path: Path, monkeypatch):
    monkeypatch.delenv("RESEARCHOS_AUTONOMY_OFF", raising=False)
    # Drop a fake compute orchestrator so the healer has something to find.
    (tmp_path / "agents").mkdir(exist_ok=True)
    (tmp_path / "agents" / "orchestrator.py").write_text(
        "import agents.pcna_crawler\n", encoding="utf-8",
    )
    result = pursue_goal(
        objective="repair + verify",
        repo_root=str(tmp_path),
        heal_first=True,
        heal_dry_run=True,
        run_verification=False,
    )
    assert result["status"] == "completed"
    assert result.get("heal_report") is not None
