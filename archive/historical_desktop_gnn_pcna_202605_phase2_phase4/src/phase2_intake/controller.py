"""Controller for governed dataset/source intake."""

from __future__ import annotations

import sys
from pathlib import Path

from phase2_intake.adapters.base import AdapterContext
from phase2_intake.adapters.registry import ALL_SAFE_SOURCES, get_adapter
from phase2_intake.config import (
    BULK_APPROVALS,
    DATASET_INVENTORY_CSV,
    DATASET_INVENTORY_JSON,
    DEFAULT_MAX_DATASET_BYTES,
    DEFAULT_MAX_FILE_BYTES,
    DOWNLOAD_MANIFEST,
    RAW_INTAKE_ROOT,
    RAW_SOURCE_DIRS,
    ROOT,
)
from phase2_intake.io.approvals import has_bulk_approval
from phase2_intake.io.downloader import download_url, guarded_target, infer_filename, probe_url
from phase2_intake.io.hasher import sha256_file
from phase2_intake.io.inventory import build_inventory, write_inventory_csv, write_inventory_json
from phase2_intake.io.manifest import ManifestWriter, read_manifest
from phase2_intake.io.reports import generate_reports
from phase2_intake.io.schema_detector import schema_status_for_path
from phase2_intake.models import BULK_STOP_MARKER, DownloadCandidate, ManifestEntry, RunSummary, utc_now


def ensure_raw_dirs() -> None:
    for source_dir in RAW_SOURCE_DIRS:
        (RAW_INTAKE_ROOT / source_dir).mkdir(parents=True, exist_ok=True)


def _entry_from_candidate(candidate: DownloadCandidate, *, action: str) -> ManifestEntry:
    return ManifestEntry(
        timestamp=utc_now(),
        source_name=candidate.source_name,
        target=candidate.target,
        url=candidate.url,
        official_url=candidate.official_url,
        action=action,
        license_status=candidate.license_status,
        schema_status=candidate.schema_status,
        trust_level=candidate.trust_level,
        file_type=candidate.expected_file_type,
        intended_role=candidate.intended_role,
        contains_structures=candidate.contains_structures,
        contains_labels=candidate.contains_labels,
        contains_splits=candidate.contains_splits,
        contains_metadata=candidate.contains_metadata,
        contains_code=candidate.contains_code,
        pcna_screening_status=candidate.pcna_screening_status,
        homolog_screening_status=candidate.homolog_screening_status,
        notes=candidate.notes,
    )


def candidate_target_path(candidate: DownloadCandidate) -> Path:
    relative = candidate.relative_path
    if not relative:
        relative = infer_filename(candidate.url, f"{candidate.target}.dat")
    return guarded_target(RAW_INTAKE_ROOT, candidate.source_name, relative)


def process_candidate(
    candidate: DownloadCandidate,
    *,
    dry_run: bool,
    max_file_bytes: int,
    max_dataset_bytes: int,
    source_total_bytes: int,
    manifest: ManifestWriter,
    summary: RunSummary,
) -> int:
    if candidate.link_only or not candidate.download:
        entry = _entry_from_candidate(candidate, action="linked_only")
        entry.reason_skipped = "linked_only_by_policy"
        manifest.append(entry)
        summary.manifest_entries.append(entry)
        summary.linked_only_count += 1
        return source_total_bytes

    target_path = candidate_target_path(candidate)
    probe = probe_url(candidate.url)

    if candidate.trust_level == "unverified_third_party":
        entry = _entry_from_candidate(candidate, action="linked_only")
        entry.http_status = probe.http_status
        entry.file_size_bytes = probe.file_size_bytes
        entry.reason_skipped = "third_party_mirror_linked_only_without_human_approval"
        manifest.append(entry)
        summary.manifest_entries.append(entry)
        summary.linked_only_count += 1
        return source_total_bytes

    if candidate.license_status in {"LICENSE_UNRESOLVED", "RESTRICTED", "TERMS_UNKNOWN"} and candidate.trust_level != "official_metadata":
        entry = _entry_from_candidate(candidate, action="skipped")
        entry.http_status = probe.http_status
        entry.file_size_bytes = probe.file_size_bytes
        entry.reason_skipped = "license_or_terms_block_download"
        manifest.append(entry)
        summary.manifest_entries.append(entry)
        summary.skipped_count += 1
        return source_total_bytes

    if probe.file_size_bytes is not None and probe.file_size_bytes > max_file_bytes:
        if not has_bulk_approval(BULK_APPROVALS, source_name=candidate.source_name, url=candidate.url):
            entry = _entry_from_candidate(candidate, action="skipped")
            entry.http_status = probe.http_status
            entry.file_size_bytes = probe.file_size_bytes
            entry.reason_skipped = BULK_STOP_MARKER
            manifest.append(entry)
            summary.manifest_entries.append(entry)
            summary.skipped_count += 1
            if BULK_STOP_MARKER not in summary.stop_markers:
                summary.stop_markers.append(BULK_STOP_MARKER)
            return source_total_bytes

    projected = source_total_bytes + (probe.file_size_bytes or 0)
    if probe.file_size_bytes is not None and projected > max_dataset_bytes:
        entry = _entry_from_candidate(candidate, action="skipped")
        entry.http_status = probe.http_status
        entry.file_size_bytes = probe.file_size_bytes
        entry.reason_skipped = "HUMAN_APPROVAL_REQUIRED_FOR_DATASET_TOTAL_OVER_20GB"
        manifest.append(entry)
        summary.manifest_entries.append(entry)
        summary.skipped_count += 1
        return source_total_bytes

    if dry_run:
        entry = _entry_from_candidate(candidate, action="skipped")
        entry.http_status = probe.http_status
        entry.file_size_bytes = probe.file_size_bytes
        entry.local_path = str(target_path.relative_to(ROOT))
        entry.reason_skipped = "dry_run_would_download"
        manifest.append(entry)
        summary.manifest_entries.append(entry)
        summary.skipped_count += 1
        return source_total_bytes

    if target_path.is_file():
        schema_status, schema_note = schema_status_for_path(target_path)
        entry = _entry_from_candidate(candidate, action="downloaded")
        entry.http_status = probe.http_status
        entry.file_size_bytes = target_path.stat().st_size
        entry.sha256 = sha256_file(target_path)
        entry.local_path = str(target_path.relative_to(ROOT))
        entry.schema_status = schema_status
        entry.notes = "; ".join(filter(None, [candidate.notes, "existing local quarantined file reused", schema_note]))
        manifest.append(entry)
        summary.manifest_entries.append(entry)
        summary.downloaded_count += 1
        summary.total_downloaded_bytes += target_path.stat().st_size
        return source_total_bytes + target_path.stat().st_size

    result = download_url(candidate.url, target_path)
    if result.error:
        entry = _entry_from_candidate(candidate, action="failed")
        entry.http_status = result.http_status or probe.http_status
        entry.file_size_bytes = result.file_size_bytes or probe.file_size_bytes
        entry.error = result.error
        manifest.append(entry)
        summary.manifest_entries.append(entry)
        summary.failed_count += 1
        return source_total_bytes

    schema_status, schema_note = schema_status_for_path(target_path)
    entry = _entry_from_candidate(candidate, action="downloaded")
    entry.http_status = result.http_status or probe.http_status
    entry.file_size_bytes = result.file_size_bytes
    entry.sha256 = result.sha256
    entry.local_path = str(target_path.relative_to(ROOT))
    entry.schema_status = schema_status
    entry.notes = "; ".join(filter(None, [candidate.notes, schema_note]))
    manifest.append(entry)
    summary.manifest_entries.append(entry)
    summary.downloaded_count += 1
    summary.total_downloaded_bytes += result.file_size_bytes or 0
    return source_total_bytes + (result.file_size_bytes or 0)


def run_intake(
    *,
    command: str,
    sources: list[str],
    targets: list[str],
    dry_run: bool,
    max_file_bytes: int = DEFAULT_MAX_FILE_BYTES,
    max_dataset_bytes: int = DEFAULT_MAX_DATASET_BYTES,
) -> RunSummary:
    ensure_raw_dirs()
    selected = ALL_SAFE_SOURCES if sources == ["all_safe"] else sources
    manifest = ManifestWriter(DOWNLOAD_MANIFEST)
    summary = RunSummary(command=command, dry_run=dry_run, source_names=selected)

    for source_name in selected:
        adapter = get_adapter(source_name)
        context = AdapterContext(targets=targets if len(selected) == 1 else [])
        source_total = 0
        for candidate in adapter.candidates(context):
            source_total = process_candidate(
                candidate,
                dry_run=dry_run,
                max_file_bytes=max_file_bytes,
                max_dataset_bytes=max_dataset_bytes,
                source_total_bytes=source_total,
                manifest=manifest,
                summary=summary,
            )

    rows = read_manifest(DOWNLOAD_MANIFEST)
    inventory = build_inventory(rows)
    write_inventory_json(DATASET_INVENTORY_JSON, inventory)
    write_inventory_csv(DATASET_INVENTORY_CSV, inventory)
    generate_reports(summary, inventory)
    return summary


def regenerate_reports(command: str) -> RunSummary:
    rows = read_manifest(DOWNLOAD_MANIFEST)
    summary = RunSummary(command=command, dry_run=True, source_names=[])
    summary.downloaded_count = sum(1 for row in rows if row.get("action") == "downloaded")
    summary.skipped_count = sum(1 for row in rows if row.get("action") == "skipped")
    summary.linked_only_count = sum(1 for row in rows if row.get("action") == "linked_only")
    summary.failed_count = sum(1 for row in rows if row.get("action") == "failed")
    summary.total_downloaded_bytes = sum(row.get("file_size_bytes") or 0 for row in rows if row.get("action") == "downloaded")
    inventory = build_inventory(rows)
    write_inventory_json(DATASET_INVENTORY_JSON, inventory)
    write_inventory_csv(DATASET_INVENTORY_CSV, inventory)
    generate_reports(summary, inventory)
    return summary


def print_summary(summary: RunSummary) -> None:
    print(f"Final status: {summary.final_status}")
    print(f"Dry run: {summary.dry_run}")
    print(f"Sources: {', '.join(summary.source_names) if summary.source_names else 'manifest-only reports'}")
    print(f"Downloaded: {summary.downloaded_count}")
    print(f"Skipped: {summary.skipped_count}")
    print(f"Linked only: {summary.linked_only_count}")
    print(f"Failed: {summary.failed_count}")
    print(f"Downloaded bytes: {summary.total_downloaded_bytes}")
    if summary.stop_markers:
        print("Stop markers: " + ", ".join(summary.stop_markers))
    print("All acquired files remain quarantined/raw_unverified and not adopted.")
