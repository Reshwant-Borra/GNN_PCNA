# GNN ResearchOS Documentation Index

This folder is the implementation blueprint for GNN ResearchOS, a research-grade autonomous agentic system for the GNN-PCNA and molecular dynamics validation project.

The system should behave like a conservative autonomous research lab with internal reviewers. Its default posture is that every impressive result is suspicious until leakage, metrics, preprocessing, biology, validation, provenance, and claims are independently checked.

## Read Order

1. `00_EXECUTIVE_BUILD_PLAN.md`
2. `01_SYSTEM_ARCHITECTURE.md`
3. `02_ORCHESTRATOR_ROUTING_SPEC.md`
4. `03_AGENT_INTERACTION_MODEL.md`
5. `memory/MEMORY_SYSTEM.md`
6. `04_GATE_SYSTEM.md`
7. `agents/00_AGENT_INDEX.md`
8. `06_IMPLEMENTATION_ROADMAP.md`
9. `07_CLAUDE_CODE_HANDOFF.md`
10. `08_PROJECT_SPECIFIC_GNN_MD_RULES.md`

## Folder Map

```text
docs/research_os/
  README.md
  00_EXECUTIVE_BUILD_PLAN.md
  01_SYSTEM_ARCHITECTURE.md
  02_ORCHESTRATOR_ROUTING_SPEC.md
  03_AGENT_INTERACTION_MODEL.md
  04_GATE_SYSTEM.md
  05_HUMAN_INTERVENTION_MODEL.md
  06_IMPLEMENTATION_ROADMAP.md
  07_CLAUDE_CODE_HANDOFF.md
  08_PROJECT_SPECIFIC_GNN_MD_RULES.md
  09_SUBMISSION_READINESS_STANDARD.md
  agents/
  memory/
  schemas/
  workflows/
  prompts/
  implementation/
```

## Non-Negotiable Rules

- The Code Builder cannot approve its own code.
- The Model Training agent cannot approve its own metrics.
- The Paper agent cannot approve its own claims.
- The Validation agent cannot ignore contradictions.
- A headline metric is invalid until Leakage and Metrics agents approve it.
- A biological claim is invalid until Biological Realism and Claim agents approve it.
- A report, checkpoint, plot, or table is unsafe until Provenance records its inputs, command, commit, environment, and status.

## Final Target

GNN ResearchOS should autonomously answer:

> Is this research project scientifically valid, biologically realistic, statistically sound, reproducible, and honestly communicated?

Not merely:

> Does the code run?
