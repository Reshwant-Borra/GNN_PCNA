"""Tests for VerificationSuite — runs the existing 21 agents through the
scientific orchestrator and reports per-check status."""
from __future__ import annotations

from pathlib import Path

import pytest

from research_os.agents.base import AgentContext
from research_os.autonomous.verification import (
    CHECK_NAME_BY_AGENT,
    VerificationSuite,
    VERIFICATION_AGENTS_ORDER,
)
from research_os.memory.store import MemoryStore, ensure_memory_initialized
from research_os.orchestrator import Orchestrator
from research_os.registries.store import RegistryStore, ensure_registries_initialized


@pytest.fixture
def wired_ctx(tmp_path: Path) -> AgentContext:
    mem = MemoryStore(tmp_path / "research_os_memory")
    ensure_memory_initialized(mem)
    reg = RegistryStore(tmp_path / "research_os_registries")
    ensure_registries_initialized(reg)
    return AgentContext(repo_root=tmp_path, memory_store=mem, registry_store=reg)


def test_verification_suite_runs_all_checks(wired_ctx, tmp_path):
    orch = Orchestrator(
        repo_root=tmp_path,
        memory_dir=tmp_path / "research_os_memory",
        registries_dir=tmp_path / "research_os_registries",
        reports_dir=tmp_path / "reports" / "research_os",
    )
    orch.bootstrap()
    suite = VerificationSuite(wired_ctx, orchestrator=orch)
    report = suite.run(prompt="self-test verification")
    # All 10 canonical check names appear in the report.
    names = {c.name for c in report.checks}
    for canonical in CHECK_NAME_BY_AGENT.values():
        assert canonical in names, f"missing check: {canonical}"


def test_verification_aggregate_status_is_valid(wired_ctx, tmp_path):
    orch = Orchestrator(
        repo_root=tmp_path,
        memory_dir=tmp_path / "research_os_memory",
        registries_dir=tmp_path / "research_os_registries",
        reports_dir=tmp_path / "reports" / "research_os",
    )
    orch.bootstrap()
    suite = VerificationSuite(wired_ctx, orchestrator=orch)
    report = suite.run()
    assert report.aggregate_status in ("pass", "warning", "fail")


def test_verification_spawns_followups_for_failing_checks(wired_ctx, tmp_path):
    orch = Orchestrator(
        repo_root=tmp_path,
        memory_dir=tmp_path / "research_os_memory",
        registries_dir=tmp_path / "research_os_registries",
        reports_dir=tmp_path / "reports" / "research_os",
    )
    orch.bootstrap()
    suite = VerificationSuite(wired_ctx, orchestrator=orch)
    report = suite.run()
    # With empty registries, some checks will warn — there should be at
    # least one spawned follow-up (most likely from dataset/leakage checks
    # that find pending sections).
    failing = [c for c in report.checks if c.status in ("fail", "warning")]
    if failing:
        assert len(report.spawned_followups) >= 1


def test_verification_agents_order_includes_all_canonical_checks():
    """Sanity check that every check_name has a corresponding agent in the order."""
    for agent_id in CHECK_NAME_BY_AGENT:
        assert agent_id in VERIFICATION_AGENTS_ORDER
