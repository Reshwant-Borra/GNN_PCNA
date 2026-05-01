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
        residue_ids  : (N,) int array
        rmsf_values  : (N,) float array in Å
    """
    raise NotImplementedError


def compute_dccm(
    u: mda.Universe,
    selection: str = 'name CA',
) -> np.ndarray:
    """
    Compute Dynamic Cross-Correlation Matrix.

    Returns:
        dccm : (N, N) float array, values in [-1, 1]
    """
    raise NotImplementedError


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
    raise NotImplementedError


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
    raise NotImplementedError
