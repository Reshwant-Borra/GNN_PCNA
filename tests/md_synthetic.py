"""Deterministic synthetic MD systems for analysis/gate testing.

These build REAL mdtraj topologies and REAL DCD files so the tests exercise the production
analysis path (md.load -> imaging -> superposition -> SASA -> hull -> DCCM -> openness ->
gate) rather than hand-written metric dictionaries.

Nothing here is scientific evidence. It exists to prove that the frozen analysis code
distinguishes genuine trajectory dynamics from a static structure plus per-frame noise.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

# The frozen supported_ge2of3 candidate residues (chain A author numbering).
POCKET_RESSEQ = [25, 26, 27, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 232, 233, 234]
CORE_RESSEQ = [25, 26, 38, 39, 40, 41, 42, 44, 45, 46, 47]

# Real control-5 cadence: 5 ns at a 50 ps output interval.
REPORT_PS = 50.0
DT_NS = REPORT_PS / 1000.0
N_FRAMES_5NS = 100

# 0.10 A of independent per-axis coordinate jitter -- the exact "static structure plus tiny
# noise" case the frozen protocol's negative_diagnostic requires to FAIL.
STATIC_JITTER_NM = 0.010


def build_topology(n_extra_res: int = 44, n_chains: int = 2):
    """A minimal but genuine protein topology containing the frozen candidate residues."""
    import mdtraj as md

    resseqs = sorted(set(POCKET_RESSEQ) | set(CORE_RESSEQ))
    filler = [r for r in range(1, 400) if r not in resseqs][:n_extra_res]
    resseqs = sorted(resseqs + filler)

    top = md.Topology()
    for _ in range(n_chains):
        chain = top.add_chain()
        prev_c = None
        for rs in resseqs:
            res = top.add_residue("ALA", chain, resSeq=rs)
            n = top.add_atom("N", md.element.nitrogen, res)
            ca = top.add_atom("CA", md.element.carbon, res)
            c = top.add_atom("C", md.element.carbon, res)
            o = top.add_atom("O", md.element.oxygen, res)
            cb = top.add_atom("CB", md.element.carbon, res)
            top.add_bond(n, ca)
            top.add_bond(ca, c)
            top.add_bond(c, o)
            top.add_bond(ca, cb)
            if prev_c is not None:
                top.add_bond(prev_c, n)
            prev_c = c
    return top, resseqs


def _base_coordinates(top, seed: int = 7) -> np.ndarray:
    rng = np.random.default_rng(seed)
    xyz = np.zeros((top.n_atoms, 3), dtype=np.float32)
    for atom in top.atoms:
        ri = atom.residue.index
        ci = atom.residue.chain.index
        t = ri * 0.35
        xyz[atom.index] = [np.cos(t) * 1.2 + ci * 6.0, np.sin(t) * 1.2, t * 0.15]
    return xyz + rng.normal(0, 0.03, xyz.shape).astype(np.float32)


def _pocket_atom_indices(top, chain_index: int = 0):
    want = set(POCKET_RESSEQ)
    return [a.index for a in top.atoms
            if a.residue.chain.index == chain_index and a.residue.resSeq in want]


def make_trajectory(kind: str, n_frames: int = N_FRAMES_5NS, seed: int = 0,
                    jitter_nm: float = STATIC_JITTER_NM, open_scale: float = 1.0):
    """Return (traj, base_xyz).

    kind='static_noise' : a MOTIONLESS structure observed with independent per-frame Gaussian
                          coordinate noise. This is the null the positive-control gate must
                          reject. There is no temporal structure and no collective motion.
    kind='dynamic'      : a genuine collective breathing motion of the candidate region --
                          a smooth low-frequency mode plus thermal noise. Temporally
                          autocorrelated and spatially collective.
    """
    import mdtraj as md

    top, _ = build_topology()
    base = _base_coordinates(top)
    if open_scale != 1.0:
        pocket = _pocket_atom_indices(top)
        centre = base[pocket].mean(axis=0)
        base = base.copy()
        base[pocket] = centre + (base[pocket] - centre) * open_scale

    rng = np.random.default_rng(1000 + seed)
    frames = np.repeat(base[None], n_frames, axis=0).astype(np.float32)

    if kind == "static_noise":
        frames += rng.normal(0.0, jitter_nm, frames.shape).astype(np.float32)
    elif kind == "dynamic":
        pocket = _pocket_atom_indices(top)
        centre = base[pocket].mean(axis=0)
        radial = base[pocket] - centre
        radial /= np.maximum(np.linalg.norm(radial, axis=1, keepdims=True), 1e-6)
        t = np.arange(n_frames)
        # two incommensurate slow modes -> smooth, autocorrelated, collective breathing
        amp = (0.18 * np.sin(2 * np.pi * t / 25.0) + 0.07 * np.sin(2 * np.pi * t / 61.0))
        frames[:, pocket, :] += (amp[:, None, None] * radial[None, :, :]).astype(np.float32)
        frames += rng.normal(0.0, 0.002, frames.shape).astype(np.float32)
    else:
        raise ValueError(f"unknown kind {kind!r}")

    traj = md.Trajectory(frames, top)
    traj.unitcell_lengths = np.tile([20.0, 20.0, 20.0], (n_frames, 1))
    traj.unitcell_angles = np.tile([90.0, 90.0, 90.0], (n_frames, 1))
    return traj, base


def make_rmsd_trajectory(mode: str, n_frames: int = N_FRAMES_5NS, displacement_nm: float = 0.5):
    """Deterministic trajectories with a KNOWN analytic RMSD answer.

    frame 0 is always the reference. Every later frame carries the transformation under test,
    so the answer is exact and independent of any fitting.

    mode='rigid_global'      : the WHOLE protein is rigidly rotated and translated.
                               Scaffold-aligned global RMSD and region RMSD are both 0.
    mode='region_displaced'  : the candidate region is rigidly translated by displacement_nm
                               while the scaffold is fixed. Region RMSD after scaffold
                               alignment must equal displacement_nm exactly.
    mode='region_deformed'   : the candidate region is internally deformed (expanded about
                               its own centroid) with no net translation. Both the
                               scaffold-aligned and the region-internal RMSD are nonzero.
    """
    import mdtraj as md

    top, _ = build_topology()
    base = _base_coordinates(top)
    frames = np.repeat(base[None], n_frames, axis=0).astype(np.float32)
    pocket = _pocket_atom_indices(top)

    if mode == "rigid_global":
        theta = 0.7
        rot = np.array([[np.cos(theta), -np.sin(theta), 0.0],
                        [np.sin(theta), np.cos(theta), 0.0],
                        [0.0, 0.0, 1.0]], dtype=np.float32)
        shift = np.array([3.0, -2.0, 1.0], dtype=np.float32)
        for f in range(1, n_frames):
            frames[f] = base @ rot.T + shift
    elif mode == "region_displaced":
        for f in range(1, n_frames):
            frames[f, pocket, :] = base[pocket] + np.array(
                [displacement_nm, 0.0, 0.0], dtype=np.float32)
    elif mode == "region_deformed":
        centre = base[pocket].mean(axis=0)
        for f in range(1, n_frames):
            frames[f, pocket, :] = centre + (base[pocket] - centre) * np.float32(1.20)
    else:
        raise ValueError(f"unknown mode {mode!r}")

    traj = md.Trajectory(frames, top)
    traj.unitcell_lengths = np.tile([20.0, 20.0, 20.0], (n_frames, 1))
    traj.unitcell_angles = np.tile([90.0, 90.0, 90.0], (n_frames, 1))
    return traj


def write_replicate(root: Path, pdb: str, replicate: str, traj, *, role: str = "control",
                    report_ps: float = REPORT_PS, timestep_fs: float = 4.0,
                    truncate_frames: int | None = None, write_done: bool = True,
                    write_log: bool = True) -> Path:
    """Materialise a replicate directory exactly as run_md.py would lay it out."""
    base = root / pdb
    rep = base / replicate
    rep.mkdir(parents=True, exist_ok=True)
    if not (base / "system_solvated.pdb").exists():
        traj[0].save_pdb(str(base / "system_solvated.pdb"))
    out = traj if truncate_frames is None else traj[:truncate_frames]
    out.save_dcd(str(rep / "production.dcd"))

    n = out.n_frames
    dt_ns = timestep_fs / 1_000_000.0
    steps_per_frame = int(round(report_ps / (timestep_fs / 1000.0)))
    production_steps = n * steps_per_frame
    equil_steps = int(round(2.0 / dt_ns))
    target_ns = traj.n_frames * report_ps / 1000.0

    if write_log:
        lines = ['#"Progress (%)"\t"Step"\t"Time (ps)"\t"Potential Energy (kJ/mole)"'
                 '\t"Temperature (K)"\t"Density (g/mL)"']
        for i in range(1, n + 1):
            lines.append(f"{100.0 * i / n:.1f}\t{equil_steps + i * steps_per_frame}"
                         f"\t{i * report_ps:.4f}\t-1.5e6\t310.1\t1.010")
        (rep / "production.log").write_text("\n".join(lines) + "\n", encoding="utf-8")

    if write_done:
        (rep / "DONE.json").write_text(json.dumps({
            "replicate": int(replicate.replace("rep", "")),
            "pdb": pdb, "role": role, "ns": target_ns,
            "md_stage": "control_validation",
            "production_ns": production_steps * dt_ns,
            "production_steps": production_steps,
            "target_production_steps": int(round(target_ns / dt_ns)),
            "equilibration_steps": equil_steps,
            "equil_ns": 2.0, "report_ps": report_ps, "checkpoint_ps": 10.0,
            "steps": equil_steps + production_steps,
            "target_total_steps": equil_steps + int(round(target_ns / dt_ns)),
            "timestep_fs": timestep_fs,
            "sanity_gate": "passed: finite energy+coords",
            "topology": "system_solvated.pdb", "trajectory": "production.dcd",
            "dcd_frames": n,
        }, indent=2), encoding="utf-8")
        (rep / "PROVENANCE.json").write_text(json.dumps({
            "schema_version": 1, "structure_pdb_id": pdb, "role": role,
            "replicate": int(replicate.replace("rep", "")),
            "input_hashes": {"frozen_analysis_protocol_sha256": "0" * 64},
        }, indent=2), encoding="utf-8")
    return rep
