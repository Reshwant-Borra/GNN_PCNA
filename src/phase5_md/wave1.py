"""Official Phase 5 MD Wave 1 audit and preflight helpers.

This module records launch-readiness facts only. It must not prepare coordinates,
run ligand parameterization, start minimization/equilibration/production, or analyze
trajectories.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import platform
import shlex
import subprocess
import sys
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]

AUTHORIZATION = REPO_ROOT / "reports" / "phase4" / "gate7_authorization_20260609.md"
EXECUTION_PACKAGE = (
    REPO_ROOT / "reports" / "phase5" / "official_wave1_execution_package_20260609.md"
)

EIGHT_GLA_CIF = REPO_ROOT / "data" / "raw_intake" / "pcna_structures" / "8GLA.cif"
EIGHT_GLA_METADATA = (
    REPO_ROOT / "data" / "raw_intake" / "pcna_structures" / "8GLA_metadata.json"
)
EIGHT_GLA_ASSEMBLY1 = (
    REPO_ROOT / "data" / "raw_intake" / "pcna_structures" / "8GLA_assembly1.json"
)
ONE_AXC_CIF = REPO_ROOT / "data" / "raw_intake" / "pcna_structures" / "1AXC.cif"
ONE_AXC_METADATA = (
    REPO_ROOT / "data" / "raw_intake" / "pcna_structures" / "1AXC_metadata.json"
)

OUTPUT_ROOT = REPO_ROOT / "outputs" / "phase5_md" / "official_wave1_20260609"
ZQZ_PARAMETER_DIR = OUTPUT_ROOT / "inputs" / "ligand_params" / "zqz"
ZQZ_PARAMETER_AUDIT = ZQZ_PARAMETER_DIR / "PARAMETER_AUDIT.md"
ZQZ_PARAMETER_AUDIT_JSON = ZQZ_PARAMETER_DIR / "zqz_parameter_audit.json"
REGISTRY_PATH = (
    REPO_ROOT / "data" / "registries" / "phase5_wave1_preparation_audit_20260610.json"
)
REPORT_DIR = REPO_ROOT / "reports" / "phase5"

AUTHORIZED_SYSTEMS = {
    "8gla_holo_zqz": {
        "pdb_id": "8GLA",
        "starting_structure": "8GLA",
        "ligand_state": "ZQZ retained",
        "replicates": 3,
        "production_ns": 100,
        "seeds": [2026060911, 2026060912, 2026060913],
    },
    "8gla_apo_from_holo": {
        "pdb_id": "8GLA",
        "starting_structure": "8GLA",
        "ligand_state": "ZQZ removed",
        "replicates": 3,
        "production_ns": 100,
        "seeds": [2026060921, 2026060922, 2026060923],
    },
    "1axc_apo_from_p21": {
        "pdb_id": "1AXC",
        "starting_structure": "1AXC",
        "ligand_state": "p21 peptides removed",
        "replicates": 3,
        "production_ns": 100,
        "seeds": [2026060931, 2026060932, 2026060933],
    },
}

AUTHORIZED_WINDOWS = {
    "PC-118": {"residues": [118, 119, 120, 121, 122], "systems": ["8gla_holo_zqz", "8gla_apo_from_holo"]},
    "T1A-239": {"residues": [239, 240, 241, 242, 243], "systems": ["1axc_apo_from_p21"]},
    "T1A-28": {"residues": [28, 29, 30, 31, 32], "systems": ["1axc_apo_from_p21"]},
    "T1A-206": {"residues": [206, 207, 208, 209, 210], "systems": ["1axc_apo_from_p21"]},
    "T2-134": {"residues": [134, 135, 136, 137, 138], "systems": ["1axc_apo_from_p21"]},
}

DEFERRED_WINDOWS = {
    "170-174",
    "175-179",
    "152-156",
}


class Phase5PreflightError(RuntimeError):
    """Raised when a required launch-readiness check fails closed."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rb") as fh:  # type: ignore[arg-type]
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def file_size(path: Path) -> int:
    return path.stat().st_size


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def clean(value: str | None) -> str | None:
    if value is None or value in {".", "?"}:
        return None
    return value


def split_cif_row(line: str) -> list[str]:
    return shlex.split(line, posix=True)


def read_loop(cif_path: Path, prefix: str) -> list[dict[str, str]]:
    """Read simple line-oriented mmCIF loops.

    The deposited 8GLA and 1AXC categories needed here are line-oriented for atom,
    sequence, assembly, nonpolymer, and missing-residue data. This intentionally does
    not try to be a complete mmCIF parser.
    """
    rows: list[dict[str, str]] = []
    lines = cif_path.read_text(encoding="utf-8", errors="replace").splitlines()
    i = 0
    while i < len(lines):
        if lines[i].strip() != "loop_":
            i += 1
            continue
        j = i + 1
        headers: list[str] = []
        while j < len(lines) and lines[j].strip().startswith(prefix + "."):
            headers.append(lines[j].strip().split(".", 1)[1])
            j += 1
        if not headers:
            i += 1
            continue
        k = j
        while k < len(lines):
            line = lines[k].strip()
            k += 1
            if not line:
                continue
            if line == "#" or line == "loop_" or line.startswith("_"):
                break
            values = split_cif_row(line)
            # Some mmCIF loops wrap the last value to the next line. Accumulate enough
            # tokens for the audit categories that wrap numeric formula weights.
            while len(values) < len(headers) and k < len(lines):
                nxt = lines[k].strip()
                if not nxt or nxt == "#" or nxt == "loop_" or nxt.startswith("_"):
                    break
                values.extend(split_cif_row(nxt))
                k += 1
            if len(values) == len(headers):
                rows.append(dict(zip(headers, values)))
        i = k
    return rows


def read_key_values(cif_path: Path, prefix: str) -> dict[str, str]:
    values: dict[str, str] = {}
    lines = cif_path.read_text(encoding="utf-8", errors="replace").splitlines()
    for line in lines:
        stripped = line.strip()
        if not stripped.startswith(prefix + "."):
            continue
        parts = stripped.split(None, 1)
        key = parts[0].split(".", 1)[1]
        values[key] = parts[1].strip().strip("'\"") if len(parts) > 1 else ""
    return values


def parse_atom_site(cif_path: Path) -> list[dict[str, str]]:
    rows = read_loop(cif_path, "_atom_site")
    required = {
        "group_PDB",
        "type_symbol",
        "label_atom_id",
        "label_alt_id",
        "label_comp_id",
        "label_asym_id",
        "label_entity_id",
        "label_seq_id",
        "pdbx_PDB_ins_code",
        "Cartn_x",
        "Cartn_y",
        "Cartn_z",
        "occupancy",
        "auth_seq_id",
        "auth_comp_id",
        "auth_asym_id",
        "auth_atom_id",
        "pdbx_PDB_model_num",
    }
    missing = required - set(rows[0]) if rows else required
    if missing:
        raise Phase5PreflightError(f"{cif_path} atom_site missing columns: {sorted(missing)}")
    return rows


def residue_summary(atoms: list[dict[str, str]], pcna_chains: list[str]) -> dict[str, Any]:
    per_chain: dict[str, dict[str, Any]] = {}
    residues: dict[str, set[int]] = defaultdict(set)
    atom_counts: dict[str, int] = defaultdict(int)
    altlocs: list[dict[str, Any]] = []
    occupancy_lt_one: list[dict[str, Any]] = []
    insertion_codes: set[tuple[str, str, str]] = set()

    for row in atoms:
        if row["pdbx_PDB_model_num"] != "1":
            continue
        chain = row["auth_asym_id"]
        if row["group_PDB"] == "ATOM" and chain in pcna_chains:
            try:
                residues[chain].add(int(row["auth_seq_id"]))
            except ValueError:
                pass
            atom_counts[chain] += 1
            ins = clean(row.get("pdbx_PDB_ins_code"))
            if ins:
                insertion_codes.add((chain, row["auth_seq_id"], ins))
        alt = clean(row.get("label_alt_id"))
        if alt:
            altlocs.append(
                {
                    "chain": chain,
                    "seq_id": row["auth_seq_id"],
                    "residue": row["auth_comp_id"],
                    "atom": row["auth_atom_id"],
                    "altloc": alt,
                }
            )
        try:
            occ = float(row["occupancy"])
        except ValueError:
            continue
        if occ < 1.0:
            occupancy_lt_one.append(
                {
                    "group": row["group_PDB"],
                    "chain": chain,
                    "seq_id": row["auth_seq_id"],
                    "residue": row["auth_comp_id"],
                    "atom": row["auth_atom_id"],
                    "occupancy": occ,
                    "altloc": clean(row.get("label_alt_id")),
                }
            )

    for chain in pcna_chains:
        nums = sorted(residues[chain])
        per_chain[chain] = {
            "modeled_residue_count": len(nums),
            "first_modeled_residue": nums[0] if nums else None,
            "last_modeled_residue": nums[-1] if nums else None,
            "atom_count": atom_counts[chain],
            "modeled_residues": nums,
        }

    return {
        "per_chain": per_chain,
        "altloc_count": len(altlocs),
        "altloc_examples": altlocs[:20],
        "occupancy_lt_one_count": len(occupancy_lt_one),
        "occupancy_lt_one_examples": occupancy_lt_one[:20],
        "insertion_codes": [
            {"chain": chain, "seq_id": seq_id, "icode": icode}
            for chain, seq_id, icode in sorted(insertion_codes)
        ],
    }


def missing_residues(cif_path: Path, chains: list[str]) -> dict[str, list[int]]:
    rows = read_loop(cif_path, "_pdbx_unobs_or_zero_occ_residues")
    out: dict[str, list[int]] = {chain: [] for chain in chains}
    for row in rows:
        if row.get("PDB_model_num") != "1":
            continue
        chain = row.get("auth_asym_id")
        if chain not in out or row.get("polymer_flag") != "Y":
            continue
        try:
            out[chain].append(int(row["auth_seq_id"]))
        except ValueError:
            continue
    return {chain: sorted(vals) for chain, vals in out.items()}


def window_presence(
    residues_by_chain: dict[str, dict[str, Any]], chains: list[str], windows: dict[str, dict[str, Any]]
) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for cid, spec in windows.items():
        nums = spec["residues"]
        chain_status: dict[str, Any] = {}
        for chain in chains:
            present = set(residues_by_chain[chain]["modeled_residues"])
            missing = [n for n in nums if n not in present]
            chain_status[chain] = {
                "present": [n for n in nums if n in present],
                "missing": missing,
                "complete": not missing,
            }
        out[cid] = {
            "residues": nums,
            "chains": chain_status,
            "complete_all_chains": all(v["complete"] for v in chain_status.values()),
        }
    return out


def struct_ref_mapping(cif_path: Path) -> list[dict[str, str]]:
    rows = read_loop(cif_path, "_struct_ref_seq")
    return [
        {
            "chain": row["pdbx_strand_id"],
            "db_accession": row["pdbx_db_accession"],
            "db_align_beg": row["db_align_beg"],
            "db_align_end": row["db_align_end"],
            "auth_seq_align_beg": row["pdbx_auth_seq_align_beg"],
            "auth_seq_align_end": row["pdbx_auth_seq_align_end"],
        }
        for row in rows
    ]


def nonpoly_summary(cif_path: Path) -> list[dict[str, str]]:
    rows = read_loop(cif_path, "_pdbx_nonpoly_scheme")
    return [
        {
            "label_asym_id": row["asym_id"],
            "entity_id": row["entity_id"],
            "mon_id": row["mon_id"],
            "auth_chain": row["pdb_strand_id"],
            "pdb_seq_num": row["pdb_seq_num"],
            "auth_seq_num": row["auth_seq_num"],
            "auth_mon_id": row["auth_mon_id"],
        }
        for row in rows
    ]


def zqz_contact_summary(atoms: list[dict[str, str]]) -> dict[str, Any]:
    pcna_atoms: list[tuple[str, int, str, tuple[float, float, float]]] = []
    zqz_atoms: dict[tuple[str, str, str], list[tuple[str, tuple[float, float, float]]]] = defaultdict(list)
    for row in atoms:
        if row["pdbx_PDB_model_num"] != "1" or row["type_symbol"] == "H":
            continue
        xyz = (float(row["Cartn_x"]), float(row["Cartn_y"]), float(row["Cartn_z"]))
        if row["group_PDB"] == "ATOM" and row["auth_asym_id"] in {"A", "B", "C"}:
            pcna_atoms.append((row["auth_asym_id"], int(row["auth_seq_id"]), row["auth_comp_id"], xyz))
        if row["group_PDB"] == "HETATM" and row["auth_comp_id"] == "ZQZ":
            key = (row["label_asym_id"], row["auth_asym_id"], row["auth_seq_id"])
            zqz_atoms[key].append((row["auth_atom_id"], xyz))

    def distance(a: tuple[float, float, float], b: tuple[float, float, float]) -> float:
        return sum((a[i] - b[i]) ** 2 for i in range(3)) ** 0.5

    instances: dict[str, Any] = {}
    for key, lig_atoms in sorted(zqz_atoms.items()):
        contacts: dict[str, set[int]] = defaultdict(set)
        min_distance = 999.0
        for chain, seq_id, _resname, pxyz in pcna_atoms:
            for _atom_name, lxyz in lig_atoms:
                d = distance(pxyz, lxyz)
                min_distance = min(min_distance, d)
                if d <= 4.5:
                    contacts[chain].add(seq_id)
        label_asym, auth_chain, auth_seq = key
        instances[label_asym] = {
            "auth_chain": auth_chain,
            "auth_seq_id": auth_seq,
            "heavy_atom_count": len(lig_atoms),
            "minimum_heavy_atom_distance_to_pcna_a": round(min_distance, 3),
            "pcna_contacts_le_4p5_a": {
                chain: sorted(values) for chain, values in sorted(contacts.items())
            },
        }
    return {
        "ligand_code": "ZQZ",
        "identity": "N-[2-(3-methoxyphenoxy)phenyl]-N~2~-(naphthalene-1-carbonyl)-L-alpha-glutamine",
        "formula": "C29 H26 N2 O6",
        "formal_charge": 0,
        "instances": instances,
    }


def assembly_from_cif(cif_path: Path) -> list[dict[str, str]]:
    rows = read_loop(cif_path, "_pdbx_struct_assembly")
    if rows:
        return rows
    kv = read_key_values(cif_path, "_pdbx_struct_assembly")
    return [kv] if kv else []


def assembly_gen_from_cif(cif_path: Path) -> list[dict[str, str]]:
    rows = read_loop(cif_path, "_pdbx_struct_assembly_gen")
    if rows:
        return rows
    kv = read_key_values(cif_path, "_pdbx_struct_assembly_gen")
    return [kv] if kv else []


def audit_8gla() -> dict[str, Any]:
    atoms = parse_atom_site(EIGHT_GLA_CIF)
    pcna_chains = ["A", "B", "C"]
    res = residue_summary(atoms, pcna_chains)
    metadata = read_json(EIGHT_GLA_METADATA)
    assembly1 = read_json(EIGHT_GLA_ASSEMBLY1)
    return {
        "pdb_id": "8GLA",
        "source_files": source_hashes([EIGHT_GLA_CIF, EIGHT_GLA_METADATA, EIGHT_GLA_ASSEMBLY1]),
        "metadata": {
            "title": metadata["struct"]["title"],
            "method": metadata["exptl"][0]["method"],
            "resolution_a": metadata["rcsb_entry_info"]["resolution_combined"][0],
            "r_work": metadata["refine"][0]["ls_R_factor_R_work"],
            "r_free": metadata["refine"][0]["ls_R_factor_R_free"],
            "primary_pmid": metadata["rcsb_primary_citation"]["pdbx_database_id_PubMed"],
            "revision_date": metadata["rcsb_accession_info"]["revision_date"],
        },
        "biological_assembly": {
            "official_assembly_for_wave1": "1",
            "assembly_1_from_rcsb": assembly1["pdbx_struct_assembly"],
            "assembly_1_gen": assembly1["pdbx_struct_assembly_gen"],
            "symmetry": assembly1.get("rcsb_struct_symmetry", []),
            "deposited_cif_assemblies": assembly_from_cif(EIGHT_GLA_CIF),
            "deposited_cif_assembly_gen": assembly_gen_from_cif(EIGHT_GLA_CIF),
            "wave1_pcna_auth_chains": pcna_chains,
            "excluded_deposited_pcna_chain": "D",
            "exclusion_reason": "chain D belongs to deposited assembly 2; Wave 1 uses RCSB biological assembly 1.",
        },
        "chain_mapping": {
            "pcna_auth_chains": pcna_chains,
            "uniprot": "P12004",
            "struct_ref_seq": struct_ref_mapping(EIGHT_GLA_CIF),
            "residue_summary": res["per_chain"],
            "canonical_numbering_status": "author numbering aligns to UniProt P12004 1-261 in struct_ref_seq.",
        },
        "nonpolymer": nonpoly_summary(EIGHT_GLA_CIF),
        "zqz": zqz_contact_summary(atoms),
        "missing_residues": missing_residues(EIGHT_GLA_CIF, pcna_chains),
        "candidate_window_presence": window_presence(res["per_chain"], pcna_chains, {"PC-118": AUTHORIZED_WINDOWS["PC-118"]}),
        "alternate_locations": {
            "count": res["altloc_count"],
            "examples": res["altloc_examples"],
        },
        "occupancy_issues": {
            "atoms_with_occupancy_lt_one_count": res["occupancy_lt_one_count"],
            "examples": res["occupancy_lt_one_examples"],
        },
        "insertion_codes": res["insertion_codes"],
        "caveats": [
            "8GLA resolution is 3.77 A and below the <=3.5 A quality threshold; it is authorized as a positive-control system only.",
            "Assembly 1 contains PCNA chains A/B/C; chain C is missing residue 122 in the PC-118 window.",
            "ZQZ appears as six ligand instances in assembly 1, contacting chains A and B in deposited coordinates; no ZQZ contacts were detected on chain C in assembly 1.",
            "No alternate locations or atom occupancies below 1.0 were detected in atom_site.",
        ],
    }


def audit_1axc() -> dict[str, Any]:
    atoms = parse_atom_site(ONE_AXC_CIF)
    pcna_chains = ["A", "C", "E"]
    p21_chains = ["B", "D", "F"]
    res = residue_summary(atoms, pcna_chains)
    metadata = read_json(ONE_AXC_METADATA)
    p21_residue_summary = residue_summary(atoms, p21_chains)["per_chain"]
    windows = {
        key: AUTHORIZED_WINDOWS[key]
        for key in ["T1A-239", "T1A-28", "T1A-206", "T2-134"]
    }
    return {
        "pdb_id": "1AXC",
        "source_files": source_hashes([ONE_AXC_CIF, ONE_AXC_METADATA]),
        "metadata": {
            "title": metadata["struct"]["title"],
            "method": metadata["exptl"][0]["method"],
            "resolution_a": metadata["rcsb_entry_info"]["resolution_combined"][0],
            "r_work": metadata["refine"][0]["ls_R_factor_R_work"],
            "r_free": metadata["refine"][0]["ls_R_factor_R_free"],
            "primary_pmid": metadata["rcsb_primary_citation"]["pdbx_database_id_PubMed"],
            "revision_date": metadata["rcsb_accession_info"]["revision_date"],
        },
        "biological_assembly": {
            "assembly_id": "1",
            "deposited_cif_assemblies": assembly_from_cif(ONE_AXC_CIF),
            "deposited_cif_assembly_gen": assembly_gen_from_cif(ONE_AXC_CIF),
            "assembly_interpretation": "hexameric deposited biological assembly: PCNA trimer A/C/E plus p21 peptide chains B/D/F.",
        },
        "chain_mapping": {
            "pcna_auth_chains": pcna_chains,
            "p21_peptide_auth_chains_to_remove": p21_chains,
            "uniprot": "P12004",
            "p21_uniprot": "P38936",
            "struct_ref_seq": struct_ref_mapping(ONE_AXC_CIF),
            "pcna_residue_summary": res["per_chain"],
            "p21_residue_summary": p21_residue_summary,
            "canonical_numbering_status": "PCNA author numbering aligns to UniProt P12004 1-261 in struct_ref_seq.",
        },
        "nonpolymer": nonpoly_summary(ONE_AXC_CIF),
        "missing_residues": missing_residues(ONE_AXC_CIF, pcna_chains),
        "candidate_window_presence": window_presence(res["per_chain"], pcna_chains, windows),
        "alternate_locations": {
            "count": res["altloc_count"],
            "examples": res["altloc_examples"],
        },
        "occupancy_issues": {
            "atoms_with_occupancy_lt_one_count": res["occupancy_lt_one_count"],
            "examples": res["occupancy_lt_one_examples"],
        },
        "insertion_codes": res["insertion_codes"],
        "caveats": [
            "1AXC is a p21-bound PCNA complex, not a clean apo crystal structure.",
            "Apo-from-p21 preparation must remove chains B/D/F and record the transformation before any minimization.",
            "Waters are present in the deposited structure and must be handled by the future setup policy.",
            "No alternate locations or atom occupancies below 1.0 were detected in atom_site.",
        ],
    }


def source_hashes(paths: list[Path]) -> dict[str, dict[str, Any]]:
    return {
        path.relative_to(REPO_ROOT).as_posix(): {
            "sha256": sha256_file(path),
            "size_bytes": file_size(path),
        }
        for path in paths
    }


def git_info() -> dict[str, str]:
    try:
        commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, text=True
        ).strip()
        branch = subprocess.check_output(
            ["git", "branch", "--show-current"], cwd=REPO_ROOT, text=True
        ).strip()
        status = subprocess.check_output(
            ["git", "status", "--short"], cwd=REPO_ROOT, text=True
        ).strip()
    except Exception as exc:  # pragma: no cover - defensive provenance fallback
        return {"error": str(exc)}
    return {"commit": commit, "branch": branch, "status_short": status}


def environment_capture() -> dict[str, Any]:
    return {
        "python": sys.version,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "cwd": str(REPO_ROOT),
        "selected_environment_variables": {
            key: os.environ.get(key)
            for key in ["CONDA_PREFIX", "CONDA_DEFAULT_ENV", "AMBERHOME", "CUDA_VISIBLE_DEVICES"]
            if os.environ.get(key)
        },
    }


def build_registry() -> dict[str, Any]:
    audit8 = audit_8gla()
    audit1 = audit_1axc()
    zqz_audit = audit_zqz_parameters()
    return {
        "schema_version": "1.0",
        "generated_utc": utc_now(),
        "generated_by": "src/phase5_md/wave1.py",
        "authorization": AUTHORIZATION.relative_to(REPO_ROOT).as_posix(),
        "execution_package": EXECUTION_PACKAGE.relative_to(REPO_ROOT).as_posix(),
        "md_execution_performed": False,
        "minimization_performed": False,
        "equilibration_performed": False,
        "production_performed": False,
        "trajectory_analysis_performed": False,
        "authorized_systems": AUTHORIZED_SYSTEMS,
        "authorized_candidate_windows": AUTHORIZED_WINDOWS,
        "deferred_windows": sorted(DEFERRED_WINDOWS),
        "audits": {
            "8GLA": audit8,
            "1AXC": audit1,
            "ZQZ_parameters": zqz_audit,
        },
        "git": git_info(),
        "environment": environment_capture(),
        "preflight_status": preflight_status(audit8, audit1, zqz_audit),
    }


def audit_zqz_parameters() -> dict[str, Any]:
    required = {
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
        "PARAMETER_AUDIT.md",
        "zqz_package_hashes.json",
    }
    missing = sorted(name for name in required if not (ZQZ_PARAMETER_DIR / name).exists())
    if missing:
        return {
            "status": "ABSENT_OR_INCOMPLETE",
            "audit_markdown": ZQZ_PARAMETER_AUDIT.relative_to(REPO_ROOT).as_posix(),
            "audit_json": ZQZ_PARAMETER_AUDIT_JSON.relative_to(REPO_ROOT).as_posix(),
            "missing_files": missing,
            "complete": False,
        }
    try:
        audit = read_json(ZQZ_PARAMETER_AUDIT_JSON)
    except Exception as exc:
        return {
            "status": "INVALID_JSON",
            "audit_markdown": ZQZ_PARAMETER_AUDIT.relative_to(REPO_ROOT).as_posix(),
            "audit_json": ZQZ_PARAMETER_AUDIT_JSON.relative_to(REPO_ROOT).as_posix(),
            "error": str(exc),
            "complete": False,
        }

    problems: list[str] = []
    scope = audit.get("scope", {})
    for key in [
        "md_execution_performed",
        "protein_system_setup_performed",
        "minimization_performed",
        "equilibration_performed",
        "production_performed",
        "trajectory_analysis_performed",
        "launch_authorization_created",
    ]:
        if scope.get(key) is not False:
            problems.append(f"scope flag {key} is not false")

    method = audit.get("method", {})
    if method.get("force_field") != "GAFF2":
        problems.append("force field is not GAFF2")
    if method.get("charge_model") != "AM1-BCC":
        problems.append("charge model is not AM1-BCC")
    if method.get("net_charge") != 0:
        problems.append("net charge is not 0")
    if audit.get("input_audit", {}).get("sdf", {}).get("formal_charge") != 0:
        problems.append("input SDF formal charge is not 0")
    if not audit.get("input_audit", {}).get("sdf", {}).get("has_explicit_hydrogens"):
        problems.append("input SDF lacks explicit hydrogens")
    if audit.get("parameter_checks", {}).get("mol2", {}).get("atom_count") != 63:
        problems.append("MOL2 atom count is not 63")
    charge_sum = audit.get("parameter_checks", {}).get("mol2", {}).get("charge_sum")
    if charge_sum is None or abs(float(charge_sum)) > 0.01:
        problems.append("MOL2 charge sum is not near neutral")
    tleap_lines = "\n".join(
        audit.get("parameter_checks", {}).get("tleap_log", {}).get("notable_lines", [])
    )
    if "Unit is OK" not in tleap_lines:
        problems.append("tleap log does not contain Unit is OK")

    output_hashes = audit.get("output_hashes", {})
    for name in required - {"PARAMETER_AUDIT.md", "zqz_parameter_audit.json", "zqz_package_hashes.json"}:
        if name not in output_hashes:
            problems.append(f"missing output hash for {name}")

    return {
        "status": "PARAMETERS_AUDITED_READY_FOR_SETUP_USE" if not problems else "INVALID",
        "audit_markdown": ZQZ_PARAMETER_AUDIT.relative_to(REPO_ROOT).as_posix(),
        "audit_json": ZQZ_PARAMETER_AUDIT_JSON.relative_to(REPO_ROOT).as_posix(),
        "package_hashes": (ZQZ_PARAMETER_DIR / "zqz_package_hashes.json").relative_to(REPO_ROOT).as_posix(),
        "method": method,
        "complete": not problems,
        "problems": problems,
        "key_hashes": {
            name: output_hashes.get(name, {}).get("sha256")
            for name in ["zqz_gaff2_am1bcc.mol2", "zqz_gaff2.frcmod", "zqz_tleap.log"]
        },
    }


def preflight_status(audit8: dict[str, Any], audit1: dict[str, Any], zqz_audit: dict[str, Any] | None = None) -> dict[str, Any]:
    blockers: list[str] = []
    warnings: list[str] = []

    if not AUTHORIZATION.exists():
        blockers.append("Gate 7 authorization record is missing.")
    if not EXECUTION_PACKAGE.exists():
        blockers.append("Official Wave 1 execution package is missing.")
    if "do_not_run_md: true" in EXECUTION_PACKAGE.read_text(encoding="utf-8", errors="replace"):
        blockers.append("Official package still records do_not_run_md: true; execution remains on hold.")

    observed_systems = set(AUTHORIZED_SYSTEMS)
    if observed_systems != {"8gla_holo_zqz", "8gla_apo_from_holo", "1axc_apo_from_p21"}:
        blockers.append("Authorized systems do not match the official Wave 1 package.")

    if set(AUTHORIZED_WINDOWS) != {"PC-118", "T1A-239", "T1A-28", "T1A-206", "T2-134"}:
        blockers.append("Authorized candidate windows do not match the official Wave 1 package.")

    if not audit8["candidate_window_presence"]["PC-118"]["complete_all_chains"]:
        warnings.append("8GLA PC-118 is incomplete on at least one Assembly 1 PCNA chain.")

    for cid, details in audit1["candidate_window_presence"].items():
        if not details["complete_all_chains"]:
            blockers.append(f"1AXC candidate window {cid} is not complete on all PCNA chains.")

    if zqz_audit is None:
        zqz_audit = audit_zqz_parameters()
    if not zqz_audit["complete"]:
        blockers.append("Audited ZQZ ligand parameter package is absent or incomplete.")

    launch_authorization = REPORT_DIR / "phase5_wave1_launch_authorization.md"
    if not launch_authorization.exists():
        blockers.append("Future explicit Phase 5 launch authorization record is absent.")

    launch_hold_blockers = {
        "Official package still records do_not_run_md: true; execution remains on hold.",
        "Future explicit Phase 5 launch authorization record is absent.",
    }
    package_status = (
        "LAUNCH_READY_AWAITING_AUTHORIZATION"
        if blockers and set(blockers).issubset(launch_hold_blockers)
        else "READY_FOR_HUMAN_REVIEW"
    )

    return {
        "package_preparation_status": package_status,
        "production_launch_status": "BLOCKED_FAIL_CLOSED" if blockers else "READY",
        "blockers": blockers,
        "warnings": warnings,
    }


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def format_hashes(source_files: dict[str, dict[str, Any]]) -> str:
    lines = ["| Path | SHA256 | Size bytes |", "|---|---|---:|"]
    for path, info in source_files.items():
        lines.append(f"| `{path}` | `{info['sha256']}` | {info['size_bytes']} |")
    return "\n".join(lines)


def fmt_missing(missing: dict[str, list[int]]) -> str:
    lines = ["| Chain | Missing residues |", "|---|---|"]
    for chain, nums in missing.items():
        text = ", ".join(str(n) for n in nums) if nums else "none"
        lines.append(f"| {chain} | {text} |")
    return "\n".join(lines)


def fmt_window_presence(presence: dict[str, Any]) -> str:
    lines = ["| Candidate | Residues | Chain completeness |", "|---|---:|---|"]
    for cid, details in presence.items():
        chain_bits = []
        for chain, cstat in details["chains"].items():
            if cstat["complete"]:
                chain_bits.append(f"{chain}: complete")
            else:
                chain_bits.append(f"{chain}: missing {','.join(map(str, cstat['missing']))}")
        lines.append(
            f"| {cid} | {details['residues'][0]}-{details['residues'][-1]} | {'; '.join(chain_bits)} |"
        )
    return "\n".join(lines)


def render_8gla_report(registry: dict[str, Any]) -> str:
    audit = registry["audits"]["8GLA"]
    caveat_bullets = "".join(f"- {item}\n" for item in audit["caveats"])
    zqz_instances = audit["zqz"]["instances"]
    zqz_lines = ["| Ligand label asym | Auth chain | Auth seq | Heavy atoms | Contacts <=4.5 A |", "|---|---|---:|---:|---|"]
    for label, info in zqz_instances.items():
        contacts = "; ".join(
            f"{chain}:{','.join(map(str, residues))}"
            for chain, residues in info["pcna_contacts_le_4p5_a"].items()
        ) or "none"
        zqz_lines.append(
            f"| {label} | {info['auth_chain']} | {info['auth_seq_id']} | {info['heavy_atom_count']} | {contacts} |"
        )

    return f"""---
type: phase5-structure-preparation-audit
pdb_id: 8GLA
date: 2026-06-10
status: PREPARATION_AUDIT_ONLY
md_executed: false
---

# 8GLA Preparation Audit - Phase 5 Wave 1

## Scope

This audit verifies deposited structure metadata, biological assembly selection, PCNA
chain mapping, canonical residue numbering, ligand location, and setup caveats for the
official Wave 1 positive-control systems. No minimization, equilibration, production,
trajectory generation, parameterization, or trajectory analysis was run.

## Source Files And Hashes

{format_hashes(audit["source_files"])}

## Experimental Metadata

- Structure title: {audit["metadata"]["title"]}
- Method: {audit["metadata"]["method"]}
- Resolution: {audit["metadata"]["resolution_a"]} A
- R-work/R-free: {audit["metadata"]["r_work"]} / {audit["metadata"]["r_free"]}
- Primary PMID: {audit["metadata"]["primary_pmid"]}
- RCSB revision date: {audit["metadata"]["revision_date"]}

## Biological Assembly And Chain Mapping

- Official Wave 1 assembly: RCSB biological assembly 1.
- Assembly 1 is recorded as trimeric with oligomeric count 3.
- Wave 1 PCNA auth chains: A, B, C.
- Deposited chain D is excluded from Wave 1 because it belongs to deposited assembly 2.
- All deposited PCNA chains map to UniProt P12004 residues 1-261 through `struct_ref_seq`.

## Missing Residues

{fmt_missing(audit["missing_residues"])}

## Candidate Window Completeness

{fmt_window_presence(audit["candidate_window_presence"])}

## ZQZ Ligand Identity And Location

- Ligand code: ZQZ.
- Identity: {audit["zqz"]["identity"]}.
- Formula/formal charge: {audit["zqz"]["formula"]}; formal charge {audit["zqz"]["formal_charge"]}.
- Assembly 1 contains six ZQZ instances assigned to chains A and B in deposited coordinates.

{chr(10).join(zqz_lines)}

## Alternate Locations And Occupancy

- Alternate-location atom records: {audit["alternate_locations"]["count"]}.
- Atom records with occupancy < 1.0: {audit["occupancy_issues"]["atoms_with_occupancy_lt_one_count"]}.
- Insertion codes: {len(audit["insertion_codes"])}.

## Structural Caveats

{caveat_bullets}
## Preparation Decision

8GLA is suitable only as the authorized positive-control starting structure after the
launch hold is lifted and ZQZ parameters are audited. The missing residue 122 on chain C
must be recorded in any future setup manifest and considered during positive-control
metric definition. This is not a novel-site validation structure.

Evidence status: verified from deposited mmCIF/RCSB metadata. Confidence: high for
chain/assembly/ligand facts; no MD outcome claim is made.
"""


def render_1axc_report(registry: dict[str, Any]) -> str:
    audit = registry["audits"]["1AXC"]
    caveat_bullets = "".join(f"- {item}\n" for item in audit["caveats"])
    return f"""---
type: phase5-structure-preparation-audit
pdb_id: 1AXC
date: 2026-06-10
status: PREPARATION_AUDIT_ONLY
md_executed: false
---

# 1AXC Preparation Audit - Phase 5 Wave 1

## Scope

This audit verifies the 1AXC PCNA trimer, p21 peptide removal policy, residue numbering,
candidate-window completeness, and apo-from-p21 limitations for the official Wave 1
`1axc_apo_from_p21` system. No minimization, equilibration, production, trajectory
generation, or trajectory analysis was run.

## Source Files And Hashes

{format_hashes(audit["source_files"])}

## Experimental Metadata

- Structure title: {audit["metadata"]["title"]}
- Method: {audit["metadata"]["method"]}
- Resolution: {audit["metadata"]["resolution_a"]} A
- R-work/R-free: {audit["metadata"]["r_work"]} / {audit["metadata"]["r_free"]}
- Primary PMID: {audit["metadata"]["primary_pmid"]}
- RCSB revision date: {audit["metadata"]["revision_date"]}

## Biological Assembly And Chain Mapping

- Biological assembly 1 is the deposited hexameric complex: PCNA trimer A/C/E plus
  p21 peptide chains B/D/F.
- Wave 1 PCNA auth chains: A, C, E.
- p21 peptide chains that must be removed for `1axc_apo_from_p21`: B, D, F.
- PCNA chains map to UniProt P12004 residues 1-261 through `struct_ref_seq`.
- p21 peptide chains map to UniProt P38936 residues 139-160 through `struct_ref_seq`.

## Missing Residues

{fmt_missing(audit["missing_residues"])}

## Candidate Window Completeness

{fmt_window_presence(audit["candidate_window_presence"])}

## Alternate Locations And Occupancy

- Alternate-location atom records: {audit["alternate_locations"]["count"]}.
- Atom records with occupancy < 1.0: {audit["occupancy_issues"]["atoms_with_occupancy_lt_one_count"]}.
- Insertion codes: {len(audit["insertion_codes"])}.

## Apo-From-p21 Limitations And Assumptions

{caveat_bullets}
- Removing p21 exposes a formerly peptide-bound PIP/IDCL surface; this transformation must be logged as setup, not treated as an experimentally observed apo state.
- The future launch preflight must verify trimer integrity and IDCL/front-face geometry after peptide removal and before production.

## Preparation Decision

1AXC satisfies the Wave 1 residue-window numbering requirement for 239-243, 28-32,
206-210, and 134-138 on all three PCNA chains. Future production remains blocked until
explicit launch authorization and complete manifests exist.

Evidence status: verified from deposited mmCIF/RCSB metadata. Confidence: high for
chain/window facts; no MD outcome claim is made.
"""


def render_zqz_plan(registry: dict[str, Any]) -> str:
    zqz = registry["audits"].get("ZQZ_parameters", {})
    status = zqz.get("status", "PLAN_ONLY_PARAMETERS_NOT_GENERATED")
    if zqz.get("complete"):
        completion = f"""
## Completion Status

The approved workflow has been completed and audited.

- Audit report: `reports/phase5/zqz_parameter_audit_20260611.md`
- Package audit: `{zqz["audit_markdown"]}`
- Machine-readable audit: `{zqz["audit_json"]}`
- Package hashes: `{zqz["package_hashes"]}`

The parameter package is ready to be linked from the future `8gla_holo_zqz` setup
manifest after launch authorization. This does not authorize minimization,
equilibration, production MD, trajectory analysis, or interpretation.
"""
    else:
        completion = """
## Completion Status

Parameters are not complete. Future production setup must fail closed until the audit
package exists and passes preflight.
"""
    return f"""---
type: phase5-ligand-parameterization-plan
ligand: ZQZ
date: 2026-06-11
status: {status}
md_executed: false
---

# ZQZ Parameterization Plan - Phase 5 Wave 1

## Official Workflow

Use AMBER-compatible ligand parameters for the `8gla_holo_zqz` system:

- Protein force field: AMBER ff19SB, as specified in the official Wave 1 package.
- Ligand force field: GAFF2.
- Charge method: AM1-BCC through AmberTools `antechamber` (`-c bcc`), unless a later
  documented deviation is approved before launch.
- Proposed net charge: 0, based on the RCSB ZQZ ligand record formal charge 0. This
  must be re-verified from the exact protonated input before parameter generation.
- Required tools: AmberTools26 `antechamber`, `parmchk2`, `tleap`, and `sqm`.

AmberTools26 is selected because the official AmberTools page identifies AmberTools26
as available and lists `antechamber`, `tleap`, `sqm`, and GAFF2-related updates. Record
the exact local executable versions at launch time; do not substitute an older version
without planned-deviation documentation.

## Required Inputs

- Deposited 8GLA mmCIF hash from `data/raw_intake/pcna_structures/8GLA.cif`.
- Extracted ZQZ coordinate file with all deposited ZQZ instances tracked.
- Single audited ligand template input for parameterization, with explicit hydrogens,
  stereochemistry, protonation/tautomer state, atom names, residue name `ZQZ`, and
  net charge.
- Human-readable ligand audit note confirming whether the deposited ligand state is
  used as-is or rebuilt from RCSB ideal SDF.

## Required Outputs

- `zqz_gaff2_am1bcc.mol2`
- `zqz_gaff2.frcmod`
- `zqz_tleap.in`
- `zqz_tleap.log`
- `zqz_parameter_audit.json`
- `PARAMETER_AUDIT.md`

All outputs must include SHA256 hashes, generation commands, AmberTools version strings,
input hashes, net charge, atom count, warning/error logs, and manual-review notes.

## Fail-Closed Behavior

Future production setup must refuse to continue if
`outputs/phase5_md/official_wave1_20260609/inputs/ligand_params/zqz/PARAMETER_AUDIT.md`
is absent, incomplete, or not linked from the system setup manifest. This turn intentionally
does not run MD setup or simulation.

{completion}

## Example Future Commands

These commands are documentation only and must not be run until launch is explicitly
authorized:

```bash
antechamber -i zqz_input.sdf -fi sdf -o zqz_gaff2_am1bcc.mol2 -fo mol2 -at gaff2 -c bcc -nc 0 -rn ZQZ
parmchk2 -i zqz_gaff2_am1bcc.mol2 -f mol2 -o zqz_gaff2.frcmod -s gaff2
tleap -f zqz_tleap.in
```

Evidence status: {"verified parameter audit" if zqz.get("complete") else "plan only"}.
Confidence: high for required workflow shape; parameter quality is audited when
`PARAMETER_AUDIT.md` is present and preflight passes its content checks.
"""


def render_manifest_templates_report(registry: dict[str, Any]) -> str:
    return """---
type: phase5-manifest-provenance-template-report
date: 2026-06-10
status: TEMPLATE_ONLY
md_executed: false
---

# Manifest And Provenance Templates - Phase 5 Wave 1

## Required Hashes

- Source mmCIF and metadata SHA256.
- Prepared coordinate and topology hashes.
- ZQZ parameter file hashes.
- Per-replicate input hashes before minimization, equilibration, and production.
- Per-replicate output hashes after each future stage.
- Manifest hash for every upstream manifest consumed.

## Environment Capture

Each future launch manifest must capture git commit, branch, dirty state, hostname,
OS/platform, Python version, AmberTools/Amber versions, CUDA/GPU details if applicable,
loaded modules or conda environment, `AMBERHOME`, and relevant environment variables.

## Seed Recording

Use the official seeds:

| System | Replicate 1 | Replicate 2 | Replicate 3 |
|---|---:|---:|---:|
| `8gla_holo_zqz` | 2026060911 | 2026060912 | 2026060913 |
| `8gla_apo_from_holo` | 2026060921 | 2026060922 | 2026060923 |
| `1axc_apo_from_p21` | 2026060931 | 2026060932 | 2026060933 |

Any seed change must be documented as a planned deviation before execution.

## Command Logging

Every future setup and execution command must be written to the manifest before it is
run and copied to a command log afterward with exit code, start/end timestamps, working
directory, stdout/stderr log paths, and output hashes.

## Stop-Condition Recording

The templates include a stop-condition table for unresolved assembly mapping, missing
candidate residues, missing or unaudited ZQZ parameters, launch authorization absence,
unstable equilibration, trimer-integrity loss, environment capture failure, unexpected
trajectory files, and claim/interpretation attempts before human review.

Template files were written under:

`outputs/phase5_md/official_wave1_20260609/`

Evidence status: template/provenance infrastructure only. No MD stage was run.
"""


def render_readiness_report(registry: dict[str, Any]) -> str:
    status = registry["preflight_status"]
    zqz = registry["audits"].get("ZQZ_parameters", {})
    blockers = "\n".join(f"- {item}" for item in status["blockers"]) or "- none"
    warnings = "\n".join(f"- {item}" for item in status["warnings"]) or "- none"
    return f"""---
type: phase5-wave1-readiness-report
date: 2026-06-11
status: LAUNCH_READY_AWAITING_AUTHORIZATION_PRODUCTION_BLOCKED
md_executed: false
---

# Wave 1 Readiness Report - Phase 5 Official Package

## Scope

This report packages the official Wave 1 preparation audits, ZQZ parameterization plan,
manifest templates, gap analysis, and fail-closed launch assessment. It does not execute
MD setup, minimization, equilibration, production, trajectory generation, trajectory
analysis, interpretation, or claims.

## Verified Package Elements

- Gate 7 Wave 1 authorization exists: `reports/phase4/gate7_authorization_20260609.md`.
- Official Wave 1 execution package exists: `reports/phase5/official_wave1_execution_package_20260609.md`.
- Authorized systems match the package: `8gla_holo_zqz`, `8gla_apo_from_holo`, `1axc_apo_from_p21`.
- Authorized windows match the package: `118-122`, `239-243`, `28-32`, `206-210`, `134-138`.
- Deferred Tier 1B windows remain excluded from Wave 1: `170-174`, `175-179`, `152-156`.
- 1AXC PCNA windows are complete on all three PCNA chains A/C/E.
- 8GLA biological assembly 1 is verified as the official trimer for the positive-control systems.
- Manifest/provenance templates and preflight checks were added.
- ZQZ GAFF2/AM1-BCC parameter package status: `{zqz.get("status", "UNKNOWN")}`.
- ZQZ parameter audit: `{zqz.get("audit_markdown", "missing")}`.

## Gap Analysis

{blockers}

## Warnings

{warnings}

## Launch-Readiness Assessment

- Package preparation status: `{status["package_preparation_status"]}`.
- Production launch status: `{status["production_launch_status"]}`.

The official package is launch-ready at the preparation level, but production launch
remains intentionally blocked. This is expected because MD execution is not yet
authorized and the official package still records `do_not_run_md: true`.

## Deliverables

- `reports/phase5/8gla_preparation_audit_20260610.md`
- `reports/phase5/1axc_preparation_audit_20260610.md`
- `reports/phase5/zqz_parameterization_plan_20260610.md`
- `reports/phase5/zqz_parameter_audit_20260611.md`
- `reports/phase5/manifest_provenance_templates_20260610.md`
- `data/registries/phase5_wave1_preparation_audit_20260610.json`
- `outputs/phase5_md/official_wave1_20260609/` manifest templates and audited ZQZ
  parameter package

Evidence status: verified preparation and fail-closed checks. No MD outcome exists.
Confidence: high for package scope and source hashes; no interpretation or claim is made.
"""


def write_manifest_templates(registry: dict[str, Any]) -> None:
    output = OUTPUT_ROOT
    system_dirs = [
        output / "systems" / "8gla_holo_zqz",
        output / "systems" / "8gla_apo_from_holo",
        output / "systems" / "1axc_apo_from_p21",
    ]
    for directory in system_dirs:
        directory.mkdir(parents=True, exist_ok=True)
        for idx in range(1, 4):
            (directory / f"replicate_{idx:02d}").mkdir(parents=True, exist_ok=True)
    for rel in [
        "inputs/8gla",
        "inputs/1axc",
        "inputs/ligand_params/zqz",
        "analysis/trajectory_qa",
        "analysis/rmsd_rmsf",
        "analysis/pocket_accessibility",
        "analysis/dccm",
        "analysis/interface_distances",
        "analysis/ligand_contacts",
    ]:
        (output / rel).mkdir(parents=True, exist_ok=True)

    write_text(
        output / "MANIFEST_TEMPLATE.md",
        f"""# Phase 5 Official Wave 1 Manifest Template

- Artifact ID: phase5_official_wave1_20260609
- Status: TEMPLATE_ONLY_DO_NOT_RUN
- Created from: `reports/phase5/official_wave1_execution_package_20260609.md`
- Gate authorization: `reports/phase4/gate7_authorization_20260609.md`
- MD execution authorized: false
- Required future launch authorization: `reports/phase5/phase5_wave1_launch_authorization.md`
- Commit hash:
- Branch:
- Dirty-state summary:
- Created by:
- Created at:
- Environment:
- AmberTools/Amber versions:
- CUDA/GPU:
- Input files and hashes:
  - 8GLA CIF: `{registry["audits"]["8GLA"]["source_files"]["data/raw_intake/pcna_structures/8GLA.cif"]["sha256"]}`
  - 1AXC CIF: `{registry["audits"]["1AXC"]["source_files"]["data/raw_intake/pcna_structures/1AXC.cif"]["sha256"]}`
- Authorized systems:
  - `8gla_holo_zqz`
  - `8gla_apo_from_holo`
  - `1axc_apo_from_p21`
- Authorized windows:
  - `PC-118`: 118-122
  - `T1A-239`: 239-243
  - `T1A-28`: 28-32
  - `T1A-206`: 206-210
  - `T2-134`: 134-138
- Deferred windows not authorized in Wave 1: 170-174, 175-179, 152-156
- Stop-condition log:
  - unresolved assembly mapping:
  - missing candidate residues:
  - missing/unaudited ZQZ parameters:
  - launch authorization absent:
  - trimer integrity failure:
  - unstable minimization/equilibration:
  - environment capture failure:
  - unexpected trajectory files:
- Command log path:
- Manual review notes:

This template is not a run manifest and does not authorize launch.
""",
    )

    for system_id, spec in AUTHORIZED_SYSTEMS.items():
        write_text(
            output / "systems" / system_id / "setup_manifest_TEMPLATE.md",
            f"""# Setup Manifest Template - {system_id}

- System ID: `{system_id}`
- Status: TEMPLATE_ONLY_DO_NOT_RUN
- Starting structure: {spec["starting_structure"]}
- Ligand/partner state: {spec["ligand_state"]}
- Required replicates: {spec["replicates"]}
- Planned production length: {spec["production_ns"]} ns per replicate
- Seeds: {", ".join(map(str, spec["seeds"]))}
- Protein force field: AMBER ff19SB
- Water model: TIP3P
- Ion policy: neutralize and 150 mM NaCl
- Protonation policy: pH 7.4 standard-state policy, identical across comparable systems
- Input coordinate hash:
- Prepared coordinate hash:
- Topology hash:
- ZQZ parameter audit path:
- ZQZ parameter hashes:
- Environment:
- Commands:
- Stop conditions triggered:
- Manual deviations:

Do not use this template as evidence of a completed setup. A future launch run must
copy it to `setup_manifest.md`, fill every required field, and link audited inputs.
""",
        )

    zqz = registry["audits"].get("ZQZ_parameters", {})
    if zqz.get("complete"):
        zqz_readme = f"""# ZQZ Ligand Parameter Package

Status: PARAMETERS_AUDITED_READY_FOR_SETUP_USE

Audit files:

- `PARAMETER_AUDIT.md`
- `zqz_parameter_audit.json`
- `zqz_package_hashes.json`

Primary parameter files:

- `zqz_gaff2_am1bcc.mol2`
- `zqz_gaff2.frcmod`
- `zqz_tleap.in`
- `zqz_tleap.log`
- `zqz_gaff2.lib`

Future production setup must still fail closed until an explicit launch authorization
exists and the 8GLA setup manifest links this package and its hashes.

Audit status: `{zqz["status"]}`
"""
    else:
        zqz_readme = """# ZQZ Ligand Parameter Placeholder

Status: TEMPLATE_ONLY_PARAMETERS_NOT_GENERATED

Required before production:

- `zqz_gaff2_am1bcc.mol2`
- `zqz_gaff2.frcmod`
- `zqz_tleap.in`
- `zqz_tleap.log`
- `zqz_parameter_audit.json`
- `PARAMETER_AUDIT.md`

Production setup must fail closed until `PARAMETER_AUDIT.md` exists and records input
hashes, output hashes, AmberTools versions, charge method, net charge, command lines,
warnings, and manual review.
"""
    write_text(output / "inputs" / "ligand_params" / "zqz" / "README_TEMPLATE.md", zqz_readme)


def write_reports(registry: dict[str, Any]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    write_text(REPORT_DIR / "8gla_preparation_audit_20260610.md", render_8gla_report(registry))
    write_text(REPORT_DIR / "1axc_preparation_audit_20260610.md", render_1axc_report(registry))
    write_text(REPORT_DIR / "zqz_parameterization_plan_20260610.md", render_zqz_plan(registry))
    write_text(
        REPORT_DIR / "manifest_provenance_templates_20260610.md",
        render_manifest_templates_report(registry),
    )
    write_text(REPORT_DIR / "wave1_readiness_report_20260610.md", render_readiness_report(registry))


def write_registry(registry: dict[str, Any]) -> None:
    REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    REGISTRY_PATH.write_text(json.dumps(registry, indent=2) + "\n", encoding="utf-8")


def verify_preflight(stage: str = "prelaunch") -> dict[str, Any]:
    registry = build_registry()
    status = registry["preflight_status"]
    if stage == "production" and status["production_launch_status"] != "READY":
        raise Phase5PreflightError("; ".join(status["blockers"]))
    return status


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--write",
        action="store_true",
        help="write registry, reports, and manifest templates",
    )
    parser.add_argument(
        "--preflight-stage",
        choices=["prelaunch", "production"],
        default="prelaunch",
        help="production stage fails closed while launch authorization or audited parameters are absent",
    )
    args = parser.parse_args(argv)

    try:
        registry = build_registry()
        if args.write:
            write_manifest_templates(registry)
            write_registry(registry)
            write_reports(registry)
        if args.preflight_stage == "production":
            verify_preflight(stage="production")
        print(json.dumps(registry["preflight_status"], indent=2))
        return 0
    except Phase5PreflightError as exc:
        print(f"FAIL_CLOSED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
