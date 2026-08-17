"""Orchestrate end-to-end manuscript generation.

Pipeline: ensure figures exist -> assemble grounding fact sheet + voice + real
references -> plan the judge-flow sections -> draft each with the local LLM
(grounded, anti-overclaim) -> finalize citations -> assemble the .docx (and a
markdown twin for review) -> write a provenance manifest. The output is an
explicitly-marked DRAFT; finalization/submission stays human-gated (Phase E).
"""
from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, List

from paper_engine import config
from paper_engine.figures import md as md_mod
from paper_engine.figures import render
from paper_engine.manuscript import assemble_docx
from paper_engine.manuscript.bibliography import (
    apply_remap, finalize_citations, load_references)
from paper_engine.manuscript.facts import build_fact_sheet
from paper_engine.manuscript.narrative import THROUGHLINE, build_plan
from paper_engine.manuscript.section_writer import SectionResult, write_section
from paper_engine.manuscript.voice import build_style_brief

TITLE = ("Leakage-Controlled Graph Neural Networks for Residue-Level "
         "Cryptic-Pocket Prediction in PCNA")
SUBTITLE = "An honestly-evaluated computational pipeline"
DRAFT_NOTICE = (
    "AUTO-GENERATED DRAFT. Every figure and statistic is computed from the project's "
    "real validation data; the held-out test set was not evaluated. This draft requires "
    "human review, revision, and verification before any submission."
)


@dataclass
class BuildResult:
    docx_path: str
    markdown_path: str
    manifest_path: str
    section_count: int
    figures_used: List[str]
    banned_hits: Dict[str, List[str]] = field(default_factory=dict)
    used_llm_sections: int = 0


def _load_figure_map() -> Dict[str, dict]:
    manifest = config.FIGURES_DIR / "figures_manifest.json"
    if not manifest.exists():
        return {}
    data = json.loads(manifest.read_text(encoding="utf-8"))
    return {f["figure_id"]: f for f in data.get("figures", [])}


def _ensure_figures(regenerate: bool) -> None:
    if regenerate:
        render.render_all()
    # Real Phase-5 MD figures (25 ns 1AXC) when the analysis is present; else the
    # trajectory-analysis path (which honestly skips without a topology).
    from paper_engine.figures import md_results
    if md_results.md_available():
        md_results.render_md_results()
        print("[build] real MD figures rendered (25 ns 1AXC triage).")
    else:
        try:
            md_mod.render_md(stride=10)
        except md_mod.MDUnavailable as exc:
            print(f"[build] MD figures skipped: {exc}")


def _write_markdown(meta: dict, sections: List[SectionResult],
                    figure_map: Dict[str, dict], references, out: Path) -> Path:
    lines = [f"# {meta['title']}", f"*{meta['subtitle']}*", "",
             f"**{meta['author']}** · {meta['date']}", "",
             f"> {meta['draft_notice']}", "", f"*Throughline: {THROUGHLINE}*", ""]
    for sec in sections:
        lines.append(f"## {sec.heading}")
        lines.append("")
        lines.append(sec.text)
        lines.append("")
        for fid in sec.figures:
            if fid in figure_map and Path(figure_map[fid]["path"]).exists():
                fm = figure_map[fid]
                rel = Path(fm["path"]).name
                lines.append(f"![{fid}](figures/{rel})")
                lines.append(f"*{fm.get('caption','')}*")
                lines.append("")
    if references:
        lines.append("## References")
        lines.append("")
        for r in references:
            lines.append(f"[{r.idx}] {r.formatted()}")
    out.write_text("\n".join(lines), encoding="utf-8")
    return out


def build_paper(regenerate_figures: bool = True, author: str = "[Author]",
                date: str = "") -> BuildResult:
    config.ensure_output_dirs()
    _ensure_figures(regenerate_figures)
    figure_map = _load_figure_map()

    facts = build_fact_sheet()
    style = build_style_brief()
    references = load_references()
    md_available = facts.md_status.get("available", False)
    plan = build_plan(md_available)

    import os
    from concurrent.futures import ThreadPoolExecutor

    from paper_engine import llm
    llm.warm()  # pre-load the model so the first section doesn't pay cold-start

    # Draft sections concurrently. Sections are largely independent; running several
    # at once keeps all CPU cores busy (a single Ollama stream only uses ~a third of
    # a hybrid CPU) and cuts wall-clock. PAPER_ENGINE_DRAFT_WORKERS controls the
    # degree of parallelism (1 = sequential). Each section still gets the static list
    # of preceding headings; the system prompt enforces opening variety.
    workers = max(1, int(os.environ.get("PAPER_ENGINE_DRAFT_WORKERS", "4")))

    def _draft(item):
        idx, spec = item
        prior_headings = [s.heading for s in plan[:idx]]
        print(f"[build] drafting {spec.heading} ...")
        return write_section(spec, facts, style, references, prior_headings, None)

    items = list(enumerate(plan))
    if workers > 1:
        with ThreadPoolExecutor(max_workers=min(workers, len(plan))) as ex:
            sections = list(ex.map(_draft, items))
        # Sequential retry for any section that timed out under contention and fell
        # back to a stub — full CPU per call, so these complete reliably.
        for i, res in enumerate(sections):
            if not res.used_llm:
                print(f"[build] retry (sequential) {res.heading} ...")
                sections[i] = write_section(
                    plan[i], facts, style, references,
                    [s.heading for s in plan[:i]], None)
    else:
        sections = [_draft(it) for it in items]

    # Opener-dedup: parallel drafting can't share openings, so re-draft any section
    # whose opening n-gram duplicates an earlier one — this time WITH the prior
    # openings so the writer varies it.
    def _opener_key(text: str):
        return tuple(re.findall(r"[a-z]+", text.lower())[:6])

    seen_keys: List[tuple] = []
    for i in range(len(sections)):
        key = _opener_key(sections[i].text)
        if key and any(len(set(key) & set(k)) >= 4 for k in seen_keys):
            prior_op = [s.text.strip().split(". ")[0][:120] for s in sections[:i]]
            print(f"[build] redrafting {plan[i].heading} (duplicate opener) ...")
            sections[i] = write_section(
                plan[i], facts, style, references,
                [s.heading for s in plan[:i]], prior_op)
            key = _opener_key(sections[i].text)
        seen_keys.append(key)

    # Finalize citations across the whole document.
    full_text = "\n".join(s.text for s in sections)
    remap, used_refs = finalize_citations(full_text, references)
    for s in sections:
        s.text = apply_remap(s.text, remap)

    meta = {"title": TITLE, "subtitle": SUBTITLE, "author": author,
            "date": date, "draft_notice": DRAFT_NOTICE}

    docx_path = assemble_docx.build_docx(
        meta, sections, figure_map, used_refs, config.PAPER_DIR / "manuscript.docx")
    md_path = _write_markdown(
        meta, sections, figure_map, used_refs, config.PAPER_DIR / "manuscript.md")

    figures_used = []
    for s in sections:
        for fid in s.figures:
            if fid in figure_map and fid not in figures_used and Path(figure_map[fid]["path"]).exists():
                figures_used.append(fid)
    banned = {s.section_id: s.banned_hits for s in sections if s.banned_hits}

    manifest = {
        "schema": "paper_engine.manuscript/v1",
        "title": TITLE,
        "throughline": THROUGHLINE,
        "draft_notice": DRAFT_NOTICE,
        "md_available": md_available,
        "sections": [
            {"section_id": s.section_id, "heading": s.heading,
             "word_count": s.word_count, "used_llm": s.used_llm,
             "banned_hits": s.banned_hits, "figures": s.figures}
            for s in sections
        ],
        "figures_used": figures_used,
        "references_used": [{"idx": r.idx, "ref": r.formatted()} for r in used_refs],
        "fact_sources": facts.sources,
    }
    manifest_path = config.PAPER_DIR / "build_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    return BuildResult(
        docx_path=str(docx_path), markdown_path=str(md_path),
        manifest_path=str(manifest_path), section_count=len(sections),
        figures_used=figures_used, banned_hits=banned,
        used_llm_sections=sum(1 for s in sections if s.used_llm),
    )


def main() -> None:  # pragma: no cover
    import argparse

    parser = argparse.ArgumentParser(description="Generate the GNN-PCNA competition paper draft.")
    parser.add_argument("--no-figures", action="store_true", help="Skip figure regeneration.")
    parser.add_argument("--author", default="[Author]")
    parser.add_argument("--date", default="")
    args = parser.parse_args()
    result = build_paper(regenerate_figures=not args.no_figures,
                         author=args.author, date=args.date)
    print("\n=== Build complete ===")
    print(f"  DOCX:     {result.docx_path}")
    print(f"  Markdown: {result.markdown_path}")
    print(f"  Manifest: {result.manifest_path}")
    print(f"  Sections: {result.section_count} ({result.used_llm_sections} via LLM)")
    print(f"  Figures:  {', '.join(result.figures_used)}")
    if result.banned_hits:
        print(f"  WARNING banned-phrase hits remain: {result.banned_hits}")


if __name__ == "__main__":  # pragma: no cover
    main()
