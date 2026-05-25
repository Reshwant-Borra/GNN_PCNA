"""End-to-end Router tests with the semantic backend mocked.

These tests verify the **merge behavior** between the semantic router and the
deterministic keyword guardrail. Each test injects a fake Ollama backend that
returns a specific structured response, then asserts that the final
``OrchestrationPlan`` contains the right agents and routing metadata.

We do not call real Ollama. We do not depend on the actual content of the
prompt the router constructs — the fake backend just returns whatever payload
the test specifies.
"""
from __future__ import annotations

import json
from typing import Optional

import pytest

from research_os.routing.claude_fallback import FlagOnlyFallback
from research_os.routing.router import Router
from research_os.routing.semantic_router import OllamaSemanticRouter


def _make_router_with_response(payload: dict | None, raise_exc: Optional[Exception] = None) -> Router:
    """Build a Router whose semantic backend returns ``payload`` (or raises)."""

    def backend(system: str, user: str, timeout_s: float) -> str:
        if raise_exc is not None:
            raise raise_exc
        return json.dumps(payload or {})

    semantic = OllamaSemanticRouter(repo_root=".", backend=backend)
    return Router(
        repo_root=".",
        semantic_router=semantic,
        claude_fallback=FlagOnlyFallback(),
        enable_semantic=True,
    )


# ────────────────────────────────────────────────────────────────────────────
# The headline bug fix: PubMed/GNN prompt must select literature_web +
# document_knowledge_ingestion + context_source_truth.
# ────────────────────────────────────────────────────────────────────────────

def test_pubmed_prompt_routes_to_literature_doc_ingestion_and_context():
    """Reproduces the user's bug report and verifies the fix."""
    payload = {
        "intent": "literature_research",
        "selected_agents": [
            "context_source_truth",
            "literature_web",
            "document_knowledge_ingestion",
            "provenance_artifacts",
        ],
        "selected_workflow": None,
        "confidence": 0.88,
        "risk_level": "medium",
        "reasoning_summary": "Literature research prompt for GNNs/PubMed",
        "requires_claude_fallback": False,
        "requires_human_approval": False,
    }
    router = _make_router_with_response(payload)
    plan = router.route("Research how Graph Neural Networks work and find PubMed articles on this topic")

    assert "context_source_truth" in plan.selected_agents
    assert "literature_web" in plan.selected_agents
    assert "document_knowledge_ingestion" in plan.selected_agents
    # context_source_truth must be FIRST.
    assert plan.selected_agents[0] == "context_source_truth"
    # Decision should be semantic (high confidence).
    assert plan.routing_decision in ("semantic", "merged")
    assert plan.routing_confidence >= 0.75


def test_md_validation_prompt_routes_to_validation_chain():
    payload = {
        "intent": "md_validation",
        "selected_agents": [
            "context_source_truth", "validation_skeptic", "biological_realism",
            "contradiction_hunter", "paper_claim", "metrics_statistics",
            "provenance_artifacts",
        ],
        "selected_workflow": "md_validation",
        "confidence": 0.92,
        "risk_level": "critical",
        "reasoning_summary": "MD validation with claim implications",
        "requires_claude_fallback": True,
        "requires_human_approval": True,
    }
    router = _make_router_with_response(payload)
    plan = router.route("Did MD validate the cryptic pocket?")

    assert "validation_skeptic" in plan.selected_agents
    assert "biological_realism" in plan.selected_agents
    assert "contradiction_hunter" in plan.selected_agents
    assert "paper_claim" in plan.selected_agents
    assert plan.risk_level == "critical"
    assert plan.human_review_required is True


def test_data_leakage_prompt_routes_to_leakage_chain():
    payload = {
        "intent": "leakage_check",
        "selected_agents": [
            "context_source_truth", "leakage_split", "dataset_integrity",
            "preprocessing_auditor",
        ],
        "selected_workflow": None,
        "confidence": 0.9,
        "risk_level": "high",
        "reasoning_summary": "Leakage audit",
        "requires_claude_fallback": False,
        "requires_human_approval": False,
    }
    router = _make_router_with_response(payload)
    plan = router.route("Is there data leakage in the train/test split?")

    assert "leakage_split" in plan.selected_agents
    assert "dataset_integrity" in plan.selected_agents
    assert "preprocessing_auditor" in plan.selected_agents


def test_claim_or_paper_prompt_routes_to_paper_chain():
    payload = {
        "intent": "claim_audit",
        "selected_agents": [
            "context_source_truth", "paper_claim", "metrics_statistics",
            "validation_skeptic", "biological_realism", "provenance_artifacts",
            "contradiction_hunter", "reviewer_collaboration",
        ],
        "selected_workflow": "claim_audit",
        "confidence": 0.95,
        "risk_level": "critical",
        "reasoning_summary": "Claim audit",
        "requires_claude_fallback": True,
        "requires_human_approval": True,
    }
    router = _make_router_with_response(payload)
    plan = router.route("Audit the paper claims before submission.")

    assert "paper_claim" in plan.selected_agents
    assert "contradiction_hunter" in plan.selected_agents
    assert "reviewer_collaboration" in plan.selected_agents
    assert plan.risk_level == "critical"
    assert plan.human_review_required is True


def test_ambiguous_broad_prompt_selects_multiple_agents():
    """A vague prompt should still result in more than 1 agent.

    The semantic router won't always have an opinion here; the keyword
    fallback still selects context_source_truth at minimum. When the
    semantic router suggests multiple agents, the union is taken.
    """
    payload = {
        "intent": "general",
        "selected_agents": ["context_source_truth", "research_design", "literature_web"],
        "selected_workflow": None,
        "confidence": 0.65,
        "risk_level": "medium",
        "reasoning_summary": "Broad scientific prompt",
        "requires_claude_fallback": False,
        "requires_human_approval": False,
    }
    router = _make_router_with_response(payload)
    plan = router.route("What should we work on next for the PCNA project?")

    assert len(plan.selected_agents) >= 2
    assert plan.selected_agents[0] == "context_source_truth"


# ────────────────────────────────────────────────────────────────────────────
# Fallback behavior
# ────────────────────────────────────────────────────────────────────────────

def test_falls_back_to_keyword_when_ollama_unavailable():
    """When the semantic router raises, we route deterministically + flag."""
    router = _make_router_with_response(None, raise_exc=ConnectionRefusedError("ollama down"))
    plan = router.route("verify the AUROC")

    assert plan.routing_decision == "keyword_only"
    assert plan.requires_claude_fallback is True
    # context_source_truth still first, metrics_statistics still selected by keyword.
    assert plan.selected_agents[0] == "context_source_truth"
    assert "metrics_statistics" in plan.selected_agents


def test_low_confidence_triggers_claude_fallback_flag():
    payload = {
        "intent": "uncertain",
        "selected_agents": ["context_source_truth", "research_design"],
        "selected_workflow": None,
        "confidence": 0.3,
        "risk_level": "low",
        "reasoning_summary": "low conf",
        "requires_claude_fallback": False,
        "requires_human_approval": False,
    }
    router = _make_router_with_response(payload)
    plan = router.route("something ambiguous")
    assert plan.routing_decision == "low_confidence"
    assert plan.requires_claude_fallback is True


def test_high_risk_always_triggers_claude_fallback_flag():
    payload = {
        "intent": "x",
        "selected_agents": ["context_source_truth", "validation_skeptic"],
        "selected_workflow": None,
        "confidence": 0.95,
        "risk_level": "critical",
        "reasoning_summary": "high stakes",
        "requires_claude_fallback": False,
        "requires_human_approval": False,
    }
    router = _make_router_with_response(payload)
    plan = router.route("submit the paper")
    assert plan.requires_claude_fallback is True


def test_semantic_result_unions_with_keyword_agents():
    """When semantic misses an agent the keyword path would catch, the union still includes it.

    Example: a prompt mentioning 'leakage' should always include leakage_split, even
    if semantic forgets it.
    """
    payload = {
        "intent": "training",
        "selected_agents": ["context_source_truth", "model_training"],  # semantic misses leakage_split
        "selected_workflow": None,
        "confidence": 0.9,
        "risk_level": "high",
        "reasoning_summary": "training",
        "requires_claude_fallback": False,
        "requires_human_approval": False,
    }
    router = _make_router_with_response(payload)
    plan = router.route("Train the model and check for leakage in the split.")

    # Both semantic agent AND keyword-derived agents present.
    assert "model_training" in plan.selected_agents
    assert "leakage_split" in plan.selected_agents


# ────────────────────────────────────────────────────────────────────────────
# Decision metadata
# ────────────────────────────────────────────────────────────────────────────

def test_plan_carries_ollama_raw_response_for_transcripts():
    payload = {
        "intent": "literature",
        "selected_agents": ["context_source_truth", "literature_web"],
        "selected_workflow": None,
        "confidence": 0.85,
        "risk_level": "medium",
        "reasoning_summary": "lit search",
        "requires_claude_fallback": False,
        "requires_human_approval": False,
    }
    router = _make_router_with_response(payload)
    plan = router.route("find me a survey paper")
    assert plan.ollama_response_raw is not None
    assert plan.ollama_response_raw.get("intent") == "literature"


def test_routing_decision_label_is_valid():
    """routing_decision must be one of the ROUTING_DECISIONS values."""
    from research_os.schemas.context import ROUTING_DECISIONS

    payload = {
        "intent": "x",
        "selected_agents": ["context_source_truth"],
        "selected_workflow": None,
        "confidence": 0.5,
        "risk_level": "medium",
        "reasoning_summary": "",
        "requires_claude_fallback": False,
        "requires_human_approval": False,
    }
    router = _make_router_with_response(payload)
    plan = router.route("anything")
    assert plan.routing_decision in ROUTING_DECISIONS
