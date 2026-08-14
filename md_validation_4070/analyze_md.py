#!/usr/bin/env python
"""
PBC-correct analysis + positive-control comparison for the PCNA MD validation (v2).

Reads outputs/{APO,CONTROL}/rep*/production.dcd (topology = system_solvated.pdb) and:
  1. Images periodic boundaries BEFORE superposition  (fixes the old 25-A RMSD artifact).
  2. Superposes on a stable core = protein Ca EXCLUDING the pocket (no circularity).
  3. RMSF about the MEAN position, after discarding equilibration.
  4. Pocket-openness proxies: pocket SASA, pocket-Ca radius of gyration.
  5. POSITIVE CONTROL: is the CONTROL (open) pocket measurably larger than the APO (closed)
     pocket? If NOT, the method/sampling can't see opening and a "no-opening" apo result is
     UNINTERPRETABLE - not a real negative. This is the gate that stops a false negative.

  === v2 changes (2026-07 biological-validity audit) ===
  * Pocket residues + apo/control PDBs + interface chains come from pockets/<name>.json
    (single source of truth shared with run_md.py; the old hand-curated list that dropped
    IDCL contacts 121/124/129/131 is gone).
  * PBC-artifact detection is now a frame-to-frame JUMP detector (a box-hop is a spike), not a
    blanket 0.6 nm cap that also trips on legitimate large-amplitude motion. Smooth large drift
    is reported separately as info, not a failure.
  * Reads prep_audit.json and surfaces low-resolution / rebuilt-residue caveats in the report
    (e.g. 8GLA is 3.77 A) so a PASS/FAIL is never read without that context.

Outputs: outputs/analysis/{summary.json, per_replicate.csv, REPORT.md, *.png}
"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
EQUIL_NS = 5.0  # discard before RMSF/pocket stats
PBC_JUMP_NM = 0.30   # frame-to-frame backbone RMSD jump above which a PBC/imaging artifact is suspected
DRIFT_INFO_NM = 0.60  # smooth drift above this is reported (info only, NOT a failure)


def load_pocket(name: str) -> dict:
    p = HERE / "pockets" / f"{name}.json"
    if not p.exists():
        sys.exit(f"No pocket definition at {p}.")
    return json.loads(p.read_text())


def _imports():
    try:
        import mdtraj as md, numpy as np, pandas as pd
        import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    except Exception as exc:
        sys.exit("Missing deps. `conda activate pcna-md-4070` first. (%s)" % exc)
    return md, np, pd, plt


def pocket_selection(top, resseqs, interface_chain_indices, allow_keys=None):
    """Atom indices of pocket residues on the interface chains (by chain ORDER, post-assembly).

    ``allow_keys``, when given, is an explicit set of ``(chain_index, resSeq)`` pairs and
    overrides the chain x resseq product. Pass the apo/control INTERSECTION here so both
    trajectories are measured over the identical atom set -- see :func:`resolved_pocket_keys`.
    """
    want_chains = set(interface_chain_indices)
    resset = set(resseqs)
    sel = []
    for a in top.atoms:
        if allow_keys is not None:
            if (a.residue.chain.index, a.residue.resSeq, a.name) in allow_keys:
                sel.append(a.index)
        elif a.residue.chain.index in want_chains and a.residue.resSeq in resset:
            sel.append(a.index)
    return sorted(sel)


def resolved_pocket_keys(top, resseqs, interface_chain_indices):
    """The ``(chain_index, resSeq, atom_name)`` pocket ATOMS present in this topology.

    Atom-level, not residue-level, deliberately. SASA is a per-atom quantity, and apo and
    control were measured to resolve the SAME 56 pocket residues but 854 vs 855 atoms --
    protonation and terminal/rebuilt side-chain differences survive a residue-level check.
    """
    want_chains = set(interface_chain_indices)
    resset = set(resseqs)
    return {(a.residue.chain.index, a.residue.resSeq, a.name) for a in top.atoms
            if a.residue.chain.index in want_chains and a.residue.resSeq in resset}


def resolved_pocket_residues(top, resseqs, interface_chain_indices):
    """The ``(chain_index, resSeq)`` pocket residues present -- for human-readable reporting."""
    return {(c, r) for c, r, _ in resolved_pocket_keys(top, resseqs, interface_chain_indices)}


def _protein_top(md, top_pdb: Path):
    """Protein-only topology, matching the slice analyze_replicate performs."""
    t = md.load(str(top_pdb))
    return t.atom_slice(t.top.select("protein")).top


def terminal_or_gap_adjacent(top):
    """``(chain_index, resSeq)`` residues at a chain end or beside a numbering gap.

    Their solvent exposure is dominated by bookkeeping, not by pocket conformation: a
    residue that is internal in one structure and a chain terminus in the other gains a
    whole exposed face plus an OXT. Measured on the real prepared assemblies, residue 254
    LYS was 0.920 nm^2 in apo (internal) but 2.416 nm^2 in the control (chain end) -- a
    +1.496 nm^2 difference from terminus status alone, against only +0.435 nm^2 of genuine
    structural difference summed over the other 22 pocket residues. Differencing those is
    measuring where the crystal stopped, not whether the pocket opened.
    """
    out = set()
    for ch in top.chains:
        res = sorted(ch.residues, key=lambda r: r.resSeq)
        if not res:
            continue
        out.add((ch.index, res[0].resSeq))
        out.add((ch.index, res[-1].resSeq))
        for a, b in zip(res, res[1:]):
            if b.resSeq - a.resSeq > 1:            # unresolved loop between them
                out.add((ch.index, a.resSeq))
                out.add((ch.index, b.resSeq))
    return out


def pocket_parity(md, role_tops: dict, resseqs, iface, min_coverage=0.80,
                  exclude_termini=True):
    """Intersect the pocket residues resolved in every role's topology.

    Apo and control are DIFFERENT crystal structures with different unmodelled regions --
    8GLA (3.77 A) lacks residues 1W60 resolves. Measuring pocket SASA over different atom
    sets makes ``control - apo`` a comparison of two different pockets: the missing
    residue's own SASA enters as an additive bias, which was large enough to INVERT the
    sign of the positive-control gate at analyze_md.py's ``holo.mean() > apo.mean()``.

    Returns ``(allow_keys, report)``. Hard-fails below ``min_coverage`` because past that
    point the intersection is no longer the pocket the GNN identified.
    """
    per_role = {role: resolved_pocket_keys(top, resseqs, iface) for role, top in role_tops.items()}
    common = set.intersection(*per_role.values()) if per_role else set()
    union = set().union(*per_role.values()) if per_role else set()

    excluded_termini = set()
    if exclude_termini and role_tops:
        bad_res = set().union(*(terminal_or_gap_adjacent(t) for t in role_tops.values()))
        excluded_termini = {(c, s) for c, s, _ in common if (c, s) in bad_res}
        if excluded_termini:
            common = {k for k in common if (k[0], k[1]) not in bad_res}
            print(f"[parity] excluding {len(excluded_termini)} terminus/gap-adjacent residue(s) "
                  "whose SASA reflects where the crystal ends, not pocket opening: "
                  + ", ".join(f"chain{c}:{s}" for c, s in sorted(excluded_termini)))
            if not common:
                sys.exit("[parity] FATAL: every pocket residue is a chain terminus or beside an "
                         "unresolved gap. There is nothing left to measure. Re-derive the pocket "
                         "or pass --keep-termini and interpret the result with that caveat.")
    dropped = {role: sorted(keys - common) for role, keys in per_role.items()}
    coverage = (len(common) / len(union)) if union else 0.0
    res_per_role = {r: {(c, s) for c, s, _ in k} for r, k in per_role.items()}
    common_res = {(c, s) for c, s, _ in common}
    report = {
        "granularity": "atom (chain_index, resSeq, atom_name)",
        "per_role_atoms": {r: len(k) for r, k in per_role.items()},
        "per_role_residues": {r: len(k) for r, k in res_per_role.items()},
        "common_atoms": len(common), "union_atoms": len(union),
        "common_residues": len(common_res),
        "atom_coverage": round(coverage, 4),
        "excluded_terminus_or_gap_adjacent": sorted(f"chain{c}:{s}" for c, s in excluded_termini),
        "dropped_per_role": {r: [f"chain{c}:{s}:{n}" for c, s, n in d] for r, d in dropped.items()},
    }
    for role, d in dropped.items():
        if d:
            print(f"[parity] {role}: dropping {len(d)} atom(s) absent from another role: "
                  + ", ".join(f"chain{c}:{s}:{n}" for c, s, n in d[:12])
                  + (" ..." if len(d) > 12 else ""))
    if union and coverage < min_coverage:
        sys.exit(f"[parity] FATAL: apo/control share only {len(common)}/{len(union)} pocket "
                 f"atoms ({coverage:.0%} < {min_coverage:.0%}). The structures do not resolve "
                 f"the same pocket, so control-minus-apo would not be a comparison of the same "
                 f"site. Details: {json.dumps(report, indent=2)}")
    print(f"[parity] measuring both roles over {len(common)} shared atoms "
          f"({len(common_res)} residues, {coverage:.1%} of the union)")
    return common, report


def analyze_replicate(dcd: Path, top_pdb: Path, resseqs, interface_chain_indices,
                      ns_per_frame_hint=0.05, allow_keys=None):
    md, np, pd, _ = _imports()
    traj = md.load(str(dcd), top=str(top_pdb))
    # 1) PBC fix BEFORE anything else
    try:
        traj.image_molecules(inplace=True)
    except Exception:
        traj.make_molecules_whole(inplace=True)
    protein = traj.atom_slice(traj.top.select("protein"))
    ca = protein.top.select("name CA")
    pocket_atoms = pocket_selection(protein.top, resseqs, interface_chain_indices,
                                    allow_keys=allow_keys)
    if not pocket_atoms:
        sys.exit(f"[analyze] FATAL: empty pocket selection for {dcd} — "
                 f"resseqs={sorted(set(resseqs))[:8]}... chains={interface_chain_indices}. "
                 f"An empty selection must fail loudly, not silently produce NaN metrics.")
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
        prod = protein[equil:]; equil_used = equil
    else:
        print(f"[warn] {dcd.parent.name}: only {n} frames (~{n*dt_ns:.1f} ns @ "
              f"{dt_ns:.4f} ns/frame, src={dt_src}) <= equilibration cutoff {equil} frames "
              f"({EQUIL_NS} ns) -> equilibration NOT discarded for this replicate.")
        prod = protein; equil_used = 0
    # 3) backbone RMSD (sanity) + pocket RMSF about the mean
    rmsd = md.rmsd(protein, protein, 0, atom_indices=core)  # nm
    rmsd_prod = rmsd[equil_used:]
    if rmsd_prod.size == 0:
        rmsd_prod = rmsd
    # --- PBC artifact = a discontinuous single-frame jump; real motion is smooth (audit fix) ---
    frame_jumps = np.abs(np.diff(rmsd)) if rmsd.size > 1 else np.array([0.0])
    max_jump_nm = float(frame_jumps.max()) if frame_jumps.size else 0.0
    pbc_artifact_suspected = bool(max_jump_nm > PBC_JUMP_NM)
    large_smooth_drift = bool(rmsd.max() > DRIFT_INFO_NM and not pbc_artifact_suspected)
    mean_xyz = prod.xyz[:, pocket_ca, :].mean(axis=0)
    rmsf = np.sqrt(((prod.xyz[:, pocket_ca, :] - mean_xyz) ** 2).sum(axis=2).mean(axis=0))  # nm
    # 4) pocket openness proxies, PER CHAIN then averaged (never summed across chains)
    sasa_res = md.shrake_rupley(prod, mode="residue")  # nm^2 per residue
    pocket_res_by_chain = {}
    for i in pocket_atoms:
        res = protein.top.atom(i).residue
        pocket_res_by_chain.setdefault(res.chain.index, set()).add(res.index)
    per_chain_sasa = []
    for cidx in sorted(pocket_res_by_chain):
        per_chain_sasa.append(sasa_res[:, sorted(pocket_res_by_chain[cidx])].sum(axis=1))
    per_chain_sasa = np.array(per_chain_sasa)
    pocket_sasa = per_chain_sasa.mean(axis=0)
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
        "max_frame_jump_nm": max_jump_nm,
        "pbc_artifact_suspected": pbc_artifact_suspected,
        "large_smooth_drift": large_smooth_drift,
        "pocket_rmsf_mean_nm": float(rmsf.mean()), "pocket_rmsf_max_nm": float(rmsf.max()),
        "pocket_sasa_mean_nm2": float(pocket_sasa.mean()), "pocket_sasa_std_nm2": float(pocket_sasa.std()),
        "pocket_sasa_max_nm2": float(pocket_sasa.max()),
        "pocket_rg_mean_nm": float(rg_pocket.mean()), "pocket_rg_max_nm": float(rg_pocket.max()),
        "_sasa_series": pocket_sasa.tolist(),
    }


def _parse_log_times(log_path: Path):
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
    done = rep_dir / "DONE.json"
    if done.exists():
        try:
            rp = json.loads(done.read_text()).get("report_ps")
            if rp:
                return float(rp) / 1000.0, "DONE.json:report_ps"
        except Exception:
            pass
    times = _parse_log_times(rep_dir / "production.log")
    if len(times) >= 2:
        d = float(np.median(np.diff(np.asarray(times[:12]))))
        if d > 0:
            return d / 1000.0, "production.log:time-column"
    return float(hint), "hint(fallback)"


def _prep_caveat(out: Path, pdb: str):
    """Surface resolution / rebuilt-residue caveats from prep_audit.json (audit medium finding)."""
    ap = out / pdb / "prep" / "prep_audit.json"
    if not ap.exists():
        return None
    try:
        a = json.loads(ap.read_text())
        return {"pdb": pdb, "assembly": a.get("assembly"),
                "internal_residues_rebuilt": a.get("internal_missing_residues_rebuilt"),
                "final_chains": a.get("final_chains")}
    except Exception:
        return None


def main():
    ap = argparse.ArgumentParser(description="PCNA MD validation analysis (v2).")
    ap.add_argument("--pocket", default="aoh1996")
    ap.add_argument("--outdir", default="outputs")
    ap.add_argument("--keep-termini", action="store_true",
                    help="do NOT drop terminus/gap-adjacent pocket residues (their SASA "
                         "difference is dominated by where the crystal ends; measured to be "
                         "77.5%% of the apparent positive-control signal)")
    ap.add_argument("--min-pocket-coverage", type=float, default=0.80,
                    dest="min_pocket_coverage",
                    help="Hard-fail if apo and control share less than this fraction of the "
                         "pocket's resolved residues (default 0.80).")
    args = ap.parse_args()

    md, np, pd, plt = _imports()
    pocket = load_pocket(args.pocket)
    resseqs = list(pocket["pocket_residues_resseq"])
    iface = list(pocket.get("interface_chain_indices", [0, 1]))
    apo_pdb, ctrl_pdb = pocket["apo_pdb"], pocket.get("control_pdb")

    out = Path(args.outdir); adir = out / "analysis"; adir.mkdir(parents=True, exist_ok=True)
    rows, sasa_pool = [], {}
    # role -> pdb; keep labels so the report reads apo/control not raw ids
    role_pdb = [("apo", apo_pdb)] + ([("control", ctrl_pdb)] if ctrl_pdb else [])

    # ---- pocket parity: apo and control MUST be measured over the same atoms ----
    role_tops = {}
    for role, pdb in role_pdb:
        tp = out / pdb / "system_solvated.pdb"
        if tp.exists():
            role_tops[role] = _protein_top(md, tp)
    allow_keys, parity_report = (None, {"skipped": "only one role present"})
    if len(role_tops) > 1:
        allow_keys, parity_report = pocket_parity(md, role_tops, resseqs, iface,
                                                  min_coverage=args.min_pocket_coverage,
                                                  exclude_termini=not args.keep_termini)
    (adir / "pocket_parity.json").write_text(json.dumps(parity_report, indent=2), encoding="utf-8")

    for role, pdb in role_pdb:
        base = out / pdb
        top = base / "system_solvated.pdb"
        if not top.exists():
            print(f"[skip] {pdb} ({role}): no system_solvated.pdb (run run_md.py --run {role})"); continue
        sasa_pool[role] = []
        for rep_dir in sorted(base.glob("rep*")):
            dcd = rep_dir / "production.dcd"
            if not dcd.exists() or dcd.stat().st_size < 100_000:
                print(f"[skip] {pdb}/{rep_dir.name}: missing/empty DCD"); continue
            print(f"[analyze] {role} {pdb}/{rep_dir.name} ...")
            r = analyze_replicate(dcd, top, resseqs, iface, allow_keys=allow_keys)
            sasa_pool[role].extend(r.pop("_sasa_series"))
            r.update({"role": role, "pdb": pdb, "replicate": rep_dir.name}); rows.append(r)

    if not rows:
        sys.exit("No trajectories analyzed. Run run_md.py --run control then --run apo first.")
    df = pd.DataFrame(rows)
    df.to_csv(adir / "per_replicate.csv", index=False)

    # ---- positive-control gate: control(open) pocket SASA vs apo(closed) ----
    verdict = {"interpretable": False, "reason": "no positive control available (control_pdb is null)"}
    if sasa_pool.get("apo") and sasa_pool.get("control"):
        apo = np.array(sasa_pool["apo"]); holo = np.array(sasa_pool["control"])
        sep = float(holo.mean() - apo.mean())
        pooled_sd = np.sqrt((apo.std()**2 + holo.std()**2) / 2) or 1e-9
        d = sep / pooled_sd
        apo_reps = [r["pocket_sasa_mean_nm2"] for r in rows if r["role"] == "apo"]
        holo_reps = [r["pocket_sasa_mean_nm2"] for r in rows if r["role"] == "control"]
        n_apo, n_holo = len(apo_reps), len(holo_reps)
        apo_med = float(np.median(apo_reps)) if apo_reps else float("nan")
        per_rep_ok = bool(holo_reps and apo_reps and all(h > apo_med for h in holo_reps))
        control_ok = (holo.mean() > apo.mean()) and (abs(d) > 0.5) and per_rep_ok
        verdict = {
            "interpretable": bool(control_ok),
            "apo_pocket_sasa_nm2": float(apo.mean()), "control_pocket_sasa_nm2": float(holo.mean()),
            "control_minus_apo_nm2": sep, "cohens_d": float(d),
            "cohens_d_caveat": ("Cohen's d is over autocorrelated MD frames pooled across replicates; "
                                "DESCRIPTIVE effect size, not an n=frames test. The independent unit "
                                "is the replicate."),
            "n_apo_replicates": n_apo, "n_control_replicates": n_holo,
            "apo_replicate_means_nm2": [float(x) for x in apo_reps],
            "control_replicate_means_nm2": [float(x) for x in holo_reps],
            "per_replicate_consistent": per_rep_ok,
            "reason": (("Positive control PASSED: the control(open) pocket reads larger than "
                        "apo(closed) in pooled SASA (Cohen's d %.2f) AND in every control replicate "
                        "vs the apo median (%d control / %d apo) -> the metric can detect opening, so "
                        "an apo result is trustworthy." % (d, n_holo, n_apo)) if control_ok else
                       ("Positive control FAILED: control and apo pockets are not cleanly separated "
                        "(pooled Cohen's d %.2f; per-replicate consistent=%s over %d control / %d apo) "
                        "-> DO NOT report apo as a negative; extend sampling or use fpocket/MDpocket/"
                        "enhanced sampling." % (d, per_rep_ok, n_holo, n_apo))),
        }
        plt.figure(figsize=(6, 4))
        plt.hist(apo, bins=40, alpha=0.6, label=f"{apo_pdb} apo (closed)")
        plt.hist(holo, bins=40, alpha=0.6, label=f"{ctrl_pdb} control (open, ligand stripped)")
        plt.xlabel(f"{pocket['pocket_name']} pocket SASA (nm^2)"); plt.ylabel("frames"); plt.legend()
        plt.title("Positive control: pocket openness, control vs apo"); plt.tight_layout()
        plt.savefig(adir / "pocket_sasa_control.png", dpi=140); plt.close()

    caveats = [c for c in (_prep_caveat(out, apo_pdb), _prep_caveat(out, ctrl_pdb) if ctrl_pdb else None) if c]
    any_pbc = bool(df["pbc_artifact_suspected"].any())
    summary = {"pocket": pocket["pocket_name"], "per_replicate": rows, "positive_control": verdict,
               "equil_ns_discarded": EQUIL_NS,
               "pbc_artifact_suspected_any": any_pbc,
               "prep_caveats": caveats}
    (adir / "summary.json").write_text(json.dumps(summary, indent=2))

    # ---- human-readable report ----
    lines = [f"# PCNA MD validation - analysis report ({pocket['pocket_name']})", "",
             f"PBC-artifact suspected in any replicate (frame-to-frame jump > {PBC_JUMP_NM} nm): "
             f"**{any_pbc}**", "",
             "## Per-replicate", "",
             "| role | pdb | rep | RMSD mean (nm) | max frame-jump (nm) | pocket RMSF (nm) | "
             "pocket SASA (nm^2) | PBC-artifact? |",
             "|---|---|---|---|---|---|---|---|"]
    for r in rows:
        lines.append(f"| {r['role']} | {r['pdb']} | {r['replicate']} | {r['rmsd_mean_nm']:.3f} | "
                     f"{r['max_frame_jump_nm']:.3f} | {r['pocket_rmsf_mean_nm']:.3f} | "
                     f"{r['pocket_sasa_mean_nm2']:.1f} | {r['pbc_artifact_suspected']} |")
    lines += ["", "## Positive-control gate (the anti-false-negative check)", "",
              f"- apo     ({apo_pdb}) pocket SASA:  {verdict.get('apo_pocket_sasa_nm2','n/a')}",
              f"- control ({ctrl_pdb}) pocket SASA:  {verdict.get('control_pocket_sasa_nm2','n/a')}",
              f"- control - apo: {verdict.get('control_minus_apo_nm2','n/a')}  "
              f"(Cohen's d {verdict.get('cohens_d','n/a')})",
              f"- independent replicates: {verdict.get('n_control_replicates','n/a')} control / "
              f"{verdict.get('n_apo_replicates','n/a')} apo; per-replicate consistent: "
              f"{verdict.get('per_replicate_consistent','n/a')}",
              f"- **Interpretable: {verdict['interpretable']}**", f"- {verdict['reason']}",
              f"- _Caveat:_ {verdict.get('cohens_d_caveat','')}", ""]
    if caveats:
        lines += ["## Structure-prep caveats (read the gate WITH these)", ""]
        for c in caveats:
            lines.append(f"- **{c['pdb']}**: biological assembly '{c['assembly']}', "
                         f"{c['internal_residues_rebuilt']} internal residues rebuilt by PDBFixer. "
                         f"(8GLA is 3.77 A - side-chain rotamers are modeled, not observed; treat "
                         f"pocket SASA magnitude as approximate.)")
        lines.append("")
    (adir / "REPORT.md").write_text("\n".join(lines))
    print("\n".join(lines))
    print(f"\nWrote {adir/'REPORT.md'}, summary.json, per_replicate.csv, pocket_sasa_control.png")


if __name__ == "__main__":
    main()
