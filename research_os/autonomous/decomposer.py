"""Goal decomposer.

Takes a high-level ``Goal`` and produces a list of sub-goals that can be
dispatched to specialized autonomous agents. Phase 5 ships with a
template-based decomposer that handles the canonical ResearchOS goal
shapes (corpus build, verification campaign, readiness assessment); future
work can swap in an LLM-backed decomposer.

The decomposer is deterministic and never makes external calls.
"""
from __future__ import annotations

import re
from typing import Callable, Dict, List, Optional

from research_os.autonomous.schemas import Goal, SuccessCriterion


class Decomposer:
    """Template-driven goal decomposer.

    Templates are keyed by name and matched against the goal's
    ``objective`` (case-insensitive). The first matching template fires.
    """

    def __init__(self):
        self._templates: Dict[str, Callable[[Goal], List[Goal]]] = {}

    def register(self, name: str, matcher: Callable[[str], bool],
                 builder: Callable[[Goal], List[Goal]]) -> None:
        self._templates[name] = (matcher, builder)  # type: ignore[assignment]

    def decompose(self, goal: Goal) -> List[Goal]:
        objective = (goal.objective or "").lower()
        for name, pair in self._templates.items():
            matcher, builder = pair  # type: ignore[misc]
            if matcher(objective):
                return builder(goal)
        # No template matched — return the goal as a single sub-goal.
        return [self._wrap(goal, agent_id=goal.inputs.get("target_agent"))]

    # ------------------------------------------------------------------

    @staticmethod
    def _wrap(parent: Goal, *, agent_id: Optional[str] = None,
              objective: Optional[str] = None,
              inputs_extra: Optional[Dict] = None) -> Goal:
        inputs = dict(parent.inputs)
        if agent_id:
            inputs["target_agent"] = agent_id
        if inputs_extra:
            inputs.update(inputs_extra)
        return Goal(
            objective=objective or parent.objective,
            rationale=parent.rationale,
            success_criteria=list(parent.success_criteria),
            stop_conditions=list(parent.stop_conditions),
            budget=parent.budget,
            inputs=inputs,
            parent_goal_id=parent.goal_id,
        )


# ---------------------------------------------------------------------------
# Default templates
# ---------------------------------------------------------------------------

_CORPUS_TOKENS = re.compile(
    r"\b(corpus|literature\s+(?:sweep|search|survey|review)|"
    r"build\s+(?:a\s+)?(?:research\s+)?(?:corpus|review))\b",
    re.IGNORECASE,
)
_VERIFY_TOKENS = re.compile(
    r"\b(verif\w*|audit|cross[\s-]?check)\b", re.IGNORECASE,
)
_READINESS_TOKENS = re.compile(
    r"\b(readiness|phase\s*\d+|next\s*phase|implementation\s*roadmap)\b",
    re.IGNORECASE,
)
_SCAFFOLD_TOKENS = re.compile(
    r"\b(scaffold|restore|repair|generate.*(?:code|module|test))\b",
    re.IGNORECASE,
)


def _corpus_matcher(obj: str) -> bool:
    return bool(_CORPUS_TOKENS.search(obj))


def _corpus_builder(goal: Goal) -> List[Goal]:
    """Corpus build: discover → ingest → coverage → synthesis."""
    return [
        Decomposer._wrap(
            goal,
            agent_id="literature_web",
            objective=f"Literature sweep for: {goal.objective[:160]}",
            inputs_extra={"phase": "discover"},
        ),
        Decomposer._wrap(
            goal,
            agent_id="document_knowledge_ingestion",
            objective="Ingest newly discovered sources into source_registry.",
            inputs_extra={"phase": "ingest"},
        ),
        Decomposer._wrap(
            goal,
            agent_id="literature_web",
            objective="Score coverage + identify gaps.",
            inputs_extra={"phase": "coverage"},
        ),
    ]


def _verify_matcher(obj: str) -> bool:
    return bool(_VERIFY_TOKENS.search(obj)) and not _CORPUS_TOKENS.search(obj)


def _verify_builder(goal: Goal) -> List[Goal]:
    """Multi-agent verification sequence. The controller's verification
    suite then runs the actual 10 checks; this template just dispatches
    one "verify" sub-goal."""
    return [
        Decomposer._wrap(
            goal,
            agent_id="__verification_suite__",
            objective=goal.objective,
            inputs_extra={"phase": "verify"},
        ),
    ]


def _readiness_matcher(obj: str) -> bool:
    return bool(_READINESS_TOKENS.search(obj))


def _readiness_builder(goal: Goal) -> List[Goal]:
    """Readiness assessment = corpus → verify → roadmap."""
    return [
        Decomposer._wrap(
            goal,
            agent_id="literature_web",
            objective=f"Pre-readiness corpus refresh for: {goal.objective[:120]}",
            inputs_extra={"phase": "corpus"},
        ),
        Decomposer._wrap(
            goal,
            agent_id="document_knowledge_ingestion",
            objective="Pre-readiness ingest of newly discovered sources.",
            inputs_extra={"phase": "ingest"},
        ),
        Decomposer._wrap(
            goal,
            agent_id="__verification_suite__",
            objective="Multi-agent verification pre-readiness.",
            inputs_extra={"phase": "verify"},
        ),
        Decomposer._wrap(
            goal,
            agent_id="__synthesis_writer__",
            objective="Synthesize Phase-N roadmap + readiness assessment.",
            inputs_extra={"phase": "synthesize"},
        ),
    ]


def _scaffold_matcher(obj: str) -> bool:
    return bool(_SCAFFOLD_TOKENS.search(obj))


def _scaffold_builder(goal: Goal) -> List[Goal]:
    """Code-scaffold goal: dispatch to autonomous code_builder."""
    return [
        Decomposer._wrap(
            goal,
            agent_id="code_builder",
            objective=goal.objective,
            inputs_extra={"phase": "scaffold"},
        ),
    ]


def default_decomposer() -> Decomposer:
    d = Decomposer()
    # Match order matters — readiness should win over corpus on a "build
    # corpus + assess readiness" objective.
    d.register("readiness", _readiness_matcher, _readiness_builder)
    d.register("corpus", _corpus_matcher, _corpus_builder)
    d.register("scaffold", _scaffold_matcher, _scaffold_builder)
    d.register("verify", _verify_matcher, _verify_builder)
    return d


__all__ = ["Decomposer", "default_decomposer"]
