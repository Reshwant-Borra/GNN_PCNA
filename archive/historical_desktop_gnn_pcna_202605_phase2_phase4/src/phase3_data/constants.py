"""Governed constants for the Phase 3 CryptoBench data pipeline."""

from __future__ import annotations

from pathlib import Path


FROZEN_SPLIT_MANIFEST = Path("data/registries/split_manifest_frozen.json")
LABEL_MANIFEST = Path("data/labels/label_manifest.json")
EXCLUDED_RECORDS = Path("data/registries/excluded_records.json")
SEQUENCE_CLUSTERS = Path("data/registries/sequence_cluster_assignments.json")
CRYPTOBENCH_CIF_ZIP = Path(
    "data/raw_intake/cryptobench/files/672a0171eae0bff252ba9ea3_cif-files.zip"
)
CRYPTOBENCH_CIF_DIR = Path("data/raw_intake/cryptobench/cif-files")

EXPECTED_SPLIT_HASH_PREFIX = "24dd5e347d880108"
EXPECTED_SPLIT_HASH_SHA256 = (
    "24dd5e347d880108e780ebd5b902fa0e51e907a5213f589206aa8c03b1e032c3"
)
EXPECTED_LABEL_STRUCTURES = 1101
EXPECTED_EXCLUDED_STRUCTURES = 6
EXPECTED_TOTAL_POSITIVES = 16335
EXPECTED_TOTAL_MASKED = 3704
EXPECTED_PCNA_CLUSTER_ID_30 = 1168
EXPECTED_CIF_ZIP_SHA256 = (
    "8d15f897bfdfdf61c7d97a29f5f6ca2c5e03d73d8fb89be7da5bbc245cf56ae4"
)
EXPECTED_CIF_FILE_COUNT = 5005

TRAIN_FOLDS = frozenset({"train-0", "train-1", "train-2", "train-3"})
VALID_INDEX_SPLITS = frozenset({"all", "train", "validation", "test"})
LABEL_VALUES = frozenset({-1, 0, 1})

GOVERNANCE_PATHS = (
    "docs/scientific_governance/04_DATASET_CONSTRAINTS.md",
    "docs/scientific_governance/05_SPLIT_PROTOCOL.md",
    "docs/scientific_governance/06_LABELING_RULES.md",
    "docs/scientific_governance/07_PREPROCESSING_AND_GRAPH_RULES.md",
    "docs/scientific_governance/15_PROVENANCE_AND_REPRODUCIBILITY.md",
    "docs/scientific_governance/16_CODING_AGENT_RULES.md",
    "docs/scientific_governance/19_STOP_CONDITIONS.md",
    "docs/scientific_governance/26_HUMAN_REVIEW_GATES.md",
)

