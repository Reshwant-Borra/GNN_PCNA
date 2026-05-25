"""Risk classifier.

Risk is shaped by what's at stake if we get the answer wrong: a routine
question about the latest AUROC is medium risk, while running 100 ns MD on
the cloud is critical because it's expensive and irreversible.
"""
from __future__ import annotations

import re
from typing import List

_CRITICAL_PATTERNS = [
    re.compile(p, re.IGNORECASE)
    for p in (
        r"\bsubmit\b",
        r"\bpublish\b",
        r"\bpreprint\b",
        r"\bproduction\b",
        r"\bfinal\b",
        r"\bdelete\b",
        r"\bforce[\s-]?merge\b",
        r"\bforce[\s-]?push\b",
        r"\bwipe\b",
        r"\bstart over\b",
        r"\b100\s*ns\b",
        r"\bcloud\b.*\b(run|md|train|gpu)\b",
        r"\bexpensive\b",
        r"\bcommit\b.*\b(?:major|paper|claim)\b",
        r"\bvalidated cryptic\b",
        r"\bvalidate\b.*\bcryptic\b",
        r"\bmd\b.*\bvalidat\w*\b",
        r"\bcan we say\b",
        r"\bconfirmed novel\b",
        r"\bdrop (table|database)\b",
    )
]

_HIGH_PATTERNS = [
    re.compile(p, re.IGNORECASE)
    for p in (
        r"\btrain\b",
        r"\bretrain\b",
        r"\bsplit\b",
        r"\bleak\w*\b",
        r"\bclaim\b",
        r"\bvalidat\w*\b",
        r"\bmd\b",
        r"\bcheckpoint\b",
        r"\bmetric\b",
        r"\bfigure\b",
    )
]

_LOW_PATTERNS = [
    re.compile(p, re.IGNORECASE)
    for p in (
        r"\bwhat is\b",
        r"\bshow\b",
        r"\bsummary\b",
        r"\bexplain\b",
        r"\bcomment\b",
        r"\bdescribe\b",
        r"\bhelp\b",
    )
]


def classify_risk(message: str, intents: List[str]) -> str:
    if not message:
        return "medium"
    intent_set = set(intents or [])
    # Critical pre-empts everything.
    for pat in _CRITICAL_PATTERNS:
        if pat.search(message):
            return "critical"
    if "submission_readiness" in intent_set:
        return "critical"
    if "compute_planning" in intent_set and any(
        p.search(message) for p in _CRITICAL_PATTERNS
    ):
        return "critical"
    # Source-of-truth / status queries are read-only: even when the prompt
    # references a high-risk topic word ("show me the training history"),
    # the action is just to *look up* state — risk stays low/medium.
    # We only allow this demotion when no destructive verb is present.
    destructive_present = bool(re.search(
        r"\b(delete|remove|drop|overwrite|wipe|submit|publish|preprint|force[\s-]?merge|force[\s-]?push)\b",
        message, re.IGNORECASE,
    ))
    if "source_of_truth_query" in intent_set and not destructive_present:
        return "low"
    if intent_set & {
        "training",
        "claim_or_paper",
        "md_or_validation",
        "split_or_leakage",
        "metric_verification",
        "preprocessing_audit",
        "contradiction_hunt",
    }:
        return "high"
    if any(pat.search(message) for pat in _HIGH_PATTERNS):
        return "high"
    if any(pat.search(message) for pat in _LOW_PATTERNS):
        return "low"
    return "medium"


__all__ = ["classify_risk"]
