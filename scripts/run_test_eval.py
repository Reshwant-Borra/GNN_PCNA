"""
Evaluate the trained model on the held-out test split.

The test split (cryptosite_split.json) was withheld from ALL training and
validation — these are genuinely unseen proteins at evaluation time.

Labels are ligand-proximity based (Ca within 6 A of any ligand atom).
This is the same labelling methodology used throughout training, applied
consistently to held-out structures.

Writes: data/results/test_split_eval.json

Usage:
    python scripts/run_test_eval.py
    python scripts/run_test_eval.py --ckpt checkpoints/pcna/best_pcna.ckpt --model small
"""
from __future__ import annotations
import sys, json, argparse
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
from sklearn.metrics import roc_auc_score, average_precision_score
from src.models import PocketGNN, PocketGNNXL


def load_model(ckpt_path: Path, model_size: str, node_in_dim: int):
    if model_size == "xl":
        model = PocketGNNXL(node_in_dim=node_in_dim).eval()
    elif model_size == "small":
        model = PocketGNN.small().eval()
    elif model_size == "medium":
        model = PocketGNN.medium().eval()
    else:
        model = PocketGNN().eval()
    if ckpt_path.exists():
        model.load_state_dict(
            torch.load(str(ckpt_path), map_location="cpu", weights_only=True))
        return model, True
    return model, False


def eval_graph(model, data):
    with torch.no_grad():
        scores = model(
            data.x, data.edge_index, data.edge_attr,
            data.edge_index_seq, data.edge_attr_seq,
            data.chain_id,
        ).numpy()
    return scores


def run(ckpt_path: Path, model_size: str, split_path: Path,
        graphs_dir: Path) -> dict:
    split = json.loads(split_path.read_text())
    test_ids = split["splits"]["test"]
    val_ids  = split["splits"]["val"]

    # Detect node_in_dim from first available graph
    sample = torch.load(str(graphs_dir / f"{test_ids[0]}.pt"), weights_only=False)
    node_in_dim = sample.x.shape[1]

    model, ckpt_loaded = load_model(ckpt_path, model_size, node_in_dim)

    results = {}
    for phase, ids in [("val", val_ids), ("test", test_ids)]:
        per_structure = []
        all_scores, all_labels = [], []
        for pid in ids:
            pt = graphs_dir / f"{pid}.pt"
            if not pt.exists():
                per_structure.append({"pdb_id": pid, "error": "graph not found"})
                continue
            data = torch.load(str(pt), weights_only=False)
            y = data.y.numpy() if hasattr(data, "y") else None
            if y is None or y.sum() == 0:
                per_structure.append({"pdb_id": pid, "skipped": "no positive labels"})
                continue

            scores = eval_graph(model, data)
            auroc = float(roc_auc_score(y, scores))
            auprc = float(average_precision_score(y, scores))
            n_pos = int(y.sum())
            n_tot = len(y)
            top_k_recovery = float(
                np.isin(np.argsort(scores)[-n_pos:], np.where(y)[0]).mean()
            )
            per_structure.append({
                "pdb_id": pid,
                "n_residues": n_tot,
                "n_positive": n_pos,
                "auroc": round(auroc, 4),
                "auprc": round(auprc, 4),
                "top_k_recovery": round(top_k_recovery, 4),
            })
            all_scores.extend(scores.tolist())
            all_labels.extend(y.tolist())

        scored = [r for r in per_structure if "auroc" in r]
        mean_auroc = float(np.mean([r["auroc"] for r in scored])) if scored else float("nan")
        mean_auprc = float(np.mean([r["auprc"] for r in scored])) if scored else float("nan")

        results[phase] = {
            "n_structures": len(ids),
            "n_scored": len(scored),
            "mean_auroc": round(mean_auroc, 4),
            "mean_auprc": round(mean_auprc, 4),
            "per_structure": per_structure,
        }

    return {
        "checkpoint": str(ckpt_path),
        "checkpoint_loaded": ckpt_loaded,
        "model": model_size,
        "node_in_dim": node_in_dim,
        "split_file": str(split_path),
        "label_method": "ligand-proximity (Ca within 6 A of any ligand atom)",
        "independence_note": (
            "Test structures were withheld from ALL training and validation. "
            "They are different protein families from the PCNA fine-tuning data. "
            "Labels use the same methodology as training (ligand-proximity) applied "
            "consistently to unseen proteins."
        ),
        "results": results,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ckpt",   default="checkpoints/pcna/best_pcna.ckpt")
    parser.add_argument("--model",  default="small",
                        choices=["small", "medium", "large", "xl"])
    parser.add_argument("--split",  default="data/splits/cryptosite_split.json")
    parser.add_argument("--graphs", default="data/graphs")
    args = parser.parse_args()

    result = run(
        Path(args.ckpt), args.model,
        Path(args.split), Path(args.graphs),
    )

    model_tag = Path(args.ckpt).stem
    out = REPO / "data" / "results" / f"test_split_eval_{model_tag}.json"
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"Saved -> {out.relative_to(REPO)}")

    for phase in ["val", "test"]:
        r = result["results"][phase]
        print(f"\n{phase.upper()} ({r['n_scored']}/{r['n_structures']} structures scored):")
        print(f"  Mean AUROC : {r['mean_auroc']:.4f}")
        print(f"  Mean AUPRC : {r['mean_auprc']:.4f}")
        for s in r["per_structure"]:
            if "auroc" in s:
                print(f"  {s['pdb_id']:6s}  AUROC={s['auroc']:.4f}  AUPRC={s['auprc']:.4f}  "
                      f"top-k={s['top_k_recovery']:.3f}  ({s['n_positive']}/{s['n_residues']} pos)")


if __name__ == "__main__":
    main()
