#!/usr/bin/env python
"""
PCNA cryptic-pocket MD validation — RTX 4070 edition.
=====================================================

This is a clean, self-contained re-do of the Phase-5 MD validation. It bakes in
fixes for EVERY reason the previous run came back as an uninterpretable negative:

  PROBLEM (last time)                          FIX (here)
  -------------------------------------------  --------------------------------------------
  Wrong "apo": 1AXC = p21-bound, 5E0V = S228I  Use the TRUE apo 1W60 + the holo 8GLA.
  No positive control                          8GLA (open/holo conformation) IS the control.
  Simulated arbitrary "novel windows"          Analysis targets the validated AOH1996 pocket.
  n=1 (rep2/rep3 died at the budget wall)      RESUMABLE: a killed run continues, never restarts.
  Topology not saved with trajectory           Saves system_solvated.pdb next to every DCD.
  Underpowered, 2 fs, ~20 ns                   HMR + 4 fs -> ~2x throughput; default 3 x 100 ns.
  PBC artifacts / bad analysis                 Sanity gate on RMSD; analysis (analyze_md.py) images first.

WHAT THIS SIMULATES (no ligand parameterization needed — fully automatic):
  * 1W60  = apo PCNA (pocket CLOSED). Question: does the AOH1996 pocket transiently open?
  * 8GLA  = holo PCNA, ligand (ZQZ/AOH1996) stripped (pocket starts OPEN). POSITIVE CONTROL:
            the pocket-volume metric MUST read larger here than in apo. If it can't tell
            8GLA-open from 1W60-closed, the *method* failed — not the biology. That is the
            check that makes a negative result trustworthy instead of meaningless.

USAGE (the friend runs exactly this):
  conda env create -f environment.yml && conda activate pcna-md-4070
  python run_md.py --pdb 8GLA --replicates 3 --ns 100      # positive control first
  python run_md.py --pdb 1W60 --replicates 3 --ns 100      # apo
  python analyze_md.py                                      # builds the comparison report
  # then send the whole `outputs/` folder back (or: wormhole send outputs).

Re-run the SAME command after any crash/shutdown — it resumes each replicate from its
last checkpoint automatically.
"""
from __future__ import annotations
import argparse, json, math, sys, time
from pathlib import Path
from datetime import datetime, timezone

# Ground-truth AOH1996 pocket residues (8GLA chains A+B, within 6 A of ZQZ).
# Recorded here so the run manifest documents exactly what we care about.
AOH_POCKET = {
    "A": [25,26,27,38,39,40,41,42,44,45,46,47,123,125,126,128,231,232,233,234,250,251,252,253],
    "B": [23,25,26,27,38,39,40,41,42,44,45,46,47,123,125,126,128,231,232,233,234,250,251,252],
}


def _imports():
    try:
        import openmm as mm
        from openmm import unit
        from openmm.app import (ForceField, Modeller, PDBFile, Simulation, PME, HBonds,
                                 DCDReporter, StateDataReporter, CheckpointReporter)
        from pdbfixer import PDBFixer
    except Exception as exc:
        sys.exit("Missing deps. Run: conda env create -f environment.yml && "
                 "conda activate pcna-md-4070\n  (%s)" % exc)
    return mm, unit, ForceField, Modeller, PDBFile, Simulation, PME, HBonds, \
        DCDReporter, StateDataReporter, CheckpointReporter, PDBFixer


def prepare_structure(pdb_id: str, work: Path, ph: float):
    """Fetch + fix PCNA, strip all ligands/waters/peptides, keep protein chains only.

    Returns the path to a prepared (vacuum) protein PDB. Deterministic & cached.
    """
    *_, PDBFile, _, _, _, _, _, _, PDBFixer = _imports()
    prepared = work / "prepared_protein.pdb"
    if prepared.exists():
        print(f"[prep] reuse {prepared}")
        return prepared
    print(f"[prep] PDBFixer downloading {pdb_id} ...")
    fixer = PDBFixer(pdbid=pdb_id)
    # Remove everything that is not a standard amino-acid chain (ligands, peptides, ions, water).
    fixer.removeHeterogens(keepWater=False)
    fixer.findMissingResidues()
    fixer.findNonstandardResidues(); fixer.replaceNonstandardResidues()
    fixer.findMissingAtoms(); fixer.addMissingAtoms()
    fixer.addMissingHydrogens(ph)
    work.mkdir(parents=True, exist_ok=True)
    with prepared.open("w") as fh:
        PDBFile.writeFile(fixer.topology, fixer.positions, fh, keepIds=True)
    # Audit the chains so a human can confirm we kept the PCNA trimer (not a peptide).
    chains = [{"id": c.id, "n_res": sum(1 for _ in c.residues())} for c in fixer.topology.chains()]
    (work / "prep_audit.json").write_text(json.dumps(
        {"pdb_id": pdb_id, "ph": ph, "chains_kept": chains,
         "note": "All heterogens removed (ligand/peptide/water). Protein only."}, indent=2))
    print(f"[prep] chains kept: {chains}")
    return prepared


def build_system(prepared_pdb: Path, run_dir: Path, args):
    """Solvate + parameterize once per (pdb). Saves the solvated TOPOLOGY (the old missing piece)."""
    mm, unit, ForceField, Modeller, PDBFile, *_ = _imports()
    solvated_pdb = run_dir.parent / "system_solvated.pdb"
    ff = ForceField("amber14-all.xml", "amber14/tip3p.xml")
    if solvated_pdb.exists():
        print(f"[sys] reuse solvated topology {solvated_pdb}")
        pdb = PDBFile(str(solvated_pdb))
        return ff, pdb.topology, pdb.positions, solvated_pdb
    print("[sys] solvating (TIP3P, 1.0 nm padding, 0.15 M NaCl, neutralized) ...")
    pdb = PDBFile(str(prepared_pdb))
    modeller = Modeller(pdb.topology, pdb.positions)
    modeller.addHydrogens(ff, pH=args.ph)
    modeller.addSolvent(ff, model="tip3p", padding=args.padding * unit.nanometer,
                        ionicStrength=args.ionic * unit.molar, neutralize=True)
    run_dir.parent.mkdir(parents=True, exist_ok=True)
    with solvated_pdb.open("w") as fh:               # <-- TOPOLOGY SAVED NEXT TO TRAJECTORIES
        PDBFile.writeFile(modeller.topology, modeller.positions, fh, keepIds=True)
    n_atoms = modeller.topology.getNumAtoms()
    print(f"[sys] solvated system: {n_atoms} atoms -> {solvated_pdb}")
    return ff, modeller.topology, modeller.positions, solvated_pdb


def make_simulation(ff, topology, positions, args, seed):
    mm, unit, _, _, _, Simulation, PME, HBonds, *_ = _imports()
    # HMR (~4 amu repartitioned H) + 4 fs is the standard recipe to ~2x throughput vs the
    # old 2 fs run. The hydrogen mass MUST be consistent with the timestep: 1.5 amu is too
    # light to keep a 4 fs step stable, so the default --hmr-amu is 4.0.
    system = ff.createSystem(topology, nonbondedMethod=PME,
                             nonbondedCutoff=1.0 * unit.nanometer,
                             constraints=HBonds,
                             hydrogenMass=(args.hmr_amu if args.hmr else 1.0) * unit.amu,
                             rigidWater=True)
    barostat = mm.MonteCarloBarostat(args.pressure * unit.bar, args.temp * unit.kelvin, 25)
    barostat.setRandomNumberSeed(seed)   # reproducibility: seed the barostat, not just the integrator
    system.addForce(barostat)
    dt = (4.0 if args.hmr else 2.0) * unit.femtoseconds
    integrator = mm.LangevinMiddleIntegrator(args.temp * unit.kelvin, 1.0 / unit.picosecond, dt)
    integrator.setRandomNumberSeed(seed)
    try:
        platform = mm.Platform.getPlatformByName(args.platform)
        props = {"Precision": "mixed"} if args.platform == "CUDA" else {}
    except Exception:
        platform = mm.Platform.getPlatformByName("CPU"); props = {}
        print("[warn] CUDA platform unavailable; falling back to CPU (slow).")
    sim = Simulation(topology, system, integrator, platform, props)
    sim.context.setPositions(positions)
    return sim, dt


# Standard + common Amber protonation-variant residue names; used to pick protein backbone
# atoms only (so water 'O' and ions are excluded from the RMSD sanity gate).
_PROTEIN_RESNAMES = {
    "ALA", "ARG", "ASN", "ASP", "CYS", "GLN", "GLU", "GLY", "HIS", "ILE", "LEU", "LYS",
    "MET", "PHE", "PRO", "SER", "THR", "TRP", "TYR", "VAL",
    "HID", "HIE", "HIP", "CYX", "CYM", "ASH", "GLH", "LYN", "MSE",
}


def _backbone_indices(topology):
    """Indices of protein backbone N/CA/C atoms (excludes water oxygens and ions)."""
    return [a.index for a in topology.atoms()
            if a.name in ("N", "CA", "C") and a.residue.name in _PROTEIN_RESNAMES]


def _kabsch_rmsd_nm(P, Q):
    """Optimal-superposition (Kabsch) RMSD in nm between two (N,3) coordinate sets."""
    import numpy as np
    Pc = P - P.mean(axis=0)
    Qc = Q - Q.mean(axis=0)
    H = Pc.T @ Qc
    U, _S, Vt = np.linalg.svd(H)
    d = 1.0 if np.linalg.det(Vt.T @ U.T) >= 0.0 else -1.0
    R = Vt.T @ np.diag([1.0, 1.0, d]) @ U.T
    diff = (Pc @ R.T) - Qc
    return float(np.sqrt((diff * diff).sum(axis=1).mean()))


def run_replicate(ff, topology, positions, solvated_pdb, run_dir: Path, rep: int, args):
    mm, unit, _, _, PDBFile, _, _, _, DCDReporter, StateDataReporter, CheckpointReporter, _ = _imports()
    import numpy as np
    run_dir.mkdir(parents=True, exist_ok=True)
    chk = run_dir / "state.chk"
    dcd = run_dir / "production.dcd"
    log = run_dir / "production.log"
    done_flag = run_dir / "DONE.json"
    failed_flag = run_dir / "FAILED.json"
    ref_npy = run_dir / "equil_backbone_ref.npy"
    if done_flag.exists():
        print(f"[rep{rep}] already complete -> {done_flag}"); return
    if failed_flag.exists():
        # A prior attempt blew up here. Do NOT resume the corrupt checkpoint and crash
        # forever -- report it and skip. (Delete FAILED.json to force a fresh retry.)
        print(f"[rep{rep}] previously FAILED -> {failed_flag} (delete it to retry)"); return

    seed = 20260000 + rep
    sim, dt = make_simulation(ff, topology, positions, args, seed)
    steps_per_ns = int(round((1.0 / dt.value_in_unit(unit.nanoseconds))))
    equil_steps = int(args.equil_ns * steps_per_ns)
    prod_steps = int(args.ns * steps_per_ns)
    # Equilibration is NOT charged against the production budget: the loop targets
    # (equil + production) steps, so "--ns 100" delivers a true 100 ns of production.
    total_steps = equil_steps + prod_steps
    report_every = int(args.report_ps / dt.value_in_unit(unit.picoseconds))
    # Sync the checkpoint cadence to the DCD write cadence: a checkpoint then always
    # coincides with a written frame, so a resume cannot replay (and thus duplicate) any
    # frame that was written past the last checkpoint. (--checkpoint-ps is superseded.)
    chk_every = report_every

    backbone = _backbone_indices(topology)
    append = False
    if chk.exists():
        # RESUME: load checkpoint, continue from where it died. This is the rep2/rep3 fix.
        print(f"[rep{rep}] resuming from checkpoint {chk}")
        sim.loadCheckpoint(str(chk))
        append = True
    else:
        print(f"[rep{rep}] minimize + equilibrate ({args.equil_ns} ns) ...")
        sim.minimizeEnergy(maxIterations=args.min_steps)
        sim.context.setVelocitiesToTemperature(args.temp * unit.kelvin, seed)
        sim.step(equil_steps)
        sim.saveCheckpoint(str(chk))
        # Stash the equilibrated backbone as the reference for the post-run RMSD gate.
        # enforcePeriodicBox=False keeps molecules whole (no PBC split), so a plain
        # superposition RMSD is valid without any imaging.
        if backbone:
            eq_xyz = sim.context.getState(getPositions=True, enforcePeriodicBox=False
                                          ).getPositions(asNumpy=True).value_in_unit(unit.nanometer)
            np.save(str(ref_npy), np.asarray(eq_xyz)[backbone])

    done_steps = sim.context.getStepCount()
    # CheckpointReporter is registered BEFORE the DCDReporter so that, at a shared report
    # step, the checkpoint is written no later than the frame it corresponds to.
    sim.reporters.append(CheckpointReporter(str(chk), chk_every))
    sim.reporters.append(DCDReporter(str(dcd), report_every, append=append))
    sim.reporters.append(StateDataReporter(str(log), report_every, step=True, time=True,
                         potentialEnergy=True, temperature=True, density=True,
                         progress=True, remainingTime=True, speed=True,
                         totalSteps=total_steps, separator="\t", append=append))
    sim.reporters.append(StateDataReporter(sys.stdout, report_every * 20, step=True,
                         temperature=True, speed=True, progress=True, totalSteps=total_steps))

    print(f"[rep{rep}] production: target {args.ns} ns ({prod_steps} steps) "
          f"+ {args.equil_ns} ns equil, already at step {done_steps}")
    # chunked loop so checkpoints land even if the process is killed between chunks
    chunk = report_every
    try:
        while sim.context.getStepCount() < total_steps:
            remaining = total_steps - sim.context.getStepCount()
            sim.step(min(chunk, remaining))
            sim.saveCheckpoint(str(chk))
    except Exception as exc:
        # A numerical blow-up (e.g. OpenMM "Particle coordinate is nan") raises here. Record
        # it as FAILED so a re-run does not resume the corrupt checkpoint and crash forever.
        failed_flag.write_text(json.dumps({
            "replicate": rep, "pdb": args.pdb, "seed": seed,
            "steps": sim.context.getStepCount(),
            "reason": "exception during integration (numerical blow-up)",
            "error": str(exc),
            "failed_utc": datetime.now(timezone.utc).isoformat(),
        }, indent=2, allow_nan=False))
        print(f"[rep{rep}] FAILED during integration: {exc}")
        return

    # ---- REAL post-run sanity gate: catch blown-up / NaN sims instead of writing them DONE ----
    state = sim.context.getState(getPositions=True, getEnergy=True, enforcePeriodicBox=False)
    pe = state.getPotentialEnergy().value_in_unit(unit.kilojoule_per_mole)
    final_xyz = np.asarray(state.getPositions(asNumpy=True).value_in_unit(unit.nanometer))
    rmsd_nm = None
    reason = None
    if not math.isfinite(pe):
        reason = f"non-finite potential energy ({pe})"
    elif not np.isfinite(final_xyz).all():
        reason = "non-finite atomic coordinates (NaN/inf) in the final frame"
    elif backbone and ref_npy.exists():
        # Whole (unimaged) coords + optimal superposition -> a PBC-correct backbone RMSD.
        try:
            rmsd_nm = _kabsch_rmsd_nm(final_xyz[backbone], np.load(str(ref_npy)))
            if not (rmsd_nm < args.rmsd_fail_nm):   # `not <` also trips on NaN
                reason = (f"final backbone RMSD to equilibrated start {rmsd_nm:.2f} nm "
                          f">= {args.rmsd_fail_nm} nm (blow-up / gross unfolding)")
        except Exception as exc:
            print(f"[rep{rep}] warn: RMSD gate could not run ({exc}); "
                  f"relying on energy/coordinate finiteness only")

    if reason is not None:
        failed_flag.write_text(json.dumps({
            "replicate": rep, "pdb": args.pdb, "seed": seed,
            "steps": sim.context.getStepCount(),
            "final_potential_kj_mol": pe if math.isfinite(pe) else None,
            "backbone_rmsd_nm": rmsd_nm, "reason": reason,
            "failed_utc": datetime.now(timezone.utc).isoformat(),
        }, indent=2, allow_nan=False))
        print(f"[rep{rep}] FAILED sanity gate: {reason}")
        return

    production_ns = (sim.context.getStepCount() - equil_steps) * dt.value_in_unit(unit.nanoseconds)
    done_flag.write_text(json.dumps({
        "replicate": rep, "pdb": args.pdb, "ns": args.ns,
        "production_ns": production_ns, "equil_ns": args.equil_ns, "report_ps": args.report_ps,
        "seed": seed,
        "steps": sim.context.getStepCount(), "timestep_fs": dt.value_in_unit(unit.femtoseconds),
        "hmr": args.hmr, "hmr_amu": (args.hmr_amu if args.hmr else 1.0),
        "final_potential_kj_mol": pe, "backbone_rmsd_nm": rmsd_nm,
        "sanity_gate": ("passed: finite energy+coords" +
                        (f", backbone RMSD {rmsd_nm:.2f} nm < {args.rmsd_fail_nm} nm"
                         if rmsd_nm is not None else ", RMSD ref unavailable")),
        "topology": str(solvated_pdb.name), "trajectory": str(dcd.name),
        "finished_utc": datetime.now(timezone.utc).isoformat(),
    }, indent=2, allow_nan=False))
    print(f"[rep{rep}] DONE ({sim.context.getStepCount()} steps, PE={pe:.0f} kJ/mol, "
          f"prod {production_ns:.1f} ns"
          + (f", bbRMSD {rmsd_nm:.2f} nm)" if rmsd_nm is not None else ")"))


def main():
    p = argparse.ArgumentParser(description="PCNA cryptic-pocket MD validation (RTX 4070).")
    p.add_argument("--pdb", required=True, help="PDB id: 1W60 (apo) or 8GLA (holo positive control)")
    p.add_argument("--replicates", type=int, default=3)
    p.add_argument("--ns", type=float, default=100.0, help="production ns per replicate")
    p.add_argument("--equil-ns", type=float, default=2.0)
    p.add_argument("--temp", type=float, default=310.0)
    p.add_argument("--pressure", type=float, default=1.0)
    p.add_argument("--ph", type=float, default=7.4)
    p.add_argument("--padding", type=float, default=1.0)
    p.add_argument("--ionic", type=float, default=0.15)
    p.add_argument("--min-steps", type=int, default=5000)
    p.add_argument("--report-ps", type=float, default=50.0, help="DCD/log interval")
    p.add_argument("--checkpoint-ps", type=float, default=500.0,
                   help="(superseded: checkpoints now land at the DCD frame cadence to keep resume frame-exact)")
    p.add_argument("--hmr", action="store_true", default=True)
    p.add_argument("--no-hmr", dest="hmr", action="store_false")
    p.add_argument("--hmr-amu", type=float, default=4.0,
                   help="repartitioned hydrogen mass (amu); ~4.0 is required to keep a 4 fs step stable")
    p.add_argument("--rmsd-fail-nm", type=float, default=1.0,
                   help="post-run backbone RMSD (nm) to equilibrated start above which a replicate is FAILED")
    p.add_argument("--platform", default="CUDA")
    p.add_argument("--outdir", default="outputs")
    args = p.parse_args()

    root = Path(args.outdir) / args.pdb
    prepared = prepare_structure(args.pdb, root / "prep", args.ph)
    ff, topology, positions, solvated = build_system(prepared, root / "rep01", args)
    (root / "pocket_definition.json").write_text(json.dumps(
        {"aoh1996_pocket_residues": AOH_POCKET,
         "note": "Analysis (analyze_md.py) targets these. Apo=1W60 closed, Holo=8GLA open control."},
        indent=2))

    t0 = time.time()
    for rep in range(1, args.replicates + 1):
        run_replicate(ff, topology, positions, solvated, root / f"rep{rep:02d}", rep, args)
    print(f"\nAll replicates for {args.pdb} done in {(time.time()-t0)/3600:.2f} h. "
          f"Next: run the other structure, then `python analyze_md.py`.")


if __name__ == "__main__":
    main()
