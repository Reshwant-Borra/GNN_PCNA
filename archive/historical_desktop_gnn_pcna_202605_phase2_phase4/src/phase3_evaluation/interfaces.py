"""Evaluation contracts for future governed Phase 3 runs."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MetricSpec:
    name: str
    aggregation: str
    status: str = "SPEC_ONLY_NOT_COMPUTED"


@dataclass(frozen=True)
class EvaluationPlan:
    metrics: tuple[MetricSpec, ...] = (
        MetricSpec("AUROC", "macro_and_micro"),
        MetricSpec("AUPRC", "macro_and_micro"),
        MetricSpec("top_k_recovery", "per_protein_and_macro"),
        MetricSpec("calibration", "frozen_config_only"),
    )
    test_set_policy: str = "No test evaluation before frozen model, thresholds, baselines, and report plan."
    status: str = "NOT_IMPLEMENTED"

