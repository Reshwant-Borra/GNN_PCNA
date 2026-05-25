"""Ollama-backed semantic router for ResearchOS.

This is the **primary** routing layer. The classical keyword/regex router in
``research_os.routing.intent`` is retained as a deterministic guardrail and as
a fallback when Ollama is unreachable or returns garbage.

Design:

- Reads ``research_os_memory/AGENT_REGISTRY.md`` and ``ROUTING_GUIDE.md`` (once
  per process, in-memory cached) to build the LLM prompt context. The KB is
  the single source of truth for both the router and humans.
- Sends a structured prompt to Ollama (Gemma 3:4b by default) via the same
  ``/api/chat`` endpoint the Telegram intent parser already uses. We don't
  import from ``agents.intent_parser`` — different layer, different concerns.
- Returns a dict matching the schema in the upgrade spec, or ``None`` on any
  failure so the caller can fall back deterministically.
- No third-party dependencies. Uses only ``urllib`` and stdlib JSON.

Routing schema (output JSON):

    {
      "intent": "<short intent label>",
      "selected_agents": ["context_source_truth", "literature_web", ...],
      "selected_workflow": "<workflow name or null>",
      "confidence": 0.0-1.0,
      "risk_level": "low" | "medium" | "high" | "critical",
      "reasoning_summary": "...",
      "requires_claude_fallback": true|false,
      "requires_human_approval": true|false
    }
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Protocol

from research_os.memory.registry_loader import (
    AgentEntry,
    RoutingCategory,
    load_agent_registry,
    load_routing_guide,
)
from research_os.routing._llm_json import extract_json
from research_os.schemas.vocab import AGENT_IDS, RISK_LEVELS


DEFAULT_MODEL = os.environ.get("RESEARCHOS_OLLAMA_MODEL", "gemma3:4b")
DEFAULT_OLLAMA_HOST = os.environ.get(
    "OLLAMA_HOST",
    "http://localhost:11434",
)
DEFAULT_TIMEOUT_S = float(os.environ.get("RESEARCHOS_OLLAMA_TIMEOUT", "15"))


class _ChatBackend(Protocol):
    """Callable that takes (system, user, timeout_s) and returns the raw model text."""
    def __call__(self, system: str, user: str, timeout_s: float) -> str: ...


def _ollama_chat(system: str, user: str, timeout_s: float = DEFAULT_TIMEOUT_S) -> str:
    """Call the local Ollama /api/chat endpoint. Raises ``OSError`` on failure."""
    endpoint = f"{DEFAULT_OLLAMA_HOST.rstrip('/')}/api/chat"
    payload = json.dumps({
        "model": DEFAULT_MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "stream": False,
        "options": {"temperature": 0},
        "format": "json",  # Ollama hint: produce JSON
    }).encode("utf-8")
    req = urllib.request.Request(
        endpoint,
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout_s) as resp:
        raw = resp.read()
    parsed = json.loads(raw)
    msg = parsed.get("message") or {}
    content = msg.get("content")
    if not isinstance(content, str):
        raise OSError("Ollama response missing message.content")
    return content


SYSTEM_PROMPT = """\
You are the ResearchOS router. Map the user prompt to scientific agents.

Output STRICT JSON only:
{"intent":"<label>","selected_agents":["<id>",...],"selected_workflow":null,
 "confidence":0.0,"risk_level":"low|medium|high|critical",
 "reasoning_summary":"<one sentence>","requires_claude_fallback":false,
 "requires_human_approval":false}

Rules (positive — MUST include):
- Always: ["context_source_truth"] first.
- Literature / "find papers" / PubMed / "literature on X": ["literature_web","document_knowledge_ingestion"].
- MD trajectories / RMSF / RMSD / DCCM / "did MD validate": ["validation_skeptic","biological_realism"]. If claim wording is involved, add ["paper_claim","contradiction_hunter"].
- Data leakage / split / homology / apo-holo: ["leakage_split"] (add "dataset_integrity","preprocessing_auditor" for feature leakage).
- Claim / paper / "can we say X?": ["paper_claim","contradiction_hunter"].
- Compute / GPU / cloud / cluster budget: ["compute_planning"].
- Figure / plot / heatmap / regenerate: ["visual_evidence"].
- Reviewer simulation / "what will reviewers ask" / "simulate reviewer concerns": ["reviewer_collaboration"].
- Biological plausibility / "residues near X" / "is this region plausible": ["biological_realism"].
- Statistics / bootstrap CI / metric comparison: ["metrics_statistics"].
- Compound prompt = union of matching categories.

Rules (negative — DO NOT include):
- Status / "what's the latest X" / "show me X" / "current status": NEVER add model_training, code_builder, paper_claim, leakage_split, dataset_integrity, preprocessing_auditor. Risk = low or medium.
- Literature: NEVER add validation_skeptic or model_training just because the topic mentions MD or cryptic pockets.
- Figure: NEVER add validation_skeptic or leakage_split unless figure is about validation/leakage.

Risk & approval:
- "high" if training, leakage, MD validation, metrics audit, expensive compute.
- "critical" if publication, claim upgrade, destructive op (delete/force-merge/wipe).
- requires_human_approval=true for submission, claim upgrade above moderately_supported, expensive compute, deleting artifacts, force-merge, destructive ops.
- requires_claude_fallback=true if confidence<0.75, risk in {"high","critical"}, or claim/validation/publication involved.

Pick the SMALLEST agent set that satisfies the rules — don't pile on agents just in case.

FEW-SHOT EXAMPLES (study these — they pin the hard cases):

Prompt: "What's the recent literature on cryptic pockets?"
Output: {"intent":"literature","selected_agents":["context_source_truth","literature_web","document_knowledge_ingestion","provenance_artifacts"],"selected_workflow":null,"confidence":0.95,"risk_level":"medium","reasoning_summary":"literature search; topic is cryptic pockets but no MD interpretation requested","requires_claude_fallback":false,"requires_human_approval":false}

Prompt: "What's the latest checkpoint?"
Output: {"intent":"status","selected_agents":["context_source_truth","provenance_artifacts"],"selected_workflow":null,"confidence":0.95,"risk_level":"low","reasoning_summary":"status query about checkpoint","requires_claude_fallback":false,"requires_human_approval":false}

Prompt: "Did MD validate the cryptic pocket?"
Output: {"intent":"claim_validation","selected_agents":["context_source_truth","validation_skeptic","biological_realism","paper_claim","contradiction_hunter"],"selected_workflow":"md_validation","confidence":0.95,"risk_level":"critical","reasoning_summary":"claim-wording question about MD validation; needs PI signoff","requires_claude_fallback":true,"requires_human_approval":true}

Prompt: "Generate Figure 3 with bootstrap confidence intervals"
Output: {"intent":"figure_generation","selected_agents":["context_source_truth","visual_evidence","metrics_statistics","provenance_artifacts"],"selected_workflow":null,"confidence":0.9,"risk_level":"medium","reasoning_summary":"figure with CIs; no leakage/validation involved","requires_claude_fallback":false,"requires_human_approval":false}

Prompt: "Review the evaluation script for correctness"
Output: {"intent":"code_review","selected_agents":["context_source_truth","scientific_code_review","testing_environment"],"selected_workflow":null,"confidence":0.9,"risk_level":"medium","reasoning_summary":"code review; no paper/figure scope","requires_claude_fallback":false,"requires_human_approval":false}

Prompt: "Find papers on cryptic pockets and update the related work section"
Output: {"intent":"literature_plus_paper","selected_agents":["context_source_truth","literature_web","document_knowledge_ingestion","paper_claim","biological_realism","contradiction_hunter"],"selected_workflow":null,"confidence":0.9,"risk_level":"high","reasoning_summary":"compound: literature search + related work edit","requires_claude_fallback":true,"requires_human_approval":false}
"""


def _render_registry_block(entries: Dict[str, AgentEntry]) -> str:
    """Render a compact per-agent summary suitable for an LLM context window."""
    if not entries:
        return "(registry empty — KB not initialized)"
    lines: List[str] = []
    for entry in entries.values():
        kw = ", ".join(entry.keywords[:8]) if entry.keywords else ""
        wf = ", ".join(entry.workflows[:6]) if entry.workflows else ""
        ex = "; ".join(entry.example_prompts[:3]) if entry.example_prompts else ""
        lines.append(
            f"- {entry.agent_id} (risk={entry.risk_level}): {entry.purpose}\n"
            f"    when: {entry.when_to_use}\n"
            f"    keywords: {kw}\n"
            f"    workflows: {wf}\n"
            f"    examples: {ex}"
        )
    return "\n".join(lines)


def _render_routing_guide_block(categories: List[RoutingCategory]) -> str:
    """Render category → always-include + a few worked examples."""
    if not categories:
        return "(routing guide empty)"
    lines: List[str] = []
    for cat in categories:
        ai = ", ".join(cat.always_include) if cat.always_include else "(none)"
        lines.append(f"- {cat.name}: ALWAYS {{{ai}}}")
        for ex in cat.examples[:2]:
            agents = ", ".join(ex.get("agents", []) or [])  # type: ignore[arg-type]
            prompt = ex.get("prompt", "")
            lines.append(f"    example: \"{prompt}\" -> [{agents}]")
    return "\n".join(lines)


USER_PROMPT_TEMPLATE = """\
=== AGENT REGISTRY ===
{registry_block}

=== ROUTING GUIDE ===
{routing_block}

=== USER PROMPT ===
{user_prompt}

Now emit the JSON.
"""


@dataclass
class SemanticRouterResult:
    """Validated output from the semantic router."""
    intent: str
    selected_agents: List[str]
    selected_workflow: Optional[str]
    confidence: float
    risk_level: str
    reasoning_summary: str
    requires_claude_fallback: bool
    requires_human_approval: bool
    raw_response: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "intent": self.intent,
            "selected_agents": list(self.selected_agents),
            "selected_workflow": self.selected_workflow,
            "confidence": self.confidence,
            "risk_level": self.risk_level,
            "reasoning_summary": self.reasoning_summary,
            "requires_claude_fallback": self.requires_claude_fallback,
            "requires_human_approval": self.requires_human_approval,
            "raw_response": self.raw_response,
        }


class OllamaSemanticRouter:
    """Semantic router backed by Ollama (or any injected chat backend).

    Use ``backend`` to inject a fake chat function in tests so we never hit
    real Ollama from CI. The default backend is the local Ollama HTTP call.
    """

    def __init__(
        self,
        repo_root: "str | Path" = ".",
        *,
        backend: Optional[_ChatBackend] = None,
        timeout_s: float = DEFAULT_TIMEOUT_S,
    ):
        self.repo_root = Path(repo_root)
        self.backend = backend or _ollama_chat
        self.timeout_s = timeout_s

    def route(self, message: str) -> Optional[SemanticRouterResult]:
        """Classify ``message``. Returns None on any failure (network, JSON, validation)."""
        message = (message or "").strip()
        if not message:
            return None

        try:
            registry = load_agent_registry(self.repo_root)
            guide = load_routing_guide(self.repo_root)
        except Exception:
            return None

        user_prompt = USER_PROMPT_TEMPLATE.format(
            registry_block=_render_registry_block(registry),
            routing_block=_render_routing_guide_block(guide),
            user_prompt=message,
        )

        try:
            raw_text = self.backend(SYSTEM_PROMPT, user_prompt, self.timeout_s)
        except (OSError, urllib.error.URLError, TimeoutError, json.JSONDecodeError):
            return None
        except Exception:
            return None

        parsed = extract_json(raw_text)
        if not parsed:
            return None

        return self._validate(parsed)

    @staticmethod
    def _validate(parsed: Dict[str, Any]) -> Optional[SemanticRouterResult]:
        """Coerce LLM output to a typed result, dropping invalid agent IDs."""
        try:
            agents_raw = parsed.get("selected_agents") or []
            if not isinstance(agents_raw, list):
                return None
            agents = [a for a in agents_raw if isinstance(a, str) and a in AGENT_IDS]
            # Enforce: at least one valid agent. context_source_truth always first.
            if not agents:
                return None
            if "context_source_truth" not in agents:
                agents.insert(0, "context_source_truth")
            else:
                # Move to front while preserving order of the rest.
                agents = ["context_source_truth"] + [a for a in agents if a != "context_source_truth"]
            # Dedup while preserving order.
            seen: set = set()
            deduped: List[str] = []
            for a in agents:
                if a not in seen:
                    seen.add(a)
                    deduped.append(a)
            agents = deduped

            risk = str(parsed.get("risk_level") or "medium").lower()
            if risk not in RISK_LEVELS:
                risk = "medium"

            confidence = float(parsed.get("confidence") or 0.0)
            confidence = max(0.0, min(1.0, confidence))

            workflow = parsed.get("selected_workflow")
            workflow = workflow if isinstance(workflow, str) and workflow else None

            return SemanticRouterResult(
                intent=str(parsed.get("intent") or "general"),
                selected_agents=agents,
                selected_workflow=workflow,
                confidence=confidence,
                risk_level=risk,
                reasoning_summary=str(parsed.get("reasoning_summary") or ""),
                requires_claude_fallback=bool(parsed.get("requires_claude_fallback", False)),
                requires_human_approval=bool(parsed.get("requires_human_approval", False)),
                raw_response=parsed,
            )
        except (TypeError, ValueError):
            return None


__all__ = [
    "OllamaSemanticRouter",
    "SemanticRouterResult",
    "DEFAULT_MODEL",
    "DEFAULT_OLLAMA_HOST",
    "DEFAULT_TIMEOUT_S",
    "SYSTEM_PROMPT",
    "USER_PROMPT_TEMPLATE",
]
