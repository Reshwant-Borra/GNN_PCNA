#!/usr/bin/env python
"""Prepare 1AXC apo-from-p21 PCNA trimer inputs for Phase 5 short MD.

This script does not run dynamics. It downloads or reads 1AXC, keeps the PCNA
trimer chains, removes p21 peptide chains, adds standard missing atoms and
hydrogens, and writes a structure audit.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def _import_dependencies():
    try:
        from openmm.app import PDBFile
        from pdbfixer import PDBFixer
    except Exception as exc:  # pragma: no cover - environment-specific
        raise SystemExit(
            "Missing OpenMM/PDBFixer dependencies. Create the conda environment with "
            "`conda env create -f envs/phase5_md_runpod.yml` and activate it."
        ) from exc
    return PDBFile, PDBFixer


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prepare 1AXC apo-from-p21 PCNA trimer structure for OpenMM."
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("outputs/phase5_md/time_crunch_1axc_25ns"),
        help="Run output root.",
    )
    parser.add_argument(
        "--input-pdb",
        type=Path,
        default=None,
        help="Optional local 1AXC PDB file. If omitted, PDBFixer downloads 1AXC.",
    )
    parser.add_argument(
        "--pcna-chains",
        nargs="+",
        default=["A", "C", "E"],
        help="PCNA trimer chain IDs to retain from 1AXC. Default: A C E.",
    )
    parser.add_argument(
        "--ph",
        type=float,
        default=7.4,
        help="pH used for hydrogen placement. Default: 7.4.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned preparation actions without writing files.",
    )
    return parser.parse_args()


def _chain_summary(topology) -> list[dict[str, object]]:
    summary: list[dict[str, object]] = []
    for chain in topology.chains():
        residues = list(chain.residues())
        summary.append(
            {
                "chain_id": chain.id,
                "n_residues": len(residues),
                "first_residue": str(residues[0]) if residues else None,
                "last_residue": str(residues[-1]) if residues else None,
            }
        )
    return summary


def main() -> None:
    args = parse_args()

    out_dir = args.output_root / "inputs"
    prepared_pdb = out_dir / "1axc_pcna_apo_from_p21_prepared.pdb"
    audit_json = out_dir / "1axc_pcna_apo_from_p21_structure_audit.json"

    if args.dry_run:
        print("DRY RUN: would prepare 1AXC apo-from-p21 PCNA trimer")
        print(f"  output_root: {args.output_root}")
        print(f"  retain PCNA chains: {', '.join(args.pcna_chains)}")
        print(f"  pH: {args.ph}")
        print(f"  prepared PDB: {prepared_pdb}")
        return

    PDBFile, PDBFixer = _import_dependencies()

    if args.input_pdb:
        fixer = PDBFixer(filename=str(args.input_pdb))
        structure_source = str(args.input_pdb)
    else:
        fixer = PDBFixer(pdbid="1AXC")
        structure_source = "PDB:1AXC via PDBFixer"

    original_chains = _chain_summary(fixer.topology)
    keep = set(args.pcna_chains)
    remove_indices: list[int] = []
    for idx, chain in enumerate(fixer.topology.chains()):
        if chain.id not in keep:
            remove_indices.append(idx)
    fixer.removeChains(remove_indices)

    retained_chains = _chain_summary(fixer.topology)
    retained_ids = {chain["chain_id"] for chain in retained_chains}
    missing = keep - retained_ids
    if missing:
        raise SystemExit(f"Requested PCNA chains not found after filtering: {sorted(missing)}")

    fixer.findMissingResidues()
    missing_residues = {
        f"{chain_idx}:{res_idx}": [str(res) for res in residues]
        for (chain_idx, res_idx), residues in fixer.missingResidues.items()
    }
    fixer.findNonstandardResidues()
    nonstandard = [str(item) for item in fixer.nonstandardResidues]
    fixer.replaceNonstandardResidues()
    fixer.findMissingAtoms()
    missing_atoms = {
        str(residue): [atom.name for atom in atoms]
        for residue, atoms in fixer.missingAtoms.items()
    }
    missing_terminals = {
        str(residue): [atom.name for atom in atoms]
        for residue, atoms in fixer.missingTerminals.items()
    }
    fixer.addMissingAtoms()
    fixer.addMissingHydrogens(args.ph)

    out_dir.mkdir(parents=True, exist_ok=True)
    with prepared_pdb.open("w", encoding="utf-8") as handle:
        PDBFile.writeFile(fixer.topology, fixer.positions, handle, keepIds=True)

    audit = {
        "status": "prepared_structure_only_no_md",
        "structure_source": structure_source,
        "prepared_pdb": str(prepared_pdb),
        "retained_pcna_chains": args.pcna_chains,
        "removed_chains_policy": "remove all chains not listed in --pcna-chains; default removes p21 peptide chains B/D/F from 1AXC",
        "ph": args.ph,
        "original_chains": original_chains,
        "retained_chains": retained_chains,
        "missing_residues_before_atom_addition": missing_residues,
        "nonstandard_residues": nonstandard,
        "missing_atoms_before_addition": missing_atoms,
        "missing_terminals_before_addition": missing_terminals,
        "governance": [
            "docs/scientific_governance/12_PCNA_SPECIFIC_CHECKS.md",
            "docs/scientific_governance/13_MD_VALIDATION_RULES.md",
            "docs/scientific_governance/15_PROVENANCE_AND_REPRODUCIBILITY.md",
        ],
        "claim_scope": "Structure preparation only. No MD result or scientific claim.",
    }
    audit_json.write_text(json.dumps(audit, indent=2), encoding="utf-8")

    print(f"Prepared PDB: {prepared_pdb}")
    print(f"Structure audit: {audit_json}")


if __name__ == "__main__":
    main()
