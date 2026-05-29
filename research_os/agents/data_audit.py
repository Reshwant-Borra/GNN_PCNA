"""Data + leakage + preprocessing + code-review + testing agents.

These are the audit-heavy agents that gate training and metric acceptance.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

from research_os.agents.base import BaseAgent, GateName
from research_os.schemas.context import ContextPacket
from research_os.schemas.core import AgentOutput


def _read_memory_section(body: str, headings: List[str]) -> str:
    """Return the text under the first matched heading, or empty string."""
    for h in headings:
        pat = re.compile(
            rf"^#+\s*{re.escape(h)}\s*$(?P<body>.*?)(?=^#+\s|\Z)",
            re.IGNORECASE | re.MULTILINE | re.DOTALL,
        )
        m = pat.search(body)
        if m:
            return m.group("body").strip()
    return ""


class DatasetIntegrityAgent(BaseAgent):
    agent_id = "dataset_integrity"
    display_name = "Dataset and Label Integrity"

    REQUIRED_SECTIONS = (
        "Datasets in use",
        "Label definition",
        "Missing-data policy",
        "Residue/chain mapping rules",
        "Split protocol",
    )

    def run(self, packet: ContextPacket) -> AgentOutput:
        findings = []
        gate_updates = []
        evidence = []
        mem = self.ctx.memory_store
        if mem is None or not mem.exists("DATASET_REGISTRY.md"):
            findings.append(
                self._new_finding(
                    severity="high",
                    title="DATASET_REGISTRY.md missing",
                    blocks_pipeline=True,
                )
            )
            gate_updates.append(self._gate(GateName.DATASET, "blocked", "no dataset registry"))
            return self._output(
                task=packet.task,
                status="blocked",
                confidence=0.9,
                summary="No dataset registry available.",
                findings=findings,
                gate_updates=gate_updates,
            )

        body = mem.read("DATASET_REGISTRY.md").body
        evidence.append(self._evidence_memory("DATASET_REGISTRY.md"))
        missing_sections = []
        pending_sections = []
        for section in self.REQUIRED_SECTIONS:
            text = _read_memory_section(body, [section])
            if not text:
                missing_sections.append(section)
            elif re.search(r"^\s*pending\b", text, re.IGNORECASE | re.MULTILINE):
                pending_sections.append(section)

        for s in missing_sections:
            findings.append(
                self._new_finding(
                    severity="high",
                    title=f"DATASET_REGISTRY.md missing '{s}' section",
                    required_action="Document the section before any training/metric work.",
                )
            )
        for s in pending_sections:
            findings.append(
                self._new_finding(
                    severity="medium",
                    title=f"DATASET_REGISTRY.md section '{s}' still pending",
                    required_action="Replace 'pending' content with the actual definition.",
                )
            )

        gate_status = "pass"
        if missing_sections:
            gate_status = "fail"
        elif pending_sections:
            gate_status = "warning"
        gate_updates.append(
            self._gate(
                GateName.DATASET,
                gate_status,
                reason="Sections audited from DATASET_REGISTRY.md",
            )
        )

        return self._output(
            task=packet.task,
            status="pass" if gate_status == "pass" else "warning",
            confidence=0.8,
            summary=(
                f"Dataset registry audit: {len(missing_sections)} missing, "
                f"{len(pending_sections)} pending."
            ),
            evidence_used=evidence,
            findings=findings,
            gate_updates=gate_updates,
        )


class LeakageSplitAgent(BaseAgent):
    agent_id = "leakage_split"
    display_name = "Leakage and Split Design"

    REQUIRED_CHECKS = (
        "chain",
        "PDB",
        "homology",
        "apo/holo",
        "label transfer",
        "feature normalization",
    )

    def run(self, packet: ContextPacket) -> AgentOutput:
        findings = []
        gate_updates = []
        evidence = []

        mem = self.ctx.memory_store
        body = ""
        if mem is not None and mem.exists("DATASET_REGISTRY.md"):
            body = mem.read("DATASET_REGISTRY.md").body
            evidence.append(self._evidence_memory("DATASET_REGISTRY.md"))
        else:
            findings.append(
                self._new_finding(
                    severity="critical",
                    title="No dataset registry to audit for leakage",
                    blocks_pipeline=True,
                )
            )

        split_text = _read_memory_section(body, ["Split protocol"]) if body else ""
        if not split_text or re.search(r"^\s*pending\b", split_text, re.IGNORECASE | re.MULTILINE):
            findings.append(
                self._new_finding(
                    severity="critical",
                    title="No documented split protocol",
                    description="The Leakage gate cannot pass without a documented, approved split.",
                    required_action="Document chain-/homology-/apo-holo-blocked splits.",
                    blocks_pipeline=True,
                )
            )
            gate_updates.append(self._gate(GateName.LEAKAGE, "blocked", "no split protocol documented"))
            return self._output(
                task=packet.task,
                status="blocked",
                confidence=0.9,
                summary="Leakage gate cannot pass without a split protocol.",
                evidence_used=evidence,
                findings=findings,
                gate_updates=gate_updates,
            )

        unchecked = [c for c in self.REQUIRED_CHECKS if c.lower() not in split_text.lower()]
        for c in unchecked:
            findings.append(
                self._new_finding(
                    severity="high",
                    title=f"Leakage check missing: {c}",
                    required_action=f"Document explicit handling of {c} leakage in DATASET_REGISTRY.md.",
                )
            )

        # Cross-check: any metric artifact must list a split artifact dependency.
        registry = self.ctx.registry_store
        if registry is not None:
            metrics = registry.find(
                "artifact_registry",
                lambda e: e.get("artifact_type") == "metric" and e.get("status") == "current",
            )
            for m in metrics:
                deps_text = " ".join(m.get("dependencies", []) or [])
                if not any(
                    (registry.get("artifact_registry", dep) or {}).get("artifact_type") == "split"
                    for dep in m.get("dependencies", []) or []
                ):
                    findings.append(
                        self._new_finding(
                            severity="critical",
                            title=f"Metric artifact {m.get('artifact_id')} has no split-artifact dependency",
                            description=(
                                "A metric without a documented split-artifact dependency cannot be "
                                "trusted because the leakage gate cannot trace which split it used."
                            ),
                            evidence=[self._evidence_registry("artifact_registry", m.get("artifact_id", "?"))],
                            affected_artifacts=[m.get("artifact_id", "?")],
                            blocks_pipeline=True,
                        )
                    )

        gate_status = "pass" if not findings else ("warning" if not any(f.blocks_pipeline for f in findings) else "fail")
        gate_updates.append(self._gate(GateName.LEAKAGE, gate_status, reason=f"{len(findings)} findings"))

        return self._output(
            task=packet.task,
            status="fail" if any(f.blocks_pipeline for f in findings) else ("warning" if findings else "pass"),
            confidence=0.85,
            summary=(
                f"Leakage audit: {len(findings)} findings. Required checks unaddressed: "
                f"{unchecked or 'none'}"
            ),
            evidence_used=evidence,
            findings=findings,
            gate_updates=gate_updates,
        )


class PreprocessingAuditorAgent(BaseAgent):
    agent_id = "preprocessing_auditor"
    display_name = "Preprocessing and Feature Engineering Auditor"

    def run(self, packet: ContextPacket) -> AgentOutput:
        findings = []
        gate_updates = []
        evidence = []
        store = self.ctx.registry_store
        if store is None:
            return self._output(
                task=packet.task,
                status="blocked",
                confidence=0.7,
                summary="No registry store to audit.",
                gate_updates=[self._gate(GateName.PREPROCESSING, "blocked", "no registry")],
            )

        graphs = store.find("artifact_registry", lambda e: e.get("artifact_type") == "graph")
        for g in graphs:
            if g.get("status") in ("stale", "invalid"):
                findings.append(
                    self._new_finding(
                        severity="high",
                        title=f"Graph artifact {g.get('artifact_id')} is {g.get('status')}",
                        description=(
                            "Downstream model / metric artifacts based on this graph must be "
                            "marked stale and regenerated."
                        ),
                        affected_artifacts=[g.get("artifact_id", "?")],
                    )
                )

        if not graphs:
            findings.append(
                self._new_finding(
                    severity="medium",
                    title="No graph artifacts registered",
                    description="Preprocessing gate cannot pass without registered graph artifacts.",
                )
            )
            gate_updates.append(self._gate(GateName.PREPROCESSING, "warning", "no graphs registered"))
        else:
            gate_updates.append(self._gate(GateName.PREPROCESSING, "warning" if findings else "pass"))

        return self._output(
            task=packet.task,
            status="warning" if findings else "pass",
            confidence=0.75,
            summary=f"Preprocessing audit found {len(findings)} issues among {len(graphs)} graphs.",
            evidence_used=evidence,
            findings=findings,
            gate_updates=gate_updates,
        )


_STALE_CHECKPOINT_PATTERNS = (
    re.compile(r"checkpoint[s]?[/\\][^'\"\s]+\.(pt|pth|ckpt)", re.IGNORECASE),
    re.compile(r"old[_\-]?ckpt", re.IGNORECASE),
)


class ScientificCodeReviewAgent(BaseAgent):
    agent_id = "scientific_code_review"
    display_name = "Scientific Code Review"

    SUSPICIOUS_PATTERNS = (
        (re.compile(r"\s*pass\s*#\s*(todo|fixme|skip)", re.IGNORECASE), "stub left in code"),
        (re.compile(r"raise\s+NotImplementedError"), "NotImplementedError left in code"),
        (re.compile(r"except\s*(?:Exception)?\s*:\s*pass"), "silently-swallowed exception"),
        (re.compile(r"#\s*(hack|hardcoded|fixme)", re.IGNORECASE), "hack/hardcoded marker"),
        (re.compile(r"@pytest\.mark\.skip", re.IGNORECASE), "skipped test marker"),
    )

    def run(self, packet: ContextPacket) -> AgentOutput:
        findings = []
        repo_root = Path(self.ctx.repo_root)
        scanned = 0
        flagged_files = 0
        for py in self._iter_python_files(repo_root):
            scanned += 1
            try:
                text = py.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            file_flags = 0
            for pat, label in self.SUSPICIOUS_PATTERNS:
                if pat.search(text):
                    file_flags += 1
                    findings.append(
                        self._new_finding(
                            severity="low",
                            title=f"{label} in {py.relative_to(repo_root)}",
                            evidence=[self._evidence_path(str(py.relative_to(repo_root)))],
                            required_action="Audit, document, or remove the marker.",
                        )
                    )
            for pat in _STALE_CHECKPOINT_PATTERNS:
                if pat.search(text):
                    file_flags += 1
                    findings.append(
                        self._new_finding(
                            severity="medium",
                            title=f"Possibly stale checkpoint path in {py.relative_to(repo_root)}",
                            description="Verify against MODEL_REGISTRY.md canonical checkpoint.",
                            evidence=[self._evidence_path(str(py.relative_to(repo_root)))],
                            required_action="Replace with canonical checkpoint reference.",
                        )
                    )
            if file_flags:
                flagged_files += 1

        gate_status = "pass" if not findings else "warning"
        return self._output(
            task=packet.task,
            status="pass" if not findings else "warning",
            confidence=0.65,
            summary=f"Scanned {scanned} Python files; {flagged_files} flagged; {len(findings)} findings.",
            findings=findings,
            gate_updates=[self._gate(GateName.CODE, gate_status)],
        )

    def _iter_python_files(self, repo_root: Path):
        for p in repo_root.rglob("*.py"):
            rel = p.relative_to(repo_root)
            parts = set(rel.parts)
            if parts & {".git", "__pycache__", "research_os_memory", "research_os_registries", "reports"}:
                continue
            if any(part.startswith(".") for part in rel.parts):
                continue
            yield p


class TestingEnvironmentAgent(BaseAgent):
    # Tell pytest this is not a test class (it starts with 'Test' which pytest
    # auto-collects by default).
    __test__ = False

    agent_id = "testing_environment"
    display_name = "Testing and Fresh Environment"

    def run(self, packet: ContextPacket) -> AgentOutput:
        findings = []
        gate_updates = []
        notes: Dict[str, Any] = {}
        repo_root = Path(self.ctx.repo_root)
        tests_dir = repo_root / "tests"

        if not tests_dir.exists():
            findings.append(
                self._new_finding(
                    severity="medium",
                    title="No tests/ directory found",
                    required_action="Create at least smoke tests under tests/.",
                )
            )
            gate_updates.append(self._gate(GateName.CODE, "warning", "no tests directory"))
            return self._output(
                task=packet.task,
                status="warning",
                confidence=0.8,
                summary="No tests/ directory; testing gate degraded.",
                findings=findings,
                gate_updates=gate_updates,
            )

        # Only run pytest if explicitly invoked via packet.allowed_actions to keep
        # full audit fast. The presence of the directory is the bare minimum.
        if "run_pytest" in (packet.allowed_actions or []):
            try:
                result = subprocess.run(
                    [sys.executable, "-m", "pytest", str(tests_dir), "-q", "--no-header"],
                    capture_output=True,
                    text=True,
                    cwd=str(repo_root),
                    timeout=180,
                    check=False,
                )
                notes["pytest_returncode"] = result.returncode
                notes["pytest_tail"] = "\n".join(result.stdout.splitlines()[-20:])
                if result.returncode != 0:
                    findings.append(
                        self._new_finding(
                            severity="high",
                            title="pytest failed",
                            description=result.stdout[-1000:],
                            blocks_pipeline=True,
                        )
                    )
                # Critical skip policy: any "skip" lines for torch_geometric.
                if re.search(r"skip\w*", result.stdout, re.IGNORECASE):
                    if re.search(r"torch[_-]geometric|pyg|torch_scatter", result.stdout, re.IGNORECASE):
                        findings.append(
                            self._new_finding(
                                severity="critical",
                                title="Critical dependency skipped (torch_geometric / PyG)",
                                description="Per docs/agents/11_testing_fresh_environment.md, skipped critical deps count as failure, not pass.",
                                blocks_pipeline=True,
                            )
                        )
            except (FileNotFoundError, subprocess.TimeoutExpired) as e:
                findings.append(
                    self._new_finding(
                        severity="high",
                        title="Could not run pytest",
                        description=str(e),
                    )
                )

        gate_status = "fail" if any(f.blocks_pipeline for f in findings) else (
            "warning" if findings else "pass"
        )
        gate_updates.append(self._gate(GateName.CODE, gate_status))

        return self._output(
            task=packet.task,
            status="fail" if any(f.blocks_pipeline for f in findings) else ("warning" if findings else "pass"),
            confidence=0.8,
            summary=f"Tests/ present; {len(findings)} findings; pytest_run={'run_pytest' in (packet.allowed_actions or [])}.",
            findings=findings,
            gate_updates=gate_updates,
            notes=notes,
        )


__all__ = [
    "DatasetIntegrityAgent",
    "LeakageSplitAgent",
    "PreprocessingAuditorAgent",
    "ScientificCodeReviewAgent",
    "TestingEnvironmentAgent",
]
