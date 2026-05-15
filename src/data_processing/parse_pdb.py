"""
Parse PDB files into cleaned residue-level records.
Strips waters/HETATM (except target ligand), standardizes chain IDs.
"""
from __future__ import annotations
from pathlib import Path
from dataclasses import dataclass
import numpy as np

try:
    from Bio.PDB import PDBParser
    from Bio.PDB.SASA import ShrakeRupley
    _BIOPYTHON = True
except ImportError:
    _BIOPYTHON = False

_STANDARD_AA = {
    'ALA', 'ARG', 'ASN', 'ASP', 'CYS', 'GLN', 'GLU', 'GLY',
    'HIS', 'ILE', 'LEU', 'LYS', 'MET', 'PHE', 'PRO',
    'SER', 'THR', 'TRP', 'TYR', 'VAL',
}

# Common crystallographic additives to ignore when looking for drug-like ligands
_SKIP_RESNAMES = {
    'HOH', 'WAT', 'SO4', 'EDO', 'PEG', 'GOL', 'DMS', 'PO4', 'MPD',
    'FMT', 'ACT', 'MES', 'HED', 'BME', 'DTT', 'EPE', 'NHE', 'IMD',
    'CIT', 'TRS', 'FLC', 'SCN', 'AZI', 'MLI', 'IOD', 'NO3', 'PGE',
    'PE5', 'PE7', 'NH4', 'ACE', 'MSE', 'SEP', 'TPO', 'PTR',
    'MG', 'CA', 'ZN', 'MN', 'FE', 'CU', 'NA', 'K', 'CD',
    'AU', 'PT', 'CO', 'NI', 'HG', 'SE', 'BR', 'CL',
}


@dataclass
class Residue:
    chain: str
    resid: int
    resname: str
    ca_coord: np.ndarray   # shape (3,)
    b_factor: float
    secondary_structure: str   # 'H', 'E', 'C'
    sasa: float                # Å²


def _parse_secondary_structure(pdb_path: Path) -> dict[tuple[str, int], str]:
    """Parse HELIX/SHEET records from PDB header → {(chain, resid): 'H'|'E'}."""
    ss: dict[tuple[str, int], str] = {}
    for line in pdb_path.read_text(errors='ignore').splitlines():
        rec = line[:6].strip()
        try:
            if rec == 'HELIX' and len(line) >= 37:
                chain = line[19]
                for r in range(int(line[21:25]), int(line[33:37]) + 1):
                    ss[(chain, r)] = 'H'
            elif rec == 'SHEET' and len(line) >= 37:
                chain = line[21]
                for r in range(int(line[22:26]), int(line[33:37]) + 1):
                    ss[(chain, r)] = 'E'
        except ValueError:
            pass
    return ss


def parse_pdb(pdb_path: Path, keep_ligand: str | None = None) -> list[Residue]:
    """Load a PDB and return one Residue per standard amino acid residue."""
    if not _BIOPYTHON:
        raise ImportError("biopython required: pip install biopython")

    parser = PDBParser(QUIET=True)
    structure = parser.get_structure("X", str(pdb_path))
    model = structure[0]

    # Per-residue SASA
    sasa_map: dict[tuple[str, int], float] = {}
    try:
        sr = ShrakeRupley()
        sr.compute(structure, level="R")
        for chain in model:
            for res in chain:
                if res.get_id()[0] == ' ' and hasattr(res, 'sasa'):
                    sasa_map[(chain.get_id(), res.get_id()[1])] = float(res.sasa)
    except Exception:
        pass

    ss_map = _parse_secondary_structure(pdb_path)
    residues: list[Residue] = []

    for chain in model:
        for res in chain:
            if res.get_id()[0] != ' ':   # skip HETATM / water
                continue
            if not res.has_id('CA'):
                continue
            resname = res.get_resname().strip()
            if resname not in _STANDARD_AA:
                continue
            ca = res['CA']
            chain_id = chain.get_id()
            resid = res.get_id()[1]
            key = (chain_id, resid)
            residues.append(Residue(
                chain=chain_id,
                resid=resid,
                resname=resname,
                ca_coord=np.array(ca.get_vector().get_array(), dtype=np.float32),
                b_factor=float(ca.get_bfactor()),
                secondary_structure=ss_map.get(key, 'C'),
                sasa=sasa_map.get(key, 0.0),
            ))
    return residues


def get_ligand_coords(pdb_path: Path, resname: str | None = None) -> np.ndarray | None:
    """
    Extract 3D coordinates of a ligand from HETATM records.

    If resname is given, returns coords of atoms with that residue name.
    Otherwise, finds the first non-solvent, non-ion HETATM residue.

    Returns:
        (L, 3) float32 array of atom positions, or None if not found.
    """
    coords: list[list[float]] = []
    found_resname: str | None = None

    for line in pdb_path.read_text(errors='ignore').splitlines():
        if not line.startswith('HETATM'):
            continue
        rn = line[17:20].strip()
        if resname:
            if rn != resname:
                continue
        else:
            if rn in _SKIP_RESNAMES:
                continue
            if found_resname is None:
                found_resname = rn
            elif rn != found_resname:
                continue   # only take the first ligand residue found
        try:
            x = float(line[30:38])
            y = float(line[38:46])
            z = float(line[46:54])
            coords.append([x, y, z])
        except (ValueError, IndexError):
            pass

    if not coords:
        return None
    return np.array(coords, dtype=np.float32)


def strip_heteroatoms(pdb_path: Path, output_path: Path,
                      keep_resname: str | None = None) -> None:
    """Write a cleaned PDB: no waters, no HETATM except keep_resname."""
    kept: list[str] = []
    for line in pdb_path.read_text(errors='ignore').splitlines(keepends=True):
        rec = line[:6].strip()
        if rec == 'ATOM':
            kept.append(line)
        elif rec == 'HETATM':
            rn = line[17:20].strip()
            if rn == 'HOH':
                continue
            if keep_resname and rn == keep_resname:
                kept.append(line)
        elif rec in ('HEADER', 'TITLE', 'REMARK', 'SEQRES', 'CRYST1',
                     'ORIGX1', 'ORIGX2', 'ORIGX3', 'SCALE1', 'SCALE2',
                     'SCALE3', 'HELIX', 'SHEET', 'TER', 'END'):
            kept.append(line)
    output_path.write_text(''.join(kept))


def standardize_chains(residues: list[Residue]) -> list[Residue]:
    """Rename chains to canonical A/B/C for PCNA homotrimer."""
    unique_chains = sorted({r.chain for r in residues})
    if len(unique_chains) <= 3:
        remap = {old: new for old, new in zip(unique_chains, 'ABC')}
    else:
        remap = {c: c for c in unique_chains}
    for r in residues:
        r.chain = remap.get(r.chain, r.chain)
    return residues


def label_pocket_residues(
    residues: list[Residue],
    ligand_coords: np.ndarray,   # (L, 3)
    cutoff_angstrom: float = 6.0,
) -> np.ndarray:
    """Return binary label array (N,) — 1 if residue Cα within cutoff of any ligand atom."""
    ca_coords = np.stack([r.ca_coord for r in residues])   # (N, 3)
    dists = np.linalg.norm(
        ca_coords[:, None, :] - ligand_coords[None, :, :], axis=-1
    )   # (N, L)
    return (dists.min(axis=1) <= cutoff_angstrom).astype(np.float32)
