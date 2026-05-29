"""Gate names and per-gate status records.

The gate system encodes the 10 scientific blockers defined in docs/04_GATE_SYSTEM.md.
A gate's status governs whether downstream work is allowed.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple

from research_os.schemas.vocab import GATE_STATUSES, require_value


class GateName:
    RESEARCH_DESIGN = "research_design"
    DATASET = "dataset"
    LEAKAGE = "leakage"
    PREPROCESSING = "preprocessing"
    CODE = "code"
    EVALUATION = "evaluation"
    VALIDATION = "validation"
    CLAIM = "claim"
    FIGURE = "figure"
    SUBMISSION = "submission"

    ALL: Tuple[str, ...] = (
        RESEARCH_DESIGN,
        DATASET,
        LEAKAGE,
        PREPROCESSING,
        CODE,
        EVALUATION,
        VALIDATION,
        CLAIM,
        FIGURE,
        SUBMISSION,
    )

    @classmethod
    def validate(cls, name: str) -> None:
        if name not in cls.ALL:
            raise ValueError(f"Unknown gate {name!r}. Allowed: {cls.ALL}")


@dataclass
class GateStatus:
    name: str
    status: str = "not_started"
    last_updated: str = ""
    updated_by: str = ""
    reason: str = ""
    blocking_findings: List[str] = field(default_factory=list)
    evidence_paths: List[str] = field(default_factory=list)

    def validate(self) -> None:
        GateName.validate(self.name)
        require_value("GateStatus.status", self.status, GATE_STATUSES)

    def is_blocking(self) -> bool:
        return self.status in ("fail", "blocked", "stale")


__all__ = ["GateName", "GateStatus"]
