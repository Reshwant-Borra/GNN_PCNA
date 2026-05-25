"""Filesystem, git, hashing, environment, and dependency-graph helpers.

These are pure utilities — no agent logic, no orchestration. Other modules pull
from here.
"""
from research_os.tools.git import (
    GitState,
    capture_git_state,
    is_inside_git_repo,
)
from research_os.tools.hashing import (
    file_hash,
    directory_hash,
    text_hash,
)
from research_os.tools.environment import (
    EnvironmentSnapshot,
    capture_environment,
)
from research_os.tools.dependency_graph import (
    propagate_stale,
    direct_downstream,
)
from research_os.tools.provenance import (
    ProvenanceRecord,
    capture_provenance,
)

__all__ = [
    "EnvironmentSnapshot",
    "GitState",
    "ProvenanceRecord",
    "capture_environment",
    "capture_git_state",
    "capture_provenance",
    "direct_downstream",
    "directory_hash",
    "file_hash",
    "is_inside_git_repo",
    "propagate_stale",
    "text_hash",
]
