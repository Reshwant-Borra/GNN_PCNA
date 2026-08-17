"""Tests that the figure data loaders read REAL Phase-3 numbers (no fabrication).

These pin the loaders to the published values in the run manifests so a future
change that silently alters or invents numbers fails loudly.
"""
import math

import pytest

from paper_engine.figures import data_loaders as dl


def test_primary_matches_published_value():
    p = dl.load_primary_training()
    # Report: 0.1876 ± 0.0113 over 12 runs.
    assert len(p.runs) == 12
    assert math.isclose(p.mean, 0.1876, abs_tol=5e-4)
    assert math.isclose(p.sd, 0.0113, abs_tol=5e-4)


def test_primary_per_fold_and_best():
    p = dl.load_primary_training()
    assert sorted(p.per_fold_mean.keys()) == [0, 1, 2, 3]
    # Best single run is fold 1, seed 2 = 0.2042.
    assert p.best_run.fold == 1 and p.best_run.seed == 2
    assert math.isclose(p.best_run.best_val_macro_auprc, 0.2042, abs_tol=1e-3)


def test_models_ordering_and_baselines_below_primary():
    models = {m.key: m for m in dl.load_all_models()}
    assert models["graphsage_3l"].kind == "primary"
    # Naive baselines must be well below the GNN.
    assert models["random"].mean < models["graphsage_3l"].mean
    assert models["degree"].mean < models["graphsage_3l"].mean
    # Ablation models are flagged as ablations.
    assert models["sage_no_spatial"].kind == "ablation"
    assert models["sage_no_sequential"].kind == "ablation"


def test_auroc_is_inflated_relative_to_auprc():
    """The rigor point: random AUROC ~0.5 while AUPRC ~ prevalence."""
    models = {m.key: m for m in dl.load_all_models()}
    assert math.isclose(models["random"].macro_auroc, 0.5, abs_tol=0.02)
    assert models["random"].mean < 0.1  # AUPRC near the prevalence floor


def test_label_and_split_stats_are_real():
    labels = dl.load_label_stats()
    assert labels["total_positives"] == 16335
    assert labels["total_masked"] == 3704
    assert labels["structures_labeled"] == 1101
    # Prevalence derived from pos_weight ~ 4-5%.
    assert 0.03 < labels["positive_prevalence"] < 0.06

    split = dl.load_split_stats()
    assert split["fold_distribution"].get("test") == 214
    assert split["manifest_hash"].startswith("24dd5e")
    assert split["pcna_holdout_count"] == 1


def test_missing_file_raises_not_fabricates(monkeypatch):
    """Integrity: a missing manifest must raise, never invent numbers."""
    monkeypatch.setattr(dl.config, "PHASE3_REPORTS", ("nonexistent/path",))
    with pytest.raises(FileNotFoundError):
        dl.load_primary_training()
