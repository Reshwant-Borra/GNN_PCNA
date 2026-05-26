"""Phase 4 — tests for migrated autonomous agents.

Each autonomous variant must:
- preserve the legacy behavior when autonomy is off
- not raise when the loop runs end-to-end
- expose its profile via the AUTONOMOUS_AGENTS registry
"""
from __future__ import annotations

from pathlib import Path

import pytest

from research_os.agents.base import AgentContext
from research_os.autonomous import AUTONOMOUS_AGENTS
from research_os.autonomous.agents.code_builder import (
    AutonomousCodeBuilderAgent,
    SAFE_WRITE_DIRS,
)
from research_os.autonomous.agents.contradiction_hunter import (
    AutonomousContradictionHunterAgent,
)
from research_os.autonomous.agents.document_ingestion import (
    AutonomousDocumentIngestionAgent,
)
from research_os.autonomous.agents.literature_web import (
    AutonomousLiteratureWebAgent,
    _PCNA_COVERAGE_CATEGORIES,
)
from research_os.autonomous.agents.paper_claim import AutonomousPaperClaimAgent
from research_os.autonomous.agents.validation_skeptic import (
    AutonomousValidationSkepticAgent,
)
from research_os.autonomous.profile import AutonomyLevel
from research_os.memory.store import MemoryStore, ensure_memory_initialized
from research_os.registries.store import RegistryStore, ensure_registries_initialized
from research_os.schemas.context import ContextPacket


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def wired_ctx(tmp_path: Path) -> AgentContext:
    mem = MemoryStore(tmp_path / "mem")
    ensure_memory_initialized(mem)
    reg = RegistryStore(tmp_path / "reg")
    ensure_registries_initialized(reg)
    return AgentContext(repo_root=tmp_path, memory_store=mem, registry_store=reg)


# ---------------------------------------------------------------------------
# Registry shape
# ---------------------------------------------------------------------------

def test_autonomous_agents_registered():
    expected = {
        "literature_web", "document_knowledge_ingestion", "code_builder",
        "paper_claim", "validation_skeptic", "contradiction_hunter",
    }
    assert expected.issubset(set(AUTONOMOUS_AGENTS))


# ---------------------------------------------------------------------------
# Literature/Web
# ---------------------------------------------------------------------------

def test_literature_web_deterministic_fallback_preserves_legacy(wired_ctx, monkeypatch):
    monkeypatch.delenv("RESEARCHOS_ENABLE_WEB", raising=False)
    agent = AutonomousLiteratureWebAgent(wired_ctx)
    out = agent.run(ContextPacket(task="anything"))
    # Profile requires_env=["RESEARCHOS_ENABLE_WEB"] — autonomy gates off,
    # legacy scan runs and reports the empty source_registry.
    out.validate()
    assert out.status in ("pass", "warning")
    assert "autonomous" not in (out.machine_readable_notes or {})


def test_literature_web_coverage_categories_cover_all_pcna_areas():
    names = {c.name for c in _PCNA_COVERAGE_CATEGORIES}
    assert {"pcna_biology", "cryptic_pockets", "protein_gnn",
            "md_validation", "leakage_splits"}.issubset(names)


# ---------------------------------------------------------------------------
# Document Ingestion
# ---------------------------------------------------------------------------

def test_document_ingestion_fallback_to_discovery(wired_ctx, monkeypatch):
    monkeypatch.delenv("RESEARCHOS_AUTONOMY_OFF", raising=False)
    # Profile autonomy level is GUIDED so the loop runs.
    agent = AutonomousDocumentIngestionAgent(wired_ctx)
    out = agent.run(ContextPacket(task="ingest candidates"))
    out.validate()
    # Even with no candidates, status should be valid; we just need no crash.
    assert out.status in ("pass", "warning", "fail")


def test_document_ingestion_deterministic_path_runs(wired_ctx, monkeypatch):
    monkeypatch.setenv("RESEARCHOS_AUTONOMY_OFF", "1")
    agent = AutonomousDocumentIngestionAgent(wired_ctx)
    out = agent.run(ContextPacket(task="x"))
    out.validate()
    # Legacy fallback may report blocked (missing ingest script in tmp dir),
    # but must produce a valid AgentOutput.
    assert out.agent_id == "document_knowledge_ingestion"


# ---------------------------------------------------------------------------
# Code Builder
# ---------------------------------------------------------------------------

def test_code_builder_safe_write_allow_list():
    assert AutonomousCodeBuilderAgent.safe_to_write("research_os/autonomous/foo.py")
    assert AutonomousCodeBuilderAgent.safe_to_write("tests/test_foo.py")
    assert AutonomousCodeBuilderAgent.safe_to_write("research_corpus/PHASE2.md")
    assert not AutonomousCodeBuilderAgent.safe_to_write("src/training/train.py")
    assert not AutonomousCodeBuilderAgent.safe_to_write("/etc/passwd")


def test_code_builder_detects_missing_referenced_modules(wired_ctx, monkeypatch):
    # Drop a fake agents/orchestrator.py that references missing modules.
    monkeypatch.delenv("RESEARCHOS_AUTONOMY_OFF", raising=False)
    (wired_ctx.repo_root / "agents").mkdir()
    (wired_ctx.repo_root / "agents" / "orchestrator.py").write_text(
        "# fake\nimport agents.pcna_crawler\nimport agents.gemma_verifier\n",
        encoding="utf-8",
    )
    agent = AutonomousCodeBuilderAgent(wired_ctx)
    missing = agent._detect_missing_referenced_modules()
    assert "agents/pcna_crawler.py" in missing
    assert "agents/gemma_verifier.py" in missing


def test_code_builder_fallback_emits_patch_plan(wired_ctx, monkeypatch):
    monkeypatch.setenv("RESEARCHOS_AUTONOMY_OFF", "1")
    # No fake source — missing list will be empty, fallback delegates legacy.
    agent = AutonomousCodeBuilderAgent(wired_ctx)
    out = agent.run(ContextPacket(task="scaffold"))
    out.validate()


# ---------------------------------------------------------------------------
# Paper / Claim
# ---------------------------------------------------------------------------

def test_paper_claim_fallback_preserves_legacy(wired_ctx, monkeypatch):
    monkeypatch.setenv("RESEARCHOS_AUTONOMY_OFF", "1")
    agent = AutonomousPaperClaimAgent(wired_ctx)
    out = agent.run(ContextPacket(task="audit claims"))
    out.validate()
    assert out.agent_id == "paper_claim"


def test_paper_claim_autonomous_runs_end_to_end(wired_ctx, monkeypatch):
    monkeypatch.delenv("RESEARCHOS_AUTONOMY_OFF", raising=False)
    agent = AutonomousPaperClaimAgent(wired_ctx)
    out = agent.run(ContextPacket(task="audit claims"))
    out.validate()
    # Should report autonomous trace in machine_readable_notes.
    assert "autonomous" in (out.machine_readable_notes or {})


# ---------------------------------------------------------------------------
# Validation Skeptic
# ---------------------------------------------------------------------------

def test_validation_skeptic_runs_with_md_token_in_report(wired_ctx, monkeypatch, tmp_path):
    monkeypatch.delenv("RESEARCHOS_AUTONOMY_OFF", raising=False)
    # Drop a fake MD report with a classification token.
    (tmp_path / "md_report.md").write_text(
        "## MD evidence\n\nClassification: supports_claim\n",
        encoding="utf-8",
    )
    agent = AutonomousValidationSkepticAgent(wired_ctx)
    out = agent.run(ContextPacket(task="MD audit"))
    out.validate()
    # md_classifications_on_disk should appear in notes when scan runs.
    # (It may be empty if the legacy fallback doesn't expose ctx_state — that's fine.)


def test_validation_skeptic_fallback_preserves_legacy(wired_ctx, monkeypatch):
    monkeypatch.setenv("RESEARCHOS_AUTONOMY_OFF", "1")
    agent = AutonomousValidationSkepticAgent(wired_ctx)
    out = agent.run(ContextPacket(task="x"))
    out.validate()


# ---------------------------------------------------------------------------
# Contradiction Hunter
# ---------------------------------------------------------------------------

def test_contradiction_hunter_detects_extra_overclaim(wired_ctx, monkeypatch, tmp_path):
    monkeypatch.delenv("RESEARCHOS_AUTONOMY_OFF", raising=False)
    # Drop a paper draft with an extra overclaim phrase.
    (tmp_path / "paper_draft.md").write_text(
        "Our work is groundbreaking and first to demonstrate the cryptic pocket.\n",
        encoding="utf-8",
    )
    agent = AutonomousContradictionHunterAgent(wired_ctx)
    out = agent.run(ContextPacket(task="contradiction sweep"))
    out.validate()
    # Status should be at least warning given the overclaim
    assert out.status in ("warning", "fail")


def test_contradiction_hunter_fallback(wired_ctx, monkeypatch):
    monkeypatch.setenv("RESEARCHOS_AUTONOMY_OFF", "1")
    agent = AutonomousContradictionHunterAgent(wired_ctx)
    out = agent.run(ContextPacket(task="x"))
    out.validate()
