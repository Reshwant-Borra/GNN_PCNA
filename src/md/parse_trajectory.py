"""
MD trajectory analysis: RMSF, DCCM, pocket volume tracking.
Uses MDAnalysis as primary library.
"""
from __future__ import annotations
import numpy as np
import MDAnalysis as mda
from MDAnalysis.analysis import rms, align


def load_trajectory(topology: str, trajectory: str) -> mda.Universe:
    """Load MD trajectory. topology: .gro/.psf, trajectory: .xtc/.dcd"""
    return mda.Universe(topology, trajectory)


def compute_rmsf(
    u: mda.Universe,
    selection: str = 'backbone',
    align_first: bool = True,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Compute per-residue RMSF over the trajectory.

    Returns:
        residue_ids  : (N,) int array of residue sequence numbers
        rmsf_values  : (N,) float array in Å
    """
    if align_first:
        align.AlignTraj(u, u, select=selection, in_memory=True).run()

    ca_atoms = u.select_atoms('name CA')
    rmsf_calc = rms.RMSF(ca_atoms).run()
    return ca_atoms.resids.copy(), rmsf_calc.rmsf.copy()


def compute_dccm(
    u: mda.Universe,
    selection: str = 'name CA',
) -> np.ndarray:
    """
    Compute Dynamic Cross-Correlation Matrix.

    Returns:
        dccm : (N, N) float array, values in [-1, 1]
               C_ij = <Δr_i·Δr_j> / sqrt(<|Δr_i|²><|Δr_j|²>)
    """
    ca = u.select_atoms(selection)
    N = len(ca)
    n_frames = len(u.trajectory)

    positions = np.zeros((n_frames, N, 3), dtype=np.float32)
    for i, _ in enumerate(u.trajectory):
        positions[i] = ca.positions

    mean_pos = positions.mean(axis=0)        # (N, 3)
    delta    = positions - mean_pos          # (T, N, 3)

    # C_ij = (1/T) Σ_t Δr_i(t)·Δr_j(t)
    corr = np.einsum('tia,tja->ij', delta, delta) / n_frames   # (N, N)

    var  = np.diag(corr)                            # (N,)
    norm = np.sqrt(np.outer(var, var))              # (N, N)
    dccm = corr / np.where(norm > 1e-10, norm, 1e-10)
    return np.clip(dccm, -1.0, 1.0)


def track_pocket_volume(
    trajectory_path: str,
    topology_path: str,
    pocket_residue_ids: list[int],
) -> np.ndarray:
    """
    Estimate pocket volume at each trajectory frame using convex hull of Cα coords.
    Rough proxy — use MDpocket for production quality.

    Returns:
        volumes : (T,) float array in Å³
    """
    from scipy.spatial import ConvexHull

    u = mda.Universe(topology_path, trajectory_path)
    resid_sel = ' or '.join(f'resid {r}' for r in pocket_residue_ids)
    pocket_ca = u.select_atoms(f'({resid_sel}) and name CA')

    volumes: list[float] = []
    for _ in u.trajectory:
        pos = pocket_ca.positions
        if len(pos) >= 4:
            try:
                volumes.append(float(ConvexHull(pos).volume))
            except Exception:
                volumes.append(0.0)
        else:
            volumes.append(0.0)
    return np.array(volumes, dtype=np.float32)


def summarize_md_validation(
    rmsf_values: np.ndarray,
    pocket_residue_ids: list[int],
    dccm: np.ndarray,
    volumes: np.ndarray,
) -> dict:
    """
    Aggregate MD evidence for a predicted pocket.

    Returns dict with:
        mean_rmsf, background_rmsf, rmsf_ratio,
        mean_internal_dccm, max_volume, fraction_open_frames
    """
    ids = np.array(pocket_residue_ids)
    pocket_rmsf     = rmsf_values[ids]
    all_idx         = np.arange(len(rmsf_values))
    bg_idx          = np.setdiff1d(all_idx, ids)
    background_rmsf = rmsf_values[bg_idx].mean() if len(bg_idx) > 0 else 1e-6

    if len(ids) > 1:
        sub = dccm[np.ix_(ids, ids)]
        off_diag = sub[~np.eye(len(ids), dtype=bool)]
        mean_internal_dccm = float(np.abs(off_diag).mean())
    else:
        mean_internal_dccm = float('nan')

    max_volume        = float(volumes.max()) if len(volumes) > 0 else 0.0
    fraction_open     = float((volumes > 100.0).mean()) if len(volumes) > 0 else 0.0

    return {
        'mean_rmsf':          float(pocket_rmsf.mean()),
        'background_rmsf':    float(background_rmsf),
        'rmsf_ratio':         float(pocket_rmsf.mean() / max(background_rmsf, 1e-6)),
        'mean_internal_dccm': mean_internal_dccm,
        'max_volume':         max_volume,
        'fraction_open_frames': fraction_open,
    }
