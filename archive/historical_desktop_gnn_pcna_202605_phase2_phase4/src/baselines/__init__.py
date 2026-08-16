"""Phase 3 baseline implementations.

Gate: reports/phase3/baseline_gate3_authorization_20260529.md
Governance: docs/scientific_governance/10_BASELINE_REQUIREMENTS.md
"""

from __future__ import annotations

from baselines.interfaces import BaselineRunSpec
from baselines.random_baseline import run_random_baseline
from baselines.structural_baseline import run_degree_baseline
from baselines.gnn_models import GCN1L, GAT2L
from baselines.gnn_trainer import train_baseline_gnn, filter_edges, BaselineGateError

__all__ = [
    "BaselineRunSpec",
    "run_random_baseline",
    "run_degree_baseline",
    "GCN1L",
    "GAT2L",
    "train_baseline_gnn",
    "filter_edges",
    "BaselineGateError",
]

