"""
PCNA 1W60 MD simulation — run locally on a CUDA GPU.

Pre-requisites (run once):
    conda install -c conda-forge openmm mdanalysis

The pre-built system files are already in data/md/:
    1W60_solvated.pdb  — solvated topology (CHARMM36m, TIP3P, 150 mM NaCl)
    system.xml         — serialized OpenMM system (PME, HBonds, HMR 4 fs)

Usage:
    python scripts/run_simulation_local.py
    python scripts/run_simulation_local.py --ns 10   # shorter run
    python scripts/run_simulation_local.py --ns 100  # full 100 ns
"""
from __future__ import annotations
import sys, time, json, argparse
from pathlib import Path

# Force UTF-8 on Windows consoles that default to cp1252
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

REPO = Path(__file__).parent.parent
DATA = REPO / "data" / "md"
OUT  = REPO / "data" / "results"
OUT.mkdir(parents=True, exist_ok=True)


class ProgressReporter:
    """In-place progress bar for OpenMM production runs. No dependencies."""

    def __init__(self, total_steps: int, ns: float, report_interval: int):
        self._total   = total_steps
        self._ns      = ns
        self._interval = report_interval
        self._t0      = time.time()
        self._bar_width = 30

    def describeNextReport(self, simulation):
        steps_done = simulation.currentStep
        steps_left = self._interval - (steps_done % self._interval)
        return (steps_left, False, False, False, True)

    def report(self, simulation, state):
        step     = simulation.currentStep
        pct      = step / self._total
        elapsed  = time.time() - self._t0
        ns_done  = step / 250_000
        speed    = (ns_done / (elapsed / 86400)) if elapsed > 0 else 0
        eta_s    = ((self._ns - ns_done) / speed * 86400) if speed > 0 else 0
        eta_str  = self._fmt_time(eta_s)

        filled = int(self._bar_width * pct)
        bar    = "#" * filled + "-" * (self._bar_width - filled)
        temp   = state.getKineticEnergy()._value  # rough proxy, not shown

        line = (
            f"\r  [{bar}] {pct*100:5.1f}%  "
            f"{ns_done:6.1f}/{self._ns:.0f} ns  |  "
            f"{speed:6.1f} ns/day  |  ETA {eta_str}   "
        )
        sys.stdout.write(line)
        sys.stdout.flush()

        if step >= self._total:
            sys.stdout.write("\n")
            sys.stdout.flush()

    @staticmethod
    def _fmt_time(seconds: float) -> str:
        if seconds <= 0:
            return "--:--"
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        return f"{h}h {m:02d}m"


def check_gpu():
    from openmm import Platform
    platforms = {Platform.getPlatform(i).getName()
                 for i in range(Platform.getNumPlatforms())}
    print(f"Available OpenMM platforms: {sorted(platforms)}")
    if "CUDA" in platforms:
        print("CUDA GPU detected - using CUDA (mixed precision)")
        return "CUDA", {"CudaPrecision": "mixed"}
    if "OpenCL" in platforms:
        print("WARNING: No CUDA found, falling back to OpenCL (slow)")
        return "OpenCL", {"OpenCLPrecision": "mixed"}
    print("WARNING: CPU only - this will be very slow for 356k atoms")
    return "CPU", {}


def run(ns: float = 100.0):
    from openmm.app import (
        PDBFile, Simulation, DCDReporter,
        StateDataReporter, CheckpointReporter
    )
    from openmm import (
        XmlSerializer, LangevinMiddleIntegrator,
        MonteCarloBarostat, Platform, unit
    )

    top_path  = DATA / "1W60_solvated.pdb"
    sys_path  = DATA / "system.xml"
    out_dcd   = DATA / "1W60_production.dcd"
    out_top   = DATA / "1W60_topology.pdb"
    out_log   = DATA / "production.log"
    out_chk   = DATA / "production.chk"

    if not top_path.exists() or not sys_path.exists():
        print(f"ERROR: Missing files in {DATA}/")
        print("  Expected: 1W60_solvated.pdb  system.xml")
        print("  Clone the GNN_PCNA repo -- both files are committed.")
        sys.exit(1)

    # Load
    print(f"\nLoading solvated system ({top_path.name})...")
    pdb = PDBFile(str(top_path))
    print(f"  {pdb.topology.getNumAtoms():,} atoms, {pdb.topology.getNumResidues():,} residues")

    print("Loading serialized force field (system.xml)...")
    with open(sys_path) as f:
        system = XmlSerializer.deserialize(f.read())

    integrator = LangevinMiddleIntegrator(
        310 * unit.kelvin,
        1.0 / unit.picosecond,
        4.0 * unit.femtosecond,
    )

    platform_name, props = check_gpu()
    platform = Platform.getPlatformByName(platform_name)
    simulation = Simulation(pdb.topology, system, integrator, platform, props)
    simulation.context.setPositions(pdb.positions)

    # Minimization
    print("\n[1/4] Energy minimization...")
    simulation.minimizeEnergy(maxIterations=2000)
    pe = simulation.context.getState(getEnergy=True).getPotentialEnergy()
    print(f"  PE: {pe}")

    # NVT equilibration — heat 100 K -> 310 K over 1 ns
    print("\n[2/4] NVT equilibration (1 ns, 100 -> 310 K)...")
    simulation.context.setVelocitiesToTemperature(100 * unit.kelvin)
    simulation.reporters.append(
        StateDataReporter(sys.stdout, 25_000,
            step=True, temperature=True, speed=True)
    )
    for T in range(100, 311, 10):
        integrator.setTemperature(T * unit.kelvin)
        simulation.step(5_000)
    simulation.step(125_000)
    print("  NVT done")
    simulation.saveCheckpoint(str(DATA / "equil_nvt.chk"))

    # NPT equilibration — 1 ns at 1 atm
    print("\n[3/4] NPT equilibration (1 ns, 310 K, 1 atm)...")
    barostat = MonteCarloBarostat(1.0 * unit.bar, 310 * unit.kelvin, 25)
    system.addForce(barostat)
    simulation.context.reinitialize(preserveState=True)

    simulation.reporters.clear()
    simulation.reporters.append(
        StateDataReporter(sys.stdout, 25_000,
            step=True, temperature=True, volume=True, density=True, speed=True)
    )
    simulation.step(250_000)
    print("  NPT done")
    simulation.saveCheckpoint(str(DATA / "equil_npt.chk"))

    state = simulation.context.getState(getPositions=True)
    with open(out_top, "w") as f:
        PDBFile.writeFile(simulation.topology, state.getPositions(), f)
    print(f"  Topology saved: {out_top.relative_to(REPO)}")

    # Production
    STEPS_PER_NS = 250_000
    PROD_STEPS   = int(ns * STEPS_PER_NS)
    SAVE_EVERY   = 2_500      # 10 ps per frame

    print(f"\n[4/4] Production run ({ns:.0f} ns = {PROD_STEPS:,} steps)...")
    simulation.reporters.clear()
    simulation.reporters.append(DCDReporter(str(out_dcd), SAVE_EVERY))
    simulation.reporters.append(
        StateDataReporter(str(out_log), 250_000,
            step=True, time=True, potentialEnergy=True, kineticEnergy=True,
            temperature=True, volume=True, speed=True,
            progress=True, remainingTime=True, totalSteps=PROD_STEPS)
    )
    simulation.reporters.append(
        ProgressReporter(PROD_STEPS, ns, report_interval=250_000)
    )
    simulation.reporters.append(
        CheckpointReporter(str(out_chk), 2_500_000)  # every 10 ns
    )

    t0 = time.time()
    simulation.step(PROD_STEPS)
    elapsed = time.time() - t0
    speed_ns_day = ns / (elapsed / 86400)

    print(f"\nProduction complete:")
    print(f"  Wall time : {elapsed/3600:.1f} hours")
    print(f"  Speed     : {speed_ns_day:.1f} ns/day")
    print(f"  Trajectory: {out_dcd.relative_to(REPO)}")

    meta = {
        "structure": "1W60 apo PCNA",
        "forcefield": "CHARMM36m + TIP3P",
        "n_atoms": pdb.topology.getNumAtoms(),
        "sim_ns": ns,
        "timestep_fs": 4.0,
        "save_interval_ps": 10.0,
        "n_frames": PROD_STEPS // SAVE_EVERY,
        "temperature_K": 310,
        "pressure_bar": 1.0,
        "ionic_strength_mM": 150,
        "platform": platform_name,
        "wall_time_hours": round(elapsed / 3600, 2),
        "speed_ns_day": round(speed_ns_day, 1),
        "trajectory": str(out_dcd.relative_to(REPO)),
        "topology": str(out_top.relative_to(REPO)),
    }
    meta_path = OUT / "md_run_metadata.json"
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"  Metadata  : {meta_path.relative_to(REPO)}")
    print(f"\nNext: python scripts\\run_md_analysis.py")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ns", type=float, default=100.0,
                        help="Production run length in nanoseconds (default: 100)")
    args = parser.parse_args()
    run(args.ns)


if __name__ == "__main__":
    main()
