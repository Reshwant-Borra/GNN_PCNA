#!/usr/bin/env python
"""
Convert a pocket_handoff.json (from the GNN pocket search) into a pockets/<name>.json that the
MD-validation harness consumes. This is the glue that lets the pocket-search stage flow straight
into the MD stage without a manual hand-off round-trip.

It carries the (chain, resid) pairs through, sets the apo/control structures from the handoff, and
copies the provenance + honesty caveats so the MD pocket file stays traceable to the GNN run.

Usage:
  python handoff_to_pocket.py --handoff cand_A_2026-07_handoff.json \
      --out ../pockets/cand_A_2026-07.json
"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main():
    ap = argparse.ArgumentParser(description="handoff JSON -> MD pockets/<name>.json")
    ap.add_argument("--handoff", type=Path, required=True)
    ap.add_argument("--out", type=Path, default=None, help="default ../pockets/<pocket_name>.json")
    args = ap.parse_args()

    h = json.loads(args.handoff.read_text(encoding="utf-8"))
    name = h["pocket_name"]
    resseq = sorted(set(h.get("pocket_residues_resseq")
                        or [r["resid"] for r in h.get("pocket_residues", [])]))
    if not resseq:
        sys.exit(f"handoff {args.handoff} has no pocket residues")
    chains = h.get("pocket_chains") or sorted({r["chain"] for r in h.get("pocket_residues", [])})
    # PCNA is a homotrimer of identical chains; after biological-assembly reconstruction the
    # subunits are ordered A,B,C. Measure the pocket on the first len(chains) subunits (the
    # AOH-class interface pockets span two adjacent subunits -> indices [0,1]).
    interface = list(range(min(max(len(chains), 1), 3)))

    prov = h.get("provenance", {})
    nov = h.get("novelty_check", {})
    pocket = {
        "pocket_name": name,
        "description": f"GNN-identified candidate pocket (EXPERIMENTAL) on {h.get('identified_on_pdb')}.",
        "provenance": {
            "source": "GNN pocket search (PocketGNNXL) -> pocket_handoff.json",
            "identified_on_pdb": h.get("identified_on_pdb"),
            "git_commit": prov.get("commit") or prov.get("git_commit"),
            "checkpoint": prov.get("checkpoint"),
            "checkpoint_sha256": prov.get("checkpoint_sha256"),
            "leakage_fixed": prov.get("leakage_fixed"),
            "gate6_approval_ref": h.get("governance", {}).get("approval_ref"),
        },
        "caveat": (f"EXPERIMENTAL candidate. Novelty classification: {nov.get('classification','unknown')}. "
                   "Not a validated novel site (governance doc 12 requires human review). The MD below "
                   "reports whatever is true; it does not assume this pocket opens."),
        "apo_pdb": h.get("apo_pdb", "1W60"),
        "apo_role": "true apo PCNA homotrimer (pocket CLOSED). Does it transiently open?",
        "control_pdb": h.get("control_pdb"),
        "control_role": ("holo/open positive control (ligand stripped)" if h.get("control_pdb")
                         else "NONE — novel site with no known-open structure; the gate will report "
                              "'inconclusive' rather than a false negative"),
        "expected_protein_chains": 3,
        "min_chain_residues": 200,
        "interface_chain_indices": interface,
        "pocket_residues_resseq": resseq,
        "pocket_residues_by_chain": h.get("pocket_residues_by_chain"),
        "residue_numbering": "PDB author (auth_seq_id); consistent across PCNA structures.",
    }
    out = args.out or (HERE.parent / "pockets" / f"{name}.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(pocket, indent=2))
    print(f"[ok] wrote {out}")
    print(f"     pocket '{name}': {len(resseq)} residues on chains {chains} "
          f"(interface indices {interface}); apo={pocket['apo_pdb']} control={pocket['control_pdb']}")
    print(f"     -> run MD: ./run_in_tmux.sh {name}")


if __name__ == "__main__":
    main()
