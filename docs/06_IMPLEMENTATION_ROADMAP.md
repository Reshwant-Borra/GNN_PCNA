# Implementation Roadmap

## Build Order

1. Documentation and contracts.
2. Package skeleton.
3. File-based memory.
4. JSON registries.
5. Provenance core.
6. Orchestrator router.
7. MVP audit agents.
8. Full audit workflow.
9. Training/evaluation workflow.
10. MD validation workflow.
11. Claim/paper/figure workflows.
12. Submission readiness workflow.
13. Searchable memory.
14. Full 20-agent integration.

## Milestone 1: Package Skeleton

Create:

```text
research_os/
  __init__.py
  __main__.py
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

Done when the package imports and CLI help works.

## Milestone 2: Memory and Registries

Create markdown memory and JSON registries:

- Artifact registry.
- Claim registry.
- Experiment registry.
- Issue registry.
- Source registry.
- Environment registry.
- Decision registry.

Done when the Context Agent can summarize current status and registry validation works.

## Milestone 3: Provenance Core

Implement:

- Git commit capture.
- Dirty state capture.
- File hashing.
- Dataset/checkpoint/environment hashing.
- Command and machine metadata.

Done when any workflow can register outputs with provenance.

## Milestone 4: Router MVP

Implement deterministic routing:

- Intent classifier.
- Risk classifier.
- Agent selector.
- Gate resolver.
- Human approval classifier.
- Context packet builder.

Done when router tests cover at least 10 common prompts.

## Milestone 5: MVP Audit Agents

Implement:

- Context.
- Provenance.
- Contradiction.
- Claim.
- Leakage.
- Metrics.
- Preprocessing.
- Scientific Code Review.

Done when full audit workflow produces markdown and JSON reports.

## Milestone 6: Research Workflows

Implement:

- Full audit.
- Training/evaluation.
- Metric verification.
- MD validation review.
- Claim audit.
- Figure audit.
- Submission readiness.

## Anti-Goal

Do not build a flashy UI or autonomous compute first. Build memory, provenance, routing, and gates first.
