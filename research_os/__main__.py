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


def cmd_paper_figures(args: argparse.Namespace) -> int:
    from paper_engine.figures import md as md_mod
    from paper_engine.figures import render
    from paper_engine import registration

    results = render.render_all(only=args.only)
    print(f"Rendered {len(results)} figure(s) to paper/figures/.")
    try:
        md_results = md_mod.render_md(stride=args.md_stride)
        print(f"Rendered {len(md_results)} MD figure(s).")
    except md_mod.MDUnavailable as exc:
        print(f"MD figures skipped (real-data guard): {exc}")
    if not args.no_register:
        ids = registration.register_figures()
        print(f"Registered {len(ids)} new figure artifact(s) in artifact_registry.json.")
    return 0


def cmd_paper(args: argparse.Namespace) -> int:
    from pathlib import Path as _Path

    from paper_engine.manuscript import build as build_mod
    from paper_engine.manuscript import self_review
    from paper_engine import registration

    res = build_mod.build_paper(
        regenerate_figures=not args.no_figures, author=args.author, date=args.date)
    print("=" * 60)
    print(f"DOCX:     {res.docx_path}")
    print(f"Markdown: {res.markdown_path}")
    print(f"Manifest: {res.manifest_path}")
    print(f"Sections: {res.section_count} ({res.used_llm_sections} via local LLM)")
    print(f"Figures:  {', '.join(res.figures_used) or '(none)'}")
    if res.banned_hits:
        print(f"WARNING — banned-phrase hits remain: {res.banned_hits}")

    if not args.no_register:
        registration.register_figures()
        registration.register_md_results()
        registration.register_paper_draft(_Path(res.docx_path), _Path(res.markdown_path))

    review = self_review.review(_Path(res.markdown_path))
    print("-" * 60)
    print(f"SELF-REVIEW (claim audit): blocked={review.blocked} "
          f"human_review_required={review.human_review_required}")
    for f in review.findings:
        print(f"  - {f}")
    print("-" * 60)
    print("HUMAN SIGN-OFF REQUIRED before any submission. ResearchOS does not "
          "auto-approve final manuscripts; the test set remains unevaluated.")
    return 0


def cmd_paper_corpus(args: argparse.Namespace) -> int:
    from paper_engine.corpus import bulk_sources, download_manager

    print(f"Discovering open-access works (per-query={args.per_query}) ...")
    records = bulk_sources.discover(per_query=args.per_query)
    print(f"Discovered {len(records)} unique OA works with direct PDFs.")
    if args.discover_only:
        return 0
    stats = download_manager.download_corpus(
        records, max_gb=args.max_gb, max_files=args.max_files)
    print(f"Downloaded {stats.downloaded} new (skipped {stats.skipped_existing} existing, "
          f"{stats.skipped_robots} robots-blocked, {stats.failed} failed); "
          f"{stats.total_bytes/1e9:.2f} GB total.")
    if args.index:
        from paper_engine.corpus import index
        print("Building BM25 index ...")
        print(index.build())
    return 0


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

    sp = sub.add_parser("paper-figures", help="Render publication figures from real data and register them.")
    sp.add_argument("--only", nargs="*", default=None, help="Subset of figure ids.")
    sp.add_argument("--md-stride", type=int, default=10, help="Frame stride for MD analysis.")
    sp.add_argument("--no-register", action="store_true", help="Do not write artifact registry entries.")
    sp.set_defaults(func=cmd_paper_figures)

    sp = sub.add_parser("paper", help="Generate the competition paper draft (figures + manuscript.docx) and self-review.")
    sp.add_argument("--no-figures", action="store_true", help="Skip figure regeneration.")
    sp.add_argument("--no-register", action="store_true", help="Do not register artifacts.")
    sp.add_argument("--author", default="[Author]", help="Author name for the title block.")
    sp.add_argument("--date", default="", help="Date string for the title block.")
    sp.set_defaults(func=cmd_paper)

    sp = sub.add_parser("paper-corpus", help="Discover + download legal open-access literature; optionally index it.")
    sp.add_argument("--max-gb", type=float, default=30.0, help="Total download cap in GB.")
    sp.add_argument("--max-files", type=int, default=None, help="Optional cap on file count.")
    sp.add_argument("--per-query", type=int, default=300, help="OA works per topic query.")
    sp.add_argument("--discover-only", action="store_true", help="List sources without downloading.")
    sp.add_argument("--index", action="store_true", help="Build the BM25 index after download.")
    sp.set_defaults(func=cmd_paper_corpus)

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
