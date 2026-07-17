#!/usr/bin/env python
"""
PBC-correct analysis + positive-control comparison for the PCNA MD validation.

Reads outputs/{1W60,8GLA}/rep*/production.dcd (topology = system_solvated.pdb) and:
  1. Images periodic boundaries BEFORE superposition  (fixes the old 25-A RMSD artifact).
  2. Superposes on a stable core = protein Ca EXCLUDING the pocket (no circularity).
  3. RMSF about the MEAN position, after discarding equilibration.
  4. Pocket-openness proxies: pocket SASA, pocket-Ca radius of gyration, cross-wall distances.
  5. POSITIVE CONTROL: is the 8GLA (open) pocket measurably larger than the 1W60 (closed)
     pocket? If NOT, the method/sampling can't see opening and a "no-opening" result on apo
     is UNINTERPRETABLE — not a real negative. This is the gate that stops a false negative.

Outputs: outputs/analysis/{summary.json, per_replicate.csv, REPORT.md, *.png}
"""
from __future__ import annotations
import json, sys
from pathlib import Path

POCKET = {  # AOH1996 pocket residues, 8GLA chains A+B (== run_md.py)
    0: [25,26,27,38,39,40,41,42,44,45,46,47,123,125,126,128,231,232,233,234,250,251,252,253],
    1: [23,25,26,27,38,39,40,41,42,44,45,46,47,123,125,126,128,231,232,233,234,250,251,252],
}
EQUIL_NS = 5.0  # discard before RMSF/pocket stats


def _imports():
    try:
        import mdtraj as md, numpy as np, pandas as pd
        import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    except Exception as exc:
        sys.exit("Missing deps. `conda activate pcna-md-4070` first. (%s)" % exc)
    return md, np, pd, plt


def pocket_selection(top, md):
    sel = []
    for cidx, resseqs in POCKET.items():
        if cidx >= top.n_chains:
            continue
        for a in top.atoms:
            if a.residue.chain.index == cidx and a.residue.resSeq in resseqs:
                sel.append(a.index)
    return sorted(sel)


def _parse_log_times(log_path: Path):
    """Return the 'Time (ps)' column from an OpenMM StateDataReporter log (tab-separated)."""
    try:
        lines = [ln for ln in log_path.read_text().splitlines() if ln.strip()]
    except Exception:
        return []
    if not lines:
        return []
    header = lines[0].lstrip("#").split("\t")
    tcol = next((i for i, h in enumerate(header) if "Time (ps)" in h), None)
    if tcol is None:
        return []
    times = []
    for ln in lines[1:]:
        parts = ln.split("\t")
        if len(parts) > tcol:
            try:
                times.append(float(parts[tcol]))
            except ValueError:
                pass
    return times


def _frame_interval_ns(rep_dir: Path, np, hint: float):
    """Read the ACTUAL ns-per-frame from run metadata/log; fall back to hint. -> (dt_ns, source)."""
    # 1) run manifest written by run_md.py records the DCD/log save interval (report_ps)
    done = rep_dir / "DONE.json"
    if done.exists():
        try:
            rp = json.loads(done.read_text()).get("report_ps")
            if rp:
                return float(rp) / 1000.0, "DONE.json:report_ps"
        except Exception:
            pass
    # 2) otherwise derive it from the spacing of the production.log 'Time (ps)' column
    times = _parse_log_times(rep_dir / "production.log")
    if len(times) >= 2:
        d = float(np.median(np.diff(np.asarray(times[:12]))))  # ps between reported frames
        if d > 0:
            return d / 1000.0, "production.log:time-column"
    return float(hint), "hint(fallback)"


def analyze_replicate(dcd: Path, top_pdb: Path, ns_per_frame_hint=0.05):
    md, np, pd, _ = _imports()
    traj = md.load(str(dcd), top=str(top_pdb))
    # 1) PBC fix BEFORE anything else
    try:
        traj.image_molecules(inplace=True)
    except Exception:
        traj.make_molecules_whole(inplace=True)
    protein = traj.atom_slice(traj.top.select("protein"))
    ca = protein.top.select("name CA")
    pocket_atoms = pocket_selection(protein.top, md)
    pocket_ca = [i for i in pocket_atoms if protein.top.atom(i).name == "CA"]
    # 2) align on core Ca that EXCLUDES the pocket (no circularity)
    pocket_ca_set = set(pocket_ca)
    core = np.array([i for i in ca if i not in pocket_ca_set])
    protein.superpose(protein, frame=0, atom_indices=core, ref_atom_indices=core)
    # frames -> ns: read the ACTUAL save interval from the run manifest/log (not hardcoded)
    dt_ns, dt_src = _frame_interval_ns(dcd.parent, np, ns_per_frame_hint)
    n = protein.n_frames
    equil = int(EQUIL_NS / dt_ns)
    if n > equil:
        prod = protein[equil:]
        equil_used = equil
    else:
        # Trajectory is shorter than the equilibration window -> we cannot discard it without
        # throwing away everything. Keep it, but say so loudly (was silently swallowed before).
        print(f"[warn] {dcd.parent.name}: only {n} frames (~{n*dt_ns:.1f} ns @ "
              f"{dt_ns:.4f} ns/frame, src={dt_src}) <= equilibration cutoff {equil} frames "
              f"({EQUIL_NS} ns) -> equilibration NOT discarded for this replicate.")
        prod = protein
        equil_used = 0
    # 3) backbone RMSD (sanity) + pocket RMSF about the mean
    rmsd = md.rmsd(protein, protein, 0, atom_indices=core)  # nm
    rmsd_prod = rmsd[equil_used:]
    if rmsd_prod.size == 0:            # guard against an empty slice -> nan
        rmsd_prod = rmsd
    mean_xyz = prod.xyz[:, pocket_ca, :].mean(axis=0)
    rmsf = np.sqrt(((prod.xyz[:, pocket_ca, :] - mean_xyz) ** 2).sum(axis=2).mean(axis=0))  # nm
    # 4) pocket openness proxies, computed PER CHAIN and then averaged across chains -- never
    #    summed across A+B, which would dilute the local opening signal with the A<->B
    #    rigid-body separation and conflate two distinct interface pockets.
    sasa_res = md.shrake_rupley(prod, mode="residue")  # nm^2 per residue
    pocket_res_by_chain = {}
    for i in pocket_atoms:
        res = protein.top.atom(i).residue
        pocket_res_by_chain.setdefault(res.chain.index, set()).add(res.index)
    per_chain_sasa = []   # each row: one chain's pocket SASA summed WITHIN that chain, per frame
    for cidx in sorted(pocket_res_by_chain):
        per_chain_sasa.append(sasa_res[:, sorted(pocket_res_by_chain[cidx])].sum(axis=1))
    per_chain_sasa = np.array(per_chain_sasa)          # (n_chains, n_frames)
    pocket_sasa = per_chain_sasa.mean(axis=0)          # per-chain-averaged openness, per frame
    # per-chain pocket-Ca Rg (within a chain), then averaged -> no cross-chain separation term
    rg_list = []
    for cidx in sorted(pocket_res_by_chain):
        ca_this = [i for i in pocket_ca if protein.top.atom(i).residue.chain.index == cidx]
        if ca_this:
            rg_list.append(md.compute_rg(prod.atom_slice(ca_this)))
    rg_pocket = (np.mean(np.array(rg_list), axis=0) if rg_list
                 else md.compute_rg(prod.atom_slice(pocket_ca)))
    return {
        "n_frames": int(n), "equil_frames": int(equil_used),
        "dt_ns": float(dt_ns), "dt_source": dt_src,
        "equil_ns_actual": float(equil_used * dt_ns),
        "n_pocket_chains": int(len(per_chain_sasa)),
        "rmsd_mean_nm": float(rmsd_prod.mean()), "rmsd_max_nm": float(rmsd.max()),
        "pocket_rmsf_mean_nm": float(rmsf.mean()), "pocket_rmsf_max_nm": float(rmsf.max()),
        "pocket_sasa_mean_nm2": float(pocket_sasa.mean()), "pocket_sasa_std_nm2": float(pocket_sasa.std()),
        "pocket_sasa_max_nm2": float(pocket_sasa.max()),
        "pocket_rg_mean_nm": float(rg_pocket.mean()), "pocket_rg_max_nm": float(rg_pocket.max()),
        "pbc_sane": bool(rmsd.max() < 0.6),   # >0.6 nm backbone RMSD => suspect PBC/blowup
        "_sasa_series": pocket_sasa.tolist(),
    }


def main():
    md, np, pd, plt = _imports()
    out = Path("outputs"); adir = out / "analysis"; adir.mkdir(parents=True, exist_ok=True)
    rows, sasa_pool = [], {}
    for pdb in ["1W60", "8GLA"]:
        base = out / pdb
        top = base / "system_solvated.pdb"
        if not top.exists():
            print(f"[skip] {pdb}: no system_solvated.pdb (run run_md.py --pdb {pdb})"); continue
        sasa_pool[pdb] = []
        for rep_dir in sorted(base.glob("rep*")):
            dcd = rep_dir / "production.dcd"
            if not dcd.exists() or dcd.stat().st_size < 100_000:
                print(f"[skip] {pdb}/{rep_dir.name}: missing/empty DCD"); continue
            print(f"[analyze] {pdb}/{rep_dir.name} ...")
            r = analyze_replicate(dcd, top)
            sasa_pool[pdb].extend(r.pop("_sasa_series"))
            r.update({"pdb": pdb, "replicate": rep_dir.name}); rows.append(r)

    if not rows:
        sys.exit("No trajectories analyzed. Run run_md.py for 1W60 and 8GLA first.")
    df = pd.DataFrame(rows)
    df.to_csv(adir / "per_replicate.csv", index=False)

    # ---- positive-control gate: 8GLA(open) pocket SASA vs 1W60(closed) ----
    verdict = {"interpretable": False, "reason": "insufficient data"}
    if sasa_pool.get("1W60") and sasa_pool.get("8GLA"):
        apo = np.array(sasa_pool["1W60"]); holo = np.array(sasa_pool["8GLA"])
        sep = float(holo.mean() - apo.mean())
        # Cohen's d effect size (see CAVEAT below: this is over autocorrelated pooled frames)
        pooled_sd = np.sqrt((apo.std()**2 + holo.std()**2) / 2) or 1e-9
        d = sep / pooled_sd
        # The independent statistical unit is the REPLICATE, not the frame. Require the opening
        # to hold per-replicate (every holo replicate mean above the apo replicate median) so a
        # single lucky replicate or frame autocorrelation cannot carry the gate.
        apo_reps = [r["pocket_sasa_mean_nm2"] for r in rows if r["pdb"] == "1W60"]
        holo_reps = [r["pocket_sasa_mean_nm2"] for r in rows if r["pdb"] == "8GLA"]
        n_apo, n_holo = len(apo_reps), len(holo_reps)
        apo_med = float(np.median(apo_reps)) if apo_reps else float("nan")
        per_rep_ok = bool(holo_reps and apo_reps and all(h > apo_med for h in holo_reps))
        control_ok = (holo.mean() > apo.mean()) and (abs(d) > 0.5) and per_rep_ok
        verdict = {
            "interpretable": bool(control_ok),
            "apo_pocket_sasa_nm2": float(apo.mean()), "holo_pocket_sasa_nm2": float(holo.mean()),
            "holo_minus_apo_nm2": sep, "cohens_d": float(d),
            "cohens_d_caveat": ("Cohen's d is computed on autocorrelated MD frames pooled across "
                                "replicates; it is a DESCRIPTIVE effect size, not an n=frames "
                                "hypothesis test. The independent unit is the replicate."),
            "n_apo_replicates": n_apo, "n_holo_replicates": n_holo,
            "apo_replicate_means_nm2": [float(x) for x in apo_reps],
            "holo_replicate_means_nm2": [float(x) for x in holo_reps],
            "per_replicate_consistent": per_rep_ok,
            "reason": (("Positive control PASSED: the holo(open) pocket reads larger than "
                        "apo(closed) in the pooled SASA (Cohen's d %.2f) AND in every holo "
                        "replicate vs the apo median (%d holo / %d apo replicates) -> the metric "
                        "can detect opening, so an apo result is trustworthy. CAVEAT: Cohen's d "
                        "is over autocorrelated pooled frames (descriptive only); the real "
                        "statistical unit is the replicate." % (d, n_holo, n_apo)) if control_ok else
                       ("Positive control FAILED: holo and apo pockets are not cleanly separated "
                        "by this metric/sampling (pooled Cohen's d %.2f; per-replicate "
                        "consistent=%s over %d holo / %d apo replicates) -> DO NOT report apo as a "
                        "negative; extend sampling or use fpocket/MDpocket/enhanced sampling. "
                        "NOTE: Cohen's d here is over autocorrelated pooled frames (descriptive "
                        "only); the real statistical unit is the replicate."
                        % (d, per_rep_ok, n_holo, n_apo))),
        }
        # plot SASA distributions
        plt.figure(figsize=(6,4))
        plt.hist(apo, bins=40, alpha=0.6, label="1W60 apo (closed)")
        plt.hist(holo, bins=40, alpha=0.6, label="8GLA holo (open, ligand stripped)")
        plt.xlabel("AOH1996 pocket SASA (nm^2)"); plt.ylabel("frames"); plt.legend()
        plt.title("Positive control: pocket openness, holo vs apo"); plt.tight_layout()
        plt.savefig(adir / "pocket_sasa_control.png", dpi=140); plt.close()

    summary = {"per_replicate": rows, "positive_control": verdict,
               "equil_ns_discarded": EQUIL_NS,
               "all_pbc_sane": bool(df["pbc_sane"].all())}
    (adir / "summary.json").write_text(json.dumps(summary, indent=2))

    # ---- human-readable report ----
    lines = ["# PCNA MD validation — analysis report", "",
             f"PBC sanity (all replicates RMSD<0.6 nm): **{summary['all_pbc_sane']}**", "",
             "## Per-replicate", "",
             "| pdb | rep | RMSD mean (nm) | pocket RMSF mean (nm) | pocket SASA mean (nm^2) | PBC ok |",
             "|---|---|---|---|---|---|"]
    for r in rows:
        lines.append(f"| {r['pdb']} | {r['replicate']} | {r['rmsd_mean_nm']:.3f} | "
                     f"{r['pocket_rmsf_mean_nm']:.3f} | {r['pocket_sasa_mean_nm2']:.1f} | {r['pbc_sane']} |")
    lines += ["", "## Positive-control gate (the anti-false-negative check)", "",
              f"- apo  (1W60) pocket SASA:  {verdict.get('apo_pocket_sasa_nm2','n/a')}",
              f"- holo (8GLA) pocket SASA:  {verdict.get('holo_pocket_sasa_nm2','n/a')}",
              f"- holo - apo: {verdict.get('holo_minus_apo_nm2','n/a')}  (Cohen's d {verdict.get('cohens_d','n/a')})",
              f"- independent replicates behind the gate: {verdict.get('n_holo_replicates','n/a')} holo / "
              f"{verdict.get('n_apo_replicates','n/a')} apo; per-replicate consistent: "
              f"{verdict.get('per_replicate_consistent','n/a')}",
              f"- **Interpretable: {verdict['interpretable']}**", f"- {verdict['reason']}",
              f"- _Caveat:_ {verdict.get('cohens_d_caveat','')}", ""]
    (adir / "REPORT.md").write_text("\n".join(lines))
    print("\n".join(lines))
    print(f"\nWrote {adir/'REPORT.md'}, summary.json, per_replicate.csv, pocket_sasa_control.png")


if __name__ == "__main__":
    main()
