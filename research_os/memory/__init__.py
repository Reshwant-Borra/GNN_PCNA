"""Markdown memory layer.

The canonical memory is human-readable markdown that lives in
`research_os_memory/`. Agents propose updates via `MemoryUpdateProposal`;
the orchestrator validates and applies through `MemoryStore`.
"""

from research_os.memory.store import (
    CANONICAL_FILES,
    MemoryStore,
    MemoryUpdateProposal,
    apply_memory_update,
    ensure_memory_initialized,
)

__all__ = [
    "CANONICAL_FILES",
    "MemoryStore",
    "MemoryUpdateProposal",
    "apply_memory_update",
    "ensure_memory_initialized",
]
