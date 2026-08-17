"""paper_engine — research paper generation subsystem for GNN ResearchOS.

This package does the heavy lifting (literature corpus, figure rendering,
manuscript drafting) behind a set of thin ResearchOS agents. It is designed to
run entirely on a local CPU via Ollama and to obey the project's integrity
guarantees:

  * Real data only. Every figure and number is pulled live from repo artifacts.
    The test set is frozen and not yet evaluated (GATE 5 pending), so nothing in
    this package may fabricate test results.
  * Integrity, not detector-evasion. The writer is conditioned on the author's
    own prior writing and the existing anti-overclaim governance stays on.
  * Human signoff stays. A final manuscript / submission can never be
    auto-approved; that gate is enforced by ResearchOS.

See ``paper_engine.config`` for paths and model configuration.
"""

__all__ = ["config"]

__version__ = "0.1.0"
