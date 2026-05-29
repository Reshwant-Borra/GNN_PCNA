# System Architecture

## Architecture Goal

GNN ResearchOS coordinates specialized agents that plan work, audit evidence, run code, verify metrics, evaluate biology, track artifacts, control claims, and simulate reviewers.

The key design rule is:

> No agent may approve the validity of its own work.

## High-Level Flow

```text
User / Claude Code conversation
  -> Master Research Orchestrator
  -> Context and Source-of-Truth
  -> selected specialist agents
  -> gates and cross-agent review
  -> provenance and registry updates
  -> reports and memory updates
  -> human approval if required
```

## Execution Modes

- `advisory`: planning, interpretation, review.
- `audit`: leakage, preprocessing, metric, provenance, or claim checks.
- `build`: code creation or refactor.
- `experiment`: training, evaluation, structural analysis, MD analysis.
- `paper`: manuscript, documentation, figure, and claim work.

## Cross-Agent Approval Matrix

| Work product | Producer | Required reviewers |
|---|---|---|
| Code patch | Code Builder | Scientific Code Review, Testing, Provenance |
| Training result | Model Training | Leakage, Metrics, Provenance |
| Headline metric | Metrics | Leakage, Provenance, Contradiction |
| Dataset split | Leakage | Dataset Integrity, human for final protocol |
| Processed graphs | Preprocessing | Dataset Integrity, Leakage, Provenance |
| MD interpretation | Validation | Biological Realism, Metrics, Claim |
| Paper claim | Paper Claim | Metrics, Validation, Biological Realism, Reviewer |
| Figure | Visual Evidence | Metrics, Claim, Provenance |
| Submission | Reviewer | All required gate owners, human |

## Runtime Memory

The implementation should use:

- Human-readable markdown memory for Claude Code and GitHub review.
- JSON registries for automation.
- Searchable memory for literature and long project history once the MVP works.

## Blocking Rules

The Orchestrator must block when:

- Required gate failed, is blocked, or is stale.
- Metric provenance is missing.
- Leakage risk is unresolved.
- Preprocessing is unverified.
- MD validation does not support the exact claim.
- Paper wording is stronger than the claim registry allows.
- Critical tests are skipped.
- Agents disagree on a major scientific decision.
- Human approval is required but missing.

## Target Python Package

```text
research_os/
  orchestrator.py
  agents/
  memory/
  registries/
  routing/
  workflows/
  schemas/
  reports/
  tools/
```

Runtime files can live in:

```text
research_os_memory/
research_os_registries/
reports/research_os/
```

## Conservative Defaults

- Use "candidate region" rather than "validated pocket" unless validation supports the exact claim.
- Use "suggestive" rather than "proven" for limited computational evidence.
- Mark unclear evidence as inconclusive.
- Mark stale outputs instead of trusting file existence.
