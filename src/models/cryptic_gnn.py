"""
CrypticGNN: per-residue cryptic pocket scorer.
GATv2Conv × 4 with edge features + scoring MLP head.
"""
from __future__ import annotations
import torch
import torch.nn as nn
from torch_geometric.nn import GATv2Conv


class NodeEmbedding(nn.Module):
    """Project raw 26-dim node features → 128-dim latent."""

    def __init__(self, in_dim: int = 26, out_dim: int = 128):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(in_dim, out_dim),
            nn.ReLU(),
            nn.LayerNorm(out_dim),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


class CrypticGNN(nn.Module):
    """
    Args:
        node_in_dim:   raw node feature dim (default 26)
        edge_dim:      edge feature dim (default 2)
        hidden_dim:    GATv2 hidden channels (default 256)
        num_layers:    number of GATv2 layers (default 4)
        num_heads:     attention heads (default 4)
        dropout:       attention dropout (default 0.2)

    Forward input:
        x           : (N, node_in_dim)
        edge_index  : (2, E)
        edge_attr   : (E, edge_dim)

    Forward output:
        scores      : (N,)  pocket probability per residue
    """

    def __init__(
        self,
        node_in_dim: int = 26,
        edge_dim: int = 2,
        hidden_dim: int = 256,
        num_layers: int = 4,
        num_heads: int = 4,
        dropout: float = 0.2,
    ):
        super().__init__()
        self.embedding = NodeEmbedding(node_in_dim, hidden_dim)

        self.convs = nn.ModuleList([
            GATv2Conv(
                in_channels=hidden_dim,
                out_channels=hidden_dim // num_heads,
                heads=num_heads,
                edge_dim=edge_dim,
                dropout=dropout,
                concat=True,
            )
            for _ in range(num_layers)
        ])
        self.norms = nn.ModuleList([nn.LayerNorm(hidden_dim) for _ in range(num_layers)])

        self.head = nn.Sequential(
            nn.Linear(hidden_dim, 64),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(64, 1),
        )

    def forward(
        self,
        x: torch.Tensor,
        edge_index: torch.Tensor,
        edge_attr: torch.Tensor,
    ) -> torch.Tensor:
        h = self.embedding(x)
        for conv, norm in zip(self.convs, self.norms):
            h = norm(h + conv(h, edge_index, edge_attr))   # residual
        return torch.sigmoid(self.head(h).squeeze(-1))
