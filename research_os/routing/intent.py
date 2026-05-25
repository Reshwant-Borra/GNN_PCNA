"""Rule-based intent classifier.

We use simple keyword + phrase matching. The classifier is deliberately
permissive: a single request can match multiple intents (e.g. "write the
results section" -> claim_or_paper + metric_verification + md_or_validation
because the orchestrator should pull all relevant gates).
"""
from __future__ import annotations

import re
from typing import Dict, List, Tuple

from research_os.schemas.vocab import INTENT_CLASSES


# Each intent has (must-match keywords | regex), ordered roughly by priority so
# the canonical example trigger appears first in the resulting list.
_INTENT_PATTERNS: Tuple[Tuple[str, List[str]], ...] = (
    (
        "claim_or_paper",
        [
            r"\bclaim",
            r"\bvalidat(ed|ion|es|e)\b",
            r"\bpaper\b",
            r"\bmanuscript\b",
            r"\babstract\b",
            r"\bresults section\b",
            r"\bwrite\b.*\b(results|discussion|abstract|conclusion|paper|section)\b",
            r"\bdraft\b",
            r"\bdocs?\b",
            r"\bsay\b",
            r"\bdescribe\b",
        ],
    ),
    (
        "md_or_validation",
        [
            r"\bmd\b",
            r"\bmolecular dynamics\b",
            r"\brmsd\b",
            r"\brmsf\b",
            r"\bdccm\b",
            r"\bpocket\b",
            r"\bcryptic\b",
            r"\bvalidation\b",
            r"\btrajector(y|ies)\b",
            r"\bopenmm\b",
        ],
    ),
    (
        "metric_verification",
        [
            r"\bauroc\b",
            r"\bauprc\b",
            r"\bprecision\b",
            r"\brecall\b",
            r"\bf1\b",
            r"\bmcc\b",
            r"\bmetric\b",
            r"\bmetrics\b",
            r"\baccuracy\b",
            r"\benrichment\b",
            r"\bconfidence interval\b",
            r"\bverify\b.*\b(metric|score|number)\b",
            # Statistical analysis: bootstrap, CI, baseline comparison are
            # metric-verification tasks driven by metrics_statistics.
            r"\bbootstrap\b",
            r"\bstatistical\b",
            r"\bstatistics\b",
            r"\bbaselines?\b.*\b(compare|comparison|vs)\b",
            r"\bcompare\b.*\bbaselines?\b",
        ],
    ),
    (
        "split_or_leakage",
        [
            r"\bleak(age|y|s|)\b",
            r"\bsplit\b",
            r"\bhomolog\w*\b",
            r"\bchain\b.*\bleak\b",
            r"\bapo/?holo\b",
            r"\btrain/test\b",
            r"\bcross[- ]validation\b",
        ],
    ),
    (
        "preprocessing_audit",
        [
            r"\bpreprocess\w*\b",
            r"\bgraph construction\b",
            r"\bfeatures?\b.*\b(align|normaliz|leak|extract)",
            r"\bresidue map\w*\b",
            r"\blabel align\w*\b",
        ],
    ),
    (
        "data_audit",
        [
            r"\bdataset\b",
            r"\bpdb\b",
            r"\blabels?\b",
            r"\bground truth\b",
            r"\bdata quality\b",
            r"\bnegatives\b",
            r"\bpositives\b",
            r"\bresidues?\b",
        ],
    ),
    (
        "training",
        [
            r"\btrain(?:ing|ed|s)?\b",
            r"\bretrain(?:ing|ed|s)?\b",
            r"\bfit\b.*\bmodel\b",
            r"\bfine[- ]?tun(?:e|ed|ing)\b",
            r"\bcheckpoint\b",
            r"\bepoch\b",
        ],
    ),
    (
        "compute_planning",
        [
            r"\bcompute\b",
            r"\bgpu\b",
            r"\bcloud\b",
            r"\bbudget\b",
            r"\bstorage\b",
            r"\bcost\b",
            r"\bplan\b.*\b(md|gpu|run)\b",
            r"\bruntime\b",
            r"\bschedule\b.*\brun\b",
        ],
    ),
    (
        "code_review",
        [
            r"\breview\b.*\b(code|script|module|function)\b",
            r"\bcode review\b",
            r"\baudit\b.*\b(code|script)\b",
        ],
    ),
    (
        "code_build",
        [
            r"\bimplement\b",
            r"\bbuild\b",
            r"\bwrite\b.*\b(script|function|module|tests?)\b",
            r"\brefactor\b",
            r"\bfix\b.*\b(bug|test|code|script)\b",
            r"\bcreate\b.*\b(cli|module|script|tests?)\b",
        ],
    ),
    (
        "figure_generation",
        [
            r"\bfigure\b",
            r"\bplot\b",
            r"\bvisuali[sz]e\b",
            r"\bchart\b",
            r"\bheatmap\b",
            r"\brender\b",
        ],
    ),
    (
        "submission_readiness",
        [
            r"\bsubmit\b",
            r"\bsubmission\b",
            r"\bready\b",
            r"\bpreprint\b",
            r"\bpublish\b",
            r"\brelease\b",
            r"\bhandoff\b",
            r"\bship\b",
        ],
    ),
    (
        "collaboration_sync",
        [
            r"\bcollaborat\w*\b",
            r"\bfriend\b",
            r"\bpull\b.*\b(branch|commit|repo|files?)\b",
            r"\bsync\b",
            r"\bteammate\b",
            r"\bhandoff\b",
            # Reviewer simulation goes through reviewer_collaboration agent,
            # which is mapped from this intent. Keyword fallback must catch
            # "what will reviewers ask?" / "simulate reviewer concerns" too.
            r"\breviewers?\b",
            r"\bpeer[\s-]?review\b",
            r"\bsimulate\b.*\breview\w*\b",
        ],
    ),
    (
        "document_ingestion",
        [
            r"\bingest\b",
            r"\bupload\b.*\b(source|paper|document|pdf|transcript|note)",
            r"\badd\b.*\b(source|paper|document|pdf|transcript|note)",
            r"\bindex\b.*\b(source|paper|document|pdf|transcript|note)",
            r"\bsource registry\b",
            r"\bdocument ingestion\b",
            r"\bknowledge ingestion\b",
            r"\bagent 21\b",
            # Literature-style prompts: route through document_ingestion so the
            # keyword fallback (when Ollama is down) still pulls in
            # literature_web + document_knowledge_ingestion.
            r"\bfind\b.*\b(papers?|articles?|literature|citations?|references?)\b",
            r"\bpull\b.*\bcitations?\b",
            r"\bget\b.*\b(papers?|articles?|citations?)\b",
            r"\bsearch\b.*\b(papers?|articles?|literature)\b",
            r"\bpub[\s-]?med\b",
            r"\barxiv\b",
            r"\bliterature\b",
            r"\bcitations?\b",
            r"\brelated work\b",
            r"\bprior work\b",
            r"\bsurvey\b",
            r"\bresearch\b.*\b(how|what|why)\b",
        ],
    ),
    (
        "contradiction_hunt",
        [
            r"\bcontradict\w*\b",
            r"\bhidden\b.*\b(bug|issue|problem|conflict)\b",
            r"\bfind\b.*\b(bug|issue|conflict|contradiction)\b",
            r"\bbreak\b.*\b(project|paper|claim|evidence)\b",
        ],
    ),
    (
        "research_design",
        [
            r"\bhypothesis\b",
            r"\bresearch question\b",
            r"\bfalsif\w*\b",
            r"\bnull hypothesis\b",
            r"\bdesign\b.*\b(experiment|study|research)\b",
            r"\broadmap\b",
            r"\bwhat should\b",
            r"\bwhat to do next\b",
            r"\bplan\b.*\bexperiment\b",
        ],
    ),
    (
        "source_of_truth_query",
        [
            r"\blatest\b",
            r"\bcurrent\b",
            r"\bstale\b",
            r"\bwhat is\b",
            r"\bwhat's\b",
            r"\bwhich (checkpoint|metric|dataset|split|file)\b",
            r"\bsource of truth\b",
            r"\bsummary\b",
            r"\bstatus\b",
            r"\bshow me\b",
        ],
    ),
)


def _compile_patterns() -> Dict[str, List[re.Pattern[str]]]:
    return {
        intent: [re.compile(pat, re.IGNORECASE) for pat in patterns]
        for intent, patterns in _INTENT_PATTERNS
    }


_COMPILED = _compile_patterns()


def classify_intent(message: str) -> List[str]:
    """Return the list of intents matched, in priority order, deduplicated.

    If nothing matches, returns ``["general"]`` so the orchestrator still
    routes through the Context Agent before deciding the next step.
    """
    if not message or not message.strip():
        return ["general"]
    matched: List[str] = []
    seen: set[str] = set()
    for intent, patterns in _INTENT_PATTERNS:
        compiled = _COMPILED[intent]
        if any(p.search(message) for p in compiled):
            if intent not in seen:
                matched.append(intent)
                seen.add(intent)
    # Cross-intent escalation: a "validation claim" should also pull the
    # contradiction hunter (per docs/02_ORCHESTRATOR_ROUTING_SPEC.md trigger
    # examples).
    if "claim_or_paper" in matched and "contradiction_hunt" not in matched:
        matched.append("contradiction_hunt")
    if not matched:
        matched = ["general"]
    # Guard: every returned intent must be in the closed vocabulary.
    for intent in matched:
        if intent not in INTENT_CLASSES:
            raise ValueError(f"Internal: intent {intent!r} not in INTENT_CLASSES")
    return matched


__all__ = ["classify_intent"]
