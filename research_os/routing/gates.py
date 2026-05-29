"""Gate resolver.

Map intent -> required gate names. Gates encode the scientific blockers from
docs/04_GATE_SYSTEM.md; failing or stale gates cause the orchestrator to
block downstream work.
"""
from __future__ import annotations

from typing import Dict, List, Tuple

from research_os.schemas.gates import GateName

_INTENT_GATES: Dict[str, Tuple[str, ...]] = {
    "source_of_truth_query": (),
    "research_design": (GateName.RESEARCH_DESIGN,),
    "data_audit": (GateName.DATASET,),
    "split_or_leakage": (GateName.DATASET, GateName.LEAKAGE),
    "preprocessing_audit": (GateName.PREPROCESSING, GateName.DATASET),
    "code_build": (GateName.CODE,),
    "code_review": (GateName.CODE,),
    "training": (
        GateName.DATASET,
        GateName.LEAKAGE,
        GateName.PREPROCESSING,
        GateName.CODE,
        GateName.EVALUATION,
    ),
    "metric_verification": (GateName.LEAKAGE, GateName.EVALUATION),
    "md_or_validation": (GateName.VALIDATION,),
    "claim_or_paper": (
        GateName.CLAIM,
        GateName.EVALUATION,
        GateName.VALIDATION,
    ),
    "figure_generation": (GateName.FIGURE, GateName.CLAIM),
    "compute_planning": (),
    "submission_readiness": (
        GateName.RESEARCH_DESIGN,
        GateName.DATASET,
        GateName.LEAKAGE,
        GateName.PREPROCESSING,
        GateName.CODE,
        GateName.EVALUATION,
        GateName.VALIDATION,
        GateName.CLAIM,
        GateName.FIGURE,
        GateName.SUBMISSION,
    ),
    "collaboration_sync": (),
    "contradiction_hunt": (),
    "general": (),
}


def determine_required_gates(intents: List[str]) -> List[str]:
    """Return the ordered, deduplicated gate list for these intents."""
    out: List[str] = []
    seen: set[str] = set()
    for intent in intents:
        for gate in _INTENT_GATES.get(intent, ()):
            if gate not in seen:
                out.append(gate)
                seen.add(gate)
    return out


__all__ = ["determine_required_gates"]
