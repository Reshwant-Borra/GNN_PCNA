"""Scientific guardrail tests.

These tests encode the non-negotiable rules from docs/README.md:

- Headline metric invalid until Leakage + Metrics approve.
- Biological claim invalid until Biological Realism + Claim approve.
- Critical skipped tests treated as failure, not pass.
- Stale artifact in paper claim => block.
- Claim upgrade without human approval => block.
- Residue-level n cannot be treated as protein-level n.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from research_os.agents import (
    AgentContext,
    BiologicalRealismAgent,
    ContradictionHunterAgent,
    LeakageSplitAgent,
    MetricsStatisticsAgent,
    PaperClaimAgent,
    ScientificCodeReviewAgent,
    TestingEnvironmentAgent,
    ValidationSkepticAgent,
)
from research_os.routing.context_builder import build_context_packet
from research_os.memory.store import (
    MemoryStore,
    MemoryUpdateProposal,
    apply_memory_update,
    ensure_memory_initialized,
)
from research_os.registries.store import RegistryStore, ensure_registries_initialized
from research_os.schemas.context import ContextPacket
from research_os.schemas.registries import ArtifactEntry, ClaimEntry


@pytest.fixture
def ctx(tmp_path: Path) -> AgentContext:
    mem = MemoryStore(tmp_path / "mem")
    reg = RegistryStore(tmp_path / "reg")
    ensure_memory_initialized(mem)
    ensure_registries_initialized(reg)
    return AgentContext(repo_root=tmp_path, memory_store=mem, registry_store=reg)


def test_leakage_gate_blocks_when_no_split_protocol(ctx):
    packet = ContextPacket(task="train", intents=["split_or_leakage"], risk_level="high")
    out = LeakageSplitAgent(ctx).run(packet)
    assert out.status == "blocked"
    assert any(gu.gate == "leakage" and gu.new_status == "blocked" for gu in out.gate_updates)


def test_leakage_blocks_metric_artifact_without_split_dependency(ctx):
    # Document a split protocol so leakage doesn't pre-block.
    apply_memory_update(
        ctx.memory_store,
        MemoryUpdateProposal(
            target_file="DATASET_REGISTRY.md",
            update_type="add_fact",
            summary="chain-blocked + homology-blocked split with apo/holo separation; feature normalization split-scoped; PDB held out.",
            append_section="chain-blocked + homology-blocked split with apo/holo separation; feature normalization split-scoped; PDB held out; label transfer audited.",
            section_heading="Split protocol",
        ),
        applied_by="test",
    )
    # Append a metric artifact without a split-artifact dep.
    ctx.registry_store.append(
        "artifact_registry",
        ArtifactEntry(
            artifact_id="",
            path="/results/metrics.json",
            artifact_type="metric",
            status="current",
            git_commit="abc",
            command="python eval.py",
            created_at="2026-05-24T00:00:00Z",
        ),
    )
    packet = ContextPacket(task="check metrics", intents=["metric_verification"], risk_level="high")
    out = LeakageSplitAgent(ctx).run(packet)
    assert any("split-artifact dependency" in f.title for f in out.findings)


def test_validation_skeptic_fails_when_inconclusive(ctx):
    packet = ContextPacket(task="check validation", intents=["md_or_validation"], risk_level="high")
    out = ValidationSkepticAgent(ctx).run(packet)
    # Default starter classification is inconclusive.
    assert any(gu.gate == "validation" and gu.new_status == "fail" for gu in out.gate_updates)


def test_biological_realism_flags_strong_claim_without_evidence(ctx):
    ctx.registry_store.append(
        "claim_registry",
        ClaimEntry(
            claim_id="",
            claim_text="We discovered a binding site near AOH1996 contacts.",
            claim_strength="strongly_supported_computationally",
            status="strongly_supported_computationally",
            evidence_for=[],
        ),
    )
    packet = ContextPacket(task="audit claims", intents=["claim_or_paper"], risk_level="high")
    out = BiologicalRealismAgent(ctx).run(packet)
    titles = [f.title for f in out.findings]
    assert any("biologically aggressive wording" in t for t in titles)
    assert any("strongly_supported" in t and "no evidence_for" in t for t in titles)


def test_metrics_agent_flags_auroc_without_auprc(ctx, tmp_path):
    metrics = tmp_path / "results"
    metrics.mkdir()
    metric_file = metrics / "auroc_only_metrics.json"
    metric_file.write_text('{"auroc": 0.91}', encoding="utf-8")
    packet = ContextPacket(task="verify metrics", intents=["metric_verification"], risk_level="high")
    out = MetricsStatisticsAgent(ctx).run(packet)
    assert any("AUPRC" in f.title for f in out.findings)


def test_paper_claim_agent_blocks_disallowed_wording(ctx, tmp_path):
    paper = tmp_path / "manuscript.md"
    paper.write_text(
        "# Results\n\nWe report a validated cryptic pocket on PCNA.\n",
        encoding="utf-8",
    )
    packet = ContextPacket(task="audit manuscript", intents=["claim_or_paper"], risk_level="high")
    out = PaperClaimAgent(ctx).run(packet)
    assert any(
        "validated cryptic pocket" in f.title.lower()
        for f in out.findings
    )


def test_contradiction_hunter_flags_strong_claim_vs_inconclusive_md(ctx):
    ctx.registry_store.append(
        "claim_registry",
        ClaimEntry(
            claim_id="",
            claim_text="GNN validated cryptic pocket discovered.",
            claim_strength="strongly_supported_computationally",
            status="strongly_supported_computationally",
            evidence_for=["MD trajectory"],
        ),
    )
    packet = ContextPacket(task="contradiction hunt", intents=["contradiction_hunt"], risk_level="high")
    out = ContradictionHunterAgent(ctx).run(packet)
    titles = [f.title for f in out.findings]
    assert any("strength conflicts with validation" in t for t in titles)


def test_scientific_code_review_flags_skipped_tests(ctx, tmp_path):
    py = tmp_path / "x.py"
    py.write_text(
        "import pytest\n\n@pytest.mark.skip(reason='disabled')\ndef test_a(): pass\n",
        encoding="utf-8",
    )
    packet = ContextPacket(task="review code", intents=["code_review"], risk_level="medium")
    out = ScientificCodeReviewAgent(ctx).run(packet)
    assert any("skipped test marker" in f.title for f in out.findings)


def test_testing_environment_flags_no_tests_dir(ctx, tmp_path):
    packet = ContextPacket(task="run tests", intents=["code_review"], risk_level="medium")
    out = TestingEnvironmentAgent(ctx).run(packet)
    assert any("No tests/ directory" in f.title for f in out.findings)


def test_scientific_audit_context_includes_research_base(ctx):
    rb = ctx.repo_root / "docs" / "research_base"
    for rel in (
        "decisions/DECISION_REGISTRY.md",
        "assumptions/ASSUMPTION_REGISTRY.md",
        "inferences/INFERENCE_REGISTRY.md",
        "project/KNOWN_LIMITATIONS.md",
        "md/MD_OBJECTIVE.md",
        "md/POCKET_OPENING_CRITERIA.md",
        "md/POSITIVE_CONTROL.md",
        "sources/SOURCE_REGISTRY.md",
        "questions/OPEN_QUESTIONS.md",
    ):
        path = rb / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# test\n", encoding="utf-8")
    packet = build_context_packet(
        task="audit suspected methodology issue",
        intents=["contradiction_hunt", "md_or_validation"],
        risk_level="high",
        memory_store=ctx.memory_store,
        registry_store=ctx.registry_store,
    )
    assert any(p.endswith("docs/research_base/decisions/DECISION_REGISTRY.md") for p in packet.repo_files)
    assert any(p.endswith("docs/research_base/assumptions/ASSUMPTION_REGISTRY.md") for p in packet.repo_files)
    assert any(p.endswith("docs/research_base/inferences/INFERENCE_REGISTRY.md") for p in packet.repo_files)
    assert any(p.endswith("docs/research_base/project/KNOWN_LIMITATIONS.md") for p in packet.repo_files)


def test_documented_choice_is_not_bug_but_remains_challengeable(tmp_path):
    rb = tmp_path / "docs" / "research_base"
    (rb / "decisions").mkdir(parents=True)
    (rb / "assumptions").mkdir(parents=True)
    (rb / "inferences").mkdir(parents=True)
    (rb / "project").mkdir(parents=True)
    (rb / "decisions" / "DECISION_REGISTRY.md").write_text(
        "DECISION-CLUSTER: DBSCAN eps=6.0 and min_samples=3 are the frozen extraction choice.\n",
        encoding="utf-8",
    )
    (rb / "assumptions" / "ASSUMPTION_REGISTRY.md").write_text(
        "ASSUMPTION-CLUSTER: DBSCAN eps=6.0 is a methodological assumption, not a source fact.\n",
        encoding="utf-8",
    )
    (rb / "inferences" / "INFERENCE_REGISTRY.md").write_text("", encoding="utf-8")
    (rb / "project" / "KNOWN_LIMITATIONS.md").write_text("", encoding="utf-8")
    agent = ContradictionHunterAgent(AgentContext(repo_root=tmp_path))

    documented = agent.classify_suspected_scientific_issue("DBSCAN eps=6.0 min_samples=3")
    assert documented["classification"] == "documented_methodological_choice"
    assert documented["bug_status"] == "not_a_software_bug_by_default"

    challenged = agent.classify_suspected_scientific_issue(
        "DBSCAN eps=6.0 min_samples=3",
        contradictory_evidence="Fragments known labeled pockets on independent proteins.",
    )
    assert challenged["classification"] == "scientific_risk_or_methodology_contradiction"
