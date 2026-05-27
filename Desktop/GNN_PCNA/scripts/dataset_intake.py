#!/usr/bin/env python3
"""Governed dataset/source intake CLI for GNN-PCNA Phase 2.

This tool acquires or links official source assets into quarantined raw intake
folders only. It does not adopt datasets, generate graphs, train models, run
MD, or make scientific claims.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from phase2_intake.adapters.registry import ADAPTERS, ALL_SAFE_SOURCES  # noqa: E402
from phase2_intake.config import DEFAULT_MAX_DATASET_BYTES, DEFAULT_MAX_FILE_BYTES  # noqa: E402
from phase2_intake.controller import print_summary, regenerate_reports, run_intake  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Governed Phase 2 dataset/source intake")
    subparsers = parser.add_subparsers(dest="command", required=True)

    for name in ["discover", "acquire"]:
        sub = subparsers.add_parser(name)
        sub.add_argument("--source", required=True, choices=sorted(set(ADAPTERS) | {"all_safe"}))
        sub.add_argument("--target", action="append", default=[])
        sub.add_argument("--dry-run", action="store_true", help="record planned actions without downloading response bodies")
        sub.add_argument("--max-file-mb", type=int, default=DEFAULT_MAX_FILE_BYTES // (1024 * 1024))
        sub.add_argument("--max-dataset-gb", type=int, default=DEFAULT_MAX_DATASET_BYTES // (1024 * 1024 * 1024))

    subparsers.add_parser("report")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    command = " ".join(sys.argv)
    if args.command == "report":
        summary = regenerate_reports(command)
        print_summary(summary)
        return 0

    dry_run = True if args.command == "discover" else bool(args.dry_run)
    summary = run_intake(
        command=command,
        sources=[args.source],
        targets=args.target,
        dry_run=dry_run,
        max_file_bytes=args.max_file_mb * 1024 * 1024,
        max_dataset_bytes=args.max_dataset_gb * 1024 * 1024 * 1024,
    )
    print_summary(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

