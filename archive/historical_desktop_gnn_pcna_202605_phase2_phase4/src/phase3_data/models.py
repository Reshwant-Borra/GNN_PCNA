"""Data models used by the governed Phase 3 data pipeline."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from phase3_data import constants


@dataclass(frozen=True)
class Phase3Paths:
    """Canonical Phase 3 inputs, resolved relative to a workspace root."""

    root: Path = Path(".")
    split_manifest: Path = constants.FROZEN_SPLIT_MANIFEST
    label_manifest: Path = constants.LABEL_MANIFEST
    excluded_records: Path = constants.EXCLUDED_RECORDS
    sequence_clusters: Path = constants.SEQUENCE_CLUSTERS
    cif_zip: Path = constants.CRYPTOBENCH_CIF_ZIP
    cif_dir: Path = constants.CRYPTOBENCH_CIF_DIR

    def resolve(self, path: Path) -> Path:
        return path if path.is_absolute() else self.root / path

    @property
    def split_manifest_path(self) -> Path:
        return self.resolve(self.split_manifest)

    @property
    def label_manifest_path(self) -> Path:
        return self.resolve(self.label_manifest)

    @property
    def excluded_records_path(self) -> Path:
        return self.resolve(self.excluded_records)

    @property
    def sequence_clusters_path(self) -> Path:
        return self.resolve(self.sequence_clusters)

    @property
    def cif_zip_path(self) -> Path:
        return self.resolve(self.cif_zip)

    @property
    def cif_dir_path(self) -> Path:
        return self.resolve(self.cif_dir)


@dataclass(frozen=True)
class SplitEntry:
    apo_pdb_id: str
    original_fold: str
    final_fold: str
    cluster_id_30: int | None
    uniprot_id: str | None
    pcna_holdout: bool
    excluded: bool
    exclusion_reason: str | None
    label_file: Path | None


@dataclass(frozen=True)
class LabelRecord:
    label_key: str
    chain_id: str
    residue_token: str
    residue_number: str
    insertion_code: str | None
    label: int
    loss_mask: bool
    supervision_role: str


@dataclass(frozen=True)
class ResidueNode:
    chain_id: str
    residue_number: str
    insertion_code: str | None
    residue_name: str
    label_key: str
    label_seq_id: str | None
    entity_id: str | None
    atom_count: int
    atom_names: tuple[str, ...]
    altloc_ids: tuple[str, ...]
    has_ca: bool


@dataclass(frozen=True)
class DatasetIndexEntry:
    apo_pdb_id: str
    fold: str
    requested_split: str
    cluster_id_30: int | None
    uniprot_id: str | None
    label_path: str
    cif_path: str
    label_hash_sha256_prefix: str
    positive_count: int
    masked_count: int
    explicit_label_count: int

    def to_json_dict(self) -> dict[str, Any]:
        return asdict(self)

