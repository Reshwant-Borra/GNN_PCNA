# Submission Readiness Standard

## Required Readiness Output

```text
Submission Readiness:
- Code reproducible: yes/no
- Fresh environment validated: yes/no
- Critical tests skipped: yes/no
- Dataset documented: yes/no
- Split leakage checked: yes/no
- Preprocessing verified: yes/no
- Metrics independently verified: yes/no
- Statistical uncertainty reported: yes/no
- Biological realism checked: yes/no
- MD validation classified: yes/no
- Claims audited: yes/no
- Figures audited: yes/no
- Artifact provenance complete: yes/no
- Paper consistent with claim registry: yes/no
- Human approvals recorded: yes/no
- Remaining reviewer risks: list
```

## Automatic Not-Ready Conditions

The project is not ready if:

- Headline metrics have unresolved leakage.
- Metrics are unverified.
- Test-set independence is unclear.
- MD evidence is inconclusive but paper says validated.
- Novel residues are called validated without evidence.
- Stale checkpoints or reports are referenced.
- Critical tests skipped.
- Environment cannot be reproduced.
- Figure captions overstate evidence.
- Required human approvals are missing.

## Reviewer Attack Checklist

Before submission, answer:

1. What is the research question?
2. What would falsify the claim?
3. How were labels defined?
4. How was leakage prevented?
5. How many independent test structures exist?
6. Why are the metrics appropriate?
7. Where is AUPRC?
8. Were baselines compared?
9. Does MD support the exact claim?
10. Are novel residues experimentally supported?
11. Are stale checkpoints excluded?
12. Can the repo run from scratch?
13. Are limitations stated?

## Final Human Signoff

Before submission:

```text
Approve final submission with current claim wording and limitations?
```

Default if no approval: do not submit.
