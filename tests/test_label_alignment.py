"""Tests for label alignment and residue distance logic."""
import numpy as np
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.data_processing.parse_pdb import Residue, label_pocket_residues


def _make_residue(ca_coord):
    return Residue(
        chain="A", resid=1, resname="ALA",
        ca_coord=np.array(ca_coord, dtype=np.float32),
        b_factor=20.0, secondary_structure="C", sasa=50.0,
    )


def test_residue_within_cutoff_labeled():
    residues = [_make_residue([0, 0, 0])]
    ligand   = np.array([[3.0, 0, 0]], dtype=np.float32)
    labels   = label_pocket_residues(residues, ligand, cutoff_angstrom=6.0)
    assert labels[0] == 1.0, "Residue 3 Å from ligand should be labeled within 6 Å cutoff"


def test_residue_outside_cutoff_unlabeled():
    residues = [_make_residue([0, 0, 0])]
    ligand   = np.array([[10.0, 0, 0]], dtype=np.float32)
    labels   = label_pocket_residues(residues, ligand, cutoff_angstrom=6.0)
    assert labels[0] == 0.0, "Residue 10 Å from ligand should not be labeled within 6 Å cutoff"


def test_multiple_residues_mixed():
    residues = [
        _make_residue([0, 0, 0]),   # 3 Å away — should be labeled
        _make_residue([8, 0, 0]),   # 8 Å away — should NOT be labeled
        _make_residue([5, 0, 0]),   # 5 Å away — should be labeled
    ]
    ligand = np.array([[3.0, 0, 0]], dtype=np.float32)
    labels = label_pocket_residues(residues, ligand, cutoff_angstrom=6.0)
    assert labels[0] == 1.0
    assert labels[1] == 0.0
    assert labels[2] == 1.0


def test_empty_residues():
    labels = label_pocket_residues([], np.zeros((1, 3), dtype=np.float32))
    assert len(labels) == 0


def test_multiple_ligand_atoms_any_within():
    residues = [_make_residue([0, 0, 0])]
    # One atom far, one atom close — residue should be labeled
    ligand = np.array([[20.0, 0, 0], [2.0, 0, 0]], dtype=np.float32)
    labels = label_pocket_residues(residues, ligand, cutoff_angstrom=6.0)
    assert labels[0] == 1.0
