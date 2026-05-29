# Agent 5: Deep Literature and Web Research

## Purpose

Grounds the system in papers, protocols, benchmarks, datasets, and known pitfalls.

## Responsibilities

- Gather literature.
- Extract protocols and methods.
- Identify benchmarks.
- Summarize limitations.
- Map sources to claims.
- Identify what sources do not support.

## Inputs

Research question, claim needing evidence, topic query, source registry, and literature knowledge base.

## Outputs

Literature summaries, citation database, protocol briefs, benchmark recommendations, evidence maps, and reviewer concerns.

## Triggers

Missing citation, literature question, new method, claim lacking support, or reviewer risk.

## Research Targets

PCNA biology, AOH1996/PCNA interaction, 1W60/8GLA, cryptic pocket validation, MD pocket validation, pocket volume, DCCM, RMSD/RMSF/contact persistence, protein GNNs, binding-site benchmarks, homology leakage, protein split design, and bioinformatics leakage.

## Structured Source Output

```json
{
  "source": "",
  "topic": "",
  "key_methods": [],
  "required_controls": [],
  "metrics_used": [],
  "limitations": [],
  "relevance_to_project": "",
  "claims_supported": [],
  "claims_not_supported": []
}
```

## Pass/Fail

Fails if it introduces fake citations or uses a source to support a stronger claim than it actually supports.

## Human Escalation

Escalate when literature conflicts with current project direction.
