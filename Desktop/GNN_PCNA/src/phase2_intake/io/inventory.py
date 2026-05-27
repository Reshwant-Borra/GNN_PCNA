"""Dataset inventory generation from the append-only download manifest."""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from phase2_intake.models import utc_now


def build_inventory(rows: list[dict[str, Any]]) -> dict[str, Any]:
    grouped: dict[str, dict[str, Any]] = {}
    by_source: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_source[row.get("source_name", "unknown")].append(row)

    for source_name, source_rows in sorted(by_source.items()):
        downloaded = [row for row in source_rows if row.get("action") == "downloaded"]
        linked = [row for row in source_rows if row.get("action") == "linked_only"]
        failed = [row for row in source_rows if row.get("action") == "failed"]
        skipped = [row for row in source_rows if row.get("action") == "skipped"]
        latest = source_rows[-1]
        grouped[source_name] = {
            "source_name": source_name,
            "source_type": "official_source_intake",
            "official_homepage": latest.get("official_url"),
            "downloaded_files": sorted({row.get("local_path") for row in downloaded if row.get("local_path")}),
            "linked_only_assets": sorted({row.get("url") for row in linked if row.get("url")}),
            "failed_attempts": len(failed),
            "skipped_attempts": len(skipped),
            "total_downloaded_bytes": sum(row.get("file_size_bytes") or 0 for row in downloaded),
            "license_status": latest.get("license_status", "LICENSE_UNRESOLVED"),
            "terms_url": latest.get("official_url"),
            "schema_status": latest.get("schema_status", "SCHEMA_UNKNOWN"),
            "contains_structures": any(bool(row.get("contains_structures")) for row in source_rows),
            "contains_labels": any(bool(row.get("contains_labels")) for row in source_rows),
            "contains_splits": any(bool(row.get("contains_splits")) for row in source_rows),
            "contains_metadata": any(bool(row.get("contains_metadata")) for row in source_rows),
            "contains_code": any(bool(row.get("contains_code")) for row in source_rows),
            "intended_role": latest.get("intended_role", "source acquisition"),
            "lifecycle_status": "quarantined" if downloaded else "candidate",
            "adoption_status": "not_adopted",
            "warnings": sorted(
                {
                    str(row.get("reason_skipped") or row.get("error") or "")
                    for row in source_rows
                    if row.get("reason_skipped") or row.get("error")
                }
            ),
            "unresolved_questions": [
                "License, schema, provenance, leakage, and human review remain unresolved for training use."
            ],
            "last_updated": utc_now(),
        }

    return {
        "schema_version": "phase2_dataset_inventory_v0",
        "created_or_updated_at": utc_now(),
        "final_status": "RAW_ASSETS_ACQUIRED_NOT_VERIFIED"
        if any(row.get("action") == "downloaded" for row in rows)
        else "NO_DATASETS_ACQUIRED",
        "adoption_status": "not_adopted",
        "items": list(grouped.values()),
    }


def write_inventory_json(path: Path, inventory: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(inventory, handle, indent=2, sort_keys=True)
        handle.write("\n")


def write_inventory_csv(path: Path, inventory: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "source_name",
        "source_type",
        "official_homepage",
        "downloaded_files",
        "linked_only_assets",
        "failed_attempts",
        "skipped_attempts",
        "total_downloaded_bytes",
        "license_status",
        "schema_status",
        "contains_structures",
        "contains_labels",
        "contains_splits",
        "contains_metadata",
        "contains_code",
        "intended_role",
        "lifecycle_status",
        "adoption_status",
        "warnings",
        "unresolved_questions",
        "last_updated",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for item in inventory.get("items", []):
            row = {field: item.get(field) for field in fields}
            for field in ["downloaded_files", "linked_only_assets", "warnings", "unresolved_questions"]:
                row[field] = "; ".join(row[field] or [])
            writer.writerow(row)
