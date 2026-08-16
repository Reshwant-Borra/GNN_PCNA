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
import argparse, hashlib, json, math, os, platform as py_platform, shlex, shutil, signal, socket
import subprocess, sys, time, urllib.request
from pathlib import Path
from datetime import datetime, timezone

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
# Local CIF cache (present on Advay's machine); the friend's machine downloads from RCSB instead.
LOCAL_CIF_DIRS = [HERE.parent / "data" / "raw_intake" / "pcna_structures"]


def load_pocket(name: str) -> dict:
    """Load the pocket definition (residues, apo/control PDBs, expected chain count)."""
    p = HERE / "pockets" / f"{name}.json"
    if not p.exists():
        sys.exit(f"No pocket definition at {p}. Available: "
                 f"{[q.stem for q in (HERE/'pockets').glob('*.json')]}")
    return json.loads(p.read_text())


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _json_default(obj):
    if isinstance(obj, Path):
        return str(obj)
    return str(obj)


def write_json(path: Path, obj: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(obj, indent=2, allow_nan=False, default=_json_default) + "\n",
                   encoding="utf-8")
    os.replace(tmp, path)


def load_json(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def sha256_file(path: Path | None) -> str | None:
    if path is None or not path.exists():
        return None
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _run_text(cmd: list[str]) -> str | None:
    try:
        out = subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL, timeout=10)
        return out.strip() or None
    except Exception:
        return None


def git_info() -> dict:
    status = _run_text(["git", "-C", str(ROOT), "status", "--short"]) or ""
    dirty_lines = status.splitlines()
    return {
        "commit": _run_text(["git", "-C", str(ROOT), "rev-parse", "HEAD"]),
        "branch": _run_text(["git", "-C", str(ROOT), "rev-parse", "--abbrev-ref", "HEAD"]),
        "dirty": bool(dirty_lines),
        "dirty_file_count": len(dirty_lines),
        "dirty_status_sample": dirty_lines[:50],
    }


def cpu_model() -> str | None:
    if Path("/proc/cpuinfo").exists():
        for line in Path("/proc/cpuinfo").read_text(errors="replace").splitlines():
            if line.lower().startswith("model name"):
                return line.split(":", 1)[1].strip()
    return (_run_text(["sysctl", "-n", "machdep.cpu.brand_string"])
            or py_platform.processor() or None)


def nvidia_info() -> dict:
    query = _run_text([
        "nvidia-smi",
        "--query-gpu=name,driver_version",
        "--format=csv,noheader",
    ])
    if not query:
        return {"available": False}
    smi_text = _run_text(["nvidia-smi"]) or ""
    cuda_version = None
    if "CUDA Version:" in smi_text:
        cuda_version = smi_text.split("CUDA Version:", 1)[1].split()[0]
    gpus = []
    for row in query.splitlines():
        parts = [p.strip() for p in row.split(",")]
        gpus.append({
            "name": parts[0] if len(parts) > 0 else None,
            "driver_version": parts[1] if len(parts) > 1 else None,
            "cuda_version": cuda_version,
        })
    return {"available": True, "gpus": gpus}


def runtime_environment(platform_used: str | None = None, precision: str | None = None) -> dict:
    try:
        import openmm as mm
        openmm_version = mm.version.version
        platforms = [mm.Platform.getPlatform(i).getName() for i in range(mm.Platform.getNumPlatforms())]
    except Exception as exc:
        openmm_version = f"unavailable: {exc}"
        platforms = []
    return {
        "hostname": socket.gethostname(),
        "os": py_platform.platform(),
        "python": sys.version.replace("\n", " "),
        "cpu_model": cpu_model(),
        "nvidia": nvidia_info(),
        "openmm_version": openmm_version,
        "openmm_platforms": platforms,
        "platform_used": platform_used,
        "precision": precision,
    }


def dcd_frame_count(path: Path) -> int | None:
    if not path.exists() or path.stat().st_size == 0:
        return 0 if path.exists() else None
    try:
        from mdtraj.formats import DCDTrajectoryFile
        with DCDTrajectoryFile(str(path), "r") as fh:
            return len(fh)
    except Exception:
        return None


def production_step_to_ns(step: int, equil_steps: int, dt_ns: float) -> float:
    return max(0.0, (int(step) - int(equil_steps)) * dt_ns)


def archive_stale_done(done_flag: Path, reason: str) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    dest = done_flag.with_name(f"DONE.stale.{stamp}.json")
    payload = load_json(done_flag, {})
    payload["_stale_for_current_target"] = {"archived_utc": utc_now(), "reason": reason}
    write_json(dest, payload)
    done_flag.unlink()
    return dest


def validate_done(done_flag: Path, args, rep: int, total_steps: int,
                  prod_steps: int, report_every: int, dcd: Path) -> tuple[bool, str]:
    done = load_json(done_flag, None)
    if not isinstance(done, dict):
        return False, "DONE.json is not valid JSON"
    if int(done.get("replicate", -1)) != rep:
        return False, "replicate number mismatch"
    if done.get("pdb") != args._pdb_id:
        return False, "PDB mismatch"
    if not str(done.get("sanity_gate", "")).startswith("passed"):
        return False, "sanity gate did not pass"
    if int(done.get("steps", -1)) < total_steps:
        return False, f"steps {done.get('steps')} < target {total_steps}"
    if float(done.get("production_ns", -1.0)) + 1e-9 < float(args.ns):
        return False, f"production_ns {done.get('production_ns')} < target {args.ns}"
    if prod_steps > 0:
        if not dcd.exists() or dcd.stat().st_size == 0:
            return False, "production trajectory is missing or empty"
        frames = dcd_frame_count(dcd)
        expected = prod_steps // report_every
        if frames is not None and frames > expected:
            return False, f"DCD has {frames} frames > expected {expected}; duplicate-frame risk"
    return True, "complete"


def estimate_output_bytes(n_atoms: int, prod_steps: int, report_every: int,
                          replicates: int, safety_factor: float) -> dict:
    frames = max(0, prod_steps // report_every)
    dcd_per_rep = 4096 + (12 * int(n_atoms) * frames)
    log_per_rep = max(4096, frames * 512)
    checkpoint_per_rep = max(32 << 20, int(n_atoms) * 128)  # current+previous+metadata margin
    raw = (dcd_per_rep + log_per_rep + checkpoint_per_rep) * max(1, replicates)
    return {
        "atom_count": int(n_atoms),
        "trajectory_format": "DCD single precision coordinates",
        "frames_per_replicate": int(frames),
        "dcd_bytes_per_replicate": int(dcd_per_rep),
        "log_bytes_per_replicate_estimate": int(log_per_rep),
        "checkpoint_bytes_per_replicate_estimate": int(checkpoint_per_rep),
        "replicates": int(replicates),
        "raw_estimated_bytes": int(raw),
        "safety_factor": float(safety_factor),
        "required_free_bytes": int(raw * safety_factor),
    }


def enforce_storage_margin(outdir: Path, estimate: dict) -> None:
    outdir.mkdir(parents=True, exist_ok=True)
    usage = shutil.disk_usage(outdir)
    estimate["free_bytes"] = int(usage.free)
    write_json(outdir / "storage_preflight.json", estimate)
    if usage.free < estimate["required_free_bytes"]:
        need_gb = estimate["required_free_bytes"] / (1024 ** 3)
        free_gb = usage.free / (1024 ** 3)
        sys.exit(f"[storage] FATAL: estimated need {need_gb:.1f} GiB free with safety factor, "
                 f"but only {free_gb:.1f} GiB is available at {outdir}. See "
                 f"{outdir/'storage_preflight.json'}.")
    print("[storage] estimated DCD/log/checkpoint need "
          f"{estimate['required_free_bytes'] / (1024 ** 3):.1f} GiB with safety factor; "
          f"free {usage.free / (1024 ** 3):.1f} GiB")


class GracefulInterrupt(Exception):
    def __init__(self, signum: int):
        self.signum = signum
        super().__init__(f"received signal {signum}")


def save_checkpoint_atomic(sim, chk: Path, meta_path: Path, dt_ns: float,
                           equil_steps: int, reason: str) -> None:
    tmp = chk.with_name(chk.name + ".tmp")
    prev = chk.with_name("state.prev.chk")
    sim.saveCheckpoint(str(tmp))
    if chk.exists():
        shutil.copy2(chk, prev)
    os.replace(tmp, chk)
    step = int(sim.context.getStepCount())
    event = {
        "timestamp_utc": utc_now(),
        "step": step,
        "simulation_time_ns": step * dt_ns,
        "production_time_ns": production_step_to_ns(step, equil_steps, dt_ns),
        "checkpoint": chk.name,
        "reason": reason,
    }
    meta = load_json(meta_path, {"writes_count": 0, "recent_checkpoints": []})
    meta["writes_count"] = int(meta.get("writes_count", 0)) + 1
    meta["last_checkpoint"] = event
    meta["recent_checkpoints"] = (meta.get("recent_checkpoints", []) + [event])[-20:]
    write_json(meta_path, meta)


class AtomicCheckpointReporter:
    """OpenMM reporter that writes checkpoints through a temp file + atomic replace."""

    def __init__(self, chk: Path, interval: int, meta_path: Path, dt_ns: float, equil_steps: int):
        self._chk = chk
        self._interval = int(interval)
        self._meta_path = meta_path
        self._dt_ns = float(dt_ns)
        self._equil_steps = int(equil_steps)

    def describeNextReport(self, simulation):
        steps = self._interval - simulation.currentStep % self._interval
        return {"steps": steps, "periodic": None, "include": []}

    def report(self, simulation, state):
        save_checkpoint_atomic(simulation, self._chk, self._meta_path, self._dt_ns,
                               self._equil_steps, "periodic")


def load_latest_checkpoint(sim, chk: Path, report_every: int, equil_steps: int,
                           dcd: Path, resume_audit: Path, dt_ns: float) -> tuple[bool, str | None]:
    candidates = [p for p in (chk, chk.with_name("state.prev.chk")) if p.exists()]
    candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    audit = load_json(resume_audit, {"resume_count": 0, "resume_events": []})
    invalid = []
    frames = dcd_frame_count(dcd)
    for cand in candidates:
        try:
            sim.loadCheckpoint(str(cand))
            step = int(sim.context.getStepCount())
            max_frames_at_checkpoint = max(0, (step - equil_steps) // report_every)
            if frames is not None and frames > max_frames_at_checkpoint:
                raise RuntimeError(
                    f"trajectory has {frames} frames, but checkpoint step {step} can only "
                    f"account for {max_frames_at_checkpoint}; refusing duplicate-frame risk"
                )
            event = {
                "timestamp_utc": utc_now(),
                "checkpoint_used": cand.name,
                "checkpoint_mtime_utc": datetime.fromtimestamp(
                    cand.stat().st_mtime, timezone.utc).isoformat(),
                "previous_step_from_checkpoint": step,
                "previous_time_ns_from_checkpoint": step * dt_ns,
                "resumed_step": step,
                "resumed_time_ns": step * dt_ns,
                "resumed_production_time_ns": production_step_to_ns(step, equil_steps, dt_ns),
                "existing_dcd_frames": frames,
                "invalid_candidates": invalid,
            }
            audit["resume_count"] = int(audit.get("resume_count", 0)) + 1
            audit["resume_events"] = audit.get("resume_events", []) + [event]
            write_json(resume_audit, audit)
            return True, cand.name
        except Exception as exc:
            invalid.append({"checkpoint": cand.name, "error": str(exc)})
    if invalid:
        audit["invalid_checkpoint_attempts"] = audit.get("invalid_checkpoint_attempts", []) + invalid
        write_json(resume_audit, audit)
    return False, None


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
    props = {}
    try:
        platform = mm.Platform.getPlatformByName(args.platform)
        if args.platform == "CUDA":
            props["Precision"] = args.precision
            device_index = args.cuda_device_index or os.environ.get("OPENMM_CUDA_DEVICE_INDEX")
            if device_index:
                props["DeviceIndex"] = str(device_index)
    except Exception as exc:
        if args.require_platform:
            available = [mm.Platform.getPlatform(i).getName() for i in range(mm.Platform.getNumPlatforms())]
            sys.exit(f"[platform] FATAL: requested OpenMM platform {args.platform!r} is unavailable "
                     f"(available: {available}). {exc}")
        platform = mm.Platform.getPlatformByName("CPU")
        props = {}
        print("[warn] requested platform unavailable; falling back to CPU (slow).")
    sim = Simulation(topology, system, integrator, platform, props)
    args._platform_used = sim.context.getPlatform().getName()
    args._platform_properties = props
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
    mm, unit, _, _, PDBFile, _, _, _, DCDReporter, StateDataReporter, _, _ = _imports()
    import numpy as np

    run_dir.mkdir(parents=True, exist_ok=True)
    chk = run_dir / "state.chk"
    chk_meta = run_dir / "checkpoint_meta.json"
    dcd = run_dir / "production.dcd"
    log = run_dir / "production.log"
    done_flag = run_dir / "DONE.json"
    failed_flag = run_dir / "FAILED.json"
    status_path = run_dir / "STATUS.json"
    provenance_path = run_dir / "PROVENANCE.json"
    resume_audit = run_dir / "RESUME_AUDIT.json"
    ref_npy = run_dir / "equil_backbone_ref.npy"
    min_json = run_dir / "MINIMIZATION.json"

    seed = 20260000 + rep
    dt_fs = 4.0 if args.hmr else 2.0
    dt_ps = dt_fs / 1000.0
    dt_ns = dt_fs / 1_000_000.0
    steps_per_ns = int(round(1.0 / dt_ns))
    equil_steps = int(round(args.equil_ns * steps_per_ns))
    prod_steps = int(round(args.ns * steps_per_ns))
    total_steps = equil_steps + prod_steps
    report_every = max(1, int(round(args.report_ps / dt_ps)))
    chk_every = max(1, int(round(args.checkpoint_ps / dt_ps)))
    if args.report_ps + 1e-12 < args.checkpoint_ps:
        print("[warn] checkpoint interval is longer than output interval; this is allowed but "
              "less restart-efficient.")
    if abs((args.report_ps / args.checkpoint_ps) - round(args.report_ps / args.checkpoint_ps)) > 1e-6:
        print("[warn] report_ps is not an integer multiple of checkpoint_ps; output remains safe, "
              "but checkpoint/output alignment is less clean.")

    target_config = {
        "pocket": args.pocket,
        "role": args.run,
        "pdb": args._pdb_id,
        "replicate": rep,
        "target_ns": args.ns,
        "equil_ns": args.equil_ns,
        "target_total_steps": total_steps,
        "target_production_steps": prod_steps,
        "timestep_fs": dt_fs,
        "report_ps": args.report_ps,
        "checkpoint_ps": args.checkpoint_ps,
        "report_every_steps": report_every,
        "checkpoint_every_steps": chk_every,
        "seed": seed,
    }

    def update_status(status: str, **extra) -> None:
        payload = load_json(status_path, {})
        payload.update({
            "status": status,
            "updated_utc": utc_now(),
            "pid": os.getpid(),
            "hostname": socket.gethostname(),
            "config": target_config,
        })
        payload.update(extra)
        write_json(status_path, payload)

    if done_flag.exists():
        ok, why = validate_done(done_flag, args, rep, total_steps, prod_steps, report_every, dcd)
        if ok:
            update_status("COMPLETE", done_json=str(done_flag), dcd_frames=dcd_frame_count(dcd))
            print(f"[rep{rep}] already complete for target {args.ns} ns -> {done_flag}")
            return "complete"
        if "duplicate-frame" in why:
            write_json(failed_flag, {
                "replicate": rep, "pdb": args._pdb_id, "seed": seed,
                "reason": f"invalid existing DONE.json: {why}",
                "failed_utc": utc_now(),
            })
            update_status("FAILED", reason=why)
            print(f"[rep{rep}] FAILED: {why}")
            return "failed"
        if dcd.exists() and dcd.stat().st_size > 0 and not chk.exists():
            reason = "existing trajectory has no checkpoint; refusing to overwrite or append unsafely"
            write_json(failed_flag, {
                "replicate": rep, "pdb": args._pdb_id, "seed": seed,
                "reason": reason, "failed_utc": utc_now(),
            })
            update_status("FAILED", reason=reason)
            print(f"[rep{rep}] FAILED: {reason}")
            return "failed"
        archived = archive_stale_done(done_flag, why)
        print(f"[rep{rep}] archived stale DONE.json ({why}) -> {archived.name}; continuing safely")

    if failed_flag.exists():
        print(f"[rep{rep}] previously FAILED -> {failed_flag} (delete it to retry)")
        update_status("FAILED", failed_json=str(failed_flag))
        return "failed"

    prior_status = load_json(status_path, {})
    prior_config = prior_status.get("config", {}) if isinstance(prior_status, dict) else {}
    if dcd.exists() and dcd.stat().st_size > 0 and prior_config:
        for key in ("timestep_fs", "report_ps", "equil_ns", "pdb", "role"):
            if str(prior_config.get(key)) != str(target_config.get(key)):
                reason = (f"existing trajectory config {key}={prior_config.get(key)!r} differs "
                          f"from requested {target_config.get(key)!r}; refusing unsafe append")
                write_json(failed_flag, {
                    "replicate": rep, "pdb": args._pdb_id, "seed": seed,
                    "reason": reason, "failed_utc": utc_now(),
                })
                update_status("FAILED", reason=reason)
                print(f"[rep{rep}] FAILED: {reason}")
                return "failed"

    run_start_wall = time.time()
    update_status("RUNNING", started_utc=prior_status.get("started_utc") or utc_now(),
                  current_step=0, current_production_ns=0.0)

    sim, dt = make_simulation(ff, topology, positions, args, seed)
    platform_used = getattr(args, "_platform_used", None)
    precision = getattr(args, "_platform_properties", {}).get("Precision")
    if args.require_platform and platform_used != args.platform:
        reason = f"required platform {args.platform} but simulation is using {platform_used}"
        write_json(failed_flag, {
            "replicate": rep, "pdb": args._pdb_id, "seed": seed,
            "reason": reason, "failed_utc": utc_now(),
        })
        update_status("FAILED", reason=reason)
        print(f"[rep{rep}] FAILED: {reason}")
        return "failed"

    existing_prov = load_json(provenance_path, {})
    provenance = existing_prov if isinstance(existing_prov, dict) else {}
    provenance.update({
        "schema_version": 1,
        "structure_pdb_id": args._pdb_id,
        "role": args.run,
        "replicate": rep,
        "random_seed": seed,
        "start_utc": provenance.get("start_utc") or utc_now(),
        "end_utc": None,
        "resumed": False,
        "system_atom_count": int(topology.getNumAtoms()),
        "environment": runtime_environment(platform_used=platform_used, precision=precision),
        "git": git_info(),
        "scientific_parameters": {
            "force_field": ["amber14-all.xml", "amber14/tip3p.xml"],
            "water_model": "TIP3P",
            "salt_concentration_molar": args.ionic,
            "temperature_kelvin": args.temp,
            "pressure_bar": args.pressure,
            "timestep_fs": dt_fs,
            "hmr_enabled": args.hmr,
            "hmr_hydrogen_mass_amu": args.hmr_amu if args.hmr else 1.0,
            "pme_cutoff_nm": 1.0,
            "constraints": "HBonds",
            "rigid_water": True,
            "equilibration_ns": args.equil_ns,
            "production_ns": args.ns,
            "output_interval_ps": args.report_ps,
            "checkpoint_interval_ps": args.checkpoint_ps,
            "minimization_max_iterations": args.min_steps,
        },
        "input_hashes": {
            "prepared_protein_pdb_sha256": sha256_file(run_dir.parent / "prep" / "prepared_protein.pdb"),
            "system_solvated_pdb_sha256": sha256_file(solvated_pdb),
            "pocket_definition_sha256": sha256_file(HERE / "pockets" / f"{args.pocket}.json"),
            "frozen_analysis_protocol_sha256": sha256_file(HERE / "FROZEN_MD_ANALYSIS_PROTOCOL.json"),
        },
        "command": " ".join([shlex.quote(x) for x in sys.argv]),
    })
    write_json(provenance_path, provenance)

    backbone = _backbone_indices(topology)
    append = False
    minimization_report = load_json(min_json, None)
    resumed, checkpoint_used = (False, None)
    if chk.exists():
        resumed, checkpoint_used = load_latest_checkpoint(sim, chk, report_every, equil_steps,
                                                          dcd, resume_audit, dt_ns)
        if not resumed:
            reason = "checkpoint exists but no valid checkpoint could be loaded"
            write_json(failed_flag, {
                "replicate": rep, "pdb": args._pdb_id, "seed": seed,
                "reason": reason, "failed_utc": utc_now(),
            })
            update_status("FAILED", reason=reason)
            print(f"[rep{rep}] FAILED: {reason}")
            return "failed"
        append = True
        resume_count = load_json(resume_audit, {}).get("resume_count", 1)
        provenance["resumed"] = True
        provenance["resume_count"] = resume_count
        provenance["checkpoint_used_for_latest_resume"] = checkpoint_used
        write_json(provenance_path, provenance)
        print(f"[rep{rep}] resumed from {checkpoint_used} at step {sim.context.getStepCount()}")
    else:
        print(f"[rep{rep}] minimize + equilibrate ({args.equil_ns} ns) ...")
        initial_state = sim.context.getState(getEnergy=True, getForces=True)
        initial_pe = initial_state.getPotentialEnergy().value_in_unit(unit.kilojoule_per_mole)
        initial_forces = initial_state.getForces(asNumpy=True).value_in_unit(
            unit.kilojoule_per_mole / unit.nanometer
        )
        sim.minimizeEnergy(maxIterations=args.min_steps)
        min_state = sim.context.getState(getEnergy=True, getForces=True)
        min_pe = min_state.getPotentialEnergy().value_in_unit(unit.kilojoule_per_mole)
        min_forces = min_state.getForces(asNumpy=True).value_in_unit(
            unit.kilojoule_per_mole / unit.nanometer
        )
        minimization_report = {
            "initial_potential_kj_mol": float(initial_pe),
            "minimized_potential_kj_mol": float(min_pe),
            "delta_potential_kj_mol": float(min_pe - initial_pe),
            "max_force_initial_kj_mol_nm": float(np.sqrt((initial_forces * initial_forces).sum(axis=1)).max()),
            "max_force_minimized_kj_mol_nm": float(np.sqrt((min_forces * min_forces).sum(axis=1)).max()),
            "max_iterations": args.min_steps,
        }
        write_json(min_json, minimization_report)
        sim.context.setVelocitiesToTemperature(args.temp * unit.kelvin, seed)
        if equil_steps > 0:
            sim.step(equil_steps)
        save_checkpoint_atomic(sim, chk, chk_meta, dt_ns, equil_steps, "post_equilibration")
        if backbone:
            eq_xyz = sim.context.getState(getPositions=True, enforcePeriodicBox=False
                                          ).getPositions(asNumpy=True).value_in_unit(unit.nanometer)
            np.save(str(ref_npy), np.asarray(eq_xyz)[backbone])

    done_steps = int(sim.context.getStepCount())
    sim.reporters.append(AtomicCheckpointReporter(chk, chk_every, chk_meta, dt_ns, equil_steps))
    if prod_steps > 0:
        sim.reporters.append(DCDReporter(str(dcd), report_every, append=append))
        sim.reporters.append(StateDataReporter(str(log), report_every, step=True, time=True,
                             potentialEnergy=True, temperature=True, density=True,
                             progress=True, remainingTime=True, speed=True,
                             totalSteps=total_steps, separator="\t", append=append))
        sim.reporters.append(StateDataReporter(sys.stdout, max(report_every * 20, report_every),
                             step=True, temperature=True, speed=True, progress=True,
                             totalSteps=total_steps))

    print(f"[rep{rep}] production: target {args.ns} ns ({prod_steps} steps) "
          f"+ {args.equil_ns} ns equil, already at step {done_steps}; "
          f"checkpoint every {args.checkpoint_ps} ps, output every {args.report_ps} ps")

    old_handlers = {}

    def handle_signal(signum, _frame):
        raise GracefulInterrupt(signum)

    for sig in (signal.SIGINT, signal.SIGTERM):
        old_handlers[sig] = signal.getsignal(sig)
        signal.signal(sig, handle_signal)

    try:
        while sim.context.getStepCount() < total_steps:
            remaining = total_steps - sim.context.getStepCount()
            sim.step(min(chk_every, remaining))
            current_step = int(sim.context.getStepCount())
            update_status("RUNNING", current_step=current_step,
                          current_time_ns=current_step * dt_ns,
                          current_production_ns=production_step_to_ns(current_step, equil_steps, dt_ns),
                          dcd_frames=dcd_frame_count(dcd))
            if args.debug_sleep_per_chunk > 0:
                time.sleep(args.debug_sleep_per_chunk)
    except GracefulInterrupt as exc:
        try:
            save_checkpoint_atomic(sim, chk, chk_meta, dt_ns, equil_steps,
                                   f"interrupted_signal_{exc.signum}")
        finally:
            step = int(sim.context.getStepCount())
            update_status("RESUMABLE", interrupted_utc=utc_now(), signal=exc.signum,
                          current_step=step, current_time_ns=step * dt_ns,
                          current_production_ns=production_step_to_ns(step, equil_steps, dt_ns),
                          checkpoint=str(chk), dcd_frames=dcd_frame_count(dcd))
        print(f"[rep{rep}] INTERRUPTED by signal {exc.signum}; checkpoint saved at step {step}")
        return "interrupted"
    except Exception as exc:
        step = int(sim.context.getStepCount())
        write_json(failed_flag, {
            "replicate": rep, "pdb": args._pdb_id, "seed": seed,
            "steps": step,
            "reason": "exception during integration (numerical blow-up or runtime failure)",
            "error": str(exc),
            "failed_utc": utc_now(),
        })
        update_status("FAILED", current_step=step, reason=str(exc), dcd_frames=dcd_frame_count(dcd))
        print(f"[rep{rep}] FAILED during integration: {exc}")
        return "failed"
    finally:
        for sig, handler in old_handlers.items():
            signal.signal(sig, handler)

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
        try:
            rmsd_nm = _kabsch_rmsd_nm(final_xyz[backbone], np.load(str(ref_npy)))
            if not (rmsd_nm < args.rmsd_fail_nm):
                reason = (f"final backbone RMSD to equilibrated start {rmsd_nm:.2f} nm "
                          f">= {args.rmsd_fail_nm} nm (blow-up / gross unfolding)")
        except Exception as exc:
            print(f"[rep{rep}] warn: RMSD gate could not run ({exc}); "
                  f"relying on energy/coordinate finiteness only")

    if reason is not None:
        step = int(sim.context.getStepCount())
        write_json(failed_flag, {
            "replicate": rep, "pdb": args._pdb_id, "seed": seed,
            "steps": step,
            "final_potential_kj_mol": pe if math.isfinite(pe) else None,
            "backbone_rmsd_nm": rmsd_nm, "reason": reason,
            "failed_utc": utc_now(),
        })
        update_status("FAILED", current_step=step, reason=reason, dcd_frames=dcd_frame_count(dcd))
        print(f"[rep{rep}] FAILED sanity gate: {reason}")
        return "failed"

    save_checkpoint_atomic(sim, chk, chk_meta, dt_ns, equil_steps, "complete")
    final_step = int(sim.context.getStepCount())
    production_ns = production_step_to_ns(final_step, equil_steps, dt_ns)
    wall_seconds = time.time() - run_start_wall
    ns_per_day = (production_ns / wall_seconds * 86400.0) if wall_seconds > 0 and production_ns > 0 else None
    resume_count = int(load_json(resume_audit, {}).get("resume_count", 0))
    done_payload = {
        "replicate": rep, "pdb": args._pdb_id, "role": args.run, "ns": args.ns,
        "production_ns": production_ns, "equil_ns": args.equil_ns,
        "report_ps": args.report_ps, "checkpoint_ps": args.checkpoint_ps,
        "seed": seed,
        "steps": final_step, "target_total_steps": total_steps,
        "timestep_fs": dt_fs,
        "hmr": args.hmr, "hmr_amu": (args.hmr_amu if args.hmr else 1.0),
        "final_potential_kj_mol": pe, "backbone_rmsd_nm": rmsd_nm,
        "minimization": minimization_report,
        "sanity_gate": ("passed: finite energy+coords" +
                        (f", backbone RMSD {rmsd_nm:.2f} nm < {args.rmsd_fail_nm} nm"
                         if rmsd_nm is not None else ", RMSD ref unavailable")),
        "topology": str(solvated_pdb.name), "trajectory": str(dcd.name),
        "dcd_frames": dcd_frame_count(dcd),
        "checkpoint": str(chk.name),
        "resumed": bool(resume_count),
        "resume_count": resume_count,
        "wall_seconds": wall_seconds,
        "ns_per_day_observed": ns_per_day,
        "started_utc": provenance.get("start_utc"),
        "finished_utc": utc_now(),
    }
    write_json(done_flag, done_payload)
    provenance.update({
        "end_utc": done_payload["finished_utc"],
        "resumed": bool(resume_count),
        "resume_count": resume_count,
        "final_simulation_time_ns": final_step * dt_ns,
        "final_production_time_ns": production_ns,
        "observed_ns_per_day": ns_per_day,
        "status": "COMPLETE",
    })
    write_json(provenance_path, provenance)
    update_status("COMPLETE", current_step=final_step, current_time_ns=final_step * dt_ns,
                  current_production_ns=production_ns, done_json=str(done_flag),
                  dcd_frames=dcd_frame_count(dcd), ns_per_day_observed=ns_per_day)
    print(f"[rep{rep}] DONE ({final_step} steps, PE={pe:.0f} kJ/mol, prod {production_ns:.3f} ns"
          + (f", {ns_per_day:.2f} ns/day" if ns_per_day else "")
          + (f", bbRMSD {rmsd_nm:.2f} nm)" if rmsd_nm is not None else ")"))
    return "complete"


def main():
    p = argparse.ArgumentParser(description="PCNA cryptic-pocket MD validation (RTX 4070, v2).")
    p.add_argument("--pocket", default="final_consensus_1w60_20260815",
                   help="pocket name -> pockets/<name>.json")
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
    p.add_argument("--checkpoint-ps", type=float, default=10.0,
                   help="checkpoint interval; default 10 ps limits crash loss without changing "
                        "the frozen 50 ps trajectory cadence")
    p.add_argument("--hmr", action="store_true", default=True)
    p.add_argument("--no-hmr", dest="hmr", action="store_false")
    p.add_argument("--hmr-amu", type=float, default=4.0,
                   help="repartitioned hydrogen mass (amu); ~4.0 is required to keep a 4 fs step stable")
    p.add_argument("--rmsd-fail-nm", type=float, default=1.0,
                   help="post-run backbone RMSD (nm) to equilibrated start above which a replicate is FAILED")
    p.add_argument("--platform", default="CUDA")
    p.add_argument("--require-platform", action="store_true",
                   help="fail instead of falling back if --platform is unavailable")
    p.add_argument("--precision", default="mixed", choices=["single", "mixed", "double"],
                   help="OpenMM CUDA precision mode")
    p.add_argument("--cuda-device-index", default=None,
                   help="optional OpenMM CUDA DeviceIndex; scientific parameters are unchanged")
    p.add_argument("--storage-safety-factor", type=float, default=1.5,
                   help="free-space safety factor over estimated DCD/log/checkpoint bytes")
    p.add_argument("--debug-sleep-per-chunk", type=float, default=0.0,
                   help=argparse.SUPPRESS)
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
    dt_fs = 4.0 if args.hmr else 2.0
    dt_ps = dt_fs / 1000.0
    dt_ns = dt_fs / 1_000_000.0
    prod_steps = int(round(args.ns / dt_ns))
    report_every = max(1, int(round(args.report_ps / dt_ps)))
    estimate = estimate_output_bytes(
        topology.getNumAtoms(), prod_steps, report_every, args.replicates,
        args.storage_safety_factor,
    )
    estimate.update({
        "pocket": args.pocket,
        "role": args.run,
        "pdb_id": pdb_id,
        "production_ns_per_replicate": args.ns,
        "output_interval_ps": args.report_ps,
        "checkpoint_interval_ps": args.checkpoint_ps,
    })
    enforce_storage_margin(root, estimate)
    (root / "pocket_definition.json").write_text(json.dumps(
        {"pocket": pocket["pocket_name"], "run": args.run, "pdb_id": pdb_id,
         "pocket_residues_resseq": pocket_resseq,
         "core_3of3": pocket.get("core_3of3"),
         "fringe_2of3": pocket.get("fringe_2of3"),
         "uncertain_fringe_1of3": pocket.get("uncertain_fringe_1of3"),
         "interface_chain_indices": pocket.get("interface_chain_indices", [0, 1]),
         "note": "Analysis (analyze_md.py) targets these residues on the biological assembly."},
        indent=2))

    t0 = time.time()
    results = []
    for rep in range(1, args.replicates + 1):
        result = run_replicate(ff, topology, positions, solvated, root / f"rep{rep:02d}", rep, args)
        results.append(result)
        if result == "interrupted":
            print(f"\nRun interrupted after replicate {rep}; re-run the same command to resume.")
            sys.exit(130)
    elapsed_h = (time.time() - t0) / 3600
    if any(r == "failed" for r in results):
        print(f"\nOne or more replicates failed for {pdb_id} ({args.run}) after {elapsed_h:.2f} h. "
              "Inspect FAILED.json/STATUS.json before retrying.")
        sys.exit(1)
    print(f"\nAll requested replicates for {pdb_id} ({args.run}) are complete in {elapsed_h:.2f} h. "
          f"Next: run the other structure if needed, then `python analyze_md.py --pocket {args.pocket}`.")


if __name__ == "__main__":
    main()
