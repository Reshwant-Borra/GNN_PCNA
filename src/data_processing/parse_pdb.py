"""
Parse PDB files into cleaned residue-level records.
Strips waters/HETATM (except target ligand), standardizes chain IDs.
"""
from __future__ import annotations
from pathlib import Path
from dataclasses import dataclass
import numpy as np


@dataclass
class Residue:
    chain: str
    resid: int
    resname: str       # 3-letter code
    ca_coord: np.ndarray   # shape (3,)
    b_factor: float
    secondary_structure: str   # 'H', 'E', 'C'
    sasa: float        # Å²


def parse_pdb(pdb_path: Path, keep_ligand: str | None = None) -> list[Residue]:
    """Load a PDB and return one Residue per standard amino acid residue."""
    raise NotImplementedError


def strip_heteroatoms(pdb_path: Path, output_path: Path, keep_resname: str | None = None) -> None:
    """Write a cleaned PDB: no waters, no HETATM except keep_resname."""
    raise NotImplementedError


def standardize_chains(residues: list[Residue]) -> list[Residue]:
    """Rename chains to canonical A/B/C for PCNA homotrimer."""
    raise NotImplementedError


def label_pocket_residues(
    residues: list[Residue],
    ligand_coords: np.ndarray,   # shape (L, 3)
    cutoff_angstrom: float = 6.0,
) -> np.ndarray:
    """Return binary label array (N,) — 1 if residue Cα within cutoff of any ligand atom."""
    raise NotImplementedError
