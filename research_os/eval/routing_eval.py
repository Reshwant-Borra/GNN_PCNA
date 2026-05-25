"""Routing evaluator — run benchmark cases through the Router and grade them.

This module is the runtime for ``python -m research_os routing-eval``. It
exposes both a programmatic API (``evaluate``, ``summarize``, ``render_report``)
and a CLI ``main(args)`` entry point.

Grading
-------

For each ``BenchmarkCase``:

- ``missing_expected``  = ``set(expected_agents) - selected``
- ``forbidden_present`` = ``set(forbidden_agents) & selected``
- ``risk_match`` = ``plan.risk_level in case.expected_risk``
- ``fallback_match`` = ``case.expected_claude_fallback is None or
                         plan.requires_claude_fallback == case.expected_claude_fallback``
- ``human_match`` = ``case.expected_human_review is None or
                      plan.human_review_required == case.expected_human_review``

Pass tiers:

- **exact pass**   = no missing, no forbidden, risk_match, fallback_match, human_match
- **partial pass** = no missing, no forbidden  (relaxes risk/fallback/human flags)
- **fail**         = anything else

The CLI prints a deterministic ranked failure list so iteration on
``AGENT_REGISTRY.md`` / ``ROUTING_GUIDE.md`` / the system prompt has a clear
signal.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from research_os.eval.routing_benchmark import CASES, BenchmarkCase, cases_by_category
from research_os.routing.router import Router
from research_os.routing.semantic_router import OllamaSemanticRouter
from research_os.routing.claude_fallback import FlagOnlyFallback
from research_os.schemas.context import OrchestrationPlan


# ────────────────────────────────────────────────────────────────────────────
# Result types
# ────────────────────────────────────────────────────────────────────────────

@dataclass
class CaseResult:
    case_id: str
    category: str
    prompt: str
    selected_agents: List[str]
    risk_level: str
    routing_decision: str
    routing_confidence: float
    requires_claude_fallback: bool
    human_review_required: bool
    missing_expected: List[str]
    forbidden_present: List[str]
    unexpected_extras: List[str]
    risk_match: bool
    fallback_match: bool
    human_match: bool
    is_exact_pass: bool
    is_partial_pass: bool
    elapsed_ms: int
    error: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CategoryStats:
    category: str
    total: int = 0
    exact: int = 0
    partial: int = 0
    fail: int = 0
    forbidden_violations: int = 0
    avg_selected: float = 0.0

    @property
    def exact_rate(self) -> float:
        return self.exact / self.total if self.total else 0.0

    @property
    def partial_rate(self) -> float:
        return self.partial / self.total if self.total else 0.0


@dataclass
class EvalSummary:
    backend: str
    total: int
    exact: int
    partial: int
    fail: int
    forbidden_violations: int
    fallback_correct: int
    fallback_evaluated: int
    human_review_correct: int
    human_review_evaluated: int
    by_category: List[CategoryStats] = field(default_factory=list)
    avg_elapsed_ms: float = 0.0
    high_risk_no_forbidden: bool = True

    @property
    def exact_rate(self) -> float:
        return self.exact / self.total if self.total else 0.0

    @property
    def partial_rate(self) -> float:
        return self.partial / self.total if self.total else 0.0

    @property
    def fallback_rate(self) -> float:
        return self.fallback_correct / self.fallback_evaluated if self.fallback_evaluated else 1.0

    @property
    def human_rate(self) -> float:
        return self.human_review_correct / self.human_review_evaluated if self.human_review_evaluated else 1.0


# ────────────────────────────────────────────────────────────────────────────
# Evaluation
# ────────────────────────────────────────────────────────────────────────────

def _grade(case: BenchmarkCase, plan: OrchestrationPlan, elapsed_ms: int) -> CaseResult:
    selected = list(plan.selected_agents)
    selected_set = set(selected)
    expected = set(case.expected_agents) | {"context_source_truth"}  # implicit
    optional = set(case.optional_agents)
    forbidden = set(case.forbidden_agents)

    missing = sorted(expected - selected_set)
    forbidden_present = sorted(forbidden & selected_set)
    # Unexpected extras = selected agents that are neither expected nor optional.
    # These are not penalized, but surfaced for inspection.
    unexpected = sorted(selected_set - expected - optional)

    risk_match = plan.risk_level in case.expected_risk
    fallback_match = (
        case.expected_claude_fallback is None
        or bool(plan.requires_claude_fallback) == bool(case.expected_claude_fallback)
    )
    human_match = (
        case.expected_human_review is None
        or bool(plan.human_review_required) == bool(case.expected_human_review)
    )

    is_partial = not missing and not forbidden_present
    is_exact = is_partial and risk_match and fallback_match and human_match

    return CaseResult(
        case_id=case.id,
        category=case.category,
        prompt=case.prompt,
        selected_agents=selected,
        risk_level=plan.risk_level,
        routing_decision=plan.routing_decision,
        routing_confidence=plan.routing_confidence,
        requires_claude_fallback=bool(plan.requires_claude_fallback),
        human_review_required=bool(plan.human_review_required),
        missing_expected=missing,
        forbidden_present=forbidden_present,
        unexpected_extras=unexpected,
        risk_match=risk_match,
        fallback_match=fallback_match,
        human_match=human_match,
        is_exact_pass=is_exact,
        is_partial_pass=is_partial,
        elapsed_ms=elapsed_ms,
    )


def evaluate(
    cases: Sequence[BenchmarkCase],
    router: Router,
    *,
    progress: bool = False,
) -> List[CaseResult]:
    """Run each case through ``router.route`` and grade it."""
    results: List[CaseResult] = []
    for i, case in enumerate(cases, start=1):
        if progress:
            print(f"  [{i:>3}/{len(cases)}] {case.id} · {case.category}", file=sys.stderr, flush=True)
        t0 = time.time()
        try:
            plan = router.route(case.prompt)
            elapsed = int((time.time() - t0) * 1000)
            results.append(_grade(case, plan, elapsed))
        except Exception as e:
            elapsed = int((time.time() - t0) * 1000)
            results.append(CaseResult(
                case_id=case.id,
                category=case.category,
                prompt=case.prompt,
                selected_agents=[],
                risk_level="medium",
                routing_decision="error",
                routing_confidence=0.0,
                requires_claude_fallback=True,
                human_review_required=False,
                missing_expected=sorted(set(case.expected_agents) | {"context_source_truth"}),
                forbidden_present=[],
                unexpected_extras=[],
                risk_match=False,
                fallback_match=False,
                human_match=False,
                is_exact_pass=False,
                is_partial_pass=False,
                elapsed_ms=elapsed,
                error=str(e)[:200],
            ))
    return results


def summarize(
    results: Sequence[CaseResult],
    backend_label: str = "ollama+keyword",
) -> EvalSummary:
    total = len(results)
    exact = sum(1 for r in results if r.is_exact_pass)
    partial = sum(1 for r in results if r.is_partial_pass)
    fail = total - partial
    forbidden_violations = sum(1 for r in results if r.forbidden_present)
    avg_elapsed = sum(r.elapsed_ms for r in results) / total if total else 0.0

    fallback_evaluated = 0
    fallback_correct = 0
    human_evaluated = 0
    human_correct = 0
    high_risk_no_forbidden = True

    by_cat: Dict[str, CategoryStats] = {}
    cbc = cases_by_category()
    case_map = {c.id: c for c in CASES}

    for r in results:
        stats = by_cat.setdefault(r.category, CategoryStats(category=r.category))
        stats.total += 1
        if r.is_exact_pass:
            stats.exact += 1
        if r.is_partial_pass:
            stats.partial += 1
        if not r.is_partial_pass:
            stats.fail += 1
        if r.forbidden_present:
            stats.forbidden_violations += 1
        stats.avg_selected += len(r.selected_agents)

        case = case_map.get(r.case_id)
        if case is not None:
            if case.expected_claude_fallback is not None:
                fallback_evaluated += 1
                if r.fallback_match:
                    fallback_correct += 1
            if case.expected_human_review is not None:
                human_evaluated += 1
                if r.human_match:
                    human_correct += 1
            if case.expected_risk in (("high",), ("critical",), ("high", "critical")) and r.forbidden_present:
                high_risk_no_forbidden = False
            if case.is_destructive and r.forbidden_present:
                high_risk_no_forbidden = False

    for stats in by_cat.values():
        if stats.total:
            stats.avg_selected /= stats.total

    by_cat_sorted = sorted(by_cat.values(), key=lambda s: s.category)

    return EvalSummary(
        backend=backend_label,
        total=total,
        exact=exact,
        partial=partial,
        fail=fail,
        forbidden_violations=forbidden_violations,
        fallback_correct=fallback_correct,
        fallback_evaluated=fallback_evaluated,
        human_review_correct=human_correct,
        human_review_evaluated=human_evaluated,
        by_category=by_cat_sorted,
        avg_elapsed_ms=avg_elapsed,
        high_risk_no_forbidden=high_risk_no_forbidden,
    )


# ────────────────────────────────────────────────────────────────────────────
# Reporting
# ────────────────────────────────────────────────────────────────────────────

def render_report(
    summary: EvalSummary,
    results: Sequence[CaseResult],
    *,
    show_failures: int = 10,
) -> str:
    lines: List[str] = []
    lines.append("=" * 72)
    lines.append("ResearchOS routing evaluation")
    lines.append("=" * 72)
    lines.append(f"Backend:        {summary.backend}")
    lines.append(f"Cases:          {summary.total}")
    lines.append(f"Avg latency:    {summary.avg_elapsed_ms:.0f} ms / prompt")
    lines.append("")
    lines.append("Overall:")
    lines.append(f"  exact pass:    {summary.exact:>3}/{summary.total} ({summary.exact_rate * 100:5.1f}%)")
    lines.append(f"  partial pass:  {summary.partial:>3}/{summary.total} ({summary.partial_rate * 100:5.1f}%)")
    lines.append(f"  fail:          {summary.fail:>3}/{summary.total} ({(1 - summary.partial_rate) * 100:5.1f}%)")
    lines.append(f"  forbidden:     {summary.forbidden_violations:>3} case(s) selected a forbidden agent")
    lines.append("")
    lines.append("Fallback / approval correctness:")
    if summary.fallback_evaluated:
        lines.append(f"  claude_fallback flag: {summary.fallback_correct:>3}/{summary.fallback_evaluated} "
                     f"({summary.fallback_rate * 100:5.1f}%)")
    else:
        lines.append("  claude_fallback flag: no cases set an expectation")
    if summary.human_review_evaluated:
        lines.append(f"  human_review flag:    {summary.human_review_correct:>3}/{summary.human_review_evaluated} "
                     f"({summary.human_rate * 100:5.1f}%)")
    else:
        lines.append("  human_review flag:    no cases set an expectation")
    lines.append(f"  high-risk/destructive prompts with NO forbidden: "
                 f"{'PASS' if summary.high_risk_no_forbidden else 'FAIL'}")
    lines.append("")
    lines.append("Per category:")
    lines.append(f"  {'category':<26} {'exact':>9} {'partial':>9} {'avg #agents':>13} {'forbid':>8}")
    for stats in summary.by_category:
        lines.append(
            f"  {stats.category:<26} "
            f"{stats.exact:>3}/{stats.total:<3} "
            f"{stats.exact_rate * 100:5.1f}%  "
            f"{stats.partial:>3}/{stats.total:<3} "
            f"{stats.avg_selected:>5.1f}        "
            f"{stats.forbidden_violations:>4}"
        )
    lines.append("")
    lines.append("Targets:")
    lines.append(f"  simple exact >= 90%:       {'PASS' if _simple_exact_rate(summary, results) >= 0.90 else 'FAIL'} "
                 f"(got {_simple_exact_rate(summary, results) * 100:.1f}%)")
    lines.append(f"  compound partial >= 95%:   {'PASS' if _compound_partial_rate(summary, results) >= 0.95 else 'FAIL'} "
                 f"(got {_compound_partial_rate(summary, results) * 100:.1f}%)")
    lines.append(f"  no forbidden on high-risk: {'PASS' if summary.high_risk_no_forbidden else 'FAIL'}")
    lines.append(f"  fallback >= 90%:           {'PASS' if summary.fallback_rate >= 0.90 else 'FAIL'} "
                 f"(got {summary.fallback_rate * 100:.1f}%)")
    lines.append("")

    failures = [r for r in results if not r.is_exact_pass]
    if failures and show_failures:
        # Rank: hard fails (missing/forbidden) first, then risk/fallback/human mismatches.
        failures.sort(key=lambda r: (
            -len(r.forbidden_present),
            -len(r.missing_expected),
            not r.risk_match,
            not r.fallback_match,
            not r.human_match,
            r.case_id,
        ))
        lines.append(f"Worst {min(show_failures, len(failures))} failures:")
        for r in failures[:show_failures]:
            lines.append("  " + "-" * 70)
            lines.append(f"  [{r.case_id}] {r.category}")
            lines.append(f"    prompt:   {r.prompt[:120]}")
            lines.append(f"    selected: {', '.join(r.selected_agents) or '(none)'}")
            if r.missing_expected:
                lines.append(f"    MISSING:  {', '.join(r.missing_expected)}")
            if r.forbidden_present:
                lines.append(f"    FORBIDDEN: {', '.join(r.forbidden_present)}")
            if not r.risk_match:
                lines.append(f"    risk:     got {r.risk_level!r}")
            if not r.fallback_match:
                lines.append(f"    fallback: got {r.requires_claude_fallback}")
            if not r.human_match:
                lines.append(f"    human:    got {r.human_review_required}")
            lines.append(f"    routing:  {r.routing_decision} / conf {r.routing_confidence:.2f}")
            if r.error:
                lines.append(f"    ERROR:    {r.error}")
        lines.append("")
    return "\n".join(lines)


def _simple_exact_rate(summary: EvalSummary, results: Sequence[CaseResult]) -> float:
    simple = [r for r in results if not _is_compound(r)]
    if not simple:
        return 1.0
    return sum(1 for r in simple if r.is_exact_pass) / len(simple)


def _compound_partial_rate(summary: EvalSummary, results: Sequence[CaseResult]) -> float:
    case_map = {c.id: c for c in CASES}
    compound = [r for r in results if (case_map.get(r.case_id) and case_map[r.case_id].is_compound)]
    if not compound:
        return 1.0
    return sum(1 for r in compound if r.is_partial_pass) / len(compound)


def _is_compound(r: CaseResult) -> bool:
    case_map = {c.id: c for c in CASES}
    case = case_map.get(r.case_id)
    return bool(case and case.is_compound)


# ────────────────────────────────────────────────────────────────────────────
# CLI
# ────────────────────────────────────────────────────────────────────────────

def _build_router(*, keyword_only: bool, repo_root: Path) -> Router:
    """Build a Router for the eval, with semantic on/off."""
    semantic = OllamaSemanticRouter(repo_root=repo_root)
    return Router(
        repo_root=repo_root,
        semantic_router=semantic,
        claude_fallback=FlagOnlyFallback(),
        enable_semantic=(not keyword_only),
    )


def _filter_cases(
    cases: Sequence[BenchmarkCase],
    *,
    category: Optional[str] = None,
    case_id: Optional[str] = None,
    limit: Optional[int] = None,
) -> List[BenchmarkCase]:
    out = list(cases)
    if category:
        out = [c for c in out if c.category == category]
    if case_id:
        out = [c for c in out if c.id == case_id]
    if limit:
        out = out[:limit]
    return out


def cmd_routing_eval(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo).resolve()
    cases = _filter_cases(
        CASES,
        category=args.category,
        case_id=args.case_id,
        limit=args.limit,
    )
    if not cases:
        print("No matching cases.")
        return 1
    router = _build_router(keyword_only=args.keyword_only, repo_root=repo_root)
    backend = "keyword-only" if args.keyword_only else f"ollama+keyword (timeout {args.timeout}s)"
    if args.timeout:
        router.semantic_router.timeout_s = args.timeout

    if args.progress:
        print(f"Evaluating {len(cases)} case(s) against backend={backend!r}...", file=sys.stderr)

    results = evaluate(cases, router, progress=args.progress)
    summary = summarize(results, backend_label=backend)

    if args.json:
        payload = {
            "backend": summary.backend,
            "summary": {
                "total": summary.total,
                "exact": summary.exact,
                "partial": summary.partial,
                "fail": summary.fail,
                "exact_rate": summary.exact_rate,
                "partial_rate": summary.partial_rate,
                "forbidden_violations": summary.forbidden_violations,
                "fallback_correct": summary.fallback_correct,
                "fallback_evaluated": summary.fallback_evaluated,
                "fallback_rate": summary.fallback_rate,
                "human_review_correct": summary.human_review_correct,
                "human_review_evaluated": summary.human_review_evaluated,
                "high_risk_no_forbidden": summary.high_risk_no_forbidden,
                "avg_elapsed_ms": summary.avg_elapsed_ms,
                "simple_exact_rate": _simple_exact_rate(summary, results),
                "compound_partial_rate": _compound_partial_rate(summary, results),
                "by_category": [asdict(s) for s in summary.by_category],
            },
            "results": [r.to_dict() for r in results],
        }
        text = json.dumps(payload, indent=2, default=str)
    else:
        text = render_report(summary, results, show_failures=args.show_failures)

    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
        print(f"wrote {args.out}")
    else:
        print(text)

    # Exit non-zero if any failures so this can gate CI later.
    return 0 if summary.partial == summary.total else 1


def add_subparser(subparsers) -> None:
    sp = subparsers.add_parser(
        "routing-eval",
        help="Run the routing benchmark against the live Router.",
    )
    sp.add_argument("--category", default=None,
                    help="Only evaluate this category (e.g. literature, md_validation).")
    sp.add_argument("--case-id", default=None,
                    help="Only evaluate this specific case id (e.g. lit-001).")
    sp.add_argument("--limit", type=int, default=None,
                    help="Cap the number of cases evaluated.")
    sp.add_argument("--keyword-only", action="store_true",
                    help="Skip Ollama, use the deterministic keyword router only.")
    sp.add_argument("--timeout", type=float, default=15.0,
                    help="Ollama call timeout in seconds (default 15).")
    sp.add_argument("--json", action="store_true",
                    help="Emit JSON instead of a text report.")
    sp.add_argument("--out", default=None,
                    help="Write report to this path instead of stdout.")
    sp.add_argument("--show-failures", type=int, default=10,
                    help="Number of worst failures to show in the text report.")
    sp.add_argument("--progress", action="store_true",
                    help="Print per-case progress to stderr.")
    sp.set_defaults(func=cmd_routing_eval)


__all__ = [
    "CaseResult",
    "EvalSummary",
    "CategoryStats",
    "evaluate",
    "summarize",
    "render_report",
    "cmd_routing_eval",
    "add_subparser",
]
