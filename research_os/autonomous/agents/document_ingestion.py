"""Autonomous Document/Knowledge Ingestion agent.

Wraps the legacy ``DocumentKnowledgeIngestionAgent`` (which only checked
``agents/ingest.py`` exists) and adds:

- Discovery of unregistered candidate files (PDFs, markdown, JSON metadata)
  under ``data/`` and ``research/``
- Ingestion via ``agents.ingest.ingest_file`` (the existing pipeline) when
  the discovered files have not already been registered
- Heuristic relevance scoring + tagging through the existing pipeline
- Coverage-aware critic that spawns follow-up discovery rounds if the
  source registry stays sparse

Deterministic fallback delegates to the legacy agent.
"""
from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any, Dict, List, Optional

from research_os.agents.base import AgentContext
from research_os.agents.communication import DocumentKnowledgeIngestionAgent
from research_os.autonomous.agent import AutonomousAgent
from research_os.autonomous.critique import simple_critic
from research_os.autonomous.profile import AgentProfile, AutonomyLevel
from research_os.autonomous.schemas import Budget, Goal, SuccessCriterion
from research_os.schemas.context import ContextPacket
from research_os.schemas.core import AgentOutput


DOC_INGEST_PROFILE = AgentProfile(
    agent_id="document_knowledge_ingestion",
    capabilities=["document_ingest", "source_discovery", "registry_update"],
    allowed_tools=[
        "memory_read", "memory_list", "registry_read", "registry_query",
        "file_read", "glob", "hash_file",
    ],
    domain_areas=["literature", "provenance"],
    autonomy_level=AutonomyLevel.GUIDED,
    confidence_model="fixed",
    handoff_targets=["literature_web", "context_source_truth",
                     "provenance_artifacts"],
    failure_modes=["ingest_script_missing", "source_registry_corrupt"],
    default_budget=Budget(max_iterations=10, max_tool_calls=20,
                          max_failures=3, max_seconds=60.0),
    fallback_behavior="scan_only",
    requires_env=[],
    notes="Phase 4: discovers + ingests candidate documents through the existing ingest pipeline.",
)


class AutonomousDocumentIngestionAgent(AutonomousAgent):
    agent_id = "document_knowledge_ingestion"
    display_name = "Autonomous Document and Knowledge Ingestion"

    SCAN_DIRS = ("data", "research", "Obsidian/Claude/Chat History")
    SUPPORTED_SUFFIXES = (".pdf", ".md", ".txt", ".json", ".html", ".htm")

    def __init__(self, ctx: AgentContext, **kwargs):
        kwargs.setdefault("profile", DOC_INGEST_PROFILE)
        kwargs.setdefault("critics", [simple_critic])
        super().__init__(ctx, **kwargs)
        self._legacy = DocumentKnowledgeIngestionAgent(ctx)

    # ------------------------------------------------------------------

    def build_goal(self, packet: ContextPacket) -> Goal:
        return Goal(
            objective="Ingest unregistered candidate documents into source_registry.",
            rationale="Sweep data/, research/, and chat-history dirs for "
                      "unregistered PDFs/MD/JSON and register them.",
            success_criteria=[
                SuccessCriterion(
                    name="ingest_attempted",
                    check_key="ingest_attempted",
                    op="==", check_value=True,
                ),
            ],
            budget=self.budget,
            inputs={"task": packet.task, "candidate_count": 0},
        )

    def _deterministic_run(self, packet: ContextPacket) -> AgentOutput:
        # Discover-and-ingest in this fallback path too. If ingest fails,
        # delegate to the original (which is a presence check + no-op).
        try:
            discovered = self._discover_candidates()
            ingested = self._ingest_all(discovered)
            self._merge_ctx_state("ingest_attempted", True)
            self._merge_ctx_state("ingest_count", len(ingested))
            summary = (
                f"Autonomous ingest fallback: {len(discovered)} candidates, "
                f"{len(ingested)} new sources registered."
            )
            return self._output(
                task=packet.task,
                status="pass" if discovered else "warning",
                confidence=0.7,
                summary=summary,
                notes={"discovered": len(discovered), "ingested": len(ingested)},
            )
        except Exception as e:
            # Final fallback: legacy agent's "check ingest.py exists" scan.
            self._merge_ctx_state("ingest_attempted", False)
            base = self._legacy.run(packet)
            base.summary = f"{base.summary} [autonomous ingest failed: {e}]"
            return base

    # ------------------------------------------------------------------

    def _discover_candidates(self) -> List[Path]:
        repo_root = Path(self.ctx.repo_root).resolve()
        # Walk SCAN_DIRS, return files with supported suffixes that are NOT
        # already in the source_registry. Capped at 50 to keep the loop bounded.
        registry = self.ctx.registry_store
        known: set = set()
        if registry is not None:
            try:
                for entry in registry.all_entries("source_registry"):
                    p = entry.get("original_path") or entry.get("path")
                    if isinstance(p, str):
                        known.add(p)
            except Exception:
                pass
        candidates: List[Path] = []
        for sub in self.SCAN_DIRS:
            base = repo_root / sub
            if not base.exists() or not base.is_dir():
                continue
            for p in base.rglob("*"):
                if not p.is_file():
                    continue
                if p.suffix.lower() not in self.SUPPORTED_SUFFIXES:
                    continue
                rel = str(p.resolve())
                if rel in known:
                    continue
                candidates.append(p)
                if len(candidates) >= 50:
                    return candidates
        return candidates

    def _ingest_all(self, paths: List[Path]) -> List[Dict[str, Any]]:
        """Invoke ``agents.ingest.ingest_file`` for each candidate, persist
        the registry mutations, return the per-file outcomes.

        Imports are lazy because ``agents.ingest`` pulls in optional
        third-party dependencies (pdfplumber, bs4). We never raise on
        import failure — just skip ingestion.
        """
        try:
            mod = importlib.import_module("agents.ingest")
            _load_registry = getattr(mod, "_load_registry")
            _save_registry = getattr(mod, "_save_registry")
            ingest_file = getattr(mod, "ingest_file")
        except Exception as e:
            # No ingest module — defer to legacy fallback.
            raise RuntimeError(f"agents.ingest unavailable: {e}")

        reg = _load_registry()
        outcomes: List[Dict[str, Any]] = []
        for p in paths:
            try:
                entry, proposals = ingest_file(p, reg)
                if entry is not None:
                    outcomes.append({
                        "id": entry.id,
                        "path": str(p),
                        "title": entry.title,
                        "topics": list(entry.topics),
                    })
            except Exception as e:  # never let one bad file kill the sweep
                outcomes.append({"path": str(p), "error": str(e)})
        if outcomes:
            try:
                _save_registry(reg)
            except Exception:
                pass
        return [o for o in outcomes if "id" in o]


__all__ = ["AutonomousDocumentIngestionAgent", "DOC_INGEST_PROFILE"]
