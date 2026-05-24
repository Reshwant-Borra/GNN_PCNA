"""Science / evaluation agents: ResearchDesign, BiologicalRealism, Literature,
Metrics, ModelTraining, ComputePlanning, ValidationSkeptic.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List

from research_os.agents.base import BaseAgent, GateName, any_phrase_in_text, phrase_in_text
from research_os.schemas.context import ContextPacket
from research_os.schemas.core import AgentOutput, EvidenceRef


def _memory_body(ctx, name: str) -> str:
    mem = ctx.memory_store
    if mem is None or not mem.exists(name):
        return ""
    return mem.read(name).body


class ResearchDesignAgent(BaseAgent):
    agent_id = "research_design"
    display_name = "Research Design and Falsification"

    REQUIRED_FIELDS = (
        "Current research question",
        "Current hypothesis",
    )
    RECOMMENDED_FIELDS = (
        "Null hypothesis",
        "Success criteria",
        "Failure criteria",
        "Falsification",
        "Controls",
        "Baselines",
    )

    def run(self, packet: ContextPacket) -> AgentOutput:
        body = _memory_body(self.ctx, "PROJECT_CANONICAL_STATUS.md")
        evidence = [self._evidence_memory("PROJECT_CANONICAL_STATUS.md")] if body else []
        findings = []
        for h in self.REQUIRED_FIELDS:
            if h.lower() not in body.lower():
                findings.append(
                    self._new_finding(
                        severity="high",
                        title=f"Research design missing required heading '{h}'",
                        required_action="Document this in PROJECT_CANONICAL_STATUS.md before training/claim work.",
                    )
                )
        for h in self.RECOMMENDED_FIELDS:
            if h.lower() not in body.lower():
                findings.append(
                    self._new_finding(
                        severity="medium",
                        title=f"Research design lacks '{h}'",
                        required_action="Add explicit falsifier / control language.",
                    )
                )
        gate_status = "fail" if any(f.severity == "high" for f in findings) else (
            "warning" if findings else "pass"
        )
        return self._output(
            task=packet.task,
            status="warning" if findings else "pass",
            confidence=0.7,
            summary=f"Research design audit: {len(findings)} findings.",
            evidence_used=evidence,
            findings=findings,
            gate_updates=[self._gate(GateName.RESEARCH_DESIGN, gate_status)],
        )


_BIO_DISALLOWED = (
    "validated cryptic pocket",
    "confirmed novel residues",
    "MD validates",
    "discovered binding site",
    "experimentally validated",
    "proved",
)


class BiologicalRealismAgent(BaseAgent):
    agent_id = "biological_realism"
    display_name = "Biological and Scientific Realism"

    def run(self, packet: ContextPacket) -> AgentOutput:
        findings = []
        claims_weakened: List[str] = []
        evidence = []

        store = self.ctx.registry_store
        if store is not None:
            for c in store.all_entries("claim_registry"):
                text = c.get("claim_text") or ""
                for phrase in any_phrase_in_text(_BIO_DISALLOWED, text):
                    findings.append(
                        self._new_finding(
                            severity="high",
                            title=f"Claim {c.get('claim_id')} uses biologically aggressive wording",
                            description=f"Phrase: '{phrase}'.",
                            evidence=[self._evidence_registry("claim_registry", c.get("claim_id", "?"))],
                            affected_claims=[c.get("claim_id", "?")],
                            required_action="Reword to safe candidate-region language.",
                        )
                    )
                    claims_weakened.append(c.get("claim_id", "?"))
                if (
                    c.get("claim_strength") == "strongly_supported_computationally"
                    and not c.get("evidence_for")
                ):
                    findings.append(
                        self._new_finding(
                            severity="critical",
                            title=f"Claim {c.get('claim_id')} is 'strongly_supported_computationally' with no evidence_for",
                            evidence=[self._evidence_registry("claim_registry", c.get("claim_id", "?"))],
                            affected_claims=[c.get("claim_id", "?")],
                            blocks_pipeline=True,
                        )
                    )

        return self._output(
            task=packet.task,
            status="warning" if findings else "pass",
            confidence=0.75,
            summary=f"Biological realism audit: {len(findings)} findings, {len(claims_weakened)} claims weakened.",
            evidence_used=evidence,
            findings=findings,
        )


class LiteratureWebAgent(BaseAgent):
    agent_id = "literature_web"
    display_name = "Deep Literature and Web Research"

    def run(self, packet: ContextPacket) -> AgentOutput:
        store = self.ctx.registry_store
        findings = []
        notes: Dict[str, Any] = {"source_count": 0}
        if store is not None:
            sources = store.all_entries("source_registry")
            notes["source_count"] = len(sources)
            if not sources:
                findings.append(
                    self._new_finding(
                        severity="medium",
                        title="source_registry is empty",
                        description=(
                            "Literature grounding is the basis for the Reviewer agent's defence. "
                            "Add the PCNA / AOH1996 / cryptic-pocket / GNN / leakage references."
                        ),
                        required_action="Populate source_registry.json with the canonical references.",
                    )
                )
        return self._output(
            task=packet.task,
            status="warning" if findings else "pass",
            confidence=0.6,
            summary=f"Literature audit: {notes['source_count']} sources registered.",
            findings=findings,
            notes=notes,
        )


_METRIC_ARTIFACT_GLOB = ("**/*metric*.json", "**/*eval*.json", "**/*results*.json")


class MetricsStatisticsAgent(BaseAgent):
    agent_id = "metrics_statistics"
    display_name = "Metrics, Statistics and Uncertainty"

    def run(self, packet: ContextPacket) -> AgentOutput:
        findings = []
        gate_updates = []
        evidence: List[EvidenceRef] = []
        notes: Dict[str, Any] = {"metric_files_seen": 0}
        repo_root = Path(self.ctx.repo_root)

        seen_files: List[Path] = []
        for pattern in _METRIC_ARTIFACT_GLOB:
            for p in repo_root.glob(pattern):
                if any(part in {".git", "research_os", "research_os_memory", "research_os_registries"} for part in p.parts):
                    continue
                seen_files.append(p)
        notes["metric_files_seen"] = len(seen_files)

        for p in seen_files:
            evidence.append(self._evidence_path(str(p.relative_to(repo_root))))
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            flat = self._flatten(data)
            has_auroc = any("auroc" in k.lower() or "auc" in k.lower() for k in flat)
            has_auprc = any("auprc" in k.lower() or "ap" == k.lower().split(".")[-1] for k in flat)
            has_ci = any("ci" in k.lower() or "confidence" in k.lower() or "uncertainty" in k.lower() for k in flat)
            if has_auroc and not has_auprc:
                findings.append(
                    self._new_finding(
                        severity="high",
                        title=f"{p.relative_to(repo_root)} reports AUROC without AUPRC",
                        description="For sparse positives the AUROC alone is misleading.",
                        evidence=[self._evidence_path(str(p.relative_to(repo_root)))],
                        required_action="Recompute AUPRC and the positive-class baseline alongside AUROC.",
                    )
                )
            if has_auroc and not has_ci:
                findings.append(
                    self._new_finding(
                        severity="medium",
                        title=f"{p.relative_to(repo_root)} has AUROC but no confidence interval",
                        required_action="Bootstrap at the correct independence unit (protein/structure).",
                    )
                )

        # Also check the Claim registry for headline numeric claims.
        store = self.ctx.registry_store
        if store is not None:
            for c in store.all_entries("claim_registry"):
                if re.search(r"\bAUROC\s*=", c.get("claim_text", "")) and c.get("claim_strength") != "moderately_supported":
                    findings.append(
                        self._new_finding(
                            severity="medium",
                            title=f"Claim {c.get('claim_id')} cites a metric without 'moderately_supported' framing",
                            description="Numeric metrics on small test sets warrant moderate-strength wording at best.",
                            affected_claims=[c.get("claim_id", "?")],
                        )
                    )

        gate_status = "warning" if findings else "pass"
        gate_updates.append(self._gate(GateName.EVALUATION, gate_status))
        return self._output(
            task=packet.task,
            status=gate_status,
            confidence=0.75,
            summary=f"Metrics audit: scanned {len(seen_files)} files; {len(findings)} findings.",
            evidence_used=evidence,
            findings=findings,
            gate_updates=gate_updates,
            notes=notes,
        )

    def _flatten(self, obj: Any, prefix: str = "") -> Dict[str, Any]:
        out: Dict[str, Any] = {}
        if isinstance(obj, dict):
            for k, v in obj.items():
                key = f"{prefix}.{k}" if prefix else k
                out.update(self._flatten(v, key))
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                out.update(self._flatten(item, f"{prefix}[{i}]"))
        else:
            out[prefix] = obj
        return out


class ModelTrainingAgent(BaseAgent):
    agent_id = "model_training"
    display_name = "Model Development and Training"

    def run(self, packet: ContextPacket) -> AgentOutput:
        body = _memory_body(self.ctx, "MODEL_REGISTRY.md")
        findings = []
        if not body:
            findings.append(
                self._new_finding(
                    severity="medium",
                    title="MODEL_REGISTRY.md missing",
                    required_action="Initialize the model registry.",
                )
            )
        else:
            if "current canonical checkpoint" not in body.lower():
                findings.append(
                    self._new_finding(
                        severity="medium",
                        title="Model registry has no 'Current canonical checkpoint' section",
                    )
                )
            if re.search(r"^\s*\(none accepted yet\b", body, re.IGNORECASE | re.MULTILINE):
                findings.append(
                    self._new_finding(
                        severity="info",
                        title="No canonical checkpoint accepted",
                        description="Training results cannot become a headline until a checkpoint is registered.",
                    )
                )

        store = self.ctx.registry_store
        if store is not None:
            ckpts = store.find("artifact_registry", lambda e: e.get("artifact_type") == "checkpoint")
            current_ckpts = [c for c in ckpts if c.get("status") == "current"]
            if ckpts and not current_ckpts:
                findings.append(
                    self._new_finding(
                        severity="high",
                        title="Checkpoints exist but none are status=current",
                        description=", ".join(c.get("artifact_id", "?") for c in ckpts),
                    )
                )

        return self._output(
            task=packet.task,
            status="warning" if findings else "pass",
            confidence=0.7,
            summary=f"Model training audit: {len(findings)} findings.",
            findings=findings,
        )


class ComputePlanningAgent(BaseAgent):
    agent_id = "compute_planning"
    display_name = "Compute Planning and Execution"

    def run(self, packet: ContextPacket) -> AgentOutput:
        body = _memory_body(self.ctx, "COMPUTE_REGISTRY.md")
        findings = []
        human_review = False
        reason = ""
        # Did the user ask for expensive compute?
        big_compute = re.search(
            r"\b(100\s*ns|\d{2,}\s*ns|cloud|gpu|expensive|budget)\b",
            packet.task,
            re.IGNORECASE,
        )
        if big_compute:
            human_review = True
            reason = "Expensive compute requires explicit PI go/no-go and a documented success/failure plan."
            if "approved expensive runs" in body.lower() and "(none recorded yet" in body.lower():
                findings.append(
                    self._new_finding(
                        severity="critical",
                        title="No approved compute budget recorded",
                        description="Cannot greenlight MD/cloud without an entry in COMPUTE_REGISTRY.md.",
                        required_action="Add an approved budget entry and a success/failure plan.",
                        blocks_pipeline=True,
                    )
                )
        return self._output(
            task=packet.task,
            status="blocked" if any(f.blocks_pipeline for f in findings) else "pass",
            confidence=0.8,
            summary=f"Compute planning audit: {len(findings)} findings.",
            findings=findings,
            human_review_required=human_review,
            human_review_reason=reason,
        )


class ValidationSkepticAgent(BaseAgent):
    agent_id = "validation_skeptic"
    display_name = "Validation and Skeptic"

    def run(self, packet: ContextPacket) -> AgentOutput:
        body = _memory_body(self.ctx, "VALIDATION_STATUS.md")
        findings = []
        gate_updates = []
        classification = "inconclusive"
        if body:
            m = re.search(
                r"Evidence classification[^\n]*\n+\W*`?([a-z_]+)`?",
                body,
                re.IGNORECASE,
            )
            if m:
                classification = m.group(1)
        else:
            findings.append(
                self._new_finding(
                    severity="high",
                    title="VALIDATION_STATUS.md missing",
                    required_action="Initialize validation memory.",
                )
            )

        if classification in ("inconclusive", "weakens_claim", "contradicts_claim"):
            gate_updates.append(self._gate(GateName.VALIDATION, "fail", f"classification={classification}"))
            findings.append(
                self._new_finding(
                    severity="high",
                    title=f"Validation classification is {classification}",
                    description="Cryptic-pocket / strong-validation claims are not currently defensible.",
                    required_action="Either downgrade claims, or generate validation evidence that classifies as supports_claim / partially_supports_claim.",
                )
            )
        elif classification == "partially_supports_claim":
            gate_updates.append(self._gate(GateName.VALIDATION, "warning", "partial support"))
        else:
            gate_updates.append(self._gate(GateName.VALIDATION, "pass", f"classification={classification}"))

        return self._output(
            task=packet.task,
            status="warning" if findings else "pass",
            confidence=0.8,
            summary=f"Validation classification: {classification}; {len(findings)} findings.",
            findings=findings,
            gate_updates=gate_updates,
            notes={"classification": classification},
        )


__all__ = [
    "BiologicalRealismAgent",
    "ComputePlanningAgent",
    "LiteratureWebAgent",
    "MetricsStatisticsAgent",
    "ModelTrainingAgent",
    "ResearchDesignAgent",
    "ValidationSkepticAgent",
]
