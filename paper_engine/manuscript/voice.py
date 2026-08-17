"""Voice conditioning.

Authentic-voice authorship (the integrity-preserving replacement for
"undetectable by AI") works by conditioning the writer on the project's own
prior prose: its tone, hedging style, sentence rhythm, and terminology. This
module reads existing wiki/report writing, extracts a compact style brief plus a
few representative exemplar sentences, and exposes them for the section writer to
imitate. It degrades to a sane default if no prior writing is found.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from paper_engine import config

# Source files for the project's voice (terminology + tone), most representative first.
_VOICE_GLOBS = [
    ("wiki/overview.md", 1),
    ("wiki/analyses/*.md", 6),
    ("wiki/concepts/*.md", 4),
    ("reports/phase3/*.md", 3),
]

_DOMAIN_TERMS = [
    "cryptic pocket", "candidate", "residue", "leakage", "homology", "split",
    "macro-AUPRC", "validation", "baseline", "GraphSAGE", "ESM2", "PCNA",
    "governance", "frozen", "exploratory", "ablation",
]


@dataclass
class StyleBrief:
    avg_sentence_words: float
    hedging_ratio: float
    first_person: bool
    top_terms: List[str]
    exemplars: List[str] = field(default_factory=list)
    n_files: int = 0

    def to_prompt_block(self) -> str:
        if self.n_files == 0:
            return (
                "VOICE: clear, precise, lightly hedged academic English; define terms on "
                "first use; prefer concrete statements grounded in the data."
            )
        tone = "cautious and precise" if self.hedging_ratio > 0.02 else "direct and precise"
        person = "first person plural ('we')" if self.first_person else "impersonal"
        # NB: we deliberately do NOT feed verbatim exemplar sentences — small models
        # copy them into the output. We describe the style abstractly instead.
        return "\n".join([
            "VOICE — write original prose in the project's style:",
            f"- {tone}; {person}; ~{self.avg_sentence_words:.0f} words/sentence on average.",
            f"- Use this terminology naturally: {', '.join(self.top_terms[:10])}.",
            "- Define terms on first use and hedge claims appropriately. Write entirely "
            "original sentences; never copy example or instruction text.",
        ])


def _iter_source_files() -> List[Path]:
    files: List[Path] = []
    for pattern, limit in _VOICE_GLOBS:
        base = config.SCIENCE_ROOT
        if "*" in pattern:
            matches = sorted(base.glob(pattern))[:limit]
        else:
            p = base / pattern
            matches = [p] if p.exists() else []
        files.extend(matches)
    return files


def _sentences(text: str) -> List[str]:
    # Strip markdown headers/code/links before splitting.
    text = re.sub(r"```.*?```", " ", text, flags=re.DOTALL)
    text = re.sub(r"`[^`]*`", " ", text)
    text = re.sub(r"^#+.*$", " ", text, flags=re.MULTILINE)
    text = re.sub(r"^[\-\*\|].*$", " ", text, flags=re.MULTILINE)
    text = re.sub(r"\[(.*?)\]\(.*?\)", r"\1", text)
    text = re.sub(r"\s+", " ", text)
    parts = re.split(r"(?<=[.!?])\s+", text)
    return [s.strip() for s in parts if s.strip()]


def build_style_brief() -> StyleBrief:
    files = _iter_source_files()
    if not files:
        return StyleBrief(0.0, 0.0, False, [], [], 0)

    all_sentences: List[str] = []
    for f in files:
        try:
            all_sentences.extend(_sentences(f.read_text(encoding="utf-8", errors="ignore")))
        except Exception:
            continue
    if not all_sentences:
        return StyleBrief(0.0, 0.0, False, [], [], 0)

    word_counts = [len(s.split()) for s in all_sentences]
    avg_len = sum(word_counts) / len(word_counts)
    hedges = ("may", "might", "suggest", "appear", "likely", "could", "possibly",
              "indicate", "consistent with", "not yet", "requires")
    hedge_hits = sum(1 for s in all_sentences for h in hedges if h in s.lower())
    hedging_ratio = hedge_hits / max(len(all_sentences), 1)
    first_person = any(re.search(r"\bwe\b", s.lower()) for s in all_sentences)

    blob = " ".join(all_sentences).lower()
    top_terms = [t for t in _DOMAIN_TERMS if t.lower() in blob]

    # Exemplars: declarative, medium-length, term-bearing sentences.
    scored = []
    for s in all_sentences:
        n = len(s.split())
        # Reject sentences with orphaned punctuation left by stripped inline code/paths.
        if re.search(r"\s[;,]\s|\s\.\s|\s[;,.]$|\(\s*\)", s):
            continue
        if 12 <= n <= 30 and s[0:1].isupper() and not s.endswith(":"):
            score = sum(1 for t in _DOMAIN_TERMS if t.lower() in s.lower())
            if score:
                scored.append((score, s))
    scored.sort(key=lambda x: (-x[0], len(x[1])))
    exemplars = [s for _, s in scored[:4]]

    return StyleBrief(
        avg_sentence_words=avg_len, hedging_ratio=hedging_ratio,
        first_person=first_person, top_terms=top_terms, exemplars=exemplars,
        n_files=len(files),
    )


if __name__ == "__main__":  # pragma: no cover
    print(build_style_brief().to_prompt_block())
