"""Governed GraphSAGE-3L model for Phase 3 residue-level pocket prediction.

Architecture (approved in model_training_decision_20260528.md,
decision_id: phase3_model_training_plan_20260528):

  SAGEConv(25 -> H) + ReLU + Dropout(p)
  SAGEConv(H  -> H) + ReLU + Dropout(p)
  SAGEConv(H  -> H) + ReLU
  Linear(H -> 1)               -> scalar logit per residue

Constraints (docs/scientific_governance/08_MODEL_ARCHITECTURE_CONSTRAINTS.md):
  - No sigmoid during training; BCEWithLogitsLoss handles sigmoid internally.
  - No virtual node or global mean across mixed-protein batches.
  - No chain-ID or residue-number in input features (absent from .npz by design).
  - hidden_dim restricted to {64, 128} per approved plan; other values require approval.
"""

from __future__ import annotations

import torch
import torch.nn as nn
from torch_geometric.nn import SAGEConv

from phase3_model.interfaces import ModelOutputContract

_FEATURE_DIM: int = 25
_APPROVED_HIDDEN_DIMS: frozenset[int] = frozenset({64, 128})


class GraphSAGE3L(nn.Module):
    """GraphSAGE with 3 message-passing layers for residue-level logit prediction."""

    output_contract: ModelOutputContract = ModelOutputContract(
        output_name="residue_logits",
        loss_pairing="BCEWithLogitsLoss-compatible logits; no final sigmoid during training",
        batch_isolation_required=True,
        training_status="IMPLEMENTED_DRY_RUN_ONLY",
    )

    def __init__(self, hidden_dim: int = 128, dropout: float = 0.1) -> None:
        """
        Args:
            hidden_dim: Width of all hidden layers (H). Approved: {64, 128}.
            dropout: Dropout probability applied after layers 1 and 2.
        """
        super().__init__()
        if hidden_dim not in _APPROVED_HIDDEN_DIMS:
            raise ValueError(
                f"hidden_dim must be in {sorted(_APPROVED_HIDDEN_DIMS)} per approved "
                f"architecture (got {hidden_dim}). Other values require separate approval."
            )
        self.conv1 = SAGEConv(_FEATURE_DIM, hidden_dim)
        self.conv2 = SAGEConv(hidden_dim, hidden_dim)
        self.conv3 = SAGEConv(hidden_dim, hidden_dim)
        self.head = nn.Linear(hidden_dim, 1)
        self.dropout = nn.Dropout(p=dropout)

    def forward(self, data: object) -> torch.Tensor:
        """Return residue-level logits shape (N,). No sigmoid applied.

        Args:
            data: PyG Batch or Data with attributes .x (N, 25) and .edge_index (2, E).

        Returns:
            Tensor of shape (N,) — one raw logit per residue node.
        """
        x, edge_index = data.x, data.edge_index

        h = self.conv1(x, edge_index)
        h = torch.relu(h)
        h = self.dropout(h)

        h = self.conv2(h, edge_index)
        h = torch.relu(h)
        h = self.dropout(h)

        h = self.conv3(h, edge_index)
        h = torch.relu(h)

        logits = self.head(h).squeeze(-1)  # (N,)
        return logits
