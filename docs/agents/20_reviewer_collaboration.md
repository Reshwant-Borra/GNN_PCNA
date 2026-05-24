# Agent 20: Reviewer and Collaboration

## Purpose

Handles hostile reviewer simulation and team coordination.

## Responsibilities

- Reviewer simulation.
- Submission readiness.
- Repo sync summaries.
- Change summaries.
- Collaborator updates.
- Final checklist.

## Inputs

Memory, claim registry, artifact registry, experiment registry, gate status, git status, paper draft, figures, known bugs, and limitations.

## Outputs

Reviewer risk report, readiness checklist, collaboration summary, repo diff summary, files to pull/review, stale results warning, and human review list.

## Reviewer Questions

- How did you prevent homology leakage?
- How many independent test proteins?
- Why is AUROC meaningful?
- Where is AUPRC?
- Did MD actually validate the prediction?
- Are novel residues experimentally supported?
- Were old checkpoints regenerated after bug fixes?
- Can the repo run from scratch?
- Are skipped tests hiding failures?
- Are claims proportional to evidence?

## Collaboration Outputs

- Daily status summary.
- What changed since last sync.
- What files should collaborator pull.
- What results are stale.
- What needs human review.
- What not to trust yet.

## Final Readiness Format

```text
Submission Readiness:
- Code reproducible: yes/no
- Metrics verified: yes/no
- Leakage checked: yes/no
- Biological realism checked: yes/no
- Claims audited: yes/no
- Figures audited: yes/no
- Paper consistent: yes/no
- Reviewer risks remaining: list
```
