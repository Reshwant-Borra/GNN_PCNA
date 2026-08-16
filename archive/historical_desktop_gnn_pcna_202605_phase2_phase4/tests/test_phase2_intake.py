from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from phase2_intake.io.downloader import guarded_target
from phase2_intake.io.inventory import build_inventory
from phase2_intake.io.schema_detector import schema_status_for_path
from phase2_intake.models import BULK_STOP_MARKER, FORBIDDEN_READINESS_LABELS, ManifestEntry, utc_now


class IntakeSafetyTests(unittest.TestCase):
    def test_guarded_target_blocks_path_escape(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with self.assertRaises(ValueError):
                guarded_target(root, "cryptobench", "../../outside.txt")

    def test_guarded_target_allows_source_subpath(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = guarded_target(root, "cryptobench", "metadata/osf.json")
            self.assertTrue(str(target).endswith("cryptobench/metadata/osf.json") or str(target).endswith("cryptobench\\metadata\\osf.json"))

    def test_schema_detector_json_is_partial_not_inferred_from_name_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.json"
            path.write_text(json.dumps({"a": 1, "b": 2}), encoding="utf-8")
            status, note = schema_status_for_path(path)
            self.assertEqual(status, "SCHEMA_PARTIAL")
            self.assertIn("a", note)

    def test_inventory_never_adopts_downloaded_rows(self) -> None:
        row = ManifestEntry(
            timestamp=utc_now(),
            source_name="cryptobench",
            target="metadata",
            url="https://example.org",
            action="downloaded",
            local_path="data/raw_intake/cryptobench/metadata.json",
            file_size_bytes=12,
            sha256="abc",
            license_status="LICENSE_UNRESOLVED",
            schema_status="SCHEMA_PARTIAL",
            trust_level="official_metadata",
        ).to_json_dict()
        inventory = build_inventory([row])
        self.assertEqual(inventory["final_status"], "RAW_ASSETS_ACQUIRED_NOT_VERIFIED")
        self.assertEqual(inventory["items"][0]["adoption_status"], "not_adopted")
        self.assertEqual(inventory["items"][0]["lifecycle_status"], "quarantined")

    def test_forbidden_readiness_labels_are_registered(self) -> None:
        self.assertIn("READY_FOR_TRAINING", FORBIDDEN_READINESS_LABELS)
        self.assertIn("READY_FOR_SPLIT_FREEZE", FORBIDDEN_READINESS_LABELS)
        self.assertIn("READY_FOR_LABEL_FREEZE", FORBIDDEN_READINESS_LABELS)

    def test_bulk_stop_marker_is_exact(self) -> None:
        self.assertEqual(BULK_STOP_MARKER, "HUMAN_APPROVAL_REQUIRED_FOR_BULK_DOWNLOAD")


if __name__ == "__main__":
    unittest.main()
