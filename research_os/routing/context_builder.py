"""Context packet builder.

Selects the subset of memory files, registry entries, and repo files that
each agent actually needs. We err toward small, well-scoped packets — agents
should not get the entire repo dumped into context.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

from research_os.memory.store import CANONICAL_FILES, MemoryStore
from research_os.registries.store import RegistryStore, REGISTRY_NAMES
from research_os.schemas.context import ContextPacket


_INTENT_MEMORY: Dict[str, tuple[str, ...]] = {
    "source_of_truth_query": (
        "PROJECT_CANONICAL_STATUS.md",
        "VALIDATION_STATUS.md",
        "CURRENT_CLAIMS.md",
        "KNOWN_BUGS_AND_RISKS.md",
    ),
    "research_design": (
        "PROJECT_CANONICAL_STATUS.md",
        "CURRENT_CLAIMS.md",
    ),
    "data_audit": (
        "PROJECT_CANONICAL_STATUS.md",
        "DATASET_REGISTRY.md",
        "KNOWN_BUGS_AND_RISKS.md",
    ),
    "split_or_leakage": (
        "DATASET_REGISTRY.md",
        "MODEL_REGISTRY.md",
        "KNOWN_BUGS_AND_RISKS.md",
    ),
    "preprocessing_audit": (
        "DATASET_REGISTRY.md",
        "KNOWN_BUGS_AND_RISKS.md",
    ),
    "code_build": (
        "PROJECT_CANONICAL_STATUS.md",
        "KNOWN_BUGS_AND_RISKS.md",
    ),
    "code_review": (
        "KNOWN_BUGS_AND_RISKS.md",
    ),
    "training": (
        "DATASET_REGISTRY.md",
        "MODEL_REGISTRY.md",
        "COMPUTE_REGISTRY.md",
        "KNOWN_BUGS_AND_RISKS.md",
    ),
    "metric_verification": (
        "MODEL_REGISTRY.md",
        "DATASET_REGISTRY.md",
        "CURRENT_CLAIMS.md",
    ),
    "md_or_validation": (
        "VALIDATION_STATUS.md",
        "CURRENT_CLAIMS.md",
        "COMPUTE_REGISTRY.md",
    ),
    "claim_or_paper": (
        "CURRENT_CLAIMS.md",
        "VALIDATION_STATUS.md",
        "PROJECT_CANONICAL_STATUS.md",
        "REVIEWER_RISK_REGISTER.md",
    ),
    "figure_generation": (
        "CURRENT_CLAIMS.md",
        "VALIDATION_STATUS.md",
    ),
    "compute_planning": (
        "COMPUTE_REGISTRY.md",
        "MODEL_REGISTRY.md",
    ),
    "submission_readiness": CANONICAL_FILES,
    "collaboration_sync": (
        "PROJECT_CANONICAL_STATUS.md",
        "CURRENT_CLAIMS.md",
        "HUMAN_DECISIONS.md",
    ),
    "document_ingestion": (
        "PROJECT_CANONICAL_STATUS.md",
        "CURRENT_CLAIMS.md",
        "HUMAN_DECISIONS.md",
    ),
    "contradiction_hunt": (
        "PROJECT_CANONICAL_STATUS.md",
        "CURRENT_CLAIMS.md",
        "VALIDATION_STATUS.md",
        "KNOWN_BUGS_AND_RISKS.md",
    ),
    "general": (
        "PROJECT_CANONICAL_STATUS.md",
    ),
}


# Per-intent registry projections. Empty tuple means "no registry needed".
_INTENT_REGISTRIES: Dict[str, tuple[str, ...]] = {
    "source_of_truth_query": ("artifact_registry", "claim_registry", "issue_registry"),
    "data_audit": ("artifact_registry", "issue_registry"),
    "split_or_leakage": ("artifact_registry", "issue_registry"),
    "preprocessing_audit": ("artifact_registry", "issue_registry"),
    "training": ("artifact_registry", "experiment_registry", "environment_registry"),
    "metric_verification": ("artifact_registry", "experiment_registry", "claim_registry"),
    "md_or_validation": ("artifact_registry", "experiment_registry", "claim_registry"),
    "claim_or_paper": ("claim_registry", "artifact_registry", "decision_registry"),
    "figure_generation": ("artifact_registry", "claim_registry"),
    "compute_planning": ("experiment_registry", "environment_registry", "decision_registry"),
    "submission_readiness": REGISTRY_NAMES,
    "contradiction_hunt": ("artifact_registry", "claim_registry", "experiment_registry", "issue_registry"),
    "collaboration_sync": ("artifact_registry", "decision_registry"),
    "document_ingestion": ("source_registry", "claim_registry", "experiment_registry", "artifact_registry"),
    "general": ("artifact_registry",),
    "research_design": ("claim_registry",),
    "code_build": ("issue_registry",),
    "code_review": ("issue_registry",),
}


_RESEARCH_BASE_CONTEXT: Dict[str, tuple[str, ...]] = {
    "source_of_truth_query": (
        "docs/research_base/INDEX.md",
        "docs/research_base/sources/SOURCE_REGISTRY.md",
        "docs/research_base/decisions/DECISION_REGISTRY.md",
        "docs/research_base/assumptions/ASSUMPTION_REGISTRY.md",
        "docs/research_base/inferences/INFERENCE_REGISTRY.md",
        "docs/research_base/project/CLAIMS_AND_EVIDENCE.md",
        "docs/research_base/project/KNOWN_LIMITATIONS.md",
    ),
    "research_design": (
        "docs/research_base/project/RESEARCH_QUESTION.md",
        "docs/research_base/project/HYPOTHESES.md",
        "docs/research_base/decisions/DECISION_REGISTRY.md",
        "docs/research_base/assumptions/ASSUMPTION_REGISTRY.md",
        "docs/research_base/inferences/INFERENCE_REGISTRY.md",
    ),
    "data_audit": (
        "docs/research_base/datasets/DATA_PROVENANCE.md",
        "docs/research_base/datasets/SPLIT_AND_HOMOLOGY_POLICY.md",
        "docs/research_base/datasets/LABEL_DEFINITION.md",
        "docs/research_base/assumptions/ASSUMPTION_REGISTRY.md",
    ),
    "split_or_leakage": (
        "docs/research_base/datasets/SPLIT_AND_HOMOLOGY_POLICY.md",
        "docs/research_base/decisions/DECISION_REGISTRY.md",
        "docs/research_base/project/KNOWN_LIMITATIONS.md",
    ),
    "preprocessing_audit": (
        "docs/research_base/ml/GRAPH_REPRESENTATION.md",
        "docs/research_base/ml/FEATURES.md",
        "docs/research_base/assumptions/ASSUMPTION_REGISTRY.md",
    ),
    "code_review": (
        "docs/research_base/decisions/DECISION_REGISTRY.md",
        "docs/research_base/assumptions/ASSUMPTION_REGISTRY.md",
        "docs/research_base/inferences/INFERENCE_REGISTRY.md",
        "docs/research_base/project/KNOWN_LIMITATIONS.md",
    ),
    "metric_verification": (
        "docs/research_base/ml/METRICS.md",
        "docs/research_base/ml/SEED_STABILITY.md",
        "docs/research_base/decisions/DECISION_REGISTRY.md",
        "docs/research_base/inferences/INFERENCE_REGISTRY.md",
    ),
    "md_or_validation": (
        "docs/research_base/md/MD_OBJECTIVE.md",
        "docs/research_base/md/POCKET_OPENING_CRITERIA.md",
        "docs/research_base/md/POSITIVE_CONTROL.md",
        "docs/research_base/project/KNOWN_LIMITATIONS.md",
        "docs/research_base/inferences/INFERENCE_REGISTRY.md",
    ),
    "claim_or_paper": (
        "docs/research_base/project/CLAIMS_AND_EVIDENCE.md",
        "docs/research_base/project/KNOWN_LIMITATIONS.md",
        "docs/research_base/sources/SOURCE_REGISTRY.md",
    ),
    "contradiction_hunt": (
        "docs/research_base/sources/SOURCE_REGISTRY.md",
        "docs/research_base/decisions/DECISION_REGISTRY.md",
        "docs/research_base/assumptions/ASSUMPTION_REGISTRY.md",
        "docs/research_base/inferences/INFERENCE_REGISTRY.md",
        "docs/research_base/project/KNOWN_LIMITATIONS.md",
        "docs/research_base/questions/OPEN_QUESTIONS.md",
    ),
    "submission_readiness": (
        "docs/research_base/INDEX.md",
        "docs/research_base/sources/SOURCE_REGISTRY.md",
        "docs/research_base/decisions/DECISION_REGISTRY.md",
        "docs/research_base/assumptions/ASSUMPTION_REGISTRY.md",
        "docs/research_base/inferences/INFERENCE_REGISTRY.md",
        "docs/research_base/project/CLAIMS_AND_EVIDENCE.md",
        "docs/research_base/project/KNOWN_LIMITATIONS.md",
        "docs/CANONICAL_PIPELINE.md",
        "docs/REPO_STRUCTURE.md",
    ),
}


def _dedup(seq) -> list:
    seen: set = set()
    out: list = []
    for item in seq:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


def build_context_packet(
    *,
    task: str,
    intents: List[str],
    risk_level: str,
    memory_store: Optional[MemoryStore] = None,
    registry_store: Optional[RegistryStore] = None,
    repo_files: Optional[List[str]] = None,
    artifacts: Optional[List[str]] = None,
    known_risks: Optional[List[str]] = None,
    allowed_actions: Optional[List[str]] = None,
    forbidden_actions: Optional[List[str]] = None,
    prior_agent_outputs: Optional[List[Dict]] = None,
) -> ContextPacket:
    """Construct a ContextPacket from the live memory + registry stores."""

    memory_files: list[str] = []
    for intent in intents or ["general"]:
        memory_files.extend(_INTENT_MEMORY.get(intent, ()))
    memory_files = _dedup(memory_files)
    if memory_store is not None:
        memory_files = [str(memory_store.path_for(n)) for n in memory_files if memory_store.exists(n)]

    registry_entries: Dict[str, List[Dict]] = {}
    if registry_store is not None:
        wanted: list[str] = []
        for intent in intents or ["general"]:
            wanted.extend(_INTENT_REGISTRIES.get(intent, ()))
        for name in _dedup(wanted):
            try:
                registry_entries[name] = registry_store.all_entries(name)
            except Exception:
                continue

    research_base_files: list[str] = []
    for intent in intents or ["general"]:
        research_base_files.extend(_RESEARCH_BASE_CONTEXT.get(intent, ()))
    if research_base_files:
        repo_root = registry_store.base_dir.parent if registry_store is not None else None
        projected_repo_files = list(repo_files or [])
        for rel in _dedup(research_base_files):
            if repo_root is None or (repo_root / rel).exists():
                projected_repo_files.append(rel)
        repo_files = _dedup(projected_repo_files)

    return ContextPacket(
        task=task,
        intents=list(intents or []),
        risk_level=risk_level,
        memory_files=memory_files,
        registry_entries=registry_entries,
        repo_files=list(repo_files or []),
        artifacts=list(artifacts or []),
        known_risks=list(known_risks or []),
        allowed_actions=list(allowed_actions or []),
        forbidden_actions=list(forbidden_actions or []),
        prior_agent_outputs=list(prior_agent_outputs or []),
    )


__all__ = ["build_context_packet"]
