# Submission Readiness Workflow

## Purpose

Perform final readiness audit before paper, preprint, poster, repository release, or collaborator handoff.

## Agents

Minimum:

- Context.
- Provenance.
- Leakage.
- Preprocessing.
- Metrics.
- Biological Realism.
- Validation.
- Claim.
- Visual Evidence.
- Reviewer.
- Testing.
- Contradiction.

## Readiness Matrix

```text
Code reproducible: yes/no
Fresh environment validated: yes/no
Critical tests skipped: yes/no
Dataset documented: yes/no
Leakage checked: yes/no
Preprocessing verified: yes/no
Metrics independently verified: yes/no
Statistical uncertainty reported: yes/no
Biological realism checked: yes/no
MD validation classified: yes/no
Claims audited: yes/no
Figures audited: yes/no
Artifact provenance complete: yes/no
Paper consistent with claim registry: yes/no
Human approvals recorded: yes/no
```

## Verdict Values

- `ready`
- `ready_with_limitations`
- `not_ready`
- `blocked_pending_human`

## Automatic Not Ready

Return not ready if critical tests skipped, metrics unverified, leakage unresolved, validation contradicts paper wording, figures are stale, claim registry disallows wording, or provenance is missing for headline artifacts.
