"""Communication agents: CodeBuilder, PaperClaim, VisualEvidence, ReviewerCollaboration."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List

from research_os.agents.base import BaseAgent, GateName, any_phrase_in_text
from research_os.schemas.context import ContextPacket
from research_os.schemas.core import AgentOutput


class CodeBuilderAgent(BaseAgent):
    agent_id = "code_builder"
    display_name = "Code Builder and Refactor"

    def run(self, packet: ContextPacket) -> AgentOutput:
        # The MVP code builder reports a plan rather than mutating the repo. Real
        # implementation happens in interactive sessions where the agent has a
        # filesystem mutation channel.
        return self._output(
            task=packet.task,
            status="pass",
            confidence=0.6,
            summary="Code Builder defers: in audit context, only proposes the patch plan.",
            required_actions=[
                "Run interactively with explicit file allowlist before mutating the repo.",
                "Hand patches to Scientific Code Review and Testing before merge.",
            ],
        )


_DISALLOWED_PAPER_WORDING = (
    "validated cryptic pocket",
    "confirmed novel residues",
    "MD proves opening",
    "MD validates",
    "discovered binding site",
    "generalizes broadly",
    "experimentally validated",
    "causal mechanism",
)


class PaperClaimAgent(BaseAgent):
    agent_id = "paper_claim"
    display_name = "Paper, Claim and Documentation"

    PAPER_HINTS = ("manuscript", "paper", "abstract", "draft", "results", "discussion")

    def run(self, packet: ContextPacket) -> AgentOutput:
        findings = []
        gate_updates = []
        evidence = []

        repo_root = Path(self.ctx.repo_root)
        draft_files = [
            p for p in repo_root.rglob("*.md")
            if any(
                hint in p.name.lower() for hint in self.PAPER_HINTS
            )
            and not any(
                part in {".git", "research_os", "research_os_memory", "research_os_registries", "reports", "docs"}
                for part in p.parts
            )
        ]
        for d in draft_files:
            text = d.read_text(encoding="utf-8", errors="ignore")
            for phrase in any_phrase_in_text(_DISALLOWED_PAPER_WORDING, text):
                findings.append(
                    self._new_finding(
                        severity="high",
                        title=f"Disallowed phrase in {d.relative_to(repo_root)}: '{phrase}'",
                        description="Replace with safe wording before the Claim gate can pass.",
                        evidence=[self._evidence_path(str(d.relative_to(repo_root)))],
                        required_action="Use approved candidate-region phrasing.",
                    )
                )
            evidence.append(self._evidence_path(str(d.relative_to(repo_root))))

        # Also check claim registry consistency.
        store = self.ctx.registry_store
        if store is not None:
            for c in store.all_entries("claim_registry"):
                if not c.get("allowed_wording"):
                    findings.append(
                        self._new_finding(
                            severity="medium",
                            title=f"Claim {c.get('claim_id')} has no allowed_wording list",
                            description="Without allowed wording, paper text cannot be safely produced.",
                            affected_claims=[c.get("claim_id", "?")],
                        )
                    )
                if not c.get("disallowed_wording"):
                    findings.append(
                        self._new_finding(
                            severity="low",
                            title=f"Claim {c.get('claim_id')} has no disallowed_wording list",
                        )
                    )

        gate_status = (
            "fail" if any(f.severity == "critical" for f in findings) else
            ("warning" if findings else "pass")
        )
        gate_updates.append(self._gate(GateName.CLAIM, gate_status))

        return self._output(
            task=packet.task,
            status="warning" if findings else "pass",
            confidence=0.8,
            summary=(
                f"Paper/Claim audit: scanned {len(draft_files)} draft files; "
                f"{len(findings)} findings."
            ),
            evidence_used=evidence,
            findings=findings,
            gate_updates=gate_updates,
        )


class VisualEvidenceAgent(BaseAgent):
    agent_id = "visual_evidence"
    display_name = "Visual Evidence and Figure"

    def run(self, packet: ContextPacket) -> AgentOutput:
        findings = []
        repo_root = Path(self.ctx.repo_root)
        figure_files: List[Path] = []
        for ext in ("*.png", "*.pdf", "*.svg", "*.jpg"):
            for p in repo_root.rglob(ext):
                if any(
                    part in {".git", "research_os_memory", "research_os_registries", "reports", "docs"}
                    for part in p.parts
                ):
                    continue
                figure_files.append(p)

        store = self.ctx.registry_store
        registered_paths = set()
        if store is not None:
            for entry in store.find(
                "artifact_registry", lambda e: e.get("artifact_type") == "figure"
            ):
                registered_paths.add(entry.get("path"))
        unregistered = [
            str(p.relative_to(repo_root)) for p in figure_files if str(p) not in registered_paths
        ]
        if unregistered:
            findings.append(
                self._new_finding(
                    severity="medium",
                    title=f"{len(unregistered)} figure files not registered as artifacts",
                    description="A figure that supports a paper claim must have a provenance entry.",
                    required_action="Register figures via the artifact registry.",
                )
            )
        return self._output(
            task=packet.task,
            status="warning" if findings else "pass",
            confidence=0.6,
            summary=f"Figure audit: {len(figure_files)} files on disk, {len(unregistered)} unregistered.",
            findings=findings,
            gate_updates=[self._gate(GateName.FIGURE, "warning" if findings else "pass")],
            notes={"figures_on_disk": len(figure_files), "unregistered": len(unregistered)},
        )


_REVIEWER_QUESTIONS = (
    "How did you prevent homology leakage?",
    "How many independent test proteins?",
    "Why is AUROC meaningful here?",
    "Where is AUPRC and what is the positive-class baseline?",
    "Did MD actually validate the prediction, or only simulation stability?",
    "Are novel residues experimentally supported?",
    "Were old checkpoints regenerated after bug fixes?",
    "Can the repo run from scratch?",
    "Are skipped tests hiding failures?",
    "Are claims proportional to evidence?",
    "Is the test set independent at the protein level (not residue level)?",
    "Were baselines compared under the same leakage-clean split?",
)


class ReviewerCollaborationAgent(BaseAgent):
    agent_id = "reviewer_collaboration"
    display_name = "Reviewer and Collaboration"

    def run(self, packet: ContextPacket) -> AgentOutput:
        findings = []
        notes: Dict[str, Any] = {"reviewer_questions": list(_REVIEWER_QUESTIONS)}
        body = ""
        mem = self.ctx.memory_store
        if mem is not None and mem.exists("REVIEWER_RISK_REGISTER.md"):
            body = mem.read("REVIEWER_RISK_REGISTER.md").body
        open_risks: List[str] = []
        if body:
            m = re.search(r"##\s*Open reviewer risks(?P<body>.*?)(?=^##\s|\Z)", body, re.MULTILINE | re.DOTALL)
            if m:
                open_risks = [
                    line.strip("-* ").strip()
                    for line in m.group("body").splitlines()
                    if line.strip().startswith(("-", "*"))
                ]
        notes["open_reviewer_risks"] = open_risks
        if not open_risks:
            findings.append(
                self._new_finding(
                    severity="medium",
                    title="No documented open reviewer risks",
                    description="A pre-submission audit cannot pass with an empty reviewer-risk register.",
                )
            )
        return self._output(
            task=packet.task,
            status="warning" if findings else "pass",
            confidence=0.8,
            summary=f"Reviewer simulation: {len(_REVIEWER_QUESTIONS)} canonical questions, {len(open_risks)} open risks tracked.",
            findings=findings,
            notes=notes,
        )


__all__ = [
    "CodeBuilderAgent",
    "PaperClaimAgent",
    "ReviewerCollaborationAgent",
    "VisualEvidenceAgent",
]
