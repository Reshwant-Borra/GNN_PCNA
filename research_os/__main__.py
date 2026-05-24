"""Command-line interface.

Subcommands:

    route                Show the orchestration plan for a request.
    run                  Route + execute a request end-to-end.
    audit                Run the full audit workflow on the repo.
    verify-metrics       Run the metric-verification workflow.
    validate-md          Run the MD validation workflow.
    claim-audit          Run the claim/paper audit workflow.
    readiness            Run the submission-readiness workflow.
    bootstrap            Create research_os_memory/ and research_os_registries/.
    inspect-memory       Print the canonical memory headers.
    inspect-registries   Validate the registries and report counts.

Examples:

    python -m research_os route "Can we say MD validated the cryptic pocket?"
    python -m research_os audit --repo .
    python -m research_os claim-audit --paper manuscript.md
    python -m research_os readiness
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional

from research_os.memory.store import CANONICAL_FILES, MemoryStore
from research_os.orchestrator import Orchestrator
from research_os.registries.store import REGISTRY_NAMES, RegistryStore, ensure_registries_initialized
from research_os.workflows import (
    run_claim_audit,
    run_full_audit,
    run_md_validation,
    run_metric_verification,
    run_submission_readiness,
    run_training_eval,
)


def _print_plan(plan_dict: dict) -> None:
    print(json.dumps(plan_dict, indent=2, default=str))


def _print_outcome(outcome) -> int:
    result = outcome.result
    print("=" * 60)
    print(f"WORKFLOW: {outcome.name}")
    print(f"REPORT:   {outcome.report.markdown}")
    print(f"BLOCKED:  {result.blocked}")
    if result.blocked:
        print(f"  reason: {result.block_reason}")
    print(f"HUMAN REVIEW REQUIRED: {result.human_review_required}")
    for reason in result.human_review_reasons:
        print(f"  - {reason}")
    print(f"GATE STATUS:")
    for gate, status in result.gate_status.items():
        marker = "X" if status in ("fail", "blocked", "stale") else (
            "!" if status in ("warning", "not_started") else "."
        )
        print(f"  [{marker}] {gate:<20s} {status}")
    print(f"AGENTS RUN: {len(result.agent_outputs)}")
    return 1 if result.blocked else 0


def cmd_route(args: argparse.Namespace) -> int:
    orch = Orchestrator(repo_root=args.repo)
    orch.bootstrap()
    plan = orch.route(args.message)
    _print_plan(plan.to_dict())
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    orch = Orchestrator(repo_root=args.repo)
    orch.bootstrap()
    result = orch.run(args.message)
    print(json.dumps(result.to_dict(), indent=2, default=str))
    return 1 if result.blocked else 0


def cmd_audit(args: argparse.Namespace) -> int:
    return _print_outcome(run_full_audit(repo_root=args.repo))


def cmd_training_eval(args: argparse.Namespace) -> int:
    return _print_outcome(run_training_eval(repo_root=args.repo))


def cmd_verify_metrics(args: argparse.Namespace) -> int:
    return _print_outcome(run_metric_verification(repo_root=args.repo, metrics_path=args.metrics))


def cmd_validate_md(args: argparse.Namespace) -> int:
    return _print_outcome(run_md_validation(repo_root=args.repo, md_report_dir=args.report))


def cmd_claim_audit(args: argparse.Namespace) -> int:
    return _print_outcome(run_claim_audit(repo_root=args.repo, paper_path=args.paper))


def cmd_readiness(args: argparse.Namespace) -> int:
    return _print_outcome(run_submission_readiness(repo_root=args.repo, paper_path=args.paper))


def cmd_bootstrap(args: argparse.Namespace) -> int:
    orch = Orchestrator(repo_root=args.repo)
    orch.bootstrap()
    print(f"memory:     {orch.memory_dir}")
    for name in CANONICAL_FILES:
        marker = "+" if orch.memory_store.exists(name) else "-"
        print(f"  [{marker}] {name}")
    print(f"registries: {orch.registries_dir}")
    for name in REGISTRY_NAMES:
        path = orch.registry_store.path_for(name)
        marker = "+" if path.exists() else "-"
        print(f"  [{marker}] {name}.json")
    return 0


def cmd_inspect_memory(args: argparse.Namespace) -> int:
    orch = Orchestrator(repo_root=args.repo)
    orch.bootstrap()
    for name in CANONICAL_FILES:
        if not orch.memory_store.exists(name):
            print(f"- {name}: MISSING")
            continue
        m = orch.memory_store.read(name)
        print(f"- {name}: status={m.status} updated={m.last_updated} by={m.updated_by}")
    return 0


def cmd_inspect_registries(args: argparse.Namespace) -> int:
    orch = Orchestrator(repo_root=args.repo)
    orch.bootstrap()
    bad = 0
    for name in REGISTRY_NAMES:
        issues = orch.registry_store.validate(name)
        entries = orch.registry_store.all_entries(name)
        tag = "ok" if not issues else f"{len(issues)} issue(s)"
        print(f"- {name}: {len(entries)} entries — {tag}")
        for issue in issues:
            print(f"    !! {issue}")
            bad += 1
    return 1 if bad else 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="research_os",
        description="GNN ResearchOS - conservative research operating system.",
    )
    p.add_argument("--repo", default=".", help="Repository root (default: cwd).")
    sub = p.add_subparsers(dest="command", required=True)

    sp = sub.add_parser("route", help="Show routing plan for a request.")
    sp.add_argument("message", help="The user request.")
    sp.set_defaults(func=cmd_route)

    sp = sub.add_parser("run", help="Route + execute a request and print the JSON result.")
    sp.add_argument("message", help="The user request.")
    sp.set_defaults(func=cmd_run)

    sp = sub.add_parser("audit", help="Run the full audit workflow.")
    sp.set_defaults(func=cmd_audit)

    sp = sub.add_parser("training-eval", help="Run the training + evaluation audit workflow.")
    sp.set_defaults(func=cmd_training_eval)

    sp = sub.add_parser("verify-metrics", help="Run the metric-verification workflow.")
    sp.add_argument("--metrics", default=None, help="Metrics JSON file to anchor the audit.")
    sp.set_defaults(func=cmd_verify_metrics)

    sp = sub.add_parser("validate-md", help="Run the MD validation workflow.")
    sp.add_argument("--report", default=None, help="MD report directory.")
    sp.set_defaults(func=cmd_validate_md)

    sp = sub.add_parser("claim-audit", help="Run the claim / paper audit workflow.")
    sp.add_argument("--paper", default=None, help="Paper draft to audit.")
    sp.set_defaults(func=cmd_claim_audit)

    sp = sub.add_parser("readiness", help="Run the submission readiness workflow.")
    sp.add_argument("--paper", default=None, help="Final paper draft.")
    sp.set_defaults(func=cmd_readiness)

    sp = sub.add_parser("bootstrap", help="Create memory + registry files if missing.")
    sp.set_defaults(func=cmd_bootstrap)

    sp = sub.add_parser("inspect-memory", help="Show canonical memory file headers.")
    sp.set_defaults(func=cmd_inspect_memory)

    sp = sub.add_parser("inspect-registries", help="Validate registries and report counts.")
    sp.set_defaults(func=cmd_inspect_registries)

    return p


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
