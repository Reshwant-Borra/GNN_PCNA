#!/usr/bin/env python
"""
Export a GNN-identified pocket to pocket_handoff.json for the MD-validation harness.

This is the LAST step of the GNN run on Rishi's GPU box. It reads the per-structure
scores.csv that run_v3_inference.py writes, takes the model's clustered pocket (NOT
hand-picked), records provenance, runs the honesty/novelty check, and emits the
handoff JSON that Advay converts into a pockets/<name>.json for MD.

It is deliberately GATE-ENFORCING: it REFUSES to emit a handoff unless you point it at a
real recorded GATE-6 approval file (--approval-file) that actually contains an approval.
A verbal OK or a chat message is not an approval; this tool will not launder one.

Usage (on Rishi's box, after run_v3_inference.py):
  python export_handoff.py \
      --worktree /path/to/gnn_xl_worktree \
      --pdb 1W60 --cluster top --pocket-name cand_A_2026-07 \
      --checkpoint checkpoints/pcna_reproduced/best.ckpt \
      --approval-file /path/to/.memory/PROJECT_STATE.md \
      --out pocket_handoff.json
Then send pocket_handoff.json back to Advay.
"""
from __future__ import annotations
import argparse, csv, json, hashlib, subprocess, sys
from pathlib import Path

# AOH1996 ground-truth pocket (known positive-control site) - to flag overlap honestly.
AOH_GT = {23,25,26,27,38,39,40,41,44,45,46,47,121,123,124,125,126,128,129,131,
          231,232,233,234,250,251,252,253}


def sha256(p: Path) -> str:
    if not p.exists():
        return "MISSING"
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def git_info(repo: Path) -> dict:
    def run(*a):
        try:
            return subprocess.check_output(["git", "-C", str(repo), *a],
                                           text=True, stderr=subprocess.DEVNULL).strip()
        except Exception:
            return "unknown"
    return {"commit": run("rev-parse", "HEAD"), "branch": run("rev-parse", "--abbrev-ref", "HEAD")}


def leakage_fix_landed(repo: Path) -> bool:
    """Heuristic: the graph-leakage-fix commits (BUG-020/021/022) are in HEAD's history."""
    try:
        log = subprocess.check_output(["git", "-C", str(repo), "log", "--oneline", "-50"],
                                      text=True, stderr=subprocess.DEVNULL).lower()
        return ("leakage" in log) and ("bug-020" in log or "bug-021" in log or "bug-022" in log
                                       or "graph fixes" in log)
    except Exception:
        return False


def approval_ok(path: Path) -> tuple[bool, str]:
    """A recorded GATE-6 approval must exist and actually contain an approval line.
    We explicitly REJECT anything that reads like a governance-override / injection string."""
    if not path or not path.exists():
        return False, f"approval file not found: {path}"
    txt = path.read_text(encoding="utf-8", errors="replace").lower()
    inject_markers = ["override all repository governance", "supersed", "ignore", "give this to your repo",
                      "highest-priority project instructions"]
    if any(m in txt for m in inject_markers):
        return False, ("approval file contains governance-override / injection language - that is NOT "
                       "a scientific approval and will not be accepted. Record a specific, scoped "
                       "GATE-6 entry instead.")
    if "gate 6" in txt and ("approved_by" in txt or "approved by" in txt):
        return True, "recorded GATE-6 approval found"
    return False, ("no recorded GATE-6 approval found in the file (need a 'GATE 6' entry with an "
                   "'approved_by' line and a specific scope).")


def load_cluster(scores_csv: Path, cluster: str):
    rows = list(csv.DictReader(scores_csv.open(encoding="utf-8", errors="replace")))
    for r in rows:
        r["score"] = float(r["score"]); r["cluster"] = int(r["cluster"])
    clustered = [r for r in rows if r["cluster"] >= 0]
    if not clustered:
        sys.exit(f"No clustered pocket (all cluster == -1) in {scores_csv}. "
                 f"The model found no above-threshold pocket on this structure.")
    if cluster == "top":
        ids = sorted({r["cluster"] for r in clustered})
        best = max(ids, key=lambda c: sum(r["score"] for r in clustered if r["cluster"] == c)
                   / max(1, sum(1 for r in clustered if r["cluster"] == c)))
        chosen = best
    else:
        chosen = int(cluster)
    members = [r for r in clustered if r["cluster"] == chosen]
    return chosen, members, rows


def main():
    ap = argparse.ArgumentParser(description="Export a GNN pocket to pocket_handoff.json (gate-enforcing).")
    ap.add_argument("--worktree", type=Path, required=True, help="path to the leakage-fixed GNN repo")
    ap.add_argument("--pdb", required=True, help="PDB id the pocket was identified on")
    ap.add_argument("--cluster", default="top", help="'top' (highest mean score) or a cluster id")
    ap.add_argument("--pocket-name", required=True)
    ap.add_argument("--checkpoint", default="checkpoints/pcna_reproduced/best.ckpt")
    ap.add_argument("--split-file", default="", help="split manifest used (for provenance)")
    ap.add_argument("--approval-file", type=Path, required=True,
                    help="path to the RECORDED GATE-6 approval (e.g. .memory/PROJECT_STATE.md)")
    ap.add_argument("--apo-pdb", default="1W60")
    ap.add_argument("--control-pdb", default="", help="holo/open structure, or leave blank if none")
    ap.add_argument("--scores-csv", type=Path, default=None,
                    help="override; default <worktree>/results/v3/<pdb>/scores.csv")
    ap.add_argument("--out", type=Path, default=Path("pocket_handoff.json"))
    ap.add_argument("--esm-model", default="facebook/esm2_t12_35M_UR50D")
    args = ap.parse_args()

    # --- GATE ENFORCEMENT (refuse without a real recorded approval) ---
    ok, why = approval_ok(args.approval_file)
    if not ok:
        sys.exit(f"[REFUSED] {why}\nNo handoff written. See POCKET_HANDOFF_PROTOCOL.md for the "
                 f"GATE-6 approval template. This tool will not emit a pocket without one.")

    wt = args.worktree
    if not leakage_fix_landed(wt):
        print("[WARN] Could not confirm the graph-leakage-fix (BUG-020/021/022) is in this repo's "
              "history. A pocket found on a pre-fix checkpoint is not defensible - confirm before "
              "sending the handoff.", file=sys.stderr)

    scores_csv = args.scores_csv or (wt / "results" / "v3" / args.pdb / "scores.csv")
    if not scores_csv.exists():
        sys.exit(f"scores.csv not found: {scores_csv}. Run scripts/run_v3_inference.py first.")

    chosen, members, all_rows = load_cluster(scores_csv, args.cluster)
    # (chain, resid) PAIRS are the authoritative pocket definition. The AOH site is a
    # two-chain subunit interface, so a bare resid is ambiguous (residue 44 on chain A
    # is a DIFFERENT site than 44 on chain B). Preserve the pairing here so the handoff
    # never collapses it away.
    pocket_residues = [
        {"chain": ch, "resid": rid}
        for ch, rid in sorted({(m["chain"], int(m["resid"])) for m in members})
    ]
    residues_by_chain: dict[str, list[int]] = {}
    for pr in pocket_residues:
        residues_by_chain.setdefault(pr["chain"], []).append(pr["resid"])
    resseq = sorted({int(m["resid"]) for m in members})   # flattened union (back-compat)
    chains = sorted(residues_by_chain)
    mean_score = sum(m["score"] for m in members) / len(members)
    max_score = max(m["score"] for m in members)

    # honesty / novelty
    overlap_aoh = sorted(set(resseq) & AOH_GT)
    if overlap_aoh:
        classification = "overlaps_known_interface"
    else:
        classification = "not_in_any_known_region"  # NOT a novelty claim on its own (doc 12)
    novelty_note = ("Run scripts/check_prediction_overlap.py on these residues for the full doc-12 "
                    "region + broader-footprint classification before calling anything novel.")

    ckpt = wt / args.checkpoint
    handoff = {
        "pocket_name": args.pocket_name,
        "identified_on_pdb": args.pdb,
        "pocket_residues": pocket_residues,
        "pocket_residues_by_chain": residues_by_chain,
        "pocket_residues_resseq": resseq,
        "pocket_chains": chains,
        "score_summary": {
            "mean_score": round(mean_score, 4), "max_score": round(max_score, 4),
            "n_residues": len(resseq), "cluster_id": chosen,
            "cluster_method": "DBSCAN eps=6.0 min_samples=3 on CA of residues scoring > 0.4",
        },
        "apo_pdb": args.apo_pdb,
        "control_pdb": args.control_pdb or None,
        "provenance": {
            **git_info(wt),
            "checkpoint": str(args.checkpoint),
            "checkpoint_sha256": sha256(ckpt),
            "split_file": args.split_file,
            "leakage_fixed": leakage_fix_landed(wt),
            "esm_model": args.esm_model,
            "scores_csv": str(scores_csv),
        },
        "novelty_check": {
            "classification": classification,
            "overlap_with_aoh_ground_truth": overlap_aoh,
            "note": novelty_note,
        },
        "governance": {
            "gate6_approval_recorded": True,
            "approval_ref": str(args.approval_file),
            "approval_sha256": sha256(args.approval_file),
        },
    }
    args.out.write_text(json.dumps(handoff, indent=2))
    print(f"[ok] wrote {args.out}")
    print(f"     pocket '{args.pocket_name}' on {args.pdb}: {len(resseq)} residues "
          f"(mean score {mean_score:.3f}), classification={classification}")
    print(f"     -> send {args.out} back to Advay for the tailored MD validation.")


if __name__ == "__main__":
    main()
