# Coding Agent Rules

## Purpose

Define strict behavior for Claude Code, Codex, or any coding agent working on GNN-PCNA Phase 2.

## Required Prompt Instruction

Every coding prompt must include:

> Implement only documented science. If a scientific assumption is missing, stop and document the assumption instead of inventing it.

## Hard Rules

- Coding agents implement governance; they do not define new science.
- Any change to dataset, label, split, model logic, MD interpretation, or claim policy requires explicit documented approval.
- If uncertainty is scientific rather than mechanical, stop and document it.

## Coding Agents May

- implement documented rules
- scaffold infrastructure
- write validation code
- write tests
- refactor
- add provenance
- add reporting
- add checks that fail closed

## Coding Agents May Not

- invent biological assumptions
- invent dataset definitions
- invent claim language
- silently change scientific methodology
- tune on the test set
- weaken verification gates
- bypass constraints
- reuse stale artifacts
- modify scientific model logic without explicit approval
- interpret MD results beyond policy

## Forbidden Actions

- Editing model science to make a metric improve without approval.
- Weakening a validator or test because it blocks progress.
- Reusing an artifact without provenance.

## Pre-Coding Checklist

- [ ] Which governance file controls this task?
- [ ] Which assumption IDs are used?
- [ ] Which artifact will prove compliance?
- [ ] Does the task touch dataset, labels, split, model logic, MD, or claims?
- [ ] If yes, is explicit scientific approval present?

## Required Checks

- Pre-coding checklist completed.
- Post-coding checklist completed.
- Diff reviewed for methodology drift.
- Relevant tests or audits run.

## Post-Coding Checklist

- [ ] Tests or checks added/updated.
- [ ] Provenance captured.
- [ ] No stale cache introduced.
- [ ] No scientific method changed silently.
- [ ] Documentation cross-reference updated.
- [ ] Stop conditions checked.

## Forbidden Phrases And Signals

- "I assumed..."
- "This should be biologically plausible" without evidence.
- "Good enough for now" for split, labels, or provenance.
- "Validated by MD" without policy language.
- "The model discovered..." without claim audit.

## If The Agent Is Uncertain

Stop implementation. Write the missing assumption, risk, or decision into the appropriate governance artifact and ask for review.

## Prevention

Keep prompts scoped to implementation and make scripts fail closed when required governance manifests are missing.

## Examples Of Failure

- Agent changes a label threshold from 6 Angstrom to 8 Angstrom to improve validation.
- Agent uses `h.mean(dim=0)` for virtual node context in mixed PyG batches.
- Agent rewrites a report to call AOH1996 recovery independent validation.

## Compliance Artifact

Code PR/checklist must link to the relevant governance file and `reports/phase2/coding_agent_audit.md`.

## If The Rule Fails

Freeze the change. Revert only with explicit instruction or supersede with a reviewed patch. Invalidate affected results.
