"""Concrete agent implementations.

Each agent is a subclass of `BaseAgent`. Agents are stateless besides the
context packet they receive and the read-only stores they're handed. The
public registry `AGENT_REGISTRY` maps the canonical agent IDs from
`research_os.schemas.vocab.AGENT_IDS` to constructor callables, so the
orchestrator can instantiate agents by ID without importing each module.
"""

from typing import Callable, Dict

from research_os.agents.base import AgentContext, BaseAgent

from research_os.agents.context_provenance import (
    ContextSourceTruthAgent,
    ContradictionHunterAgent,
    ProvenanceArtifactsAgent,
)
from research_os.agents.orchestrator_role import MasterResearchOrchestratorAgent
from research_os.agents.data_audit import (
    DatasetIntegrityAgent,
    LeakageSplitAgent,
    PreprocessingAuditorAgent,
    ScientificCodeReviewAgent,
    TestingEnvironmentAgent,
)
from research_os.agents.science_evaluation import (
    BiologicalRealismAgent,
    ComputePlanningAgent,
    LiteratureWebAgent,
    MetricsStatisticsAgent,
    ModelTrainingAgent,
    ResearchDesignAgent,
    ValidationSkepticAgent,
)
from research_os.agents.communication import (
    CodeBuilderAgent,
    PaperClaimAgent,
    ReviewerCollaborationAgent,
    VisualEvidenceAgent,
)


AGENT_REGISTRY: Dict[str, Callable[[AgentContext], BaseAgent]] = {
    "master_orchestrator": MasterResearchOrchestratorAgent,
    "context_source_truth": ContextSourceTruthAgent,
    "research_design": ResearchDesignAgent,
    "biological_realism": BiologicalRealismAgent,
    "literature_web": LiteratureWebAgent,
    "dataset_integrity": DatasetIntegrityAgent,
    "leakage_split": LeakageSplitAgent,
    "preprocessing_auditor": PreprocessingAuditorAgent,
    "code_builder": CodeBuilderAgent,
    "scientific_code_review": ScientificCodeReviewAgent,
    "testing_environment": TestingEnvironmentAgent,
    "model_training": ModelTrainingAgent,
    "metrics_statistics": MetricsStatisticsAgent,
    "compute_planning": ComputePlanningAgent,
    "validation_skeptic": ValidationSkepticAgent,
    "contradiction_hunter": ContradictionHunterAgent,
    "provenance_artifacts": ProvenanceArtifactsAgent,
    "paper_claim": PaperClaimAgent,
    "visual_evidence": VisualEvidenceAgent,
    "reviewer_collaboration": ReviewerCollaborationAgent,
}


__all__ = [
    "AGENT_REGISTRY",
    "AgentContext",
    "BaseAgent",
    "BiologicalRealismAgent",
    "CodeBuilderAgent",
    "ComputePlanningAgent",
    "ContextSourceTruthAgent",
    "ContradictionHunterAgent",
    "DatasetIntegrityAgent",
    "LeakageSplitAgent",
    "LiteratureWebAgent",
    "MasterResearchOrchestratorAgent",
    "MetricsStatisticsAgent",
    "ModelTrainingAgent",
    "PaperClaimAgent",
    "PreprocessingAuditorAgent",
    "ProvenanceArtifactsAgent",
    "ResearchDesignAgent",
    "ReviewerCollaborationAgent",
    "ScientificCodeReviewAgent",
    "TestingEnvironmentAgent",
    "ValidationSkepticAgent",
    "VisualEvidenceAgent",
]
