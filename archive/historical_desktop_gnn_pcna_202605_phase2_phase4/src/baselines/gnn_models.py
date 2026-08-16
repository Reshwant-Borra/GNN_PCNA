"""GCN-1L and GAT-2L baseline model architectures.

Both models accept the same PyG Data objects as GraphSAGE-3L
(node features x shape (N, 25), edge_index) and output raw logits (N,).
No sigmoid during training — BCEWithLogitsLoss is used.

Governance: docs/scientific_governance/08_MODEL_ARCHITECTURE_CONSTRAINTS.md
Gate: reports/phase3/baseline_gate3_authorization_20260529.md
"""

from __future__ import annotations

import torch
import torch.nn as nn
from torch_geometric.nn import GATConv, GCNConv

_FEATURE_DIM: int = 25  # must match phase3_model/gnn.py


class GCN1L(nn.Module):
    """Single-layer GCN baseline.

    Architecture: GCNConv(25 -> H) + ReLU + Linear(H -> 1)
    Much simpler than GraphSAGE-3L (one layer, symmetric normalization).
    """

    def __init__(self, hidden_dim: int = 128) -> None:
        super().__init__()
        self.conv = GCNConv(_FEATURE_DIM, hidden_dim, add_self_loops=True)
        self.head = nn.Linear(hidden_dim, 1)

    def forward(self, data: object) -> torch.Tensor:
        x, edge_index = data.x, data.edge_index
        h = torch.relu(self.conv(x, edge_index))
        return self.head(h).squeeze(-1)


class GAT2L(nn.Module):
    """Two-layer GAT baseline with multi-head attention.

    Architecture:
      GATConv(25 -> head_dim, heads=4, concat=True) + ReLU   → (N, 128)
      GATConv(128 -> 128, heads=1, concat=False)  + ReLU     → (N, 128)
      Linear(128 -> 1)                                         → (N,)

    head_dim = hidden_dim // 4  so the concat output stays at hidden_dim.
    """

    def __init__(self, hidden_dim: int = 128, heads: int = 4, dropout: float = 0.1) -> None:
        super().__init__()
        if hidden_dim % heads != 0:
            raise ValueError(
                f"hidden_dim ({hidden_dim}) must be divisible by heads ({heads})."
            )
        head_dim = hidden_dim // heads
        self.conv1 = GATConv(
            _FEATURE_DIM, head_dim, heads=heads, concat=True,
            dropout=dropout, add_self_loops=True,
        )
        self.conv2 = GATConv(
            hidden_dim, hidden_dim, heads=1, concat=False,
            dropout=dropout, add_self_loops=True,
        )
        self.head = nn.Linear(hidden_dim, 1)

    def forward(self, data: object) -> torch.Tensor:
        x, edge_index = data.x, data.edge_index
        h = torch.relu(self.conv1(x, edge_index))
        h = torch.relu(self.conv2(h, edge_index))
        return self.head(h).squeeze(-1)
