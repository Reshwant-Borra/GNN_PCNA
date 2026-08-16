"""Model contracts for future governed Phase 3 implementation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class ModelOutputContract:
    output_name: str = "residue_logits"
    loss_pairing: str = "BCEWithLogitsLoss-compatible logits; no final sigmoid during training"
    batch_isolation_required: bool = True
    training_status: str = "NOT_IMPLEMENTED"


class ModelInterface(Protocol):
    """Future model implementations must satisfy this contract."""

    output_contract: ModelOutputContract

    def forward(self, batch: object) -> object:
        """Return residue-level logits once model science is approved."""
        raise NotImplementedError

