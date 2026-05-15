"""
PocketGNN — dual-branch GNN for cryptic pocket prediction.

v2 (large, ~10.4M params): hidden_dim=768, 4 spatial + 3 seq layers, 8 heads
v1 (CrypticGNN, ~850k):    original single-branch for comparison

Node features: 40 dims  |  Edge features: 6 dims  (see graph_construction.py)
"""
from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import GATv2Conv


# ── CrypticGNN v1 (preserved) ────────────────────────────────────────────────

class CrypticGNN(nn.Module):
    """Original single-branch GATv2Conv baseline (~850k params)."""

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
        self.embedding = nn.Sequential(
            nn.Linear(node_in_dim, hidden_dim), nn.ReLU(), nn.LayerNorm(hidden_dim))
        self.convs = nn.ModuleList([
            GATv2Conv(hidden_dim, hidden_dim // num_heads,
                      heads=num_heads, edge_dim=edge_dim, dropout=dropout, concat=True)
            for _ in range(num_layers)
        ])
        self.norms = nn.ModuleList([nn.LayerNorm(hidden_dim) for _ in range(num_layers)])
        self.head  = nn.Sequential(
            nn.Linear(hidden_dim, 64), nn.ReLU(), nn.Dropout(dropout), nn.Linear(64, 1))

    def forward(self, x, edge_index, edge_attr):
        h = self.embedding(x)
        for conv, norm in zip(self.convs, self.norms):
            h = norm(h + conv(h, edge_index, edge_attr))
        return torch.sigmoid(self.head(h).squeeze(-1))


# ── PocketGNN v2 ──────────────────────────────────────────────────────────────

class PocketGNN(nn.Module):
    """
    Dual-branch GNN: spatial contacts + backbone sequential graph, gated fusion.
    Default config: ~10.4M parameters.

    Configs
    -------
    PocketGNN()           — large  (~10.4M) hidden=768, heads=8, 4+3 layers
    PocketGNN.small()     — small  (~850k)  hidden=256, heads=4, 3+2 layers
    PocketGNN.medium()    — medium (~3.2M)  hidden=512, heads=8, 3+2 layers

    Forward args
    ------------
    x               : (N, node_in_dim)
    edge_index      : (2, E_c)   spatial contact graph
    edge_attr       : (E_c, edge_dim)
    edge_index_seq  : (2, E_s)   backbone sequential graph
    edge_attr_seq   : (E_s, edge_dim)
    chain_id        : (N,) long  0/1/2 for PCNA chains A/B/C  [optional]

    Returns: (N,) per-residue pocket probability in [0,1]
    """

    NODE_DIM = 40
    EDGE_DIM = 6

    def __init__(
        self,
        node_in_dim : int   = 40,
        edge_dim    : int   = 6,
        hidden_dim  : int   = 768,
        n_spatial   : int   = 4,
        n_seq       : int   = 3,
        num_heads   : int   = 8,
        dropout     : float = 0.2,
        sym_weight  : float = 0.1,
    ):
        super().__init__()
        assert hidden_dim % num_heads == 0, "hidden_dim must be divisible by num_heads"
        self.hidden_dim = hidden_dim
        self.sym_weight = sym_weight
        head_dim = hidden_dim // num_heads

        # ── Pre-encoder: 3-layer MLP lifting node features to hidden_dim ──────
        self.node_encoder = nn.Sequential(
            nn.Linear(node_in_dim, hidden_dim // 3),
            nn.ReLU(),
            nn.Linear(hidden_dim // 3, hidden_dim // 3 * 2),
            nn.ReLU(),
            nn.Linear(hidden_dim // 3 * 2, hidden_dim),
            nn.LayerNorm(hidden_dim),
        )

        # ── Branch 1: spatial contact graph ───────────────────────────────────
        self.spatial_convs = nn.ModuleList([
            GATv2Conv(hidden_dim, head_dim, heads=num_heads,
                      edge_dim=edge_dim, dropout=dropout, concat=True)
            for _ in range(n_spatial)
        ])
        self.spatial_norms = nn.ModuleList([
            nn.LayerNorm(hidden_dim) for _ in range(n_spatial)
        ])

        # ── Branch 2: backbone sequential graph ───────────────────────────────
        self.seq_convs = nn.ModuleList([
            GATv2Conv(hidden_dim, head_dim, heads=num_heads,
                      edge_dim=edge_dim, dropout=dropout, concat=True)
            for _ in range(n_seq)
        ])
        self.seq_norms = nn.ModuleList([
            nn.LayerNorm(hidden_dim) for _ in range(n_seq)
        ])

        # ── Gated fusion ───────────────────────────────────────────────────────
        self.gate_proj = nn.Linear(hidden_dim * 2, hidden_dim)

        # ── Scoring head: 4-layer MLP (deeper than v1) ────────────────────────
        self.head = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim // 2, hidden_dim // 4),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim // 4, hidden_dim // 8),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim // 8, 1),
        )

    def forward(
        self,
        x             : torch.Tensor,
        edge_index    : torch.Tensor,
        edge_attr     : torch.Tensor,
        edge_index_seq: torch.Tensor,
        edge_attr_seq : torch.Tensor,
        chain_id      : torch.Tensor | None = None,
    ) -> torch.Tensor:
        h = self.node_encoder(x)

        # Branch 1 — spatial
        h_s = h
        for conv, norm in zip(self.spatial_convs, self.spatial_norms):
            h_s = norm(h_s + conv(h_s, edge_index, edge_attr))

        # Branch 2 — sequential
        h_b = h
        for conv, norm in zip(self.seq_convs, self.seq_norms):
            h_b = norm(h_b + conv(h_b, edge_index_seq, edge_attr_seq))

        # Gated fusion
        gate    = torch.sigmoid(self.gate_proj(torch.cat([h_s, h_b], dim=-1)))
        h_fused = gate * h_s + (1.0 - gate) * h_b

        # Soft symmetry prior for PCNA homotrimer
        if chain_id is not None and self.sym_weight > 0:
            h_mean  = h_fused.mean(dim=0, keepdim=True).expand_as(h_fused)
            h_fused = h_fused + self.sym_weight * (h_mean - h_fused).detach()

        return torch.sigmoid(self.head(h_fused).squeeze(-1))

    @classmethod
    def small(cls) -> "PocketGNN":
        return cls(hidden_dim=256, n_spatial=3, n_seq=2, num_heads=4)

    @classmethod
    def medium(cls) -> "PocketGNN":
        return cls(hidden_dim=512, n_spatial=3, n_seq=2, num_heads=8)

    def param_count(self) -> int:
        return sum(p.numel() for p in self.parameters())


# ── Loss functions ────────────────────────────────────────────────────────────

def focal_loss(
    scores : torch.Tensor,
    targets: torch.Tensor,
    gamma  : float = 2.0,
    alpha  : float = 0.25,
) -> torch.Tensor:
    bce     = F.binary_cross_entropy(scores, targets, reduction="none")
    p_t     = scores * targets + (1 - scores) * (1 - targets)
    alpha_t = alpha * targets + (1 - alpha) * (1 - targets)
    return (alpha_t * (1 - p_t) ** gamma * bce).mean()


def ranking_loss(
    scores   : torch.Tensor,
    targets  : torch.Tensor,
    margin   : float = 0.2,
    max_pairs: int   = 1024,
) -> torch.Tensor:
    pos_mask = targets > 0.5
    neg_mask = ~pos_mask
    if not pos_mask.any() or not neg_mask.any():
        return scores.new_zeros(1).squeeze()
    pos_s = scores[pos_mask][:32].unsqueeze(1)
    neg_s = scores[neg_mask][:max_pairs // 32].unsqueeze(0)
    return F.relu(margin - (pos_s - neg_s)).mean()


def symmetry_loss(
    scores  : torch.Tensor,
    chain_id: torch.Tensor,
    resid   : torch.Tensor,
) -> torch.Tensor:
    loss = scores.new_zeros(1).squeeze()
    for rid in resid.unique():
        mask = resid == rid
        if mask.sum() >= 2:
            loss = loss + scores[mask].var()
    return loss / max(resid.unique().numel(), 1)


def pocket_loss(
    scores      : torch.Tensor,
    targets     : torch.Tensor,
    chain_id    : torch.Tensor | None = None,
    resid       : torch.Tensor | None = None,
    use_symmetry: bool  = False,
    w_rank      : float = 0.05,
    w_sym       : float = 0.10,
) -> torch.Tensor:
    loss = focal_loss(scores, targets) + w_rank * ranking_loss(scores, targets)
    if use_symmetry and chain_id is not None and resid is not None:
        loss = loss + w_sym * symmetry_loss(scores, chain_id, resid)
    return loss
