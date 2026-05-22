"""
MD trajectory analysis for GNN-PCNA.

Reads a trajectory produced by colab_md_simulation.ipynb and computes:
  - Per-residue Ca RMSF
  - Dynamic Cross-Correlation Matrix (DCCM)
  - Pocket volume time series (rolling convex-hull approximation)
  - Apo pocket vs. background fold-change (MD version of the ANM comparison)

Writes:
  data/results/md_rmsf_1W60.json      -- per-residue RMSF
  data/results/md_dccm_1W60.npy       -- N×N DCCM matrix
  data/results/md_pocket_volume.json  -- pocket volume per frame
  data/results/md_apo_comparison.json -- pocket vs. background stats

Usage:
    python scripts/run_md_analysis.py
    python scripts/run_md_analysis.py --top data/md/1W60_topology.pdb \
                                      --traj data/md/1W60_production.dcd \
                                      --stride 10
"""
from __future__ import annotations
import sys, json, argparse
from pathlib import Path

import numpy as np

REPO = Path(__file__).parent.parent
sys.path.insert(0, str(REPO))

# AOH1996 ground-truth pocket residue IDs (transferred to 1W60 by sequence)
AOH_GT_BY_CHAIN = {
    "A": {25,26,27,38,39,40,41,42,44,45,46,47,
          123,125,126,128,231,232,233,234,250,251,252,253},
    "B": {23,25,26,27,38,39,40,41,42,44,45,46,47,
          123,125,126,128,231,232,233,234,250,251,252},
}
AOH_GT = set().union(*AOH_GT_BY_CHAIN.values())


def compute_rmsf(u, stride: int = 1):
    """Align trajectory to first frame on backbone, then compute Ca RMSF."""
    try:
        from MDAnalysis.analysis import rms, align
    except ImportError:
        raise ImportError("pip install MDAnalysis")

    import MDAnalysis as mda

    ref = mda.Universe(u.filename)
    print("  Aligning trajectory to reference (backbone)...")
    # in_memory=False streams to a temp file (safe for large DCD); run() with no step aligns
    # all frames so RMSF.run(step=stride) below doesn't double-skip frames
    align.AlignTraj(u, ref, select="backbone", in_memory=False).run()

    ca = u.select_atoms("name CA")
    n_frames = len(u.trajectory) // stride
    print(f"  Computing RMSF over {n_frames} frames ({ca.n_atoms} Ca atoms)...")
    rmsf_calc = rms.RMSF(ca).run(step=stride)
    return ca.resids.copy(), ca.segids.copy(), rmsf_calc.rmsf.copy()


def compute_dccm(u, stride: int = 10):
    """Compute Dynamic Cross-Correlation Matrix from Ca displacement."""
    ca = u.select_atoms("name CA")
    N = ca.n_atoms
    n_frames = len(u.trajectory) // stride
    print(f"  Computing DCCM: {N}×{N} over {n_frames} frames...")

    # Accumulate mean and outer products
    sum_r  = np.zeros((N, 3))
    sum_rr = np.zeros((N, N))
    sum_r2 = np.zeros(N)
    count  = 0

    for ts in u.trajectory[::stride]:
        r = ca.positions.copy()
        sum_r  += r
        count  += 1

    mean_r = sum_r / count  # (N, 3)

    # Second pass: compute cross-correlations
    for ts in u.trajectory[::stride]:
        dr = ca.positions - mean_r   # (N, 3)
        dot = (dr[:, None, :] * dr[None, :, :]).sum(axis=2)  # (N, N)
        sum_rr += dot
        sum_r2 += (dr ** 2).sum(axis=1)

    cross = sum_rr / count
    denom = np.sqrt(np.maximum(np.outer(sum_r2 / count, sum_r2 / count), 0.0))
    denom[denom == 0] = 1.0
    dccm = np.clip(cross / denom, -1.0, 1.0)
    return dccm.astype(np.float32)


def compute_pocket_volume(u, pocket_resids: set, stride: int = 10):
    """Estimate pocket volume per frame using Ca convex hull approximation."""
    try:
        from scipy.spatial import ConvexHull
    except ImportError:
        print("  scipy not available — skipping volume analysis")
        return None

    from scipy.spatial import ConvexHull

    ca = u.select_atoms("name CA")
    volumes = []
    times_ps = []

    for ts in u.trajectory[::stride]:
        coords = ca.positions
        resids = ca.resids
        mask = np.array([r in pocket_resids for r in resids])
        pocket_coords = coords[mask]
        if len(pocket_coords) >= 4:
            try:
                hull = ConvexHull(pocket_coords)
                volumes.append(float(hull.volume))  # Å³
            except Exception:
                volumes.append(float("nan"))
        else:
            volumes.append(float("nan"))
        times_ps.append(float(ts.time))

    return times_ps, volumes


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--top",    default="data/md/1W60_topology.pdb",
                        help="Topology file (.pdb)")
    parser.add_argument("--traj",   default="data/md/1W60_production.dcd",
                        help="Trajectory file (.dcd or .xtc)")
    parser.add_argument("--stride", type=int, default=10,
                        help="Frame stride for DCCM/volume (default: 10 = every 100 ps)")
    args = parser.parse_args()

    top_path  = REPO / args.top
    traj_path = REPO / args.traj
    out_dir   = REPO / "data" / "results"
    out_dir.mkdir(parents=True, exist_ok=True)

    if not top_path.exists():
        print(f"ERROR: topology not found: {top_path}")
        print("  Run colab_md_simulation.ipynb first and copy outputs to data/md/")
        sys.exit(1)
    if not traj_path.exists():
        print(f"ERROR: trajectory not found: {traj_path}")
        print("  Run colab_md_simulation.ipynb first and copy outputs to data/md/")
        sys.exit(1)

    try:
        import MDAnalysis as mda
    except ImportError:
        print("ERROR: MDAnalysis not installed. Run: pip install MDAnalysis")
        sys.exit(1)

    print(f"Loading universe: {top_path.name} + {traj_path.name}")
    u = mda.Universe(str(top_path), str(traj_path))
    print(f"  {len(u.trajectory)} frames, {u.trajectory.dt:.1f} ps/frame")
    print(f"  {u.atoms.n_atoms} atoms, {u.residues.n_residues} residues")
    sim_time_ns = len(u.trajectory) * u.trajectory.dt / 1000
    print(f"  Simulation length: {sim_time_ns:.1f} ns")

    # ── 1. RMSF ───────────────────────────────────────────────────────────────
    print("\n[1/3] Computing Ca RMSF...")
    resids, chains, rmsf = compute_rmsf(u, stride=args.stride)

    pocket_mask = np.array([r in AOH_GT for r in resids])
    pocket_rmsf = float(rmsf[pocket_mask].mean()) if pocket_mask.any() else None
    bg_rmsf     = float(rmsf[~pocket_mask].mean()) if (~pocket_mask).any() else None
    fold_change = round(pocket_rmsf / bg_rmsf, 3) if pocket_rmsf and bg_rmsf else None

    print(f"  Pocket RMSF : {pocket_rmsf:.3f} Å")
    print(f"  Background  : {bg_rmsf:.3f} Å")
    print(f"  Fold-change : {fold_change:.3f}")

    rmsf_result = {
        "source": "MDAnalysis Ca RMSF",
        "topology": args.top,
        "trajectory": args.traj,
        "n_frames": len(u.trajectory),
        "sim_time_ns": sim_time_ns,
        "stride": args.stride,
        "pocket_rmsf_angstrom": round(pocket_rmsf, 4) if pocket_rmsf else None,
        "background_rmsf_angstrom": round(bg_rmsf, 4) if bg_rmsf else None,
        "fold_change_pocket_vs_bg": fold_change,
        "residues": [
            {"resid": int(resids[i]), "chain": str(chains[i]),
             "rmsf_angstrom": round(float(rmsf[i]), 4),
             "in_aoh_pocket": bool(pocket_mask[i])}
            for i in range(len(resids))
        ],
    }
    out_rmsf = out_dir / "md_rmsf_1W60.json"
    out_rmsf.write_text(json.dumps(rmsf_result, indent=2), encoding="utf-8")
    print(f"  Saved -> {out_rmsf.relative_to(REPO)}")

    # ── 2. DCCM ──────────────────────────────────────────────────────────────
    print("\n[2/3] Computing DCCM...")
    dccm = compute_dccm(u, stride=args.stride)
    out_dccm = out_dir / "md_dccm_1W60.npy"
    np.save(str(out_dccm), dccm)
    print(f"  DCCM shape: {dccm.shape}")

    # Pocket internal DCCM
    pocket_idx = np.where(pocket_mask)[0]
    if len(pocket_idx) >= 2:
        sub = dccm[np.ix_(pocket_idx, pocket_idx)]
        off = sub[np.triu_indices(len(pocket_idx), k=1)]
        pocket_dccm = float(off.mean())
    else:
        pocket_dccm = None
    print(f"  Pocket internal DCCM: {pocket_dccm:.4f}")
    print(f"  Saved -> {out_dccm.relative_to(REPO)}")

    # ── 3. Pocket volume ──────────────────────────────────────────────────────
    print("\n[3/3] Computing pocket volume time series...")
    vol_result = compute_pocket_volume(u, AOH_GT, stride=args.stride)

    if vol_result:
        times_ps, volumes = vol_result
        vols_clean = [v for v in volumes if not (isinstance(v, float) and v != v)]
        mean_vol = float(np.nanmean(volumes))
        max_vol  = float(np.nanmax(volumes))
        print(f"  Mean pocket volume: {mean_vol:.1f} Å³")
        print(f"  Max pocket volume:  {max_vol:.1f} Å³")
        vol_data = {
            "method": "Ca convex hull (approximate)",
            "note": "Convex hull overestimates true pocket volume; use fpocket/MDpocket for accurate cavity volume",
            "mean_volume_angstrom3": round(mean_vol, 1),
            "max_volume_angstrom3": round(max_vol, 1),
            "frames": [{"time_ps": t, "volume_angstrom3": v}
                       for t, v in zip(times_ps, volumes)],
        }
        out_vol = out_dir / "md_pocket_volume.json"
        out_vol.write_text(json.dumps(vol_data, indent=2), encoding="utf-8")
        print(f"  Saved -> {out_vol.relative_to(REPO)}")

    # ── Summary ───────────────────────────────────────────────────────────────
    summary = {
        "topology": args.top,
        "trajectory": args.traj,
        "sim_time_ns": sim_time_ns,
        "n_frames": len(u.trajectory),
        "aoh_pocket_residues": int(pocket_mask.sum()),
        "md_rmsf": {
            "pocket_angstrom": round(pocket_rmsf, 4) if pocket_rmsf else None,
            "background_angstrom": round(bg_rmsf, 4) if bg_rmsf else None,
            "fold_change": fold_change,
        },
        "md_dccm": {
            "pocket_internal": round(pocket_dccm, 4) if pocket_dccm else None,
            "matrix_file": "data/results/md_dccm_1W60.npy",
        },
        "anm_comparison": {
            "anm_fold_change_apo": 0.857,
            "md_fold_change_apo": fold_change,
            "note": "ANM fold-change was 0.857; MD fold-change here is the all-atom equivalent",
        },
    }
    out_summary = out_dir / "md_apo_comparison.json"
    out_summary.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"\nSummary -> {out_summary.relative_to(REPO)}")
    print(f"\nANM vs MD comparison:")
    print(f"  ANM fold-change (apo 1W60): 0.857")
    print(f"  MD  fold-change (apo 1W60): {fold_change}")
    print(f"  ANM internal DCCM:          0.0995")
    print(f"  MD  internal DCCM:          {pocket_dccm:.4f}" if pocket_dccm else "  MD  internal DCCM: N/A")


if __name__ == "__main__":
    main()
