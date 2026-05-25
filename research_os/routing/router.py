"""Top-level Router: glue semantic + keyword classifiers, risk, gates, human, context.

The semantic router (Ollama-backed) is the **primary** classifier. The
keyword/regex classifier is always run too and serves as a deterministic
guardrail — its agent set is unioned with the semantic result so we never
miss a critical agent because the LLM forgot it.

After the union, a small deterministic post-prune step strips agents that
are clearly out-of-scope for the prompt (e.g. ``validation_skeptic`` on a
pure literature query that merely *mentions* cryptic pockets as a topic).
That step is the only way to reliably suppress overreach by smaller LLMs
like ``gemma3:4b``.
"""
from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from research_os.memory.store import MemoryStore
from research_os.registries.store import RegistryStore
from research_os.routing.agents import select_agents
from research_os.routing.claude_fallback import (
    ClaudeFallback,
    ClaudeFallbackResult,
    FlagOnlyFallback,
    get_default_fallback,
)
from research_os.routing.context_builder import build_context_packet
from research_os.routing.gates import determine_required_gates
from research_os.routing.human import requires_human_review
from research_os.routing.intent import classify_intent
from research_os.routing.risk import classify_risk
from research_os.routing.semantic_router import (
    OllamaSemanticRouter,
    SemanticRouterResult,
)
from research_os.schemas.context import OrchestrationPlan
from research_os.schemas.vocab import AGENT_IDS, RISK_LEVELS


# Below this semantic confidence, the keyword guardrail dominates AND we
# request Claude Code's judgement via the fallback flag.
_CONFIDENCE_FLOOR = float(os.environ.get("RESEARCHOS_SEMANTIC_CONF_FLOOR", "0.55"))
_CONFIDENCE_HIGH = float(os.environ.get("RESEARCHOS_SEMANTIC_CONF_HIGH", "0.75"))

_RISK_RANK = {r: i for i, r in enumerate(RISK_LEVELS)}


def _max_risk(a: str, b: str) -> str:
    """Return the higher-severity risk between a and b."""
    return a if _RISK_RANK.get(a, 0) >= _RISK_RANK.get(b, 0) else b


# ── Post-merge agent-prune patterns ─────────────────────────────────────────
# Compiled once. Each constant captures "is this prompt about X?". Used by
# ``_prune_inappropriate_agents`` to drop agents the merged set picked up
# from over-eager intent matching (keyword or LLM).

_PAT_MD_CONTEXT = re.compile(
    r"\b(md|molecular\s+dynamics|rmsd|rmsf|dccm|trajector\w*|openmm|simulation|validat\w*|cryptic.*open|pocket.*open|prove.*opening|interpret.*trajector)\b",
    re.IGNORECASE,
)
_PAT_LEAKAGE_CONTEXT = re.compile(
    r"\b(leak\w*|train[/\s-]?test\s*split|train[/\s-]?test\s*overlap|homolog\w*|apo[/\s-]?holo|cross[\s-]?validation|chain\s*leak|split\s*audit|split\s*protocol)\b",
    re.IGNORECASE,
)
_PAT_TRAINING_ACTION = re.compile(
    r"\b(train|retrain|fine[\s-]?tune|fit|continue\s*training)\b\s*(?:the\s+model|for|with|from|on|further|now|tonight|the\s+\w+|new|model)\b|"
    r"\bfine[\s-]?tune\b|\bretrain\b|"
    r"\b(start|kick\s*off|launch|run)\b.*\btrain\w*\b",
    re.IGNORECASE,
)
_PAT_STATUS_QUERY = re.compile(
    r"\b(what'?s\s+the\s+latest|what\s+is\s+the\s+latest|show\s+me|current\s+(status|state|checkpoint)|"
    r"latest\s+(checkpoint|metric|run|status)|status\s+of|"
    r"what\s+blockers|what\s+is\s+the\s+current|how\s+(many|much)|show\s+training\s+history|training\s+history)\b",
    re.IGNORECASE,
)
_PAT_FIGURE_ACTION = re.compile(
    r"\b(figure\s*\d*|plot|heatmap|chart|render|generate.*figure|regenerate.*figure|axis|caption)\b",
    re.IGNORECASE,
)
_PAT_DATA_AUDIT = re.compile(
    r"\b(dataset|pdb|labels?|positives?|negatives?|ground\s*truth|sampl\w+\s+strategy|data\s+quality)\b",
    re.IGNORECASE,
)
_PAT_CODE_ACTION = re.compile(
    r"\b(implement|refactor|fix\s+bug|write\s+(?:script|tests?|module|function)|create\s+(?:cli|module|script)|review\s+code|audit\s+code|audit\s+script|code\s+review)\b",
    re.IGNORECASE,
)
_PAT_PAPER_ACTION = re.compile(
    r"\b(paper|manuscript|abstract|draft|results?\s+section|discussion\s+section|conclusion\s+section|claim|publish|submit|preprint|related\s+work|reviewer|peer\s*review)\b",
    re.IGNORECASE,
)


def _prune_inappropriate_agents(message: str, agents: List[str]) -> Tuple[List[str], List[str]]:
    """Drop agents that have no business being selected for ``message``.

    Returns ``(kept_agents, dropped_agents)``. ``context_source_truth`` is
    never dropped. The pruning rules are intentionally conservative — only
    strip an agent when the prompt clearly doesn't justify it.
    """
    has_md = bool(_PAT_MD_CONTEXT.search(message))
    has_leakage = bool(_PAT_LEAKAGE_CONTEXT.search(message))
    has_training = bool(_PAT_TRAINING_ACTION.search(message))
    is_status = bool(_PAT_STATUS_QUERY.search(message))
    has_figure = bool(_PAT_FIGURE_ACTION.search(message))
    has_data_audit = bool(_PAT_DATA_AUDIT.search(message))
    has_code = bool(_PAT_CODE_ACTION.search(message))
    has_paper = bool(_PAT_PAPER_ACTION.search(message))

    kept: List[str] = []
    dropped: List[str] = []
    for agent in agents:
        if agent == "context_source_truth":
            kept.append(agent); continue
        drop = False
        # validation_skeptic only when MD context OR paper/claim context
        # (claims need validation evidence even without MD mentioned).
        if agent == "validation_skeptic" and not has_md and not has_paper:
            drop = True
        elif agent == "model_training" and is_status and not has_training:
            drop = True
        elif agent == "code_builder" and is_status and not has_code:
            drop = True
        elif agent == "leakage_split" and has_figure and not (has_leakage or has_training or has_data_audit):
            drop = True
        elif agent == "leakage_split" and is_status and not (has_leakage or has_training):
            drop = True
        elif agent == "paper_claim" and has_code and not has_paper:
            # "Review the evaluation script" should not pull paper_claim.
            drop = True
        if drop:
            dropped.append(agent)
        else:
            kept.append(agent)
    return kept, dropped


class Router:
    def __init__(
        self,
        memory_store: Optional[MemoryStore] = None,
        registry_store: Optional[RegistryStore] = None,
        *,
        repo_root: "str | Path" = ".",
        semantic_router: Optional[OllamaSemanticRouter] = None,
        claude_fallback: Optional[ClaudeFallback] = None,
        enable_semantic: Optional[bool] = None,
    ):
        self.memory_store = memory_store
        self.registry_store = registry_store
        self.repo_root = Path(repo_root)
        # Injectable for tests; default is the real Ollama router.
        self.semantic_router = semantic_router or OllamaSemanticRouter(self.repo_root)
        self.claude_fallback = claude_fallback or get_default_fallback()
        # Explicit constructor arg wins; falling through to env var keeps the
        # production-time kill switch (RESEARCHOS_DISABLE_SEMANTIC=1) working.
        if enable_semantic is None:
            self.enable_semantic = os.environ.get("RESEARCHOS_DISABLE_SEMANTIC") != "1"
        else:
            self.enable_semantic = enable_semantic

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def route(self, message: str) -> OrchestrationPlan:
        # 1. Always run the deterministic keyword path. It can never hurt and
        #    ensures we have a safe baseline.
        keyword_intents = classify_intent(message)
        keyword_risk = classify_risk(message, keyword_intents)
        keyword_agents = select_agents(keyword_intents, keyword_risk)

        # 2. Try the semantic router. Returns None on failure.
        semantic: Optional[SemanticRouterResult] = None
        if self.enable_semantic:
            try:
                semantic = self.semantic_router.route(message)
            except Exception:
                semantic = None

        # 3. Merge.
        if semantic is None:
            # No semantic result — keyword-only path, with a fallback flag.
            decision = "keyword_only"
            confidence = 0.0
            final_agents = keyword_agents
            final_risk = keyword_risk
            reasoning = "Ollama unavailable or returned no result; deterministic keyword routing used."
            requires_claude = True
            requires_human_from_semantic = False
            ollama_raw: Optional[Dict[str, object]] = None
            workflow = None
        else:
            ollama_raw = semantic.raw_response
            workflow = semantic.selected_workflow
            requires_human_from_semantic = semantic.requires_human_approval
            # Union of agent lists, with context_source_truth first.
            final_agents = self._merge_agents(semantic.selected_agents, keyword_agents)
            final_risk = _max_risk(semantic.risk_level, keyword_risk)
            if semantic.confidence < _CONFIDENCE_FLOOR:
                decision = "low_confidence"
                reasoning = (
                    f"Semantic confidence {semantic.confidence:.2f} below floor "
                    f"{_CONFIDENCE_FLOOR:.2f}; merged with keyword guardrail."
                )
                requires_claude = True
            elif semantic.confidence < _CONFIDENCE_HIGH:
                decision = "merged"
                reasoning = (
                    f"Semantic confidence {semantic.confidence:.2f}; merged with keyword "
                    f"guardrail. {semantic.reasoning_summary}"
                )
                requires_claude = True
            else:
                # High confidence: accept semantic mostly as-is but still keep the
                # union for safety. Mark as semantic.
                decision = "semantic"
                reasoning = semantic.reasoning_summary or "Semantic routing accepted."
                requires_claude = semantic.requires_claude_fallback
            confidence = semantic.confidence
            # High/critical risk always requests Claude Code's judgement.
            if final_risk in ("high", "critical"):
                requires_claude = True

        # 4. Optional Claude API second-opinion (only when AnthropicAPIFallback active).
        if requires_claude:
            try:
                review = self.claude_fallback.review(message, final_agents, final_risk)
            except Exception:
                review = None
            if review is not None:
                final_agents = self._merge_agents(review.selected_agents, final_agents)
                final_risk = _max_risk(review.risk_level, final_risk)
                if review.requires_human_approval:
                    requires_human_from_semantic = True
                decision = "claude_fallback"
                confidence = max(confidence, review.confidence)
                reasoning = f"Claude fallback: {review.reasoning_summary}"
                requires_claude = False  # Already adjudicated by Claude API.

        # 5. Post-merge prune: drop agents that are clearly out of scope for
        #    the prompt. The keyword and LLM unions over-include; this step
        #    is the only way to reliably suppress overreach by small LLMs.
        pruned_agents, dropped_for_prune = _prune_inappropriate_agents(message, final_agents)
        if dropped_for_prune:
            # Re-ensure context_source_truth stays first.
            if "context_source_truth" not in pruned_agents:
                pruned_agents = ["context_source_truth"] + pruned_agents
            final_agents = pruned_agents
            reasoning = (reasoning + (" " if reasoning else "")
                         + f"[pruned: {', '.join(dropped_for_prune)}]")

        # 6. Required gates come from the keyword intents (deterministic, closed vocab).
        gates = determine_required_gates(keyword_intents)
        keyword_human, keyword_human_reason = requires_human_review(
            message, keyword_intents, final_risk
        )
        human_required = keyword_human or requires_human_from_semantic
        human_reason = keyword_human_reason or (
            "Semantic router flagged human approval." if requires_human_from_semantic else ""
        )

        # 7. Context packet uses the keyword intents (since context_builder is
        #    written against the closed INTENT_CLASSES vocab).
        packet = build_context_packet(
            task=message,
            intents=keyword_intents,
            risk_level=final_risk,
            memory_store=self.memory_store,
            registry_store=self.registry_store,
        )

        plan = OrchestrationPlan(
            request_summary=message.strip().splitlines()[0][:280] if message.strip() else "(empty)",
            intents=keyword_intents,
            risk_level=final_risk,
            selected_agents=final_agents,
            required_gates=gates,
            context_packet=packet,
            actions=self._actions_for(keyword_intents, final_agents, gates, final_risk),
            blocked=False,
            block_reason="",
            human_review_required=human_required,
            human_review_reason=human_reason,
            expected_outputs=self._expected_outputs_for(keyword_intents),
            routing_decision=decision,
            routing_confidence=confidence,
            routing_reason=reasoning,
            ollama_response_raw=ollama_raw,
            requires_claude_fallback=requires_claude,
            selected_workflow=workflow,
        )
        plan.validate()
        return plan

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    @staticmethod
    def _merge_agents(primary: List[str], secondary: List[str]) -> List[str]:
        """Return the union of agent lists with context_source_truth first.

        Invalid agent IDs are dropped. Order: context_source_truth first, then
        primary order, then any secondary agents not in primary.
        """
        ordered: List[str] = ["context_source_truth"]
        seen: set = {"context_source_truth"}
        for agent in list(primary) + list(secondary):
            if not isinstance(agent, str):
                continue
            if agent not in AGENT_IDS:
                continue
            if agent in seen:
                continue
            ordered.append(agent)
            seen.add(agent)
        return ordered

    def _actions_for(
        self,
        intents: List[str],
        agents: List[str],
        gates: List[str],
        risk: str,
    ) -> List[str]:
        actions: List[str] = []
        actions.append(f"Run agents in order: {', '.join(agents)}")
        if gates:
            actions.append(f"Evaluate gates: {', '.join(gates)}")
        if "claim_or_paper" in intents:
            actions.append("Block paper writing if claim/validation/leakage gates are not pass.")
        if "training" in intents:
            actions.append("Reject metrics if dataset, leakage, preprocessing, or code gates fail.")
        if "md_or_validation" in intents:
            actions.append("Require explicit MD evidence classification before any validation claim.")
        if "submission_readiness" in intents:
            actions.append("Produce readiness matrix and request human signoff.")
        if "document_ingestion" in intents:
            actions.append("Ingest sources through Agent 21 and update source_registry with provenance.")
        if risk in ("high", "critical"):
            actions.append("Run contradiction hunter at end of pipeline.")
        return actions

    def _expected_outputs_for(self, intents: List[str]) -> List[str]:
        out: List[str] = ["AgentOutput per agent", "OrchestrationPlan JSON"]
        if "training" in intents:
            out.append("Updated experiment_registry + artifact_registry entries")
        if "metric_verification" in intents:
            out.append("Verified metrics JSON with confidence intervals")
        if "md_or_validation" in intents:
            out.append("Validation classification: supports|partially|inconclusive|weakens|contradicts")
        if "claim_or_paper" in intents:
            out.append("Claim audit report with safe-wording replacements")
        if "submission_readiness" in intents:
            out.append("Readiness matrix + human signoff prompt")
        if "document_ingestion" in intents:
            out.append("Source registry entries + ingest report")
        return out


__all__ = ["Router"]
