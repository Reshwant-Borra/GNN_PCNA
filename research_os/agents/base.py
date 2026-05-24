"""BaseAgent + AgentContext.

Every agent receives an `AgentContext` (the runtime stores it needs) and a
`ContextPacket` (the per-task brief) and returns an `AgentOutput`. Agents
never write to memory or registries directly — they emit `MemoryUpdate` /
`gate_updates` and the orchestrator applies them.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence


def phrase_in_text(phrase: str, text: str, *, gap: int = 2) -> bool:
    """Return True if ``phrase`` appears in ``text`` with up to ``gap`` extra
    interleaved words between each token of the phrase. This is intentionally
    loose so "discovered a binding site" still matches the disallowed
    phrase "discovered binding site"."""
    parts = re.split(r"\s+", phrase.strip())
    if not parts:
        return False
    between = rf"\s+(?:\w+\s+){{0,{gap}}}"
    pattern = r"\b" + between.join(re.escape(p) for p in parts) + r"\b"
    return bool(re.search(pattern, text, re.IGNORECASE))


def any_phrase_in_text(phrases: Sequence[str], text: str, *, gap: int = 2) -> List[str]:
    """Return the phrases that match within ``text``."""
    return [p for p in phrases if phrase_in_text(p, text, gap=gap)]

from research_os.memory.store import MemoryStore
from research_os.registries.store import RegistryStore
from research_os.schemas.context import ContextPacket
from research_os.schemas.core import (
    AgentOutput,
    EvidenceRef,
    Finding,
    GateUpdate,
    MemoryUpdate,
    Risk,
)
from research_os.schemas.gates import GateName


@dataclass
class AgentContext:
    """Runtime context handed to each agent. All fields are optional so agents
    can run in lightweight unit tests with empty stores."""

    repo_root: Path = field(default_factory=lambda: Path("."))
    memory_store: Optional[MemoryStore] = None
    registry_store: Optional[RegistryStore] = None
    reports_root: Path = field(default_factory=lambda: Path("reports/research_os"))
    fixtures: Dict[str, Any] = field(default_factory=dict)


def _next_finding_id(prefix: str, n: int) -> str:
    return f"{prefix}-{n:03d}"


class BaseAgent:
    """Subclasses override `agent_id`, `display_name`, and `run`.

    The base provides helpers to build evidence refs, findings, risks, gate
    updates, and to package the final AgentOutput.
    """

    agent_id: str = ""
    display_name: str = ""

    def __init__(self, ctx: AgentContext):
        self.ctx = ctx
        self._finding_counter = 0

    # ----- builders -----

    def _new_finding(
        self,
        *,
        severity: str,
        title: str,
        description: str = "",
        evidence: Optional[List[EvidenceRef]] = None,
        affected_claims: Optional[List[str]] = None,
        affected_artifacts: Optional[List[str]] = None,
        required_action: str = "",
        blocks_pipeline: bool = False,
    ) -> Finding:
        self._finding_counter += 1
        fid = _next_finding_id(self.agent_id.upper(), self._finding_counter)
        return Finding(
            finding_id=fid,
            severity=severity,
            title=title,
            description=description,
            evidence=list(evidence or []),
            affected_claims=list(affected_claims or []),
            affected_artifacts=list(affected_artifacts or []),
            required_action=required_action,
            blocks_pipeline=blocks_pipeline,
        )

    def _evidence_memory(self, name: str, description: str = "") -> EvidenceRef:
        path = ""
        if self.ctx.memory_store is not None:
            try:
                path = str(self.ctx.memory_store.path_for(name))
            except ValueError:
                path = ""
        return EvidenceRef(type="memory", id=name, path=path, description=description)

    def _evidence_registry(self, registry: str, entry_id: str, description: str = "") -> EvidenceRef:
        return EvidenceRef(
            type="registry", id=f"{registry}:{entry_id}", description=description
        )

    def _evidence_path(self, repo_path: str, description: str = "") -> EvidenceRef:
        return EvidenceRef(type="source_code", path=repo_path, description=description)

    def _evidence_artifact(self, artifact_id: str, description: str = "") -> EvidenceRef:
        return EvidenceRef(type="artifact", id=artifact_id, description=description)

    def _gate(self, name: str, status: str, reason: str = "") -> GateUpdate:
        return GateUpdate(gate=name, new_status=status, reason=reason)

    def _memory_update(
        self,
        *,
        target_file: str,
        update_type: str,
        summary: str,
        append_section: Optional[str] = None,
        section_heading: Optional[str] = None,
        new_body: Optional[str] = None,
        requires_human_approval: bool = False,
        reason_human_approval_required: str = "",
        evidence: Optional[List[str]] = None,
    ) -> MemoryUpdate:
        return MemoryUpdate(
            target_file=target_file,
            update_type=update_type,
            summary=summary,
            evidence=list(evidence or []),
            requires_human_approval=requires_human_approval,
            reason_human_approval_required=reason_human_approval_required,
        )

    def _output(
        self,
        *,
        task: str,
        status: str,
        confidence: float,
        summary: str,
        evidence_used: Optional[List[EvidenceRef]] = None,
        findings: Optional[List[Finding]] = None,
        risks: Optional[List[Risk]] = None,
        required_actions: Optional[List[str]] = None,
        gate_updates: Optional[List[GateUpdate]] = None,
        human_review_required: bool = False,
        human_review_reason: str = "",
        updates_to_memory: Optional[List[MemoryUpdate]] = None,
        artifacts_to_mark_stale: Optional[List[str]] = None,
        next_recommended_agents: Optional[List[str]] = None,
        notes: Optional[Dict[str, Any]] = None,
    ) -> AgentOutput:
        out = AgentOutput(
            agent=self.display_name,
            agent_id=self.agent_id,
            task=task,
            status=status,
            confidence=confidence,
            summary=summary,
            evidence_used=list(evidence_used or []),
            findings=list(findings or []),
            risks=list(risks or []),
            required_actions=list(required_actions or []),
            gate_updates=list(gate_updates or []),
            human_review_required=human_review_required,
            human_review_reason=human_review_reason,
            updates_to_memory=list(updates_to_memory or []),
            artifacts_to_mark_stale=list(artifacts_to_mark_stale or []),
            next_recommended_agents=list(next_recommended_agents or []),
            machine_readable_notes=dict(notes or {}),
        )
        out.validate()
        return out

    # ----- override -----

    def run(self, packet: ContextPacket) -> AgentOutput:  # pragma: no cover
        raise NotImplementedError


__all__ = [
    "AgentContext",
    "BaseAgent",
    "GateName",
    "any_phrase_in_text",
    "phrase_in_text",
]
