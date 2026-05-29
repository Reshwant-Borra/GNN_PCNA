"""Configuration constants for governed raw dataset intake."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RAW_INTAKE_ROOT = ROOT / "data" / "raw_intake"
REGISTRY_DIR = ROOT / "data" / "registries"
REPORT_DIR = ROOT / "reports" / "phase2"

DOWNLOAD_MANIFEST = REGISTRY_DIR / "download_manifest.jsonl"
DATASET_INVENTORY_JSON = REGISTRY_DIR / "dataset_inventory.json"
DATASET_INVENTORY_CSV = REGISTRY_DIR / "dataset_inventory.csv"
BULK_APPROVALS = REGISTRY_DIR / "bulk_download_approvals.json"

DEFAULT_MAX_FILE_BYTES = 500 * 1024 * 1024
DEFAULT_MAX_DATASET_BYTES = 20 * 1024 * 1024 * 1024
USER_AGENT = "GNN-PCNA-Phase2-Dataset-Intake/0.1"

REPORT_PATHS = {
    "acquisition_log": REPORT_DIR / "dataset_acquisition_log.md",
    "file_inventory": REPORT_DIR / "dataset_file_inventory.md",
    "license_review": REPORT_DIR / "license_and_terms_review.md",
    "schema_first_pass": REPORT_DIR / "dataset_schema_first_pass.md",
    "adoption_recommendation": REPORT_DIR / "dataset_adoption_recommendation.md",
    "friend_report": REPORT_DIR / "friend_dataset_acquisition_report.md",
}

RAW_SOURCE_DIRS = [
    "cryptobench",
    "rcsb_pdb",
    "pcna_structures",
    "biolip",
    "scpdb",
    "pdbbind",
    "asd",
    "pocketminer",
    "alphafold",
    "biogrid",
    "string",
    "baseline_tools",
    "literature_metadata",
]

