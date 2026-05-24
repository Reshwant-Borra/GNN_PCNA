# Workflow Index

Workflows are repeatable multi-agent procedures.

| Workflow | File | Purpose |
|---|---|---|
| Full Research Cycle | `FULL_RESEARCH_CYCLE.md` | Default end-to-end loop |
| Training and Evaluation | `TRAINING_EVALUATION_WORKFLOW.md` | Leakage-safe training and metrics |
| MD Validation | `MD_VALIDATION_WORKFLOW.md` | Plan, audit, and interpret MD |
| Claim and Paper | `CLAIM_AND_PAPER_WORKFLOW.md` | Keep writing proportional to evidence |
| Submission Readiness | `SUBMISSION_READINESS_WORKFLOW.md` | Final gate and reviewer audit |

Each workflow should produce:

- Markdown report.
- JSON report.
- Agent outputs.
- Gate status summary.
- Registry updates.
- Human review list.

Reports should be stored under:

```text
reports/research_os/<workflow>/<timestamp>/
```
