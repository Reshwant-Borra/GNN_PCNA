"""Markdown report generation for governed dataset intake."""

from __future__ import annotations

import platform
from pathlib import Path

from phase2_intake.config import REPORT_PATHS
from phase2_intake.models import FORBIDDEN_READINESS_LABELS, RunSummary, utc_now


def _write_report(path: Path, title: str, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    update_note = ""
    if path.exists():
        update_note = (
            "\n## Update Note\n\n"
            f"- Updated at: {utc_now()}\n"
            "- Prior useful content was superseded by manifest-derived regenerated sections.\n"
            "- Reason: governed dataset intake run/report regeneration.\n"
        )
    content = f"# {title}\n\n{body}{update_note}\n"
    for forbidden in FORBIDDEN_READINESS_LABELS:
        content = content.replace(forbidden, f"FORBIDDEN_STATUS_{forbidden}")
    path.write_text(content, encoding="utf-8")


def provenance_block(summary: RunSummary) -> str:
    return (
        "## Provenance\n\n"
        f"- Date: {utc_now()}\n"
        f"- Script/command used: `{summary.command}`\n"
        "- Source paths inspected: `data/registries/download_manifest.jsonl`, `data/raw_intake/`, source adapter official URLs\n"
        "- Confidence level: high for local manifest/report generation; uncertain for external source completeness until official audits finish\n"
        "- Evidence status: verified for local files and manifest rows; inferred/uncertain for external source content not downloaded\n"
        f"- Python: `{platform.python_version()}`\n"
        "- Unresolved questions: licenses, schemas, leakage, PCNA/homolog screening, label definitions, and human approvals remain unresolved\n"
    )


def generate_reports(summary: RunSummary, inventory: dict) -> None:
    items = inventory.get("items", [])
    rows = summary.manifest_entries
    downloaded = [row for row in rows if row.action == "downloaded"]
    skipped = [row for row in rows if row.action == "skipped"]
    linked = [row for row in rows if row.action == "linked_only"]
    failed = [row for row in rows if row.action == "failed"]

    common_status = (
        "## Conservative Status\n\n"
        f"- Final status: `{summary.final_status}`\n"
        "- Adoption status: `not_adopted`\n"
        "- Quarantine status: `raw_unverified`\n"
        "- Training, graph generation, split freeze, label freeze, evaluation, MD, and claims remain blocked.\n\n"
    )

    acquisition_lines = [
        "## Acquisition Summary",
        "",
        f"- Dry run: `{summary.dry_run}`",
        f"- Sources: {', '.join(summary.source_names) if summary.source_names else 'none'}",
        f"- Downloaded: {len(downloaded)}",
        f"- Skipped: {len(skipped)}",
        f"- Linked only: {len(linked)}",
        f"- Failed: {len(failed)}",
        f"- Downloaded bytes: {summary.total_downloaded_bytes}",
        f"- Stop markers: {', '.join(summary.stop_markers) if summary.stop_markers else 'none'}",
    ]
    _write_report(
        REPORT_PATHS["acquisition_log"],
        "Dataset Acquisition Log",
        common_status + "\n".join(acquisition_lines) + "\n\n" + provenance_block(summary),
    )

    inventory_lines = ["## File Inventory", ""]
    for item in items:
        inventory_lines.append(
            f"- `{item['source_name']}`: {len(item.get('downloaded_files', []))} downloaded, "
            f"{len(item.get('linked_only_assets', []))} linked-only, "
            f"{item.get('total_downloaded_bytes', 0)} bytes, status `{item.get('lifecycle_status')}`"
        )
    _write_report(
        REPORT_PATHS["file_inventory"],
        "Dataset File Inventory",
        common_status + "\n".join(inventory_lines) + "\n\n" + provenance_block(summary),
    )

    license_lines = ["## License And Terms", ""]
    for item in items:
        license_lines.append(
            f"- `{item['source_name']}`: license status `{item.get('license_status')}`, terms URL `{item.get('terms_url')}`"
        )
    _write_report(
        REPORT_PATHS["license_review"],
        "License And Terms Review",
        common_status + "\n".join(license_lines) + "\n\n" + provenance_block(summary),
    )

    schema_lines = ["## Schema First Pass", ""]
    for item in items:
        schema_lines.append(
            f"- `{item['source_name']}`: schema status `{item.get('schema_status')}`; "
            f"structures={item.get('contains_structures')}, labels={item.get('contains_labels')}, "
            f"splits={item.get('contains_splits')}, metadata={item.get('contains_metadata')}, code={item.get('contains_code')}"
        )
    _write_report(
        REPORT_PATHS["schema_first_pass"],
        "Dataset Schema First Pass",
        common_status + "\n".join(schema_lines) + "\n\n" + provenance_block(summary),
    )

    recommendation = (
        "## Recommendation\n\n"
        "- Keep all downloaded or linked assets quarantined.\n"
        "- Do not adopt any dataset for graph generation or training from this intake step.\n"
        "- Next required steps are license review, schema audit, hash verification, PCNA/homolog screening, leakage audit, and human review.\n\n"
    )
    _write_report(
        REPORT_PATHS["adoption_recommendation"],
        "Dataset Adoption Recommendation",
        common_status + recommendation + provenance_block(summary),
    )

    all_downloaded_paths: list[str] = []
    all_linked_urls: list[str] = []
    all_warnings: list[str] = []
    for item in items:
        all_downloaded_paths.extend(item.get("downloaded_files", []))
        all_linked_urls.extend(item.get("linked_only_assets", []))
        all_warnings.extend(item.get("warnings", []))

    friend = (
        "## What Was Downloaded\n\n"
        + "\n".join(f"- `{path}`" for path in all_downloaded_paths)
        + ("\n" if all_downloaded_paths else "- Nothing downloaded.\n")
        + "\n## What Was Only Linked\n\n"
        + "\n".join(f"- {url}" for url in all_linked_urls)
        + ("\n" if all_linked_urls else "- Nothing linked-only.\n")
        + "\n## What Could Not Be Accessed Or Was Skipped\n\n"
        + "\n".join(f"- {warning}" for warning in all_warnings if warning)
        + ("\n" if any(all_warnings) else "- No skipped or failed rows are present in the inventory summary.\n")
        + "\n## Manual Approval Still Needed\n\n"
        "- Any single file/archive over 500 MB.\n"
        "- Any dataset over 20 GB.\n"
        "- Any unclear/restricted license.\n"
        "- Any third-party mirror use beyond linked-only.\n"
        "- Any dataset adoption, split freeze, or label freeze.\n\n"
    )
    _write_report(
        REPORT_PATHS["friend_report"],
        "Friend Dataset Acquisition Report",
        common_status + friend + provenance_block(summary),
    )
