"""Schemas for the autonomous-agent framework.

These dataclasses are intentionally small and JSON-serializable so they can
flow through the existing transcript / event / MCP layers without needing new
serialization machinery.

Closed vocabularies live alongside the schemas they constrain (e.g.
``STEP_STATUSES``). New values may be added — never removed — same rule as
``schemas/vocab.py``.
"""
from __future__ import annotations

import time
import uuid
from dataclasses import asdict, dataclass, field
from typing import Any, Callable, Dict, List, Optional


# ---------------------------------------------------------------------------
# Step / Plan / Goal vocab
# ---------------------------------------------------------------------------

STEP_STATUSES = (
    "pending",
    "running",
    "succeeded",
    "failed",
    "skipped",
    "deferred",
    "blocked",
)

STEP_KINDS = (
    "tool_call",          # invoke a registered tool
    "sub_goal",           # delegate to another autonomous agent
    "handoff",            # explicitly hand the work to another agent
    "deterministic",      # run an agent-internal deterministic step
    "critique",           # run a critic over prior step results
    "evaluate_coverage",  # evaluate coverage and possibly spawn follow-ups
    "noop",               # explicit placeholder; never executes
)


class StepStatus:
    """Constants for step status (mirrors STEP_STATUSES)."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    SKIPPED = "skipped"
    DEFERRED = "deferred"
    BLOCKED = "blocked"


def _new_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:10]}"


# ---------------------------------------------------------------------------
# Budget + stop conditions
# ---------------------------------------------------------------------------

@dataclass
class Budget:
    """Hard caps on autonomous execution. Every cap is independent.

    The first cap that trips ends the loop with a ``budget_exhausted`` event.
    ``None`` means "no cap for this dimension" — at least one cap should
    always be set, otherwise the loop can run forever.
    """
    max_iterations: int = 8
    max_tool_calls: int = 32
    max_failures: int = 3
    max_seconds: Optional[float] = 120.0
    max_tokens: Optional[int] = None      # informational; tools may enforce

    def is_exhausted(self, *, iterations: int, tool_calls: int, failures: int,
                     started_at: float) -> Optional[str]:
        """Return the name of the first exhausted dimension, or None."""
        if iterations >= self.max_iterations:
            return "max_iterations"
        if tool_calls >= self.max_tool_calls:
            return "max_tool_calls"
        if failures >= self.max_failures:
            return "max_failures"
        if self.max_seconds is not None and (time.time() - started_at) >= self.max_seconds:
            return "max_seconds"
        return None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class StopCondition:
    """A condition that, if true, terminates the loop *without* being a failure."""
    name: str
    description: str = ""
    # Callable receives (current_results: list[StepResult]) → bool.
    # Stored separately because dataclass asdict() can't serialize callables.
    predicate: Optional[Callable[[List["StepResult"]], bool]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name, "description": self.description}


# ---------------------------------------------------------------------------
# Success criteria
# ---------------------------------------------------------------------------

@dataclass
class SuccessCriterion:
    """A measurable check a goal must satisfy to be declared completed.

    Two forms supported:

    - ``check_key`` + ``check_value`` + ``op`` for simple comparisons against
      a key emitted in step results (e.g. ``source_count >= 200``).
    - ``predicate`` for arbitrary callables — not serialized.
    """
    name: str
    check_key: Optional[str] = None
    op: str = ">="     # one of ">=", ">", "==", "<", "<=", "contains"
    check_value: Any = None
    predicate: Optional[Callable[[Dict[str, Any]], bool]] = None
    description: str = ""

    def evaluate(self, ctx: Dict[str, Any]) -> bool:
        if self.predicate is not None:
            try:
                return bool(self.predicate(ctx))
            except Exception:
                return False
        if self.check_key is None:
            return False
        actual = ctx.get(self.check_key)
        try:
            if self.op == ">=":
                return actual is not None and actual >= self.check_value
            if self.op == ">":
                return actual is not None and actual > self.check_value
            if self.op == "==":
                return actual == self.check_value
            if self.op == "<=":
                return actual is not None and actual <= self.check_value
            if self.op == "<":
                return actual is not None and actual < self.check_value
            if self.op == "contains":
                return actual is not None and self.check_value in actual
        except TypeError:
            return False
        return False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "check_key": self.check_key,
            "op": self.op,
            "check_value": self.check_value,
            "description": self.description,
        }


# ---------------------------------------------------------------------------
# Step + Plan + StepResult
# ---------------------------------------------------------------------------

@dataclass
class Step:
    """One unit of autonomous work.

    A ``Step`` is *what to do next*; a ``StepResult`` is *what happened*.
    """
    step_id: str = field(default_factory=lambda: _new_id("step"))
    kind: str = "tool_call"            # one of STEP_KINDS
    description: str = ""
    tool_name: Optional[str] = None
    tool_input: Dict[str, Any] = field(default_factory=dict)
    target_agent: Optional[str] = None    # for sub_goal / handoff
    sub_goal: Optional["Goal"] = None     # for sub_goal kind
    depends_on: List[str] = field(default_factory=list)
    rationale: str = ""
    spawned_by: Optional[str] = None      # critic that proposed this step

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        # ``sub_goal`` may be a Goal; nested asdict handles it.
        return d


@dataclass
class StepResult:
    step_id: str
    status: str                          # one of STEP_STATUSES
    output: Any = None
    error: str = ""
    confidence: float = 0.0
    evidence: List[str] = field(default_factory=list)
    duration_seconds: float = 0.0
    retried_from: Optional[str] = None   # original step_id if this is a retry
    notes: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Plan:
    """An ordered sequence of steps an agent intends to execute.

    Plans can be revised mid-run — the framework emits ``plan_revised`` when
    that happens. A revised plan keeps the same ``plan_id`` and increments
    ``revision``.
    """
    plan_id: str = field(default_factory=lambda: _new_id("plan"))
    revision: int = 0
    goal_id: str = ""
    steps: List[Step] = field(default_factory=list)
    rationale: str = ""
    created_by: str = ""                 # planner name

    def step(self, step_id: str) -> Optional[Step]:
        for s in self.steps:
            if s.step_id == step_id:
                return s
        return None

    def append(self, step: Step) -> None:
        self.steps.append(step)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "revision": self.revision,
            "goal_id": self.goal_id,
            "steps": [s.to_dict() for s in self.steps],
            "rationale": self.rationale,
            "created_by": self.created_by,
        }


@dataclass
class Goal:
    """A high-level objective handed to an autonomous agent or controller.

    Goals can nest — a controller decomposes a top-level goal into sub-goals
    that are dispatched to specialized agents. Each level carries its own
    ``Budget`` so resource caps are explicit.
    """
    goal_id: str = field(default_factory=lambda: _new_id("goal"))
    objective: str = ""
    rationale: str = ""
    success_criteria: List[SuccessCriterion] = field(default_factory=list)
    stop_conditions: List[StopCondition] = field(default_factory=list)
    budget: Budget = field(default_factory=Budget)
    inputs: Dict[str, Any] = field(default_factory=dict)
    parent_goal_id: Optional[str] = None

    def all_criteria_met(self, ctx: Dict[str, Any]) -> bool:
        if not self.success_criteria:
            return False
        return all(c.evaluate(ctx) for c in self.success_criteria)

    def unmet_criteria(self, ctx: Dict[str, Any]) -> List[SuccessCriterion]:
        return [c for c in self.success_criteria if not c.evaluate(ctx)]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "goal_id": self.goal_id,
            "objective": self.objective,
            "rationale": self.rationale,
            "success_criteria": [c.to_dict() for c in self.success_criteria],
            "stop_conditions": [s.to_dict() for s in self.stop_conditions],
            "budget": self.budget.to_dict(),
            "inputs": dict(self.inputs),
            "parent_goal_id": self.parent_goal_id,
        }


# ---------------------------------------------------------------------------
# Critique + Coverage
# ---------------------------------------------------------------------------

@dataclass
class CritiqueResult:
    """Output of a critic. The crucial field is ``spawned_steps`` — critics
    feed the planner directly so weaknesses become follow-up tasks instead of
    inert findings in a report.
    """
    critic_name: str
    severity: str = "info"               # critical|high|medium|low|info
    summary: str = ""
    issues: List[str] = field(default_factory=list)
    spawned_steps: List[Step] = field(default_factory=list)
    requires_replan: bool = False
    confidence: float = 0.5

    def to_dict(self) -> Dict[str, Any]:
        return {
            "critic_name": self.critic_name,
            "severity": self.severity,
            "summary": self.summary,
            "issues": list(self.issues),
            "spawned_steps": [s.to_dict() for s in self.spawned_steps],
            "requires_replan": self.requires_replan,
            "confidence": self.confidence,
        }


@dataclass
class CoverageCategory:
    """A named coverage bucket used by the CoverageEstimator."""
    name: str
    keywords: List[str] = field(default_factory=list)
    min_items: int = 1
    weight: float = 1.0
    description: str = ""

    def matches(self, item_text: str) -> bool:
        if not self.keywords:
            return False
        low = item_text.lower()
        return any(k.lower() in low for k in self.keywords)


@dataclass
class CoverageResult:
    """Output of a CoverageEstimator pass.

    ``score`` is the weighted fraction of categories at or above ``min_items``.
    ``gaps`` lists category names that did NOT meet ``min_items`` — these are
    the obvious targets for follow-up tasks.
    """
    score: float
    per_category_counts: Dict[str, int] = field(default_factory=dict)
    per_category_score: Dict[str, float] = field(default_factory=dict)
    gaps: List[str] = field(default_factory=list)
    suggested_queries: List[str] = field(default_factory=list)
    total_items: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# Handoff
# ---------------------------------------------------------------------------

@dataclass
class HandoffRequest:
    """An autonomous agent can request that another agent take over part of
    its work. The controller decides whether to honor the request.
    """
    from_agent: str
    to_agent: str
    reason: str
    payload: Dict[str, Any] = field(default_factory=dict)
    sub_goal: Optional[Goal] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "from_agent": self.from_agent,
            "to_agent": self.to_agent,
            "reason": self.reason,
            "payload": dict(self.payload),
            "sub_goal": self.sub_goal.to_dict() if self.sub_goal else None,
        }


__all__ = [
    "Budget",
    "CoverageCategory",
    "CoverageResult",
    "CritiqueResult",
    "Goal",
    "HandoffRequest",
    "Plan",
    "STEP_KINDS",
    "STEP_STATUSES",
    "Step",
    "StepResult",
    "StepStatus",
    "StopCondition",
    "SuccessCriterion",
]
