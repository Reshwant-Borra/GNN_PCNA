"""
Post-processing: cluster per-residue scores into pocket candidates.
Score, rank, and export results.
"""
from __future__ import annotations
import json
import numpy as np
from sklearn.cluster import DBSCAN


def cluster_pocket_residues(
    scores: np.ndarray,      # (N,) per-residue scores
    coords: np.ndarray,      # (N, 3) Cα coordinates
    threshold: float = 0.5,
    eps: float = 6.0,
    min_samples: int = 3,
) -> list[dict]:
    """
    Threshold scores, spatially cluster high-scoring residues.

    Returns:
        List of pocket dicts: {residue_indices, mean_score, size, centroid}
    """
    raise NotImplementedError


def rank_pockets(pockets: list[dict]) -> list[dict]:
    """Sort pockets by mean_score × size (descending)."""
    return sorted(pockets, key=lambda p: p['mean_score'] * p['size'], reverse=True)


def write_scored_pdb(
    pdb_path: str,
    output_path: str,
    scores: np.ndarray,    # (N,) will replace B-factors
) -> None:
    """Write PDB with per-residue pocket scores in B-factor column."""
    raise NotImplementedError


def export_pockets_json(pockets: list[dict], output_path: str) -> None:
    with open(output_path, 'w') as f:
        json.dump(pockets, f, indent=2, default=lambda x: x.tolist() if hasattr(x, 'tolist') else x)


def compute_auroc(scores: np.ndarray, labels: np.ndarray) -> float:
    """AUROC for evaluating recovery of 8GLA pocket residues."""
    from sklearn.metrics import roc_auc_score
    return roc_auc_score(labels, scores)
