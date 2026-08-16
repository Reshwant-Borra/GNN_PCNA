"""Approved MVP node feature encoding for Phase 3 graphs.

Feature vector layout (25-dimensional float32):
  [0-19]  one-hot residue identity — standard 20 amino acids, alphabetical
  [20]    one-hot — modified residue (non-standard AA with polymer position)
  [21]    one-hot — unknown residue (not standard and not flagged as modified)
  [22]    binary flag — is_modified (1.0 if non-standard polymer residue)
  [23]    binary flag — missing_ca (1.0 if no CA atom present in structure)
  [24]    binary flag — has_altloc (1.0 if any alternate location records exist)

Approved by: reports/phase3/graph_policy_human_decision_20260528.md
Governance:  docs/scientific_governance/07_PREPROCESSING_AND_GRAPH_RULES.md

NOT approved for first graph release:
  - ESM / protein-language-model embeddings
  - normalization statistics
  - raw chain ID, residue number, fold, cluster, split assignment as trainable inputs
"""

from __future__ import annotations

import numpy as np

# Standard 20 amino acids in alphabetical order — index 0-19
STANDARD_AA: list[str] = [
    "ALA", "ARG", "ASN", "ASP", "CYS",
    "GLN", "GLU", "GLY", "HIS", "ILE",
    "LEU", "LYS", "MET", "PHE", "PRO",
    "SER", "THR", "TRP", "TYR", "VAL",
]

_STANDARD_AA_SET: frozenset[str] = frozenset(STANDARD_AA)
_AA_TO_INDEX: dict[str, int] = {aa: i for i, aa in enumerate(STANDARD_AA)}

MODIFIED_IDX: int = 20
UNKNOWN_IDX: int = 21
VOCAB_SIZE: int = 22   # 20 standard + modified + unknown
FEATURE_DIM: int = 25  # 22 one-hot + 3 binary flags


def is_modified_residue(residue_name: str) -> bool:
    """True when residue is not a standard amino acid (e.g. MSE, SEP, HYP)."""
    return residue_name.upper().strip() not in _STANDARD_AA_SET


def residue_one_hot_index(residue_name: str, is_modified: bool) -> int:
    upper = residue_name.upper().strip()
    if upper in _AA_TO_INDEX:
        return _AA_TO_INDEX[upper]
    if is_modified:
        return MODIFIED_IDX
    return UNKNOWN_IDX


def residue_features(
    residue_name: str,
    is_modified: bool,
    has_ca: bool,
    has_altloc: bool,
) -> np.ndarray:
    """Return a 25-dim float32 feature vector for one residue node."""
    feat = np.zeros(FEATURE_DIM, dtype=np.float32)
    feat[residue_one_hot_index(residue_name, is_modified)] = 1.0
    feat[VOCAB_SIZE]     = float(is_modified)
    feat[VOCAB_SIZE + 1] = float(not has_ca)
    feat[VOCAB_SIZE + 2] = float(has_altloc)
    return feat
