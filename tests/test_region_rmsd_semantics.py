"""Region RMSD must mean what the emitted metadata says it means.

Reproduced 2026-08-16 against b4d9d7c: the production path computed

    local_rmsd = md.rmsd(protein, protein, 0, atom_indices=region_ca)

while summary.json's rmsd_protocol declared

    "local_region_rmsd": {"measurement_selection": "region CA after scaffold alignment"}

mdtraj's rmsd RE-SUPERPOSES on atom_indices, so the scaffold transformation is discarded and
only internal deformation survives. A region rigidly displaced 0.5 nm against a fixed
scaffold was reported as 0.000 nm -- i.e. "the pocket did not move".

These tests drive the real analyze_replicate() over real DCD files, not helper functions.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
MD = ROOT / "md_validation_4070"
sys.path.insert(0, str(ROOT / "tests"))

import md_synthetic as syn  # noqa: E402


def _load():
    spec = importlib.util.spec_from_file_location("analyze_md_rmsd", MD / "analyze_md.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["analyze_md_rmsd"] = mod
    spec.loader.exec_module(mod)
    return mod


an = _load()
REGIONS = {"core_3of3": syn.CORE_RESSEQ, "supported_ge2of3": syn.POCKET_RESSEQ}
DISPLACEMENT_NM = 0.5


def _run(tmp_path, mode):
    traj = syn.make_rmsd_trajectory(mode, displacement_nm=DISPLACEMENT_NM)
    rep = syn.write_replicate(tmp_path / mode, "8GLA", "rep01", traj)
    done = json.loads((rep / "DONE.json").read_text())
    return an.analyze_replicate(
        rep / "production.dcd", tmp_path / mode / "8GLA" / "system_solvated.pdb",
        syn.POCKET_RESSEQ, [0], regions=REGIONS,
        thresholds={"supported_sasa_A2": 0.0, "supported_ca_convex_hull_volume_A3": 0.0},
        done_payload=done)


def test_1_whole_protein_rigid_transform_gives_zero_rmsd(tmp_path):
    """Pure rigid translation + rotation of the whole protein: everything must read ~0."""
    r = _run(tmp_path, "rigid_global")
    region = r["regions"]["supported_ge2of3"]
    assert r["rmsd_max_nm"] == pytest.approx(0.0, abs=1e-3), \
        "scaffold-aligned global RMSD must remove a whole-protein rigid transform"
    assert region["region_rmsd_scaffold_aligned_max_nm"] == pytest.approx(0.0, abs=1e-3), \
        "a rigid transform of the whole protein must not appear as region motion"
    assert region["region_internal_rmsd_max_nm"] == pytest.approx(0.0, abs=1e-3)


def test_2_region_displaced_relative_to_scaffold_reads_the_true_displacement(tmp_path):
    """Region rigidly displaced 0.5 nm against a fixed scaffold -> 0.5 nm, not 0."""
    r = _run(tmp_path, "region_displaced")
    region = r["regions"]["supported_ge2of3"]

    assert region["region_rmsd_scaffold_aligned_max_nm"] == pytest.approx(
        DISPLACEMENT_NM, abs=0.02), (
        "region RMSD after scaffold alignment must retain displacement relative to the "
        f"scaffold; got {region['region_rmsd_scaffold_aligned_max_nm']}")

    # And the separately named internal metric must, correctly, be ~0: a RIGID displacement
    # involves no internal deformation. This is the quantity the old code reported under the
    # scaffold-aligned label.
    assert region["region_internal_rmsd_max_nm"] == pytest.approx(0.0, abs=1e-3), (
        "region-internal RMSD must exclude rigid displacement by construction")


def test_3_region_internal_deformation_is_nonzero(tmp_path):
    """A genuine internal deformation must be visible in BOTH region metrics."""
    r = _run(tmp_path, "region_deformed")
    region = r["regions"]["supported_ge2of3"]
    assert region["region_internal_rmsd_max_nm"] > 0.05, \
        "internal deformation must register in the region-internal RMSD"
    assert region["region_rmsd_scaffold_aligned_max_nm"] > 0.05, \
        "internal deformation must also register after scaffold alignment"


def test_units_are_nanometres(tmp_path):
    """The 0.5 nm displacement must read 0.5, not 5 (Angstrom) and not 0.0005 (metres)."""
    r = _run(tmp_path, "region_displaced")
    v = r["regions"]["supported_ge2of3"]["region_rmsd_scaffold_aligned_max_nm"]
    assert 0.45 < v < 0.55, f"expected nm units near 0.5, got {v}"


def test_metadata_matches_the_implementation():
    """summary.json's rmsd_protocol must describe what the code actually computes."""
    src = (MD / "analyze_md.py").read_text(encoding="utf-8")
    assert "region_rmsd_scaffold_aligned" in src
    assert "region_internal_rmsd" in src
    # the misleading single field name must be gone from the production output
    assert '"local_rmsd_mean_nm"' not in src
    assert '"local_region_rmsd"' not in src


def test_old_behaviour_is_genuinely_different(tmp_path):
    """Witness that the pre-repair implementation really did report 0 for case 2."""
    import mdtraj as md
    import numpy as np

    traj = syn.make_rmsd_trajectory("region_displaced", displacement_nm=DISPLACEMENT_NM)
    top, _ = syn.build_topology()
    want = set(syn.POCKET_RESSEQ)
    region_ca = [a.index for a in traj.top.atoms
                 if a.residue.chain.index == 0 and a.residue.resSeq in want and a.name == "CA"]
    old = md.rmsd(traj, traj, 0, atom_indices=np.array(region_ca))
    assert float(old.max()) == pytest.approx(0.0, abs=1e-3), (
        "the pre-repair metric must be shown to report ~0 for a 0.5 nm rigid region "
        "displacement -- that is the defect being fixed")
