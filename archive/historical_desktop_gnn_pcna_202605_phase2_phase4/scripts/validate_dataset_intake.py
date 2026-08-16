#!/usr/bin/env python3
"""Validate governed dataset intake scaffolding and generated manifests.

This validator is read-only. It does not download files, parse scientific
labels, generate graphs, train models, run MD, or approve data.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from phase2_intake.config import (  # noqa: E402
    DATASET_INVENTORY_CSV,
    DATASET_INVENTORY_JSON,
    DOWNLOAD_MANIFEST,
    RAW_INTAKE_ROOT,
    RAW_SOURCE_DIRS,
    REPORT_PATHS,
)
from phase2_intake.models import (  # noqa: E402
    DOWNLOAD_ACTIONS,
    FORBIDDEN_READINESS_LABELS,
    LICENSE_STATUSES,
    SCHEMA_STATUSES,
    TRUST_LEVELS,
)


REQUIRED_CODE_FILES = [
    "scripts/dataset_intake.py",
    "src/phase2_intake/controller.py",
    "src/phase2_intake/adapters/base.py",
    "src/phase2_intake/io/downloader.py",
    "src/phase2_intake/io/manifest.py",
]


def validate_manifest() -> list[str]:
    errors: list[str] = []
    if not DOWNLOAD_MANIFEST.exists():
        return errors
    with DOWNLOAD_MANIFEST.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                errors.append(f"{DOWNLOAD_MANIFEST}:{line_number}: invalid JSON: {exc}")
                continue
            required = [
                "timestamp",
                "source_name",
                "target",
                "url",
                "action",
                "license_status",
                "schema_status",
                "trust_level",
                "quarantine_status",
            ]
            for field in required:
                if field not in row:
                    errors.append(f"{DOWNLOAD_MANIFEST}:{line_number}: missing {field}")
            if row.get("action") not in DOWNLOAD_ACTIONS:
                errors.append(f"{DOWNLOAD_MANIFEST}:{line_number}: invalid action {row.get('action')}")
            if row.get("license_status") not in LICENSE_STATUSES:
                errors.append(f"{DOWNLOAD_MANIFEST}:{line_number}: invalid license_status {row.get('license_status')}")
            if row.get("schema_status") not in SCHEMA_STATUSES:
                errors.append(f"{DOWNLOAD_MANIFEST}:{line_number}: invalid schema_status {row.get('schema_status')}")
            if row.get("trust_level") not in TRUST_LEVELS:
                errors.append(f"{DOWNLOAD_MANIFEST}:{line_number}: invalid trust_level {row.get('trust_level')}")
            if row.get("quarantine_status") != "raw_unverified":
                errors.append(f"{DOWNLOAD_MANIFEST}:{line_number}: quarantine_status must be raw_unverified")
            local_path = row.get("local_path")
            if local_path:
                resolved = (ROOT / local_path).resolve()
                raw_root = RAW_INTAKE_ROOT.resolve()
                if raw_root != resolved and raw_root not in resolved.parents:
                    errors.append(f"{DOWNLOAD_MANIFEST}:{line_number}: local_path escapes raw intake: {local_path}")
    return errors


def validate_text_forbidden_labels() -> list[str]:
    errors: list[str] = []
    paths = list(REPORT_PATHS.values()) + [DATASET_INVENTORY_JSON, DATASET_INVENTORY_CSV]
    for path in paths:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for forbidden in FORBIDDEN_READINESS_LABELS:
            if forbidden in text:
                errors.append(f"{path}: contains forbidden readiness label {forbidden}")
    return errors


def main() -> int:
    errors: list[str] = []
    for relative in REQUIRED_CODE_FILES:
        if not (ROOT / relative).is_file():
            errors.append(f"missing required code file: {relative}")
    for source_dir in RAW_SOURCE_DIRS:
        path = RAW_INTAKE_ROOT / source_dir
        if path.exists() and not path.is_dir():
            errors.append(f"raw intake path is not a directory: {path}")
    errors.extend(validate_manifest())
    errors.extend(validate_text_forbidden_labels())

    if errors:
        print("Dataset intake validation: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Dataset intake validation: PASS")
    print("No training, graph, split-freeze, label-freeze, MD, or claim readiness is granted.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

