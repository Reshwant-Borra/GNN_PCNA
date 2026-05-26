"""Pre-built autonomous campaigns for ResearchOS.

A *campaign* is a high-level scientific objective expressed as a registered
function ``run(repo_root, mode="smoke") -> CampaignReport``. Campaigns:

- decompose a top-level Goal via the decomposer (or supply explicit sub-goals)
- run the AutonomousController with the migrated AUTONOMOUS_AGENTS registry
- optionally inject a domain-specific synthesis writer
- write deliverables to ``research_corpus/`` and ``reports/research_os/``

Two modes are supported by every campaign:

- ``smoke``: uses stub sources / fake LLM / no web — safe to run in tests + CI
- ``live``: uses real web + LLM if env vars are set; otherwise falls back to
  deterministic behavior on a per-agent basis
"""
from research_os.autonomous.campaigns.phase2_pcna import (
    PHASE2_GOAL_OBJECTIVE,
    Phase2CampaignReport,
    run_phase2_pcna,
)

CAMPAIGNS = {
    "phase2_pcna": run_phase2_pcna,
}


__all__ = [
    "CAMPAIGNS",
    "PHASE2_GOAL_OBJECTIVE",
    "Phase2CampaignReport",
    "run_phase2_pcna",
]
