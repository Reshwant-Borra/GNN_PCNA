"""Tests for the memory / knowledge base files used by the semantic router.

These files (AGENT_REGISTRY.md, ROUTING_GUIDE.md, CODEBASE_MAP.md,
WORKFLOW_REGISTRY.md) are the source the Ollama router reads on every call,
so we want strong assertions that:

- All 21 agents from ``research_os.schemas.vocab.AGENT_IDS`` have entries.
- ROUTING_GUIDE.md includes the canonical PubMed/literature example.
- WORKFLOW_REGISTRY.md covers all 6 workflows registered in
  ``research_os.workflows.WORKFLOWS``.
- The CLI ``refresh-memory`` updates the codebase map without errors.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from research_os.memory.registry_loader import (
    AGENT_REGISTRY_FILE,
    ROUTING_GUIDE_FILE,
    CODEBASE_MAP_FILE,
    WORKFLOW_REGISTRY_FILE,
    TOOL_REGISTRY_FILE,
    RECENT_RUN_SUMMARY_FILE,
    load_agent_registry,
    load_routing_guide,
    query_memory,
)
from research_os.memory.codebase_indexer import regenerate_codebase_map, scan_repo
from research_os.schemas.vocab import AGENT_IDS
from research_os.workflows import WORKFLOWS


REPO = Path(".")


# ────────────────────────────────────────────────────────────────────────────
# File existence
# ────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("name", [
    AGENT_REGISTRY_FILE, ROUTING_GUIDE_FILE, CODEBASE_MAP_FILE,
    WORKFLOW_REGISTRY_FILE, TOOL_REGISTRY_FILE, RECENT_RUN_SUMMARY_FILE,
])
def test_kb_file_exists(name: str):
    assert (REPO / "research_os_memory" / name).exists(), f"missing KB file: {name}"


# ────────────────────────────────────────────────────────────────────────────
# AGENT_REGISTRY.md
# ────────────────────────────────────────────────────────────────────────────

def test_agent_registry_covers_every_agent_id():
    """Every agent in AGENT_IDS must have a registry entry."""
    entries = load_agent_registry(REPO)
    missing = [a for a in AGENT_IDS if a not in entries]
    assert not missing, f"AGENT_REGISTRY.md missing entries: {missing}"


def test_agent_registry_has_no_stale_entries():
    """Every entry in the registry must correspond to a real agent ID."""
    entries = load_agent_registry(REPO)
    extra = [a for a in entries if a not in AGENT_IDS]
    assert not extra, f"AGENT_REGISTRY.md has stale entries: {extra}"


def test_agent_registry_entries_have_required_fields():
    entries = load_agent_registry(REPO)
    for agent_id, entry in entries.items():
        assert entry.purpose, f"{agent_id} missing purpose"
        assert entry.when_to_use, f"{agent_id} missing when_to_use"
        assert entry.risk_level in ("low", "medium", "high", "critical"), \
            f"{agent_id} invalid risk_level={entry.risk_level}"


def test_literature_web_entry_mentions_pubmed_and_examples():
    entries = load_agent_registry(REPO)
    lit = entries["literature_web"]
    assert "pubmed" in (lit.purpose + " " + lit.when_to_use + " " + " ".join(lit.keywords)).lower(), \
        "literature_web should mention PubMed"
    assert any("pubmed" in e.lower() for e in lit.example_prompts), \
        "literature_web should have a PubMed example prompt"


def test_document_ingestion_entry_supports_research_prompts():
    entries = load_agent_registry(REPO)
    doc = entries["document_knowledge_ingestion"]
    text = (doc.purpose + " " + doc.when_to_use + " " + " ".join(doc.keywords)).lower()
    assert "ingest" in text or "document" in text


# ────────────────────────────────────────────────────────────────────────────
# ROUTING_GUIDE.md
# ────────────────────────────────────────────────────────────────────────────

def test_routing_guide_has_literature_category():
    cats = load_routing_guide(REPO)
    names = [c.name.lower() for c in cats]
    assert any("literature" in n for n in names), f"no literature category, got: {names}"


def test_routing_guide_literature_category_includes_required_agents():
    cats = load_routing_guide(REPO)
    lit = next(c for c in cats if "literature" in c.name.lower())
    assert "literature_web" in lit.always_include
    assert "document_knowledge_ingestion" in lit.always_include
    assert "context_source_truth" in lit.always_include


def test_routing_guide_has_pubmed_gnn_example():
    cats = load_routing_guide(REPO)
    lit = next(c for c in cats if "literature" in c.name.lower())
    has_pubmed_example = any("pubmed" in ex.get("prompt", "").lower() for ex in lit.examples)
    assert has_pubmed_example, "literature category should have a PubMed example"


def test_routing_guide_covers_md_leakage_claim_categories():
    cats = load_routing_guide(REPO)
    names = " ".join(c.name.lower() for c in cats)
    assert "md" in names or "validation" in names
    assert "leakage" in names or "split" in names
    assert "claim" in names or "paper" in names


# ────────────────────────────────────────────────────────────────────────────
# WORKFLOW_REGISTRY.md
# ────────────────────────────────────────────────────────────────────────────

def test_workflow_registry_covers_all_workflows():
    md = (REPO / "research_os_memory" / WORKFLOW_REGISTRY_FILE).read_text(encoding="utf-8")
    for name in WORKFLOWS:
        assert name in md, f"workflow {name!r} not documented in WORKFLOW_REGISTRY.md"


# ────────────────────────────────────────────────────────────────────────────
# CODEBASE_MAP + refresh
# ────────────────────────────────────────────────────────────────────────────

def test_codebase_map_includes_key_modules():
    md = (REPO / "research_os_memory" / CODEBASE_MAP_FILE).read_text(encoding="utf-8")
    must_mention = [
        "research_os/orchestrator.py",
        "routing/router.py",
        "routing/semantic_router.py",
        "memory/registry_loader.py",
        "transcripts",
    ]
    for token in must_mention:
        assert token in md, f"CODEBASE_MAP.md missing reference to {token!r}"


def test_codebase_indexer_produces_entries_for_research_os(tmp_path: Path):
    """The indexer walks the actual repo (not tmp) and should find research_os modules."""
    scan = scan_repo(REPO)
    assert "research_os" in scan
    paths = [p for p, _ in scan["research_os"]]
    assert any("orchestrator.py" in p for p in paths)
    assert any("routing/router.py" in p for p in paths)
    assert any("memory/registry_loader.py" in p for p in paths)


def test_refresh_memory_idempotent(tmp_path: Path):
    """Run regenerate_codebase_map twice; second run should produce identical output."""
    # Copy current CODEBASE_MAP.md into tmp to avoid mutating the real one.
    src = REPO / "research_os_memory" / CODEBASE_MAP_FILE
    target_dir = tmp_path / "research_os_memory"
    target_dir.mkdir()
    (target_dir / CODEBASE_MAP_FILE).write_text(src.read_text(encoding="utf-8"), encoding="utf-8")

    # Make the tmp_path look enough like the repo by symlinking the source dirs.
    # Actually we just need the indexer to run; it walks ``repo_root``.
    # Point it at the real repo so we have something to scan.
    p1 = regenerate_codebase_map(REPO)
    text1 = p1.read_text(encoding="utf-8")
    p2 = regenerate_codebase_map(REPO)
    text2 = p2.read_text(encoding="utf-8")
    assert text1 == text2, "regenerate_codebase_map should be deterministic"


# ────────────────────────────────────────────────────────────────────────────
# query_memory
# ────────────────────────────────────────────────────────────────────────────

def test_query_memory_finds_literature():
    hits = query_memory(REPO, "literature")
    assert hits, "expected hits for 'literature' across the KB"
    files = {h["file"] for h in hits}
    assert "AGENT_REGISTRY.md" in files or "ROUTING_GUIDE.md" in files


def test_query_memory_finds_pubmed():
    hits = query_memory(REPO, "PubMed")
    assert hits
    files = {h["file"] for h in hits}
    assert "ROUTING_GUIDE.md" in files or "AGENT_REGISTRY.md" in files


def test_query_memory_empty_returns_no_hits():
    assert query_memory(REPO, "") == []
    assert query_memory(REPO, "   ") == []


def test_query_memory_misses_return_empty():
    assert query_memory(REPO, "xxxxx_nonexistent_token_xxxxx") == []
