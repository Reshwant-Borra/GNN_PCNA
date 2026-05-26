"""Phase 6 — corpus build with mock web backend.

Demonstrates that a literature corpus build runs end-to-end against
injected fake search/fetch tools, with the coverage critic spawning
follow-up searches for any missing category.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

import pytest

from research_os.agents.base import AgentContext
from research_os.autonomous.coverage import CoverageEstimator
from research_os.autonomous.critique import make_coverage_critic, simple_critic
from research_os.autonomous.schemas import CoverageCategory
from research_os.memory.store import MemoryStore, ensure_memory_initialized
from research_os.registries.store import RegistryStore, ensure_registries_initialized


def _categories():
    return [
        CoverageCategory(name="pcna", keywords=["pcna", "aoh1996"], min_items=2),
        CoverageCategory(name="gnn", keywords=["graph neural", "gnn"], min_items=2),
        CoverageCategory(name="md", keywords=["molecular dynamics", "rmsf"], min_items=2),
    ]


def test_coverage_critic_drives_corpus_filling(tmp_path: Path):
    """Start with one item (PCNA), let the coverage critic spawn follow-up
    queries for the remaining categories, simulate ingest, repeat until
    coverage is complete."""
    estimator = CoverageEstimator(_categories())
    items: List[Dict[str, Any]] = [
        {"title": "PCNA pocket study"},
    ]
    fake_db = {
        "graph neural gnn": [
            {"title": "GNN review for proteins"},
            {"title": "Graph Neural Network architectures"},
        ],
        "molecular dynamics rmsf": [
            {"title": "MD RMSF analysis"},
            {"title": "molecular dynamics primer"},
        ],
        "pcna aoh1996": [
            {"title": "AOH1996 binding mechanism"},
        ],
    }
    critic = make_coverage_critic(
        estimator=estimator,
        items_key="collected_items",
        min_score=0.99,
        spawn_tool="web_search",
        spawn_input_template={"source": "pubmed", "limit": 5},
    )

    rounds = 0
    while rounds < 6:
        rounds += 1
        out = critic(plan=None, results=[], ctx_state={"collected_items": list(items)})
        if not out.spawned_steps:
            break
        # Fulfill each spawned query by reading from the fake DB.
        for step in out.spawned_steps:
            q = step.tool_input.get("query", "")
            for kw, hits in fake_db.items():
                if any(t in q for t in kw.split()):
                    items.extend(hits)
    # After filling, coverage should be complete (>=0.99) — and we made
    # progress in a bounded number of rounds.
    assert rounds <= 5
    final = estimator.evaluate(items)
    assert final.score >= 0.99
    assert final.total_items >= 5


def test_full_corpus_flow_with_simple_critic_retries(tmp_path: Path):
    """A corpus-building flow where one search fails and simple_critic
    spawns a retry. This exercises the critique → planner pipeline at
    test-level."""
    from research_os.autonomous.schemas import Plan, Step, StepResult, StepStatus

    s_failed = Step(kind="tool_call", description="search pubmed",
                    tool_name="web_search", tool_input={"query": "PCNA"})
    plan = Plan(steps=[s_failed])
    results = [StepResult(step_id=s_failed.step_id, status=StepStatus.FAILED,
                          error="connection refused")]
    out = simple_critic(plan, results, {})
    assert out.spawned_steps
    retry = out.spawned_steps[0]
    assert retry.tool_name == "web_search"
    assert retry.spawned_by == "simple_critic"
    assert retry.description.startswith("Retry")
