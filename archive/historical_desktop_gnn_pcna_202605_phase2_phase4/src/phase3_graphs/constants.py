"""Governed constants for Phase 3 graph generation.

All values here are approved by decision record:
  reports/phase3/graph_policy_human_decision_20260528.md
  decision_id: phase3_graph_policy_20260528
"""

from __future__ import annotations

from pathlib import Path

# Human-approved decision that authorizes graph generation
GRAPH_POLICY_DECISION_ID = "phase3_graph_policy_20260528"
GRAPH_POLICY_APPROVAL_PATH = Path("reports/phase3/graph_policy_human_decision_20260528.md")
GRAPH_POLICY_PACKET_PATH = Path(
    "reports/phase3/graph_edge_feature_policy_approval_packet_20260528.md"
)

# Approved CA-CA spatial edge cutoff (Angstrom), approved as written in policy packet
CA_CUTOFF_ANGSTROM: float = 8.0

# Edge type integer encoding (stored in edge_type array)
EDGE_TYPE_SPATIAL: int = 0
EDGE_TYPE_SEQUENTIAL: int = 1

# Output directories
GRAPHS_DIR = Path("data/graphs")

# Governance references required by 07_PREPROCESSING_AND_GRAPH_RULES.md
GOVERNANCE_PATHS = (
    "docs/scientific_governance/07_PREPROCESSING_AND_GRAPH_RULES.md",
    "docs/scientific_governance/08_MODEL_ARCHITECTURE_CONSTRAINTS.md",
    "docs/scientific_governance/15_PROVENANCE_AND_REPRODUCIBILITY.md",
    "docs/scientific_governance/19_STOP_CONDITIONS.md",
    "docs/scientific_governance/26_HUMAN_REVIEW_GATES.md",
)
