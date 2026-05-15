"""
Post-processing: cluster per-residue scores into pocket candidates.
Score, rank, and export results.
"""
from __future__ import annotations
import json
from pathlib import Path
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
    Threshold scores, spatially cluster high-scoring residues with DBSCAN.

    Returns:
        List of pocket dicts sorted by mean_score descending:
        {residue_indices, mean_score, size, centroid}
    """
    high = np.where(scores >= threshold)[0]
    if len(high) < min_samples:
        return []

    clustering = DBSCAN(eps=eps, min_samples=min_samples).fit(coords[high])
    labels = clustering.labels_

    pockets: list[dict] = []
    for label in set(labels):
        if label == -1:
            continue
        mask = labels == label
        indices = high[mask]
        pockets.append({
            'residue_indices': indices.tolist(),
            'mean_score': float(scores[indices].mean()),
            'max_score':  float(scores[indices].max()),
            'size': int(mask.sum()),
            'centroid': coords[indices].mean(axis=0).tolist(),
        })
    return pockets


def rank_pockets(pockets: list[dict]) -> list[dict]:
    """Sort pockets by mean_score × sqrt(size) (descending)."""
    return sorted(pockets,
                  key=lambda p: p['mean_score'] * (p['size'] ** 0.5),
                  reverse=True)


def write_scored_pdb(
    pdb_path: str,
    output_path: str,
    scores: np.ndarray,    # (N,) per-residue scores — replaces B-factor
) -> None:
    """Write PDB with per-residue pocket scores in B-factor column (scaled 0–100)."""
    from src.data_processing.parse_pdb import parse_pdb

    # Build (chain, resid) → score map in residue order from parse_pdb
    residues = parse_pdb(Path(pdb_path))
    if len(residues) != len(scores):
        raise ValueError(
            f"score length {len(scores)} != residue count {len(residues)}")
    score_map: dict[tuple[str, int], float] = {
        (r.chain, r.resid): float(scores[i]) * 100.0
        for i, r in enumerate(residues)
    }

    out_lines: list[str] = []
    for line in Path(pdb_path).read_text(errors='ignore').splitlines(keepends=True):
        if line.startswith('ATOM') and len(line) >= 60:
            try:
                chain = line[21]
                resid = int(line[22:26].strip())
                key   = (chain, resid)
                if key in score_map:
                    bfac  = f"{score_map[key]:6.2f}"
                    line  = line[:60] + bfac + line[66:]
            except (ValueError, IndexError):
                pass
        out_lines.append(line)
    Path(output_path).write_text(''.join(out_lines))


def export_pockets_json(pockets: list[dict], output_path: str) -> None:
    with open(output_path, 'w') as f:
        json.dump(pockets, f, indent=2,
                  default=lambda x: x.tolist() if hasattr(x, 'tolist') else x)


def compute_auroc(scores: np.ndarray, labels: np.ndarray) -> float:
    """AUROC for evaluating recovery of 8GLA pocket residues."""
    from sklearn.metrics import roc_auc_score
    return roc_auc_score(labels, scores)
