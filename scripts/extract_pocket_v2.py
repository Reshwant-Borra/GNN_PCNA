#!/usr/bin/env python3
"""Pocket extraction v2 - terminus/gap masking + chain-resistant clustering.

This is ADDITIVE. It does not modify, import from, or alter the behaviour of the
frozen policy in scripts/independent_extraction_gate.py (EPS=6.0, MIN_SAMPLES=3),
which stays byte-identical so the August provenance chain still verifies.

Two defects in the frozen extraction motivate this module. Both are recorded in
md_validation_4070/GO_CHECKLIST.md and both were reproduced on real 1W60 scores.

1. CHAIN-END INFLATION.
   A crystal structure stops where the density stops, not where the protein
   stops. 1W60 models residues 1-255 of a 261-residue protein, so residues
   251-255 present a raw, unshielded cut face. Concavity and exposure features
   read that as a pocket. Measured on the retrained PCNA-naive checkpoint:

       chain A   N-term 0.191 | interior 0.204 | C-term 0.585   (2.87x)
       chain B   N-term 0.236 | interior 0.240 | C-term 0.655   (2.73x)

   Only the truncated end is inflated; the intact N-terminus scores at interior
   level. That asymmetry is the tell that it is a truncation artifact rather
   than a general terminus effect. PocketMiner (Nat Commun 2023) handles this by
   chopping terminal segments before predicting. Same fix here, applied to
   numbering gaps too, since an unresolved internal loop leaves the same
   artificial face.

2. DBSCAN CHAINING.
   DBSCAN grows a cluster transitively: A near B and B near C puts A and C in
   one cluster however far apart they are. With EPS=6.0 A against a consecutive
   Ca-Ca spacing of 3.75-3.83 A, every contiguous run of above-threshold
   residues merges, and runs merge into runs. One checkpoint produced a
   505-of-510-residue "pocket".

   Complete linkage with a diameter cap is used instead. It guarantees that
   every pair of residues inside a cluster is within max_diameter of each other,
   so a cluster cannot grow a tail. The parameter is also physically meaningful:
   the 3/3 consensus core of the AOH site spans 15.44 A across its Ca atoms, so
   an 18 A default admits a real pocket while rejecting a smear across the fold.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from collections import defaultdict
from pathlib import Path


def load_scores(path: Path) -> list[dict]:
    rows = []
    with path.open(newline="") as fh:
        for r in csv.DictReader(fh):
            rows.append({
                "chain": r["chain"],
                "resid": int(r["resid"]),
                "resname": r.get("resname", ""),
                "score": float(r["score"]),
            })
    if not rows:
        sys.exit("[extract-v2] FATAL: no rows in %s" % path)
    return rows


def load_ca_coords(pdb: Path) -> dict:
    coords = {}
    with pdb.open() as fh:
        for ln in fh:
            if ln.startswith("ATOM") and ln[12:16].strip() == "CA":
                key = (ln[21], int(ln[22:26]))
                coords.setdefault(key, (float(ln[30:38]), float(ln[38:46]), float(ln[46:54])))
    if not coords:
        sys.exit("[extract-v2] FATAL: no CA atoms parsed from %s" % pdb)
    return coords


def terminus_gap_mask(rows: list[dict], margin: int):
    """(chain, resid) within `margin` of a chain end or either side of a numbering gap.

    An unresolved internal loop produces the same artificially exposed face as a
    chain terminus, so gap-flanking residues are masked on the same rule.
    """
    by_chain = defaultdict(list)
    for r in rows:
        by_chain[r["chain"]].append(r["resid"])

    masked = set()
    detail = {"margin": margin, "chains": {}}
    for ch, ids in by_chain.items():
        ids = sorted(ids)
        lo, hi = ids[0], ids[-1]
        gaps = [(a, b) for a, b in zip(ids, ids[1:]) if b - a > 1]
        for i in ids:
            if i <= lo + margin or i >= hi - margin:
                masked.add((ch, i))
        for a, b in gaps:
            for i in ids:
                if abs(i - a) <= margin or abs(i - b) <= margin:
                    masked.add((ch, i))
        detail["chains"][ch] = {
            "resolved_range": [lo, hi],
            "numbering_gaps": [[a, b] for a, b in gaps],
            "masked_count": sum(1 for c, _ in masked if c == ch),
        }
    return masked, detail


def complete_linkage_clusters(points, max_diameter: float, min_size: int) -> list:
    """Cluster so every intra-cluster pair is within max_diameter. -1 = unassigned.

    Complete linkage is the point: unlike the transitive growth of DBSCAN, the
    merge criterion is the FARTHEST pair, so a cluster cannot chain into a tail.
    """
    import numpy as np
    from scipy.cluster.hierarchy import fcluster, linkage
    from scipy.spatial.distance import pdist

    pts = np.asarray(points, dtype=float)
    if len(pts) < 2:
        return [-1] * len(pts)
    labels = fcluster(linkage(pdist(pts), method="complete"),
                      t=max_diameter, criterion="distance")
    counts = defaultdict(int)
    for lab in labels:
        counts[lab] += 1
    out, remap = [], {}
    for lab in labels:
        if counts[lab] < min_size:
            out.append(-1)
        else:
            out.append(remap.setdefault(lab, len(remap)))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--scores", type=Path, required=True,
                    help="scores.csv produced by run_v3_inference.py")
    ap.add_argument("--pdb", type=Path, required=True,
                    help="structure the scores were computed on")
    ap.add_argument("--threshold", type=float, default=0.4)
    ap.add_argument("--terminus-margin", type=int, default=5,
                    help="mask residues this close to a chain end or numbering gap (0 disables)")
    ap.add_argument("--max-diameter", type=float, default=18.0,
                    help="max Ca-Ca distance permitted within one cluster, Angstrom")
    ap.add_argument("--min-cluster-size", type=int, default=3)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    rows = load_scores(args.scores)
    coords = load_ca_coords(args.pdb)
    if args.terminus_margin > 0:
        masked, mask_detail = terminus_gap_mask(rows, args.terminus_margin)
    else:
        masked, mask_detail = set(), {"margin": 0, "chains": {}}

    above = [r for r in rows if r["score"] >= args.threshold]
    kept = [r for r in above if (r["chain"], r["resid"]) not in masked]
    dropped = [r for r in above if (r["chain"], r["resid"]) in masked]
    usable = [r for r in kept if (r["chain"], r["resid"]) in coords]

    if usable:
        labels = complete_linkage_clusters(
            [coords[(r["chain"], r["resid"])] for r in usable],
            args.max_diameter, args.min_cluster_size)
    else:
        labels = []

    clusters = defaultdict(list)
    for r, lab in zip(usable, labels):
        if lab >= 0:
            clusters[lab].append(r)

    def diameter(members):
        pts = [coords[(m["chain"], m["resid"])] for m in members]
        return max((math.dist(a, b) for i, a in enumerate(pts) for b in pts[i + 1:]),
                   default=0.0)

    ranked = sorted(
        ({"cluster_id": int(cid),
          "n_residues": len(ms),
          "mean_score": sum(m["score"] for m in ms) / len(ms),
          "rank_score": (sum(m["score"] for m in ms) / len(ms)) * (len(ms) ** 0.5),
          "ca_max_pair_distance_A": round(diameter(ms), 3),
          "residues": [{"chain": m["chain"], "resid": m["resid"],
                        "resname": m["resname"], "score": round(m["score"], 4)}
                       for m in sorted(ms, key=lambda m: (m["chain"], m["resid"]))]}
         for cid, ms in clusters.items()),
        key=lambda c: -c["rank_score"])

    report = {
        "generator": "scripts/extract_pocket_v2.py",
        "note": "Additive. The frozen policy in independent_extraction_gate.py is unmodified.",
        "inputs": {"scores": str(args.scores), "pdb": str(args.pdb)},
        "parameters": {"threshold": args.threshold,
                       "terminus_margin": args.terminus_margin,
                       "max_diameter_A": args.max_diameter,
                       "min_cluster_size": args.min_cluster_size,
                       "clustering": "complete linkage, diameter-capped"},
        "terminus_gap_mask": mask_detail,
        "counts": {"scored": len(rows), "above_threshold": len(above),
                   "dropped_by_mask": len(dropped), "kept": len(kept),
                   "clustered": sum(len(v) for v in clusters.values()),
                   "n_clusters": len(clusters)},
        "dropped_by_mask": ["%s%d(%.3f)" % (r["chain"], r["resid"], r["score"])
                            for r in sorted(dropped, key=lambda r: -r["score"])],
        "clusters": ranked,
    }

    print("scored %d | >= %.2f: %d | masked out %d | clustered into %d"
          % (len(rows), args.threshold, len(above), len(dropped), len(clusters)))
    if dropped:
        tail = " ..." if len(dropped) > 12 else ""
        print("  dropped by terminus/gap mask: %s%s"
              % (", ".join(report["dropped_by_mask"][:12]), tail))
    for c in ranked:
        res = " ".join("%s%d" % (r["chain"], r["resid"]) for r in c["residues"])
        print("  cluster %d: n=%d mean=%.3f rank=%.3f diameter=%.1f A"
              % (c["cluster_id"], c["n_residues"], c["mean_score"],
                 c["rank_score"], c["ca_max_pair_distance_A"]))
        print("     %s" % res)
    if not ranked:
        print("  no cluster met the size threshold")

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print("\nwrote %s" % args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
