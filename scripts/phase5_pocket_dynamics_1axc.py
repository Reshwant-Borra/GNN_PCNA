#!/usr/bin/env python
"""Phase 5 1AXC — pocket-dynamics metrics (geometry, not just CA RMSF).

Answers 'does the pocket have dynamics' with metrics RMSF alone cannot give:
  - heavy-atom RMSF (sidechain gating, not just backbone)
  - per-region SASA time series (opening = SASA increases / fluctuates)
  - per-region radius of gyration time series (breathing)
  - front-face pocket cross-wall CA distances (mouth opening/closing)

Exploratory triage only. rep1 (full 25 ns) only; 5 ns equilibration discarded.
Computed per monomer (chains 0/1/2) as informal triplicates. METRICS ONLY — any
supports/weakens conclusion is gated on human MD-interpretation review (doc 26).
"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np, pandas as pd, mdtraj as md

RUN = Path("outputs/phase5_md/time_crunch_1axc_25ns")
REP = RUN / "replicate_01"
EQUIL_FRAMES = 50          # 5 ns @ 0.1 ns/frame
NS_PER_FRAME = 0.1
OUT = RUN / "analysis_fixed"
OUT.mkdir(parents=True, exist_ok=True)

def expand(spec):
    out = []
    for part in spec:
        a, b = part.split("-"); out += list(range(int(a), int(b) + 1))
    return sorted(set(out))

REGIONS = {
    "front_face_pip_pocket": expand(["40-44", "117-135", "230-235", "251-253"]),
    "cand_239-243": expand(["239-243"]),
    "cand_28-32":   expand(["28-32"]),
    "cand_206-210": expand(["206-210"]),
    "cand_134-138": expand(["134-138"]),
    "ref_118-122":  expand(["118-122"]),
}
# canonical front-face cross-wall CA pairs (pocket mouth)
CROSS_PAIRS = [(44, 251), (122, 232), (128, 252), (42, 234)]

print("loading rep1 ...")
traj = md.load_dcd(str(REP / "trajectory.dcd"), top=str(REP / "solvated_initial.pdb"))
traj.make_molecules_whole(inplace=True)
traj.image_molecules(inplace=True)

# protein-only copy for SASA/Rg speed
prot_idx = traj.topology.select("protein")
prot = traj.atom_slice(prot_idx)
# align protein on core CA (exclude analyzed regions) to remove rigid drift
analyzed = set(sum(REGIONS.values(), []))
core_ca = prot.topology.select(
    "name CA and protein and not (resSeq " + " ".join(str(r) for r in sorted(analyzed)) + ")")
prot.superpose(prot, 0, atom_indices=core_ca)
prot = prot[EQUIL_FRAMES:]
n = prot.n_frames
print(f"frames after equil: {n}")

chains = sorted({r.chain.index for r in prot.topology.residues if r.is_protein})
print("protein chains:", chains)

# per-residue SASA once (mode='residue'): shape (frames, n_residues)
print("computing SASA (Shrake-Rupley) ...")
sasa = md.shrake_rupley(prot, mode="residue")        # nm^2
res_list = list(prot.topology.residues)
resindex_of = {r.index: i for i, r in enumerate(res_list)}

def region_res_indices(ch, resseqs):
    s = set(resseqs)
    return [r.index for r in prot.topology.residues
            if r.is_protein and r.chain.index == ch and int(r.resSeq) in s]

rows, sasa_ts_rows = [], []
for name, resseqs in REGIONS.items():
    for ch in chains:
        ridx = region_res_indices(ch, resseqs)
        if not ridx:
            continue
        heavy = prot.topology.select(
            "chainid %d and not element H and (resSeq %s)"
            % (ch, " ".join(str(r) for r in resseqs)))
        # heavy-atom RMSF about mean
        xyz = prot.xyz[:, heavy, :]
        rmsf = np.sqrt(np.mean(np.sum((xyz - xyz.mean(0)) ** 2, axis=2), axis=0))
        # region SASA (sum over residues) per frame, nm^2 -> A^2
        cols = [resindex_of[i] for i in ridx]
        reg_sasa = sasa[:, cols].sum(axis=1) * 100.0
        # region Rg (heavy atoms) per frame
        sub = prot.atom_slice(heavy)
        rg = md.compute_rg(sub) * 10.0  # nm -> A
        rows.append({
            "region": name, "chain": ch, "n_res": len(ridx),
            "heavy_rmsf_mean_A": float(np.mean(rmsf) * 10),
            "heavy_rmsf_max_A": float(np.max(rmsf) * 10),
            "sasa_mean_A2": float(reg_sasa.mean()),
            "sasa_std_A2": float(reg_sasa.std()),
            "sasa_cv": float(reg_sasa.std() / reg_sasa.mean()) if reg_sasa.mean() else float("nan"),
            "sasa_range_A2": float(reg_sasa.max() - reg_sasa.min()),
            "rg_mean_A": float(rg.mean()),
            "rg_std_A": float(rg.std()),
        })
        for fi in range(n):
            sasa_ts_rows.append({"region": name, "chain": ch, "frame": fi + EQUIL_FRAMES,
                                 "time_ns": (fi + EQUIL_FRAMES) * NS_PER_FRAME,
                                 "sasa_A2": float(reg_sasa[fi])})

df = pd.DataFrame(rows)
df.to_csv(OUT / "pocket_dynamics_summary.csv", index=False)
pd.DataFrame(sasa_ts_rows).to_csv(OUT / "pocket_sasa_timeseries.csv", index=False)

# cross-wall CA distances (per chain), front-face pocket mouth
dist_rows = []
for ch in chains:
    for a, b in CROSS_PAIRS:
        ia = prot.topology.select(f"chainid {ch} and resSeq {a} and name CA")
        ib = prot.topology.select(f"chainid {ch} and resSeq {b} and name CA")
        if len(ia) == 0 or len(ib) == 0:
            continue
        d = md.compute_distances(prot, [[ia[0], ib[0]]])[:, 0] * 10.0  # A
        dist_rows.append({"chain": ch, "pair": f"{a}-{b}",
                          "mean_A": float(d.mean()), "std_A": float(d.std()),
                          "min_A": float(d.min()), "max_A": float(d.max()),
                          "range_A": float(d.max() - d.min())})
dist_df = pd.DataFrame(dist_rows)
dist_df.to_csv(OUT / "pocket_crosswall_distances.csv", index=False)

pd.set_option("display.width", 200, "display.max_columns", 20)
print("\n=== PER-REGION DYNAMICS (rep1, 3 monomers) ===")
agg = df.groupby("region").agg(
    heavy_rmsf_A=("heavy_rmsf_mean_A", "mean"),
    sasa_mean_A2=("sasa_mean_A2", "mean"),
    sasa_std_A2=("sasa_std_A2", "mean"),
    sasa_cv=("sasa_cv", "mean"),
    sasa_range_A2=("sasa_range_A2", "mean"),
    rg_std_A=("rg_std_A", "mean"),
).reset_index()
print(agg.to_string(index=False))
print("\n=== FRONT-FACE POCKET CROSS-WALL CA DISTANCES (mean over chains) ===")
if not dist_df.empty:
    print(dist_df.groupby("pair").agg(mean_A=("mean_A", "mean"), std_A=("std_A", "mean"),
                                      range_A=("range_A", "mean")).reset_index().to_string(index=False))
print(f"\nOutputs -> {OUT}")
