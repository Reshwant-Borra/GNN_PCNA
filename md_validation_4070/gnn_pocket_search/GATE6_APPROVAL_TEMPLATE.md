# GATE-6 approval — TEMPLATE (this file is NOT itself an approval)

This is a ready-to-sign draft of the GATE-6 (PCNA inference) approval the pipeline requires. I can
draft it, but I can't *be* the approver — recording it is a human accountability act. To activate it,
the accountable person (team lead / co-author) does three things:

1. Replace every `<...>` placeholder with real values (especially `approved_by` — that's the signature).
2. Paste the finished block into `.memory/PROJECT_STATE.md` and **commit it under your own identity**.
3. Point the run at that file (`--approval-file .../.memory/PROJECT_STATE.md`).

The gate tool **rejects this file as-is** (it detects the unfilled placeholders), so it can't be used
accidentally. It only accepts a version a real person has filled in and recorded.

```
### GATE 6 — PCNA inference approval
approved_by:   <your full legal name — the person accountable for this decision>
role:          <team lead / co-author>
date:          <YYYY-MM-DD>
scope:         run PocketGNNXL inference on the PCNA structures to identify an EXPERIMENTAL
               candidate pocket. This does NOT approve a publishable / competition-headline result.
preconditions: on graph-leakage-fix; checkpoint RETRAINED after the virtual-node fix; residue
               mapping spot-checked. (Rishi's review: OK for a test/experimental candidate; not a
               headline result until these are done.)
checkpoint:    <path>  (sha256: <fill after retrain>)
test_set_note: the reported score is a development estimate, NOT a pristine untouched final test.
human_review:  novelty requires the doc-12 PCNA audit before any site is called "novel".
note:          authorizes the RUN + handoff only; pre-approves NO pocket and NO dynamics claim.
```

Why the signature has to be yours, not mine: a GATE-6 entry is an attestation that a named human
takes responsibility for running the inference and standing behind it under review. If I wrote your
name based on a chat message, that would be me fabricating your attestation — exactly the thing the
gate exists to prevent, and the first thing a competition judge or admissions reviewer checks. Filling
this in yourself takes ~30 seconds and makes the result actually defensible.
