"""Random residue-score baseline.

Assigns uniform random [0, 1] scores to all loss_mask=True residues.
Expected macro-AUPRC ≈ positive rate ≈ 0.046.

Governance: docs/scientific_governance/10_BASELINE_REQUIREMENTS.md
Gate: reports/phase3/baseline_gate3_authorization_20260529.md
"""

from __future__ import annotations

import random
from typing import Any

from torch_geometric.data import Data


def _collect_random_scores(
    val_data: list[Data],
    seed: int,
) -> list[tuple[list[float], list[int]]]:
    """Assign random [0,1] scores to each loss_mask=True residue."""
    rng = random.Random(seed)
    protein_scores: list[tuple[list[float], list[int]]] = []
    for d in val_data:
        lm = d.loss_mask
        labels = [int(v) for v in d.y[lm].tolist()]
        scores = [rng.random() for _ in labels]
        protein_scores.append((scores, labels))
    return protein_scores


def run_random_baseline(
    val_data: list[Data],
    seeds: tuple[int, ...] = (0, 1, 2),
) -> dict[str, Any]:
    """Run random baseline across multiple seeds.

    Args:
        val_data: Validation-fold Data objects (loss_mask applied inside).
        seeds: Random seeds to run.

    Returns:
        Dict with per-seed metrics and aggregate mean ± SD.
    """
    import sys
    from pathlib import Path
    ROOT = Path(__file__).resolve().parents[2]
    if str(ROOT / "src") not in sys.path:
        sys.path.insert(0, str(ROOT / "src"))

    from phase3_evaluation.metrics import (
        aggregate_seeds,
        bootstrap_ci,
        compute_metrics_from_lists,
    )

    per_seed: list[dict[str, Any]] = []
    seed_results: list[dict[str, Any]] = []

    for seed in seeds:
        ps = _collect_random_scores(val_data, seed)
        m = compute_metrics_from_lists(ps)
        ci = bootstrap_ci(ps)
        per_seed.append({"seed": seed, "metrics": m, "ci": ci})
        seed_results.append(m)

    aggregate = aggregate_seeds(seed_results)

    return {
        "baseline_name": "random",
        "description": "Uniform random scores in [0, 1] per residue. No structure used.",
        "seeds": list(seeds),
        "per_seed": per_seed,
        "aggregate": aggregate,
        "governance": "docs/scientific_governance/10_BASELINE_REQUIREMENTS.md",
        "gate": "reports/phase3/baseline_gate3_authorization_20260529.md",
        "no_test_set_evaluation": True,
        "no_scientific_claims": True,
    }
