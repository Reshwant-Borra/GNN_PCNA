"""Training gates for Phase 3.

This module deliberately does not contain gradient, optimizer, or checkpoint logic.
"""

from __future__ import annotations

from pathlib import Path


class TrainingGateError(RuntimeError):
    """Raised when real training is requested before governed human sign-off."""


def training_gate_status(real_training: bool, human_pipeline_signoff: Path | None) -> dict[str, object]:
    if not real_training:
        return {
            "status": "DRY_RUN_ONLY",
            "training": "NOT_PERFORMED",
            "gradients": "NOT_COMPUTED",
            "human_pipeline_signoff": str(human_pipeline_signoff) if human_pipeline_signoff else None,
        }
    if human_pipeline_signoff is None:
        raise TrainingGateError(
            "Real Phase 3 training is blocked until the data pipeline/graph audit has human sign-off."
        )
    if not human_pipeline_signoff.is_file():
        raise TrainingGateError(f"Human pipeline sign-off record is missing: {human_pipeline_signoff}")
    # GATE 2 cleared: signoff record exists and is a real file.
    # Approved by: reports/phase3/first_training_signoff_20260528.md
    # decision_id: phase3_first_training_signoff_20260528
    return {
        "status": "GATE_CLEARED",
        "training": "AUTHORIZED",
        "human_pipeline_signoff": str(human_pipeline_signoff),
    }

