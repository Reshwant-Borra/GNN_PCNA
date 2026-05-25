"""Markdown memory layer.

The canonical memory is human-readable markdown that lives in
`research_os_memory/`. Agents propose updates via `MemoryUpdateProposal`;
the orchestrator validates and applies through `MemoryStore`.

The KB sub-layer (registry_loader, codebase_indexer) handles a second set of
markdown files (AGENT_REGISTRY, ROUTING_GUIDE, CODEBASE_MAP, etc.) that act
as a token-efficient knowledge base for the semantic router and human readers.
"""

from research_os.memory.store import (
    CANONICAL_FILES,
    MemoryStore,
    MemoryUpdateProposal,
    apply_memory_update,
    ensure_memory_initialized,
)
from research_os.memory.registry_loader import (
    KB_FILES,
    AgentEntry,
    RoutingCategory,
    load_agent_registry,
    load_routing_guide,
    query_memory,
)
from research_os.memory.codebase_indexer import regenerate_codebase_map

__all__ = [
    "CANONICAL_FILES",
    "MemoryStore",
    "MemoryUpdateProposal",
    "apply_memory_update",
    "ensure_memory_initialized",
    "KB_FILES",
    "AgentEntry",
    "RoutingCategory",
    "load_agent_registry",
    "load_routing_guide",
    "query_memory",
    "regenerate_codebase_map",
]
