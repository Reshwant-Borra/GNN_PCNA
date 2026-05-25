"""Parse the KB memory files (AGENT_REGISTRY.md, ROUTING_GUIDE.md, etc.) into
Python dicts that the semantic router and dashboard can consume.

These files are markdown by design (so humans can edit them in Obsidian), but
the structure is regular enough to parse without YAML or JSON. We cache parses
in-process — the files are small (~3-5k tokens) and read on every routing call.

Files are expected at ``<repo_root>/research_os_memory/<NAME>.md``.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


KB_DIR_NAME = "research_os_memory"

AGENT_REGISTRY_FILE = "AGENT_REGISTRY.md"
ROUTING_GUIDE_FILE = "ROUTING_GUIDE.md"
CODEBASE_MAP_FILE = "CODEBASE_MAP.md"
WORKFLOW_REGISTRY_FILE = "WORKFLOW_REGISTRY.md"
TOOL_REGISTRY_FILE = "TOOL_REGISTRY.md"
RECENT_RUN_SUMMARY_FILE = "RECENT_RUN_SUMMARY.md"

KB_FILES = (
    AGENT_REGISTRY_FILE,
    ROUTING_GUIDE_FILE,
    CODEBASE_MAP_FILE,
    WORKFLOW_REGISTRY_FILE,
    TOOL_REGISTRY_FILE,
    RECENT_RUN_SUMMARY_FILE,
)


@dataclass
class AgentEntry:
    """One agent's entry parsed from AGENT_REGISTRY.md."""
    agent_id: str
    name: str = ""
    purpose: str = ""
    when_to_use: str = ""
    when_not_to_use: str = ""
    example_prompts: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    required_gates: List[str] = field(default_factory=list)
    typical_outputs: str = ""
    risk_level: str = "medium"
    related_agents: List[str] = field(default_factory=list)
    workflows: List[str] = field(default_factory=list)


@dataclass
class RoutingCategory:
    """One category parsed from ROUTING_GUIDE.md."""
    name: str
    always_include: List[str] = field(default_factory=list)
    examples: List[Dict[str, object]] = field(default_factory=list)  # {prompt, agents}
    notes: str = ""


# In-process cache, keyed by (path, content_hash)
_CACHE: Dict[str, object] = {}


def _kb_dir(repo_root: "str | Path") -> Path:
    return Path(repo_root) / KB_DIR_NAME


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def _strip_inline_md(s: str) -> str:
    """Strip markdown inline noise (backticks, **bold**) without parsing fully."""
    s = re.sub(r"`([^`]*)`", r"\1", s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"\1", s)
    return s.strip()


def _split_list(value: str) -> List[str]:
    """Split a comma-separated value, stripping whitespace and surrounding quotes."""
    if not value:
        return []
    parts = [p.strip().strip('"').strip("'") for p in value.split(",")]
    return [p for p in parts if p and p.lower() != "none"]


def parse_agent_registry(text: str) -> Dict[str, AgentEntry]:
    """Parse AGENT_REGISTRY.md into {agent_id: AgentEntry}.

    Format expected per agent:

        ### <agent_id>
        - name: <...>
        - purpose: <...>
        - when_to_use: <...>
        ...

    Lines starting with ``- <key>:`` set fields. Anything else is ignored.
    """
    entries: Dict[str, AgentEntry] = {}
    current: Optional[AgentEntry] = None

    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        # Agent header (### agent_id)
        m = re.match(r"^###\s+([a-z_][a-z0-9_]*)\s*$", line)
        if m:
            current = AgentEntry(agent_id=m.group(1))
            entries[current.agent_id] = current
            continue
        if current is None:
            continue
        # Field line: "- key: value" or "- key: ..."
        fm = re.match(r"^\s*-\s+([a-z_]+)\s*:\s*(.*)$", line)
        if not fm:
            continue
        key = fm.group(1).strip().lower()
        value = _strip_inline_md(fm.group(2).strip())

        if key == "name":
            current.name = value
        elif key == "purpose":
            current.purpose = value
        elif key == "when_to_use":
            current.when_to_use = value
        elif key == "when_not_to_use":
            current.when_not_to_use = value
        elif key == "example_prompts":
            # Examples are quoted, comma-separated
            current.example_prompts = re.findall(r'"([^"]+)"', value) or _split_list(value)
        elif key == "keywords":
            current.keywords = _split_list(value)
        elif key == "required_gates":
            current.required_gates = _split_list(value)
        elif key == "typical_outputs":
            current.typical_outputs = value
        elif key == "risk_level":
            current.risk_level = value.lower() or "medium"
        elif key == "related_agents":
            current.related_agents = _split_list(value)
        elif key == "workflows":
            current.workflows = _split_list(value)

    return entries


def parse_routing_guide(text: str) -> List[RoutingCategory]:
    """Parse ROUTING_GUIDE.md into a list of RoutingCategory.

    Section delimiter: ``## Category:`` headings.
    """
    categories: List[RoutingCategory] = []
    sections = re.split(r"^##\s+Category:\s*", text, flags=re.MULTILINE)
    # First chunk is the preamble before any category — discard.
    for chunk in sections[1:]:
        # First line of chunk is the category name; rest is body.
        first_nl = chunk.find("\n")
        name = chunk[:first_nl].strip() if first_nl >= 0 else chunk.strip()
        body = chunk[first_nl:] if first_nl >= 0 else ""
        cat = RoutingCategory(name=name)

        # Extract "Always include: ..." lists. Be tolerant of bolded labels.
        ai_match = re.search(
            r"(?:\*\*)?Always include:?(?:\*\*)?\s*(.+?)(?=\n\n|\Z)",
            body, re.IGNORECASE | re.DOTALL,
        )
        if ai_match:
            raw = _strip_inline_md(ai_match.group(1))
            cat.always_include = re.findall(r"[a-z_]{3,}", raw)

        # Extract bullet examples that pair a prompt with an arrow → agents
        for ex in re.finditer(
            r'"([^"]+)"[^\n]*?\n[^\n]*?(?:→|->)\s*[`]?([a-z_,\s]+)[`]?',
            body, re.IGNORECASE,
        ):
            prompt = ex.group(1)
            agents = re.findall(r"[a-z_]{3,}", ex.group(2))
            cat.examples.append({"prompt": prompt, "agents": agents})

        categories.append(cat)
    return categories


def load_agent_registry(repo_root: "str | Path" = ".") -> Dict[str, AgentEntry]:
    """Load and cache the parsed AGENT_REGISTRY.md."""
    path = _kb_dir(repo_root) / AGENT_REGISTRY_FILE
    text = _read(path)
    cache_key = f"agent_registry:{path}:{_hash(text)}"
    cached = _CACHE.get(cache_key)
    if cached is not None:
        return cached  # type: ignore[return-value]
    parsed = parse_agent_registry(text)
    _CACHE[cache_key] = parsed
    return parsed


def load_routing_guide(repo_root: "str | Path" = ".") -> List[RoutingCategory]:
    """Load and cache the parsed ROUTING_GUIDE.md."""
    path = _kb_dir(repo_root) / ROUTING_GUIDE_FILE
    text = _read(path)
    cache_key = f"routing_guide:{path}:{_hash(text)}"
    cached = _CACHE.get(cache_key)
    if cached is not None:
        return cached  # type: ignore[return-value]
    parsed = parse_routing_guide(text)
    _CACHE[cache_key] = parsed
    return parsed


def query_memory(repo_root: "str | Path", topic: str, max_chars: int = 4000) -> List[Dict[str, str]]:
    """Grep across the KB markdown files for ``topic`` (case-insensitive).

    Returns a list of ``{file, snippet}`` dicts, one per matching file. ``snippet``
    is the matching line plus ~3 lines of surrounding context, truncated to
    ``max_chars`` total per file.
    """
    if not topic.strip():
        return []
    needle = topic.strip().lower()
    results: List[Dict[str, str]] = []
    kb = _kb_dir(repo_root)
    if not kb.exists():
        return results
    for md in sorted(kb.glob("*.md")):
        text = _read(md)
        if needle not in text.lower():
            continue
        lines = text.splitlines()
        hits: List[str] = []
        for i, line in enumerate(lines):
            if needle in line.lower():
                start = max(0, i - 2)
                end = min(len(lines), i + 3)
                hits.append("\n".join(lines[start:end]))
            if sum(len(h) for h in hits) > max_chars:
                break
        if hits:
            results.append({"file": md.name, "snippet": "\n---\n".join(hits)[:max_chars]})
    return results


__all__ = [
    "AGENT_REGISTRY_FILE",
    "ROUTING_GUIDE_FILE",
    "CODEBASE_MAP_FILE",
    "WORKFLOW_REGISTRY_FILE",
    "TOOL_REGISTRY_FILE",
    "RECENT_RUN_SUMMARY_FILE",
    "KB_FILES",
    "AgentEntry",
    "RoutingCategory",
    "parse_agent_registry",
    "parse_routing_guide",
    "load_agent_registry",
    "load_routing_guide",
    "query_memory",
]
