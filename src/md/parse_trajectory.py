"""
MD trajectory analysis for GNN-PCNA — per-chain pocket-dynamics (CORRECTED).

Why this file was rewritten (see KNOWN_BUGS BUG-013..BUG-019):
  PCNA is a homotrimer. The AOH1996 cryptic pocket sits at ONE subunit interface
  and is measured per chain. The previous implementation made two fatal mistakes:

    1. It built a single convex hull from pocket residues matched by residue
       NUMBER across ALL THREE chains, so the "pocket volume" was actually the
       envelope of ~72 Cα scattered around the whole ~80 Å ring (~20,000 Å³).
       That envelope is rigid, so the volume looked flat — "the pocket has no
       dynamics" — a pure artifact of measuring the ring instead of the cavity.

    2. RMSF/DCCM were computed on UNALIGNED coordinates (MDAnalysis
       `AlignTraj(..., in_memory=False)` never rewires the Universe), so global
       rigid-body tumbling of the whole trimer dominated every residue.

  This module fixes both. Metric invariances make the design simple:
    * Convex-hull VOLUME, SASA and cross-wall DISTANCES are invariant to rigid
      motion, so they need NO alignment — they only need to be restricted to a
      SINGLE chain's pocket. SASA is computed on the whole protein (so the A–B
      interface burial is preserved) then summed over one chain's residues.
    * RMSF and DCCM measure deviation from a mean, so they DO need per-chain
      superposition on a stable core that EXCLUDES the pocket (no circularity).

Uses mdtraj (robust DCD + selection language). MDAnalysis is no longer required.
"""
from __future__ import annotations

from typing import Iterable, Sequence
import numpy as np
import mdtraj as md
from scipy.spatial import ConvexHull

# AOH1996 ground-truth pocket residues (PDB resSeq), 8GLA chains A and B.
# Keyed by protein CHAIN INDEX (0 = A, 1 = B). Chain C (index 2) does NOT bind
# AOH1996 (no ZQZ), so it is intentionally absent — matching by number alone
# would wrongly pull in the chain-C copy of every residue.
AOH_GT_BY_CHAIN: dict[int, list[int]] = {
    0: [25, 26, 27, 38, 39, 40, 41, 42, 44, 45, 46, 47,
        123, 125, 126, 128, 231, 232, 233, 234, 250, 251, 252, 253],
    1: [23, 25, 26, 27, 38, 39, 40, 41, 42, 44, 45, 46, 47,
        123, 125, 126, 128, 231, 232, 233, 234, 250, 251, 252],
}

# Front-face pocket "mouth" — cross-wall Cα pairs whose separation tracks
# opening/closing of the AOH1996 site.
MOUTH_PAIRS: list[tuple[int, int]] = [(44, 251), (122, 232), (128, 252), (42, 234)]

# Canonical front-face pocket residue set (chain-A AOH1996 numbering). PCNA is a
# homotrimer, so the SAME physical pocket exists on every subunit — for MD
# dynamics we apply this set to all three chains (informal n=3 triplicate),
# unlike the asymmetric AOH_GT_BY_CHAIN which is the ligand-resolved eval label.
MD_POCKET_RESSEQ: list[int] = list(AOH_GT_BY_CHAIN[0])


def pocket_for_all_chains(traj: md.Trajectory,
                          resseqs: Sequence[int] = MD_POCKET_RESSEQ) -> dict[int, list[int]]:
    """Map the canonical pocket residue set onto every protein chain present."""
    return {c: list(resseqs) for c in protein_chain_indices(traj)}


# ── loading ──────────────────────────────────────────────────────────────────

def load_trajectory(topology: str, trajectory: str, stride: int = 1) -> md.Trajectory:
    """Load an MD trajectory and make each molecule whole across the periodic box.

    topology: .pdb/.gro/.psf   trajectory: .dcd/.xtc
    """
    traj = md.load(str(trajectory), top=str(topology), stride=stride)
    try:
        traj.make_molecules_whole(inplace=True)
    except Exception:
        pass
    return traj


def protein_chain_indices(traj: md.Trajectory) -> list[int]:
    return sorted({r.chain.index for r in traj.topology.residues if r.is_protein})


def _resseq_selection(chain: int, resseqs: Iterable[int], extra: str = "") -> str:
    rs = " ".join(str(int(r)) for r in resseqs)
    sel = f"chainid {chain} and (resSeq {rs})"
    return f"{sel} and {extra}" if extra else sel


# ── per-chain metrics ────────────────────────────────────────────────────────

def pocket_volume_series(traj: md.Trajectory, chain: int,
                         resseqs: Sequence[int]) -> np.ndarray:
    """Convex-hull volume (Å³) of ONE chain's pocket Cα per frame.

    Rigid-motion invariant, so no alignment is required — the only thing that
    matters is that the residues come from a single subunit.
    """
    ca = traj.topology.select(_resseq_selection(chain, resseqs, "name CA"))
    if len(ca) < 4:
        return np.full(traj.n_frames, np.nan)
    xyz = traj.xyz[:, ca, :] * 10.0  # nm → Å
    vols = np.empty(traj.n_frames)
    for i in range(traj.n_frames):
        try:
            vols[i] = ConvexHull(xyz[i]).volume
        except Exception:
            vols[i] = np.nan
    return vols


def pocket_sasa_series(traj: md.Trajectory, chain: int, resseqs: Sequence[int],
                       sasa_residue: np.ndarray | None = None) -> np.ndarray:
    """Summed solvent-accessible surface area (Å²) of one chain's pocket per frame.

    SASA must be computed on the WHOLE protein so interface burial is preserved,
    then summed over the target chain's residues. Pass a precomputed
    (frames, n_residues) SASA array to avoid recomputing per chain.
    """
    if sasa_residue is None:
        sasa_residue = md.shrake_rupley(traj, mode="residue")
    res_index = {r.index: i for i, r in enumerate(traj.topology.residues)}
    want = set(int(r) for r in resseqs)
    cols = [res_index[r.index] for r in traj.topology.residues
            if r.chain.index == chain and r.is_protein and int(r.resSeq) in want]
    if not cols:
        return np.full(traj.n_frames, np.nan)
    return sasa_residue[:, cols].sum(axis=1) * 100.0  # nm² → Å²


def mouth_distance_series(traj: md.Trajectory, chain: int,
                          pairs: Sequence[tuple[int, int]] = MOUTH_PAIRS
                          ) -> dict[str, np.ndarray]:
    """Cross-wall Cα distances (Å) per frame — invariant, no alignment needed."""
    out: dict[str, np.ndarray] = {}
    for a, b in pairs:
        ia = traj.topology.select(f"chainid {chain} and resSeq {a} and name CA")
        ib = traj.topology.select(f"chainid {chain} and resSeq {b} and name CA")
        if len(ia) and len(ib):
            out[f"{a}-{b}"] = md.compute_distances(traj, [[ia[0], ib[0]]])[:, 0] * 10.0
    return out


def pocket_rmsf(traj: md.Trajectory, chain: int, resseqs: Sequence[int]
                ) -> tuple[np.ndarray, np.ndarray]:
    """Per-residue Cα RMSF (Å) for one chain's pocket, computed about the MEAN
    position AFTER superposing on that chain's non-pocket core (no circularity).

    Returns (resseq_array, rmsf_array).
    """
    core = traj.topology.select(
        _resseq_selection_complement(chain, resseqs))
    if len(core) < 10:
        core = traj.topology.select(f"chainid {chain} and name CA")
    t = traj[:]
    t.superpose(t, 0, atom_indices=core)
    ca = t.topology.select(_resseq_selection(chain, resseqs, "name CA"))
    if len(ca) == 0:
        return np.array([]), np.array([])
    xyz = t.xyz[:, ca, :]
    rmsf = np.sqrt(((xyz - xyz.mean(axis=0)) ** 2).sum(axis=2).mean(axis=0)) * 10.0
    resseq = np.array([t.topology.atom(i).residue.resSeq for i in ca])
    return resseq, rmsf


def _resseq_selection_complement(chain: int, resseqs: Iterable[int]) -> str:
    rs = " ".join(str(int(r)) for r in resseqs)
    return f"chainid {chain} and name CA and not (resSeq {rs})"


def chain_backbone_rmsd(traj: md.Trajectory, chain: int,
                        resseqs: Sequence[int]) -> np.ndarray:
    """Backbone Cα RMSD (Å) of one chain vs frame 0, aligned on that chain's
    non-pocket core. Sanity gate: a folded monomer should stay well under ~4 Å.
    Whole-trimer alignment (the old bug) inflates this to ~25–40 Å.
    """
    core = traj.topology.select(_resseq_selection_complement(chain, resseqs))
    if len(core) < 10:
        core = traj.topology.select(f"chainid {chain} and name CA")
    t = traj[:]
    t.superpose(t, 0, atom_indices=core)
    return md.rmsd(t, t, 0, atom_indices=core) * 10.0


def compute_dccm(traj: md.Trajectory, chain: int, resseqs: Sequence[int] | None = None
                 ) -> np.ndarray:
    """Signed dynamic cross-correlation matrix for ONE chain's Cα, after
    superposing on that chain's non-pocket core. Sign is preserved (correlated
    vs anti-correlated motion are physically different).
    """
    if resseqs is None:
        resseqs = AOH_GT_BY_CHAIN.get(chain, [])
    core = traj.topology.select(_resseq_selection_complement(chain, resseqs))
    if len(core) < 10:
        core = traj.topology.select(f"chainid {chain} and name CA")
    t = traj[:]
    t.superpose(t, 0, atom_indices=core)
    ca = t.topology.select(f"chainid {chain} and name CA")
    pos = t.xyz[:, ca, :]                    # (T, N, 3)
    delta = pos - pos.mean(axis=0)
    corr = np.einsum("tia,tja->ij", delta, delta) / pos.shape[0]
    var = np.diag(corr)
    norm = np.sqrt(np.outer(var, var))
    dccm = corr / np.where(norm > 1e-10, norm, 1e-10)
    return np.clip(dccm, -1.0, 1.0).astype(np.float32)


# ── whole-analysis driver ────────────────────────────────────────────────────

def analyze_pocket_dynamics(traj: md.Trajectory,
                            pocket_by_chain: dict[int, list[int]] = None,
                            equil_frames: int = 0,
                            ns_per_frame: float = 0.1) -> dict:
    """Full per-chain pocket-dynamics analysis on an already-loaded trajectory.

    Returns a dict with per-chain volume/SASA/mouth/RMSF time series + summaries
    and a cross-chain aggregate. All metrics honour chain identity.
    """
    if pocket_by_chain is None:
        pocket_by_chain = AOH_GT_BY_CHAIN

    prot = traj.atom_slice(traj.topology.select("protein"))
    if equil_frames > 0 and prot.n_frames > equil_frames:
        prot = prot[equil_frames:]
    chains = [c for c in protein_chain_indices(prot) if c in pocket_by_chain]

    # SASA once on the whole protein (interface burial preserved)
    sasa_res = md.shrake_rupley(prot, mode="residue")
    times = (np.arange(prot.n_frames) + equil_frames) * ns_per_frame

    per_chain: dict[str, dict] = {}
    for ch in chains:
        resseqs = pocket_by_chain[ch]
        vol = pocket_volume_series(prot, ch, resseqs)
        sasa = pocket_sasa_series(prot, ch, resseqs, sasa_residue=sasa_res)
        mouth = mouth_distance_series(prot, ch)
        _, rmsf = pocket_rmsf(prot, ch, resseqs)
        rmsd = chain_backbone_rmsd(prot, ch, resseqs)

        def _stats(a):
            a = np.asarray(a, float)
            a = a[~np.isnan(a)]
            if a.size == 0:
                return dict(mean=float("nan"), std=float("nan"),
                            min=float("nan"), max=float("nan"), range=float("nan"))
            return dict(mean=float(a.mean()), std=float(a.std()),
                        min=float(a.min()), max=float(a.max()),
                        range=float(a.max() - a.min()))

        per_chain[str(ch)] = {
            "times_ns": times.tolist(),
            "volume_A3": vol.tolist(),
            "sasa_A2": sasa.tolist(),
            "volume_stats": _stats(vol),
            "volume_cv": float(np.nanstd(vol) / np.nanmean(vol)) if np.nanmean(vol) else float("nan"),
            "sasa_stats": _stats(sasa),
            "pocket_rmsf_mean_A": float(np.nanmean(rmsf)) if rmsf.size else float("nan"),
            "pocket_rmsf_max_A": float(np.nanmax(rmsf)) if rmsf.size else float("nan"),
            "backbone_rmsd_mean_A": float(rmsd.mean()),
            "backbone_rmsd_max_A": float(rmsd.max()),
            "mouth": {k: _stats(v) for k, v in mouth.items()},
        }

    def _agg(key_path):
        vals = []
        for c in per_chain.values():
            node = c
            for k in key_path:
                node = node.get(k, {}) if isinstance(node, dict) else {}
            if isinstance(node, (int, float)) and not (isinstance(node, float) and np.isnan(node)):
                vals.append(node)
        return float(np.mean(vals)) if vals else float("nan")

    mouth_key = "122-232"
    aggregate = {
        "n_chains": len(chains),
        "vol_mean_A3": _agg(["volume_stats", "mean"]),
        "vol_range_A3": _agg(["volume_stats", "range"]),
        "vol_cv": float(np.nanmean([c["volume_cv"] for c in per_chain.values()]))
                  if per_chain else float("nan"),
        "sasa_range_A2": _agg(["sasa_stats", "range"]),
        "pocket_rmsf_mean_A": _agg(["pocket_rmsf_mean_A"]),
        "backbone_rmsd_mean_A": _agg(["backbone_rmsd_mean_A"]),
        f"mouth_{mouth_key}_range_A": float(np.nanmean(
            [c["mouth"].get(mouth_key, {}).get("range", np.nan) for c in per_chain.values()])),
        "pbc_sane": bool(_agg(["backbone_rmsd_max_A"]) < 5.0),
    }
    return {"chains": per_chain, "aggregate": aggregate,
            "ns_per_frame": ns_per_frame, "equil_frames": equil_frames}


# ── backward-compatible thin wrappers (used by src.md.__init__ re-exports) ────

def compute_rmsf(traj: md.Trajectory, chain: int = 0,
                 resseqs: Sequence[int] | None = None):
    """Per-chain pocket Cα RMSF. (Legacy name kept for the src.md re-export.)"""
    if resseqs is None:
        resseqs = AOH_GT_BY_CHAIN.get(chain, [])
    return pocket_rmsf(traj, chain, resseqs)


def track_pocket_volume(traj: md.Trajectory, chain: int,
                        pocket_resseqs: Sequence[int]) -> np.ndarray:
    """Single-chain pocket convex-hull volume series. (Legacy name.)"""
    return pocket_volume_series(traj, chain, pocket_resseqs)
