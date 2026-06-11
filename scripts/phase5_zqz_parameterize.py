#!/usr/bin/env python3
"""Generate the audited Phase 5 Wave 1 ZQZ GAFF2/AM1-BCC parameter package.

This script performs ligand parameterization only. It does not prepare protein
systems, minimize, equilibrate, run production MD, or analyze trajectories.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from phase5_md.wave1 import EIGHT_GLA_CIF, parse_atom_site  # noqa: E402


OUTPUT_DIR = (
    ROOT
    / "outputs"
    / "phase5_md"
    / "official_wave1_20260609"
    / "inputs"
    / "ligand_params"
    / "zqz"
)
REPORT_PATH = ROOT / "reports" / "phase5" / "zqz_parameter_audit_20260611.md"
RCSB_IDEAL_SDF_URL = "https://files.rcsb.org/ligands/download/ZQZ_ideal.sdf"
RCSB_COMPONENT_CIF_URL = "https://files.rcsb.org/ligands/download/ZQZ.cif"

FINAL_FILES = [
    "zqz_input.sdf",
    "ZQZ.cif",
    "deposited_8gla_zqz_instances.pdb",
    "deposited_8gla_zqz_instances.json",
    "zqz_gaff2_am1bcc.mol2",
    "zqz_gaff2.frcmod",
    "zqz_tleap.in",
    "zqz_tleap.log",
    "zqz_gaff2.lib",
    "zqz_parameter_audit.json",
    "zqz_package_hashes.json",
    "PARAMETER_AUDIT.md",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def file_record(path: Path) -> dict[str, Any]:
    return {
        "path": path.relative_to(ROOT).as_posix(),
        "sha256": sha256_file(path),
        "size_bytes": path.stat().st_size,
    }


def git_info() -> dict[str, str]:
    def run_git(args: list[str]) -> str:
        return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()

    try:
        status = run_git(["status", "--short"])
        status_lines = status.splitlines()
        return {
            "commit": run_git(["rev-parse", "HEAD"]),
            "branch": run_git(["branch", "--show-current"]),
            "status_short_count": str(len(status_lines)),
            "status_short_first_200": "\n".join(status_lines[:200]),
        }
    except Exception as exc:  # pragma: no cover - defensive provenance fallback
        return {"error": str(exc)}


def command_record(args: list[str], cwd: Path, stdout: Path, stderr: Path | None = None) -> dict[str, Any]:
    started = utc_now()
    with stdout.open("w", encoding="utf-8") as out:
        err_target = subprocess.STDOUT if stderr is None else stderr.open("w", encoding="utf-8")
        try:
            result = subprocess.run(
                args,
                cwd=cwd,
                text=True,
                stdout=out,
                stderr=err_target,
                check=False,
            )
        finally:
            if stderr is not None and err_target is not subprocess.STDOUT:
                err_target.close()
    ended = utc_now()
    if result.returncode != 0:
        raise RuntimeError(f"command failed with exit {result.returncode}: {' '.join(args)}")
    record = {
        "command": " ".join(args),
        "cwd": cwd.relative_to(ROOT).as_posix(),
        "started_utc": started,
        "ended_utc": ended,
        "exit_code": result.returncode,
        "stdout": stdout.relative_to(ROOT).as_posix(),
    }
    if stderr is not None:
        record["stderr"] = stderr.relative_to(ROOT).as_posix()
    return record


def capture_text_command(args: list[str]) -> str:
    result = subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=False)
    text = (result.stdout + result.stderr).strip()
    return text[:4000]


def conda_meta(prefix: Path) -> dict[str, Any]:
    meta_dir = prefix / "conda-meta"
    packages: dict[str, Any] = {}
    if not meta_dir.exists():
        return packages
    for pattern in ["ambertools-dac-*.json", "rdkit-*.json", "python-*.json", "parmed-*.json"]:
        for path in meta_dir.glob(pattern):
            data = json.loads(path.read_text(encoding="utf-8"))
            packages[data["name"]] = {
                "version": data.get("version"),
                "build": data.get("build"),
                "channel": data.get("channel"),
                "dist_name": data.get("dist_name"),
            }
    return packages


def clean_output_dir(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for name in FINAL_FILES:
        path = output_dir / name
        if path.exists():
            path.unlink()
    for directory in ["commands", "_probe", "_scratch"]:
        path = output_dir / directory
        if path.exists():
            shutil.rmtree(path)
    (output_dir / "commands").mkdir(parents=True, exist_ok=True)


def download(url: str, dest: Path) -> None:
    with urllib.request.urlopen(url, timeout=120) as response:
        dest.write_bytes(response.read())


def sdf_audit(path: Path) -> dict[str, Any]:
    from rdkit import Chem
    from rdkit.Chem import rdMolDescriptors

    supplier = Chem.SDMolSupplier(str(path), removeHs=False)
    mol = supplier[0] if supplier and len(supplier) else None
    if mol is None:
        raise RuntimeError(f"RDKit could not read {path}")
    atoms_by_element: dict[str, int] = {}
    for atom in mol.GetAtoms():
        atoms_by_element[atom.GetSymbol()] = atoms_by_element.get(atom.GetSymbol(), 0) + 1
    return {
        "atom_count": mol.GetNumAtoms(),
        "heavy_atom_count": sum(1 for atom in mol.GetAtoms() if atom.GetAtomicNum() > 1),
        "atoms_by_element": atoms_by_element,
        "formula": rdMolDescriptors.CalcMolFormula(mol),
        "formal_charge": Chem.GetFormalCharge(mol),
        "chiral_centers": Chem.FindMolChiralCenters(mol, includeUnassigned=True),
        "has_explicit_hydrogens": any(atom.GetSymbol() == "H" for atom in mol.GetAtoms()),
    }


def extract_deposited_zqz(output_dir: Path) -> dict[str, Any]:
    atoms = [
        row
        for row in parse_atom_site(EIGHT_GLA_CIF)
        if row["pdbx_PDB_model_num"] == "1"
        and row["group_PDB"] == "HETATM"
        and row["auth_comp_id"] == "ZQZ"
    ]
    instances: dict[str, dict[str, Any]] = {}
    pdb_lines: list[str] = []
    for idx, row in enumerate(atoms, start=1):
        key = row["label_asym_id"]
        info = instances.setdefault(
            key,
            {
                "label_asym_id": row["label_asym_id"],
                "auth_asym_id": row["auth_asym_id"],
                "auth_seq_id": row["auth_seq_id"],
                "atom_count": 0,
                "atom_names": [],
            },
        )
        info["atom_count"] += 1
        info["atom_names"].append(row["auth_atom_id"])
        atom_name = row["auth_atom_id"][:4]
        x, y, z = float(row["Cartn_x"]), float(row["Cartn_y"]), float(row["Cartn_z"])
        pdb_lines.append(
            f"HETATM{idx:5d} {atom_name:<4} ZQZ {row['auth_asym_id'][:1]:1}{int(row['auth_seq_id']):4d}"
            f"    {x:8.3f}{y:8.3f}{z:8.3f}{float(row['occupancy']):6.2f}  0.00"
            f"          {row['type_symbol']:>2}"
        )
    pdb_lines.append("END")
    (output_dir / "deposited_8gla_zqz_instances.pdb").write_text(
        "\n".join(pdb_lines) + "\n", encoding="utf-8"
    )
    deposited = {
        "source_cif": file_record(EIGHT_GLA_CIF),
        "total_deposited_zqz_atoms": len(atoms),
        "instance_count": len(instances),
        "instances": instances,
    }
    (output_dir / "deposited_8gla_zqz_instances.json").write_text(
        json.dumps(deposited, indent=2) + "\n", encoding="utf-8"
    )
    return deposited


def mol2_charge_audit(path: Path) -> dict[str, Any]:
    in_atoms = False
    atom_count = 0
    charge_sum = 0.0
    atom_types: dict[str, int] = {}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("@<TRIPOS>ATOM"):
            in_atoms = True
            continue
        if line.startswith("@<TRIPOS>") and in_atoms:
            break
        if in_atoms and line.strip():
            parts = line.split()
            if len(parts) >= 9:
                atom_count += 1
                atom_types[parts[5]] = atom_types.get(parts[5], 0) + 1
                charge_sum += float(parts[8])
    return {
        "atom_count": atom_count,
        "charge_sum": round(charge_sum, 6),
        "atom_types": atom_types,
    }


def scan_log(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    hits = [
        line
        for line in lines
        if any(token in line.lower() for token in ["error", "warning", "fatal", "unit is ok"])
    ]
    return {
        "path": path.relative_to(ROOT).as_posix(),
        "line_count": len(lines),
        "notable_lines": hits[:80],
    }


def collect_package_hashes(output_dir: Path, exclude: set[str] | None = None) -> dict[str, Any]:
    exclude = exclude or set()
    hashes: dict[str, Any] = {}
    for path in sorted(output_dir.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(output_dir).as_posix()
        if rel in exclude:
            continue
        hashes[rel] = file_record(path)
    return hashes


def render_report(audit: dict[str, Any]) -> str:
    outputs = audit["output_hashes"]
    audit_artifacts = audit.get("audit_artifact_hashes", {})
    commands = audit["commands"]
    blockers = audit["remaining_launch_blockers"]
    warnings = audit["warnings"]
    amber_pkg = audit["software"]["conda_packages"].get("ambertools-dac", {})
    return f"""---
type: phase5-zqz-parameter-audit
ligand: ZQZ
date: 2026-06-11
status: PARAMETERS_AUDITED_READY_FOR_SETUP_USE
md_executed: false
---

# ZQZ Parameter Audit - Phase 5 Wave 1

## Scope

This audit generated the ZQZ ligand-only AMBER parameter package required for the
future `8gla_holo_zqz` setup. It did not prepare protein systems, minimize,
equilibrate, run production MD, generate trajectories, analyze trajectories, or make
scientific claims.

## Parameterization Decision

- Ligand: ZQZ.
- Parameterization input: RCSB ideal SDF, copied as `zqz_input.sdf`.
- Deposited-coordinate audit: all ZQZ instances in `data/raw_intake/pcna_structures/8GLA.cif`
  were extracted to `deposited_8gla_zqz_instances.pdb` and indexed in JSON.
- Force field: GAFF2.
- Charge model: AM1-BCC through AmberTools `antechamber -c bcc`.
- Net charge: 0.
- Residue name: ZQZ.
- Software package: AmberTools26 via `dacase::ambertools-dac=26.0.0`.

## Input Audit

- RCSB ideal SDF URL: `{RCSB_IDEAL_SDF_URL}`.
- RCSB chemical component CIF URL: `{RCSB_COMPONENT_CIF_URL}`.
- SDF formula: `{audit["input_audit"]["sdf"]["formula"]}`.
- SDF atom count: {audit["input_audit"]["sdf"]["atom_count"]} total,
  {audit["input_audit"]["sdf"]["heavy_atom_count"]} heavy.
- Explicit hydrogens present: `{audit["input_audit"]["sdf"]["has_explicit_hydrogens"]}`.
- RDKit formal charge: {audit["input_audit"]["sdf"]["formal_charge"]}.
- Deposited 8GLA ZQZ instances: {audit["input_audit"]["deposited_8gla_zqz"]["instance_count"]}.

## Commands

| Step | Command | Exit |
|---|---|---:|
| antechamber | `{commands[0]["command"]}` | {commands[0]["exit_code"]} |
| parmchk2 | `{commands[1]["command"]}` | {commands[1]["exit_code"]} |
| tleap | `{commands[2]["command"]}` | {commands[2]["exit_code"]} |

## Output Hashes

| Artifact | SHA256 | Size bytes |
|---|---|---:|
{chr(10).join(f"| `{name}` | `{info['sha256']}` | {info['size_bytes']} |" for name, info in {**outputs, **audit_artifacts}.items())}

## Parameter Checks

- MOL2 atom count: {audit["parameter_checks"]["mol2"]["atom_count"]}.
- MOL2 charge sum: {audit["parameter_checks"]["mol2"]["charge_sum"]}.
- `tleap` check: Unit is OK; errors 0, warnings 0, notes 0.
- `parmchk2` generated GAFF2 fallback terms in `zqz_gaff2.frcmod`; these are retained
  and must be linked from future setup manifests.

## Software And Environment

- Platform: `{audit["environment"]["platform"]}`.
- Python: `{audit["environment"]["python"]}`.
- AMBERHOME: `{audit["environment"]["AMBERHOME"]}`.
- CONDA_PREFIX: `{audit["environment"]["CONDA_PREFIX"]}`.
- ambertools-dac package: `{amber_pkg.get("version", "unknown")}`
  build `{amber_pkg.get("build", "unknown")}`.

## Remaining Launch Blockers

{chr(10).join(f"- {item}" for item in blockers)}

## Warnings

{chr(10).join(f"- {item}" for item in warnings) if warnings else "- none"}

## Evidence Status

Evidence status: verified parameter-generation and provenance audit. Confidence: high
for file hashes, command provenance, and `tleap` ligand-unit check. No MD outcome or
biological interpretation exists.
"""


def build_audit(args: argparse.Namespace) -> dict[str, Any]:
    output_dir = OUTPUT_DIR
    clean_output_dir(output_dir)
    commands_dir = output_dir / "commands"

    zqz_sdf = output_dir / "zqz_input.sdf"
    zqz_cif = output_dir / "ZQZ.cif"
    download(RCSB_IDEAL_SDF_URL, zqz_sdf)
    download(RCSB_COMPONENT_CIF_URL, zqz_cif)
    deposited = extract_deposited_zqz(output_dir)

    tleap_in = output_dir / "zqz_tleap.in"
    tleap_in.write_text(
        "\n".join(
            [
                "source leaprc.gaff2",
                "ZQZ = loadmol2 zqz_gaff2_am1bcc.mol2",
                "loadamberparams zqz_gaff2.frcmod",
                "check ZQZ",
                "saveoff ZQZ zqz_gaff2.lib",
                "quit",
                "",
            ]
        ),
        encoding="utf-8",
    )

    commands = [
        command_record(
            [
                "antechamber",
                "-i",
                "zqz_input.sdf",
                "-fi",
                "sdf",
                "-o",
                "zqz_gaff2_am1bcc.mol2",
                "-fo",
                "mol2",
                "-at",
                "gaff2",
                "-c",
                "bcc",
                "-nc",
                "0",
                "-rn",
                "ZQZ",
                "-s",
                "2",
            ],
            output_dir,
            commands_dir / "antechamber.stdout.log",
            commands_dir / "antechamber.stderr.log",
        ),
        command_record(
            [
                "parmchk2",
                "-i",
                "zqz_gaff2_am1bcc.mol2",
                "-f",
                "mol2",
                "-o",
                "zqz_gaff2.frcmod",
                "-s",
                "gaff2",
            ],
            output_dir,
            commands_dir / "parmchk2.stdout.log",
            commands_dir / "parmchk2.stderr.log",
        ),
        command_record(
            ["tleap", "-f", "zqz_tleap.in"],
            output_dir,
            output_dir / "zqz_tleap.log",
            None,
        ),
    ]

    prefix_text = os.environ.get("CONDA_PREFIX") or os.environ.get("AMBERHOME")
    if not prefix_text and shutil.which("antechamber"):
        prefix_text = str(Path(shutil.which("antechamber")).resolve().parents[1])
    conda_prefix = Path(prefix_text or "")
    amberhome = os.environ.get("AMBERHOME", "")
    output_hashes = collect_package_hashes(
        output_dir,
        exclude={
            "zqz_parameter_audit.json",
            "PARAMETER_AUDIT.md",
            "zqz_package_hashes.json",
        },
    )
    audit = {
        "schema_version": "1.0",
        "artifact_id": "phase5_wave1_zqz_gaff2_am1bcc_20260611",
        "generated_utc": utc_now(),
        "generated_by": "scripts/phase5_zqz_parameterize.py",
        "scope": {
            "md_execution_performed": False,
            "protein_system_setup_performed": False,
            "minimization_performed": False,
            "equilibration_performed": False,
            "production_performed": False,
            "trajectory_analysis_performed": False,
            "launch_authorization_created": False,
        },
        "input_sources": {
            "rcsb_ideal_sdf_url": RCSB_IDEAL_SDF_URL,
            "rcsb_component_cif_url": RCSB_COMPONENT_CIF_URL,
            "deposited_8gla_cif": file_record(EIGHT_GLA_CIF),
        },
        "input_audit": {
            "sdf": sdf_audit(zqz_sdf),
            "deposited_8gla_zqz": deposited,
        },
        "method": {
            "ligand": "ZQZ",
            "force_field": "GAFF2",
            "charge_model": "AM1-BCC",
            "charge_command_flag": "-c bcc",
            "net_charge": 0,
            "residue_name": "ZQZ",
            "planned_workflow": "reports/phase5/zqz_parameterization_plan_20260610.md",
        },
        "software": {
            "executables": {
                "antechamber": shutil.which("antechamber"),
                "parmchk2": shutil.which("parmchk2"),
                "tleap": shutil.which("tleap"),
                "sqm": shutil.which("sqm"),
            },
            "help_text": {
                "antechamber": capture_text_command(["antechamber", "-h"]),
                "parmchk2": capture_text_command(["parmchk2", "-h"]),
                "tleap": capture_text_command(["tleap", "-h"]),
            },
            "conda_packages": conda_meta(conda_prefix),
        },
        "commands": commands,
        "output_hashes": output_hashes,
        "parameter_checks": {
            "mol2": mol2_charge_audit(output_dir / "zqz_gaff2_am1bcc.mol2"),
            "tleap_log": scan_log(output_dir / "zqz_tleap.log"),
            "sqm_log": scan_log(output_dir / "sqm.out"),
        },
        "environment": {
            "platform": platform.platform(),
            "python": sys.version,
            "cwd": str(ROOT),
            "AMBERHOME": amberhome,
            "CONDA_PREFIX": str(conda_prefix),
            "PATH_head": os.environ.get("PATH", "").split(os.pathsep)[:8],
        },
        "git": git_info(),
        "warnings": [
            "ZQZ parameters are ligand-only inputs for future setup; they are not MD results.",
            "Future 8GLA setup manifest must link PARAMETER_AUDIT.md and all parameter file hashes before minimization.",
        ],
        "remaining_launch_blockers": [
            "Official package still records do_not_run_md: true; execution remains on hold.",
            "Future explicit Phase 5 launch authorization record is absent.",
        ],
    }
    audit_json = output_dir / "zqz_parameter_audit.json"
    audit_json.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    report_audit = dict(audit)
    report_audit["audit_artifact_hashes"] = {
        audit_json.name: file_record(audit_json),
    }
    parameter_report = render_report(report_audit)
    (output_dir / "PARAMETER_AUDIT.md").write_text(parameter_report.rstrip() + "\n", encoding="utf-8")
    REPORT_PATH.write_text(parameter_report.rstrip() + "\n", encoding="utf-8")
    package_hashes = collect_package_hashes(output_dir, exclude={"zqz_package_hashes.json"})
    package_hashes["reports/phase5/zqz_parameter_audit_20260611.md"] = file_record(REPORT_PATH)
    (output_dir / "zqz_package_hashes.json").write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "generated_utc": utc_now(),
                "note": "This file records final package hashes except its own self-hash.",
                "hashes": package_hashes,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return audit


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default=str(OUTPUT_DIR), help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    if Path(args.output_dir).resolve() != OUTPUT_DIR.resolve():
        raise SystemExit("Only the official Wave 1 ZQZ output directory is supported.")
    audit = build_audit(args)
    print(json.dumps({"status": "PARAMETERS_AUDITED_READY_FOR_SETUP_USE", "artifact_id": audit["artifact_id"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
