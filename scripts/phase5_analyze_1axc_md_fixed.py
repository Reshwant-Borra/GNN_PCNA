#!/usr/bin/env python
"""Phase 5 1AXC MD re-analysis — corrected RMSD/RMSF pipeline.

Fixes vs scripts/phase5_analyze_1axc_md.py:
  1. PBC imaging (make_molecules_whole + image_molecules) BEFORE superposition,
     so trimer chains that wrap across the periodic box no longer produce
     ~4 nm RMSD/RMSF spikes.
  2. Superpose on a stable core = protein CA EXCLUDING the analyzed windows
     (removes circularity: we don't align on the residues we're measuring).
  3. RMSF computed about the MEAN position, not frame 0.
  4. Equilibration discard before RMSF (default 5 ns).
  5. replicate_02 is flagged incomplete; replicate count reported honestly.

Exploratory triage only. No druggability / validated-site / GATE-7-complete claims.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import matplotlib.pyplot as plt
import mdtraj as md
import numpy as np
import pandas as pd


def parse_window(value: str) -> tuple[int, int]:
    left, right = value.split("-", 1)
    return int(left), int(right)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Corrected 1AXC Phase 5 MD analysis.")
    p.add_argument("--run-root", type=Path,
                   default=Path("outputs/phase5_md/time_crunch_1axc_25ns"))
    p.add_argument("--windows", nargs="+",
                   default=["239-243", "28-32", "206-210", "134-138"])
    p.add_argument("--reference-window", default="118-122")
    p.add_argument("--equil-ns", type=float, default=5.0,
                   help="Equilibration time discarded before RMSF.")
    p.add_argument("--ns-per-frame", type=float, default=0.1,
                   help="Trajectory save interval (ns/frame). 25 ns / 250 frames = 0.1.")
    p.add_argument("--min-frames", type=int, default=100,
                   help="Replicates with fewer post-equil frames are flagged incomplete.")
    p.add_argument("--out-suffix", default="_fixed")
    return p.parse_args()


def resseq_to_residue_indices(traj, start: int, end: int) -> list[int]:
    out = []
    for r in traj.topology.residues:
        try:
            rs = int(r.resSeq)
        except Exception:
            continue
        if r.is_protein and start <= rs <= end:
            out.append(r.index)
    return out


def ca_atoms_for_residues(traj, residue_indices: set[int]) -> list[int]:
    return [a.index for a in traj.topology.atoms
            if a.residue.index in residue_indices and a.name == "CA"]


def main() -> None:
    args = parse_args()
    analysis_dir = args.run_root / f"analysis{args.out_suffix}"
    analysis_dir.mkdir(parents=True, exist_ok=True)

    windows = [(lbl, *parse_window(lbl)) for lbl in args.windows]
    if args.reference_window:
        windows.append((f"{args.reference_window}_reference",
                        *parse_window(args.reference_window)))

    equil_frames = int(round(args.equil_ns / args.ns_per_frame))

    summaries, rmsd_rows, rmsf_rows = [], [], []
    rep_status: dict[str, dict] = {}

    for rep_dir in sorted(args.run_root.glob("replicate_*")):
        traj_path = rep_dir / "trajectory.dcd"
        top_path = rep_dir / "solvated_initial.pdb"
        if not traj_path.exists() or not top_path.exists():
            continue
        rep = rep_dir.name
        print(f"[{rep}] loading {traj_path}")
        traj = md.load_dcd(str(traj_path), top=str(top_path))
        n_total = traj.n_frames

        # --- FIX 1: make the complex whole and image into the box BEFORE aligning ---
        try:
            traj.make_molecules_whole(inplace=True)
        except Exception as exc:
            print(f"[{rep}] make_molecules_whole skipped: {exc}")
        try:
            traj.image_molecules(inplace=True)
        except Exception as exc:
            print(f"[{rep}] image_molecules skipped: {exc}")

        all_ca = traj.topology.select("protein and name CA")
        if len(all_ca) == 0:
            print(f"[{rep}] no protein CA; skipping")
            continue

        # residue indices belonging to any analyzed window (for core exclusion)
        window_res = set()
        for _lbl, s, e in windows:
            window_res.update(resseq_to_residue_indices(traj, s, e))

        # --- FIX 2: align on stable core = protein CA NOT in any measured window ---
        core_ca = np.array([i for i in all_ca
                            if traj.topology.atom(i).residue.index not in window_res])
        if core_ca.size < 10:
            core_ca = all_ca  # fallback
        traj.superpose(traj, 0, atom_indices=core_ca)

        # backbone RMSD (post-imaging, core-aligned) over full trajectory
        rmsd = md.rmsd(traj, traj, 0, atom_indices=core_ca)
        for fi, val in enumerate(rmsd):
            rmsd_rows.append({"replicate": rep, "frame": fi,
                              "time_ns": fi * args.ns_per_frame,
                              "rmsd_nm": float(val)})

        # --- FIX 4: discard equilibration for RMSF ---
        usable = max(0, n_total - equil_frames)
        incomplete = usable < args.min_frames
        rep_status[rep] = {"n_frames": int(n_total), "equil_frames": equil_frames,
                           "frames_used_for_rmsf": int(usable),
                           "incomplete": bool(incomplete),
                           "mean_backbone_rmsd_nm": float(np.mean(rmsd)),
                           "max_backbone_rmsd_nm": float(np.max(rmsd)),
                           "final_backbone_rmsd_nm": float(rmsd[-1])}
        prod = traj[equil_frames:] if usable > 0 else traj

        for lbl, s, e in windows:
            res = set(resseq_to_residue_indices(traj, s, e))
            ca = ca_atoms_for_residues(traj, res)
            if not ca:
                summaries.append({"replicate": rep, "window": lbl,
                                  "status": "no_ca_atoms_found",
                                  "residue_start": s, "residue_end": e})
                continue
            xyz = prod.xyz[:, ca, :]                       # (frames, atoms, 3)
            # --- FIX 3: RMSF about the MEAN position ---
            mean_xyz = xyz.mean(axis=0)
            diffs = xyz - mean_xyz[None, :, :]
            per_atom = np.sqrt(np.mean(np.sum(diffs ** 2, axis=2), axis=0))
            for ai, val in zip(ca, per_atom):
                at = traj.topology.atom(ai)
                rmsf_rows.append({"replicate": rep, "window": lbl,
                                  "chain_index": at.residue.chain.index,
                                  "residue": int(at.residue.resSeq),
                                  "resname": at.residue.name,
                                  "rmsf_nm": float(val)})
            summaries.append({"replicate": rep, "window": lbl, "status": "ok",
                              "incomplete_replicate": bool(incomplete),
                              "residue_start": s, "residue_end": e,
                              "n_ca_atoms": len(ca),
                              "mean_rmsf_nm": float(np.mean(per_atom)),
                              "max_rmsf_nm": float(np.max(per_atom))})

    rmsd_df = pd.DataFrame(rmsd_rows)
    rmsf_df = pd.DataFrame(rmsf_rows)
    summary_df = pd.DataFrame(summaries)
    rmsd_df.to_csv(analysis_dir / "rmsd_timeseries.csv", index=False)
    rmsf_df.to_csv(analysis_dir / "window_rmsf.csv", index=False)
    summary_df.to_csv(analysis_dir / "window_summary.csv", index=False)

    # window mean RMSF vs reference, per replicate (complete replicates only)
    cmp_rows = []
    if not summary_df.empty:
        ok = summary_df[summary_df["status"] == "ok"]
        for rep, g in ok.groupby("replicate"):
            ref = g[g["window"].str.contains("reference")]["mean_rmsf_nm"]
            ref_val = float(ref.iloc[0]) if len(ref) else float("nan")
            for _, row in g.iterrows():
                cmp_rows.append({"replicate": rep, "window": row["window"],
                                 "mean_rmsf_nm": row["mean_rmsf_nm"],
                                 "ref_118_122_nm": ref_val,
                                 "ratio_vs_ref": (row["mean_rmsf_nm"] / ref_val)
                                 if ref_val == ref_val and ref_val else float("nan"),
                                 "incomplete_replicate": bool(row.get("incomplete_replicate", False))})
    cmp_df = pd.DataFrame(cmp_rows)
    cmp_df.to_csv(analysis_dir / "window_vs_reference.csv", index=False)

    (analysis_dir / "analysis_summary.json").write_text(json.dumps({
        "status": "analysis_complete_corrected",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "run_root": str(args.run_root),
        "windows": args.windows,
        "reference_window": args.reference_window,
        "equil_ns_discarded": args.equil_ns,
        "ns_per_frame": args.ns_per_frame,
        "replicates": rep_status,
        "fixes_applied": [
            "PBC make_molecules_whole + image_molecules before superpose",
            "align on core CA excluding analyzed windows (no circularity)",
            "RMSF about mean position (not frame 0)",
            f"discard first {args.equil_ns} ns equilibration before RMSF",
            "incomplete replicates flagged",
        ],
        "limitations": [
            "Exploratory short-timescale MD; 1AXC apo-from-p21 only.",
            "No 8GLA positive control; not GATE 7 Wave 1 completion.",
            "RMSD/RMSF alone do not prove pocket opening or binding.",
            "No druggability / therapeutic / validated-site claims supported.",
        ],
    }, indent=2), encoding="utf-8")

    if not rmsd_df.empty:
        plt.figure(figsize=(7, 4))
        for rep, g in rmsd_df.groupby("replicate"):
            plt.plot(g["time_ns"], g["rmsd_nm"], label=rep, lw=1)
        plt.axvline(args.equil_ns, ls="--", c="grey", lw=1, label=f"equil {args.equil_ns} ns")
        plt.xlabel("Time (ns)"); plt.ylabel("Backbone CA RMSD (nm)")
        plt.legend(); plt.tight_layout()
        plt.savefig(analysis_dir / "rmsd_timeseries.png", dpi=200); plt.close()

    if not cmp_df.empty:
        plt.figure(figsize=(8, 4))
        comp = cmp_df[~cmp_df["incomplete_replicate"]]
        plot_src = comp if not comp.empty else cmp_df
        for rep, g in plot_src.groupby("replicate"):
            plt.bar([f"{w}\n{rep}" for w in g["window"]], g["mean_rmsf_nm"])
        plt.ylabel("Mean window CA RMSF (nm)")
        plt.xticks(rotation=30, ha="right"); plt.tight_layout()
        plt.savefig(analysis_dir / "window_rmsf_summary.png", dpi=200); plt.close()

    print("\n=== REPLICATE STATUS ===")
    print(json.dumps(rep_status, indent=2))
    print("\n=== WINDOW SUMMARY (ok rows) ===")
    if not summary_df.empty:
        cols = ["replicate", "window", "n_ca_atoms", "mean_rmsf_nm",
                "max_rmsf_nm", "incomplete_replicate"]
        print(summary_df[summary_df["status"] == "ok"][cols].to_string(index=False))
    print("\n=== WINDOW vs REFERENCE 118-122 ===")
    if not cmp_df.empty:
        print(cmp_df.to_string(index=False))
    print(f"\nOutputs -> {analysis_dir}")


if __name__ == "__main__":
    main()
