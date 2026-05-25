"""Per-run transcript writer.

Each ResearchOS run writes a full JSONL transcript alongside the existing
``plan.json`` / ``result.json`` / ``report.md`` outputs:

    reports/research_os/runs/<workflow>/<timestamp>/
        transcript.jsonl    # event-by-event log (this layer)
        summary.md          # short executive summary (this layer)
        result.json         # full WorkflowResult (existing reports.writer)

The transcript is the source of truth for "what did each agent do?"; the
dashboard's Logs / Transcript tab reads from these files.
"""

from research_os.transcripts.writer import (
    TranscriptWriter,
    init_transcript_for_run,
    finalize_transcript,
)

__all__ = [
    "TranscriptWriter",
    "init_transcript_for_run",
    "finalize_transcript",
]
