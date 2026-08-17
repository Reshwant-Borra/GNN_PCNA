"""The frozen protocol's provenance pointers must actually bind to the artifacts on disk.

Found 2026-08-16 while re-verifying documented hashes (this was NOT in the pre-smoke re-audit
report): FROZEN_MD_ANALYSIS_PROTOCOL.json recorded

    source_hashes.pocket_definition_sha256 = 81281e85...

while the tracked pockets/final_consensus_1w60_20260815.json hashes to e88a53b0... . The
mismatch predates b4d9d7c. Nothing verified the field, so it drifted silently. The pocket
CONTENT was checked against the frozen August three-seed consensus and is correct; only the
bookkeeping pointer was stale. These tests make both the digest and the residue sets
enforceable so a substitution cannot go unnoticed again.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
MD = ROOT / "md_validation_4070"
PROTOCOL = MD / "FROZEN_MD_ANALYSIS_PROTOCOL.json"
POCKET = MD / "pockets" / "final_consensus_1w60_20260815.json"
STATIC_REF = MD / "static_reference_analysis.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.fixture(scope="module")
def protocol():
    return json.loads(PROTOCOL.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def pocket():
    return json.loads(POCKET.read_text(encoding="utf-8"))


# --------------------------------------------------------------------------------------
# Hash bindings
# --------------------------------------------------------------------------------------
def test_protocol_sha256_file_matches_the_protocol():
    recorded = (MD / "FROZEN_MD_ANALYSIS_PROTOCOL.sha256").read_text().split()[0]
    assert recorded == sha256(PROTOCOL)


def test_md_workflow_expects_the_actual_protocol_hash():
    import importlib.util
    import sys
    spec = importlib.util.spec_from_file_location("mw_prov", MD / "md_workflow.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["mw_prov"] = mod
    spec.loader.exec_module(mod)
    assert mod.EXPECTED_ANALYSIS_PROTOCOL_SHA256 == sha256(PROTOCOL)
    ok, why = mod.protocol_ok()
    assert ok, why


def test_pocket_definition_hash_binding(protocol):
    """The exact drift that went unnoticed until 2026-08-16."""
    assert protocol["source_hashes"]["pocket_definition_sha256"] == sha256(POCKET), (
        "FROZEN_MD_ANALYSIS_PROTOCOL.json no longer points at the tracked pocket definition")


def test_static_reference_hash_binding(protocol):
    assert protocol["source_hashes"]["static_reference_metrics_sha256"] == sha256(STATIC_REF)


def test_the_previous_stale_value_is_preserved_not_erased(protocol):
    assert protocol["source_hashes"]["pocket_definition_sha256_stale_value_before_2026_08_16"] == \
        "81281e852785fa51165fd3d0a0c7486a2a232cab2611a071607050368d8019c3"
    assert protocol["source_hashes"]["pocket_definition_hash_correction_note"]


# --------------------------------------------------------------------------------------
# The frozen candidate itself must be untouched
# --------------------------------------------------------------------------------------
FROZEN_CORE_3OF3 = [25, 26, 38, 39, 40, 41, 42, 44, 45, 46, 47]
FROZEN_SUPPORTED_GE2OF3 = [25, 26, 27, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 232, 233, 234]
FROZEN_FRINGE_1OF3 = [231, 250, 251, 252]
FROZEN_MEAN_JACCARD = 0.6791537667698658


def _ids(items):
    return sorted(int(x["resid"]) if isinstance(x, dict) else int(x) for x in items or [])


def test_pocket_residue_sets_are_the_frozen_august_consensus(pocket):
    assert _ids(pocket["core_3of3"]) == FROZEN_CORE_3OF3
    assert sorted(pocket["pocket_residues_resseq"]) == FROZEN_SUPPORTED_GE2OF3
    assert _ids(pocket["uncertain_fringe_1of3"]) == FROZEN_FRINGE_1OF3
    union = set(pocket["pocket_residues_resseq"]) | set(_ids(pocket["uncertain_fringe_1of3"]))
    assert len(union) == 20


def test_protocol_residue_sets_agree_with_the_pocket(protocol):
    rs = protocol["residue_sets"]
    assert _ids(rs["core_3of3"]) == FROZEN_CORE_3OF3
    assert _ids(rs["supported_ge2of3_primary"]) == FROZEN_SUPPORTED_GE2OF3
    assert _ids(rs["seed_specific_uncertain_fringe_1of3_exploratory"]) == FROZEN_FRINGE_1OF3


def test_frozen_jaccard_and_structures_unchanged(protocol):
    assert protocol["gnn_interpretation"]["literal_mean_jaccard"] == FROZEN_MEAN_JACCARD
    assert protocol["reference_structures"]["apo"]["pdb"] == "1W60"
    assert protocol["reference_structures"]["positive_control"]["pdb"] == "8GLA"


def test_openness_thresholds_are_unchanged_by_the_gate_repair(protocol):
    """The gate-v2 revision must not have moved any openness threshold."""
    assert protocol["metrics"]["openness"]["thresholds"] == {
        "core_sasa_A2": 501.317,
        "supported_sasa_A2": 808.568,
        "supported_ca_convex_hull_volume_A3": 560.687,
    }
    static = json.loads(STATIC_REF.read_text())
    assert static["reference_midpoint_thresholds"] == \
        protocol["metrics"]["openness"]["thresholds"]


def test_gate_v2_is_frozen_and_documents_its_supersession(protocol):
    gate = protocol["control_interpretability_gate"]
    assert gate["name"] == "trajectory_dynamic_control_gate_v2"
    assert gate["frozen_before_meaningful_control_md"] is True
    assert gate["rejects_static_structure_plus_per_frame_noise"] is True
    assert gate["supersedes"] == "trajectory_dynamic_control_gate_v1"
    assert gate["supersede_reason"]
    d = gate["dynamic_discriminators"]
    assert d["k_sigma"] == 3.0
    assert "analytic" in d["threshold_derivation"].lower()
    assert "not derived from" in d["threshold_derivation"].lower()


def test_no_control5_or_production_results_existed_when_the_gate_was_frozen():
    """The v2 thresholds cannot have been tuned on outcomes that do not exist."""
    outputs = MD / "outputs"
    if not outputs.exists():
        return
    for pdb in ("8GLA", "1W60"):
        for done in (outputs / pdb).glob("rep*/DONE.json"):
            payload = json.loads(done.read_text())
            assert float(payload.get("production_ns", 0.0)) < 1.0, (
                f"{done} contains a >=1 ns result; the gate must be re-frozen only "
                "before meaningful control MD exists")
