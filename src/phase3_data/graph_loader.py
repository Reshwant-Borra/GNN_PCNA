"""Governed PyG DataLoader for Phase 3 graph datasets.

Loads .npz graphs from data/graphs/, applies frozen split assignments,
and enforces loss_mask (True = participates in loss; False = excluded).

Governance:
  docs/scientific_governance/04_DATASET_CONSTRAINTS.md
  docs/scientific_governance/05_SPLIT_PROTOCOL.md
  docs/scientific_governance/07_PREPROCESSING_AND_GRAPH_RULES.md
Approval: reports/phase3/model_training_decision_20260528.md
  (decision_id: phase3_model_training_plan_20260528)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

import numpy as np
import torch
from torch_geometric.data import Data
from torch_geometric.loader import DataLoader

from phase3_data.constants import (
    EXPECTED_SPLIT_HASH_SHA256,
)

Split = Literal["train", "val", "test"]

_TRAIN_FOLD_NAMES = {f"train-{i}" for i in range(4)}


def _validate_split_manifest(manifest: dict) -> None:
    """Abort if the manifest hash prefix does not match the frozen hash."""
    actual = manifest.get("manifest_hash_sha256", "")
    expected_prefix = EXPECTED_SPLIT_HASH_SHA256[:16]
    if not actual.startswith(expected_prefix):
        raise ValueError(
            f"Split manifest hash mismatch: got prefix {actual[:16]!r}, "
            f"expected {expected_prefix!r}. "
            "Do not use an unfrozen split manifest."
        )


def _npz_to_data(npz_path: Path, pdb_id: str) -> Data:
    """Load one .npz graph into a PyG Data object."""
    d = np.load(npz_path)
    return Data(
        x=torch.from_numpy(d["node_features"]),
        y=torch.from_numpy(d["node_labels"].astype(np.int32)),
        loss_mask=torch.from_numpy(d["loss_mask"]),
        edge_index=torch.from_numpy(d["edge_index"]),
        edge_type=torch.from_numpy(d["edge_type"].astype(np.int64)),
        edge_attr=torch.from_numpy(d["edge_distance"]),
        pdb_id=pdb_id,
    )


def _get_pdb_ids_for_split(
    manifest: dict,
    split: Split,
    val_fold: int | None,
) -> list[str]:
    """Return PDB IDs assigned to the requested split/fold combination."""
    entries = manifest.get("entries", {})

    if split == "test":
        return [
            pdb_id for pdb_id, entry in entries.items()
            if not entry.get("excluded", True)
            and entry.get("final_fold") == "test"
        ]

    if val_fold is None:
        raise ValueError("val_fold must be provided for split='train' or 'val'.")
    if val_fold not in range(4):
        raise ValueError(f"val_fold must be 0-3, got {val_fold}.")

    val_fold_name = f"train-{val_fold}"

    if split == "val":
        return [
            pdb_id for pdb_id, entry in entries.items()
            if not entry.get("excluded", True)
            and not entry.get("pcna_holdout", False)
            and entry.get("final_fold") == val_fold_name
        ]

    # split == "train": all train folds except val_fold; no PCNA holdout
    active_train_folds = _TRAIN_FOLD_NAMES - {val_fold_name}
    return [
        pdb_id for pdb_id, entry in entries.items()
        if not entry.get("excluded", True)
        and not entry.get("pcna_holdout", False)
        and entry.get("final_fold") in active_train_folds
    ]


def load_split(
    graph_dir: Path,
    split_manifest_path: Path,
    split: Split,
    val_fold: int | None = None,
) -> list[Data]:
    """Load PyG Data objects for one split of one CV fold.

    Args:
        graph_dir: Directory containing {pdb_id}.npz files.
        split_manifest_path: Path to frozen split manifest JSON.
        split: "train" | "val" | "test".
        val_fold: CV fold index 0-3 (required for split="train" or "val").

    Returns:
        List of PyG Data objects sorted by PDB ID for deterministic ordering.

    Raises:
        ValueError: if manifest hash is invalid or val_fold is missing/invalid.
        FileNotFoundError: if any expected .npz file is absent.
    """
    with open(split_manifest_path) as f:
        manifest = json.load(f)

    _validate_split_manifest(manifest)

    pdb_ids = sorted(_get_pdb_ids_for_split(manifest, split, val_fold))

    data_list: list[Data] = []
    missing: list[str] = []
    for pdb_id in pdb_ids:
        npz_path = graph_dir / f"{pdb_id}.npz"
        if not npz_path.is_file():
            missing.append(str(npz_path))
            continue
        data_list.append(_npz_to_data(npz_path, pdb_id))

    if missing:
        n = len(missing)
        preview = missing[:5]
        suffix = "..." if n > 5 else ""
        raise FileNotFoundError(
            f"Missing .npz graph files for {n} PDB IDs: {preview}{suffix}"
        )

    return data_list


def make_dataloader(
    data_list: list[Data],
    batch_size: int = 4,
    shuffle: bool = False,
) -> DataLoader:
    """Wrap a list of PyG Data objects in a DataLoader."""
    return DataLoader(data_list, batch_size=batch_size, shuffle=shuffle)


def compute_pos_weight(train_data: list[Data]) -> torch.Tensor:
    """Compute BCEWithLogitsLoss pos_weight from training-fold nodes only.

    pos_weight = n_background_train / n_positive_train
    Computed exclusively from loss_mask=True nodes in the training fold.
    Never called with validation or test data.

    Governance: docs/scientific_governance/08_MODEL_ARCHITECTURE_CONSTRAINTS.md
      "Focal-loss alpha and class weights must be computed from train only."
    """
    n_pos = 0
    n_bg = 0
    for d in train_data:
        masked_labels = d.y[d.loss_mask]
        n_pos += int((masked_labels == 1).sum())
        n_bg += int((masked_labels == 0).sum())
    if n_pos == 0:
        raise ValueError("No positive labels found in training fold — cannot compute pos_weight.")
    return torch.tensor(n_bg / n_pos, dtype=torch.float32)
