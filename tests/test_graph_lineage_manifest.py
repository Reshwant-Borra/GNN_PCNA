from __future__ import annotations

import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

import verify_graph_lineage


def test_graph_lineage_manifest_loads_55_structure_contract():
    manifest = verify_graph_lineage.load_manifest(
        REPO / "artifacts" / "provenance" / "GRAPH_LINEAGE_520_MANIFEST.json"
    )
    assert manifest["graphs"]["structure_count"] == 55
    assert len(manifest["graphs"]["per_structure"]) == 55
    assert manifest["feature_contract"]["node_features_total"] == 520
    assert manifest["graphs"]["split_counts"] == {"train": 43, "val": 6, "test": 6}
    assert manifest["graphs"]["graph_manifest_hash"] == (
        "69744b548e812697ba9015c6563ed526f1af2e915b1595badb1dd47fd1b4c64f"
    )


def test_graph_lineage_missing_clean_clone_graphs_are_retrievable_not_silent(tmp_path):
    manifest = verify_graph_lineage.load_manifest(
        REPO / "artifacts" / "provenance" / "GRAPH_LINEAGE_520_MANIFEST.json"
    )
    result = verify_graph_lineage.validate(manifest, tmp_path / "graphs_xl")
    assert not result["ok"]
    assert result["found_graphs"] == 0
    assert result["expected_graphs"] == 55
    assert manifest["retrieval"]["verification_command"] == (
        "python3 scripts/verify_graph_lineage.py --retrieve-from-origin"
    )
