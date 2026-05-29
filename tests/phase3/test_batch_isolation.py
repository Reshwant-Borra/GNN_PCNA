"""Batch-isolation unit test for Phase 3 GraphSAGE-3L.

Per docs/scientific_governance/08_MODEL_ARCHITECTURE_CONSTRAINTS.md:
  "Batch two proteins in different orders and verify each protein's logits
   match single-protein inference within numerical tolerance."

GATE 2 requirement: this test MUST PASS before real training is allowed.
If it fails, stop. Do NOT weaken the tolerance or skip assertions.

Tests:
  1. Protein A's logits in batch [A, B] match single-protein A (atol=1e-5).
  2. Protein B's logits in batch [A, B] match single-protein B (atol=1e-5).
  3. Protein A's logits in reversed batch [B, A] match single-protein A.
  4. Protein B's logits in reversed batch [B, A] match single-protein B.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np
import torch
from torch_geometric.data import Data
from torch_geometric.loader import DataLoader

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from phase3_model.gnn import GraphSAGE3L


def _make_synthetic_graph(n_nodes: int, n_edges: int, seed: int) -> Data:
    """Create a reproducible synthetic protein graph for testing."""
    rng = np.random.default_rng(seed)
    x = torch.from_numpy(rng.random((n_nodes, 25)).astype(np.float32))
    src = rng.integers(0, n_nodes, n_edges).astype(np.int64)
    dst = rng.integers(0, n_nodes, n_edges).astype(np.int64)
    edge_index = torch.from_numpy(np.stack([src, dst], axis=0))
    y = torch.zeros(n_nodes, dtype=torch.int32)
    loss_mask = torch.ones(n_nodes, dtype=torch.bool)
    return Data(x=x, edge_index=edge_index, y=y, loss_mask=loss_mask)


class TestBatchIsolation(unittest.TestCase):
    """Verify that batching proteins does not contaminate each other's logits."""

    @classmethod
    def setUpClass(cls) -> None:
        # dropout=0.0 is required: stochastic dropout breaks the equality.
        cls.model = GraphSAGE3L(hidden_dim=64, dropout=0.0)
        cls.model.eval()
        cls.graph_a = _make_synthetic_graph(n_nodes=40, n_edges=80, seed=0)
        cls.graph_b = _make_synthetic_graph(n_nodes=55, n_edges=110, seed=1)

    def _infer_single(self, g: Data) -> torch.Tensor:
        with torch.no_grad():
            return self.model(g)

    def _infer_batched(self, *graphs: Data) -> list[torch.Tensor]:
        loader = DataLoader(list(graphs), batch_size=len(graphs), shuffle=False)
        batch = next(iter(loader))
        with torch.no_grad():
            logits = self.model(batch)
        return [logits[batch.batch == i] for i in range(len(graphs))]

    def test_a_isolated_in_ab_batch(self) -> None:
        single_a = self._infer_single(self.graph_a)
        batched_a, _ = self._infer_batched(self.graph_a, self.graph_b)
        torch.testing.assert_close(batched_a, single_a, atol=1e-5, rtol=0.0)

    def test_b_isolated_in_ab_batch(self) -> None:
        single_b = self._infer_single(self.graph_b)
        _, batched_b = self._infer_batched(self.graph_a, self.graph_b)
        torch.testing.assert_close(batched_b, single_b, atol=1e-5, rtol=0.0)

    def test_a_isolated_in_ba_batch_reversed(self) -> None:
        single_a = self._infer_single(self.graph_a)
        _, batched_a = self._infer_batched(self.graph_b, self.graph_a)
        torch.testing.assert_close(batched_a, single_a, atol=1e-5, rtol=0.0)

    def test_b_isolated_in_ba_batch_reversed(self) -> None:
        single_b = self._infer_single(self.graph_b)
        batched_b, _ = self._infer_batched(self.graph_b, self.graph_a)
        torch.testing.assert_close(batched_b, single_b, atol=1e-5, rtol=0.0)


if __name__ == "__main__":
    unittest.main()
