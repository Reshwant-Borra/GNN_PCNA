"""Claude fallback layer for routing.

Two modes:

- ``FlagOnlyFallback`` (default) — the router annotates the plan with
  ``requires_claude_fallback=True`` and lets Claude Code (the interactive
  session calling the MCP) make the final routing call. Zero new
  dependencies, zero API cost, full transparency.

- ``AnthropicAPIFallback`` — calls the Anthropic Claude API directly. Only
  activated when ``RESEARCHOS_CLAUDE_FALLBACK_API=1`` is set in the
  environment **and** the ``anthropic`` SDK is importable. Falls back to
  flag-only mode silently if either condition isn't met.

Both implement the same ``ClaudeFallback`` protocol so the caller doesn't
care which one is active.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Protocol

from research_os.routing._llm_json import extract_json
from research_os.schemas.vocab import AGENT_IDS, RISK_LEVELS


# Reasonable default — Claude 4.7 Sonnet is fine for routing.
DEFAULT_CLAUDE_MODEL = os.environ.get("RESEARCHOS_CLAUDE_MODEL", "claude-sonnet-4-6")


@dataclass
class ClaudeFallbackResult:
    """Output of a Claude fallback decision."""
    selected_agents: List[str]
    risk_level: str
    confidence: float
    reasoning_summary: str
    requires_human_approval: bool
    raw_response: Optional[Dict[str, Any]] = None
    mode: str = "flag_only"  # one of: flag_only, anthropic_api


class ClaudeFallback(Protocol):
    """Common interface."""
    mode: str
    def review(self, message: str, current_agents: List[str], current_risk: str) -> Optional[ClaudeFallbackResult]: ...


class FlagOnlyFallback:
    """Default mode: do not call any external API.

    ``review`` returns ``None``, signaling that the caller should keep the
    current agent selection and just mark ``requires_claude_fallback=True``
    on the plan so the surrounding Claude Code session can act.
    """
    mode = "flag_only"

    def review(
        self,
        message: str,
        current_agents: List[str],
        current_risk: str,
    ) -> Optional[ClaudeFallbackResult]:
        return None


class AnthropicAPIFallback:
    """Active mode: call Anthropic Claude API to second-opinion the routing.

    This is opt-in. We import ``anthropic`` lazily inside ``review`` so the
    SDK isn't required at install time.
    """
    mode = "anthropic_api"

    def __init__(self, model: str = DEFAULT_CLAUDE_MODEL) -> None:
        self.model = model

    def review(
        self,
        message: str,
        current_agents: List[str],
        current_risk: str,
    ) -> Optional[ClaudeFallbackResult]:
        try:
            import anthropic  # type: ignore[import-not-found]
        except ImportError:
            return None
        if not os.environ.get("ANTHROPIC_API_KEY"):
            return None
        try:
            client = anthropic.Anthropic()
            resp = client.messages.create(
                model=self.model,
                max_tokens=512,
                temperature=0,
                system=(
                    "You are reviewing a routing decision for ResearchOS. The local "
                    "semantic router selected these agents. Decide whether to keep, "
                    "add, or remove agents. Output STRICT JSON only:\n"
                    "{\"selected_agents\":[...], \"risk_level\":\"low|medium|high|critical\", "
                    "\"confidence\":0-1, \"reasoning_summary\":\"...\", \"requires_human_approval\":bool}"
                ),
                messages=[{
                    "role": "user",
                    "content": (
                        f"Prompt: {message}\n"
                        f"Current agents: {json.dumps(current_agents)}\n"
                        f"Current risk: {current_risk}\n"
                        f"Valid agent IDs: {json.dumps(list(AGENT_IDS))}\n"
                        "Emit the JSON now."
                    ),
                }],
            )
            content = resp.content[0].text if resp.content else ""
        except Exception:
            return None

        parsed = extract_json(content)
        if not parsed:
            return None

        agents_raw = parsed.get("selected_agents") or []
        if not isinstance(agents_raw, list):
            return None
        agents = [a for a in agents_raw if isinstance(a, str) and a in AGENT_IDS]
        if not agents:
            return None
        if "context_source_truth" not in agents:
            agents.insert(0, "context_source_truth")

        risk = str(parsed.get("risk_level") or current_risk).lower()
        if risk not in RISK_LEVELS:
            risk = current_risk

        try:
            confidence = float(parsed.get("confidence") or 0.0)
        except (TypeError, ValueError):
            confidence = 0.0
        confidence = max(0.0, min(1.0, confidence))

        return ClaudeFallbackResult(
            selected_agents=agents,
            risk_level=risk,
            confidence=confidence,
            reasoning_summary=str(parsed.get("reasoning_summary") or ""),
            requires_human_approval=bool(parsed.get("requires_human_approval", False)),
            raw_response=parsed,
            mode=self.mode,
        )


def get_default_fallback() -> ClaudeFallback:
    """Pick the right fallback based on env. Defaults to flag-only."""
    if os.environ.get("RESEARCHOS_CLAUDE_FALLBACK_API") == "1":
        return AnthropicAPIFallback()
    return FlagOnlyFallback()


__all__ = [
    "ClaudeFallback",
    "ClaudeFallbackResult",
    "FlagOnlyFallback",
    "AnthropicAPIFallback",
    "get_default_fallback",
    "DEFAULT_CLAUDE_MODEL",
]
