"""Deterministic regression tests for the 10 critical routing behaviors.

These tests pin the *contract* between the router (Ollama + keyword merge)
and the rest of the system. Each test injects a fake Ollama backend that
emits a structured response a healthy router *should* produce — we then
verify the merge logic + keyword guardrail produce the final selection,
risk level, and approval flags the user requires.

Real Ollama drift is caught by ``python -m research_os routing-eval``
(the model-level evaluator). This file catches contract drift.

Cases covered (per upgrade spec):
  1. PubMed/literature → literature_web
  2. Data leakage → leakage_split
  3. MD validation → validation_skeptic + biological_realism
  4. Claim wording → paper_claim + contradiction_hunter
  5. Compute/cloud/GPU → compute_planning + human_review (if expensive)
  6. Figure/poster/visual → visual_evidence
  7. "Can we say this?" → claim + validation + contradiction agents
  8. "Why did this fail?" → context_source_truth + provenance_artifacts
  9. Broad research prompts → multiple agents
 10. Dangerous/destructive prompts → human_review_required=True (no silent execute)
"""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

import pytest

from research_os.routing.claude_fallback import FlagOnlyFallback
from research_os.routing.router import Router
from research_os.routing.semantic_router import OllamaSemanticRouter


# ────────────────────────────────────────────────────────────────────────────
# Helpers
# ────────────────────────────────────────────────────────────────────────────

def _router_returning(payload: Dict[str, Any]) -> Router:
    """Build a Router whose fake Ollama backend always returns ``payload``."""

    def backend(system: str, user: str, timeout_s: float) -> str:
        return json.dumps(payload)

    semantic = OllamaSemanticRouter(repo_root=".", backend=backend)
    return Router(
        repo_root=".",
        semantic_router=semantic,
        claude_fallback=FlagOnlyFallback(),
        enable_semantic=True,
    )


def _assert_includes(plan_agents: List[str], required: List[str]) -> None:
    missing = [a for a in required if a not in plan_agents]
    assert not missing, f"plan missing required agents: {missing} (got {plan_agents})"


# ────────────────────────────────────────────────────────────────────────────
# 1. PubMed / literature → literature_web
# ────────────────────────────────────────────────────────────────────────────

def test_regression_1_pubmed_routes_to_literature_web():
    payload = {
        "intent": "literature_research",
        "selected_agents": [
            "context_source_truth", "literature_web", "document_knowledge_ingestion",
            "provenance_artifacts",
        ],
        "selected_workflow": None,
        "confidence": 0.9,
        "risk_level": "medium",
        "reasoning_summary": "literature query",
        "requires_claude_fallback": False,
        "requires_human_approval": False,
    }
    plan = _router_returning(payload).route(
        "Find PubMed articles on graph neural networks for protein binding"
    )
    _assert_includes(plan.selected_agents, ["context_source_truth", "literature_web"])


# ────────────────────────────────────────────────────────────────────────────
# 2. Data leakage → leakage_split
# ────────────────────────────────────────────────────────────────────────────

def test_regression_2_leakage_routes_to_leakage_split():
    payload = {
        "intent": "leakage_audit",
        "selected_agents": [
            "context_source_truth", "leakage_split", "dataset_integrity",
            "preprocessing_auditor",
        ],
        "confidence": 0.9,
        "risk_level": "high",
        "reasoning_summary": "leakage audit",
        "requires_claude_fallback": False,
        "requires_human_approval": False,
    }
    plan = _router_returning(payload).route(
        "Check the train/test split for homology leakage"
    )
    _assert_includes(plan.selected_agents, ["context_source_truth", "leakage_split"])
    # Also the keyword guardrail recognizes leakage as high-risk.
    assert plan.risk_level in ("high", "critical")


# ────────────────────────────────────────────────────────────────────────────
# 3. MD validation → validation_skeptic + biological_realism
# ────────────────────────────────────────────────────────────────────────────

def test_regression_3_md_validation_routes_to_skeptic_and_realism():
    payload = {
        "intent": "md_validation",
        "selected_agents": [
            "context_source_truth", "validation_skeptic", "biological_realism",
            "metrics_statistics", "provenance_artifacts",
        ],
        "confidence": 0.9,
        "risk_level": "high",
        "reasoning_summary": "MD interpretation",
        "requires_claude_fallback": False,
        "requires_human_approval": False,
    }
    plan = _router_returning(payload).route(
        "Interpret the RMSF trajectories from last week's MD run"
    )
    _assert_includes(plan.selected_agents, [
        "context_source_truth", "validation_skeptic", "biological_realism",
    ])


# ────────────────────────────────────────────────────────────────────────────
# 4. Claim wording → paper_claim + contradiction_hunter
# ────────────────────────────────────────────────────────────────────────────

def test_regression_4_claim_wording_routes_to_paper_claim_and_contradiction():
    payload = {
        "intent": "claim_audit",
        "selected_agents": [
            "context_source_truth", "paper_claim", "metrics_statistics",
            "validation_skeptic", "biological_realism", "contradiction_hunter",
            "reviewer_collaboration",
        ],
        "confidence": 0.92,
        "risk_level": "critical",
        "reasoning_summary": "claim audit",
        "requires_claude_fallback": True,
        "requires_human_approval": False,
    }
    plan = _router_returning(payload).route(
        "Audit the paper claims for disallowed wording"
    )
    _assert_includes(plan.selected_agents, ["paper_claim", "contradiction_hunter"])


# ────────────────────────────────────────────────────────────────────────────
# 5. Compute/cloud/GPU → compute_planning (+ human approval if expensive)
# ────────────────────────────────────────────────────────────────────────────

def test_regression_5a_compute_routes_to_compute_planning():
    payload = {
        "intent": "compute_planning",
        "selected_agents": [
            "context_source_truth", "compute_planning", "validation_skeptic",
        ],
        "confidence": 0.9,
        "risk_level": "medium",
        "reasoning_summary": "compute budget",
        "requires_claude_fallback": False,
        "requires_human_approval": False,
    }
    plan = _router_returning(payload).route("How much GPU time does training take?")
    _assert_includes(plan.selected_agents, ["compute_planning"])


def test_regression_5b_expensive_compute_requires_human_review():
    payload = {
        "intent": "compute_planning",
        "selected_agents": [
            "context_source_truth", "compute_planning", "validation_skeptic",
        ],
        "confidence": 0.95,
        "risk_level": "high",
        "reasoning_summary": "expensive cloud run",
        "requires_claude_fallback": True,
        "requires_human_approval": True,
    }
    plan = _router_returning(payload).route(
        "Spin up 5 cloud GPU nodes to run 100ns MD trajectories"
    )
    _assert_includes(plan.selected_agents, ["compute_planning"])
    # Either the semantic router or the keyword human_review path should flag it.
    assert plan.human_review_required, "expensive compute should require human review"
    assert plan.requires_claude_fallback


# ────────────────────────────────────────────────────────────────────────────
# 6. Figure/poster/visual → visual_evidence
# ────────────────────────────────────────────────────────────────────────────

def test_regression_6_figure_routes_to_visual_evidence():
    payload = {
        "intent": "figure_generation",
        "selected_agents": [
            "context_source_truth", "visual_evidence", "metrics_statistics",
            "paper_claim", "provenance_artifacts",
        ],
        "confidence": 0.9,
        "risk_level": "medium",
        "reasoning_summary": "figure generation",
        "requires_claude_fallback": False,
        "requires_human_approval": False,
    }
    plan = _router_returning(payload).route(
        "Generate Figure 3 with bootstrap confidence intervals"
    )
    _assert_includes(plan.selected_agents, ["visual_evidence"])


# ────────────────────────────────────────────────────────────────────────────
# 7. "Can we say this?" → claim + validation + contradiction
# ────────────────────────────────────────────────────────────────────────────

def test_regression_7_can_we_say_routes_to_claim_validation_contradiction():
    payload = {
        "intent": "claim_audit",
        "selected_agents": [
            "context_source_truth", "paper_claim", "validation_skeptic",
            "biological_realism", "contradiction_hunter", "metrics_statistics",
            "provenance_artifacts", "reviewer_collaboration",
        ],
        "confidence": 0.95,
        "risk_level": "critical",
        "reasoning_summary": "claim wording requires evidence",
        "requires_claude_fallback": True,
        "requires_human_approval": True,
    }
    plan = _router_returning(payload).route(
        "Can we say MD validated the cryptic pocket?"
    )
    _assert_includes(plan.selected_agents, [
        "paper_claim", "validation_skeptic", "contradiction_hunter",
    ])
    assert plan.requires_claude_fallback, "claim wording prompts should flag claude fallback"
    assert plan.human_review_required, "claim upgrade prompts should require human review"


# ────────────────────────────────────────────────────────────────────────────
# 8. "Why did this fail?" → context_source_truth + provenance_artifacts
# ────────────────────────────────────────────────────────────────────────────

def test_regression_8_failure_debug_routes_to_context_and_provenance():
    payload = {
        "intent": "debug",
        "selected_agents": [
            "context_source_truth", "provenance_artifacts", "contradiction_hunter",
            "testing_environment",
        ],
        "confidence": 0.85,
        "risk_level": "medium",
        "reasoning_summary": "debug query",
        "requires_claude_fallback": False,
        "requires_human_approval": False,
    }
    plan = _router_returning(payload).route(
        "Why did the last training run fail?"
    )
    _assert_includes(plan.selected_agents, ["context_source_truth", "provenance_artifacts"])


# ────────────────────────────────────────────────────────────────────────────
# 9. Broad research prompts → multiple agents
# ────────────────────────────────────────────────────────────────────────────

def test_regression_9_broad_research_selects_multiple_agents():
    payload = {
        "intent": "research_design",
        "selected_agents": [
            "context_source_truth", "research_design", "literature_web",
            "biological_realism",
        ],
        "confidence": 0.8,
        "risk_level": "medium",
        "reasoning_summary": "broad scientific question",
        "requires_claude_fallback": False,
        "requires_human_approval": False,
    }
    plan = _router_returning(payload).route(
        "What's the most important experiment for the PCNA project next?"
    )
    assert len(plan.selected_agents) >= 3, (
        f"broad research should select multiple agents (got {plan.selected_agents})"
    )
    assert plan.selected_agents[0] == "context_source_truth"


# ────────────────────────────────────────────────────────────────────────────
# 10. Dangerous/destructive prompts → human review required, no silent execute
# ────────────────────────────────────────────────────────────────────────────

def test_regression_10_destructive_requires_human_review():
    """A destructive prompt must surface a human approval requirement even if
    the LLM said it was safe — the keyword guardrail (``requires_human_review``)
    is the deterministic backstop."""
    payload = {
        "intent": "submission",
        "selected_agents": [
            "context_source_truth", "paper_claim", "contradiction_hunter",
            "reviewer_collaboration",
        ],
        "confidence": 0.9,
        "risk_level": "high",
        "reasoning_summary": "submission prep",
        "requires_claude_fallback": False,
        "requires_human_approval": False,  # the LLM says no — guardrail must override
    }
    plan = _router_returning(payload).route(
        "Submit the paper to Nature"
    )
    # The keyword "submit" should always trip human_review via
    # research_os.routing.human.
    assert plan.human_review_required, "'submit' should always require human review"


def test_regression_10b_destructive_delete_also_blocks():
    payload = {
        "intent": "destructive",
        "selected_agents": ["context_source_truth"],
        "confidence": 0.6,
        "risk_level": "high",
        "reasoning_summary": "destructive op",
        "requires_claude_fallback": True,
        "requires_human_approval": True,
    }
    plan = _router_returning(payload).route(
        "Delete the experiment registry and start over"
    )
    assert plan.human_review_required
    assert plan.requires_claude_fallback


# ────────────────────────────────────────────────────────────────────────────
# Sanity: every regression case is also present in the benchmark dataset.
# ────────────────────────────────────────────────────────────────────────────

def test_regressions_covered_by_benchmark_dataset():
    """The 10 enumerated cases should also exist in the benchmark, so the
    eval picks them up alongside everything else. We grep by category."""
    from research_os.eval.routing_benchmark import CASES
    cats = {c.category for c in CASES}
    must_have = {
        "literature", "data_leakage", "md_validation", "claim_audit",
        "compute_planning", "figure_generation", "dashboard_status_debug",
        "compound_ambiguous", "destructive_dangerous",
    }
    missing = must_have - cats
    assert not missing, f"benchmark missing categories: {missing}"
