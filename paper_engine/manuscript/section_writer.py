"""Draft one manuscript section with the local LLM, grounded and anti-overclaim.

The writer may use only the fact sheet, may cite only the provided references,
must obey the governance guardrails, and is conditioned on the project's voice.
After generation the output is scanned for the project's disallowed phrases
(imported from ResearchOS); a hit triggers one corrective regeneration, then a
safe-substitution fallback. If the LLM is unavailable a deterministic fact-based
stub is produced so the document always assembles (clearly marked).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional

from paper_engine import llm
from paper_engine.manuscript.bibliography import Reference, to_prompt_block
from paper_engine.manuscript.facts import FactSheet
from paper_engine.manuscript.narrative import SectionPlan
from paper_engine.manuscript.voice import StyleBrief

try:  # the canonical banned-phrase list lives in ResearchOS
    from research_os.agents.base import any_phrase_in_text
    from research_os.agents.communication import _DISALLOWED_PAPER_WORDING as DISALLOWED
except Exception:  # pragma: no cover - fallback if research_os not importable
    DISALLOWED = (
        "validated cryptic pocket", "confirmed novel residues", "MD proves opening",
        "MD validates", "discovered binding site", "generalizes broadly",
        "experimentally validated", "causal mechanism",
    )

    def any_phrase_in_text(phrases, text, gap=2):
        return [p for p in phrases if p.lower() in text.lower()]


# Safe replacements applied if a banned phrase survives regeneration.
_SAFE_SUBSTITUTIONS = [
    (r"validated cryptic pocket", "candidate cryptic-pocket region"),
    (r"discovered (a )?binding site", "highlighted a candidate binding region"),
    (r"confirmed novel residues", "candidate residues"),
    (r"experimentally validated", "computationally predicted"),
    (r"MD validates?", "MD exploratorily characterizes"),
    (r"MD proves opening", "MD shows local flexibility"),
    (r"generalizes broadly", "may generalize, pending further testing"),
    (r"causal mechanism", "association"),
]

SYSTEM_PROMPT = (
    "You are drafting ONE section of a high-school science-competition research paper "
    "about a graph neural network that predicts candidate cryptic-pocket residues in "
    "PCNA, a cancer-relevant protein. Write polished, specific academic prose.\n"
    "ABSOLUTE RULES:\n"
    "1. Use ONLY the facts in the FACTS block. Never invent numbers, datasets, "
    "citations, p-values, or results.\n"
    "2. The test set was NOT evaluated. Never state or imply any test-set performance.\n"
    "3. Banned wording (and close variants): 'validated/confirmed/discovered/proved "
    "pocket or binding site', 'MD validates', 'experimentally validated', 'generalizes "
    "broadly', 'causal mechanism'. Use candidate-region, computationally-predicted, "
    "and requires-further-validation language instead.\n"
    "4. macro-AUPRC is the primary metric; AUROC is inflated at ~4.6% prevalence.\n"
    "5. Cite only from the provided reference list, as [n]. Do not add a reference list.\n"
    "6. Output ONLY the section's prose paragraphs — no heading, no markdown, no "
    "bullet lists, no preamble like 'Here is'.\n"
    "7. VARY your opening sentence. Never begin a section the same way as an earlier "
    "section, and never open with 'Based on validation macro-AUPRC...'. Do not repeat "
    "whole sentences verbatim across sections."
)


@dataclass
class SectionResult:
    section_id: str
    heading: str
    text: str
    word_count: int
    used_llm: bool
    banned_hits: List[str] = field(default_factory=list)
    figures: List[str] = field(default_factory=list)


def _retrieved_context(section: SectionPlan, k: int = 3) -> str:
    """Optional RAG: pull real snippets from the corpus index if one is built."""
    try:
        from paper_engine.corpus import index as corpus_index

        query = (f"{section.heading} PCNA cryptic pocket graph neural network "
                 + " ".join(section.reviewer_questions))
        hits = corpus_index.search(query, k=k)
    except Exception:
        return ""
    if not hits:
        return ""
    lines = ["RELEVANT LITERATURE CONTEXT (real snippets retrieved from the corpus for "
             "grounding — use for context only, do not fabricate beyond them):"]
    for h in hits:
        doi = f" doi:{h.doi}" if h.doi else ""
        lines.append(f"- {h.title}{doi}: {h.snippet[:220]}")
    return "\n".join(lines)


def _build_prompt(section: SectionPlan, facts: FactSheet, style: StyleBrief,
                  refs: List[Reference], prior_headings: List[str],
                  prior_openings: List[str], retrieved: str) -> str:
    qs = ""
    if section.reviewer_questions:
        qs = "ANSWER THESE JUDGE/REVIEWER QUESTIONS implicitly:\n- " + \
             "\n- ".join(section.reviewer_questions) + "\n"
    prior = ""
    if prior_headings:
        prior = ("ALREADY-WRITTEN SECTIONS (do not repeat their content): "
                 + ", ".join(prior_headings) + "\n")
    avoid = ""
    if prior_openings:
        avoid = ("DO NOT open with any of these phrasings already used:\n- "
                 + "\n- ".join(o[:80] for o in prior_openings) + "\n")
    rag = f"--- {retrieved}\n\n" if retrieved else ""
    return (
        f"SECTION TO WRITE: {section.heading}\n"
        f"PURPOSE: {section.purpose}\n"
        f"INSTRUCTIONS: {section.guidance}\n"
        f"TARGET LENGTH: about {section.target_words} words.\n"
        f"{qs}{prior}{avoid}\n"
        f"--- FACTS (the only results you may state) ---\n{facts.to_prompt_block()}\n\n"
        f"{rag}"
        f"--- {style.to_prompt_block()}\n\n"
        f"--- REFERENCES ---\n{to_prompt_block(refs)}\n\n"
        f"Write the {section.heading} section now."
    )


def _fallback_text(section: SectionPlan, facts: FactSheet) -> str:
    """Deterministic, fact-grounded stub when the LLM is unavailable."""
    p = facts.primary
    base = {
        "abstract": (
            f"PCNA is a clinically important but historically hard-to-target protein. "
            f"This work trains a leakage-controlled graph neural network to highlight "
            f"candidate cryptic-pocket residues at the residue level. On a frozen, "
            f"homology-blocked split, the primary {p['display']} model reaches a "
            f"validation macro-AUPRC of {p['mean']:.3f} +/- {p['sd']:.3f}, above naive "
            f"and ablated baselines. The test set is reserved for a single future "
            f"human-authorized evaluation. Results are computational and require "
            f"further validation."),
    }
    return base.get(section.section_id, (
        f"[Draft pending language model] This {section.heading} section will be "
        f"written from the grounded fact sheet. Key figure(s): "
        f"{', '.join(section.figures) or 'none'}."))


def _sanitize(text: str) -> str:
    for pattern, repl in _SAFE_SUBSTITUTIONS:
        text = re.sub(pattern, repl, text, flags=re.IGNORECASE)
    return text


_BOILERPLATE_OPENER = re.compile(r"^\s*Based on [^:]{0,90}:\s*", re.IGNORECASE)


def _clean(text: str) -> str:
    text = text.strip()
    # Drop a stray leading "Here is..." or repeated heading line.
    text = re.sub(r"^(here is|here's|below is)[^\n]*\n", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^#+\s.*\n", "", text)
    # Strip the model's recurring "Based on validation macro-AUPRC...:" stock opener.
    stripped = _BOILERPLATE_OPENER.sub("", text, count=1)
    if stripped != text and stripped:
        text = stripped[0].upper() + stripped[1:]
    return text.strip()


def write_section(section: SectionPlan, facts: FactSheet, style: StyleBrief,
                  refs: List[Reference], prior_headings: List[str],
                  prior_openings: Optional[List[str]] = None) -> SectionResult:
    retrieved = _retrieved_context(section)
    prompt = _build_prompt(section, facts, style, refs, prior_headings,
                           prior_openings or [], retrieved)
    # Cap output near the section's real length (it stops naturally anyway). A tight
    # cap bounds worst-case latency so parallel streams don't blow the timeout.
    num_predict = min(800, int(section.target_words * 3.5) + 150)
    text = llm.generate(prompt, system=SYSTEM_PROMPT, num_predict=num_predict)
    used_llm = text is not None
    if not used_llm:
        text = _fallback_text(section, facts)
    text = _clean(text)

    banned = any_phrase_in_text(DISALLOWED, text)
    if banned and used_llm:
        retry_prompt = (
            prompt + "\n\nYOUR PREVIOUS DRAFT USED BANNED WORDING: "
            + "; ".join(banned)
            + ". Rewrite the section completely without any banned wording, keeping all "
            "facts accurate.")
        retry = llm.generate(retry_prompt, system=SYSTEM_PROMPT, num_predict=num_predict)
        if retry:
            text = _clean(retry)
            banned = any_phrase_in_text(DISALLOWED, text)
    if banned:  # last-resort safe substitution
        text = _sanitize(text)
        banned = any_phrase_in_text(DISALLOWED, text)

    return SectionResult(
        section_id=section.section_id, heading=section.heading, text=text,
        word_count=len(text.split()), used_llm=used_llm, banned_hits=list(banned),
        figures=list(section.figures),
    )
