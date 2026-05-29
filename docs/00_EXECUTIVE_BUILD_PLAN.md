# Executive Build Plan

## Objective

Build GNN ResearchOS: an autonomous research operating system for the GNN-PCNA and molecular dynamics validation project.

The target operating model is about 95 percent AI involvement and 5 percent human intervention. The human acts as principal investigator, approving scientific direction, major claims, expensive compute, and final submission.

## Problems This System Must Prevent

- Chain or homology leakage.
- Inflated AUROC from non-independent residue-level samples.
- Very small independent test sets being overinterpreted.
- Incorrect post-validation metrics.
- MD evidence being described as stronger than it is.
- Old checkpoints or stale reports contaminating current conclusions.
- Broken environments where critical tests are skipped.
- Source-of-truth drift across repos, chats, VMs, reports, and paper drafts.
- Biological claims made before structural realism is checked.
- Expensive compute without success/failure criteria.
- Hallucinated terminology, mechanisms, or citations.

## Definition of Success

The system is successful when it can:

- Route any user or Claude Code conversation to the correct agent or workflow.
- Maintain current source of truth.
- Track every generated artifact and mark stale outputs.
- Track every scientific claim and restrict wording to the evidence.
- Detect leakage before accepting performance.
- Audit preprocessing and label alignment.
- Recompute metrics independently.
- Check biological and physical plausibility.
- Classify MD validation as support, partial support, inconclusive, weakening, or contradiction.
- Simulate hostile reviewer questions.
- Escalate to the human only for defined PI-level decisions.

## System Layers

1. Conversation and orchestration.
2. Agent execution.
3. Memory and registries.
4. Gates and workflows.
5. Reports and collaboration.

## Core Agents

1. Master Research Orchestrator.
2. Context and Source-of-Truth.
3. Research Design and Falsification.
4. Biological and Scientific Realism.
5. Deep Literature and Web Research.
6. Dataset and Label Integrity.
7. Leakage and Split Design.
8. Preprocessing and Feature Engineering Auditor.
9. Code Builder and Refactor.
10. Scientific Code Review.
11. Testing and Fresh Environment.
12. Model Development and Training.
13. Metrics, Statistics and Uncertainty.
14. Compute Planning and Execution.
15. Validation and Skeptic.
16. Contradiction and Error Hunter.
17. Provenance, Versioning and Artifact.
18. Paper, Claim and Documentation.
19. Visual Evidence and Figure.
20. Reviewer and Collaboration.

## MVP Priority

Build the highest-safety agents first:

- Context and Source-of-Truth.
- Leakage and Split Design.
- Preprocessing Auditor.
- Scientific Code Review.
- Metrics and Statistics.
- Biological Realism.
- Validation and Skeptic.
- Contradiction Hunter.
- Provenance.
- Paper and Claim.

## Build Phases

### Phase 0: Documentation

Create this blueprint: routing, memory, agents, schemas, gates, workflows, and handoff docs.

### Phase 1: Memory and Registries

Implement markdown memory, JSON registries, registry validation, artifact dependency tracking, and stale propagation.

### Phase 2: Orchestrator Router

Implement intent classification, risk classification, agent selection, gate resolution, context packet building, and human approval detection.

### Phase 3: Audit Agents

Implement the MVP audit agents and run a full audit on the current repo.

### Phase 4: Workflow Runners

Implement full audit, training/evaluation, metric verification, validation review, claim audit, figure audit, and submission readiness workflows.

### Phase 5: Full Agent System

Implement all 20 agents and connect them to memory, registries, and reports.

### Phase 6: Searchable Knowledge

Add full-text or embedding search for literature, source summaries, registry entries, and historical decisions.

## First Code Milestone

```bash
python -m research_os.workflows.run_full_audit --repo . --out reports/research_os/full_audit_latest
```

This should summarize current status, detect stale outputs, audit claims, and produce a blocker report.

## Final Code Milestone

```bash
python -m research_os.orchestrator "Can we write the paper results section now?"
```

The expected behavior is to check source-of-truth, metrics, leakage, validation, claims, provenance, and contradictions before writing or blocking.
