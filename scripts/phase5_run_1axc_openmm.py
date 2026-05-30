#!/usr/bin/env python
"""Run budget-constrained 1AXC apo-from-p21 short OpenMM MD replicates.

The default production scope is the approved budget-constrained Phase 5 plan:
3 x 25 ns on 1AXC PCNA trimer, p21 removed. This script does not train,
evaluate, or run PCNA inference.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import platform
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


PS_PER_STEP = 0.002  # 2 fs
STEPS_PER_NS = int(1000 / PS_PER_STEP)


def _import_dependencies():
    try:
        import openmm as mm
        from openmm import unit
        from openmm.app import (
            PME,
            HBonds,
            CheckpointReporter,
            DCDReporter,
            ForceField,
            Modeller,
            PDBFile,
            Simulation,
            StateDataReporter,
        )
    except Exception as exc:  # pragma: no cover - environment-specific
        raise SystemExit(
            "Missing OpenMM dependencies. Create and activate the RunPod conda env: "
            "`conda env create -f envs/phase5_md_runpod.yml && conda activate phase5-md`."
        ) from exc
    return {
        "mm": mm,
        "unit": unit,
        "PDBFile": PDBFile,
        "ForceField": ForceField,
        "Modeller": Modeller,
        "Simulation": Simulation,
        "DCDReporter": DCDReporter,
        "StateDataReporter": StateDataReporter,
        "CheckpointReporter": CheckpointReporter,
        "PME": PME,
        "HBonds": HBonds,
    }


def parse_window(value: str) -> tuple[int, int]:
    left, right = value.split("-", 1)
    return int(left), int(right)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run budget-constrained Phase 5 1AXC OpenMM MD replicates."
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("outputs/phase5_md/time_crunch_1axc_25ns"),
        help="Run output root.",
    )
    parser.add_argument("--replicates", type=int, default=3)
    parser.add_argument("--production-ns", type=float, default=25.0)
    parser.add_argument(
        "--seeds",
        nargs="+",
        type=int,
        default=[2026052901, 2026052902, 2026052903],
    )
    parser.add_argument(
        "--windows",
        nargs="+",
        default=["239-243", "28-32", "206-210", "134-138"],
    )
    parser.add_argument("--reference-window", default="118-122")
    parser.add_argument("--temperature-k", type=float, default=300.0)
    parser.add_argument("--pressure-bar", type=float, default=1.0)
    parser.add_argument("--ph", type=float, default=7.4)
    parser.add_argument("--padding-nm", type=float, default=1.0)
    parser.add_argument("--ionic-strength-molar", type=float, default=0.15)
    parser.add_argument("--minimize-steps", type=int, default=2000)
    parser.add_argument("--nvt-ps", type=float, default=100.0)
    parser.add_argument("--npt-ps", type=float, default=250.0)
    parser.add_argument("--report-ps", type=float, default=50.0)
    parser.add_argument("--trajectory-ps", type=float, default=100.0)
    parser.add_argument("--checkpoint-ps", type=float, default=250.0)
    parser.add_argument("--chunk-ps", type=float, default=50.0)
    parser.add_argument("--max-wall-hours", type=float, default=4.0)
    parser.add_argument("--hourly-cost-usd", type=float, default=6.0)
    parser.add_argument("--target-cost-usd", type=float, default=27.0)
    parser.add_argument("--hard-cost-usd", type=float, default=30.0)
    parser.add_argument(
        "--platform",
        default="CUDA",
        help="OpenMM platform. Default CUDA. Use CPU only for tiny smoke tests.",
    )
    parser.add_argument(
        "--smoke-test",
        action="store_true",
        help="Run a tiny 0.01 ns single-replicate workflow for environment validation.",
    )
    parser.add_argument(
        "--prepare-only",
        action="store_true",
        help="Prepare 1AXC input and manifest, then stop before MD.",
    )
    return parser.parse_args()


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git_commit() -> str | None:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return None


def run_prepare(output_root: Path, ph: float) -> Path:
    prepared = output_root / "inputs" / "1axc_pcna_apo_from_p21_prepared.pdb"
    if prepared.exists():
        return prepared
    script = Path(__file__).with_name("phase5_prepare_1axc_openmm.py")
    cmd = [
        sys.executable,
        str(script),
        "--output-root",
        str(output_root),
        "--pcna-chains",
        "A",
        "C",
        "E",
        "--ph",
        str(ph),
    ]
    subprocess.check_call(cmd)
    if not prepared.exists():
        raise SystemExit(f"Preparation did not create expected PDB: {prepared}")
    return prepared


def write_manifest(args: argparse.Namespace, prepared_pdb: Path, deps: dict[str, object]) -> None:
    manifest = args.output_root / "MANIFEST.md"
    command = " ".join([sys.executable, *sys.argv])
    openmm_module = deps["mm"]
    content = f"""# Phase 5 Budget-Constrained 1AXC MD Manifest

- Artifact ID: phase5_time_crunch_1axc_3x25ns
- Artifact path: `{args.output_root}`
- Created at: {datetime.now(timezone.utc).isoformat()}
- Commit hash: {git_commit()}
- Command: `{command}`
- Environment: Python {platform.python_version()} on {platform.platform()}
- OpenMM version: {getattr(openmm_module, '__version__', 'unknown')}
- Input structure: `{prepared_pdb}`
- Input structure SHA256: `{sha256(prepared_pdb)}`
- System: 1AXC PCNA trimer, p21 chains removed, apo-from-p21
- Force field: OpenMM `amber14-all.xml` protein parameters, `amber14/tip3p.xml` water
- Water/ions: TIP3P, neutralized, 0.15 M ionic strength
- Temperature: {args.temperature_k} K
- Pressure: {args.pressure_bar} bar
- Replicates: {args.replicates}
- Production length per replicate: {args.production_ns} ns
- Seeds: {args.seeds[:args.replicates]}
- Windows: {args.windows}
- Reference window: {args.reference_window}
- Budget target USD: {args.target_cost_usd}
- Budget hard cap USD: {args.hard_cost_usd}
- Governance:
  - `docs/scientific_governance/12_PCNA_SPECIFIC_CHECKS.md`
  - `docs/scientific_governance/13_MD_VALIDATION_RULES.md`
  - `docs/scientific_governance/14_CLAIM_POLICY.md`
  - `docs/scientific_governance/15_PROVENANCE_AND_REPRODUCIBILITY.md`
- Known limitations:
  - Exploratory short-timescale MD only.
  - Not official GATE 7 Wave 1 completion.
  - 8GLA positive-control systems are deferred.
  - Results cannot support validated-site, druggability, therapeutic, or mechanism claims.
"""
    manifest.write_text(content, encoding="utf-8")


def projected_cost(start: float, hourly_cost: float) -> float:
    return ((time.monotonic() - start) / 3600.0) * hourly_cost


def check_budget(args: argparse.Namespace, start: float, context: str) -> None:
    elapsed_h = (time.monotonic() - start) / 3600.0
    cost = elapsed_h * args.hourly_cost_usd
    if elapsed_h >= args.max_wall_hours or cost >= args.hard_cost_usd:
        raise SystemExit(
            f"Stopping at {context}: elapsed={elapsed_h:.2f}h projected_cost=${cost:.2f}; "
            "hard wall/cost guard reached."
        )
    if cost >= args.target_cost_usd:
        raise SystemExit(
            f"Stopping at {context}: projected_cost=${cost:.2f} reached target guard "
            f"${args.target_cost_usd:.2f}."
        )


def steps_from_ps(ps_value: float) -> int:
    return max(1, int(round(ps_value / PS_PER_STEP)))


def run_replicate(
    args: argparse.Namespace,
    deps: dict[str, object],
    prepared_pdb: Path,
    replicate_idx: int,
    seed: int,
    start_time: float,
) -> None:
    mm = deps["mm"]
    unit = deps["unit"]
    PDBFile = deps["PDBFile"]
    ForceField = deps["ForceField"]
    Modeller = deps["Modeller"]
    Simulation = deps["Simulation"]
    DCDReporter = deps["DCDReporter"]
    StateDataReporter = deps["StateDataReporter"]
    CheckpointReporter = deps["CheckpointReporter"]
    PME = deps["PME"]
    HBonds = deps["HBonds"]

    rep_dir = args.output_root / f"replicate_{replicate_idx:02d}"
    rep_dir.mkdir(parents=True, exist_ok=True)
    checkpoint = rep_dir / "checkpoint.chk"
    final_pdb = rep_dir / "final.pdb"
    complete_marker = rep_dir / "COMPLETE.json"
    if complete_marker.exists():
        print(f"Replicate {replicate_idx}: COMPLETE marker exists, skipping.")
        return

    pdb = PDBFile(str(prepared_pdb))
    forcefield = ForceField("amber14-all.xml", "amber14/tip3p.xml")
    modeller = Modeller(pdb.topology, pdb.positions)
    modeller.addSolvent(
        forcefield,
        model="tip3p",
        padding=args.padding_nm * unit.nanometer,
        ionicStrength=args.ionic_strength_molar * unit.molar,
        neutralize=True,
    )
    solvated_pdb = rep_dir / "solvated_initial.pdb"
    if not solvated_pdb.exists():
        with solvated_pdb.open("w", encoding="utf-8") as handle:
            deps["PDBFile"].writeFile(modeller.topology, modeller.positions, handle, keepIds=True)

    system = forcefield.createSystem(
        modeller.topology,
        nonbondedMethod=PME,
        nonbondedCutoff=1.0 * unit.nanometer,
        constraints=HBonds,
    )
    system.addForce(mm.MonteCarloBarostat(args.pressure_bar * unit.bar, args.temperature_k * unit.kelvin))
    integrator = mm.LangevinMiddleIntegrator(
        args.temperature_k * unit.kelvin,
        1.0 / unit.picosecond,
        PS_PER_STEP * unit.picoseconds,
    )
    integrator.setRandomNumberSeed(seed)

    platform_obj = mm.Platform.getPlatformByName(args.platform)
    properties = {"Precision": "mixed"} if args.platform.upper() == "CUDA" else {}
    simulation = Simulation(modeller.topology, system, integrator, platform_obj, properties)

    if checkpoint.exists():
        print(f"Replicate {replicate_idx}: loading checkpoint {checkpoint}")
        with checkpoint.open("rb") as handle:
            simulation.context.loadCheckpoint(handle.read())
    else:
        simulation.context.setPositions(modeller.positions)
        print(f"Replicate {replicate_idx}: minimizing")
        simulation.minimizeEnergy(maxIterations=args.minimize_steps)
        check_budget(args, start_time, f"replicate {replicate_idx} after minimize")
        print(f"Replicate {replicate_idx}: NVT {args.nvt_ps} ps")
        simulation.step(steps_from_ps(args.nvt_ps))
        check_budget(args, start_time, f"replicate {replicate_idx} after NVT")
        print(f"Replicate {replicate_idx}: NPT {args.npt_ps} ps")
        simulation.step(steps_from_ps(args.npt_ps))
        with checkpoint.open("wb") as handle:
            handle.write(simulation.context.createCheckpoint())

    simulation.reporters.append(
        DCDReporter(
            str(rep_dir / "trajectory.dcd"),
            steps_from_ps(args.trajectory_ps),
            append=(rep_dir / "trajectory.dcd").exists(),
        )
    )
    simulation.reporters.append(
        StateDataReporter(
            str(rep_dir / "state.csv"),
            steps_from_ps(args.report_ps),
            step=True,
            time=True,
            potentialEnergy=True,
            temperature=True,
            density=True,
            speed=True,
            progress=True,
            remainingTime=True,
            totalSteps=int(round(args.production_ns * STEPS_PER_NS)),
            separator=",",
            append=(rep_dir / "state.csv").exists(),
        )
    )
    simulation.reporters.append(
        CheckpointReporter(str(checkpoint), steps_from_ps(args.checkpoint_ps))
    )

    total_steps = int(round(args.production_ns * STEPS_PER_NS))
    chunk_steps = steps_from_ps(args.chunk_ps)
    run_steps = 0
    progress_json = rep_dir / "progress.json"
    if progress_json.exists():
        try:
            run_steps = int(json.loads(progress_json.read_text(encoding="utf-8")).get("production_steps_completed", 0))
        except Exception:
            run_steps = 0

    print(f"Replicate {replicate_idx}: production {args.production_ns} ns, seed={seed}")
    while run_steps < total_steps:
        check_budget(args, start_time, f"replicate {replicate_idx} production")
        step_now = min(chunk_steps, total_steps - run_steps)
        simulation.step(step_now)
        run_steps += step_now
        progress = {
            "replicate": replicate_idx,
            "seed": seed,
            "production_steps_completed": run_steps,
            "production_steps_total": total_steps,
            "production_ns_completed": run_steps / STEPS_PER_NS,
            "projected_cost_usd": projected_cost(start_time, args.hourly_cost_usd),
            "updated_utc": datetime.now(timezone.utc).isoformat(),
        }
        progress_json.write_text(json.dumps(progress, indent=2), encoding="utf-8")
        with checkpoint.open("wb") as handle:
            handle.write(simulation.context.createCheckpoint())

    state = simulation.context.getState(getPositions=True)
    with final_pdb.open("w", encoding="utf-8") as handle:
        deps["PDBFile"].writeFile(simulation.topology, state.getPositions(), handle, keepIds=True)
    complete_marker.write_text(
        json.dumps(
            {
                "replicate": replicate_idx,
                "seed": seed,
                "production_ns": args.production_ns,
                "completed_utc": datetime.now(timezone.utc).isoformat(),
                "projected_cost_usd": projected_cost(start_time, args.hourly_cost_usd),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Replicate {replicate_idx}: complete")


def main() -> None:
    args = parse_args()
    if args.smoke_test:
        args.replicates = 1
        args.production_ns = 0.01
        args.output_root = args.output_root / "smoke_test"

    if len(args.seeds) < args.replicates:
        raise SystemExit("--seeds must provide at least one seed per replicate")

    args.output_root.mkdir(parents=True, exist_ok=True)
    deps = _import_dependencies()
    prepared_pdb = run_prepare(args.output_root, args.ph)
    write_manifest(args, prepared_pdb, deps)
    if args.prepare_only:
        print(f"Prepare-only complete: {args.output_root}")
        return

    start = time.monotonic()
    for rep_idx in range(1, args.replicates + 1):
        run_replicate(args, deps, prepared_pdb, rep_idx, args.seeds[rep_idx - 1], start)

    print(f"Run complete: {args.output_root}")
    print("Run analysis next with scripts/phase5_analyze_1axc_md.py")


if __name__ == "__main__":
    main()
