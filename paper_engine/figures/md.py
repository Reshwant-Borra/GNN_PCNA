"""Molecular-dynamics trajectory analysis and figures.

The production trajectory ``data/md/1W60_production.dcd`` is a fully solvated
system (~356k atoms). A DCD has no topology, so rigorous protein analysis needs
the matching solvated-system topology (the OpenMM starting PDB or a PSF with the
same atom count). This module:

  * discovers a topology whose atom count matches the trajectory,
  * if found, computes Cα RMSD(t), per-residue RMSF, radius of gyration, and the
    Cα dynamic cross-correlation matrix (DCCM), caching the derived series so the
    2.6 GB trajectory is parsed once,
  * if not found, raises :class:`MDUnavailable` with an actionable message so the
    renderer skips MD figures instead of fabricating them.

Drop the topology next to the trajectory (``data/md/*.psf`` / ``*.pdb`` with the
matching atom count) or set ``PAPER_ENGINE_MD_TOPOLOGY=/path/to/system.pdb``.
"""
from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import numpy as np

from paper_engine import config
from paper_engine.figures import style
from paper_engine.figures.figure_specs import MD_FIGURE_SPECS

style.set_style()
import matplotlib.pyplot as plt  # noqa: E402


class MDUnavailable(RuntimeError):
    """Raised when the trajectory cannot be analysed (no matching topology)."""


@dataclass
class MDResults:
    times_ns: np.ndarray
    rmsd: np.ndarray
    rmsf_resids: np.ndarray
    rmsf: np.ndarray
    rgyr: np.ndarray
    dccm: np.ndarray
    dccm_resids: np.ndarray
    n_frames: int
    n_atoms: int
    dt_ps: float
    length_ns: float
    stride: int
    topology: str
    trajectory: str


# --------------------------------------------------------------------------- #
def _dcd_natoms(dcd_path: Path) -> int:
    from MDAnalysis.coordinates.DCD import DCDReader

    return DCDReader(str(dcd_path)).n_atoms


def discover_topology(dcd_path: Path) -> Optional[Path]:
    """Find a topology whose atom count matches the trajectory.

    Search order: env var, then data/md/, then the friend_sample dir.
    """
    import MDAnalysis as mda

    target = _dcd_natoms(dcd_path)
    candidates: List[Path] = []

    env = os.environ.get("PAPER_ENGINE_MD_TOPOLOGY")
    if env:
        candidates.append(Path(env))
    md_dir = dcd_path.parent
    for ext in ("*.psf", "*.pdb", "*.gro", "*.prmtop", "*.parm7", "*.cif"):
        candidates.extend(sorted(md_dir.glob(ext)))
    sample = config.SCIENCE_ROOT / "data" / "raw_intake" / "friend_sample"
    if sample.exists():
        candidates.extend(sorted(sample.glob("1W60*.pdb")))

    for cand in candidates:
        if not cand.exists():
            continue
        try:
            u = mda.Universe(str(cand))
            if u.atoms.n_atoms == target:
                return cand
        except Exception:
            continue
    return None


def _cache_path(dcd_path: Path, topology: Path, stride: int) -> Path:
    stat = dcd_path.stat()
    key = f"{dcd_path}|{stat.st_size}|{stat.st_mtime_ns}|{topology}|{stride}"
    digest = hashlib.sha256(key.encode()).hexdigest()[:16]
    return config.CACHE_DIR / f"md_{digest}.npz"


# --------------------------------------------------------------------------- #
def analyze(stride: int = 1, force: bool = False) -> MDResults:
    """Analyse the production trajectory. Cached after the first run."""
    dcd_path = config.find_data_file(*config.MD_TRAJECTORY)
    if dcd_path is None:
        raise MDUnavailable(
            "MD trajectory not found. Expected data/md/1W60_production.dcd."
        )
    topology = discover_topology(dcd_path)
    if topology is None:
        n = _dcd_natoms(dcd_path)
        raise MDUnavailable(
            "No topology matches the solvated trajectory "
            f"({n} atoms). Provide the OpenMM solvated-system PDB/PSF "
            "(same atom count) in data/md/ or set PAPER_ENGINE_MD_TOPOLOGY. "
            "The protein-only crystal 1W60.pdb does not match (it lacks "
            "hydrogens, water, and ions). MD figures are skipped until then."
        )

    config.ensure_output_dirs()
    cache = _cache_path(dcd_path, topology, stride)
    if cache.exists() and not force:
        data = np.load(cache, allow_pickle=False)
        return MDResults(
            times_ns=data["times_ns"], rmsd=data["rmsd"], rmsf_resids=data["rmsf_resids"],
            rmsf=data["rmsf"], rgyr=data["rgyr"], dccm=data["dccm"],
            dccm_resids=data["dccm_resids"], n_frames=int(data["n_frames"]),
            n_atoms=int(data["n_atoms"]), dt_ps=float(data["dt_ps"]),
            length_ns=float(data["length_ns"]), stride=int(data["stride"]),
            topology=str(topology), trajectory=str(dcd_path),
        )

    import MDAnalysis as mda
    from MDAnalysis.analysis import align, rms

    u = mda.Universe(str(topology), str(dcd_path))
    ca = u.select_atoms("protein and name CA")
    if ca.n_atoms == 0:
        raise MDUnavailable(
            f"Topology {topology.name} matched atom count but exposes no protein "
            "Cα atoms; a labelled topology (PSF or solvated PDB) is required."
        )

    dt_ps = float(getattr(u.trajectory, "dt", 0.0)) or 10.0
    n_frames = u.trajectory.n_frames

    # RMSD of Cα vs first frame.
    rmsd_run = rms.RMSD(u, select="protein and name CA", ref_frame=0).run(step=stride)
    rmsd_arr = rmsd_run.results.rmsd  # columns: frame, time, rmsd
    frames_used = rmsd_arr[:, 0].astype(int)
    rmsd = rmsd_arr[:, 2]
    times_ns = frames_used * dt_ps / 1000.0

    # Collect aligned Cα positions for RMSF + DCCM + Rg.
    average = align.AverageStructure(u, u, select="protein and name CA",
                                     ref_frame=0).run(step=stride)
    aligner = align.AlignTraj(u, average.results.universe,
                              select="protein and name CA", in_memory=True).run(step=stride)
    del aligner

    positions = []
    rgyr = []
    for ts in u.trajectory[::stride]:
        positions.append(ca.positions.copy())
        rgyr.append(ca.radius_of_gyration())
    P = np.asarray(positions)  # (F, N, 3)
    rgyr = np.asarray(rgyr)

    mean_pos = P.mean(axis=0)
    disp = P - mean_pos  # (F, N, 3)
    rmsf = np.sqrt((disp ** 2).sum(axis=2).mean(axis=0))  # (N,)
    resids = ca.resids

    # DCCM: C_ij = <dr_i . dr_j> / sqrt(<dr_i^2><dr_j^2>)
    F = P.shape[0]
    cov = np.einsum("fid,fjd->ij", disp, disp) / F
    diag = np.sqrt(np.clip(np.diag(cov), 1e-12, None))
    dccm = cov / np.outer(diag, diag)

    length_ns = float(times_ns.max()) if len(times_ns) else 0.0
    result = MDResults(
        times_ns=times_ns, rmsd=rmsd, rmsf_resids=resids.astype(float), rmsf=rmsf,
        rgyr=rgyr, dccm=dccm, dccm_resids=resids.astype(float), n_frames=int(n_frames),
        n_atoms=int(u.atoms.n_atoms), dt_ps=dt_ps, length_ns=length_ns,
        stride=int(stride), topology=str(topology), trajectory=str(dcd_path),
    )
    np.savez_compressed(
        cache, times_ns=times_ns, rmsd=rmsd, rmsf_resids=result.rmsf_resids, rmsf=rmsf,
        rgyr=rgyr, dccm=dccm, dccm_resids=result.dccm_resids, n_frames=n_frames,
        n_atoms=result.n_atoms, dt_ps=dt_ps, length_ns=length_ns, stride=stride,
    )
    return result


# --------------------------------------------------------------------------- #
# Figure builders (imported lazily by render to keep heavy deps optional)
# --------------------------------------------------------------------------- #
def _caption(figure_id: str, res: MDResults) -> str:
    return MD_FIGURE_SPECS[figure_id].caption.format(
        n_frames=res.n_frames, length_ns=res.length_ns, dt_ps=res.dt_ps
    )


def _save(fig, figure_id: str):
    from paper_engine.figures.render import FigureResult  # local import avoids cycle

    config.ensure_output_dirs()
    out = config.FIGURES_DIR / f"{figure_id}.png"
    fig.savefig(out)
    plt.close(fig)
    spec = MD_FIGURE_SPECS[figure_id]
    return out, spec


def render_md(stride: int = 2) -> List["object"]:
    """Render MD figures. Returns a list of FigureResult, or [] if unavailable."""
    from paper_engine.figures.render import FigureResult

    res = analyze(stride=stride)  # raises MDUnavailable if no topology
    results = []

    # RMSD
    fig, ax = plt.subplots(figsize=(7.0, 3.6))
    ax.plot(res.times_ns, res.rmsd, color=style.PRIMARY_COLOR, lw=1.4)
    ax.set_xlabel("Time (ns)")
    ax.set_ylabel("Cα RMSD (Å)")
    ax.set_title("Backbone stability (Cα RMSD)")
    style.despine(ax)
    out, spec = _save(fig, "md_rmsd")
    results.append(FigureResult(
        figure_id="md_rmsd", path=str(out), title=spec.title, caption=_caption("md_rmsd", res),
        reviewer_question=spec.reviewer_question, claim_support=spec.claim_support,
        kind=spec.kind, data_sources=[res.trajectory, res.topology],
        command="python -m paper_engine.figures.md"))

    # RMSF
    fig, ax = plt.subplots(figsize=(7.0, 3.6))
    ax.plot(res.rmsf_resids, res.rmsf, color=style.ACCENT_COLOR, lw=1.2)
    ax.fill_between(res.rmsf_resids, res.rmsf, color=style.ACCENT_COLOR, alpha=0.15)
    ax.set_xlabel("Residue")
    ax.set_ylabel("Cα RMSF (Å)")
    ax.set_title("Per-residue flexibility (Cα RMSF)")
    style.despine(ax)
    out, spec = _save(fig, "md_rmsf")
    results.append(FigureResult(
        figure_id="md_rmsf", path=str(out), title=spec.title, caption=_caption("md_rmsf", res),
        reviewer_question=spec.reviewer_question, claim_support=spec.claim_support,
        kind=spec.kind, data_sources=[res.trajectory, res.topology],
        command="python -m paper_engine.figures.md"))

    # DCCM
    fig, ax = plt.subplots(figsize=(5.6, 4.8))
    im = ax.imshow(res.dccm, cmap="RdBu_r", vmin=-1, vmax=1, origin="lower",
                   extent=[res.dccm_resids.min(), res.dccm_resids.max(),
                           res.dccm_resids.min(), res.dccm_resids.max()])
    ax.set_xlabel("Residue")
    ax.set_ylabel("Residue")
    ax.set_title("Cα dynamic cross-correlation")
    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label("Correlation")
    out, spec = _save(fig, "md_dccm")
    results.append(FigureResult(
        figure_id="md_dccm", path=str(out), title=spec.title, caption=_caption("md_dccm", res),
        reviewer_question=spec.reviewer_question, claim_support=spec.claim_support,
        kind=spec.kind, data_sources=[res.trajectory, res.topology],
        command="python -m paper_engine.figures.md"))
    return results


def main() -> None:  # pragma: no cover
    import argparse

    parser = argparse.ArgumentParser(description="Analyse the MD trajectory and render figures.")
    parser.add_argument("--stride", type=int, default=2)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    try:
        results = render_md(stride=args.stride)
        print(f"Rendered {len(results)} MD figure(s) to {config.FIGURES_DIR}")
        for r in results:
            print(f"  [{r.figure_id}] {r.path}")
    except MDUnavailable as exc:
        print("MD figures skipped (real-data integrity guard):")
        print(f"  {exc}")


if __name__ == "__main__":  # pragma: no cover
    main()
