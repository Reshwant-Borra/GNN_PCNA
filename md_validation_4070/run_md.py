#!/usr/bin/env python
"""
PCNA cryptic-pocket MD validation - RTX 4070 edition (v2).
==========================================================

A clean, self-contained re-do of the Phase-5 MD validation. It bakes in fixes for
EVERY reason the previous run came back as an uninterpretable negative, PLUS the
structural-validity fixes from the 2026-07 biological-validity audit.

  PROBLEM                                        FIX (here)
  -------------------------------------------    -------------------------------------------
  Wrong "apo": 1AXC = p21-bound, 5E0V = S228I    Use TRUE apo 1W60 + holo 8GLA (from pocket json).
  No positive control                            8GLA (open/holo conformation) IS the control.
  Simulated arbitrary "novel windows"            Analysis targets the pocket's DERIVED residues.
  n=1 (rep2/rep3 died at the budget wall)        RESUMABLE: a killed run continues, never restarts.
  Topology not saved with trajectory             Saves system_solvated.pdb next to every DCD.
  Underpowered, 2 fs, ~20 ns                     HMR + 4 fs -> ~2x throughput; default 3 x 100 ns.
  PBC artifacts / bad analysis                   Sanity gate on RMSD; analyze_md.py images first.

  === NEW in v2 (2026-07 biological-validity audit) ===
  APO/HOLO WERE APPLES-TO-ORANGES (HIGH):        Build the BIOLOGICAL ASSEMBLY (homotrimer) for BOTH
   PDBFixer(pdbid=) fetched the asymmetric         structures via gemmi, so apo and holo are matched
   unit. 1W60's ASU is 2 chains that seed          3-chain rings with a genuine A-B interface. The
   DIFFERENT crystallographic trimers (a           previous 1W60 run simulated 2 monomers whose
   crystal contact, not the ring interface);       "interface" was a crystal-packing artifact.
   8GLA's ASU is 4 chains. The pocket only
   exists at a real subunit-subunit interface.
  Chain count never enforced (HIGH):             Hard-fail unless the assembly yields exactly
                                                   expected_protein_chains PCNA subunits.
  "peptides stripped" but removeHeterogens        Keep only protein polymer chains >= min_chain_res;
   keeps standard-AA peptides (p21) (LOW):         p21 / FEN1 peptides are dropped by length.
  Pocket residues hand-curated, dropped IDCL      Pocket residues come from pockets/<name>.json
   contacts under a false "6 A" comment (MED):     (derived, reproducible list). Single source of
                                                   truth shared with analyze_md.py.

WHAT THIS SIMULATES (no ligand parameterization needed - fully automatic, protein-only):
  * apo  (1W60) = pocket CLOSED. Does it transiently open over 100 ns?
  * ctrl (8GLA) = holo, ligand stripped (pocket starts OPEN). POSITIVE CONTROL: the openness
                  metric MUST read larger here than apo, or the *method* failed, not the biology.

USAGE:
  conda env create -f environment.yml && conda activate pcna-md-4070
  python run_md.py --pocket aoh1996 --run control --replicates 3 --ns 100   # 8GLA control FIRST
  python run_md.py --pocket aoh1996 --run apo     --replicates 3 --ns 100   # 1W60 apo
  python analyze_md.py --pocket aoh1996                                     # comparison report

Re-run the SAME command after any crash/shutdown - it resumes each replicate from its last
checkpoint automatically. (Or use ./run_in_tmux.sh to run the whole thing detached in tmux.)
"""
from __future__ import annotations
import argparse, json, math, sys, time, urllib.request
from pathlib import Path
from datetime import datetime, timezone

HERE = Path(__file__).resolve().parent
# Local CIF cache (present on Advay's machine); the friend's machine downloads from RCSB instead.
LOCAL_CIF_DIRS = [HERE.parent / "data" / "raw_intake" / "pcna_structures"]


def load_pocket(name: str) -> dict:
    """Load the pocket definition (residues, apo/control PDBs, expected chain count)."""
    p = HERE / "pockets" / f"{name}.json"
    if not p.exists():
        sys.exit(f"No pocket definition at {p}. Available: "
                 f"{[q.stem for q in (HERE/'pockets').glob('*.json')]}")
    return json.loads(p.read_text())


def _imports():
    try:
        import gemmi  # noqa: F401
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


def _fetch_cif(pdb_id: str, work: Path) -> Path:
    """Return a local mmCIF path for pdb_id: use the repo cache if present, else download from RCSB."""
    pdb_id = pdb_id.upper()
    for d in LOCAL_CIF_DIRS:
        c = d / f"{pdb_id}.cif"
        if c.exists():
            print(f"[prep] using cached CIF {c}")
            return c
    work.mkdir(parents=True, exist_ok=True)
    dest = work / f"{pdb_id}.cif"
    if not dest.exists():
        url = f"https://files.rcsb.org/download/{pdb_id}.cif"
        print(f"[prep] downloading {url}")
        urllib.request.urlretrieve(url, dest)
    return dest


def prepare_structure(pdb_id: str, work: Path, ph: float,
                      expected_chains: int, min_chain_res: int, pocket_resseq: list[int]):
    """Build the BIOLOGICAL ASSEMBLY (homotrimer), keep protein chains only, fix + protonate.

    This is the core fix vs v1: v1 called PDBFixer(pdbid=...) which loads only the deposited
    asymmetric unit and NEVER applies crystallographic symmetry, so apo (1W60, 2-chain ASU) and
    holo (8GLA, 4-chain ASU) were structurally non-comparable. Here gemmi applies the assembly
    operators, so both structures become matched biological homotrimers with a real interface.

    Returns the prepared (vacuum) protein PDB path. Deterministic & cached.
    """
    import gemmi
    *_, PDBFile, _, _, _, _, _, _, PDBFixer = _imports()
    prepared = work / "prepared_protein.pdb"
    audit = work / "prep_audit.json"
    if prepared.exists():
        print(f"[prep] reuse {prepared}")
        return prepared
    work.mkdir(parents=True, exist_ok=True)

    cif = _fetch_cif(pdb_id, work)
    st = gemmi.read_structure(str(cif))
    st.setup_entities()

    # --- 1. apply the biological-assembly operators (this is what v1 was missing) ---
    if st.assemblies:
        asm = st.assemblies[0]
        model = gemmi.make_assembly(asm, st[0], gemmi.HowToNameCopiedChain.AddNumber)
        assembly_id = asm.name
    else:
        model = st[0]
        assembly_id = "(none: used deposited coordinates)"

    # --- 2. keep only protein polymer chains with >= min_chain_res residues ---
    #     This drops waters, ions, small-molecule ligands, AND standard-AA peptides
    #     (p21 in 1AXC, FEN1 in 5E0V) that removeHeterogens would have wrongly kept.
    kept = []
    seen = []
    for ch in model:
        poly = ch.get_polymer()
        seq = poly.make_one_letter_sequence() if poly else ""
        ptype = poly.check_polymer_type() if poly else None
        is_protein = ptype in (gemmi.PolymerType.PeptideL, gemmi.PolymerType.PeptideD)
        seen.append({"chain": ch.name, "n_poly_res": len(seq), "protein": bool(is_protein)})
        if is_protein and len(seq) >= min_chain_res:
            kept.append(ch)

    # --- 3. ENFORCE chain count (hard-fail, not the silent skip v1 relied on) ---
    if len(kept) != expected_chains:
        audit.write_text(json.dumps(
            {"pdb_id": pdb_id, "assembly": assembly_id, "chains_seen": seen,
             "kept_protein_chains": [c.name for c in kept],
             "expected_protein_chains": expected_chains,
             "ERROR": f"expected {expected_chains} PCNA chains, got {len(kept)}"}, indent=2))
        sys.exit(f"[prep] FATAL: {pdb_id} biological assembly '{assembly_id}' yielded "
                 f"{len(kept)} protein chains (>= {min_chain_res} aa), expected "
                 f"{expected_chains}. See {audit}. Refusing to simulate a wrong oligomeric state.")

    # --- 4. rebuild a clean single-model structure with single-letter chain ids ---
    letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    clean = gemmi.Structure()
    clean.cell = st.cell
    clean.spacegroup_hm = st.spacegroup_hm
    nm = gemmi.Model("1")
    for i, ch in enumerate(kept):
        nc = gemmi.Chain(letters[i])
        for res in ch.get_polymer():
            nc.add_residue(res)
        nm.add_chain(nc)
    clean.add_model(nm)
    clean.setup_entities()

    # Carry the DEPOSITED full sequence onto the rebuilt entities so write_pdb emits SEQRES.
    # Without SEQRES, PDBFixer.findMissingResidues() cannot see that residues are missing:
    # it reported "internal_missing_residues_rebuilt: 0" for 8GLA despite ~50 unresolved
    # internal residues, the loops were never rebuilt, and OpenMM then bonded C(i)-N(i+1)
    # straight across each gap -- 13 covalent bonds up to 10.79 A (r0=1.33 A), one of them
    # worth 183,222 kJ/mol. That fuses physically disconnected loops in the CONTROL only,
    # i.e. an asymmetry between exactly the two systems whose pocket SASA is differenced.
    seqres_ok = False
    try:
        full_seqs = [e.full_sequence for e in st.entities if e.full_sequence]
        if full_seqs:
            longest = max(full_seqs, key=len)
            for ent in clean.entities:
                if ent.entity_type == gemmi.EntityType.Polymer and len(longest) > len(ent.full_sequence):
                    ent.full_sequence = list(longest)
            seqres_ok = True
    except Exception as exc:  # gemmi API drift must not silently degrade the prep
        print(f"[prep] WARN: could not transfer SEQRES ({type(exc).__name__}: {exc})")
    if not seqres_ok:
        print("[prep] WARN: no deposited full sequence available; PDBFixer cannot detect "
              "internal gaps and OpenMM may bond across them. The long-bond assertion below "
              "is the backstop.")

    raw_pdb = work / "assembly_protein_raw.pdb"
    clean.write_pdb(str(raw_pdb))

    # --- 5. PDBFixer: repair missing atoms + protonate. Build only INTERNAL gaps (do not
    #        fabricate long terminal tails). Record what was rebuilt for transparency. ---
    fixer = PDBFixer(filename=str(raw_pdb))
    fixer.findMissingResidues()
    # Drop terminal missing-residue runs so we don't invent floppy tails that never diffracted.
    chains = list(fixer.topology.chains())
    keys_to_drop = []
    for (ch_idx, res_idx), _seq in list(fixer.missingResidues.items()):
        chain_len = len(list(chains[ch_idx].residues()))
        if res_idx == 0 or res_idx == chain_len:
            keys_to_drop.append((ch_idx, res_idx))
    for k in keys_to_drop:
        fixer.missingResidues.pop(k, None)
    n_internal_missing = sum(len(v) for v in fixer.missingResidues.values())
    fixer.findNonstandardResidues(); fixer.replaceNonstandardResidues()
    fixer.findMissingAtoms(); fixer.addMissingAtoms()
    fixer.addMissingHydrogens(ph)
    with prepared.open("w") as fh:
        PDBFile.writeFile(fixer.topology, fixer.positions, fh, keepIds=True)

    # --- 6. audit: chain composition + how many residues were rebuilt (transparency) ---
    final_chains = [{"id": c.id, "n_res": sum(1 for _ in c.residues())}
                    for c in fixer.topology.chains()]
    pocket_set = set(pocket_resseq)
    audit.write_text(json.dumps({
        "pdb_id": pdb_id, "assembly": assembly_id,
        "chains_seen": seen, "kept_protein_chains": [c.name for c in kept],
        "expected_protein_chains": expected_chains, "final_chains": final_chains,
        "internal_missing_residues_rebuilt": n_internal_missing,
        "note": ("Biological assembly reconstructed (gemmi). Protein-only, peptides/ligands/waters "
                 "dropped by >= %d aa filter. Terminal missing residues NOT fabricated. "
                 "%d internal residues rebuilt by PDBFixer - if this is large and the structure is "
                 "low-resolution (e.g. 8GLA 3.77 A), treat pocket side-chain geometry as modeled, "
                 "not observed (report as a caveat)." % (min_chain_res, n_internal_missing)),
        "pocket_residues_resseq": sorted(pocket_set),
    }, indent=2))
    print(f"[prep] {pdb_id}: assembly '{assembly_id}' -> {len(kept)} PCNA chains "
          f"{[c.name for c in kept]}, {n_internal_missing} internal residues rebuilt -> {prepared}")
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


def assert_no_impossible_bonds(system, positions, max_len_nm=0.25):
    """Refuse to simulate a system containing a covalent bond longer than a bond can be.

    Backstop for the SEQRES/gap defect: when PDBFixer cannot see an unresolved loop, OpenMM
    bonds the residues flanking it. Measured on 8GLA: 13 HarmonicBondForce terms above 2.5 A
    (r0 = 1.33 A, k = 410032 kJ/mol/nm^2), the worst being chain0 184:C-193:N at 10.79 A
    carrying 183,222 kJ/mol. Such a system minimises into a distorted structure rather than
    failing, so nothing downstream would have flagged it -- hence an explicit assertion.
    """
    mm, unit, _, _, _, _, _, _, *_ = _imports()
    import numpy as np

    try:
        xyz = np.array(positions.value_in_unit(unit.nanometer))
    except AttributeError:
        xyz = np.array([[v.x, v.y, v.z] for v in positions])

    offenders = []
    for force in system.getForces():
        if not isinstance(force, mm.HarmonicBondForce):
            continue
        for i in range(force.getNumBonds()):
            a, b, r0, k = force.getBondParameters(i)
            d = float(np.linalg.norm(xyz[a] - xyz[b]))
            if d > max_len_nm:
                r0_nm = r0.value_in_unit(unit.nanometer) if hasattr(r0, "value_in_unit") else float(r0)
                k_val = k.value_in_unit(unit.kilojoule_per_mole / unit.nanometer**2) \
                    if hasattr(k, "value_in_unit") else float(k)
                offenders.append((a, b, d, r0_nm, 0.5 * k_val * (d - r0_nm) ** 2))
    if offenders:
        offenders.sort(key=lambda t: -t[2])
        lines = "\n".join(
            f"    atoms {a}-{b}: {d*10:.2f} A (r0 {r0*10:.2f} A, E {e:,.0f} kJ/mol)"
            for a, b, d, r0, e in offenders[:15]
        )
        sys.exit(
            f"[prep] FATAL: {len(offenders)} covalent bond(s) longer than {max_len_nm*10:.1f} A "
            f"in the parameterized system:\n{lines}\n"
            "    These are almost certainly bonds across unresolved loops: the structure was "
            "written without SEQRES, so PDBFixer never saw the gaps and OpenMM joined the "
            "flanking residues. Refusing to simulate a chemically impossible system."
        )


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
    assert_no_impossible_bonds(system, positions, max_len_nm=0.25)
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
            "replicate": rep, "pdb": args._pdb_id, "seed": seed,
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
            "replicate": rep, "pdb": args._pdb_id, "seed": seed,
            "steps": sim.context.getStepCount(),
            "final_potential_kj_mol": pe if math.isfinite(pe) else None,
            "backbone_rmsd_nm": rmsd_nm, "reason": reason,
            "failed_utc": datetime.now(timezone.utc).isoformat(),
        }, indent=2, allow_nan=False))
        print(f"[rep{rep}] FAILED sanity gate: {reason}")
        return

    production_ns = (sim.context.getStepCount() - equil_steps) * dt.value_in_unit(unit.nanoseconds)
    done_flag.write_text(json.dumps({
        "replicate": rep, "pdb": args._pdb_id, "ns": args.ns,
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
    p = argparse.ArgumentParser(description="PCNA cryptic-pocket MD validation (RTX 4070, v2).")
    p.add_argument("--pocket", default="aoh1996", help="pocket name -> pockets/<name>.json")
    p.add_argument("--run", choices=["apo", "control"], required=True,
                   help="which structure to simulate: 'control' (holo positive control) FIRST, then 'apo'")
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
    p.add_argument("--hmr", action="store_true", default=True)
    p.add_argument("--no-hmr", dest="hmr", action="store_false")
    p.add_argument("--hmr-amu", type=float, default=4.0,
                   help="repartitioned hydrogen mass (amu); ~4.0 is required to keep a 4 fs step stable")
    p.add_argument("--rmsd-fail-nm", type=float, default=1.0,
                   help="post-run backbone RMSD (nm) to equilibrated start above which a replicate is FAILED")
    p.add_argument("--platform", default="CUDA")
    p.add_argument("--outdir", default="outputs")
    args = p.parse_args()

    pocket = load_pocket(args.pocket)
    pdb_id = (pocket["apo_pdb"] if args.run == "apo" else pocket["control_pdb"])
    if pdb_id is None:
        sys.exit(f"[main] pocket '{args.pocket}' has no {args.run}_pdb defined "
                 f"(novel pocket with no {'apo' if args.run=='apo' else 'holo control'} structure). "
                 f"Cannot run '{args.run}'.")
    args._pdb_id = pdb_id
    expected_chains = int(pocket.get("expected_protein_chains", 3))
    min_chain_res = int(pocket.get("min_chain_residues", 200))
    pocket_resseq = list(pocket.get("pocket_residues_resseq", []))

    print(f"[main] pocket={pocket['pocket_name']} run={args.run} -> PDB {pdb_id} "
          f"(expect {expected_chains} chains)")
    root = Path(args.outdir) / pdb_id
    prepared = prepare_structure(pdb_id, root / "prep", args.ph,
                                 expected_chains, min_chain_res, pocket_resseq)
    ff, topology, positions, solvated = build_system(prepared, root / "rep01", args)
    (root / "pocket_definition.json").write_text(json.dumps(
        {"pocket": pocket["pocket_name"], "run": args.run, "pdb_id": pdb_id,
         "pocket_residues_resseq": pocket_resseq,
         "interface_chain_indices": pocket.get("interface_chain_indices", [0, 1]),
         "note": "Analysis (analyze_md.py) targets these residues on the biological assembly."},
        indent=2))

    t0 = time.time()
    for rep in range(1, args.replicates + 1):
        run_replicate(ff, topology, positions, solvated, root / f"rep{rep:02d}", rep, args)
    print(f"\nAll replicates for {pdb_id} ({args.run}) done in {(time.time()-t0)/3600:.2f} h. "
          f"Next: run the other structure, then `python analyze_md.py --pocket {args.pocket}`.")


if __name__ == "__main__":
    main()
