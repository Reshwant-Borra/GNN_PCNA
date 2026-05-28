#!/usr/bin/env python3
"""Reproducible structural derivation of PCNA interface contact residues (Track 4 support).

Derives the residue lists used in `data/registries/pcna_interface_map.json` for regions
that are taken directly from deposited coordinates rather than from a text citation:

  - trimer_interface     : inter-subunit heavy-atom contacts among the PCNA trimer chains
                           A/C/E of PDB 1AXC.
  - aoh1996_contact_region: PCNA heavy-atom contacts within the cutoff of the AOH1996
                           derivative ligand ZQZ in PDB 8GLA.
  - pip_box_structural_contacts: PCNA heavy-atom contacts to the p21 PIP-box peptide
                           (chains B/D/F) of PDB 1AXC -- recorded as supporting evidence;
                           the canonical PIP-box pocket residues in the map come from the
                           literature (Mueller et al. 2019, PMID 31134302).

Method: heavy-atom (non-hydrogen) distance <= 4.5 Angstrom. Residue numbers are PDB author
numbers, which for these human PCNA entries follow canonical UniProt P12004 numbering
(verified: PCNA chains span residues 1-255 of the 261-aa sequence).

The PDB files live only inside the local crawl zip and are NOT committed. This script
fail-closes (clear message, no crash) when the zip is absent. It only reads coordinates
and writes a small provenance JSON; it does not train, evaluate, or make claims.

Governance: docs/scientific_governance/12_PCNA_SPECIFIC_CHECKS.md,
            docs/scientific_governance/15_PROVENANCE_AND_REPRODUCIBILITY.md
"""

from __future__ import annotations

import json
import zipfile
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = ROOT / "data" / "registries" / "pcna_interface_contacts_derived.json"
ZIP_PATH = Path("C:/Users/advay/GNN_PNCA_crawled_data.zip")
CONTACT_CUTOFF_A = 4.5


def parse_pdb(zf: zipfile.ZipFile, pdb_id: str) -> list[tuple]:
    raw = zf.read(f"data/raw/{pdb_id}.pdb").decode("utf-8", "replace")
    atoms: list[tuple] = []
    for line in raw.splitlines():
        if line.startswith(("ATOM", "HETATM")):
            element = line[76:78].strip()
            atom_name = line[12:16].strip()
            # Skip hydrogens (element column, or leading H in atom name).
            if element == "H" or (not element and atom_name[:1] == "H"):
                continue
            try:
                xyz = np.array(
                    [float(line[30:38]), float(line[38:46]), float(line[46:54])]
                )
            except ValueError:
                continue
            atoms.append(
                (line[:6].strip(), line[21], int(line[22:26]), line[17:20].strip(), xyz)
            )
    return atoms


def contact_residues(atoms, sel_target, sel_partner) -> list[int]:
    partner = np.array([a[4] for a in atoms if sel_partner(a)])
    if partner.size == 0:
        return []
    hits: set[int] = set()
    for record, chain, resseq, resname, xyz in atoms:
        if sel_target((record, chain, resseq, resname, xyz)):
            if (np.linalg.norm(partner - xyz, axis=1) <= CONTACT_CUTOFF_A).any():
                hits.add(resseq)
    return sorted(hits)


def main() -> None:
    out: dict = {
        "schema_version": "1.0",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "generator": "scripts/derive_pcna_interface_contacts.py",
        "method": f"heavy-atom distance <= {CONTACT_CUTOFF_A} A",
        "numbering": "PDB author numbering == canonical UniProt P12004 (1-261)",
    }

    if not ZIP_PATH.exists():
        out["status"] = "SKIPPED_ZIP_ABSENT"
        out["note"] = "Local crawl zip not present; re-run on the machine holding it."
        OUTPUT_PATH.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
        print("Zip absent -> wrote SKIPPED contacts manifest.")
        return

    with zipfile.ZipFile(ZIP_PATH) as zf:
        axc = parse_pdb(zf, "1AXC")
        gla = parse_pdb(zf, "8GLA")

    pcna_chains_1axc = {"A", "C", "E"}
    pep_chains_1axc = {"B", "D", "F"}

    # PIP-box structural contacts (PCNA <-> p21 peptide).
    pip_contacts = contact_residues(
        axc,
        lambda a: a[0] == "ATOM" and a[1] in pcna_chains_1axc,
        lambda a: a[0] == "ATOM" and a[1] in pep_chains_1axc,
    )

    # Trimer interface (PCNA subunit <-> other PCNA subunits).
    trimer: set[int] = set()
    for chain in pcna_chains_1axc:
        others = pcna_chains_1axc - {chain}
        trimer.update(
            contact_residues(
                axc,
                lambda a, c=chain: a[0] == "ATOM" and a[1] == c,
                lambda a, o=others: a[0] == "ATOM" and a[1] in o,
            )
        )

    # AOH1996 derivative (ZQZ) contacts in 8GLA.
    zqz = contact_residues(
        gla,
        lambda a: a[0] == "ATOM",
        lambda a: a[0] == "HETATM" and a[3] == "ZQZ",
    )

    out.update(
        {
            "status": "DERIVED",
            "pip_box_structural_contacts": {
                "source_pdb": "1AXC",
                "partner": "p21 C-terminal PIP-box peptide (chains B/D/F, p21 res 143-160)",
                "residues": pip_contacts,
            },
            "trimer_interface": {
                "source_pdb": "1AXC",
                "description": "inter-subunit contacts among PCNA trimer chains A/C/E",
                "residues": sorted(trimer),
            },
            "aoh1996_contact_region": {
                "source_pdb": "8GLA",
                "ligand": "ZQZ (AOH1996 derivative, AOH1996-1LE)",
                "residues": zqz,
            },
        }
    )
    OUTPUT_PATH.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print("PIP-box structural contacts:", pip_contacts)
    print("Trimer interface:", sorted(trimer))
    print("ZQZ contacts:", zqz)
    print(f"Wrote {OUTPUT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
