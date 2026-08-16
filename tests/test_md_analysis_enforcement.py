from __future__ import annotations

import json
import math
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "md_validation_4070"))

import analyze_md


def _write_complete_rep(rep: Path, *, frames: int = 2, failed: bool = False) -> None:
    rep.mkdir(parents=True)
    (rep.parent / "system_solvated.pdb").write_text("MODEL\nEND\n", encoding="utf-8")
    (rep / "production.dcd").write_bytes(b"not-a-real-dcd-but-done-carries-count")
    done = {
        "replicate": 1,
        "pdb": "8GLA",
        "role": "control",
        "ns": 0.1,
        "production_ns": 0.1,
        "equil_ns": 2.0,
        "report_ps": 50.0,
        "timestep_fs": 4.0,
        "steps": 525000,
        "target_total_steps": 525000,
        "sanity_gate": "passed: finite energy+coords",
        "topology": "system_solvated.pdb",
        "trajectory": "production.dcd",
        "dcd_frames": frames,
    }
    (rep / "DONE.json").write_text(json.dumps(done), encoding="utf-8")
    prov = {
        "structure_pdb_id": "8GLA",
        "role": "control",
        "input_hashes": {"frozen_analysis_protocol_sha256": "abc"},
    }
    (rep / "PROVENANCE.json").write_text(json.dumps(prov), encoding="utf-8")
    (rep / "production.log").write_text("#Step\tTime (ps)\n1\t50\n2\t100\n", encoding="utf-8")
    if failed:
        (rep / "FAILED.json").write_text('{"reason":"boom"}', encoding="utf-8")


def test_complete_run_passes_completion_validation(tmp_path):
    rep = tmp_path / "8GLA" / "rep01"
    _write_complete_rep(rep)
    result = analyze_md.validate_scientific_replicate(rep, "8GLA", "control", 0.1)
    assert result["ok"], result
    assert result["expected_frames"] == 2


def test_missing_done_fails_completion_validation(tmp_path):
    rep = tmp_path / "8GLA" / "rep01"
    rep.mkdir(parents=True)
    result = analyze_md.validate_scientific_replicate(rep, "8GLA", "control", 0.1)
    assert not result["ok"]
    assert "DONE.json missing" in result["issues"]


def test_truncated_frames_fail_completion_validation(tmp_path):
    rep = tmp_path / "8GLA" / "rep01"
    _write_complete_rep(rep, frames=1)
    result = analyze_md.validate_scientific_replicate(rep, "8GLA", "control", 0.1)
    assert not result["ok"]
    assert any("trajectory truncated" in issue for issue in result["issues"])


def test_failed_json_fails_completion_validation(tmp_path):
    rep = tmp_path / "8GLA" / "rep01"
    _write_complete_rep(rep, failed=True)
    result = analyze_md.validate_scientific_replicate(rep, "8GLA", "control", 0.1)
    assert not result["ok"]
    assert "FAILED.json present" in result["issues"]


def test_duplicate_frames_fail_completion_validation(tmp_path):
    rep = tmp_path / "8GLA" / "rep01"
    _write_complete_rep(rep, frames=3)
    result = analyze_md.validate_scientific_replicate(rep, "8GLA", "control", 0.1)
    assert not result["ok"]
    assert any("duplicate frame risk" in issue for issue in result["issues"])


def test_diagnostic_override_marker_constant_is_unambiguous():
    assert analyze_md.DIAGNOSTIC_MARK == "DIAGNOSTIC_ONLY - NOT_FOR_SCIENTIFIC_INTERPRETATION"


def test_stationary_series_converges_and_drifting_series_does_not():
    stationary = [1.0 + 0.01 * math.sin(i) for i in range(90)]
    drifting = [1.0 + 0.02 * i for i in range(90)]
    assert analyze_md.assess_convergence(stationary)["status"] == "STABLE_BLOCKS"
    assert analyze_md.assess_convergence(drifting)["status"] == "DRIFTING_BLOCKS"


def test_replica_aggregation_keeps_replicates_identifiable():
    rows = [
        {"role": "control", "replicate": "rep01", "completion_status": "PASS",
         "openness": {"open_like_fraction": 0.2}, "convergence": {"overall_status": "STABLE_BLOCKS"}},
        {"role": "control", "replicate": "rep02", "completion_status": "PASS",
         "openness": {"open_like_fraction": 0.4}, "convergence": {"overall_status": "STABLE_BLOCKS"}},
        {"role": "control", "replicate": "rep03", "completion_status": "PASS",
         "openness": {"open_like_fraction": 0.6}, "convergence": {"overall_status": "STABLE_BLOCKS"}},
    ]
    agg = analyze_md.aggregate_replicates(rows)["control"]
    assert agg["independent_unit"] == "replicate"
    assert agg["support_count"] == 3
    assert agg["mean"] == 0.4
    assert [x["replicate"] for x in agg["per_replicate"]] == ["rep01", "rep02", "rep03"]
