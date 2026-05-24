"""Orchestrator integration: gate enforcement, blocking, no self-approval."""
from __future__ import annotations

import re

import pytest

from research_os.schemas.registries import ClaimEntry, ArtifactEntry


def test_claim_request_blocks_when_validation_inconclusive(tmp_orchestrator):
    """The bedrock scenario: paper-grade claim requested but validation is inconclusive."""
    result = tmp_orchestrator.run("Can we say MD validated the cryptic pocket?")
    assert result.blocked, result.gate_status
    assert any(
        "validation" in g or "leakage" in g or "claim" in g
        for g, status in result.gate_status.items()
        if status in ("fail", "blocked", "stale")
    )


def test_submission_request_requires_human(tmp_orchestrator):
    result = tmp_orchestrator.run("Submit the manuscript.")
    assert result.human_review_required
    assert result.human_review_reasons


def test_routing_includes_contradiction_hunter_for_high_risk(tmp_orchestrator):
    plan = tmp_orchestrator.route("Run training on the latest split.")
    assert "contradiction_hunter" in plan.selected_agents


def test_strongly_supported_claim_without_evidence_blocks(tmp_orchestrator):
    tmp_orchestrator.registry_store.append(
        "claim_registry",
        ClaimEntry(
            claim_id="",
            claim_text="The GNN discovered a binding site near AOH1996 contacts.",
            claim_strength="strongly_supported_computationally",
            status="strongly_supported_computationally",
            evidence_for=[],  # deliberately empty
        ),
    )
    result = tmp_orchestrator.run("Audit the project for hidden contradictions.")
    flagged = [
        f
        for agent in result.agent_outputs
        for f in agent.findings
        if "strongly_supported" in (f.title + f.description)
        or "biologically aggressive" in f.title
    ]
    assert flagged, [f.title for a in result.agent_outputs for f in a.findings]


def test_current_artifact_with_stale_dependency_is_flagged(tmp_orchestrator):
    parent = tmp_orchestrator.registry_store.append(
        "artifact_registry",
        ArtifactEntry(
            artifact_id="",
            path="/data/graphs",
            artifact_type="graph",
            status="stale",
            status_reason="bug fix",
        ),
    )
    child = tmp_orchestrator.registry_store.append(
        "artifact_registry",
        ArtifactEntry(
            artifact_id="",
            path="/results/metrics.json",
            artifact_type="metric",
            status="current",
            dependencies=[parent],
            git_commit="abc",
            command="python train.py",
            created_at="2026-05-24T00:00:00Z",
        ),
    )
    result = tmp_orchestrator.run("What is the latest AUROC?")
    flagged = [
        f
        for agent in result.agent_outputs
        for f in agent.findings
        if child in (f.affected_artifacts or [])
    ]
    assert flagged, [f.title for a in result.agent_outputs for f in a.findings]


def test_gate_status_is_worst_of_all_reports(tmp_orchestrator):
    """If any agent reports 'fail' or 'blocked', the gate should reflect that."""
    result = tmp_orchestrator.run("Can we claim MD validated the cryptic pocket?")
    # Validation is inconclusive by default, leakage gate has no split protocol.
    assert any(
        status in ("fail", "blocked")
        for status in result.gate_status.values()
    )


def test_paper_claim_agent_does_not_self_approve_claim_gate(tmp_orchestrator):
    """Paper Claim is the gate owner — but Reviewer + Contradiction must weigh in
    before the claim gate can be 'pass'."""
    plan = tmp_orchestrator.route("Write the results section about the MD-validated pocket.")
    # claim gate is in the required gates
    assert "claim" in plan.required_gates
    result = tmp_orchestrator.execute_plan(plan)
    # The contradiction hunter must have run after paper_claim.
    ids = [a.agent_id for a in result.agent_outputs]
    assert ids.index("paper_claim") < ids.index("contradiction_hunter")
