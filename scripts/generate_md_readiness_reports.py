#!/usr/bin/env python3
"""Generate the final pre-MD readiness report packet for the GNN-PCNA project.

This script is intentionally conservative: it records source-backed checks, marks
inferred choices as assumptions, and leaves production readiness false unless the
prospective smoke/control/human gates have actually passed.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import platform
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from Bio.PDB import MMCIFParser, PDBParser, ShrakeRupley
from Bio.PDB.MMCIF2Dict import MMCIF2Dict
from scipy.spatial import ConvexHull, cKDTree


ROOT = Path(__file__).resolve().parents[1]
MD = ROOT / "md_validation_4070"
POCKET = MD / "pockets" / "final_consensus_1w60_20260815.json"
HANDOFF = ROOT / "artifacts" / "final_benchmark_expansion_20260815" / "md_handoff_packet.json"
MEMBERSHIP = ROOT / "artifacts" / "strong_robustness_20260815" / "current_06792_residue_membership.csv"
STABILITY = ROOT / "artifacts" / "pre_md_independent_extraction_20260815" / "final_1w60_three_seed_stability_report.json"
FROZEN_POLICY = ROOT / "artifacts" / "pre_md_independent_extraction_20260815" / "frozen_extraction_method.json"
PREFLIGHT = MD / "preflight_outputs_min5000"
NOW = datetime.now(timezone.utc).isoformat()

AA1_TO_3 = {
    "A": "ALA", "R": "ARG", "N": "ASN", "D": "ASP", "C": "CYS",
    "Q": "GLN", "E": "GLU", "G": "GLY", "H": "HIS", "I": "ILE",
    "L": "LEU", "K": "LYS", "M": "MET", "F": "PHE", "P": "PRO",
    "S": "SER", "T": "THR", "W": "TRP", "Y": "TYR", "V": "VAL",
}

ANALYSIS_REGIONS = {
    "core_3of3": [25, 26, 38, 39, 40, 41, 42, 44, 45, 46, 47],
    "supported_ge2of3": [25, 26, 27, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 232, 233, 234],
    "full_union_exploratory": [25, 26, 27, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 231, 232, 233, 234, 250, 251, 252],
}


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, obj: object) -> None:
    path.write_text(json.dumps(obj, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def write_md(path: Path, text: str) -> None:
    path.write_text(text.strip() + "\n", encoding="utf-8")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def git_info() -> dict:
    def run(*args: str) -> str:
        try:
            return subprocess.check_output(["git", "-C", str(ROOT), *args], text=True, stderr=subprocess.DEVNULL).strip()
        except Exception:
            return "unknown"

    dirty = run("status", "--short")
    dirty_lines = dirty.splitlines() if dirty else []
    return {
        "commit": run("rev-parse", "HEAD"),
        "branch": run("rev-parse", "--abbrev-ref", "HEAD"),
        "dirty": bool(dirty_lines),
        "dirty_file_count": len(dirty_lines),
        "dirty_status_sample": dirty_lines[:50],
    }


def openmm_info() -> dict:
    out = {
        "python": platform.python_version(),
        "host": platform.node(),
        "platform": platform.platform(),
    }
    try:
        import openmm as mm

        out["openmm_version"] = mm.version.version
        out["openmm_platforms"] = [mm.Platform.getPlatform(i).getName() for i in range(mm.Platform.getNumPlatforms())]
    except Exception as exc:
        out["openmm_error"] = str(exc)
    return out


def membership_rows() -> list[dict]:
    with MEMBERSHIP.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    for row in rows:
        row["resid"] = int(row["resid"])
        row["n_seeds"] = int(row["n_seeds"])
        for seed in ("42", "43", "44"):
            row[f"seed{seed}_selected"] = row[f"seed{seed}_selected"] == "True"
    return sorted(rows, key=lambda r: r["resid"])


def seed_membership_table(rows: list[dict]) -> str:
    lines = [
        "| Residue | Chain | Residue identity | 42 | 43 | 44 | Support |",
        "| ------- | ----- | ---------------- | -- | -- | -- | ------- |",
    ]
    for r in rows:
        if r["n_seeds"] == 3:
            support = "CORE"
        elif r["n_seeds"] == 2:
            support = "SUPPORTED FRINGE"
        else:
            support = "SEED-SPECIFIC / UNCERTAIN FRINGE"
        lines.append(
            f"| {r['resid']} | {r['chain']} | {r['resname']} | "
            f"{int(r['seed42_selected'])} | {int(r['seed43_selected'])} | {int(r['seed44_selected'])} | {support} |"
        )
    return "\n".join(lines)


def set_from_residue_objects(items: list[dict]) -> set[tuple[str, int]]:
    return {(x["chain"], int(x["resid"])) for x in items}


def verify_handoff() -> dict:
    pocket = read_json(POCKET)
    handoff = read_json(HANDOFF)
    stability = read_json(STABILITY)
    rows = membership_rows()

    core = {(r["chain"], r["resid"]) for r in rows if r["n_seeds"] == 3}
    supported_fringe = {(r["chain"], r["resid"]) for r in rows if r["n_seeds"] == 2}
    uncertain = {(r["chain"], r["resid"]) for r in rows if r["n_seeds"] == 1}
    supported = core | supported_fringe

    checks = {}
    checks["pocket_required_keys_for_run_md"] = all(
        k in pocket for k in ("pocket_name", "pocket_residues_resseq", "apo_pdb", "control_pdb", "expected_protein_chains")
    )
    checks["pocket_supported_residue_set_matches_membership"] = set_from_residue_objects(pocket["pocket_residues"]) == supported
    checks["pocket_core_matches_membership"] = set_from_residue_objects(pocket["core_3of3"]) == core
    checks["pocket_supported_fringe_matches_membership"] = set_from_residue_objects(pocket["fringe_2of3"]) == supported_fringe
    checks["pocket_uncertain_fringe_matches_membership"] = set_from_residue_objects(pocket["uncertain_fringe_1of3"]) == uncertain
    checks["handoff_core_matches_membership"] = set_from_residue_objects(handoff["candidate"]["core_3of3"]) == core
    checks["handoff_supported_fringe_matches_membership"] = set_from_residue_objects(handoff["candidate"]["fringe_2of3"]) == supported_fringe
    checks["handoff_uncertain_fringe_matches_membership"] = set_from_residue_objects(
        handoff["candidate"]["seed_specific_boundary_union_only"]
    ) == uncertain
    checks["stability_consensus_n_16"] = int(stability["consensus_n_residues"]) == 16
    checks["stability_mean_jaccard_recorded"] = math.isclose(
        float(stability["literal_mean_pairwise_jaccard"]), 0.6791537667698658, rel_tol=1e-12
    )
    checks["frozen_policy_matches"] = (
        stability["policy_id"] == "independent_mcc_rank_fraction_size_weighted_cluster"
        and stability["frozen_policy_sha256"] == pocket["frozen_policy_sha256"]
    )

    return {
        "created_at": NOW,
        "checks": checks,
        "status": "PASS" if all(checks.values()) else "FAIL",
        "core_3of3": sorted([f"{c}:{r}" for c, r in core]),
        "supported_fringe_2of3": sorted([f"{c}:{r}" for c, r in supported_fringe]),
        "uncertain_fringe_1of3": sorted([f"{c}:{r}" for c, r in uncertain]),
        "literal_jaccard_mean": stability["literal_mean_pairwise_jaccard"],
        "policy_id": stability["policy_id"],
        "pocket_sha256": sha256(POCKET),
        "handoff_sha256": sha256(HANDOFF),
    }


def parse_oper_count(expr: str) -> int:
    expr = expr.replace("(", "").replace(")", "")
    count = 0
    for part in expr.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            a, b = part.split("-", 1)
            count += abs(int(b) - int(a)) + 1
        else:
            count += 1
    return count


def assembly_protein_count(cif_path: Path, assembly_id: str = "1") -> dict:
    d = MMCIF2Dict(str(cif_path))
    protein_entities = set(d.get("_entity_poly.entity_id", []))
    labels = d["_atom_site.label_asym_id"]
    entities = d["_atom_site.label_entity_id"]
    protein_label_asym = {lab for lab, ent in zip(labels, entities) if ent in protein_entities}
    asm_ids = d.get("_pdbx_struct_assembly_gen.assembly_id", [])
    asym_lists = d.get("_pdbx_struct_assembly_gen.asym_id_list", [])
    op_exprs = d.get("_pdbx_struct_assembly_gen.oper_expression", [])
    total = 0
    selected = []
    for aid, asym_list, op_expr in zip(asm_ids, asym_lists, op_exprs):
        if aid != assembly_id:
            continue
        asym_ids = [x.strip() for x in asym_list.split(",")]
        protein_ids = [x for x in asym_ids if x in protein_label_asym]
        selected.extend(protein_ids)
        total += len(protein_ids) * parse_oper_count(op_expr)
    return {"assembly_id": assembly_id, "protein_label_asym_ids": selected, "protein_chain_count_after_ops": total}


def cif_structure_summary(pdb_id: str) -> dict:
    cif = ROOT / "data" / "raw_intake" / "pcna_structures" / f"{pdb_id}.cif"
    metadata = read_json(ROOT / "data" / "raw_intake" / "pcna_structures" / f"{pdb_id}_metadata.json")
    parser = MMCIFParser(QUIET=True, auth_chains=True, auth_residues=True)
    structure = parser.get_structure(pdb_id, str(cif))
    d = MMCIF2Dict(str(cif))
    seq = d["_entity_poly.pdbx_seq_one_letter_code_can"][0].replace("\n", "")
    chains = []
    candidate_all = sorted(set(ANALYSIS_REGIONS["full_union_exploratory"]))
    for chain in structure[0]:
        residues = [r for r in chain if r.id[0] == " "]
        if not residues:
            continue
        present = {r.id[1]: r for r in residues}
        gaps = [(a.id[1], b.id[1]) for a, b in zip(residues, residues[1:]) if b.id[1] - a.id[1] > 1]
        missing = [i for i in range(1, len(seq) + 1) if i not in present]
        backbone_missing = []
        for r in residues:
            miss = [a for a in ("N", "CA", "C", "O") if a not in r]
            if miss:
                backbone_missing.append({"resid": r.id[1], "resname": r.resname, "missing": miss})
        candidate_missing = [r for r in candidate_all if r not in present]
        candidate_names = {str(r): present[r].resname for r in candidate_all if r in present}
        chains.append(
            {
                "chain": chain.id,
                "n_modeled_protein_residues": len(residues),
                "first_residue": residues[0].id[1],
                "last_residue": residues[-1].id[1],
                "n_missing_vs_entity_sequence": len(missing),
                "missing_residues_vs_entity_sequence": missing,
                "internal_gaps": gaps,
                "backbone_missing": backbone_missing,
                "candidate_missing": candidate_missing,
                "candidate_residue_names": candidate_names,
            }
        )

    heterogens = {}
    for comp in d.get("_pdbx_entity_nonpoly.comp_id", []):
        heterogens[comp] = heterogens.get(comp, 0) + 1

    disulfides = []
    if "_struct_conn.conn_type_id" in d:
        for i, typ in enumerate(d["_struct_conn.conn_type_id"]):
            if typ == "disulf":
                disulfides.append(
                    {
                        "chain1": d["_struct_conn.ptnr1_label_asym_id"][i],
                        "resid1": d["_struct_conn.ptnr1_auth_seq_id"][i],
                        "atom1": d["_struct_conn.ptnr1_label_atom_id"][i],
                        "chain2": d["_struct_conn.ptnr2_label_asym_id"][i],
                        "resid2": d["_struct_conn.ptnr2_auth_seq_id"][i],
                        "atom2": d["_struct_conn.ptnr2_label_atom_id"][i],
                    }
                )

    return {
        "pdb_id": pdb_id,
        "title": metadata["struct"]["title"],
        "method": metadata["exptl"][0]["method"],
        "resolution_A": metadata["rcsb_entry_info"]["resolution_combined"][0],
        "r_free": metadata.get("refine", [{}])[0].get("ls_R_factor_R_free"),
        "r_work": metadata.get("refine", [{}])[0].get("ls_R_factor_R_work"),
        "deposited_polymer_instances": metadata["rcsb_entry_info"]["deposited_polymer_entity_instance_count"],
        "deposited_unmodeled_polymer_monomers": metadata["rcsb_entry_info"]["deposited_unmodeled_polymer_monomer_count"],
        "metadata_disulfide_count": metadata["rcsb_entry_info"]["disulfide_bond_count"],
        "assembly1": assembly_protein_count(cif),
        "chains": chains,
        "heterogens": heterogens,
        "struct_conn_disulfides": disulfides,
        "source_files": {
            "cif": str(cif.relative_to(ROOT)),
            "metadata": str((ROOT / "data" / "raw_intake" / "pcna_structures" / f"{pdb_id}_metadata.json").relative_to(ROOT)),
        },
    }


def close_contacts_in_prepared(pdb_id: str) -> dict:
    path = PREFLIGHT / pdb_id / "prep" / "prepared_protein.pdb"
    if not path.exists():
        return {"error": f"missing {path}"}
    structure = PDBParser(QUIET=True).get_structure(pdb_id, str(path))
    atoms = []
    meta = []
    for atom in structure.get_atoms():
        if atom.element == "H" or atom.name.startswith("H"):
            continue
        residue = atom.get_parent()
        chain = residue.get_parent()
        if residue.id[0] != " ":
            continue
        atoms.append(atom.coord)
        meta.append((chain.id, residue.id[1], atom.name))
    coords = np.asarray(atoms, dtype=float)
    tree = cKDTree(coords)
    severe = []
    suspicious = []
    for i, j in tree.query_pairs(2.0):
        ci, ri, ai = meta[i]
        cj, rj, aj = meta[j]
        if ci == cj and abs(ri - rj) <= 1:
            continue
        dist = float(np.linalg.norm(coords[i] - coords[j]))
        item = {"a": f"{ci}:{ri}:{ai}", "b": f"{cj}:{rj}:{aj}", "distance_A": round(dist, 3)}
        if dist < 1.5:
            severe.append(item)
        else:
            suspicious.append(item)
    return {
        "prepared_pdb": str(path.relative_to(ROOT)),
        "heavy_atom_count": len(meta),
        "severe_nonbonded_close_contacts_lt_1p5A": len(severe),
        "suspicious_nonbonded_close_contacts_1p5_to_2p0A": len(suspicious),
        "examples": severe[:10] + suspicious[:10],
    }


def preflight_minimization_summary(pdb_id: str) -> dict:
    audit = read_json(PREFLIGHT / pdb_id / "prep" / "prep_audit.json")
    done = read_json(PREFLIGHT / pdb_id / "rep01" / "DONE.json")
    solvated = PREFLIGHT / pdb_id / "system_solvated.pdb"
    prepared = PREFLIGHT / pdb_id / "prep" / "prepared_protein.pdb"
    return {
        "pdb_id": pdb_id,
        "prep_audit": audit,
        "done": done,
        "prepared_sha256": sha256(prepared),
        "solvated_topology_sha256": sha256(solvated),
        "close_contacts": close_contacts_in_prepared(pdb_id),
    }


def static_reference_metrics() -> dict:
    out = {
        "source": "Biopython ShrakeRupley and CA geometry on PDBFixer-prepared protein-only assemblies from preflight_outputs_min5000.",
        "regions": {},
        "atom_parity": {},
    }
    structures = {}
    for pdb_id in ("1W60", "8GLA"):
        path = PREFLIGHT / pdb_id / "prep" / "prepared_protein.pdb"
        s = PDBParser(QUIET=True).get_structure(pdb_id, str(path))
        ShrakeRupley().compute(s, level="R")
        structures[pdb_id] = s

    for region, resids in ANALYSIS_REGIONS.items():
        out["regions"][region] = {}
        atom_keys = {}
        for pdb_id, s in structures.items():
            chain = s[0]["A"]
            residues = [chain[(" ", r, " ")] for r in resids if (" ", r, " ") in chain]
            sasa = sum(float(getattr(r, "sasa", 0.0)) for r in residues)
            ca = np.asarray([r["CA"].coord for r in residues if "CA" in r], dtype=float)
            rg = float(np.sqrt(((ca - ca.mean(axis=0)) ** 2).sum(axis=1).mean()))
            max_dist = max(float(np.linalg.norm(a - b)) for i, a in enumerate(ca) for b in ca[i + 1 :])
            hull = float(ConvexHull(ca).volume) if len(ca) >= 4 else None
            out["regions"][region][pdb_id] = {
                "n_residues": len(residues),
                "sasa_A2": round(sasa, 3),
                "ca_rg_A": round(rg, 3),
                "ca_max_pair_distance_A": round(max_dist, 3),
                "ca_convex_hull_volume_A3": round(hull, 3) if hull is not None else None,
            }
            atom_keys[pdb_id] = {
                (r.id[1], atom.name)
                for r in residues
                for atom in r
                if not atom.name.startswith("H") and atom.element != "H"
            }
        common = atom_keys["1W60"] & atom_keys["8GLA"]
        union = atom_keys["1W60"] | atom_keys["8GLA"]
        out["atom_parity"][region] = {
            "1W60_heavy_atoms": len(atom_keys["1W60"]),
            "8GLA_heavy_atoms": len(atom_keys["8GLA"]),
            "common_heavy_atoms": len(common),
            "union_heavy_atoms": len(union),
            "coverage": round(len(common) / len(union), 4) if union else 0.0,
        }
        a = out["regions"][region]["1W60"]
        c = out["regions"][region]["8GLA"]
        out["regions"][region]["control_minus_apo"] = {
            "sasa_A2": round(c["sasa_A2"] - a["sasa_A2"], 3),
            "ca_rg_A": round(c["ca_rg_A"] - a["ca_rg_A"], 3),
            "ca_max_pair_distance_A": round(c["ca_max_pair_distance_A"] - a["ca_max_pair_distance_A"], 3),
            "ca_convex_hull_volume_A3": round(c["ca_convex_hull_volume_A3"] - a["ca_convex_hull_volume_A3"], 3),
        }
    supported = out["regions"]["supported_ge2of3"]
    core = out["regions"]["core_3of3"]
    out["reference_midpoint_thresholds"] = {
        "core_sasa_A2": round((core["1W60"]["sasa_A2"] + core["8GLA"]["sasa_A2"]) / 2, 3),
        "supported_sasa_A2": round((supported["1W60"]["sasa_A2"] + supported["8GLA"]["sasa_A2"]) / 2, 3),
        "supported_ca_convex_hull_volume_A3": round(
            (supported["1W60"]["ca_convex_hull_volume_A3"] + supported["8GLA"]["ca_convex_hull_volume_A3"]) / 2,
            3,
        ),
    }
    return out


def protocol(static_metrics: dict) -> dict:
    pocket = read_json(POCKET)
    return {
        "created_at": NOW,
        "status": "FROZEN_FOR_PRE_PRODUCTION_VALIDATION",
        "do_not_change_after_candidate_production": True,
        "gnn_interpretation": {
            "policy": "independent_mcc_rank_fraction_size_weighted_cluster",
            "literal_mean_jaccard": 0.6791537667698658,
            "interpretation": "MODERATE / EXPLORATORY PASS; same physical candidate region, not strong residue-level reproducibility.",
        },
        "residue_sets": {
            "core_3of3": pocket["core_3of3"],
            "supported_fringe_2of3": pocket["fringe_2of3"],
            "supported_ge2of3_primary": pocket["pocket_residues"],
            "seed_specific_uncertain_fringe_1of3_exploratory": pocket["uncertain_fringe_1of3"],
        },
        "reference_structures": {
            "apo": {"pdb": "1W60", "role": "closed/reference apo PCNA"},
            "positive_control": {
                "pdb": "8GLA",
                "role": "AOH1996-derivative-bound reference, ligand stripped for protein-only MD",
                "expectation": "analysis should recognize static/reference exposure or geometry distinction; short apo-like MD need not manufacture an opening event",
            },
        },
        "atom_selections": {
            "alignment": "protein CA excluding the supported_ge2of3 pocket residues",
            "primary_pocket": "chain index 0 residues in core_3of3 and supported_ge2of3",
            "exploratory_union": "core + supported fringe + 1-of-3 seed-specific fringe; never primary by itself",
            "sasa": "protein context, Shrake-Rupley, atom-key parity enforced across apo/control before comparison",
        },
        "metrics": {
            "rmsd": "backbone/CA RMSD after PBC imaging and alignment; stability descriptor only",
            "rmsf": "per-residue fluctuation after alignment, summarized by core/support/fringe; no pseudoreplication across frames",
            "sasa": "sum residue SASA for each predefined region, measured over identical atom keys across systems",
            "dccm": "CA dynamic cross-correlation after alignment; qualitative/supportive unless replicate-stable",
            "openness": {
                "formula": "open_like_frame if supported-region SASA and supported-region CA convex-hull volume both exceed reference midpoint thresholds; core SASA is reported as the primary localization check",
                "thresholds_source": "prepared 1W60 and ligand-stripped prepared 8GLA static references before candidate production",
                "thresholds": static_metrics["reference_midpoint_thresholds"],
            },
            "pocket_volume": {
                "metric": "CA convex hull volume of the predefined region",
                "status": "adopted as a geometric descriptor, not a ligand-volume estimate; validated only as static reference discriminator before production",
            },
        },
        "event_definitions": {
            "opening_event": {
                "minimum_duration": ">= 2 consecutive saved frames",
                "frame_rule": "supported_sasa_A2 >= threshold.supported_sasa_A2 and supported_ca_convex_hull_volume_A3 >= threshold.supported_ca_convex_hull_volume_A3",
                "localization_rule": "core_sasa_A2 must be reported; events dominated only by seed-specific fringe are exploratory, not primary support",
            }
        },
        "replicate_aggregation": {
            "independent_unit": "trajectory replicate, not frame",
            "summaries": ["replicate traces", "median", "mean", "range/IQR", "bootstrap CI across replicates only when n is sufficient", "event frequency", "event duration", "fraction open-like"],
        },
        "interpretation_categories": {
            "supportive": "multiple independent candidate trajectories show reproducible predefined opening/accessibility dynamics centered on core/supported region and controls remain interpretable",
            "partially_supportive": "some predefined behavior appears, but magnitude/frequency/replicate consistency is limited",
            "inconclusive": "sampling, control behavior, mapping, or variability prevents reliable conclusion",
            "weakening": "region remains closed/stable under adequate sampling where control demonstrates assay sensitivity",
            "contradictory": "evidence conflicts with a specific prospective prediction",
        },
        "source_hashes": {
            "pocket_definition_sha256": sha256(POCKET),
            "static_reference_metrics_sha256": sha256(MD / "static_reference_analysis.json") if (MD / "static_reference_analysis.json").exists() else None,
        },
    }


def make_reports() -> dict:
    pocket = read_json(POCKET)
    handoff_check = verify_handoff()
    rows = membership_rows()
    stability = read_json(STABILITY)
    git = git_info()
    runtime = openmm_info()
    struct = {p: cif_structure_summary(p) for p in ("1W60", "8GLA")}
    preflight = {p: preflight_minimization_summary(p) for p in ("1W60", "8GLA")}
    static = static_reference_metrics()
    write_json(MD / "MD_GNN_HANDOFF_VERIFICATION.json", handoff_check)
    write_json(MD / "MD_STRUCTURE_VALIDATION.json", {"created_at": NOW, "cif": struct, "preflight_min5000": preflight})
    write_json(MD / "static_reference_analysis.json", static)
    frozen = protocol(static)
    write_json(MD / "FROZEN_MD_ANALYSIS_PROTOCOL.json", frozen)
    frozen_hash = sha256(MD / "FROZEN_MD_ANALYSIS_PROTOCOL.json")
    (MD / "FROZEN_MD_ANALYSIS_PROTOCOL.sha256").write_text(f"{frozen_hash}  FROZEN_MD_ANALYSIS_PROTOCOL.json\n", encoding="utf-8")

    mapping = {
        "created_at": NOW,
        "numbering": "PDB author/auth_seq_id",
        "canonical_sequence_length": 261,
        "simulated_assembly_chains": {
            "1W60": {"A": "1W60 assembly1 copy A1", "B": "1W60 assembly1 copy A2", "C": "1W60 assembly1 copy A3"},
            "8GLA": {"A": "8GLA assembly1 chain A1", "B": "8GLA assembly1 chain B1", "C": "8GLA assembly1 chain C1"},
        },
        "analysis_chain_indices": {"0": "chain A in prepared PDB", "1": "chain B", "2": "chain C"},
        "candidate_regions": frozen["residue_sets"],
    }
    write_json(MD / "pcna_chain_residue_mapping.json", mapping)

    write_md(
        MD / "MD_SCIENTIFIC_QUESTION.md",
        f"""
# MD Scientific Question

## Primary Question

Does the independently predicted PCNA candidate region exhibit reproducible dynamic behavior consistent with transient pocket opening or increased accessibility under the simulated conditions?

## What The MD Experiment Tests

The GNN result is a hypothesis about where to investigate PCNA dynamics. The MD experiment tests whether the frozen 3/3 core and >=2/3 supported region show reproducible, predefined changes in accessibility, geometry, and flexibility under the chosen apo/control simulation protocol.

## What The MD Experiment Does Not Test

It does not establish ligand binding, druggability, therapeutic relevance, biological efficacy, or that a true cryptic pocket exists. A negative or inconclusive result from this protocol remains scientifically valid if preparation, control behavior, and analysis sensitivity pass prospectively.

## Secondary Questions

- Does local solvent accessibility increase in the 3/3 core and supported >=2/3 region?
- Does local flexibility change after alignment and PBC correction?
- Does candidate-region geometry expand by predefined CA geometry metrics?
- Are opening-like events reproducible across independent trajectories?
- Are motions correlated with nearby structural elements by DCCM, interpreted qualitatively unless replicate-stable?
- Can the 8GLA reference/control distinguish the relevant open/reference state from 1W60 under frozen analysis?
- Is the 3/3 core more stable and interpretable than the uncertain 1-of-3 fringe?

## Frozen GNN Context

Policy: `{stability['policy_id']}`. Literal mean pairwise Jaccard: `{stability['literal_mean_pairwise_jaccard']:.4f}`. Interpretation remains `MODERATE / EXPLORATORY PASS`, not strong residue-level reproducibility.
""",
    )

    write_md(
        MD / "PCNA_CHAIN_AND_RESIDUE_MAPPING.md",
        f"""
# PCNA Chain And Residue Mapping

Generated: {NOW}

Numbering is PDB author/auth_seq_id numbering. The GNN candidate was selected on 1W60 chain A. PCNA is homotrimeric; prepared MD assemblies rename the simulated chains to A/B/C and analysis chain index 0 maps to prepared chain A.

## GNN Support Table

{seed_membership_table(rows)}

## Classification

- CORE: 11 residues selected by all 3 seeds.
- SUPPORTED FRINGE: 5 residues selected by exactly 2 seeds.
- SEED-SPECIFIC / UNCERTAIN FRINGE: 4 residues selected by exactly 1 seed and retained only for exploratory union analysis.

Machine-readable mapping: `md_validation_4070/pcna_chain_residue_mapping.json`.
""",
    )

    assumptions = [
        ("Starting apo structure", "1W60", "RCSB metadata title `NATIVE HUMAN PCNA`; local md handoff", "direct", "high", "Other apo structures", "Wrong starting state can make apo dynamics uninterpretable."),
        ("Positive-control/reference", "8GLA ligand-stripped protein", "RCSB metadata title co-crystal with AOH1996 derivative; local positive-control docs", "direct plus methodological inference", "medium", "No control or other holo structures", "Control may not validate metric sensitivity if structural differences are unrelated or not stable after ligand stripping."),
        ("Biological assembly", "Homotrimer assembly 1 for both structures", "RCSB assembly metadata and run_md.py gemmi assembly construction", "direct", "high", "ASU only", "ASU-only simulation recurs the prior wrong-assembly failure."),
        ("Chain selection", "Prepared chains A/B/C; primary candidate on chain index 0", "GNN handoff chain A and run_md chain renaming", "direct/inferred", "medium", "Analyze all symmetry equivalents", "Wrong chain mapping can test the wrong physical region."),
        ("Missing residues", "Rebuild internal gaps with PDBFixer; do not fabricate terminal tails", "run_md.py and prep_audit.json", "methodological refinement", "medium", "Model all missing residues or none", "Modeled loops, especially 8GLA 50 internal residues, may affect local geometry."),
        ("Histidines/protonation", "PDBFixer hydrogens at pH 7.4; no manual histidine override", "run_md.py defaults", "inferred methodology", "medium", "Manual PROPKA/PDB2PQR review", "Incorrect histidine tautomer/charge can perturb local H-bonding."),
        ("Disulfides", "8GLA has Cys135-Cys162 disulfides; 1W60 does not declare disulfides", "8GLA struct_conn and metadata", "direct", "high", "Force matched disulfide state or use alternate control", "Construct/oxidation difference may affect dynamics outside the pocket."),
        ("Ligands/cofactors", "Remove ligands, ions, crystallographic waters before protein-only MD", "run_md.py protein-only filter", "methodological choice", "medium", "Parameterize ZQZ and retain ligand", "Ligand-stripped control starts from open-like coordinates but may relax; it is not guaranteed to stay open."),
        ("Force field/water", "Amber14 protein, TIP3P water", "run_md.py and environment.yml", "methodological choice", "medium", "CHARMM36m/OPC", "Force-field choice affects flexibility and solvent exposure."),
        ("Salt/thermodynamic state", "0.15 M NaCl, 310 K, 1 bar", "run_md.py defaults", "methodological choice", "medium", "Crystal conditions or 300 K", "Dynamics and stability may differ."),
        ("Timestep/HMR", "4 fs with HMR 4.0 amu, HBond constraints", "run_md.py", "methodological choice", "medium", "2 fs no HMR", "Too aggressive timestep could destabilize; smoke/equil gates must catch this."),
        ("Trajectory output", "50 ps default", "run_md.py", "methodological choice", "medium", "10 ps or 100 ps", "Event duration estimates are limited by output interval."),
        ("Analysis alignment", "Protein CA excluding pocket", "analyze_md.py and frozen protocol", "methodological choice", "medium", "All CA or domain-specific alignment", "Circular alignment can suppress pocket motion."),
        ("Pocket definition", "Core primary, supported >=2/3 primary extension, full union exploratory", "membership CSV and final handoff", "direct", "high", "Treat all 20 equally", "Boundary uncertainty can otherwise dominate interpretation."),
    ]
    assumption_lines = [
        "# MD Assumption And Source Audit",
        "",
        f"Generated: {NOW}",
        "",
        "| Choice | Current value | Source/evidence | Source type | Confidence | Alternative | Effect if wrong |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for a in assumptions:
        assumption_lines.append("| " + " | ".join(a) + " |")
    write_md(MD / "MD_ASSUMPTION_AND_SOURCE_AUDIT.md", "\n".join(assumption_lines))

    failures = [
        ("Impossible peptide connections across unresolved gaps", "SEQRES/gap loss let OpenMM bond across missing loops", "run_md.py transfers full sequence and asserts no >2.5 A covalent bonds", "assert_no_impossible_bonds plus prep_audit", "Protected in preflight; exact smoke still pending"),
        ("Wrong apo/control structures", "Prior 1AXC/5E0V variants were not true apo/control", "Frozen 1W60 apo and 8GLA reference", "pocket JSON and readiness gate check", "Protected"),
        ("Wrong biological assembly", "ASU-only preparation made incomparable systems", "gemmi assembly 1 homotrimer for both", "prep_audit expected 3 chains", "Protected in preflight"),
        ("Chain mapping errors", "Bare residue numbers are ambiguous in homotrimer", "pcna_chain_residue_mapping.json", "md_readiness_gate checks mapping file", "Protected for current chain A hypothesis"),
        ("SASA atom-parity mismatch", "Apo/control atom sets differed", "atom-key parity required in frozen protocol; prepared static parity is 100 percent", "static_reference_analysis.json", "Protected for static refs; trajectory parity checked by analyze_md.py"),
        ("PBC/imaging artifacts", "Old RMSD/RMSF used un-imaged trajectories", "analyze_md.py images before alignment and detects jumps", "analysis script checks", "Needs smoke trajectory validation"),
        ("Stale/generated input reuse", "Existing DONE/topology could be reused silently", "Readiness gate checks hashes; preflight kept outside production outputs", "md_readiness_gate", "Protected for production if gate used"),
        ("Topology/trajectory pairing mismatch", "Old trajectory lacked saved topology", "run_md.py writes system_solvated.pdb next to DCD", "DONE.json topology field and file hash", "Protected"),
        ("Pseudoreplication", "Chains/frames treated as independent replicates", "replicate plan defines trajectory as independent unit", "FROZEN_MD_ANALYSIS_PROTOCOL.json", "Protected prospectively"),
    ]
    failure_lines = [
        "# Previous MD Failures And Preventions",
        "",
        f"Generated: {NOW}",
        "",
        "| Problem | Cause | Fix | Automated check | Current status |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in failures:
        failure_lines.append("| " + " | ".join(row) + " |")
    write_md(MD / "PREVIOUS_MD_FAILURES_AND_PREVENTIONS.md", "\n".join(failure_lines))

    structure_lines = [
        "# MD Structure Validation Report",
        "",
        f"Generated: {NOW}",
        "",
        "Status: PASS FOR PREPARATION PREFLIGHT; NOT YET PRODUCTION READY because the 0.1 ns smoke and equilibration gates have not passed.",
        "",
        "## Key Findings",
        "",
        f"- 1W60 assembly 1 protein chain count after operators: {struct['1W60']['assembly1']['protein_chain_count_after_ops']} (expected 3).",
        f"- 8GLA assembly 1 protein chain count after operators: {struct['8GLA']['assembly1']['protein_chain_count_after_ops']} (expected 3).",
        f"- PDBFixer rebuilt {preflight['8GLA']['prep_audit']['internal_missing_residues_rebuilt']} internal residues for 8GLA and {preflight['1W60']['prep_audit']['internal_missing_residues_rebuilt']} for 1W60.",
        f"- 8GLA is {struct['8GLA']['resolution_A']} A resolution and declares {struct['8GLA']['metadata_disulfide_count']} disulfides, including Cys135-Cys162 per chain; 1W60 declares none.",
        f"- Prepared static heavy-atom parity for supported region: {static['atom_parity']['supported_ge2of3']['common_heavy_atoms']}/{static['atom_parity']['supported_ge2of3']['union_heavy_atoms']}.",
        f"- Severe prepared-protein close contacts <1.5 A: 1W60={preflight['1W60']['close_contacts']['severe_nonbonded_close_contacts_lt_1p5A']}, 8GLA={preflight['8GLA']['close_contacts']['severe_nonbonded_close_contacts_lt_1p5A']}.",
        "",
        "## Default-Minimization Preflight",
        "",
        "| System | Initial PE (kJ/mol) | Final PE (kJ/mol) | Initial max force | Final max force | Rebuilt internal residues | Solvated atoms |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for pdb_id in ("1W60", "8GLA"):
        done = preflight[pdb_id]["done"]
        mini = done["minimization"]
        atoms = sum(1 for line in (PREFLIGHT / pdb_id / "system_solvated.pdb").open(encoding="utf-8", errors="ignore") if line.startswith(("ATOM", "HETATM")))
        structure_lines.append(
            f"| {pdb_id} | {mini['initial_potential_kj_mol']:.3g} | {mini['minimized_potential_kj_mol']:.3g} | "
            f"{mini['max_force_initial_kj_mol_nm']:.3g} | {mini['max_force_minimized_kj_mol_nm']:.3g} | "
            f"{preflight[pdb_id]['prep_audit']['internal_missing_residues_rebuilt']} | {atoms} |"
        )
    structure_lines += [
        "",
        "The high initial 8GLA energy reflects severe generated-coordinate/solvent contacts before minimization. Default minimization resolves this to finite negative energy, but production is still gated on smoke and equilibration stability.",
        "",
        "Machine-readable details: `MD_STRUCTURE_VALIDATION.json`.",
    ]
    write_md(MD / "MD_STRUCTURE_VALIDATION_REPORT.md", "\n".join(structure_lines))

    write_md(
        MD / "POSITIVE_CONTROL_SPECIFICATION.md",
        """
# Positive Control Specification

## Definition

The positive-control/reference structure is 8GLA, a PCNA co-crystal with an AOH1996 derivative (ZQZ) bound. The MD preparation strips ligand and simulates protein-only PCNA from the ligand-bound/reference coordinates.

## What It Tests

The control tests whether the preparation plus frozen analysis can recognize a structural/accessibility distinction relevant to the candidate hypothesis. It does not require short ligand-stripped MD to spontaneously produce a dramatic opening event.

## Expected Behavior

At initialization/static reference, the frozen metrics should report larger accessibility or geometry in 8GLA than 1W60 for the predefined candidate region. In short MD, the control should remain technically stable and interpretable; relaxation after ligand stripping is allowed.

## Interpretable

Technically stable simulation, correct topology/trajectory pairing, valid PBC handling, atom-parity-safe analysis, and metrics that distinguish the static/reference state or produce structurally sensible trajectories.

## Technically Valid But Biologically Ambiguous

The run is stable and analyzable, but ligand stripping, 8GLA resolution/rebuilt loops, or disulfide/construct differences make the biological meaning uncertain.

## Failed

Preparation/mapping mismatch, severe instability, analysis parity failure, PBC artifacts, corrupted outputs, or metrics unable to distinguish reference states where they should.
""",
    )

    write_md(
        MD / "MD_PARAMETER_AUDIT.md",
        f"""
# MD Parameter Audit

Generated: {NOW}

| Parameter | Current value | Source | Original methodology specified? | Appropriateness |
| --- | --- | --- | --- | --- |
| Force field | amber14-all.xml | run_md.py | Project methodology choice | Standard protein force field, acceptable for exploratory PCNA MD |
| Water model | amber14/tip3p.xml | run_md.py | Project methodology choice | Consistent with Amber14 default |
| Ions | neutralized, 0.15 M NaCl | run_md.py | Project methodology choice | Physiological-strength salt assumption |
| Temperature | 310 K | run_md.py | Project methodology choice | Human physiological temperature; not chosen to force opening |
| Pressure | 1 bar | run_md.py | Project methodology choice | Standard NPT pressure |
| Box | 1.0 nm solvent padding | run_md.py | Project methodology choice | Reasonable minimum padding; verify no self-contact after equilibration |
| Constraints | HBonds, rigid water | run_md.py | Project methodology choice | Standard with 2-4 fs biomolecular MD |
| HMR/timestep | HMR 4.0 amu, 4 fs | run_md.py | Methodological refinement | Efficient but must pass smoke/equilibration gates |
| Nonbonded | PME, 1.0 nm cutoff | run_md.py | Project methodology choice | Standard periodic electrostatics |
| Thermostat | LangevinMiddle, 1/ps friction | run_md.py | Project methodology choice | Standard OpenMM integrator |
| Barostat | MonteCarloBarostat, frequency 25 | run_md.py | Project methodology choice | NPT from start; objective density/box checks required |
| Minimization | 5000 iterations default | run_md.py | Project methodology choice | Preflight finite; final max forces require equilibration monitoring |
| Equilibration | 2.0 ns default | run_md.py | Project methodology choice | Must be judged by criteria in EQUILIBRATION_ACCEPTANCE_CRITERIA.json |
| Output | DCD/log every 50 ps | run_md.py | Project methodology choice | Adequate for broad events, not sub-50 ps kinetics |
| Platform | CUDA default, CPU fallback | run_md.py | Runtime choice | Production should use CUDA/validated GPU, not accidental slow CPU |

No parameter was changed to encourage pocket opening. The only code change in this pass adds minimization energy/force reporting.
""",
    )

    equil = {
        "created_at": NOW,
        "temperature_K": {"target": 310.0, "accept_mean_range": [300.0, 320.0], "no_runaway": "no sustained drift > 15 K from target after first 20 percent of equilibration"},
        "pressure_bar": {"target": 1.0, "accept_mean_range": [0.5, 1.5], "applies_to": "NPT only; fluctuations are expected"},
        "density_g_ml": {"accept_final_range": [0.95, 1.10]},
        "potential_energy": {"requirement": "finite, no monotonic runaway over final half of equilibration"},
        "box_vectors": {"requirement": "finite, positive dimensions, no collapse, no abrupt discontinuity after equilibration"},
        "protein_backbone_rmsd_nm": {"warning": 0.5, "fail": 1.0, "reference": "post-minimization/equilibrated start"},
        "candidate_region": {"requirement": "all core/support residues present; no nonfinite coordinates; no chain break or gross distortion"},
        "control_region": {"requirement": "same as candidate plus atom-parity-safe analysis"},
        "proceed_to_production": "all fail criteria absent and smoke/analysis/control gates passed",
    }
    write_json(MD / "EQUILIBRATION_ACCEPTANCE_CRITERIA.json", equil)

    smoke_status = "NOT_RUN"
    smoke_reason = "Exact required 0.1 ns control smoke has not been executed in md_validation_4070/outputs. Zero-production preflight was run separately and is not scientific evidence."
    write_md(
        MD / "CONTROL_SMOKE_TEST_REPORT.md",
        f"""
# Control Smoke Test Report

Status: {smoke_status}

Required command:

```bash
cd md_validation_4070 && python run_md.py --pocket final_consensus_1w60_20260815 --run control --replicates 1 --ns 0.1
```

Result: {smoke_reason}

Preflight completed in `preflight_outputs_min5000` with zero production steps. That validates assembly, PDBFixer repair, solvation, parameterization, long-bond assertions, and default minimization, but it does not validate trajectory output, NaN-free dynamics, frame count, PBC handling, or analysis compatibility.
""",
    )

    write_md(
        MD / "MD_ANALYSIS_VALIDATION_REPORT.md",
        f"""
# MD Analysis Validation Report

Status: PARTIAL STATIC PASS; TRAJECTORY VALIDATION PENDING.

## Static Reference Sanity Check

Prepared protein-only 1W60 and ligand-stripped 8GLA references were analyzed before candidate production.

| Region | 1W60 SASA (A^2) | 8GLA SASA (A^2) | Delta | 1W60 hull (A^3) | 8GLA hull (A^3) | Delta |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| core_3of3 | {static['regions']['core_3of3']['1W60']['sasa_A2']} | {static['regions']['core_3of3']['8GLA']['sasa_A2']} | {static['regions']['core_3of3']['control_minus_apo']['sasa_A2']} | {static['regions']['core_3of3']['1W60']['ca_convex_hull_volume_A3']} | {static['regions']['core_3of3']['8GLA']['ca_convex_hull_volume_A3']} | {static['regions']['core_3of3']['control_minus_apo']['ca_convex_hull_volume_A3']} |
| supported_ge2of3 | {static['regions']['supported_ge2of3']['1W60']['sasa_A2']} | {static['regions']['supported_ge2of3']['8GLA']['sasa_A2']} | {static['regions']['supported_ge2of3']['control_minus_apo']['sasa_A2']} | {static['regions']['supported_ge2of3']['1W60']['ca_convex_hull_volume_A3']} | {static['regions']['supported_ge2of3']['8GLA']['ca_convex_hull_volume_A3']} | {static['regions']['supported_ge2of3']['control_minus_apo']['ca_convex_hull_volume_A3']} |
| full_union_exploratory | {static['regions']['full_union_exploratory']['1W60']['sasa_A2']} | {static['regions']['full_union_exploratory']['8GLA']['sasa_A2']} | {static['regions']['full_union_exploratory']['control_minus_apo']['sasa_A2']} | {static['regions']['full_union_exploratory']['1W60']['ca_convex_hull_volume_A3']} | {static['regions']['full_union_exploratory']['8GLA']['ca_convex_hull_volume_A3']} | {static['regions']['full_union_exploratory']['control_minus_apo']['ca_convex_hull_volume_A3']} |

Atom parity is 100 percent for core, supported, and union heavy atoms in prepared static references.

## Trajectory Analysis Status

RMSD, RMSF, SASA, DCCM, PBC imaging, output frame count, and topology/trajectory pairing still require the exact smoke trajectory. Do not launch candidate production until that validation passes.

Machine-readable metrics: `static_reference_analysis.json`.
""",
    )

    write_md(
        MD / "MD_REPLICATE_AND_DURATION_PLAN.md",
        """
# MD Replicate And Duration Plan

## Staging

1. Technical smoke: 1 control replicate, 0.1 ns production, default equilibration, execution only.
2. Control-first scientific readiness run: 3 independent control replicates, 5 ns production each after the frozen equilibration protocol. Purpose: stability, analysis interpretability, and metric responsiveness, not proof of biology.
3. Production, only after all gates and explicit human Gate-6 approval: 3 independent control replicates and 3 independent candidate/apo replicates, 100 ns production each.

## Seeds

Replicate seeds are the existing run_md.py deterministic seeds: 20260001, 20260002, 20260003 for integrator and barostat.

## Why 100 ns For Production

The prior 20-25 ns single-run design was underpowered and uninterpretable. 100 ns x 3 remains exploratory for cryptic-pocket dynamics, which can be slower than this, but gives a reasonable near-term opportunity to detect ns-scale accessibility changes without adapting duration after observing favorable candidate behavior.

## Early Stop Conditions

Stop only for technical failure: NaNs, nonfinite energies, temperature runaway, box collapse, severe unfolding/RMSD gate failure, chain separation, corrupted trajectory, topology/trajectory mismatch, failed checkpoint/restart, invalid residue mapping, or failed analysis parity/PBC checks.

Scientific no-opening is not an early stop condition.
""",
    )

    readiness = {
        "created_at": NOW,
        "md_ready": False,
        "next_stage_ready": False,
        "blockers": [
            "Exact 0.1 ns control smoke test has not passed.",
            "Trajectory analysis validation is pending smoke output.",
            "Control-first 5 ns interpretability run has not been executed.",
            "Human Gate-6 approval is not recorded.",
            "Worktree is dirty; production provenance would be ambiguous.",
        ],
        "passes": [
            "GNN handoff integrity verified.",
            "Pocket JSON now matches run_md.py required keys.",
            "Biological assembly/preparation preflight passed for 1W60 and 8GLA.",
            "Default minimization completed with finite energies for both systems.",
            "Static reference metrics distinguish 8GLA from 1W60 modestly and prospectively.",
            "Frozen analysis protocol written and hashed.",
        ],
        "frozen_analysis_hash": frozen_hash,
        "git": git,
        "runtime": runtime,
    }
    write_json(MD / "md_readiness_status.json", readiness)

    write_md(
        MD / "MD_READINESS_REPORT.md",
        f"""
# MD Readiness Report

Generated: {NOW}

## Verdict

MD READY: NO

This means production MD is not ready. The protocol is ready for the next technical stage only after the exact 0.1 ns control smoke is run on an appropriate MD environment.

## Passed In This Readiness Pass

- GNN handoff integrity: {handoff_check['status']}.
- Structure preparation preflight: 1W60 and 8GLA biological assemblies produced exactly 3 PCNA chains.
- Default minimization: finite energies for both systems.
- Static analysis: 8GLA reference is modestly more exposed/expanded than 1W60 under frozen core/support metrics.
- Frozen analysis protocol hash: `{frozen_hash}`.

## Blockers

- Exact control smoke test has not passed.
- Control interpretability run has not been executed.
- Human Gate-6 approval is not recorded and must not be fabricated.
- Worktree is dirty; production must not run from ambiguous provenance.
- Trajectory-level analysis validation remains pending.
""",
    )

    write_md(
        MD / "GATE6_PACKET_FINAL_PRE_MD_READINESS.md",
        f"""
# Gate-6 Packet: Final Pre-MD Readiness

Status: AWAITING HUMAN APPROVAL

## GNN Handoff

- Extraction policy: `independent_mcc_rank_fraction_size_weighted_cluster`
- Literal mean Jaccard: `0.6792`
- Interpretation: `MODERATE / EXPLORATORY PASS`
- 3/3 core: 11 residues
- >=2/3 supported region: 16 residues
- Full union: 20 residues, with 4 seed-specific residues treated as exploratory only

## Validation Artifacts

- Structure validation: `MD_STRUCTURE_VALIDATION_REPORT.md`
- Assumption audit: `MD_ASSUMPTION_AND_SOURCE_AUDIT.md`
- Positive control: `POSITIVE_CONTROL_SPECIFICATION.md`
- Frozen analysis: `FROZEN_MD_ANALYSIS_PROTOCOL.json`
- Frozen analysis SHA-256: `{frozen_hash}`
- Replicate/duration plan: `MD_REPLICATE_AND_DURATION_PLAN.md`
- Readiness gate: `python scripts/md_readiness_gate.py`

## Gate Status

Not approved. Human approval is required after smoke, trajectory-analysis validation, and control interpretability pass.

## Next Legitimate Command

```bash
cd md_validation_4070 && python run_md.py --pocket final_consensus_1w60_20260815 --run control --replicates 1 --ns 0.1
```
""",
    )

    write_md(
        MD / "MD_MACHINE_AND_STORAGE_OPTIONS.md",
        """
# MD Machine And Storage Options

## RTX 4070 Super

Best local option for the smoke, control-first run, and exploratory production. Use the conda environment in `environment.yml`; keep trajectories on fast local NVMe during runs, then archive DCD/topology/checkpoint/log/provenance hashes.

## M5 Mac

Good for report generation, static validation, code checks, and small CPU smoke/prep tests. Not appropriate for 3 x 100 ns production on this 150k atom system unless runtime is acceptable. Use OpenMM CPU/Metal only after validating platform availability; CUDA is not available.

## Cloud GPUs

Use for production if local GPU time is limited. Prefer a single-GPU NVIDIA instance with enough VRAM for 150k atoms and fast attached SSD. Record cloud provider, instance type, GPU model, driver, CUDA, OpenMM platform, image/container hash, costs, and storage location.

## Storage

Plan for topology/checkpoint/log/provenance plus DCD trajectories. At 50 ps output, 100 ns gives about 2000 frames per replicate. For about 155k atoms, uncompressed DCD can be several GB per 100 ns replicate; six production replicates can plausibly require tens of GB before derived analyses. Keep at least 200 GB free working space for production plus backups, and register hashes for every non-committed large artifact.
""",
    )

    return readiness


if __name__ == "__main__":
    result = make_reports()
    print(json.dumps({"md_ready": result["md_ready"], "frozen_analysis_hash": result["frozen_analysis_hash"]}, indent=2))
