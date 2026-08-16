#!/usr/bin/env python3
"""Check Phase 2 governed data-foundation scaffold status.

This script is intentionally read-only. It validates that required foundation
artifacts exist and that JSON registries parse. It does not inspect, transform,
train on, or claim from scientific data.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = [
    "reports/phase2/source_of_truth_audit.md",
    "reports/phase2/project_scope_audit.md",
    "reports/phase2/governance_reading_checklist.md",
    "data/registries/assumption_registry.json",
    "reports/phase2/assumption_audit.md",
    "reports/phase2/scientific_uncertainty_register.md",
    "data/registries/source_registry.json",
    "reports/phase2/source_registry.md",
    "reports/phase2/source_audit.md",
    "reports/phase2/benchmark_limitations.md",
    "docs/scientific_governance/DATASET_REGISTRY.md",
    "reports/phase2/dataset_audit.md",
    "data/registries/data_lifecycle_registry.json",
    "reports/phase2/data_lifecycle_audit.md",
    "reports/phase2/split_freeze_plan.md",
    "data/splits/phase2_split_TEMPLATE.json",
    "reports/phase2/label_freeze_plan.md",
    "data/labels/phase2_labels_TEMPLATE.json",
    "reports/phase2/human_review_log.md",
    "reports/phase2/biological_data_sanity_review.md",
    "reports/phase2/readiness_gate.md",
]

JSON_FILES = [
    "data/registries/assumption_registry.json",
    "data/registries/source_registry.json",
    "data/registries/data_lifecycle_registry.json",
    "data/splits/phase2_split_TEMPLATE.json",
    "data/labels/phase2_labels_TEMPLATE.json",
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true", help="emit machine-readable status")
    args = parser.parse_args()

    missing = [path for path in REQUIRED_FILES if not (ROOT / path).is_file()]
    invalid_json: list[dict[str, str]] = []

    for path in JSON_FILES:
        try:
            with (ROOT / path).open("r", encoding="utf-8") as handle:
                json.load(handle)
        except Exception as exc:  # pragma: no cover - diagnostic path
            invalid_json.append({"path": path, "error": str(exc)})

    status = {
        "foundation_scaffold_complete": not missing and not invalid_json,
        "ready_for_dataset_planning": not missing and not invalid_json,
        "ready_for_training": False,
        "missing_files": missing,
        "invalid_json": invalid_json,
        "training_blockers": [
            "No accepted dataset.",
            "No frozen split.",
            "No frozen label definition.",
            "No biological data sanity PASS.",
            "No human review approvals.",
            "No graph audit.",
        ],
    }

    if args.json:
        print(json.dumps(status, indent=2))
    else:
        print(f"Foundation scaffold complete: {status['foundation_scaffold_complete']}")
        print(f"Ready for dataset planning: {status['ready_for_dataset_planning']}")
        print("Ready for training: False")
        if missing:
            print("Missing files:")
            for path in missing:
                print(f"  - {path}")
        if invalid_json:
            print("Invalid JSON:")
            for item in invalid_json:
                print(f"  - {item['path']}: {item['error']}")
        print("Training remains blocked by governance gates.")

    return 0 if not missing and not invalid_json else 1


if __name__ == "__main__":
    raise SystemExit(main())
