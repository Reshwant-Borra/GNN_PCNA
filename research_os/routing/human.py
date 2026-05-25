"""Human-approval classifier.

Per docs/05_HUMAN_INTERVENTION_MODEL.md, the human is invoked for:

- expensive compute,
- dataset/split protocol changes,
- claim strength upgrades or major downgrades,
- contradictory validation interpretation,
- irreversible actions,
- final figures,
- submission,
- agent disagreement on a major conclusion.

The router can spot most of these directly from the message; the rest get
flagged later by individual agents.
"""
from __future__ import annotations

import re
from typing import List, Tuple

from research_os.agents.base import phrase_in_text

_TRIGGERS: Tuple[Tuple[str, str], ...] = (
    (
        r"\bsubmit\b|\bsubmission\b|\bpreprint\b|\bpublish\b|\brelease\b",
        "submission/publication is a Level-4 PI decision",
    ),
    (
        r"\b100\s*ns\b|\b\d{2,}\s*ns\b|\bcloud\b.*\b(md|gpu|train|run)\b|\bexpensive\b|\bbudget\b",
        "expensive compute requires explicit PI go/no-go",
    ),
    (
        r"\bsplit protocol\b|\bdataset protocol\b|\bredefine label\b|\brelabel\b",
        "dataset or split protocol changes require PI approval",
    ),
    (
        r"\bdelete\b|\bdrop\b|\bremove\b.*\b(artifact|checkpoint|trajectory|split|dataset|registry)\b",
        "irreversible artifact deletion requires PI approval",
    ),
    (
        r"\bforce[\s-]?merge\b|\bforce[\s-]?push\b|\bwipe\b|\boverwrite\b.*\bmain\b",
        "force-merge / wipe is irreversible and requires PI approval",
    ),
    (
        r"\bdelete\b.*\b(registry|experiment|memory)\b|\bstart over\b",
        "deleting registries or starting over wipes provenance; requires PI approval",
    ),
    (
        r"\bfinal figure\b|\bfinal abstract\b|\bfinal manuscript\b|\bfinal paper\b",
        "final figures and final manuscript wording require PI approval",
    ),
)


# Loose-phrase triggers. These tolerate intervening articles like
# "MD validated [the/this] cryptic pocket" so we don't miss claim-upgrade
# requests because of one filler word.
_LOOSE_PHRASE_TRIGGERS: Tuple[Tuple[str, str], ...] = (
    ("validated cryptic pocket", "claim upgrade: 'validated cryptic pocket' wording requires PI approval"),
    ("MD validated", "'MD validated' wording is a claim upgrade; PI approval required"),
    ("MD validate", "'MD validate' wording is a claim upgrade; PI approval required"),
    ("MD validates", "'MD validates' wording is a claim upgrade; PI approval required"),
    ("md validate the cryptic", "claim upgrade: validating the cryptic pocket requires PI approval"),
    ("MD proves opening", "'MD proves opening' wording is a claim upgrade; PI approval required"),
    ("confirmed novel residues", "'confirmed novel residues' wording is a claim upgrade; PI approval required"),
    ("discovered binding site", "'discovered binding site' wording is a claim upgrade; PI approval required"),
    ("experimentally validated", "'experimentally validated' wording is a major claim; PI approval required"),
    ("proved", "'proved' wording is a major claim; PI approval required"),
    ("can we say", "claim-wording question requires PI approval before publication"),
)


def requires_human_review(
    message: str, intents: List[str], risk_level: str
) -> Tuple[bool, str]:
    """Return (required, reason)."""
    if "submission_readiness" in intents:
        return True, "submission readiness audit is a Level-4 PI decision"
    if risk_level == "critical":
        # Critical risk requires at least an acknowledgement, even if not a hard veto.
        # We surface a reason but keep the door open for the agent layer to refine.
        for pat, reason in _TRIGGERS:
            if re.search(pat, message, re.IGNORECASE):
                return True, reason
        for phrase, reason in _LOOSE_PHRASE_TRIGGERS:
            if phrase_in_text(phrase, message):
                return True, reason
        return True, "request was classified critical risk; PI confirmation required"
    for pat, reason in _TRIGGERS:
        if re.search(pat, message, re.IGNORECASE):
            return True, reason
    for phrase, reason in _LOOSE_PHRASE_TRIGGERS:
        if phrase_in_text(phrase, message):
            return True, reason
    return False, ""


__all__ = ["requires_human_review"]
