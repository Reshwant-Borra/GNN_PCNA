"""Phase 6 — resilience tests.

The system must survive:
- missing workflows (no registered factory for a sub-goal's target_agent)
- missing files (the agent's repo_root is bare)
- corrupt registries
- incompatible interfaces (agent factory returns something that isn't an agent)
- partial failures (some sub-goals succeed, some fail)
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

import pytest

from research_os.agents.base import AgentContext
from research_os.autonomous import AUTONOMOUS_AGENTS
from research_os.autonomous.agent import AutonomousAgent
from research_os.autonomous.controller import AutonomousController
from research_os.autonomous.reference_agent import ReferenceAutonomousAgent
from research_os.autonomous.schemas import Goal
from research_os.memory.store import MemoryStore, ensure_memory_initialized
from research_os.registries.store import RegistryStore, ensure_registries_initialized
from research_os.schemas.context import ContextPacket


@pytest.fixture
def wired_ctx(tmp_path: Path) -> AgentContext:
    mem = MemoryStore(tmp_path / "research_os_memory")
    ensure_memory_initialized(mem)
    reg = RegistryStore(tmp_path / "research_os_registries")
    ensure_registries_initialized(reg)
    return AgentContext(repo_root=tmp_path, memory_store=mem, registry_store=reg)


def test_missing_factory_does_not_crash_campaign(wired_ctx, monkeypatch):
    monkeypatch.delenv("RESEARCHOS_AUTONOMY_OFF", raising=False)
    controller = AutonomousController(
        wired_ctx,
        agent_factories={"reference_autonomous": ReferenceAutonomousAgent},
        default_agent_id="reference_autonomous",
    )
    result = controller.pursue_goal(
        Goal(objective="run"),
        sub_goals=[
            Goal(objective="sg1", inputs={"target_agent": "reference_autonomous"}),
            Goal(objective="sg2-orphan", inputs={"target_agent": "vanished_agent"}),
        ],
        run_verification=False,
    )
    assert result.succeeded_count == 1
    assert result.sub_outcomes[1].skipped is True


def test_missing_repo_files_do_not_crash(tmp_path: Path, monkeypatch):
    """An empty repo_root with no memory or registries — the autonomous
    agent must still complete via deterministic fallback rather than
    crash."""
    monkeypatch.delenv("RESEARCHOS_AUTONOMY_OFF", raising=False)
    # Bare ctx — no memory/registry stores attached.
    ctx = AgentContext(repo_root=tmp_path)
    # Build an autonomous agent that has no store, so any tool that
    # requires one will fail and trigger fallback.
    agent = ReferenceAutonomousAgent(ctx)
    out = agent.run(ContextPacket(task="anything"))
    out.validate()
    # Should be warning since no canonical files exist, but not crash.
    assert out.status in ("pass", "warning")


def test_corrupt_registry_is_recoverable(wired_ctx, monkeypatch):
    """A registry that fails to read should not crash an autonomous
    agent — the legacy fallback handles it gracefully."""
    monkeypatch.delenv("RESEARCHOS_AUTONOMY_OFF", raising=False)
    # Corrupt the source_registry by writing non-JSON bytes.
    reg_path = wired_ctx.repo_root / "research_os_registries" / "source_registry.json"
    reg_path.write_text("not json at all\n", encoding="utf-8")
    controller = AutonomousController(
        wired_ctx,
        agent_factories=dict(AUTONOMOUS_AGENTS),
    )
    result = controller.pursue_goal(
        Goal(objective="Build a corpus for PCNA"),
        run_verification=False,
    )
    # We don't insist on success — just that nothing crashed.
    assert result.aggregate_status in ("pass", "warning", "fail")


def test_factory_returning_non_agent_is_handled(wired_ctx, monkeypatch):
    """If a factory returns something that doesn't implement .run, the
    controller treats it as a crash, not an unhandled AttributeError."""
    monkeypatch.delenv("RESEARCHOS_AUTONOMY_OFF", raising=False)

    def bad_factory(ctx):
        class _NotAnAgent:
            pass
        return _NotAnAgent()

    controller = AutonomousController(
        wired_ctx,
        agent_factories={"bad": bad_factory},
        default_agent_id="bad",
    )
    result = controller.pursue_goal(
        Goal(objective="anything"),
        run_verification=False,
    )
    assert result.aggregate_status == "fail"
    assert "crashed" in result.sub_outcomes[0].error.lower() or \
           "no attribute" in result.sub_outcomes[0].error.lower() or \
           "factory failed" in result.sub_outcomes[0].error.lower()


def test_partial_failure_keeps_succeeded_count_correct(wired_ctx, monkeypatch):
    """Some sub-goals succeed, some fail — the aggregate should reflect
    both and the campaign should not abort midway."""
    monkeypatch.delenv("RESEARCHOS_AUTONOMY_OFF", raising=False)

    class _CrashAgent(AutonomousAgent):
        agent_id = "crash_test"
        display_name = "Crash Test"

        def run(self, packet):  # type: ignore[override]
            raise RuntimeError("planned crash")

    controller = AutonomousController(
        wired_ctx,
        agent_factories={
            "reference_autonomous": ReferenceAutonomousAgent,
            "crash_test": _CrashAgent,
        },
    )
    result = controller.pursue_goal(
        Goal(objective="mixed"),
        sub_goals=[
            Goal(objective="a", inputs={"target_agent": "reference_autonomous"}),
            Goal(objective="b", inputs={"target_agent": "crash_test"}),
            Goal(objective="c", inputs={"target_agent": "reference_autonomous"}),
        ],
        run_verification=False,
    )
    assert result.succeeded_count == 2
    assert result.failed_count == 1
    assert result.aggregate_status == "fail"


def test_verification_suite_survives_blocked_orchestrator(tmp_path, monkeypatch):
    """A repo with empty memory + registries makes verification produce
    warnings/blocks — but the suite itself must return a report, not
    crash."""
    monkeypatch.delenv("RESEARCHOS_AUTONOMY_OFF", raising=False)
    # Don't bootstrap — verify it still works.
    mem = MemoryStore(tmp_path / "research_os_memory")
    ensure_memory_initialized(mem)
    reg = RegistryStore(tmp_path / "research_os_registries")
    ensure_registries_initialized(reg)
    ctx = AgentContext(repo_root=tmp_path, memory_store=mem, registry_store=reg)
    controller = AutonomousController(
        ctx, agent_factories=dict(AUTONOMOUS_AGENTS),
    )
    result = controller.pursue_goal(
        Goal(objective="Verify everything"),
        run_verification=True,
    )
    # Verification report exists and aggregated to a valid status.
    assert len(result.verification_reports) >= 1
    assert result.verification_reports[0].aggregate_status in ("pass", "warning", "fail")


def test_memory_propose_update_human_gate_is_preserved(wired_ctx):
    """The autonomous tool must respect requires_human_approval and NOT
    apply the update — instead queue it."""
    from research_os.tools.registry import ToolRegistry
    from research_os.tools.builtin import register_builtin

    reg = ToolRegistry()
    register_builtin(reg, wired_ctx, agent_id="resilience_test")
    res = reg.call("memory_propose_update", {
        "target_file": "CURRENT_CLAIMS.md",
        "update_type": "upgrade_claim",
        "summary": "Auto-upgrade attempt (should be blocked)",
        "append_section": "(test)",
        "requires_human_approval": True,
        "reason_human_approval_required": "claim upgrade above moderately_supported",
    })
    assert res.ok is True
    assert res.output["applied"] is False
    assert res.output["queued_for_human"] is True
