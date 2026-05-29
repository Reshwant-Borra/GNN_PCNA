"""Graph-degree structural baseline.

Uses negative spatial-edge degree as the pocket score.
Higher spatial degree = more buried; lower degree = more surface-exposed.
Negative degree → higher score = more surface-exposed residue.

This is a proxy for solvent exposure via graph structure — no MD or SASA
calculation is performed. Score direction: lower spatial degree → higher score
→ more likely to be surface-accessible (and thus a pocket candidate in apo form).

Governance: docs/scientific_governance/10_BASELINE_REQUIREMENTS.md
Gate: reports/phase3/baseline_gate3_authorization_20260529.md
"""

from __future__ import annotations

from typing import Any

import torch
from torch_geometric.data import Data

EDGE_TYPE_SPATIAL: int = 0  # from phase3_graphs/constants.py


def _degree_scores(data: Data) -> tuple[list[float], list[int]]:
    """Compute negative spatial degree for loss_mask=True residues."""
    N = int(data.x.shape[0])
    edge_type = data.edge_type          # (E,)
    edge_index = data.edge_index        # (2, E)

    spatial_mask = (edge_type == EDGE_TYPE_SPATIAL)
    spatial_src = edge_index[0][spatial_mask]  # source nodes of spatial edges

    degree = torch.zeros(N, dtype=torch.float32)
    if spatial_src.numel() > 0:
        degree.scatter_add_(0, spatial_src, torch.ones_like(spatial_src, dtype=torch.float32))

    lm = data.loss_mask
    # Negative degree: fewer contacts → higher score → more surface-exposed
    scores = (-degree[lm]).tolist()
    labels = [int(v) for v in data.y[lm].tolist()]
    return scores, labels


def run_degree_baseline(val_data: list[Data]) -> dict[str, Any]:
    """Run negative-spatial-degree baseline on the validation fold.

    No training performed. Score is computed from graph structure only.
    """
    import sys
    from pathlib import Path
    ROOT = Path(__file__).resolve().parents[2]
    if str(ROOT / "src") not in sys.path:
        sys.path.insert(0, str(ROOT / "src"))

    from phase3_evaluation.metrics import bootstrap_ci, compute_metrics_from_lists

    protein_scores = [_degree_scores(d) for d in val_data]
    m = compute_metrics_from_lists(protein_scores)
    ci = bootstrap_ci(protein_scores)

    return {
        "baseline_name": "degree",
        "description": (
            "Negative spatial-edge degree per residue. "
            "Higher score = fewer spatial contacts = more surface-exposed. "
            "Proxy for solvent exposure via graph topology. No training."
        ),
        "score_formula": "score = -degree(spatial_edges)",
        "edge_type_used": EDGE_TYPE_SPATIAL,
        "metrics": m,
        "ci": ci,
        "governance": "docs/scientific_governance/10_BASELINE_REQUIREMENTS.md",
        "gate": "reports/phase3/baseline_gate3_authorization_20260529.md",
        "no_test_set_evaluation": True,
        "no_scientific_claims": True,
    }
