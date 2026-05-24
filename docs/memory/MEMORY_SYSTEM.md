# Memory System

## Purpose

Memory is the foundation of GNN ResearchOS. Without it, agents will forget context, reuse stale files, contradict prior decisions, and overstate claims.

## Memory Layers

### Hot Operational Memory

Small state loaded often:

- Current task.
- Current workflow.
- Current branch/commit.
- Files being edited.
- Active hypothesis.
- Recent errors.
- Agents already run.
- Current blockers.
- Pending human approvals.

### Canonical Project Memory

Human-readable source of truth:

- Project overview.
- Research question.
- Hypothesis and null hypothesis.
- Current dataset status.
- Current model status.
- Current validation status.
- Current paper status.
- Accepted, rejected, and pending claims.
- Current limitations.

### Artifact Registry

Machine-readable record for every output:

- Path.
- Type.
- Command.
- Git commit.
- Dataset hash.
- Checkpoint hash.
- Environment hash.
- Timestamp.
- Machine/VM.
- Status.
- Associated claims/figures/tables.

### Experiment Registry

Tracks:

- Experiment ID.
- Purpose.
- Hypothesis.
- Inputs.
- Script/command.
- Parameters.
- Expected and actual outcome.
- Metrics.
- Interpretation.
- Failure modes.
- Claim impact.

### Claim Registry

Controls scientific wording:

- Claim text.
- Evidence for/against.
- Claim strength.
- Allowed wording.
- Disallowed wording.
- Required evidence to strengthen.
- Human approval status.

### Issue and Bug Registry

Tracks:

- Known bugs.
- Potential bugs.
- Fixed bugs.
- Stale outputs caused by bugs.
- Artifacts needing regeneration.
- Paper numbers affected.

### Literature Knowledge Base

Stores:

- Papers.
- Protocols.
- Benchmarks.
- Citation summaries.
- Extracted claims.
- What each source supports and does not support.

### Collaboration Memory

Tracks:

- Local repo state.
- Friend/collaborator repo state.
- Last shared commit.
- Pending sync actions.
- Stale outputs to avoid.

## Source-of-Truth Priority

When sources conflict:

1. Human decision registry.
2. Claim registry.
3. Artifact registry.
4. Experiment registry.
5. Canonical memory.
6. Latest audited reports.
7. Source code and data.
8. Older reports.
9. Chat history.

Older reports and chats are not authoritative when they conflict with registries.

## Required Context Summary

The Context Agent should always be able to output:

```text
Current source of truth:
- Current model checkpoint:
- Current dataset version:
- Current split:
- Current valid metrics:
- Current MD status:
- Current allowed claims:
- Stale artifacts:
- Blocking risks:
- Human approvals pending:
```

## Anti-Hallucination Rule

Before making a technical or biological claim, ask:

```text
Do we have evidence for this statement?
```

If not, mark the statement unsupported and do not place it in the paper.
