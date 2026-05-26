"""Agent Capability Profiles.

Each profile declares what an agent is allowed to do autonomously: which
tools it can call, what domain it covers, how much autonomy it should
attempt, how to fall back when autonomy is disabled, and which other agents
it can hand off to.

Profiles are *defaults* — an individual agent can override its profile via
its class attribute. The framework reads the profile to enforce safety
rails (don't let ``code_builder`` call ``web_search``; don't let
``literature_web`` write to ``MODEL_REGISTRY.md``).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from research_os.autonomous.schemas import Budget


class AutonomyLevel:
    """How much autonomy an agent should attempt.

    - ``DETERMINISTIC`` (0): Skip the planning loop entirely. Behave exactly
      like a legacy ``BaseAgent``.
    - ``GUIDED`` (1): Use a deterministic planner with a small bounded set of
      built-in tools. No LLM, no web.
    - ``ASSISTED`` (2): Add LLM-backed planning + critique if
      ``RESEARCHOS_ENABLE_LLM_AGENTS=1``. Web tools still off unless
      ``RESEARCHOS_ENABLE_WEB=1``.
    - ``FULL`` (3): All capabilities the agent's profile declares. Subject to
      env-var gates and budget caps.
    """
    DETERMINISTIC = 0
    GUIDED = 1
    ASSISTED = 2
    FULL = 3


@dataclass
class AgentProfile:
    """Declarative profile for one agent."""
    agent_id: str
    capabilities: List[str] = field(default_factory=list)
    allowed_tools: List[str] = field(default_factory=list)
    domain_areas: List[str] = field(default_factory=list)
    autonomy_level: int = AutonomyLevel.DETERMINISTIC
    confidence_model: str = "fixed"           # "fixed" | "evidence_weighted" | "calibrated"
    handoff_targets: List[str] = field(default_factory=list)
    failure_modes: List[str] = field(default_factory=list)
    default_budget: Budget = field(default_factory=Budget)
    fallback_behavior: str = "scan_only"      # "scan_only" | "skip" | "human"
    requires_env: List[str] = field(default_factory=list)
    notes: str = ""

    def can_call(self, tool_name: str) -> bool:
        """Tool gating. Empty allow-list = no tools (deterministic only)."""
        return tool_name in self.allowed_tools

    def can_handoff_to(self, agent_id: str) -> bool:
        return agent_id in self.handoff_targets

    def with_overrides(self, **kwargs) -> "AgentProfile":
        """Return a copy with selected fields overridden."""
        base = self.__dict__.copy()
        base.update(kwargs)
        return AgentProfile(**base)


# ---------------------------------------------------------------------------
# Default profiles for the 21 existing scientific agents.
#
# All start at DETERMINISTIC autonomy with empty allowed_tools — i.e. running
# AutonomousAgent.run() with one of these profiles produces the same output
# as the legacy BaseAgent.run(). Phase 4 raises autonomy_level + populates
# allowed_tools per agent.
# ---------------------------------------------------------------------------

_BUILT_IN_READS = (
    "memory_read", "memory_list", "registry_read", "registry_query",
    "file_read", "glob", "git_state", "env_snapshot", "hash_file",
)
_MEMORY_WRITE = ("memory_propose_update",)
_LLM = ("llm_chat",)
_WEB = ("web_fetch", "web_search")


def _profile(
    agent_id: str,
    *,
    capabilities: List[str],
    domain_areas: List[str],
    handoff_targets: List[str] = (),
    failure_modes: List[str] = (),
    notes: str = "",
) -> AgentProfile:
    return AgentProfile(
        agent_id=agent_id,
        capabilities=list(capabilities),
        allowed_tools=list(_BUILT_IN_READS),
        domain_areas=list(domain_areas),
        autonomy_level=AutonomyLevel.DETERMINISTIC,
        confidence_model="fixed",
        handoff_targets=list(handoff_targets),
        failure_modes=list(failure_modes),
        default_budget=Budget(),
        fallback_behavior="scan_only",
        requires_env=[],
        notes=notes,
    )


DEFAULT_PROFILES: Dict[str, AgentProfile] = {
    "master_orchestrator": _profile(
        "master_orchestrator",
        capabilities=["summarize_routing"],
        domain_areas=["orchestration"],
        notes="Graph-view role only; never directly routed.",
    ),
    "context_source_truth": _profile(
        "context_source_truth",
        capabilities=["read_canonical_memory", "git_state"],
        domain_areas=["context"],
        handoff_targets=["provenance_artifacts", "contradiction_hunter"],
        failure_modes=["memory_missing"],
        notes="Always runs first; provides source of truth for downstream agents.",
    ),
    "research_design": _profile(
        "research_design",
        capabilities=["audit_hypothesis", "falsifier_check"],
        domain_areas=["research_design"],
        handoff_targets=["biological_realism", "literature_web", "validation_skeptic"],
    ),
    "biological_realism": _profile(
        "biological_realism",
        capabilities=["claim_biology_check", "residue_plausibility"],
        domain_areas=["biology"],
        handoff_targets=["validation_skeptic", "paper_claim", "contradiction_hunter"],
        failure_modes=["disallowed_wording"],
    ),
    "literature_web": _profile(
        "literature_web",
        capabilities=["literature_search", "source_count", "gap_analysis"],
        domain_areas=["literature"],
        handoff_targets=["document_knowledge_ingestion", "research_design",
                         "context_source_truth"],
        failure_modes=["empty_source_registry", "network_unavailable"],
        notes="Phase 4 candidate for FULL autonomy + RESEARCHOS_ENABLE_WEB.",
    ),
    "dataset_integrity": _profile(
        "dataset_integrity",
        capabilities=["dataset_audit", "label_definition_check"],
        domain_areas=["data"],
        handoff_targets=["leakage_split", "preprocessing_auditor", "provenance_artifacts"],
    ),
    "leakage_split": _profile(
        "leakage_split",
        capabilities=["leakage_audit", "split_protocol_check"],
        domain_areas=["data", "evaluation"],
        handoff_targets=["dataset_integrity", "metrics_statistics", "provenance_artifacts"],
        failure_modes=["no_split_protocol"],
    ),
    "preprocessing_auditor": _profile(
        "preprocessing_auditor",
        capabilities=["preprocessing_audit", "graph_check"],
        domain_areas=["data"],
        handoff_targets=["dataset_integrity", "scientific_code_review"],
    ),
    "code_builder": _profile(
        "code_builder",
        capabilities=["patch_plan", "scaffold_module", "compatibility_patch"],
        domain_areas=["engineering"],
        handoff_targets=["scientific_code_review", "testing_environment", "provenance_artifacts"],
        failure_modes=["disallowed_path", "review_required"],
        notes="Phase 4 candidate for ASSISTED autonomy + safe patch-then-review.",
    ),
    "scientific_code_review": _profile(
        "scientific_code_review",
        capabilities=["code_review", "suspicious_pattern_scan"],
        domain_areas=["engineering"],
        handoff_targets=["code_builder", "testing_environment", "preprocessing_auditor"],
    ),
    "testing_environment": _profile(
        "testing_environment",
        capabilities=["pytest_run", "env_check", "reproducibility_audit"],
        domain_areas=["engineering", "reproducibility"],
        handoff_targets=["scientific_code_review", "provenance_artifacts"],
        failure_modes=["pytest_failure", "missing_critical_dep"],
    ),
    "model_training": _profile(
        "model_training",
        capabilities=["training_history", "checkpoint_audit"],
        domain_areas=["training"],
        handoff_targets=["metrics_statistics", "leakage_split", "provenance_artifacts"],
    ),
    "metrics_statistics": _profile(
        "metrics_statistics",
        capabilities=["metric_audit", "uncertainty_check", "ci_check"],
        domain_areas=["evaluation"],
        handoff_targets=["leakage_split", "contradiction_hunter", "provenance_artifacts"],
    ),
    "compute_planning": _profile(
        "compute_planning",
        capabilities=["compute_budget", "expensive_run_gate"],
        domain_areas=["compute"],
        handoff_targets=["validation_skeptic", "model_training"],
    ),
    "validation_skeptic": _profile(
        "validation_skeptic",
        capabilities=["md_evidence_classification", "validation_status_audit"],
        domain_areas=["validation", "md"],
        handoff_targets=["biological_realism", "metrics_statistics", "paper_claim",
                         "provenance_artifacts"],
        failure_modes=["inconclusive_evidence"],
    ),
    "contradiction_hunter": _profile(
        "contradiction_hunter",
        capabilities=["contradiction_sweep", "claim_evidence_cross_check"],
        domain_areas=["validation", "claims"],
        handoff_targets=["paper_claim", "leakage_split", "metrics_statistics",
                         "validation_skeptic"],
    ),
    "provenance_artifacts": _profile(
        "provenance_artifacts",
        capabilities=["artifact_audit", "stale_detection", "lineage_walk"],
        domain_areas=["provenance"],
        handoff_targets=["dataset_integrity", "model_training", "visual_evidence"],
    ),
    "paper_claim": _profile(
        "paper_claim",
        capabilities=["claim_audit", "paper_wording_check", "safe_wording_propose"],
        domain_areas=["claims", "writing"],
        handoff_targets=["biological_realism", "validation_skeptic",
                         "contradiction_hunter", "reviewer_collaboration"],
        failure_modes=["disallowed_wording"],
    ),
    "visual_evidence": _profile(
        "visual_evidence",
        capabilities=["figure_audit", "axis_check"],
        domain_areas=["figures"],
        handoff_targets=["paper_claim", "metrics_statistics"],
    ),
    "reviewer_collaboration": _profile(
        "reviewer_collaboration",
        capabilities=["reviewer_simulation", "risk_register_update"],
        domain_areas=["peer_review"],
        handoff_targets=["paper_claim", "contradiction_hunter"],
    ),
    "document_knowledge_ingestion": _profile(
        "document_knowledge_ingestion",
        capabilities=["document_ingest", "source_registry_update"],
        domain_areas=["literature"],
        handoff_targets=["literature_web", "context_source_truth", "provenance_artifacts"],
        notes="Phase 4 candidate for ASSISTED autonomy + actual ingest invocation.",
    ),
}


def profile_for(agent_id: str) -> AgentProfile:
    """Return the default profile for an agent, or a minimal one if unknown.

    Unknown agent IDs get a maximally-restrictive profile (no tools, no
    handoffs) so opting a new agent into autonomy is an explicit step.
    """
    if agent_id in DEFAULT_PROFILES:
        return DEFAULT_PROFILES[agent_id]
    return AgentProfile(
        agent_id=agent_id,
        capabilities=[],
        allowed_tools=[],
        domain_areas=[],
        autonomy_level=AutonomyLevel.DETERMINISTIC,
        fallback_behavior="scan_only",
        notes="Auto-generated minimal profile for unregistered agent.",
    )


__all__ = ["AgentProfile", "AutonomyLevel", "DEFAULT_PROFILES", "profile_for"]
