from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from phase5_md.wave1 import (
    AUTHORIZED_SYSTEMS,
    AUTHORIZED_WINDOWS,
    Phase5PreflightError,
    audit_1axc,
    audit_8gla,
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
    assert "Audited ZQZ ligand parameter manifest is absent" in message
