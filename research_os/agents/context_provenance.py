"""Context source-of-truth, Provenance, and Contradiction Hunter agents.

These three are read-only audit agents. They never approve other agents'
work; they assemble and verify the canonical state that every other agent
depends on.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from research_os.agents.base import BaseAgent, GateName
from research_os.memory.store import CANONICAL_FILES
from research_os.schemas.context import ContextPacket
from research_os.schemas.core import AgentOutput
from research_os.tools.git import capture_git_state


class ContextSourceTruthAgent(BaseAgent):
    agent_id = "context_source_truth"
    display_name = "Context and Source-of-Truth"

    def run(self, packet: ContextPacket) -> AgentOutput:
        evidence = []
        findings = []
        notes: Dict[str, Any] = {}

        mem = self.ctx.memory_store
        if mem is None:
            findings.append(
                self._new_finding(
                    severity="high",
                    title="No memory store attached — context cannot be summarized",
                    description="Initialize research_os_memory/ before running workflows.",
                    blocks_pipeline=True,
                )
            )
            return self._output(
                task=packet.task,
                status="blocked",
                confidence=0.9,
                summary="No memory store available; cannot summarize source of truth.",
                findings=findings,
                required_actions=["Run `python -m research_os audit --repo .` once to seed memory."],
            )

        present = []
        missing = []
        for name in CANONICAL_FILES:
            if mem.exists(name):
                present.append(name)
                evidence.append(self._evidence_memory(name, "canonical state"))
            else:
                missing.append(name)

        needs_review = []
        for name in present:
            try:
                f = mem.read(name)
            except Exception:
                continue
            if f.status != "current":
                needs_review.append((name, f.status, f.last_updated))

        if missing:
            findings.append(
                self._new_finding(
                    severity="high",
                    title=f"{len(missing)} canonical memory files missing",
                    description="Missing: " + ", ".join(missing),
                    required_action="Run bootstrap to create the missing files.",
                    blocks_pipeline=True,
                )
            )
        for name, status, ts in needs_review:
            findings.append(
                self._new_finding(
                    severity="medium" if status == "needs_review" else "high",
                    title=f"{name} status={status}",
                    description=f"Last updated {ts or 'unknown'} — content should be re-confirmed.",
                    required_action=f"Have an authoritative agent refresh {name} and set status=current.",
                )
            )

        git = capture_git_state(self.ctx.repo_root)
        notes["git"] = git.to_dict()
        if git.inside_repo and git.dirty:
            findings.append(
                self._new_finding(
                    severity="low",
                    title="Working tree is dirty",
                    description=(
                        f"{git.modified_count} modified, {git.untracked_count} untracked. "
                        "Provenance for any outputs produced now will record git_dirty=true."
                    ),
                )
            )

        summary = (
            f"{len(present)} of {len(CANONICAL_FILES)} canonical files present; "
            f"{len(needs_review)} need review. "
            f"git={git.short_commit} branch={git.branch} dirty={git.dirty}."
        )

        status = "pass" if not findings else "warning"
        if any(f.blocks_pipeline for f in findings):
            status = "fail"

        return self._output(
            task=packet.task,
            status=status,
            confidence=0.9,
            summary=summary,
            evidence_used=evidence,
            findings=findings,
            notes=notes,
            next_recommended_agents=["contradiction_hunter", "provenance_artifacts"],
        )


class ProvenanceArtifactsAgent(BaseAgent):
    agent_id = "provenance_artifacts"
    display_name = "Provenance, Versioning and Artifact"

    def run(self, packet: ContextPacket) -> AgentOutput:
        findings = []
        gate_updates = []
        evidence = []
        artifacts_to_mark_stale: List[str] = []
        notes: Dict[str, Any] = {}

        store = self.ctx.registry_store
        if store is None:
            findings.append(
                self._new_finding(
                    severity="high",
                    title="No registry store attached — provenance cannot be evaluated",
                    blocks_pipeline=True,
                )
            )
            return self._output(
                task=packet.task,
                status="blocked",
                confidence=0.9,
                summary="No registry store available.",
                findings=findings,
            )

        entries = store.all_entries("artifact_registry")
        notes["artifact_count"] = len(entries)
        if not entries:
            findings.append(
                self._new_finding(
                    severity="medium",
                    title="Artifact registry is empty",
                    description="No outputs have been registered; provenance gate cannot pass.",
                    required_action="Register checkpoints, predictions, metrics, MD outputs, and figures.",
                )
            )
            gate_updates.append(self._gate(GateName.CODE, "warning", "no artifacts registered"))
        for entry in entries:
            aid = entry.get("artifact_id", "?")
            missing: List[str] = []
            for field in ("git_commit", "command", "created_at"):
                if not entry.get(field):
                    missing.append(field)
            artifact_type = entry.get("artifact_type")
            paper_grade_types = {"checkpoint", "metric", "md_analysis", "figure", "table", "report"}
            if artifact_type in paper_grade_types and missing:
                findings.append(
                    self._new_finding(
                        severity="high",
                        title=f"Artifact {aid} missing provenance fields: {missing}",
                        description=(
                            f"Type={artifact_type} is paper-grade and must record git_commit, "
                            "command, and timestamp."
                        ),
                        evidence=[self._evidence_registry("artifact_registry", aid)],
                        required_action=f"Update artifact {aid} with full provenance.",
                        affected_artifacts=[aid],
                    )
                )

            # If a paper-grade artifact is current but a dependency is stale/invalid,
            # surface that as a contradiction.
            if artifact_type in paper_grade_types and entry.get("status") == "current":
                for dep in entry.get("dependencies", []) or []:
                    dep_entry = store.get("artifact_registry", dep)
                    if dep_entry and dep_entry.get("status") in ("stale", "invalid"):
                        artifacts_to_mark_stale.append(aid)
                        findings.append(
                            self._new_finding(
                                severity="critical",
                                title=f"Artifact {aid} claims current but depends on {dep_entry.get('status')} upstream",
                                description=f"Upstream artifact {dep} is {dep_entry.get('status')}.",
                                affected_artifacts=[aid, dep],
                                required_action=f"Mark {aid} stale and regenerate from refreshed inputs.",
                                blocks_pipeline=True,
                            )
                        )

        status = "pass"
        if any(f.severity == "critical" for f in findings):
            status = "fail"
        elif findings:
            status = "warning"

        return self._output(
            task=packet.task,
            status=status,
            confidence=0.85,
            summary=(
                f"Reviewed {len(entries)} artifact entries; "
                f"{len(findings)} provenance findings; "
                f"{len(artifacts_to_mark_stale)} artifacts should be marked stale."
            ),
            evidence_used=evidence,
            findings=findings,
            gate_updates=gate_updates,
            artifacts_to_mark_stale=artifacts_to_mark_stale,
            notes=notes,
        )


_DISALLOWED_WORDING = (
    "validated cryptic pocket",
    "confirmed novel residues",
    "MD proves opening",
    "MD validates",
    "discovered binding site",
    "generalizes broadly",
    "experimentally validated",
    "causal mechanism",
    "proved",
)


class ContradictionHunterAgent(BaseAgent):
    agent_id = "contradiction_hunter"
    display_name = "Contradiction and Error Hunter"

    def run(self, packet: ContextPacket) -> AgentOutput:
        findings: List = []
        evidence = []
        notes: Dict[str, Any] = {}

        mem = self.ctx.memory_store
        registry = self.ctx.registry_store

        # 1. Validation says inconclusive/weakens, but a claim is strongly_supported.
        if mem is not None and mem.exists("VALIDATION_STATUS.md") and registry is not None:
            vstatus = mem.read("VALIDATION_STATUS.md").body
            evidence.append(self._evidence_memory("VALIDATION_STATUS.md"))
            classification = self._extract_classification(vstatus)
            notes["validation_classification"] = classification
            claims = registry.all_entries("claim_registry")
            for c in claims:
                if c.get("claim_strength") in ("strongly_supported_computationally", "proven_experimentally"):
                    if classification in ("inconclusive", "weakens_claim", "contradicts_claim"):
                        findings.append(
                            self._new_finding(
                                severity="critical",
                                title=f"Claim {c.get('claim_id')} strength conflicts with validation status",
                                description=(
                                    f"Claim strength={c.get('claim_strength')} but validation "
                                    f"classification={classification}."
                                ),
                                evidence=[
                                    self._evidence_memory("VALIDATION_STATUS.md"),
                                    self._evidence_registry("claim_registry", c.get("claim_id", "?")),
                                ],
                                affected_claims=[c.get("claim_id", "?")],
                                required_action="Downgrade the claim or strengthen the validation evidence.",
                                blocks_pipeline=True,
                            )
                        )

        # 2. Paper drafts in repo containing disallowed wording.
        repo_root = Path(self.ctx.repo_root)
        for draft in self._scan_paper_drafts(repo_root):
            text = draft.read_text(encoding="utf-8", errors="ignore")
            for phrase in _DISALLOWED_WORDING:
                if re.search(rf"\b{re.escape(phrase)}\b", text, re.IGNORECASE):
                    findings.append(
                        self._new_finding(
                            severity="high",
                            title=f"Disallowed phrase '{phrase}' in {draft.name}",
                            description=f"Phrase appears in {draft}",
                            evidence=[self._evidence_path(str(draft.relative_to(repo_root)))],
                            required_action="Replace with safe wording approved by the Claim agent.",
                        )
                    )

        # 3. Artifact registry: current artifacts whose dependencies are stale/invalid.
        if registry is not None:
            for entry in registry.all_entries("artifact_registry"):
                if entry.get("status") != "current":
                    continue
                for dep in entry.get("dependencies", []) or []:
                    dep_entry = registry.get("artifact_registry", dep)
                    if dep_entry and dep_entry.get("status") in ("stale", "invalid"):
                        findings.append(
                            self._new_finding(
                                severity="critical",
                                title=f"{entry.get('artifact_id')} current but {dep} is {dep_entry.get('status')}",
                                description="Downstream artifact must be marked stale and regenerated.",
                                affected_artifacts=[entry.get("artifact_id", "?"), dep],
                                blocks_pipeline=True,
                            )
                        )

        status = "pass"
        if any(f.severity in ("critical", "high") for f in findings):
            status = "fail" if any(f.severity == "critical" for f in findings) else "warning"
        elif findings:
            status = "warning"

        return self._output(
            task=packet.task,
            status=status,
            confidence=0.85,
            summary=f"Contradiction sweep produced {len(findings)} findings.",
            evidence_used=evidence,
            findings=findings,
            notes=notes,
        )

    def _extract_classification(self, body: str) -> str:
        m = re.search(
            r"Evidence classification[^\n]*\n+\W*`?([a-z_]+)`?",
            body,
            re.IGNORECASE,
        )
        return m.group(1) if m else "inconclusive"

    def _scan_paper_drafts(self, repo_root: Path) -> List[Path]:
        candidates: List[Path] = []
        for pattern in ("*.md", "**/*.md"):
            for p in repo_root.glob(pattern):
                # Skip docs/ and research_os/ memory; only look at manuscript-shaped files.
                rel = str(p.relative_to(repo_root)).lower()
                if rel.startswith(("docs", "research_os", ".git", "research_os_memory")):
                    continue
                if any(token in p.name.lower() for token in ("manuscript", "paper", "abstract", "draft")):
                    candidates.append(p)
        return sorted(set(candidates))


__all__ = [
    "ContextSourceTruthAgent",
    "ContradictionHunterAgent",
    "ProvenanceArtifactsAgent",
]
