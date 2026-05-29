"""Shared dataclasses and governed status values for dataset intake."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


DOWNLOAD_ACTIONS = {"downloaded", "skipped", "linked_only", "failed"}
LICENSE_STATUSES = {"LICENSE_KNOWN", "LICENSE_UNRESOLVED", "RESTRICTED", "TERMS_UNKNOWN"}
SCHEMA_STATUSES = {"SCHEMA_KNOWN", "SCHEMA_PARTIAL", "SCHEMA_UNKNOWN", "SCHEMA_UNREADABLE"}
TRUST_LEVELS = {"official", "official_metadata", "unverified_third_party", "crawl_lead", "unknown"}
ACQUISITION_STATUSES = {
    "NO_DATASETS_ACQUIRED",
    "RAW_ASSETS_ACQUIRED_NOT_VERIFIED",
    "CRYPTOBENCH_READY_FOR_SCHEMA_AUDIT",
    "AUXILIARY_DATA_READY_FOR_SCHEMA_AUDIT",
    "NOT_READY_FOR_SPLIT_FREEZE",
}
FORBIDDEN_READINESS_LABELS = {
    "READY_FOR_TRAINING",
    "READY_FOR_SPLIT_FREEZE",
    "READY_FOR_LABEL_FREEZE",
}
BULK_STOP_MARKER = "HUMAN_APPROVAL_REQUIRED_FOR_BULK_DOWNLOAD"


def utc_now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


@dataclass(frozen=True)
class DownloadCandidate:
    source_name: str
    target: str
    url: str
    official_url: str
    relative_path: str | None = None
    intended_role: str = "source acquisition"
    license_status: str = "LICENSE_UNRESOLVED"
    schema_status: str = "SCHEMA_UNKNOWN"
    trust_level: str = "official"
    link_only: bool = False
    download: bool = True
    expected_file_type: str = "unknown"
    contains_structures: bool = False
    contains_labels: bool = False
    contains_splits: bool = False
    contains_metadata: bool = True
    contains_code: bool = False
    pcna_screening_status: str = "not_started"
    homolog_screening_status: str = "not_started"
    notes: str = ""


@dataclass
class ManifestEntry:
    timestamp: str
    source_name: str
    target: str
    url: str
    official_url: str | None = None
    local_path: str | None = None
    action: str = "skipped"
    http_status: int | None = None
    error: str | None = None
    reason_skipped: str | None = None
    file_size_bytes: int | None = None
    sha256: str | None = None
    license_status: str = "LICENSE_UNRESOLVED"
    schema_status: str = "SCHEMA_UNKNOWN"
    trust_level: str = "unknown"
    quarantine_status: str = "raw_unverified"
    file_type: str = "unknown"
    intended_role: str = "source acquisition"
    contains_structures: bool = False
    contains_labels: bool = False
    contains_splits: bool = False
    contains_metadata: bool = False
    contains_code: bool = False
    pcna_screening_status: str = "not_started"
    homolog_screening_status: str = "not_started"
    notes: str = ""

    def to_json_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RunSummary:
    command: str
    dry_run: bool
    source_names: list[str]
    downloaded_count: int = 0
    skipped_count: int = 0
    linked_only_count: int = 0
    failed_count: int = 0
    total_downloaded_bytes: int = 0
    stop_markers: list[str] = field(default_factory=list)
    manifest_entries: list[ManifestEntry] = field(default_factory=list)

    @property
    def final_status(self) -> str:
        if self.downloaded_count > 0:
            return "RAW_ASSETS_ACQUIRED_NOT_VERIFIED"
        return "NO_DATASETS_ACQUIRED"

