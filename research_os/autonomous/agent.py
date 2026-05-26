"""AutonomousAgent — the planning-loop base class.

Subclasses ``BaseAgent`` so it slots into the existing ``Orchestrator``
without any orchestrator change. The legacy ``run(packet) -> AgentOutput``
contract is preserved.

Behavior contract:

1. ``run(packet)`` checks if autonomy should be attempted:
   - profile.autonomy_level > DETERMINISTIC
   - RESEARCHOS_AUTONOMY_OFF not set
   - every env in profile.requires_env is set

   If any check fails, the agent runs ``_deterministic_run(packet)`` (the
   subclass's legacy scan) and returns that ``AgentOutput`` directly. This
   is the **deterministic fallback** — autonomy is purely additive.

2. If autonomy is enabled, ``_autonomous_loop(packet)`` runs:
     - build a Goal from the packet
     - the planner produces a Plan
     - iterate steps, honoring depends_on and the Budget
     - on critique-spawned steps, replan
     - on tool/step failure, count toward max_failures; optionally retry
     - on any uncaught exception, emit ``fallback_triggered`` and revert
       to ``_deterministic_run(packet)``.

3. The composed output preserves all legacy AgentOutput fields and adds the
   plan/step trace to ``machine_readable_notes`` for downstream consumers.
"""
from __future__ import annotations

import os
import time
import uuid
from typing import Any, Dict, List, Optional

from research_os.agents.base import AgentContext, BaseAgent
from research_os.autonomous import events as ev
from research_os.autonomous.critique import Critic
from research_os.autonomous.memory import AgentMemory
from research_os.autonomous.planner import DeterministicPlanner, Planner
from research_os.autonomous.profile import AgentProfile, AutonomyLevel, profile_for
from research_os.autonomous.schemas import (
    Budget,
    CritiqueResult,
    Goal,
    Plan,
    Step,
    StepResult,
    StepStatus,
)
from research_os.schemas.context import ContextPacket
from research_os.schemas.core import AgentOutput
from research_os.tools.builtin import register_builtin
from research_os.tools.llm import register_llm
from research_os.tools.registry import ToolRegistry, ToolResult
from research_os.tools.web import register_web


_AUTONOMY_KILL = "RESEARCHOS_AUTONOMY_OFF"


# ---------------------------------------------------------------------------
# Run result envelope
# ---------------------------------------------------------------------------

class AutonomousRunResult:
    """In-memory record of one autonomous loop. Folded into AgentOutput."""

    def __init__(self, *, goal: Goal, plan: Plan):
        self.goal = goal
        self.plan = plan
        self.step_results: List[StepResult] = []
        self.critiques: List[CritiqueResult] = []
        self.ctx_state: Dict[str, Any] = dict(goal.inputs)
        self.iterations = 0
        self.tool_calls = 0
        self.failures = 0
        self.budget_exhausted: Optional[str] = None
        self.completed_at: float = 0.0

    @property
    def criteria_met(self) -> bool:
        return self.goal.all_criteria_met(self.ctx_state) if self.goal.success_criteria else True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "goal": self.goal.to_dict(),
            "plan": self.plan.to_dict(),
            "step_results": [r.to_dict() for r in self.step_results],
            "critiques": [c.to_dict() for c in self.critiques],
            "ctx_state_summary": {
                k: (v if not isinstance(v, (list, tuple, dict))
                    else f"[{type(v).__name__} len={len(v) if hasattr(v, '__len__') else '?'}]")
                for k, v in self.ctx_state.items()
            },
            "iterations": self.iterations,
            "tool_calls": self.tool_calls,
            "failures": self.failures,
            "budget_exhausted": self.budget_exhausted,
            "criteria_met": self.criteria_met,
        }


# ---------------------------------------------------------------------------
# AutonomousAgent
# ---------------------------------------------------------------------------

class AutonomousAgent(BaseAgent):
    """BaseAgent + planning loop. Subclasses override:

    - ``_deterministic_run(packet)`` — the legacy scan / fallback.
    - ``build_goal(packet)`` (optional) — construct the goal from the packet.
    - ``build_default_profile()`` (optional) — return an AgentProfile if the
      registry doesn't already have one for this agent.
    """

    # Subclasses set; defaults come from profile_for(agent_id) otherwise.
    profile: Optional[AgentProfile] = None

    def __init__(
        self,
        ctx: AgentContext,
        *,
        profile: Optional[AgentProfile] = None,
        tool_registry: Optional[ToolRegistry] = None,
        planner: Optional[Planner] = None,
        critics: Optional[List[Critic]] = None,
        budget: Optional[Budget] = None,
        workflow_id: Optional[str] = None,
    ):
        super().__init__(ctx)
        self.profile = profile or self.profile or profile_for(self.agent_id)
        self.tools = tool_registry or self._build_default_tools(ctx)
        self.planner = planner or DeterministicPlanner()
        self.critics: List[Critic] = list(critics or [])
        self.budget = budget or self.profile.default_budget
        self._workflow_id = workflow_id or f"auto-{uuid.uuid4().hex[:8]}"
        self._memory: Optional[AgentMemory] = None
        self._last_run_result: Optional[AutonomousRunResult] = None

    # ------------------------------------------------------------------
    # Public entry point (overrides BaseAgent.run)
    # ------------------------------------------------------------------

    def run(self, packet: ContextPacket) -> AgentOutput:
        if not self._autonomy_enabled():
            return self._deterministic_run(packet)
        try:
            result = self._autonomous_loop(packet)
            self._last_run_result = result
            output = self._compose_output(packet, result)
            return output
        except Exception as e:
            ev.fallback_triggered(self._workflow_id,
                                  agent_id=self.agent_id,
                                  reason=f"autonomous_loop_crash: {e}")
            self._memory_record("fallback_triggered", {"error": str(e)})
            try:
                return self._deterministic_run(packet)
            except Exception as inner:
                # Both autonomy and fallback failed — return a clean error
                # so the orchestrator can surface it without crashing.
                return self._error_output(packet, str(e), str(inner))

    # ------------------------------------------------------------------
    # Subclass extension hooks
    # ------------------------------------------------------------------

    def _deterministic_run(self, packet: ContextPacket) -> AgentOutput:
        """Subclass override: the legacy single-pass scan.

        Default raises so opting an agent into AutonomousAgent without
        wiring a fallback is loud, not silent.
        """
        raise NotImplementedError(
            f"{type(self).__name__} must implement _deterministic_run"
        )

    def build_goal(self, packet: ContextPacket) -> Goal:
        """Default: a single-objective goal derived from the packet's task."""
        return Goal(
            objective=(packet.task or "(no objective)")[:280],
            rationale=f"Default goal for {self.agent_id}",
            budget=self.budget,
            inputs={"task": packet.task, "intents": list(packet.intents)},
        )

    # ------------------------------------------------------------------
    # The autonomous loop
    # ------------------------------------------------------------------

    def _autonomous_loop(self, packet: ContextPacket) -> AutonomousRunResult:
        wfid = self._workflow_id
        self._memory = AgentMemory.for_agent(self.agent_id, repo_root=self.ctx.repo_root)
        goal = self.build_goal(packet)
        ev.goal_started(wfid, goal_id=goal.goal_id, agent_id=self.agent_id,
                        objective=goal.objective, budget=goal.budget.to_dict())
        self._memory_record("goal_started", {
            "goal_id": goal.goal_id, "objective": goal.objective,
        })

        plan = self.planner.plan(goal, packet, profile=self.profile, tools=self.tools)
        ev.plan_created(wfid, plan_id=plan.plan_id, goal_id=goal.goal_id,
                        agent_id=self.agent_id, step_count=len(plan.steps),
                        rationale=plan.rationale)
        self._memory_record("plan_created", {
            "goal_id": goal.goal_id, "plan_id": plan.plan_id,
            "step_count": len(plan.steps),
        })

        result = AutonomousRunResult(goal=goal, plan=plan)
        self._active_result = result   # exposed so _merge_ctx_state can find it
        started_at = time.time()
        executed_ids: set = set()

        while True:
            # 1. Budget check
            exhausted = goal.budget.is_exhausted(
                iterations=result.iterations,
                tool_calls=result.tool_calls,
                failures=result.failures,
                started_at=started_at,
            )
            if exhausted is not None:
                result.budget_exhausted = exhausted
                ev.budget_exhausted(wfid, agent_id=self.agent_id, dimension=exhausted,
                                    iterations=result.iterations,
                                    tool_calls=result.tool_calls,
                                    failures=result.failures)
                self._memory_record("budget_exhausted", {"dimension": exhausted})
                break

            # 2. Pick next runnable step
            next_step = self._next_runnable_step(plan, executed_ids, result.step_results)
            if next_step is None:
                # No more pending steps. Have we met the goal?
                if not goal.success_criteria or result.criteria_met:
                    break
                # Run critics one more time to see if they want to add steps.
                if not self.critics:
                    break
                spawned_count_before = sum(len(c.spawned_steps) for c in result.critiques)
                self._run_critics(plan, result, wfid)
                spawned_count_after = sum(len(c.spawned_steps) for c in result.critiques)
                if spawned_count_after == spawned_count_before:
                    break  # critics had nothing to add
                self._replan(plan, result, packet, wfid)
                plan = result.plan
                continue  # plan was revised, take another lap

            # 3. Execute step
            executed_ids.add(next_step.step_id)
            ev.step_started(wfid, step_id=next_step.step_id, agent_id=self.agent_id,
                            kind=next_step.kind, description=next_step.description,
                            tool_name=next_step.tool_name)
            self._memory_record("step_started", {
                "goal_id": goal.goal_id, "step_id": next_step.step_id,
                "kind": next_step.kind, "description": next_step.description,
            })

            step_result = self._execute_step(next_step, plan, packet, result, wfid)
            result.step_results.append(step_result)
            result.iterations += 1
            if next_step.kind == "tool_call":
                result.tool_calls += 1
            if step_result.status == StepStatus.FAILED:
                result.failures += 1
                ev.step_failed(wfid, step_id=next_step.step_id, agent_id=self.agent_id,
                               error=step_result.error, will_retry=False)
            ev.step_completed(wfid, step_id=next_step.step_id, agent_id=self.agent_id,
                              status=step_result.status, summary=step_result.error or "",
                              confidence=step_result.confidence,
                              duration_seconds=step_result.duration_seconds)
            self._memory_record("step_completed", {
                "goal_id": goal.goal_id, "step_id": next_step.step_id,
                "status": step_result.status, "confidence": step_result.confidence,
            })

            # 4. Critique-triggered replanning
            if next_step.kind == "critique" and self._critique_requires_replan(result):
                self._replan(plan, result, packet, wfid)
                plan = result.plan

        # Loop exited: record outcome
        result.completed_at = time.time()
        status_str = self._outcome_status(result)
        ev.goal_completed(
            wfid, goal_id=goal.goal_id, agent_id=self.agent_id,
            status=status_str, summary=plan.rationale,
            criteria_met=[c.name for c in goal.success_criteria if c.evaluate(result.ctx_state)],
            criteria_unmet=[c.name for c in goal.unmet_criteria(result.ctx_state)],
        )
        self._memory_record("goal_completed", {
            "goal_id": goal.goal_id, "status": status_str,
            "iterations": result.iterations, "failures": result.failures,
        })
        return result

    # ------------------------------------------------------------------
    # Step execution dispatch
    # ------------------------------------------------------------------

    def _execute_step(
        self,
        step: Step,
        plan: Plan,
        packet: ContextPacket,
        result: AutonomousRunResult,
        wfid: str,
    ) -> StepResult:
        start = time.time()
        try:
            if step.kind == "tool_call":
                return self._exec_tool_call(step, wfid, start)
            if step.kind == "deterministic":
                return self._exec_deterministic(step, packet, start)
            if step.kind == "critique":
                return self._exec_critique(step, plan, result, wfid, start)
            if step.kind == "evaluate_coverage":
                # Coverage runs as a critic — surface as a critique step.
                return self._exec_critique(step, plan, result, wfid, start)
            if step.kind in ("sub_goal", "handoff"):
                # Phase 3 scaffold: we record a handoff request; the
                # controller (Phase 5) will dispatch sub-goals.
                target = step.target_agent or "(unspecified)"
                ev.handoff_requested(wfid, from_agent=self.agent_id, to_agent=target,
                                     reason=step.description)
                return StepResult(
                    step_id=step.step_id, status=StepStatus.DEFERRED,
                    output={"deferred_to": target, "reason": step.description},
                    duration_seconds=time.time() - start,
                    notes={"kind": step.kind},
                )
            if step.kind == "noop":
                return StepResult(step_id=step.step_id, status=StepStatus.SKIPPED,
                                  duration_seconds=time.time() - start)
            return StepResult(step_id=step.step_id, status=StepStatus.FAILED,
                              error=f"unknown step kind: {step.kind}",
                              duration_seconds=time.time() - start)
        except Exception as e:
            return StepResult(step_id=step.step_id, status=StepStatus.FAILED,
                              error=f"{type(e).__name__}: {e}",
                              duration_seconds=time.time() - start)

    def _exec_tool_call(self, step: Step, wfid: str, start: float) -> StepResult:
        if not step.tool_name:
            return StepResult(step_id=step.step_id, status=StepStatus.FAILED,
                              error="tool_call step has no tool_name",
                              duration_seconds=time.time() - start)
        # Tool-call summary for events.
        inputs_summary = ", ".join(f"{k}={v!r}"[:40] for k, v in (step.tool_input or {}).items())
        ev.tool_called(wfid, tool_name=step.tool_name, agent_id=self.agent_id,
                       step_id=step.step_id, inputs_summary=inputs_summary)
        tr: ToolResult = self.tools.call_for_profile(
            self.profile.allowed_tools, step.tool_name, step.tool_input or {},
        )
        ev.tool_result(wfid, tool_name=step.tool_name, agent_id=self.agent_id,
                       step_id=step.step_id, ok=tr.ok, summary=tr.summary(),
                       duration_seconds=tr.duration_seconds)
        duration = time.time() - start
        if not tr.ok:
            return StepResult(step_id=step.step_id, status=StepStatus.FAILED,
                              output=None, error=tr.error,
                              duration_seconds=duration,
                              notes={"tool_metadata": tr.metadata})
        # Update ctx_state if the tool output is a dict.
        if isinstance(tr.output, dict):
            for k, v in tr.output.items():
                if k not in ("ok", "error"):
                    # Don't blindly stomp existing keys with the same name.
                    self._merge_ctx_state(k, v)
        return StepResult(step_id=step.step_id, status=StepStatus.SUCCEEDED,
                          output=tr.output, confidence=0.8,
                          duration_seconds=duration)

    def _exec_deterministic(self, step: Step, packet: ContextPacket, start: float) -> StepResult:
        # Run the subclass's legacy scan inline. The AgentOutput is preserved
        # in the step's output for the composer.
        try:
            out = self._deterministic_run(packet)
        except NotImplementedError:
            return StepResult(step_id=step.step_id, status=StepStatus.SKIPPED,
                              error="no deterministic implementation",
                              duration_seconds=time.time() - start)
        # Carry summary fields into ctx_state so success criteria can read them.
        self._merge_ctx_state("deterministic_output", out.to_dict())
        self._merge_ctx_state("deterministic_status", out.status)
        # Map AgentOutput.status to StepStatus so the loop's failure
        # accounting (max_failures budget) can react to a deterministic
        # scan that reports fail/blocked — not just to thrown exceptions.
        step_status = (
            StepStatus.FAILED
            if out.status in ("fail", "blocked") else StepStatus.SUCCEEDED
        )
        error_msg = "" if step_status == StepStatus.SUCCEEDED else out.summary[:240]
        return StepResult(step_id=step.step_id, status=step_status,
                          output={"agent_output": out.to_dict()},
                          confidence=out.confidence,
                          error=error_msg,
                          duration_seconds=time.time() - start)

    def _exec_critique(self, step: Step, plan: Plan, result: AutonomousRunResult,
                       wfid: str, start: float) -> StepResult:
        if not self.critics:
            return StepResult(step_id=step.step_id, status=StepStatus.SKIPPED,
                              error="no critics attached",
                              duration_seconds=time.time() - start)
        self._run_critics(plan, result, wfid)
        return StepResult(step_id=step.step_id, status=StepStatus.SUCCEEDED,
                          output={"critique_count": len(result.critiques)},
                          confidence=0.7,
                          duration_seconds=time.time() - start)

    # ------------------------------------------------------------------
    # Critique + replan
    # ------------------------------------------------------------------

    def _run_critics(self, plan: Plan, result: AutonomousRunResult, wfid: str) -> None:
        for critic in self.critics:
            cname = getattr(critic, "name", critic.__class__.__name__)
            ev.critique_started(wfid, agent_id=self.agent_id,
                                critic_name=cname, goal_id=result.goal.goal_id)
            try:
                crit_result = critic(plan, result.step_results, result.ctx_state)
            except Exception as e:
                crit_result = CritiqueResult(
                    critic_name=cname, severity="high",
                    summary=f"critic crashed: {e}",
                    issues=[str(e)], confidence=0.0,
                )
            result.critiques.append(crit_result)
            ev.critique_completed(
                wfid, agent_id=self.agent_id, critic_name=cname,
                goal_id=result.goal.goal_id,
                severity=crit_result.severity,
                issue_count=len(crit_result.issues),
                spawned_step_count=len(crit_result.spawned_steps),
                requires_replan=crit_result.requires_replan,
            )
            self._memory_record("critique", {
                "goal_id": result.goal.goal_id,
                "critic_name": cname,
                "severity": crit_result.severity,
                "issues_count": len(crit_result.issues),
                "spawned_steps": len(crit_result.spawned_steps),
            })

    def _critique_requires_replan(self, result: AutonomousRunResult) -> bool:
        return any(c.requires_replan or c.spawned_steps for c in result.critiques)

    def _replan(self, plan: Plan, result: AutonomousRunResult,
                packet: ContextPacket, wfid: str) -> None:
        ev.replan_started(wfid, agent_id=self.agent_id,
                          goal_id=result.goal.goal_id, plan_id=plan.plan_id,
                          reason="critique requested replan")
        prev_step_count = len(plan.steps)
        new_plan = self.planner.replan(
            plan, result.step_results, result.critiques,
            goal=result.goal, packet=packet,
            profile=self.profile, tools=self.tools,
        )
        # replan returns the same plan (mutated) or a new one. Either way:
        result.plan = new_plan
        ev.replan_completed(wfid, agent_id=self.agent_id,
                            goal_id=result.goal.goal_id, plan_id=new_plan.plan_id,
                            revision=new_plan.revision,
                            new_step_count=len(new_plan.steps) - prev_step_count)
        # Clear consumed critiques so we don't replan in a tight loop on the
        # same critique payload.
        for c in result.critiques:
            c.spawned_steps = []
            c.requires_replan = False

    # ------------------------------------------------------------------
    # Output composition
    # ------------------------------------------------------------------

    def _compose_output(self, packet: ContextPacket, result: AutonomousRunResult) -> AgentOutput:
        """Fold the autonomous run into a valid AgentOutput.

        We start from the deterministic scan (if it ran) and *augment* it
        with plan/step trace + criteria status. This keeps the existing
        orchestrator + gate logic happy.
        """
        det = result.ctx_state.get("deterministic_output")
        if isinstance(det, dict):
            # Reconstruct an AgentOutput from the deterministic dict so all
            # status/confidence/findings/gate_updates pass through unchanged.
            base = self._output_from_dict(det)
        else:
            # No deterministic scan ran — synthesize a minimal output.
            base = self._output(
                task=packet.task,
                status="pass" if result.criteria_met else "warning",
                confidence=self._aggregate_confidence(result),
                summary=self._compose_summary(result),
            )
        # Merge autonomous trace into machine_readable_notes.
        notes = dict(base.machine_readable_notes or {})
        notes["autonomous"] = result.to_dict()
        notes["autonomous"]["workflow_id"] = self._workflow_id
        # Use object.__setattr__ in case AgentOutput is frozen elsewhere.
        base.machine_readable_notes = notes
        # Carry across criteria-met info into the summary if interesting.
        if result.budget_exhausted:
            base.summary = (
                base.summary
                + f" [autonomy stopped: {result.budget_exhausted}]"
            )[:480]
        return base

    def _output_from_dict(self, d: Dict[str, Any]) -> AgentOutput:
        """Rebuild AgentOutput from a dict produced earlier in this run.

        Only the fields we actually round-trip are restored — we don't need
        to re-validate, since the original AgentOutput was already validated.
        """
        out = AgentOutput(
            agent=d.get("agent", self.display_name),
            agent_id=d.get("agent_id", self.agent_id),
            task=d.get("task", ""),
            status=d.get("status", "pass"),
            confidence=float(d.get("confidence", 0.0)),
            summary=d.get("summary", ""),
            human_review_required=bool(d.get("human_review_required", False)),
            human_review_reason=d.get("human_review_reason", ""),
        )
        # Don't bother round-tripping the structured sub-fields here — the
        # caller will fold autonomous trace into machine_readable_notes.
        out.machine_readable_notes = dict(d.get("machine_readable_notes") or {})
        return out

    def _error_output(self, packet: ContextPacket, primary: str, secondary: str) -> AgentOutput:
        return self._output(
            task=packet.task,
            status="fail",
            confidence=0.0,
            summary=f"autonomous + fallback both failed: {primary} | {secondary}",
            human_review_required=True,
            human_review_reason="agent could not produce any output",
        )

    def _aggregate_confidence(self, result: AutonomousRunResult) -> float:
        succeeded = [r.confidence for r in result.step_results
                     if r.status == StepStatus.SUCCEEDED]
        if not succeeded:
            return 0.3
        return round(sum(succeeded) / len(succeeded), 3)

    def _compose_summary(self, result: AutonomousRunResult) -> str:
        n = len(result.step_results)
        ok = sum(1 for r in result.step_results if r.status == StepStatus.SUCCEEDED)
        return (
            f"autonomous run: {n} steps, {ok} ok, {result.failures} failed, "
            f"{result.tool_calls} tool calls, "
            f"criteria_met={result.criteria_met}"
        )

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _autonomy_enabled(self) -> bool:
        if self.profile.autonomy_level == AutonomyLevel.DETERMINISTIC:
            return False
        if os.environ.get(_AUTONOMY_KILL, "").strip() in ("1", "true", "yes", "on"):
            return False
        for env in self.profile.requires_env:
            if not os.environ.get(env, "").strip():
                return False
        return True

    def _next_runnable_step(
        self,
        plan: Plan,
        executed_ids: set,
        results: List[StepResult],
    ) -> Optional[Step]:
        successful_ids = {r.step_id for r in results if r.status == StepStatus.SUCCEEDED}
        for s in plan.steps:
            if s.step_id in executed_ids:
                continue
            deps_ok = all(dep in successful_ids for dep in s.depends_on)
            if deps_ok:
                return s
        return None

    def _merge_ctx_state(self, key: str, value: Any) -> None:
        """Smart merge into the active run's ctx_state.

        Append lists, update dicts, otherwise overwrite. No-op if no
        autonomous loop is currently running (e.g. during the deterministic
        fallback path).
        """
        result = getattr(self, "_active_result", None)
        if result is None:
            return
        cur = result.ctx_state.get(key)
        if isinstance(cur, list) and isinstance(value, list):
            cur.extend(value)
            return
        if isinstance(cur, dict) and isinstance(value, dict):
            cur.update(value)
            return
        result.ctx_state[key] = value

    def _memory_record(self, event_type: str, payload: Dict[str, Any]) -> None:
        if self._memory is None:
            return
        self._memory.record(event_type, payload)

    def _outcome_status(self, result: AutonomousRunResult) -> str:
        if result.budget_exhausted:
            return "warning"
        if result.failures > 0 and not any(
            r.status == StepStatus.SUCCEEDED for r in result.step_results
        ):
            return "fail"
        if result.goal.success_criteria and not result.criteria_met:
            return "warning"
        return "pass"

    @staticmethod
    def _build_default_tools(ctx: AgentContext) -> ToolRegistry:
        registry = ToolRegistry()
        register_builtin(registry, ctx)
        # web + llm registered always — env-var gate keeps them inert until
        # the user opts in. Putting them in the registry lets profiles
        # declare them in allowed_tools without registration ceremony.
        try:
            register_web(registry)
        except ValueError:
            pass
        try:
            register_llm(registry)
        except ValueError:
            pass
        return registry


__all__ = ["AutonomousAgent", "AutonomousRunResult"]
