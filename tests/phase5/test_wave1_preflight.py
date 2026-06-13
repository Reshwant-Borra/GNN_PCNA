from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from phase5_md.wave1 import (
    APPROVED_WAVE1_POLICY,
    AUTHORIZED_SYSTEMS,
    AUTHORIZED_WINDOWS,
    FORCE_FIELD_WATER_DECISION,
    Phase5PreflightError,
    ZQZ_CHEMISTRY_DECISION,
    ZQZ_NEUTRAL_SUPERSEDED_MARKER,
    audit_1axc,
    audit_8gla,
    audit_zqz_parameters,
    build_registry,
    decision_record_status,
    verify_preflight,
)


def test_authorized_wave1_scope_matches_package():
    assert set(AUTHORIZED_SYSTEMS) == {
        "8gla_holo_zqz",
        "8gla_apo_from_holo",
        "1axc_apo_from_p21",
    }
    assert {
        (spec["residues"][0], spec["residues"][-1])
        for spec in AUTHORIZED_WINDOWS.values()
    } == {
        (118, 122),
        (239, 243),
        (28, 32),
        (206, 210),
        (134, 138),
    }


def test_1axc_audit_identifies_pcna_and_p21_chains_and_complete_windows():
    audit = audit_1axc()
    mapping = audit["chain_mapping"]
    assert mapping["pcna_auth_chains"] == ["A", "C", "E"]
    assert mapping["p21_peptide_auth_chains_to_remove"] == ["B", "D", "F"]
    for details in audit["candidate_window_presence"].values():
        assert details["complete_all_chains"]


def test_8gla_audit_records_assembly1_and_chain_c_pc118_caveat():
    audit = audit_8gla()
    assert audit["biological_assembly"]["official_assembly_for_wave1"] == "1"
    assert audit["biological_assembly"]["wave1_pcna_auth_chains"] == ["A", "B", "C"]
    chain_c = audit["candidate_window_presence"]["PC-118"]["chains"]["C"]
    assert chain_c["missing"] == [122]
    assert audit["zqz"]["formal_charge"] == 0


def test_production_preflight_fails_closed_without_launch_and_zqz_audit():
    with pytest.raises(Phase5PreflightError) as excinfo:
        verify_preflight(stage="production")
    message = str(excinfo.value)
    assert "do_not_run_md: true" in message
    assert "Future explicit Phase 5 launch authorization record is absent" in message
    assert "Audited ZQZ ligand parameter package is absent or incomplete" not in message


def test_zqz_parameter_audit_is_complete_and_ligand_only():
    audit = audit_zqz_parameters()
    assert audit["complete"]
    assert audit["status"] == "PARAMETERS_AUDITED_READY_FOR_SETUP_USE"
    assert audit["active_package_dir"].endswith("zqz_minus1")
    assert Path(ROOT / audit["neutral_superseded_marker"]).exists()
    assert audit["method"]["force_field"] == "GAFF2"
    assert audit["method"]["charge_model"] == "AM1-BCC"
    assert audit["method"]["net_charge"] == -1
    assert audit["method"]["protonation_state"] == "deprotonated_sidechain_carboxylate"
    assert audit["key_hashes"]["zqz_minus1_gaff2_am1bcc.mol2"]
    assert audit["key_hashes"]["zqz_minus1_gaff2.frcmod"]
    assert ZQZ_NEUTRAL_SUPERSEDED_MARKER.exists()


def test_decision_records_exist_and_are_resolved():
    chem = decision_record_status(ZQZ_CHEMISTRY_DECISION)
    ff = decision_record_status(FORCE_FIELD_WATER_DECISION)
    assert chem["exists"]
    assert ff["exists"]
    assert chem["status"] == "APPROVED_HUMAN_REVIEW_RESOLVED"
    assert ff["status"] == "APPROVED_HUMAN_REVIEW_RESOLVED"
    assert not chem["is_open"]
    assert not ff["is_open"]


def test_production_preflight_only_blocks_on_launch_hold():
    with pytest.raises(Phase5PreflightError) as excinfo:
        verify_preflight(stage="production")
    message = str(excinfo.value)
    assert "do_not_run_md: true" in message
    assert "Future explicit Phase 5 launch authorization record is absent" in message
    assert "ZQZ protonation/net-charge decision record" not in message
    assert "Force-field/water-model policy decision record" not in message


def test_registry_records_approved_opc_policy_and_launch_hold():
    registry = build_registry()
    policy = registry["approved_wave1_policy"]
    assert policy == APPROVED_WAVE1_POLICY
    assert policy["water_model"] == "OPC"
    assert policy["ion_parameters"] == "Joung-Cheatham OPC-compatible ions"
    assert registry["launch_authorized"] is False
    assert registry["do_not_run_md"] is True
    assert registry["preflight_status"]["package_preparation_status"] == "LAUNCH_READY_AWAITING_AUTHORIZATION"
    assert registry["preflight_status"]["production_launch_status"] == "BLOCKED_FAIL_CLOSED"
