"""Unit tests for OllamaSemanticRouter.

We never call real Ollama from tests — every test injects a fake chat backend.
This guarantees deterministic behavior and means the suite runs without any
external dependency.
"""
from __future__ import annotations

import json
from typing import Optional

import pytest

from research_os.routing.semantic_router import (
    OllamaSemanticRouter,
    SemanticRouterResult,
)


def _make_router(repo_root, response_text: Optional[str] = None, raise_exc: Optional[Exception] = None):
    """Build a router with a fake backend that returns ``response_text`` or raises."""

    def backend(system: str, user: str, timeout_s: float) -> str:
        if raise_exc is not None:
            raise raise_exc
        return response_text or ""

    return OllamaSemanticRouter(repo_root=repo_root, backend=backend)


def test_returns_result_when_backend_returns_valid_json(tmp_path):
    # Need the KB files to exist for the router to load them. Use the real repo.
    repo = "."
    payload = {
        "intent": "literature_research",
        "selected_agents": [
            "context_source_truth", "literature_web", "document_knowledge_ingestion",
            "provenance_artifacts",
        ],
        "selected_workflow": None,
        "confidence": 0.85,
        "risk_level": "medium",
        "reasoning_summary": "PubMed literature search",
        "requires_claude_fallback": False,
        "requires_human_approval": False,
    }
    router = _make_router(repo, response_text=json.dumps(payload))
    result = router.route("Research how GNNs work and find PubMed articles")

    assert result is not None
    assert isinstance(result, SemanticRouterResult)
    assert result.selected_agents[0] == "context_source_truth"
    assert "literature_web" in result.selected_agents
    assert "document_knowledge_ingestion" in result.selected_agents
    assert result.confidence == 0.85
    assert result.risk_level == "medium"
    assert result.intent == "literature_research"


def test_returns_none_when_backend_unreachable():
    router = _make_router(".", raise_exc=ConnectionRefusedError("ollama down"))
    assert router.route("anything") is None


def test_returns_none_when_backend_returns_non_json():
    router = _make_router(".", response_text="not json at all, just prose")
    assert router.route("anything") is None


def test_handles_code_fence_wrapped_json():
    payload = {
        "intent": "leakage_check",
        "selected_agents": ["context_source_truth", "leakage_split", "dataset_integrity"],
        "confidence": 0.9,
        "risk_level": "critical",
        "reasoning_summary": "leakage",
        "requires_claude_fallback": True,
        "requires_human_approval": False,
    }
    fenced = "```json\n" + json.dumps(payload) + "\n```"
    router = _make_router(".", response_text=fenced)
    result = router.route("did we check leakage?")
    assert result is not None
    assert "leakage_split" in result.selected_agents
    assert result.risk_level == "critical"


def test_invalid_agent_ids_are_dropped_but_valid_kept():
    payload = {
        "intent": "literature",
        "selected_agents": [
            "context_source_truth",
            "literature_web",
            "this_is_not_a_real_agent",   # should be dropped
            "another_fake",                # should be dropped
            "paper_claim",
        ],
        "confidence": 0.8,
        "risk_level": "medium",
        "reasoning_summary": "",
        "requires_claude_fallback": False,
        "requires_human_approval": False,
    }
    router = _make_router(".", response_text=json.dumps(payload))
    result = router.route("find papers")
    assert result is not None
    # Only valid IDs remain.
    assert "this_is_not_a_real_agent" not in result.selected_agents
    assert "another_fake" not in result.selected_agents
    assert "literature_web" in result.selected_agents
    assert "paper_claim" in result.selected_agents


def test_returns_none_when_all_agents_are_invalid():
    payload = {
        "intent": "garbage",
        "selected_agents": ["foo", "bar", "baz"],
        "confidence": 0.5,
        "risk_level": "low",
        "reasoning_summary": "",
        "requires_claude_fallback": False,
        "requires_human_approval": False,
    }
    router = _make_router(".", response_text=json.dumps(payload))
    assert router.route("anything") is None


def test_context_source_truth_is_always_first():
    payload = {
        "intent": "metric",
        "selected_agents": ["metrics_statistics", "leakage_split", "context_source_truth"],
        "confidence": 0.9,
        "risk_level": "high",
        "reasoning_summary": "",
        "requires_claude_fallback": False,
        "requires_human_approval": False,
    }
    router = _make_router(".", response_text=json.dumps(payload))
    result = router.route("verify metrics")
    assert result is not None
    assert result.selected_agents[0] == "context_source_truth"


def test_confidence_is_clamped_to_unit_interval():
    payload = {
        "intent": "x",
        "selected_agents": ["context_source_truth"],
        "confidence": 2.5,   # > 1
        "risk_level": "medium",
        "reasoning_summary": "",
        "requires_claude_fallback": False,
        "requires_human_approval": False,
    }
    router = _make_router(".", response_text=json.dumps(payload))
    result = router.route("x")
    assert result is not None
    assert result.confidence == 1.0


def test_invalid_risk_falls_back_to_medium():
    payload = {
        "intent": "x",
        "selected_agents": ["context_source_truth"],
        "confidence": 0.5,
        "risk_level": "yolo",
        "reasoning_summary": "",
        "requires_claude_fallback": False,
        "requires_human_approval": False,
    }
    router = _make_router(".", response_text=json.dumps(payload))
    result = router.route("x")
    assert result is not None
    assert result.risk_level == "medium"


def test_empty_message_returns_none():
    router = _make_router(".", response_text="{}")
    assert router.route("") is None
    assert router.route("   ") is None
