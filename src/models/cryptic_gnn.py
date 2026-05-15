"""
PocketGNN v2 — dual-branch GNN for cryptic pocket prediction.

Replaces the original single-branch CrypticGNN with:
  - Richer node features (40 dims vs 26)
  - Two graph views: spatial contacts + backbone bonds
  - Gated branch fusion
  - Symmetry-aware head for PCNA homotrimer
  - Deeper scoring MLP

Backward-compatible: CrypticGNN (v1) is preserved for reference.
"""
from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import GATv2Conv


# ── CrypticGNN v1 (preserved for reference) ─────────────────────────────────

class NodeEmbedding(nn.Module):
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
    """Original v1 architecture — 4-layer GATv2Conv, single contact graph."""

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
            GATv2Conv(hidden_dim, hidden_dim // num_heads,
                      heads=num_heads, edge_dim=edge_dim,
                      dropout=dropout, concat=True)
            for _ in range(num_layers)
        ])
        self.norms = nn.ModuleList([nn.LayerNorm(hidden_dim) for _ in range(num_layers)])
        self.head = nn.Sequential(
            nn.Linear(hidden_dim, 64), nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(64, 1),
        )

    def forward(self, x, edge_index, edge_attr):
        h = self.embedding(x)
        for conv, norm in zip(self.convs, self.norms):
            h = norm(h + conv(h, edge_index, edge_attr))
        return torch.sigmoid(self.head(h).squeeze(-1))


# ── PocketGNN v2 ─────────────────────────────────────────────────────────────

class PocketGNN(nn.Module):
    """
    Dual-branch GNN with gated fusion and symmetry-aware scoring.

    Node features: 40 dims (see graph_construction.py v2)
    Edge features: 6 dims (both branches use the same schema)

    Forward args
    ─────────────
    x                : (N, node_in_dim)
    edge_index       : (2, E_contact)   spatial contact graph
    edge_attr        : (E_contact, edge_dim)
    edge_index_seq   : (2, E_seq)       backbone sequential graph
    edge_attr_seq    : (E_seq, edge_dim)
    chain_id         : (N,) long        0/1/2 for chains A/B/C (optional)

    Returns: (N,) per-residue pocket probability in [0, 1]
    """

    NODE_IN_DIM  = 40
    EDGE_DIM     = 6
    HIDDEN_DIM   = 256
    NUM_HEADS    = 4

    def __init__(
        self,
        node_in_dim: int   = NODE_IN_DIM,
        edge_dim: int      = EDGE_DIM,
        hidden_dim: int    = HIDDEN_DIM,
        n_spatial: int     = 3,
        n_seq: int         = 2,
        num_heads: int     = NUM_HEADS,
        dropout: float     = 0.2,
        sym_weight: float  = 0.1,   # soft symmetry prior strength
    ):
        super().__init__()
        self.sym_weight = sym_weight
        head_dim = hidden_dim // num_heads

        # Node projection
        self.node_proj = nn.Sequential(
            nn.Linear(node_in_dim, hidden_dim),
            nn.ReLU(),
            nn.LayerNorm(hidden_dim),
        )

        # Branch 1: spatial contact graph
        self.spatial_convs = nn.ModuleList([
            GATv2Conv(hidden_dim, head_dim, heads=num_heads,
                      edge_dim=edge_dim, dropout=dropout, concat=True)
            for _ in range(n_spatial)
        ])
        self.spatial_norms = nn.ModuleList([
            nn.LayerNorm(hidden_dim) for _ in range(n_spatial)
        ])

        # Branch 2: backbone sequential graph
        self.seq_convs = nn.ModuleList([
            GATv2Conv(hidden_dim, head_dim, heads=num_heads,
                      edge_dim=edge_dim, dropout=dropout, concat=True)
            for _ in range(n_seq)
        ])
        self.seq_norms = nn.ModuleList([
            nn.LayerNorm(hidden_dim) for _ in range(n_seq)
        ])

        # Gated fusion: [h_spatial || h_seq] → gate vector
        self.gate_proj = nn.Linear(hidden_dim * 2, hidden_dim)

        # Scoring head (deeper than v1)
        self.head = nn.Sequential(
            nn.Linear(hidden_dim, 128),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(64, 1),
        )

    def forward(
        self,
        x: torch.Tensor,
        edge_index: torch.Tensor,
        edge_attr: torch.Tensor,
        edge_index_seq: torch.Tensor,
        edge_attr_seq: torch.Tensor,
        chain_id: torch.Tensor | None = None,
    ) -> torch.Tensor:
        h = self.node_proj(x)

        # ── Branch 1: spatial ────────────────────────────────────────────────
        h_s = h
        for conv, norm in zip(self.spatial_convs, self.spatial_norms):
            h_s = norm(h_s + conv(h_s, edge_index, edge_attr))

        # ── Branch 2: sequential ─────────────────────────────────────────────
        h_b = h
        for conv, norm in zip(self.seq_convs, self.seq_norms):
            h_b = norm(h_b + conv(h_b, edge_index_seq, edge_attr_seq))

        # ── Gated fusion ─────────────────────────────────────────────────────
        gate   = torch.sigmoid(self.gate_proj(torch.cat([h_s, h_b], dim=-1)))
        h_fused = gate * h_s + (1.0 - gate) * h_b

        # ── Symmetry prior (PCNA homotrimer) ─────────────────────────────────
        # When chain_id is given, soft-regularize so equivalent residue positions
        # across chains A/B/C receive similar representations.
        if chain_id is not None and self.sym_weight > 0:
            from torch_geometric.utils import scatter
            # Mean-pool features per residue index within each chain
            # Use a simple cross-chain mean: average over all chains equally
            h_mean = h_fused.mean(dim=0, keepdim=True).expand_as(h_fused)
            h_fused = h_fused + self.sym_weight * (h_mean - h_fused).detach()

        return torch.sigmoid(self.head(h_fused).squeeze(-1))

    @staticmethod
    def from_v1_config() -> "PocketGNN":
        """Construct with defaults matching v1 hidden dim for easy comparison."""
        return PocketGNN()


# ── Loss functions ────────────────────────────────────────────────────────────

def focal_loss(
    scores: torch.Tensor,
    targets: torch.Tensor,
    gamma: float = 2.0,
    alpha: float = 0.25,
) -> torch.Tensor:
    bce   = F.binary_cross_entropy(scores, targets, reduction="none")
    p_t   = scores * targets + (1 - scores) * (1 - targets)
    alpha_t = alpha * targets + (1 - alpha) * (1 - targets)
    return (alpha_t * (1 - p_t) ** gamma * bce).mean()


def ranking_loss(
    scores: torch.Tensor,
    targets: torch.Tensor,
    margin: float = 0.2,
    max_pairs: int = 1024,
) -> torch.Tensor:
    """Hinge ranking loss: pocket residues should score > non-pocket by margin."""
    pos_mask = targets > 0.5
    neg_mask = ~pos_mask
    if not pos_mask.any() or not neg_mask.any():
        return scores.new_zeros(1).squeeze()

    pos_scores = scores[pos_mask]
    neg_scores = scores[neg_mask]

    # Sample a bounded number of pairs to keep memory manageable
    n_pos = min(len(pos_scores), 32)
    n_neg = min(len(neg_scores), max_pairs // n_pos)
    pos_s = pos_scores[:n_pos].unsqueeze(1)    # (n_pos, 1)
    neg_s = neg_scores[:n_neg].unsqueeze(0)    # (1, n_neg)

    return F.relu(margin - (pos_s - neg_s)).mean()


def symmetry_loss(
    scores: torch.Tensor,
    chain_id: torch.Tensor,
    resid: torch.Tensor,
) -> torch.Tensor:
    """
    Penalize variance in scores for structurally equivalent residues across
    the 3 PCNA chains. Applied only during PCNA fine-tuning.
    """
    loss = scores.new_zeros(1).squeeze()
    for rid in resid.unique():
        mask = resid == rid
        if mask.sum() < 2:
            continue
        chain_scores = scores[mask]
        loss = loss + chain_scores.var()
    n_unique = resid.unique().numel()
    return loss / max(n_unique, 1)


def pocket_loss(
    scores: torch.Tensor,
    targets: torch.Tensor,
    chain_id: torch.Tensor | None = None,
    resid: torch.Tensor | None = None,
    use_symmetry: bool = False,
    w_rank: float = 0.05,
    w_sym: float = 0.1,
) -> torch.Tensor:
    fl   = focal_loss(scores, targets)
    rl   = ranking_loss(scores, targets)
    loss = fl + w_rank * rl

    if use_symmetry and chain_id is not None and resid is not None:
        sl   = symmetry_loss(scores, chain_id, resid)
        loss = loss + w_sym * sl

    return loss
