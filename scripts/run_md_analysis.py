"""
MD trajectory analysis for GNN-PCNA — CORRECTED per-chain pocket dynamics.

Computes, for the AOH1996 cryptic pocket of PCNA (a homotrimer), the metrics
that actually reveal whether the pocket has dynamics — measured PER CHAIN, not
across the whole ring (see src/md/parse_trajectory.py header and KNOWN_BUGS
BUG-013..BUG-019 for why the previous whole-ring convex hull was a flat artifact):

  - per-chain pocket convex-hull VOLUME time series (breathing)
  - per-chain pocket SASA time series (solvent exposure / opening)
  - per-chain front-face MOUTH cross-wall Cα distances (open/close)
  - per-chain pocket Cα RMSF about the mean, core-aligned (flexibility)
  - per-chain backbone RMSD sanity gate (whole-trimer alignment inflated this to
    ~25-40 Å — a false "corrupt" negative; per-chain alignment gives ~2-3 Å)

Writes to data/results/:
  md_pocket_volume.json   -- per-chain volume + sasa + mouth series & summaries
  md_rmsf.json            -- per-residue, per-chain pocket & background RMSF
  md_dccm.npy             -- chain-averaged Cα DCCM (signed)
  md_apo_comparison.json  -- aggregate summary + honest ANM comparison

Usage:
    python scripts/run_md_analysis.py                  # auto-discovers a trajectory
    python scripts/run_md_analysis.py --top TOP.pdb --traj TRAJ.dcd
    python scripts/run_md_analysis.py --stride 2 --equil-ns 5 --ns-per-frame 0.1
"""
from __future__ import annotations
import sys, io, json, argparse
from pathlib import Path

import numpy as np

# Force UTF-8 on Windows consoles (cp1252 chokes on Å, ×, etc.)
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = Path(__file__).parent.parent
sys.path.insert(0, str(REPO))

from src.md.parse_trajectory import (           # noqa: E402
    load_trajectory, analyze_pocket_dynamics, protein_chain_indices,
    pocket_rmsf, compute_dccm, pocket_for_all_chains,
)

# ── self-validating verdict thresholds ────────────────────────────────────────
# A broken analysis (e.g. whole-trimer misalignment) inflates per-chain backbone
# RMSD to ~25-40 Å. A folded monomer over ns-timescale MD should stay < ~5 Å.
RMSD_SANITY_MAX_A   = 5.0     # above this → analysis INVALID, not a negative
VOL_RANGE_DYN_A3    = 150.0   # pocket volume fluctuation range that counts as dynamics
SASA_RANGE_DYN_A2   = 150.0
MOUTH_RANGE_DYN_A   = 2.0


def classify_dynamics(agg: dict) -> tuple[str, str]:
    """Three-way self-validating verdict so a BROKEN analysis can never be
    mistaken for a genuine 'no dynamics' negative (the exact failure this
    pipeline exists to prevent).

    Returns (code, human_message) where code ∈
      {"DYNAMICS", "VALID_NEGATIVE", "INVALID_ANALYSIS"}.
    """
    rmsd = agg.get("backbone_rmsd_mean_A", float("nan"))
    if not (rmsd == rmsd) or rmsd > RMSD_SANITY_MAX_A or not agg.get("pbc_sane", False):
        return ("INVALID_ANALYSIS",
                f"per-chain backbone RMSD {rmsd:.1f} Å exceeds the {RMSD_SANITY_MAX_A} Å "
                "sanity bound — the analysis frame of reference is broken (likely "
                "whole-trimer alignment / PBC). This is INCONCLUSIVE, NOT a negative. "
                "Do not report 'no dynamics'; fix alignment and re-run.")
    vr = agg.get("vol_range_A3", float("nan"))
    sr = agg.get("sasa_range_A2", float("nan"))
    mr = agg.get("mouth_122-232_range_A", float("nan"))
    signals = [(vr == vr and vr > VOL_RANGE_DYN_A3),
               (sr == sr and sr > SASA_RANGE_DYN_A2),
               (mr == mr and mr > MOUTH_RANGE_DYN_A)]
    if any(signals):
        return ("DYNAMICS",
                "pocket shows measurable dynamics (volume/SASA/mouth fluctuate well "
                "above the noise floor; analysis verified sane).")
    return ("VALID_NEGATIVE",
            "analysis is verified sane (backbone RMSD in range) but the pocket shows "
            "no clear dynamics on this timescale — a TRUSTWORTHY negative. Consider "
            "longer sampling / a positive control before concluding rigidity.")

# Candidate (topology, trajectory, structure-label) triples, tried in order.
# The paper target (1W60) comes first; the 1AXC exploratory run that actually
# exists on disk is the fallback so `run_md_analysis.py` "just works".
def _discover() -> tuple[Path, Path, str] | None:
    cands = [
        (REPO / "data/md/1W60_solvated.pdb",   REPO / "data/md/1W60_production.dcd",  "1W60"),
        (REPO / "data/md/1W60_topology.pdb",   REPO / "data/md/1W60_production.dcd",  "1W60"),
        (REPO / "data/md/production_top.pdb",  REPO / "data/md/production.dcd",       "1W60"),
    ]
    # 1AXC 25 ns exploratory trajectory (lives in the sibling GNN_PNCA checkout)
    for root in (REPO, REPO.parent / "GNN_PNCA", REPO.parent):
        rep = root / "outputs/phase5_md/time_crunch_1axc_25ns/replicate_01"
        cands.append((rep / "solvated_initial.pdb", rep / "trajectory.dcd", "1AXC"))
    for top, traj, label in cands:
        if top.exists() and traj.exists():
            return top, traj, label
    return None


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--top", type=Path, help="Topology (.pdb). Omit to auto-discover.")
    ap.add_argument("--traj", type=Path, help="Trajectory (.dcd/.xtc). Omit to auto-discover.")
    ap.add_argument("--structure", default=None, help="Structure label (e.g. 1W60, 1AXC).")
    ap.add_argument("--stride", type=int, default=1, help="Frame stride when loading.")
    ap.add_argument("--equil-ns", type=float, default=5.0, help="Equilibration discarded.")
    ap.add_argument("--ns-per-frame", type=float, default=0.1,
                    help="Save interval (ns/frame) of the STRIDED trajectory input.")
    args = ap.parse_args()

    if args.top and args.traj:
        top, traj_path, label = args.top, args.traj, (args.structure or args.top.stem)
    else:
        found = _discover()
        if not found:
            print("ERROR: no trajectory found. Pass --top TOP.pdb --traj TRAJ.dcd.")
            print("  (Looked for data/md/1W60_production.dcd and the 1AXC 25 ns run.)")
            sys.exit(1)
        top, traj_path, label = found
        if args.structure:
            label = args.structure
        print(f"Auto-discovered {label} trajectory:\n  {traj_path}")

    out_dir = REPO / "data" / "results"
    out_dir.mkdir(parents=True, exist_ok=True)

    ns_per_frame = args.ns_per_frame * args.stride
    print(f"Loading {top.name} + {traj_path.name} (stride {args.stride}) ...")
    traj = load_trajectory(str(top), str(traj_path), stride=args.stride)
    n_prot_chains = len(protein_chain_indices(traj))
    print(f"  {traj.n_frames} frames, {traj.n_atoms} atoms, {n_prot_chains} protein chains, "
          f"{ns_per_frame:.3f} ns/frame")

    equil_frames = int(round(args.equil_ns / ns_per_frame))

    # ── per-chain pocket dynamics (all 3 subunits = informal triplicate) ─────
    pocket_by_chain = pocket_for_all_chains(traj)
    print(f"Analyzing pocket dynamics on {len(pocket_by_chain)} chains "
          f"(volume / SASA / mouth / RMSF) ...")
    res = analyze_pocket_dynamics(traj, pocket_by_chain,
                                  equil_frames=equil_frames, ns_per_frame=ns_per_frame)
    agg = res["aggregate"]
    vol_out = {
        "structure": label,
        "trajectory": str(traj_path),
        "method": "per-chain Cα convex hull + SASA + mouth distances (corrected)",
        "note": ("Convex hull is an approximate cavity proxy; use fpocket/MDpocket "
                 "for absolute volumes. Metric is per-chain (A/B interface), NOT the "
                 "whole-ring hull the previous version used."),
        "ns_per_frame": ns_per_frame,
        "equil_ns_discarded": args.equil_ns,
        "aggregate": agg,
        "chains": res["chains"],
    }
    (out_dir / "md_pocket_volume.json").write_text(json.dumps(vol_out, indent=2), encoding="utf-8")

    # ── per-residue RMSF (chain-aware: pocket vs background, averaged over chains) ─
    print("Computing per-residue RMSF (chain-aware) ...")
    prot = traj.atom_slice(traj.topology.select("protein"))
    if prot.n_frames > equil_frames:
        prot = prot[equil_frames:]
    chains = protein_chain_indices(prot)
    # accumulate per-residue RMSF over pocket residues of each chain
    residues_out, pocket_vals, bg_vals = [], [], []
    for ch in chains:
        pocket = pocket_by_chain[ch]
        # background = all this chain's residues NOT in the pocket
        all_res = sorted(int(r.resSeq) for r in prot.topology.residues
                         if r.chain.index == ch and r.is_protein)
        bg = [r for r in all_res if r not in set(pocket)]
        rseq_p, rmsf_p = pocket_rmsf(prot, ch, pocket)
        rseq_b, rmsf_b = pocket_rmsf(prot, ch, bg)
        for rs, v in zip(rseq_p.tolist(), rmsf_p.tolist()):
            residues_out.append({"chain": ch, "resid": int(rs),
                                 "rmsf_angstrom": round(float(v), 4), "in_aoh_pocket": True})
            pocket_vals.append(v)
        for rs, v in zip(rseq_b.tolist(), rmsf_b.tolist()):
            residues_out.append({"chain": ch, "resid": int(rs),
                                 "rmsf_angstrom": round(float(v), 4), "in_aoh_pocket": False})
            bg_vals.append(v)
    pocket_rmsf_mean = float(np.mean(pocket_vals)) if pocket_vals else None
    bg_rmsf_mean = float(np.mean(bg_vals)) if bg_vals else None
    fold_change = (round(pocket_rmsf_mean / bg_rmsf_mean, 3)
                   if pocket_rmsf_mean and bg_rmsf_mean else None)
    rmsf_out = {
        "source": "mdtraj per-chain aligned Cα RMSF (about mean, pocket-excluded core)",
        "structure": label, "trajectory": str(traj_path),
        "n_frames": int(prot.n_frames), "ns_per_frame": ns_per_frame,
        "pocket_rmsf_angstrom": round(pocket_rmsf_mean, 4) if pocket_rmsf_mean else None,
        "background_rmsf_angstrom": round(bg_rmsf_mean, 4) if bg_rmsf_mean else None,
        "fold_change_pocket_vs_bg": fold_change,
        "residues": residues_out,
    }
    (out_dir / "md_rmsf.json").write_text(json.dumps(rmsf_out, indent=2), encoding="utf-8")

    # ── DCCM (chain-averaged, signed, core-aligned) ──────────────────────────
    print("Computing chain-averaged DCCM ...")
    dccms, pocket_internal_vals = [], []
    for ch in chains:
        try:
            m = compute_dccm(prot, ch, pocket_by_chain[ch])
            dccms.append(m)
            # pocket-internal signed DCCM for this chain
            ca_res = [int(r.resSeq) for r in prot.topology.residues
                      if r.chain.index == ch and r.is_protein]
            want = set(pocket_by_chain[ch])
            pidx = [i for i, rs in enumerate(ca_res) if rs in want]
            if len(pidx) >= 2:
                sub = m[np.ix_(pidx, pidx)]
                pocket_internal_vals.append(float(sub[np.triu_indices(len(pidx), k=1)].mean()))
        except Exception as exc:
            print(f"  chain {ch} DCCM skipped: {exc}")
    dccm = np.mean(dccms, axis=0).astype(np.float32) if dccms else np.zeros((0, 0), np.float32)
    np.save(str(out_dir / "md_dccm.npy"), dccm)
    pocket_internal_dccm = (float(np.mean(pocket_internal_vals))
                            if pocket_internal_vals else None)

    # ── self-validating verdict (DYNAMICS / VALID_NEGATIVE / INVALID_ANALYSIS) ─
    verdict_code, verdict_msg = classify_dynamics(agg)

    # ── summary + honest ANM comparison ──────────────────────────────────────
    summary = {
        "structure": label, "trajectory": str(traj_path),
        "dynamics_verdict": {"code": verdict_code, "message": verdict_msg},
        "aggregate": agg,
        "md_rmsf": {"pocket_angstrom": rmsf_out["pocket_rmsf_angstrom"],
                    "background_angstrom": rmsf_out["background_rmsf_angstrom"],
                    "fold_change": fold_change},
        "md_dccm": {"pocket_internal": (round(pocket_internal_dccm, 4)
                                        if pocket_internal_dccm is not None else None),
                    "matrix_file": "data/results/md_dccm.npy"},
        "md_pocket_volume": {
            "mean_volume_angstrom3": round(agg["vol_mean_A3"], 1) if agg["vol_mean_A3"] == agg["vol_mean_A3"] else None,
            "max_volume_angstrom3": (round(agg["vol_mean_A3"] + agg["vol_range_A3"] / 2, 1)
                                     if agg["vol_mean_A3"] == agg["vol_mean_A3"] else None),
            "fluctuation_range_angstrom3": round(agg["vol_range_A3"], 1) if agg["vol_range_A3"] == agg["vol_range_A3"] else None,
        },
        "anm_comparison": {
            "anm_fold_change_apo_1W60": 0.857,
            "md_fold_change": fold_change,
            "note": ("ANM apo(1W60) pocket-vs-global fold-change is 0.857; the MD "
                     "fold-change here is pocket-vs-background Cα RMSF on "
                     f"{label}. Different references — compare qualitatively only."),
        },
        "caveats": [
            f"{label} exploratory MD; short timescale. No 8GLA positive control in this run.",
            "Convex-hull volume is an approximate proxy, not an absolute cavity volume.",
            "RMSF/SASA fluctuation shows the pocket is dynamic; it does NOT by itself "
            "prove a full cryptic opening event.",
        ],
    }
    (out_dir / "md_apo_comparison.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    # ── verdict ──────────────────────────────────────────────────────────────
    def f(x, d=1):
        return f"{x:.{d}f}" if isinstance(x, (int, float)) and x == x else "n/a"
    print("\n" + "=" * 66)
    print(f"  POCKET DYNAMICS — {label}  (per-chain, corrected)")
    print("=" * 66)
    print(f"  backbone RMSD (sanity) : mean {f(agg['backbone_rmsd_mean_A'],2)} Å   "
          f"[PBC/align sane: {agg['pbc_sane']}]")
    print(f"  pocket volume          : mean {f(agg['vol_mean_A3'],0)} Å³   "
          f"fluctuation range {f(agg['vol_range_A3'],0)} Å³   (CV {f(agg['vol_cv'],3)})")
    print(f"  pocket SASA range      : {f(agg['sasa_range_A2'],0)} Å²")
    print(f"  mouth 122-232 open/close: {f(agg.get('mouth_122-232_range_A'),2)} Å")
    print(f"  pocket Cα RMSF (mean)  : {f(agg['pocket_rmsf_mean_A'],2)} Å   "
          f"fold vs background {f(fold_change,3) if fold_change else 'n/a'}")
    banner = {"DYNAMICS": "✔ POCKET HAS MEASURABLE DYNAMICS",
              "VALID_NEGATIVE": "○ NO DYNAMICS (verified-sane negative)",
              "INVALID_ANALYSIS": "✗ ANALYSIS INVALID — inconclusive, NOT a negative"}[verdict_code]
    print("-" * 66)
    print(f"  VERDICT [{verdict_code}]: {banner}")
    print(f"  {verdict_msg}")
    print("=" * 66)
    print(f"\nWrote md_pocket_volume.json, md_rmsf.json, md_dccm.npy, md_apo_comparison.json → {out_dir}")


if __name__ == "__main__":
    main()
