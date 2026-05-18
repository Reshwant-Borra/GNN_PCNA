"""
PocketGNN — dual-branch GNN for cryptic pocket prediction.

v2 (large, ~10.4M params): hidden_dim=768, 4 spatial + 3 seq layers, 8 heads
v1 (CrypticGNN, ~850k):    original single-branch for comparison

PocketGNNXL: ESM2 protein language model features (480-dim) + virtual node.
  Node features: 520 dims (40 hand-crafted + 480 ESM2)
  Edge features: 6 dims
  ~12M params default config
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

    def param_count(self) -> int:
        return sum(p.numel() for p in self.parameters())


# ── PocketGNN v2 ──────────────────────────────────────────────────────────────

class PocketGNN(nn.Module):
    """
    Dual-branch GNN: spatial contacts + backbone sequential graph, gated fusion.
    Default config: ~10.4M parameters.

    Configs
    -------
    PocketGNN()           — large  (~10.4M) hidden=768, heads=8, 4+3 layers
    PocketGNN.small()     — small  (~907k)  hidden=256, heads=4, 3+2 layers
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
        sym_weight  : float = 0.0,
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


# ── PocketGNNXL ──────────────────────────────────────────────────────────────

class PocketGNNXL(nn.Module):
    """
    Highest-power pocket predictor.

    Dual-branch GATv2Conv (spatial + sequential) with:
      - ESM2 protein language model embeddings concatenated to hand-crafted features
      - Virtual node: global protein context broadcast back to every residue
      - Deeper node encoder (4-layer MLP)
      - Deeper scoring head (5-layer MLP)

    Default input assumes ESM2 t12 (480-dim) + 40 hand-crafted = 520-dim nodes.
    Node dim is flexible — pass node_in_dim to match whatever ESM2 variant you use.

    Default config: ~12M parameters.

    Configs
    -------
    PocketGNNXL()           — default (520-dim input, hidden=768, 5+4 layers, 8 heads)
    PocketGNNXL.from_esm6() — use ESM2 t6 320-dim → 360-dim input

    Forward args
    ------------
    x               : (N, node_in_dim)
    edge_index      : (2, E_c)   spatial contact graph
    edge_attr       : (E_c, edge_dim)
    edge_index_seq  : (2, E_s)   backbone sequential graph
    edge_attr_seq   : (E_s, edge_dim)
    chain_id        : (N,) long  [optional]

    Returns: (N,) per-residue pocket probability in [0,1]
    """

    ESM2_T12_DIM = 480   # facebook/esm2_t12_35M_UR50D
    ESM2_T6_DIM  = 320   # facebook/esm2_t6_8M_UR50D
    HAND_DIM     = 40    # hand-crafted features from graph_construction.py
    EDGE_DIM     = 6

    def __init__(
        self,
        node_in_dim : int   = 520,   # 40 + 480 (ESM2 t12)
        edge_dim    : int   = 6,
        hidden_dim  : int   = 768,
        n_spatial   : int   = 5,
        n_seq       : int   = 4,
        num_heads   : int   = 8,
        dropout     : float = 0.2,
    ):
        super().__init__()
        assert hidden_dim % num_heads == 0
        self.hidden_dim  = hidden_dim
        head_dim = hidden_dim // num_heads

        # ── 4-layer node encoder (deeper than PocketGNN v2) ───────────────────
        self.node_encoder = nn.Sequential(
            nn.Linear(node_in_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.LayerNorm(hidden_dim // 2),
            nn.Linear(hidden_dim // 2, hidden_dim),
            nn.ReLU(),
            nn.LayerNorm(hidden_dim),
        )

        # ── Spatial branch ────────────────────────────────────────────────────
        self.spatial_convs = nn.ModuleList([
            GATv2Conv(hidden_dim, head_dim, heads=num_heads,
                      edge_dim=edge_dim, dropout=dropout, concat=True)
            for _ in range(n_spatial)
        ])
        self.spatial_norms = nn.ModuleList([
            nn.LayerNorm(hidden_dim) for _ in range(n_spatial)
        ])

        # ── Sequential branch ─────────────────────────────────────────────────
        self.seq_convs = nn.ModuleList([
            GATv2Conv(hidden_dim, head_dim, heads=num_heads,
                      edge_dim=edge_dim, dropout=dropout, concat=True)
            for _ in range(n_seq)
        ])
        self.seq_norms = nn.ModuleList([
            nn.LayerNorm(hidden_dim) for _ in range(n_seq)
        ])

        # ── Virtual node: broadcast global protein context ────────────────────
        self.vnode_proj = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.LayerNorm(hidden_dim),
        )
        self.vnode_gate = nn.Linear(hidden_dim * 2, 1)

        # ── Gated branch fusion ───────────────────────────────────────────────
        self.gate_proj = nn.Linear(hidden_dim * 2, hidden_dim)

        # ── 5-layer scoring head ──────────────────────────────────────────────
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
            nn.Linear(hidden_dim // 8, hidden_dim // 16),
            nn.ReLU(),
            nn.Linear(hidden_dim // 16, 1),
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

        # Spatial branch
        h_s = h
        for conv, norm in zip(self.spatial_convs, self.spatial_norms):
            h_s = norm(h_s + conv(h_s, edge_index, edge_attr))

        # Virtual node: aggregate → project → gate broadcast
        h_vn  = self.vnode_proj(h_s.mean(dim=0, keepdim=True))    # (1, H)
        vn_bc = h_vn.expand(h_s.size(0), -1)                      # (N, H)
        vgate = torch.sigmoid(self.vnode_gate(torch.cat([h_s, vn_bc], dim=-1)))
        h_s   = h_s + vgate * vn_bc                               # (N, H)

        # Sequential branch
        h_b = h
        for conv, norm in zip(self.seq_convs, self.seq_norms):
            h_b = norm(h_b + conv(h_b, edge_index_seq, edge_attr_seq))

        # Gated fusion
        gate    = torch.sigmoid(self.gate_proj(torch.cat([h_s, h_b], dim=-1)))
        h_fused = gate * h_s + (1.0 - gate) * h_b

        return torch.sigmoid(self.head(h_fused).squeeze(-1))

    @classmethod
    def from_esm6(cls) -> "PocketGNNXL":
        """Use ESM2 t6 (320-dim) embeddings → 360-dim input. Faster on CPU."""
        return cls(node_in_dim=cls.HAND_DIM + cls.ESM2_T6_DIM)

    def param_count(self) -> int:
        return sum(p.numel() for p in self.parameters())


# ── Loss functions ────────────────────────────────────────────────────────────

def focal_loss(
    scores : torch.Tensor,
    targets: torch.Tensor,
    gamma  : float = 2.0,
    alpha  : float | None = None,
) -> torch.Tensor:
    """
    Focal loss with auto-calibrated alpha.
    alpha=None (default): alpha = 1 - pos_fraction, giving pocket residues
    proportionally higher weight regardless of class imbalance.
    Pass a fixed float to override (legacy: alpha=0.25 under-weights rare classes).
    """
    if alpha is None:
        pos_frac = targets.float().mean().clamp(0.02, 0.50)
        alpha = float(1.0 - pos_frac)   # e.g. 5% pocket → alpha=0.95
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
    n_pos = min(int(pos_mask.sum()), 32)
    n_neg = min(int(neg_mask.sum()), max(max_pairs // max(n_pos, 1), 1))
    pos_s = scores[pos_mask][:n_pos].unsqueeze(1)
    neg_s = scores[neg_mask][:n_neg].unsqueeze(0)
    return F.relu(margin - (pos_s - neg_s)).mean()


def symmetry_loss(
    scores  : torch.Tensor,
    chain_id: torch.Tensor,
    resid   : torch.Tensor,
    batch   : torch.Tensor | None = None,
) -> torch.Tensor:
    """Penalise score variance among symmetry-equivalent residues (same protein, same resid).

    Uses (batch_index, resid) as the grouping key so residues that share a sequence
    number but belong to different proteins in a batched DataLoader are never mixed.
    When batch is None (single graph), all residues are treated as one protein.
    """
    if batch is None:
        batch = scores.new_zeros(scores.shape[0], dtype=torch.long)

    loss = scores.new_zeros(1).squeeze()
    n_groups = 0
    # Pack (batch_idx, resid) into a single integer key for cheap unique()
    batch_size = int(batch.max().item()) + 1
    resid_range = int(resid.max().item()) + 1
    key = batch * resid_range + resid
    for k in key.unique():
        mask = key == k
        if mask.sum() >= 2:
            loss = loss + scores[mask].var()
            n_groups += 1
    return loss / max(n_groups, 1)


def pocket_loss(
    scores      : torch.Tensor,
    targets     : torch.Tensor,
    chain_id    : torch.Tensor | None = None,
    resid       : torch.Tensor | None = None,
    batch       : torch.Tensor | None = None,
    use_symmetry: bool  = False,
    w_rank      : float = 0.05,
    w_sym       : float = 0.10,
) -> torch.Tensor:
    loss = focal_loss(scores, targets) + w_rank * ranking_loss(scores, targets)
    if use_symmetry and chain_id is not None and resid is not None:
        loss = loss + w_sym * symmetry_loss(scores, chain_id, resid, batch)
    return loss
