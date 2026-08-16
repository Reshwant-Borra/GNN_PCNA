from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from phase3_data.cif_archive import inspect_cif_inputs
from phase3_data.errors import Phase3DataError
from phase3_data.index import _assert_pcna_not_train_or_validation, build_dataset_index
from phase3_data.io import reject_original_folds_path
from phase3_data.labels import load_structure_label_file
from phase3_data.manifests import (
    load_split_manifest,
    reject_forbidden_supervised_source,
    validate_governed_inputs,
)
from phase3_data.models import DatasetIndexEntry, Phase3Paths, SplitEntry
from phase3_data.audit import audit_index_entry


MINIMAL_MMCIF = """data_TEST
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
ATOM CA . GLY A 1 1 ? 1 GLY A CA 1
#
"""


class Phase3DataGovernanceTests(unittest.TestCase):
    def test_split_manifest_loads_from_frozen_path(self) -> None:
        paths = Phase3Paths(root=ROOT)
        summary = validate_governed_inputs(paths)
        self.assertEqual(summary["frozen_split_hash"][:16], "24dd5e347d880108")

    def test_original_folds_json_is_rejected(self) -> None:
        with self.assertRaises(Phase3DataError):
            reject_original_folds_path(Path("data/raw_intake/cryptobench/metadata_files/folds.json"))
        with self.assertRaises(Phase3DataError):
            load_split_manifest(Path("folds.json"))

    def test_friend_crawl_paths_are_rejected_for_supervised_phase3(self) -> None:
        with self.assertRaises(Phase3DataError):
            reject_forbidden_supervised_source(Path("data/registries/friend_crawl_registry.json"))

    def test_excluded_records_are_skipped_in_index(self) -> None:
        entries = build_dataset_index(Phase3Paths(root=ROOT), requested_split="all", require_cif=False)
        ids = {entry.apo_pdb_id for entry in entries}
        self.assertEqual(len(entries), 1101)
        for excluded in {"1lx7", "2b23", "4gpi", "5e0v", "8hc1", "8oqp"}:
            self.assertNotIn(excluded, ids)

    def test_masked_label_is_excluded_from_loss(self) -> None:
        _, labels = load_structure_label_file(ROOT / "data/labels/labels_1fd4.json")
        masked = labels["G_10"]
        self.assertEqual(masked.label, -1)
        self.assertFalse(masked.loss_mask)
        self.assertEqual(masked.supervision_role, "masked_from_loss")

    def test_pcna_cluster_cannot_enter_train_or_validation(self) -> None:
        entry = SplitEntry(
            apo_pdb_id="5e0v",
            original_fold="test",
            final_fold="train-0",
            cluster_id_30=1168,
            uniprot_id="P12004",
            pcna_holdout=True,
            excluded=False,
            exclusion_reason=None,
            label_file=Path("data/labels/labels_5e0v.json"),
        )
        with self.assertRaises(Phase3DataError):
            _assert_pcna_not_train_or_validation(entry, "train")
        with self.assertRaises(Phase3DataError):
            _assert_pcna_not_train_or_validation(entry, "validation")

    def test_label_residue_mismatch_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "data/raw_intake/cryptobench/cif-files").mkdir(parents=True)
            (root / "data/labels").mkdir(parents=True)
            cif_rel = Path("data/raw_intake/cryptobench/cif-files/test.cif")
            label_rel = Path("data/labels/labels_test.json")
            (root / cif_rel).write_text(MINIMAL_MMCIF, encoding="utf-8")
            (root / label_rel).write_text(
                (
                    '{"apo_pdb_id":"test","chain":"A","fold":"train-0",'
                    '"pocket_token_count":1,"positive_count":1,"masked_count":0,'
                    '"remapped_count":0,"fraction_masked":0.0,'
                    '"labels":{"A_999":1},'
                    '"generated_at":"2026-05-28T00:00:00",'
                    '"governance":"docs/scientific_governance/06_LABELING_RULES.md"}'
                ),
                encoding="utf-8",
            )
            entry = DatasetIndexEntry(
                apo_pdb_id="test",
                fold="train-0",
                requested_split="train",
                cluster_id_30=1,
                uniprot_id=None,
                label_path=str(label_rel),
                cif_path=str(cif_rel),
                label_hash_sha256_prefix="unused",
                positive_count=1,
                masked_count=0,
                explicit_label_count=1,
            )
            with self.assertRaises(Phase3DataError):
                audit_index_entry(Phase3Paths(root=root), entry)

    def test_missing_cif_dir_and_zip_has_clear_status(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            state = inspect_cif_inputs(Phase3Paths(root=Path(tmp)))
            self.assertEqual(state["status"], "MISSING_CIF_DIR_AND_ZIP")
            self.assertFalse(state["cif_zip_exists"])


if __name__ == "__main__":
    unittest.main()

