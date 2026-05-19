"""
AOH1996 Validation Gate Check.

Computes exact per-residue scores on 8GLA and reports whether the model
recovers the AOH1996 pocket above the 0.7 validation threshold.

Usage:
    python scripts/aoh_gate_check.py
    python scripts/aoh_gate_check.py --ckpt checkpoints/pcna/best_pcna_v3.ckpt --model xl

Outputs:
    - Mean / median score over labeled AOH1996 residues
    - Rank of top AOH1996 residue in the full score list
    - Pass/fail verdict against the 0.7 threshold
"""
from __future__ import annotations
import sys, json
from pathlib import Path

REPO = Path(__file__).parent.parent
sys.path.insert(0, str(REPO))

try:
    import torch
    import torch_geometric  # noqa: F401
except ImportError as e:
    print(f"\n[ERROR] Missing dependency: {e}")
    print("  PyTorch Geometric is required. Run the environment checker first:")
    print("    python scripts/check_env.py")
    print("  Then follow its install instructions.\n")
    sys.exit(1)

import numpy as np
from src.models import PocketGNN, PocketGNNXL

# AOH1996 ground truth: residue numbers per chain in 8GLA
AOH_GT_BY_CHAIN = {
    "A": {25,26,27,38,39,40,41,42,44,45,46,47,
          123,125,126,128,231,232,233,234,250,251,252,253},
    "B": {23,25,26,27,38,39,40,41,42,44,45,46,47,
          123,125,126,128,231,232,233,234,250,251,252},
}
GATE = 0.7


def run(ckpt_path: Path, model_size: str) -> dict:
    if model_size == "xl":
        graph_path = REPO / "data" / "pcna_xl" / "8GLA.pt"
        if not graph_path.exists():
            graph_path = REPO / "data" / "pcna" / "8GLA.pt"
    else:
        graph_path = REPO / "data" / "pcna" / "8GLA.pt"
        if not graph_path.exists():
            graph_path = REPO / "data" / "pcna_xl" / "8GLA.pt"
    if not graph_path.exists():
        return {"error": "8GLA.pt not found in data/pcna/ or data/pcna_xl/"}

    data = torch.load(str(graph_path), weights_only=False)

    node_in_dim = data.x.shape[1]
    if model_size == "xl":
        model = PocketGNNXL(node_in_dim=node_in_dim).eval()
    else:
        model = PocketGNN.small().eval()

    if not ckpt_path.exists():
        return {"error": f"checkpoint not found: {ckpt_path}"}

    model.load_state_dict(torch.load(str(ckpt_path), map_location="cpu", weights_only=True))

    with torch.no_grad():
        scores = model(
            data.x, data.edge_index, data.edge_attr,
            data.edge_index_seq, data.edge_attr_seq,
            data.chain_id,
        ).numpy()

    # Map chain_id integer back to letter
    resids   = data.resid.numpy()   if hasattr(data, "resid")    else np.arange(len(scores))
    chain_ids = data.chain_id.numpy() if hasattr(data, "chain_id") else np.zeros(len(scores), dtype=int)
    chain_letters = [chr(65 + int(c)) for c in chain_ids]

    # Identify labeled residue indices
    labeled_mask = np.array([
        r in AOH_GT_BY_CHAIN.get(ch, set())
        for r, ch in zip(resids.tolist(), chain_letters)
    ])

    if not labeled_mask.any():
        return {"error": "No AOH1996 labeled residues found — check resid/chain_id in graph"}

    labeled_scores = scores[labeled_mask]
    all_sorted     = np.sort(scores)[::-1]

    mean_score   = float(labeled_scores.mean())
    median_score = float(np.median(labeled_scores))
    min_score    = float(labeled_scores.min())
    max_score    = float(labeled_scores.max())
    # Rank of best labeled residue (1 = highest score in whole structure)
    best_labeled_score = float(labeled_scores.max())
    rank_of_best = int(np.searchsorted(-all_sorted, -best_labeled_score)) + 1
    n_labeled    = int(labeled_mask.sum())

    gate_pass = mean_score >= GATE

    result = {
        "checkpoint": str(ckpt_path),
        "model": model_size,
        "n_residues_total": len(scores),
        "n_aoh_labeled": n_labeled,
        "aoh_mean_score": round(mean_score, 4),
        "aoh_median_score": round(median_score, 4),
        "aoh_min_score": round(min_score, 4),
        "aoh_max_score": round(max_score, 4),
        "rank_of_best_aoh_residue": rank_of_best,
        "gate_threshold": GATE,
        "gate_pass": gate_pass,
        "verdict": "PASS" if gate_pass else f"FAIL (mean {mean_score:.4f} < {GATE})",
        "command": f"python scripts/aoh_gate_check.py --ckpt {ckpt_path} --model {model_size}",
    }
    return result


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--ckpt",  default="checkpoints/pcna/best_pcna.ckpt")
    parser.add_argument("--model", default="small", choices=["small", "xl"])
    args = parser.parse_args()

    result = run(Path(args.ckpt), args.model)
    print(json.dumps(result, indent=2))
    if "error" in result:
        sys.exit(1)
    sys.exit(0 if result["gate_pass"] else 1)


if __name__ == "__main__":
    main()
