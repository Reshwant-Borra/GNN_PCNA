"""Tests for Phase 3 governed graph generation.

Governance: docs/scientific_governance/07_PREPROCESSING_AND_GRAPH_RULES.md
Approval:   reports/phase3/graph_policy_human_decision_20260528.md
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from phase3_data.errors import Phase3DataError
from phase3_data.models import DatasetIndexEntry, Phase3Paths
from phase3_graphs import constants
from phase3_graphs.builder import (
    _build_sequential_edges,
    _build_spatial_edges,
    build_graph,
)
from phase3_graphs.features import (
    FEATURE_DIM,
    MODIFIED_IDX,
    STANDARD_AA,
    UNKNOWN_IDX,
    VOCAB_SIZE,
    is_modified_residue,
    residue_features,
    residue_one_hot_index,
)
from phase3_graphs.manifest import feature_definition_hash, policy_hash
from phase3_graphs.mmcif_coords import extract_ca_coordinates


# ---------------------------------------------------------------------------
# Minimal CIF fixtures
# ---------------------------------------------------------------------------

def _make_cif_with_coords(rows: list[str]) -> str:
    """Build a minimal but valid mmCIF string with coordinate columns."""
    header = """\
data_TEST
#
loop_
_atom_site.group_PDB
_atom_site.label_atom_id
_atom_site.label_alt_id
_atom_site.label_comp_id
_atom_site.label_asym_id
_atom_site.label_entity_id
_atom_site.label_seq_id
_atom_site.pdbx_PDB_ins_code
_atom_site.auth_seq_id
_atom_site.auth_comp_id
_atom_site.auth_asym_id
_atom_site.auth_atom_id
_atom_site.pdbx_PDB_model_num
_atom_site.Cartn_x
_atom_site.Cartn_y
_atom_site.Cartn_z
_atom_site.occupancy
"""
    return header + "\n".join(rows) + "\n#\n"


# Two residues in chain A, seq IDs 1 and 2, CA at (1,2,3) and (10,2,3) — 9 Å apart (> 8 Å)
_CIF_TWO_RESIDUES = _make_cif_with_coords([
    "ATOM CA . GLY A 1 1 ? 1 GLY A CA 1  1.0  2.0  3.0 1.00",
    "ATOM CB . GLY A 1 1 ? 1 GLY A CB 1  4.0  5.0  6.0 1.00",
    "ATOM CA . ALA A 1 2 ? 2 ALA A CA 1 10.0  2.0  3.0 1.00",
])

# Three residues: GLY(1) and ALA(2) at 1 Å apart, SER(3) sequential to ALA
_CIF_THREE_CLOSE = _make_cif_with_coords([
    "ATOM CA . GLY A 1 1 ? 1 GLY A CA 1  1.0  2.0  3.0 1.00",
    "ATOM CA . ALA A 1 2 ? 2 ALA A CA 1  2.0  2.0  3.0 1.00",
    "ATOM CA . SER A 1 3 ? 3 SER A CA 1 20.0  2.0  3.0 1.00",
])

# Residue with altloc: two CA records, altloc A (occ 0.4) and altloc B (occ 0.6)
_CIF_ALTLOC = _make_cif_with_coords([
    "ATOM CA A GLY A 1 1 ? 1 GLY A CA 1  1.0  2.0  3.0 0.40",
    "ATOM CA B GLY A 1 1 ? 1 GLY A CA 1  5.0  6.0  7.0 0.60",
])

# Residue with altloc tie: two CA records same occupancy, altloc A and B
_CIF_ALTLOC_TIE = _make_cif_with_coords([
    "ATOM CA A GLY A 1 1 ? 1 GLY A CA 1  1.0  2.0  3.0 0.50",
    "ATOM CA B GLY A 1 1 ? 1 GLY A CA 1  5.0  6.0  7.0 0.50",
])

# Non-numeric coordinates — should raise Phase3DataError
_CIF_BAD_COORDS = _make_cif_with_coords([
    "ATOM CA . GLY A 1 1 ? 1 GLY A CA 1 NaN 2.0 3.0 1.00",
])

# Residue with gap in seq IDs: 1, 2, 5 (gap between 2 and 5)
_CIF_GAP = _make_cif_with_coords([
    "ATOM CA . GLY A 1 1 ? 1 GLY A CA 1  1.0  2.0  3.0 1.00",
    "ATOM CA . ALA A 1 2 ? 2 ALA A CA 1  2.0  2.0  3.0 1.00",
    "ATOM CA . SER A 1 5 ? 5 SER A CA 1  3.0  2.0  3.0 1.00",
])

# Two chains: A (seq 1,2) and B (seq 1,2) — no cross-chain sequential edges
_CIF_TWO_CHAINS = _make_cif_with_coords([
    "ATOM CA . GLY A 1 1 ? 1 GLY A CA 1 1.0 2.0 3.0 1.00",
    "ATOM CA . ALA A 1 2 ? 2 ALA A CA 1 2.0 2.0 3.0 1.00",
    "ATOM CA . GLY B 1 1 ? 1 GLY B CA 1 1.0 2.0 3.0 1.00",
    "ATOM CA . ALA B 1 2 ? 2 ALA B CA 1 2.0 2.0 3.0 1.00",
])


def _minimal_label_file(
    apo_pdb_id: str,
    chain: str,
    fold: str,
    labels: dict[str, int],
    pos_count: int,
    masked_count: int,
) -> str:
    return json.dumps({
        "apo_pdb_id": apo_pdb_id,
        "chain": chain,
        "fold": fold,
        "pocket_token_count": pos_count,
        "positive_count": pos_count,
        "masked_count": masked_count,
        "remapped_count": 0,
        "fraction_masked": 0.0,
        "labels": labels,
        "generated_at": "2026-05-28T00:00:00",
        "governance": "docs/scientific_governance/06_LABELING_RULES.md",
    })


def _setup_tmp_entry(
    tmp_root: Path,
    apo_id: str,
    cif_content: str,
    label_content: str,
    fold: str = "train-0",
    pos_count: int = 0,
    masked_count: int = 0,
    explicit_label_count: int = 0,
) -> tuple[Phase3Paths, DatasetIndexEntry]:
    cif_dir = tmp_root / "data/raw_intake/cryptobench/cif-files"
    cif_dir.mkdir(parents=True, exist_ok=True)
    label_dir = tmp_root / "data/labels"
    label_dir.mkdir(parents=True, exist_ok=True)

    cif_rel = Path(f"data/raw_intake/cryptobench/cif-files/{apo_id}.cif")
    label_rel = Path(f"data/labels/labels_{apo_id}.json")

    (tmp_root / cif_rel).write_text(cif_content, encoding="utf-8")
    (tmp_root / label_rel).write_text(label_content, encoding="utf-8")

    paths = Phase3Paths(root=tmp_root)
    entry = DatasetIndexEntry(
        apo_pdb_id=apo_id,
        fold=fold,
        requested_split="train",
        cluster_id_30=1,
        uniprot_id=None,
        label_path=str(label_rel),
        cif_path=str(cif_rel),
        label_hash_sha256_prefix="unused",
        positive_count=pos_count,
        masked_count=masked_count,
        explicit_label_count=explicit_label_count,
    )
    return paths, entry


class TestResidueFeatures(unittest.TestCase):
    def test_standard_aa_one_hot(self) -> None:
        # GLY is at index 7 in alphabetical order
        feat = residue_features("GLY", is_modified=False, has_ca=True, has_altloc=False)
        self.assertEqual(feat.shape, (FEATURE_DIM,))
        self.assertEqual(feat.dtype, np.float32)
        self.assertEqual(feat[7], 1.0)
        self.assertEqual(feat.sum(), 1.0)

    def test_all_standard_aa_one_hot_correct(self) -> None:
        for i, aa in enumerate(STANDARD_AA):
            feat = residue_features(aa, is_modified=False, has_ca=True, has_altloc=False)
            self.assertEqual(feat[i], 1.0, f"{aa} should be at index {i}")

    def test_modified_residue_encoding(self) -> None:
        feat = residue_features("MSE", is_modified=True, has_ca=True, has_altloc=False)
        self.assertEqual(feat[MODIFIED_IDX], 1.0)
        self.assertEqual(feat[VOCAB_SIZE], 1.0)  # is_modified flag

    def test_unknown_residue_encoding(self) -> None:
        feat = residue_features("XYZ", is_modified=False, has_ca=True, has_altloc=False)
        self.assertEqual(feat[UNKNOWN_IDX], 1.0)

    def test_missing_ca_flag(self) -> None:
        feat = residue_features("ALA", is_modified=False, has_ca=False, has_altloc=False)
        self.assertEqual(feat[VOCAB_SIZE + 1], 1.0)

    def test_has_altloc_flag(self) -> None:
        feat = residue_features("ALA", is_modified=False, has_ca=True, has_altloc=True)
        self.assertEqual(feat[VOCAB_SIZE + 2], 1.0)

    def test_is_modified_residue(self) -> None:
        self.assertFalse(is_modified_residue("GLY"))
        self.assertFalse(is_modified_residue("ALA"))
        self.assertTrue(is_modified_residue("MSE"))
        self.assertTrue(is_modified_residue("SEP"))


class TestCACoordinateExtraction(unittest.TestCase):
    def test_single_ca(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".cif", mode="w", delete=False, encoding="utf-8") as f:
            f.write(_CIF_TWO_RESIDUES)
            tmp = Path(f.name)
        coords = extract_ca_coordinates(tmp)
        tmp.unlink()
        self.assertIn(("A", "1", None), coords)
        x, y, z, alt = coords[("A", "1", None)]
        self.assertAlmostEqual(x, 1.0)
        self.assertAlmostEqual(y, 2.0)
        self.assertAlmostEqual(z, 3.0)
        self.assertIsNone(alt)  # no altloc

    def test_altloc_highest_occupancy_wins(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".cif", mode="w", delete=False, encoding="utf-8") as f:
            f.write(_CIF_ALTLOC)
            tmp = Path(f.name)
        coords = extract_ca_coordinates(tmp)
        tmp.unlink()
        self.assertIn(("A", "1", None), coords)
        x, y, z, alt = coords[("A", "1", None)]
        # altloc B has occ 0.6 — its coords are (5,6,7)
        self.assertAlmostEqual(x, 5.0)
        self.assertEqual(alt, "B")

    def test_altloc_tie_prefers_a_over_b(self) -> None:
        # Equal occupancy: altloc A and B — A < B lexicographically → A wins
        with tempfile.NamedTemporaryFile(suffix=".cif", mode="w", delete=False, encoding="utf-8") as f:
            f.write(_CIF_ALTLOC_TIE)
            tmp = Path(f.name)
        coords = extract_ca_coordinates(tmp)
        tmp.unlink()
        _, _, _, alt = coords[("A", "1", None)]
        self.assertEqual(alt, "A")

    def test_non_numeric_coords_fail_closed(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".cif", mode="w", delete=False, encoding="utf-8") as f:
            f.write(_CIF_BAD_COORDS)
            tmp = Path(f.name)
        with self.assertRaises(Phase3DataError):
            extract_ca_coordinates(tmp)
        tmp.unlink()

    def test_non_ca_atoms_excluded(self) -> None:
        # CB atom in TWO_RESIDUES should not appear in coords
        with tempfile.NamedTemporaryFile(suffix=".cif", mode="w", delete=False, encoding="utf-8") as f:
            f.write(_CIF_TWO_RESIDUES)
            tmp = Path(f.name)
        coords = extract_ca_coordinates(tmp)
        tmp.unlink()
        self.assertEqual(len(coords), 2)  # GLY and ALA only (CB excluded)


class TestSpatialEdges(unittest.TestCase):
    def _write_tmp_cif(self, content: str) -> Path:
        import tempfile as tf
        f = tf.NamedTemporaryFile(suffix=".cif", mode="w", delete=False, encoding="utf-8")
        f.write(content)
        f.close()
        return Path(f.name)

    def test_residues_within_cutoff_get_edge(self) -> None:
        tmp = self._write_tmp_cif(_CIF_THREE_CLOSE)
        ca_coords = extract_ca_coordinates(tmp)
        tmp.unlink()
        # GLY(1) at (1,2,3) and ALA(2) at (2,2,3) → distance=1.0 Å < 8.0
        node_keys = [("A", "1", None), ("A", "2", None), ("A", "3", None)]
        ei, dists = _build_spatial_edges(ca_coords, node_keys, constants.CA_CUTOFF_ANGSTROM)
        # GLY-ALA pair: 1.0 Å; ALA-SER: 18.0 Å; GLY-SER: 19.0 Å — only GLY-ALA within cutoff
        unique_pairs = set(map(tuple, ei.T.tolist()))
        self.assertIn((0, 1), unique_pairs)
        self.assertIn((1, 0), unique_pairs)
        self.assertNotIn((1, 2), unique_pairs)
        self.assertNotIn((0, 2), unique_pairs)

    def test_residues_beyond_cutoff_no_edge(self) -> None:
        tmp = self._write_tmp_cif(_CIF_TWO_RESIDUES)
        ca_coords = extract_ca_coordinates(tmp)
        tmp.unlink()
        # Distance = 9.0 Å > 8.0 Å
        node_keys = [("A", "1", None), ("A", "2", None)]
        ei, _ = _build_spatial_edges(ca_coords, node_keys, constants.CA_CUTOFF_ANGSTROM)
        self.assertEqual(ei.shape[1], 0)

    def test_node_without_ca_omitted_from_spatial_edges(self) -> None:
        # Only one CA in coords, other node has no CA
        ca_coords = {("A", "1", None): (1.0, 2.0, 3.0, None)}
        node_keys = [("A", "1", None), ("A", "2", None)]  # node 1 has no CA
        ei, _ = _build_spatial_edges(ca_coords, node_keys, constants.CA_CUTOFF_ANGSTROM)
        self.assertEqual(ei.shape[1], 0)

    def test_edge_distances_are_correct(self) -> None:
        tmp = self._write_tmp_cif(_CIF_THREE_CLOSE)
        ca_coords = extract_ca_coordinates(tmp)
        tmp.unlink()
        node_keys = [("A", "1", None), ("A", "2", None), ("A", "3", None)]
        ei, dists = _build_spatial_edges(ca_coords, node_keys, constants.CA_CUTOFF_ANGSTROM)
        # The only edges are (0,1) and (1,0) — each with distance 1.0
        for d in dists:
            self.assertAlmostEqual(d, 1.0, places=4)

    def test_undirected_both_directions_stored(self) -> None:
        ca_coords = {
            ("A", "1", None): (1.0, 2.0, 3.0, None),
            ("A", "2", None): (2.0, 2.0, 3.0, None),
        }
        node_keys = [("A", "1", None), ("A", "2", None)]
        ei, _ = _build_spatial_edges(ca_coords, node_keys, constants.CA_CUTOFF_ANGSTROM)
        pairs = set(map(tuple, ei.T.tolist()))
        self.assertIn((0, 1), pairs)
        self.assertIn((1, 0), pairs)
        self.assertEqual(ei.shape[1], 2)


class TestSequentialEdges(unittest.TestCase):
    def _make_node(self, chain: str, res_num: str, label_seq_id: str | None):
        from phase3_data.models import ResidueNode
        return ResidueNode(
            chain_id=chain,
            residue_number=res_num,
            insertion_code=None,
            residue_name="GLY",
            label_key=f"{chain}_{res_num}",
            label_seq_id=label_seq_id,
            entity_id="1",
            atom_count=1,
            atom_names=("CA",),
            altloc_ids=(),
            has_ca=True,
        )

    def test_consecutive_residues_get_edge(self) -> None:
        nodes = [
            self._make_node("A", "1", "1"),
            self._make_node("A", "2", "2"),
        ]
        key_to_idx = {("A", "1", None): 0, ("A", "2", None): 1}
        ei = _build_sequential_edges(nodes, key_to_idx)
        pairs = set(map(tuple, ei.T.tolist()))
        self.assertIn((0, 1), pairs)
        self.assertIn((1, 0), pairs)

    def test_gap_in_seq_id_no_edge(self) -> None:
        nodes = [
            self._make_node("A", "1", "1"),
            self._make_node("A", "2", "2"),
            self._make_node("A", "5", "5"),
        ]
        key_to_idx = {
            ("A", "1", None): 0,
            ("A", "2", None): 1,
            ("A", "5", None): 2,
        }
        ei = _build_sequential_edges(nodes, key_to_idx)
        pairs = set(map(tuple, ei.T.tolist()))
        # (1,2) consecutive → edge; (2,5) gap → no edge
        self.assertIn((0, 1), pairs)
        self.assertIn((1, 0), pairs)
        self.assertNotIn((1, 2), pairs)
        self.assertNotIn((2, 1), pairs)

    def test_no_cross_chain_sequential_edges(self) -> None:
        nodes = [
            self._make_node("A", "1", "1"),
            self._make_node("B", "2", "2"),
        ]
        key_to_idx = {("A", "1", None): 0, ("B", "2", None): 1}
        ei = _build_sequential_edges(nodes, key_to_idx)
        self.assertEqual(ei.shape[1], 0)

    def test_missing_seq_id_skipped(self) -> None:
        # Residue without label_seq_id cannot participate in sequential edges
        nodes = [
            self._make_node("A", "1", "1"),
            self._make_node("A", "2", None),  # no label_seq_id
        ]
        key_to_idx = {("A", "1", None): 0, ("A", "2", None): 1}
        ei = _build_sequential_edges(nodes, key_to_idx)
        self.assertEqual(ei.shape[1], 0)

    def test_sequential_edges_are_undirected(self) -> None:
        nodes = [
            self._make_node("A", "1", "1"),
            self._make_node("A", "2", "2"),
            self._make_node("A", "3", "3"),
        ]
        key_to_idx = {("A", "1", None): 0, ("A", "2", None): 1, ("A", "3", None): 2}
        ei = _build_sequential_edges(nodes, key_to_idx)
        pairs = set(map(tuple, ei.T.tolist()))
        # Expect both directions for each consecutive pair
        for src, dst in [(0, 1), (1, 0), (1, 2), (2, 1)]:
            self.assertIn((src, dst), pairs)
        self.assertEqual(ei.shape[1], 4)  # 2 pairs × 2 directions


class TestBuildGraph(unittest.TestCase):
    def _dummy_hashes(self) -> tuple[str, str]:
        return "a" * 64, "b" * 64

    def test_minimal_graph_builds_correctly(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            label_json = _minimal_label_file(
                "test", "A", "train-0",
                labels={},  # all background
                pos_count=0,
                masked_count=0,
            )
            paths, entry = _setup_tmp_entry(
                root, "test", _CIF_TWO_RESIDUES, label_json,
                pos_count=0, masked_count=0,
            )
            ph, fh = self._dummy_hashes()
            result = build_graph(paths, entry, ph, fh)

        self.assertEqual(result.structure_id, "test")
        self.assertEqual(result.node_features.shape, (2, FEATURE_DIM))
        self.assertEqual(result.node_features.dtype, np.float32)
        self.assertEqual(result.node_labels.shape, (2,))
        self.assertEqual(result.loss_mask.shape, (2,))
        self.assertEqual(result.edge_index.shape[0], 2)
        self.assertEqual(len(result.node_metadata), 2)

    def test_no_training_performed_flag(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            label_json = _minimal_label_file("test", "A", "train-0", {}, 0, 0)
            paths, entry = _setup_tmp_entry(root, "test", _CIF_TWO_RESIDUES, label_json)
            ph, fh = self._dummy_hashes()
            result = build_graph(paths, entry, ph, fh)
        self.assertTrue(result.manifest_entry["NO_TRAINING_PERFORMED"])

    def test_positive_label_aligns_to_node(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            # GLY at seq 1 → label_key "A_1"
            label_json = _minimal_label_file(
                "test", "A", "train-0",
                labels={"A_1": 1},
                pos_count=1,
                masked_count=0,
            )
            paths, entry = _setup_tmp_entry(
                root, "test", _CIF_TWO_RESIDUES, label_json, pos_count=1,
            )
            ph, fh = self._dummy_hashes()
            result = build_graph(paths, entry, ph, fh)
        labels = result.node_labels.tolist()
        loss_masks = result.loss_mask.tolist()
        pos_idx = next(i for i, m in enumerate(result.node_metadata) if m["label_key"] == "A_1")
        self.assertEqual(labels[pos_idx], 1)
        self.assertTrue(loss_masks[pos_idx])

    def test_masked_label_has_loss_mask_false(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            label_json = _minimal_label_file(
                "test", "A", "train-0",
                labels={"A_1": -1},
                pos_count=0,
                masked_count=1,
            )
            paths, entry = _setup_tmp_entry(
                root, "test", _CIF_TWO_RESIDUES, label_json, masked_count=1,
            )
            ph, fh = self._dummy_hashes()
            result = build_graph(paths, entry, ph, fh)
        masked_idx = next(
            i for i, m in enumerate(result.node_metadata) if m["label_key"] == "A_1"
        )
        self.assertEqual(result.node_labels[masked_idx], -1)
        self.assertFalse(result.loss_mask[masked_idx])

    def test_nonexistent_positive_label_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            label_json = _minimal_label_file(
                "test", "A", "train-0",
                labels={"A_999": 1},  # residue 999 does not exist
                pos_count=1,
                masked_count=0,
            )
            paths, entry = _setup_tmp_entry(
                root, "test", _CIF_TWO_RESIDUES, label_json, pos_count=1,
            )
            ph, fh = self._dummy_hashes()
            with self.assertRaises(Phase3DataError):
                build_graph(paths, entry, ph, fh)

    def test_spatial_edges_within_cutoff_present(self) -> None:
        # GLY(1) and ALA(2) are 1.0 Å apart in _CIF_THREE_CLOSE
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            label_json = _minimal_label_file("test", "A", "train-0", {}, 0, 0)
            paths, entry = _setup_tmp_entry(
                root, "test", _CIF_THREE_CLOSE, label_json,
            )
            ph, fh = self._dummy_hashes()
            result = build_graph(paths, entry, ph, fh)
        spatial_mask = result.edge_type == constants.EDGE_TYPE_SPATIAL
        self.assertTrue(spatial_mask.any(), "Expected at least one spatial edge")

    def test_sequential_edges_no_gap_bridging(self) -> None:
        # _CIF_GAP: seq IDs 1,2,5 → only (1,2) gets a sequential edge
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            label_json = _minimal_label_file("test", "A", "train-0", {}, 0, 0)
            paths, entry = _setup_tmp_entry(root, "test", _CIF_GAP, label_json)
            ph, fh = self._dummy_hashes()
            result = build_graph(paths, entry, ph, fh)
        seq_mask = result.edge_type == constants.EDGE_TYPE_SEQUENTIAL
        seq_edges = result.edge_index[:, seq_mask].T.tolist()
        # Node indices: GLY(1)=0, ALA(2)=1, SER(5)=2
        # Expect (0,1) and (1,0) but not (1,2) or (2,1)
        pairs = set(map(tuple, seq_edges))
        self.assertIn((0, 1), pairs)
        self.assertIn((1, 0), pairs)
        self.assertNotIn((1, 2), pairs)
        self.assertNotIn((2, 1), pairs)

    def test_manifest_contains_required_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            label_json = _minimal_label_file("test", "A", "train-0", {}, 0, 0)
            paths, entry = _setup_tmp_entry(root, "test", _CIF_TWO_RESIDUES, label_json)
            ph, fh = self._dummy_hashes()
            result = build_graph(paths, entry, ph, fh)

        required = [
            "structure_id", "fold", "cif_hash_sha256", "label_hash_sha256",
            "policy_hash_sha256", "feature_hash_sha256", "graph_hash_sha256",
            "included_chains", "excluded_chains", "node_count",
            "positive_count", "masked_count", "background_count",
            "masked_label_entries_without_nodes", "spatial_edge_pairs",
            "sequential_edge_pairs", "total_directed_edges", "nodes_without_ca",
            "nodes_with_altloc", "ca_cutoff_angstrom", "NO_TRAINING_PERFORMED",
            "graph_policy_decision_id", "governance",
        ]
        for field in required:
            self.assertIn(field, result.manifest_entry, f"Missing field: {field}")

    def test_graph_hash_is_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            label_json = _minimal_label_file("test", "A", "train-0", {}, 0, 0)
            paths, entry = _setup_tmp_entry(root, "test", _CIF_TWO_RESIDUES, label_json)
            ph, fh = self._dummy_hashes()
            r1 = build_graph(paths, entry, ph, fh)
            r2 = build_graph(paths, entry, ph, fh)
        self.assertEqual(
            r1.manifest_entry["graph_hash_sha256"],
            r2.manifest_entry["graph_hash_sha256"],
        )


class TestManifestHelpers(unittest.TestCase):
    def test_feature_definition_hash_is_stable(self) -> None:
        h1 = feature_definition_hash()
        h2 = feature_definition_hash()
        self.assertEqual(h1, h2)
        self.assertEqual(len(h1), 64)

    def test_policy_hash_requires_approval_record(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            # Approval record does not exist in tmp dir
            with self.assertRaises(Phase3DataError):
                policy_hash(root)

    def test_policy_hash_stable_with_real_record(self) -> None:
        if not (ROOT / constants.GRAPH_POLICY_APPROVAL_PATH).is_file():
            self.skipTest("Graph policy approval record not present in workspace")
        h1 = policy_hash(ROOT)
        h2 = policy_hash(ROOT)
        self.assertEqual(h1, h2)
        self.assertEqual(len(h1), 64)


class TestGraphConstants(unittest.TestCase):
    def test_ca_cutoff_is_approved_value(self) -> None:
        self.assertEqual(constants.CA_CUTOFF_ANGSTROM, 8.0)

    def test_edge_type_values(self) -> None:
        self.assertEqual(constants.EDGE_TYPE_SPATIAL, 0)
        self.assertEqual(constants.EDGE_TYPE_SEQUENTIAL, 1)

    def test_feature_dim(self) -> None:
        self.assertEqual(FEATURE_DIM, 25)
        self.assertEqual(VOCAB_SIZE, 22)
        self.assertEqual(len(STANDARD_AA), 20)


if __name__ == "__main__":
    unittest.main()
