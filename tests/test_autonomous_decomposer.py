"""Tests for the goal Decomposer."""
from __future__ import annotations

import pytest

from research_os.autonomous.decomposer import Decomposer, default_decomposer
from research_os.autonomous.schemas import Goal


def test_default_templates_registered():
    d = default_decomposer()
    # The Decomposer doesn't expose its template names directly, but a
    # corpus goal must map to multiple sub-goals.
    sg = d.decompose(Goal(objective="Build a research corpus for PCNA"))
    assert len(sg) >= 2


def test_corpus_template_fires_on_corpus_objective():
    d = default_decomposer()
    sg = d.decompose(Goal(objective="Conduct a literature sweep for cryptic pockets"))
    assert [s.inputs.get("target_agent") for s in sg] == [
        "literature_web", "document_knowledge_ingestion", "literature_web",
    ]


def test_verify_template_fires_on_verification_objective():
    d = default_decomposer()
    sg = d.decompose(Goal(objective="Cross-check all claims for overclaim"))
    assert len(sg) == 1
    assert sg[0].inputs.get("target_agent") == "__verification_suite__"


def test_readiness_template_fires_with_full_pipeline():
    d = default_decomposer()
    sg = d.decompose(Goal(
        objective="Assess Phase 2 readiness and produce an implementation roadmap",
    ))
    agents = [s.inputs.get("target_agent") for s in sg]
    assert agents[0] == "literature_web"
    assert "__verification_suite__" in agents
    assert "__synthesis_writer__" in agents


def test_scaffold_template_fires_for_scaffolding():
    d = default_decomposer()
    sg = d.decompose(Goal(objective="Scaffold the missing crawler module"))
    assert sg[0].inputs.get("target_agent") == "code_builder"


def test_unrecognized_objective_falls_back_to_single_subgoal():
    d = default_decomposer()
    parent = Goal(objective="totally novel objective with no template match",
                  inputs={"target_agent": "literature_web"})
    sg = d.decompose(parent)
    assert len(sg) == 1
    assert sg[0].inputs.get("target_agent") == "literature_web"


def test_subgoals_carry_parent_id():
    d = default_decomposer()
    parent = Goal(objective="research corpus on cryptic pockets")
    sg = d.decompose(parent)
    for s in sg:
        assert s.parent_goal_id == parent.goal_id
