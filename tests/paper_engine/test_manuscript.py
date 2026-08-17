"""Tests for the manuscript engine pieces that do not require the LLM."""
from paper_engine.manuscript import bibliography, narrative
from paper_engine.manuscript.facts import build_fact_sheet
from paper_engine.manuscript.section_writer import DISALLOWED, _sanitize


def test_fact_sheet_is_grounded_in_real_numbers():
    facts = build_fact_sheet()
    block = facts.to_prompt_block()
    assert "0.1876" in block  # real primary value appears
    assert "test set" in block.lower()
    # Guardrails must include the no-test-fabrication rule.
    assert any("test set was NOT evaluated" in g for g in facts.guardrails)


def test_narrative_plan_md_gating():
    without_md = {s.section_id for s in narrative.build_plan(md_available=False)}
    with_md = {s.section_id for s in narrative.build_plan(md_available=True)}
    assert "md" not in without_md
    assert "md" in with_md
    # Results section always carries the baseline comparison figure.
    results = [s for s in narrative.build_plan(False) if s.section_id == "results"][0]
    assert "baseline_comparison" in results.figures


def test_bibliography_loads_real_relevant_references():
    refs = bibliography.load_references(limit=15)
    assert refs, "expected curated references from seed_relevant_papers.json"
    assert all(r.title for r in refs)
    # Relevance ranking should surface domain terms among the top references.
    joined = " ".join(r.title.lower() for r in refs)
    assert any(t in joined for t in ("pcna", "pocket", "protein", "molecular", "structure"))


def test_citation_finalization_renumbers_used_only():
    refs = bibliography.load_references(limit=10)
    # Cite refs 3 and 1 (out of order); 2 is unused.
    text = f"Foo [3] bar [1] baz [3]."
    remap, used = bibliography.finalize_citations(text, refs)
    assert remap == {3: 1, 1: 2}
    assert [r.idx for r in used] == [1, 2]
    rewritten = bibliography.apply_remap(text, remap)
    assert "[1]" in rewritten and "[2]" in rewritten and "[3]" not in rewritten


def test_sanitizer_removes_banned_phrases():
    bad = "We validated cryptic pocket and experimentally validated the result."
    cleaned = _sanitize(bad)
    # No banned phrase should survive the safe-substitution pass.
    from paper_engine.manuscript.section_writer import any_phrase_in_text
    assert not any_phrase_in_text(DISALLOWED, cleaned)
