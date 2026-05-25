"""Routing evaluation harness.

``research_os.eval.routing_benchmark.CASES`` is the hand-curated dataset of
representative prompts across every major ResearchOS intent. The router is
expected to behave like a *model*: we evaluate it against this dataset and
track per-category accuracy, fallback correctness, and worst failing
examples.

The evaluator (``routing_eval``) is a CLI tool, not a pytest target, because
it talks to real Ollama by default. The deterministic regression tests live
in ``tests/test_routing_regressions.py`` and use injected fake backends.
"""

from research_os.eval.routing_benchmark import CASES, BenchmarkCase
from research_os.eval.routing_eval import (
    CaseResult,
    EvalSummary,
    evaluate,
    render_report,
    summarize,
)

__all__ = [
    "CASES",
    "BenchmarkCase",
    "CaseResult",
    "EvalSummary",
    "evaluate",
    "summarize",
    "render_report",
]
