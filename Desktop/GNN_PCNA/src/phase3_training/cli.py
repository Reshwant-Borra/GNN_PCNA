"""Dry-run-safe Phase 3 trainer entrypoint."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from phase3_data.provenance import command_from_argv, process_context
from phase3_training.gates import TrainingGateError, training_gate_status


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="Workspace root.")
    parser.add_argument(
        "--real-training",
        action="store_true",
        help="Attempt real training. This is expected to fail until human pipeline sign-off exists.",
    )
    parser.add_argument(
        "--human-pipeline-signoff",
        type=Path,
        help="Future human sign-off evidence packet for the first training gate.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        status = training_gate_status(args.real_training, args.human_pipeline_signoff)
    except TrainingGateError as exc:
        parser.exit(2, f"Phase 3 training blocked: {exc}\n")
    payload = {
        "artifact_type": "phase3_training_dry_run",
        **process_context(Path(args.root), command_from_argv()),
        **status,
        "governance": [
            "docs/scientific_governance/08_MODEL_ARCHITECTURE_CONSTRAINTS.md",
            "docs/scientific_governance/19_STOP_CONDITIONS.md",
            "docs/scientific_governance/26_HUMAN_REVIEW_GATES.md",
        ],
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

