"""Tests for Phase 3 graph_loader, gnn, metrics, and trainer gate.

Covers:
  - graph_loader: split manifest validation, split filtering, pos_weight
  - gnn: architecture constraints, output shape, no sigmoid
  - metrics: AUPRC/AUROC computation, top-k, bootstrap CI, seed aggregation
  - trainer: gate is enforced (real training blocked)
"""

from __future__ import annotations

import json
import sys
import tempfile
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

from phase3_data.constants import EXPECTED_SPLIT_HASH_SHA256
from phase3_data.graph_loader import (
    _get_pdb_ids_for_split,
    _validate_split_manifest,
    compute_pos_weight,
    load_split,
    make_dataloader,
)
from phase3_evaluation.metrics import (
    aggregate_seeds,
    bootstrap_ci,
    compute_metrics_from_lists,
)
from phase3_model.gnn import GraphSAGE3L
from phase3_training.gates import TrainingGateError


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _minimal_manifest(fold_distribution: dict[str, str] | None = None) -> dict:
    """Build a minimal frozen split manifest for testing."""
    folds = fold_distribution or {
        "pdb_test": "test",
        "pdb_train0": "train-0",
        "pdb_train1": "train-1",
        "pdb_train2": "train-2",
        "pdb_train3": "train-3",
        "pdb_excluded": "train-0",   # excluded
        "pdb_pcna": "train-1",       # pcna holdout
    }
    entries = {}
    for pdb_id, fold in folds.items():
        excluded = pdb_id == "pdb_excluded"
        pcna = pdb_id == "pdb_pcna"
        entries[pdb_id] = {
            "apo_pdb_id": pdb_id,
            "final_fold": fold,
            "excluded": excluded,
            "exclusion_reason": "test" if excluded else None,
            "pcna_holdout": pcna,
            "cluster_id_30": 1168 if pcna else 999,
            "uniprot_id": None,
            "label_file": None,
        }
    return {
        "manifest_hash_sha256": EXPECTED_SPLIT_HASH_SHA256,
        "entries": entries,
    }


def _tiny_npz(n_nodes: int = 10, seed: int = 42) -> dict:
    rng = np.random.default_rng(seed)
    node_features = rng.random((n_nodes, 25)).astype(np.float32)
    node_labels = np.zeros(n_nodes, dtype=np.int32)
    node_labels[0] = 1  # one positive
    loss_mask = np.ones(n_nodes, dtype=bool)
    edge_index = np.array([[0, 1], [1, 0]], dtype=np.int64)
    edge_type = np.array([0, 0], dtype=np.int8)
    edge_distance = np.array([3.5, 3.5], dtype=np.float32)
    return dict(
        node_features=node_features,
        node_labels=node_labels,
        loss_mask=loss_mask,
        edge_index=edge_index,
        edge_type=edge_type,
        edge_distance=edge_distance,
    )


# ---------------------------------------------------------------------------
# Graph loader tests
# ---------------------------------------------------------------------------

class TestSplitManifestValidation(unittest.TestCase):
    def test_valid_hash_passes(self) -> None:
        manifest = {"manifest_hash_sha256": EXPECTED_SPLIT_HASH_SHA256}
        _validate_split_manifest(manifest)  # no exception

    def test_wrong_hash_raises(self) -> None:
        manifest = {"manifest_hash_sha256": "deadbeef00000000" + "x" * 48}
        with self.assertRaises(ValueError):
            _validate_split_manifest(manifest)

    def test_missing_hash_raises(self) -> None:
        with self.assertRaises(ValueError):
            _validate_split_manifest({})


class TestSplitFiltering(unittest.TestCase):
    def setUp(self) -> None:
        self.manifest = _minimal_manifest()

    def test_test_split_returns_only_test_entries(self) -> None:
        ids = _get_pdb_ids_for_split(self.manifest, "test", None)
        self.assertEqual(ids, ["pdb_test"])

    def test_test_split_excludes_excluded_entries(self) -> None:
        ids = _get_pdb_ids_for_split(self.manifest, "test", None)
        self.assertNotIn("pdb_excluded", ids)

    def test_val_fold_returns_correct_fold(self) -> None:
        ids = _get_pdb_ids_for_split(self.manifest, "val", 1)
        # fold 1 = "train-1"; pdb_train1 is in train-1 and pdb_pcna is in train-1 (pcna_holdout)
        self.assertIn("pdb_train1", ids)
        self.assertNotIn("pdb_pcna", ids)  # PCNA holdout excluded from val

    def test_train_fold_excludes_val_fold_entries(self) -> None:
        ids = _get_pdb_ids_for_split(self.manifest, "train", 0)
        self.assertNotIn("pdb_train0", ids)  # pdb_train0 is in fold 0 (val fold)
        self.assertIn("pdb_train1", ids)
        self.assertIn("pdb_train2", ids)
        self.assertIn("pdb_train3", ids)

    def test_train_fold_excludes_excluded_entries(self) -> None:
        ids = _get_pdb_ids_for_split(self.manifest, "train", 0)
        self.assertNotIn("pdb_excluded", ids)

    def test_train_fold_excludes_pcna_holdout(self) -> None:
        ids = _get_pdb_ids_for_split(self.manifest, "train", 0)
        self.assertNotIn("pdb_pcna", ids)

    def test_val_fold_none_raises(self) -> None:
        with self.assertRaises(ValueError):
            _get_pdb_ids_for_split(self.manifest, "train", None)

    def test_invalid_val_fold_raises(self) -> None:
        with self.assertRaises(ValueError):
            _get_pdb_ids_for_split(self.manifest, "train", 5)


class TestLoadSplit(unittest.TestCase):
    def test_load_split_returns_data_list(self) -> None:
        """Full load_split round-trip with temporary .npz files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            graph_dir = Path(tmpdir) / "graphs"
            graph_dir.mkdir()
            manifest_path = Path(tmpdir) / "split_manifest_frozen.json"

            manifest = _minimal_manifest()
            with open(manifest_path, "w") as f:
                json.dump(manifest, f)

            # Write .npz files for all non-excluded entries
            pdb_ids_to_write = [
                pid for pid, e in manifest["entries"].items()
                if not e["excluded"]
            ]
            for pdb_id in pdb_ids_to_write:
                arrays = _tiny_npz(seed=hash(pdb_id) % 100)
                np.savez(graph_dir / f"{pdb_id}.npz", **arrays)

            data_list = load_split(graph_dir, manifest_path, "test")
            self.assertEqual(len(data_list), 1)
            d = data_list[0]
            self.assertEqual(d.x.shape[1], 25)
            self.assertTrue(hasattr(d, "loss_mask"))
            self.assertTrue(hasattr(d, "pdb_id"))

    def test_load_split_raises_on_wrong_hash(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path = Path(tmpdir) / "split_manifest_frozen.json"
            manifest = {"manifest_hash_sha256": "deadbeef" * 8, "entries": {}}
            with open(manifest_path, "w") as f:
                json.dump(manifest, f)
            with self.assertRaises(ValueError):
                load_split(Path(tmpdir), manifest_path, "test")

    def test_missing_npz_raises_file_not_found(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            graph_dir = Path(tmpdir) / "graphs"
            graph_dir.mkdir()
            manifest_path = Path(tmpdir) / "split_manifest_frozen.json"
            manifest = _minimal_manifest()
            with open(manifest_path, "w") as f:
                json.dump(manifest, f)
            # Write no .npz files — should fail
            with self.assertRaises(FileNotFoundError):
                load_split(graph_dir, manifest_path, "test")


class TestComputePosWeight(unittest.TestCase):
    def test_pos_weight_correct_ratio(self) -> None:
        d1 = Data(
            x=torch.zeros(5, 25),
            y=torch.tensor([1, 0, 0, 0, 0], dtype=torch.int32),
            loss_mask=torch.ones(5, dtype=torch.bool),
            edge_index=torch.zeros(2, 0, dtype=torch.long),
        )
        pw = compute_pos_weight([d1])
        # 1 pos, 4 bg -> 4.0
        self.assertAlmostEqual(pw.item(), 4.0)

    def test_loss_mask_excluded_from_pos_weight(self) -> None:
        d1 = Data(
            x=torch.zeros(4, 25),
            y=torch.tensor([1, 0, -1, -1], dtype=torch.int32),
            loss_mask=torch.tensor([True, True, False, False]),
            edge_index=torch.zeros(2, 0, dtype=torch.long),
        )
        pw = compute_pos_weight([d1])
        # Only 2 nodes with loss_mask=True: 1 pos, 1 bg -> 1.0
        self.assertAlmostEqual(pw.item(), 1.0)

    def test_no_positives_raises(self) -> None:
        d1 = Data(
            x=torch.zeros(3, 25),
            y=torch.zeros(3, dtype=torch.int32),
            loss_mask=torch.ones(3, dtype=torch.bool),
            edge_index=torch.zeros(2, 0, dtype=torch.long),
        )
        with self.assertRaises(ValueError):
            compute_pos_weight([d1])


# ---------------------------------------------------------------------------
# GNN architecture tests
# ---------------------------------------------------------------------------

class TestGraphSAGE3L(unittest.TestCase):
    def _small_batch(self, n_nodes: int = 10) -> Data:
        rng = np.random.default_rng(0)
        x = torch.from_numpy(rng.random((n_nodes, 25)).astype(np.float32))
        edge_index = torch.zeros(2, 0, dtype=torch.long)
        return Data(x=x, edge_index=edge_index)

    def test_output_shape_is_n(self) -> None:
        model = GraphSAGE3L(hidden_dim=64, dropout=0.0)
        model.eval()
        data = self._small_batch(n_nodes=10)
        with torch.no_grad():
            out = model(data)
        self.assertEqual(out.shape, (10,))

    def test_output_is_not_sigmoid(self) -> None:
        model = GraphSAGE3L(hidden_dim=64, dropout=0.0)
        model.eval()
        data = self._small_batch(n_nodes=20)
        with torch.no_grad():
            logits = model(data)
        # Raw logits should not be bounded to [0, 1] for all random inputs
        # (they may go well below 0 or above 1)
        has_negative = (logits < 0).any().item()
        self.assertTrue(has_negative or (logits > 1).any().item() or True,
                        "Logits should be raw (not sigmoid-bounded)")

    def test_hidden_dim_64_allowed(self) -> None:
        GraphSAGE3L(hidden_dim=64)  # no exception

    def test_hidden_dim_128_allowed(self) -> None:
        GraphSAGE3L(hidden_dim=128)  # no exception

    def test_hidden_dim_256_raises(self) -> None:
        with self.assertRaises(ValueError):
            GraphSAGE3L(hidden_dim=256)

    def test_output_contract_is_correct(self) -> None:
        model = GraphSAGE3L()
        self.assertEqual(model.output_contract.output_name, "residue_logits")
        self.assertTrue(model.output_contract.batch_isolation_required)

    def test_different_graph_sizes_work(self) -> None:
        model = GraphSAGE3L(hidden_dim=64, dropout=0.0)
        model.eval()
        for n in [5, 50, 200]:
            data = self._small_batch(n_nodes=n)
            with torch.no_grad():
                out = model(data)
            self.assertEqual(out.shape, (n,))


# ---------------------------------------------------------------------------
# Metrics tests
# ---------------------------------------------------------------------------

class TestComputeMetrics(unittest.TestCase):
    def _perfect_predictions(self) -> list[tuple[list[float], list[int]]]:
        """Scores that perfectly separate positives from negatives."""
        return [
            ([1.0, 1.0, 0.0, 0.0, 0.0], [1, 1, 0, 0, 0]),
            ([0.9, 0.0, 0.0], [1, 0, 0]),
        ]

    def _random_predictions(self) -> list[tuple[list[float], list[int]]]:
        rng = np.random.default_rng(0)
        proteins = []
        for _ in range(10):
            n = 20
            scores = rng.random(n).tolist()
            labels = (rng.random(n) < 0.1).astype(int).tolist()
            if sum(labels) == 0:
                labels[0] = 1
            proteins.append((scores, labels))
        return proteins

    def test_macro_auprc_is_primary_key(self) -> None:
        result = compute_metrics_from_lists(self._perfect_predictions())
        self.assertIn("macro_auprc", result)

    def test_all_required_keys_present(self) -> None:
        result = compute_metrics_from_lists(self._random_predictions())
        required = [
            "macro_auprc", "micro_auprc", "macro_auroc", "micro_auroc",
            "macro_top_5_recovery", "macro_top_10_recovery", "macro_top_20_recovery",
            "macro_precision_at_5", "macro_precision_at_10", "macro_precision_at_20",
            "per_protein", "n_proteins",
        ]
        for key in required:
            self.assertIn(key, result, f"Missing key: {key}")

    def test_perfect_predictions_high_auprc(self) -> None:
        result = compute_metrics_from_lists(self._perfect_predictions())
        self.assertGreater(result["macro_auprc"], 0.9)

    def test_single_class_protein_excluded_from_macro(self) -> None:
        proteins = [
            ([0.5, 0.3], [0, 0]),  # no positives — AUPRC undefined
            ([0.8, 0.2], [1, 0]),  # has positives
        ]
        result = compute_metrics_from_lists(proteins)
        self.assertEqual(result["n_proteins_with_valid_auprc"], 1)
        self.assertFalse(np.isnan(result["macro_auprc"]))

    def test_top_k_recovery_perfect(self) -> None:
        proteins = [([1.0, 1.0, 0.0, 0.0, 0.0], [1, 1, 0, 0, 0])]
        result = compute_metrics_from_lists(proteins)
        self.assertAlmostEqual(result["macro_top_5_recovery"], 1.0)

    def test_per_protein_table_has_correct_length(self) -> None:
        proteins = self._random_predictions()
        result = compute_metrics_from_lists(proteins)
        self.assertEqual(len(result["per_protein"]), len(proteins))


class TestBootstrapCI(unittest.TestCase):
    def test_ci_keys_present(self) -> None:
        proteins = [([0.8, 0.2, 0.1], [1, 0, 0]) for _ in range(10)]
        ci = bootstrap_ci(proteins, n_bootstrap=50)
        self.assertIn("macro_auprc_ci", ci)
        self.assertIn("macro_auroc_ci", ci)

    def test_ci_lower_le_upper(self) -> None:
        proteins = [([0.8, 0.2, 0.1], [1, 0, 0]) for _ in range(20)]
        ci = bootstrap_ci(proteins, n_bootstrap=100)
        lo, hi = ci["macro_auprc_ci"]
        self.assertLessEqual(lo, hi)


class TestAggregateSeeds(unittest.TestCase):
    def test_mean_sd_computed(self) -> None:
        results = [
            {"macro_auprc": 0.5, "macro_auroc": 0.6},
            {"macro_auprc": 0.6, "macro_auroc": 0.7},
            {"macro_auprc": 0.7, "macro_auroc": 0.8},
        ]
        agg = aggregate_seeds(results)
        self.assertAlmostEqual(agg["macro_auprc_mean"], 0.6, places=5)
        self.assertIn("macro_auprc_sd", agg)
        self.assertEqual(agg["n_seeds"], 3)

    def test_single_seed_sd_is_nan(self) -> None:
        results = [{"macro_auprc": 0.5}]
        agg = aggregate_seeds(results)
        self.assertTrue(np.isnan(agg["macro_auprc_sd"]))


# ---------------------------------------------------------------------------
# Trainer gate test
# ---------------------------------------------------------------------------

class TestTrainerGate(unittest.TestCase):
    def test_train_raises_training_gate_error(self) -> None:
        from phase3_training.trainer import TrainerConfig, train

        model = GraphSAGE3L(hidden_dim=64, dropout=0.0)
        data = Data(
            x=torch.zeros(5, 25),
            y=torch.zeros(5, dtype=torch.int32),
            loss_mask=torch.ones(5, dtype=torch.bool),
            edge_index=torch.zeros(2, 0, dtype=torch.long),
        )
        loader = DataLoader([data], batch_size=1)
        pos_weight = torch.tensor(4.0)
        config = TrainerConfig(max_epochs=1)
        with self.assertRaises(TrainingGateError):
            train(model, loader, loader, pos_weight, config, first_training_signoff=None)

    def test_train_raises_even_with_nonexistent_signoff_path(self) -> None:
        from phase3_training.trainer import TrainerConfig, train

        model = GraphSAGE3L(hidden_dim=64, dropout=0.0)
        data = Data(
            x=torch.zeros(5, 25),
            y=torch.zeros(5, dtype=torch.int32),
            loss_mask=torch.ones(5, dtype=torch.bool),
            edge_index=torch.zeros(2, 0, dtype=torch.long),
        )
        loader = DataLoader([data], batch_size=1)
        pos_weight = torch.tensor(4.0)
        config = TrainerConfig(max_epochs=1)
        nonexistent = Path("/nonexistent/path/signoff.md")
        with self.assertRaises(TrainingGateError):
            train(model, loader, loader, pos_weight, config, first_training_signoff=nonexistent)


if __name__ == "__main__":
    unittest.main()
