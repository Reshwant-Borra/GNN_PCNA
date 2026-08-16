from __future__ import annotations

import sys
from pathlib import Path

import pytest


np = pytest.importorskip("numpy")
REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "md_validation_4070"))

import analyze_md


def test_kabsch_rigid_body_transformation_zero_rmsd():
    ref = np.array(
        [
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
        ]
    )
    theta = np.pi / 3
    rot = np.array(
        [
            [np.cos(theta), -np.sin(theta), 0.0],
            [np.sin(theta), np.cos(theta), 0.0],
            [0.0, 0.0, 1.0],
        ]
    )
    mobile = ref @ rot.T + np.array([10.0, -3.0, 2.0])
    assert analyze_md.kabsch_rmsd_nm(mobile, ref) < 1e-12


def test_local_perturbation_after_alignment_is_detected():
    ref = np.array(
        [
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
        ]
    )
    mobile = ref.copy()
    mobile[3] += np.array([0.5, 0.0, 0.0])
    scaffold_rmsd = analyze_md.kabsch_rmsd_nm(mobile[:3], ref[:3])
    local_rmsd = analyze_md.kabsch_rmsd_nm(mobile[[0, 1, 3]], ref[[0, 1, 3]])
    assert scaffold_rmsd < 1e-12
    assert local_rmsd > 0.1
