"""Manuscript engine: turn real results + figures into a competition-format paper.

Pipeline: facts (grounding) -> narrative (judge-flow plan) -> section_writer
(local-LLM drafting, anti-overclaim) -> assemble_docx -> self_review. Every
number the writer may use comes from :mod:`paper_engine.manuscript.facts`, which
reads real run manifests; the writer is forbidden from inventing values.
"""

__all__ = [
    "facts",
    "narrative",
    "voice",
    "section_writer",
    "bibliography",
    "assemble_docx",
    "build",
]
