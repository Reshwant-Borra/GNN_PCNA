"""Schema validation: closed vocabularies, required fields, dataclass shape."""
from __future__ import annotations

import pytest

from research_os.schemas import (
    AgentOutput,
    ArtifactEntry,
    ClaimEntry,
    GateName,
    GateStatus,
    OrchestrationPlan,
)
from research_os.schemas.core import EvidenceRef, Finding


def test_agent_output_status_must_be_allowed():
    out = AgentOutput(
        agent="x", agent_id="x", task="t", status="pass", confidence=0.5, summary="ok"
    )
    out.validate()
    out.status = "bogus"
    with pytest.raises(ValueError):
        out.validate()


def test_agent_output_confidence_range():
    out = AgentOutput(
        agent="x", agent_id="x", task="t", status="pass", confidence=1.5, summary="ok"
    )
    with pytest.raises(ValueError):
        out.validate()


def test_agent_output_human_review_requires_reason():
    out = AgentOutput(
        agent="x",
        agent_id="x",
        task="t",
        status="pass",
        confidence=0.5,
        summary="ok",
        human_review_required=True,
        human_review_reason="",
    )
    with pytest.raises(ValueError):
        out.validate()


def test_finding_severity_validated():
    f = Finding(finding_id="F1", severity="critical", title="x")
    f.validate()
    f.severity = "minor"
    with pytest.raises(ValueError):
        f.validate()


def test_artifact_entry_vocab_enforced():
    a = ArtifactEntry(
        artifact_id="ART-1", path="/x", artifact_type="checkpoint", status="current"
    )
    a.validate()
    a.artifact_type = "magical"
    with pytest.raises(ValueError):
        a.validate()


def test_claim_entry_strength_vocab():
    c = ClaimEntry(
        claim_id="CLAIM-1",
        claim_text="x",
        claim_strength="hypothesis_generating",
        status="hypothesis_generating",
    )
    c.validate()
    c.claim_strength = "definitive"
    with pytest.raises(ValueError):
        c.validate()


def test_gate_status_name_validated():
    g = GateStatus(name=GateName.LEAKAGE, status="pass")
    g.validate()
    g.name = "unknown_gate"
    with pytest.raises(ValueError):
        g.validate()


def test_orchestration_plan_block_requires_reason():
    plan = OrchestrationPlan(request_summary="x", risk_level="medium", blocked=True, block_reason="")
    with pytest.raises(ValueError):
        plan.validate()


def test_evidence_ref_type_validated():
    e = EvidenceRef(type="artifact", id="ART-1")
    e.validate()
    e.type = "telepathy"
    with pytest.raises(ValueError):
        e.validate()
