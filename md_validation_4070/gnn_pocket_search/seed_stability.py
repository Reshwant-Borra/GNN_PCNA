#!/usr/bin/env python
"""Multi-seed pocket stability: the gate between "the GNN found something" and MD.

WHY THIS EXISTS
---------------
The pre-MD audit (2026-08) established that the exported candidate pocket is not a
property of the data -- it is a property of *which retrain you happened to run*. Scoring
1W60 with the repo's checkpoints selected, variously: the AOH site, an 8-residue IDCL
fragment, a 5-residue C-terminal tail, and a 255-residue whole chain. On the committed
scores the top cluster beats the runner-up by 0.0016-0.0119 mean score.

Running MD on a single seed's pocket therefore measures the seed, not the protein. This
tool runs the SAME selection logic across N seeded retrains and reports what survives.

WHAT IT DOES
------------
1. For each checkpoint, score the target structure with scripts/run_v3_inference.py
   (the real inference path -- no reimplementation, so semantics cannot drift) into an
   isolated output dir.
2. Take each run's top cluster as a set of (chain, resid) pairs.
3. Report pairwise Jaccard, per-residue selection frequency, and the consensus set
   (residues chosen by >= --min-fraction of runs).
4. Emit a verdict: STABLE (consensus is usable) or UNSTABLE (do not spend MD compute).

USAGE
-----
    # after producing several seeded checkpoints:
    #   for s in 42 43 44; do
    #     python scripts/finetune_v3_fixed.py --seed $s --out checkpoints/seed_$s/best.ckpt
    #   done
    python seed_stability.py --worktree /path/to/gnn_xl_worktree --pdb 1W60 \
        --ckpt checkpoints/seed_42/best.ckpt \
        --ckpt checkpoints/seed_43/best.ckpt \
        --ckpt checkpoints/seed_44/best.ckpt \
        --out stability_1W60.json

Pass --consensus-out to write a handoff-shaped residue list built from the consensus
rather than from any single seed.
"""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
import tempfile
from collections import Counter
from itertools import combinations
from pathlib import Path


def score_with_checkpoint(worktree: Path, pdb: str, ckpt: Path, out_dir: Path) -> Path:
    """Run the real inference script for one checkpoint; return the scores.csv path."""
    cmd = [sys.executable, "scripts/run_v3_inference.py",
           "--ckpt", str(ckpt), "--out-dir", str(out_dir), "--only", pdb]
    proc = subprocess.run(cmd, cwd=worktree, capture_output=True, text=True)
    if proc.returncode != 0:
        tail = (proc.stdout + proc.stderr).strip().splitlines()[-12:]
        sys.exit(f"[stability] inference failed for {ckpt}:\n  " + "\n  ".join(tail))
    csv_path = out_dir / pdb / "scores.csv"
    if not csv_path.exists():
        sys.exit(f"[stability] no scores.csv produced for {ckpt} (looked at {csv_path})")
    return csv_path


def top_cluster_residues(scores_csv: Path) -> tuple[set[tuple[str, int]], float, float]:
    """Top cluster by mean score -> {(chain, resid)}, its mean, and the runner-up margin.

    Mirrors export_handoff.load_cluster exactly so this tool measures the thing that
    would actually be exported.
    """
    rows = list(csv.DictReader(scores_csv.open(encoding="utf-8", errors="replace")))
    for r in rows:
        r["score"] = float(r["score"])
        r["cluster"] = int(r["cluster"])
    clustered = [r for r in rows if r["cluster"] >= 0]
    if not clustered:
        return set(), float("nan"), float("nan")
    ids = sorted({r["cluster"] for r in clustered})
    means = {c: sum(r["score"] for r in clustered if r["cluster"] == c)
                / max(1, sum(1 for r in clustered if r["cluster"] == c)) for c in ids}
    best = max(means, key=means.get)
    ordered = sorted(means.values(), reverse=True)
    margin = (ordered[0] - ordered[1]) if len(ordered) > 1 else float("inf")
    members = {(r["chain"], int(r["resid"])) for r in clustered if r["cluster"] == best}
    return members, means[best], margin


def jaccard(a: set, b: set) -> float:
    if not a and not b:
        return 1.0
    return len(a & b) / max(len(a | b), 1)


def main() -> None:
    ap = argparse.ArgumentParser(description="Multi-seed pocket stability gate.")
    ap.add_argument("--worktree", type=Path, required=True)
    ap.add_argument("--pdb", required=True, help="structure to score, e.g. 1W60")
    ap.add_argument("--ckpt", type=Path, action="append", required=True,
                    help="repeatable; one per seed. Use >= 3.")
    ap.add_argument("--min-fraction", type=float, default=0.6,
                    help="a residue joins the consensus if chosen by >= this fraction of runs")
    ap.add_argument("--min-jaccard", type=float, default=0.5,
                    help="mean pairwise Jaccard below this => UNSTABLE")
    ap.add_argument("--min-consensus-residues", type=int, default=8)
    ap.add_argument("--out", type=Path, default=None, help="write the full report as JSON")
    ap.add_argument("--consensus-out", type=Path, default=None,
                    help="write the consensus residue list (handoff-shaped) here")
    ap.add_argument("--scores-dir", type=Path, default=None,
                    help="reuse/keep per-checkpoint scores here instead of a temp dir")
    args = ap.parse_args()

    if len(args.ckpt) < 2:
        sys.exit("[stability] give at least 2 --ckpt (3+ strongly recommended); "
                 "a single seed cannot show stability by construction.")

    workroot = args.scores_dir or Path(tempfile.mkdtemp(prefix="seedstab_"))
    workroot.mkdir(parents=True, exist_ok=True)

    runs = []
    for i, ck in enumerate(args.ckpt):
        if not ck.exists():
            sys.exit(f"[stability] checkpoint not found: {ck}")
        print(f"[stability] [{i+1}/{len(args.ckpt)}] scoring {args.pdb} with {ck.name} ...")
        csv_path = score_with_checkpoint(args.worktree, args.pdb, ck, workroot / f"run{i}")
        residues, mean, margin = top_cluster_residues(csv_path)
        runs.append({"checkpoint": str(ck), "n_residues": len(residues),
                     "top_mean_score": None if mean != mean else round(mean, 5),
                     "runner_up_margin": (None if margin == float("inf") or margin != margin
                                          else round(margin, 5)),
                     "residues": sorted(residues)})
        print(f"    -> {len(residues)} residues, mean {mean:.4f}, margin "
              f"{'inf' if margin == float('inf') else f'{margin:.4f}'}")

    sets = [set(map(tuple, r["residues"])) for r in runs]
    pairs = [(i, j, jaccard(sets[i], sets[j])) for i, j in combinations(range(len(sets)), 2)]
    mean_j = sum(p[2] for p in pairs) / len(pairs) if pairs else 1.0

    freq = Counter()
    for s in sets:
        freq.update(s)
    need = args.min_fraction * len(sets)
    consensus = sorted({k for k, c in freq.items() if c >= need})

    unstable = []
    if mean_j < args.min_jaccard:
        unstable.append(f"mean pairwise Jaccard {mean_j:.3f} < {args.min_jaccard}: the seeds "
                        f"do not agree on which residues form the pocket")
    if len(consensus) < args.min_consensus_residues:
        unstable.append(f"only {len(consensus)} residues reach {args.min_fraction:.0%} agreement "
                        f"(< {args.min_consensus_residues}): no usable consensus pocket")
    margins = [r["runner_up_margin"] for r in runs if r["runner_up_margin"] is not None]
    if margins and max(margins) < 0.02:
        unstable.append(f"every run's top cluster beats its runner-up by < 0.02 "
                        f"(max {max(margins):.4f}): selection is within noise in all seeds")

    report = {
        "pdb": args.pdb,
        "n_runs": len(runs),
        "mean_pairwise_jaccard": round(mean_j, 4),
        "pairwise_jaccard": [{"a": i, "b": j, "jaccard": round(v, 4)} for i, j, v in pairs],
        "consensus_min_fraction": args.min_fraction,
        "consensus_n_residues": len(consensus),
        "consensus_residues": [{"chain": c, "resid": r} for c, r in consensus],
        "residue_frequency": {f"{c}:{r}": n for (c, r), n in sorted(freq.items())},
        "runs": runs,
        "verdict": "UNSTABLE" if unstable else "STABLE",
        "reasons": unstable,
    }

    print("\n=== stability report ===")
    print(f"  runs                  : {len(runs)}")
    print(f"  mean pairwise Jaccard : {mean_j:.3f}")
    print(f"  consensus residues    : {len(consensus)} at >= {args.min_fraction:.0%} agreement")
    if consensus:
        by_chain: dict[str, list[int]] = {}
        for c, r in consensus:
            by_chain.setdefault(c, []).append(r)
        for c in sorted(by_chain):
            print(f"      chain {c}: {sorted(by_chain[c])}")
    print(f"  VERDICT               : {report['verdict']}")
    for r in unstable:
        print(f"      - {r}")

    if args.out:
        args.out.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"  report -> {args.out}")
    if args.consensus_out and consensus:
        args.consensus_out.write_text(json.dumps({
            "pocket_residues": [{"chain": c, "resid": r} for c, r in consensus],
            "pocket_residues_by_chain": {c: sorted(v) for c, v in
                                         ((c, [r for cc, r in consensus if cc == c])
                                          for c in sorted({c for c, _ in consensus}))},
            "pocket_chains": sorted({c for c, _ in consensus}),
            "derived_from": "multi-seed consensus", "n_runs": len(runs),
            "min_fraction": args.min_fraction,
            "mean_pairwise_jaccard": round(mean_j, 4),
        }, indent=2), encoding="utf-8")
        print(f"  consensus -> {args.consensus_out}")

    sys.exit(0 if not unstable else 2)


if __name__ == "__main__":
    main()
