---
type: human-review-packet
status: awaiting_review
created: 2026-05-27
blockers_addressed: [1, 2, 5]
reviewer: Rishi (project supervisor)
---

# Human Review Packet — GNN-PCNA Phase 2

**Reviewer:** Rishi
**Prepared by:** Reshwant (Phase 2 lead)
**Date prepared:** 2026-05-27
**Purpose:** Three governance decisions are blocking all downstream Phase 2 and Phase 3
work. This packet consolidates them into one document so you can review and sign off
without reading multiple separate reports.

**How to use this document:** Read each section, check one box (YES / NO / DEFER), sign
with your initials and date, and return. All three decisions are independent — you can
approve some and defer others. Each section states clearly what happens under each choice.

---

## Decision 1 of 3 — CryptoBench Dataset Adoption

**What you are deciding:** Whether to adopt CryptoBench as the Phase 2 benchmark
dataset under a restricted, cryptic-only configuration with specific records excluded.

### What CryptoBench Is

CryptoBench is a published benchmark dataset for cryptic pocket prediction. It contains
1,107 apo (unbound) structures and 5,493 cryptic-pocket (holo) records. All 5,005 CIF
structure files have been downloaded and verified as locally present and readable. The
dataset was fully audited by automated scripts; the audit results are in
`reports/phase2/cryptobench_schema_deep_audit.md`.

### What "Cryptic-Only Adoption" Means

CryptoBench also includes a set of "noncryptic" (non-cryptic pocket) auxiliary records.
Those auxiliary records have missing structure files and unresolved label semantics.
The proposed adoption uses **only the cryptic-pocket records** from `dataset.json`
(the 1,107 apo / 5,493 cryptic entries with complete CIF coverage) and excludes the
noncryptic auxiliary records entirely for now.

### What Gets Excluded Before Any Training

These records must be removed or held out regardless of your YES decision:

| Record | Reason | Action |
|---|---|---|
| Apo `5e0v`, Holo `3vkx` | Exact PCNA contamination (P12004, UniProt confirmed) | Exclude from model development; hold as PCNA positive-control only |
| CIF hits `2xur`, `3bep` | Identified as sliding-clamp structures via CIF text screen | Hold pending sequence clustering review |
| 6 repeated holo PDB IDs across folds (`2fzc`, `2fzg`, `4f04`, `5qya`, `6a5y`, `7fo6`) | Same holo structure appears in multiple official folds, risking leakage | Must be grouped into a single split group before split assignment |
| 721 records with residue mapping failures | Pocket labels cannot be mapped to residue coordinates (see Decision 3) | Mask or exclude per residue mapping policy |

### What Happens Under Each Choice

**YES — Adopt CryptoBench (cryptic-only, with listed exclusions):**
- Blocker 1 is cleared
- Sequence clustering can proceed on the remaining candidate structures
- Split manifest draft can be started after clustering completes
- No training begins until blockers 2–6 also clear

**NO — Reject CryptoBench:**
- Phase 2 has no benchmark dataset candidate
- All downstream work (splits, labels, training) is blocked indefinitely until an
  alternative dataset is identified, acquired, and audited (months of work)
- Recommended only if you identify a fundamental scientific problem with using
  CryptoBench as a cryptic-pocket benchmark

**DEFER — Decide later:**
- All Phase 2 and Phase 3 work depending on CryptoBench remains blocked
- Acceptable if you need more information; please specify what information you need

### Supporting Reports

- Full decision matrix: `reports/phase2/cryptobench_adoption_decision.md`
- Leakage and fold analysis: `reports/phase2/cryptobench_leakage_remediation.md`
- Split risk audit: `reports/phase2/cryptobench_split_risk_audit.md`
- Benchmark limitations: `reports/phase2/benchmark_role_classification.md`

### Decision 1 Sign-Off

```
[ ] YES — Adopt CryptoBench (cryptic-only, with exclusions listed above)
[ ] NO  — Reject CryptoBench
[ ] DEFER — Need more information (specify below)

Notes / conditions:
_______________________________________________________________
_______________________________________________________________

Reviewer initials: _______   Date: _______________
```

---

## Decision 2 of 3 — PCNA Isolation Policy

**What you are deciding:** Whether PCNA and PCNA-like sliding-clamp structures must be
fully isolated from all model development — meaning they cannot appear in training,
validation, threshold selection, feature scaling, architecture search, or split tuning.

### What Was Found

An automated screen of all CryptoBench CIF files identified the following:

| Structure | Finding | Source |
|---|---|---|
| Apo `5e0v`, Holo `3vkx` | Exact PCNA — UniProt P12004, text confirms "pcna", "proliferating cell nuclear antigen", "sliding clamp" | CIF text + UniProt screen |
| `2xur` | CIF text confirms "sliding clamp" | CIF text screen |
| `3bep` | CIF text confirms "sliding clamp" | CIF text screen |

**Important limit:** This was an exact text and UniProt search only — not a sequence
homology search. Additional PCNA-like structures may exist in CryptoBench that were not
caught by the text screen. A full sequence clustering run is still required to catch
distant homologs. This policy applies to confirmed records now and extends to any
additional hits found by clustering later.

### Why This Matters

The scientific goal of this project is to train a GNN that can later be applied to PCNA
to predict its cryptic pockets. If PCNA structures appear in training or validation,
the model may learn PCNA-specific features that inflate performance metrics without
generalizing. Any PCNA-specific claims would then be circular.

### What "Full Isolation" Means in Practice

- `5e0v` and `3vkx`: Excluded from training, validation, and all model selection.
  They may be used later as a PCNA positive-control inference target only, after the
  model is fully frozen.
- `2xur`, `3bep`: Held out pending sequence clustering. If clustering confirms they
  are sliding-clamp homologs, same treatment as above.
- Any additional PCNA-like hits from sequence clustering: Same hold-out policy.
- The split manifest must record PCNA holdout status explicitly for each affected record.

### What Happens Under Each Choice

**YES — Approve full PCNA isolation:**
- Blocker 2 is cleared
- `5e0v` / `3vkx` are flagged as excluded in all downstream pipeline code
- Split manifest can record their holdout status
- Sequence clustering can proceed knowing the isolation rule is approved

**NO — Do not isolate PCNA from model development:**
- Not recommended. Any performance claim on PCNA would be scientifically invalid.
- If rejected, state the alternative policy explicitly.

**DEFER — Need more information:**
- Acceptable if you want to see clustering results before deciding on `2xur`/`3bep`.
- Note: Exact PCNA (`5e0v`/`3vkx`) isolation should be approved regardless of clustering.

### Supporting Reports

- Full isolation policy: `reports/phase2/pcna_isolation_policy.md`
- Contamination screen results: `reports/phase2/pcna_contamination_screen.md`
- Governance rule: `docs/scientific_governance/12_PCNA_SPECIFIC_CHECKS.md`

### Decision 2 Sign-Off

```
[ ] YES — Approve full PCNA isolation (5e0v, 3vkx excluded; 2xur, 3bep held pending clustering)
[ ] NO  — Do not isolate (specify alternative policy below)
[ ] DEFER — Need more information (specify below)

Notes / conditions:
_______________________________________________________________
_______________________________________________________________

Reviewer initials: _______   Date: _______________
```

---

## Decision 3 of 3 — Label Supervision Policy

**What you are deciding:** Whether to approve the proposed label supervision contract
for Phase 2 — specifically what counts as a positive label, what counts as unlabeled
(not a true negative), and what gets masked.

### Current Label Source

Labels come from CryptoBench's `dataset.json` field `apo_pocket_selection`, which maps
pocket-forming residues in the apo structure to residue IDs. These are
**proxy benchmark cryptic-pocket annotations** — they are not independently verified
experimental labels. They represent the benchmark's definition of which residues form
a cryptic pocket in the apo structure.

### The Core Problem: True Negatives Do Not Exist

CryptoBench only marks known positive cryptic-pocket residues. All other residues are
**unlisted** — they are not confirmed negatives. If the model is trained with a
standard binary cross-entropy loss where unlisted = negative, it will be trained on
a false signal (treating "not yet annotated" as "confirmed not a pocket").

### Proposed Supervision Contract

| Residue class | Proposed label |
|---|---|
| In `apo_pocket_selection`, mapping succeeds | **Positive** (label = 1) |
| Not in `apo_pocket_selection` | **Unlabeled** — treated as background, not true negative |
| Mapping fails (residue absent from atom_site) | **Masked** — excluded from loss |
| Mapping fails (numbering scheme mismatch, remappable) | **Remap then label normally** |
| PCNA / isolated records | **Holdout** — not used in training or validation |
| Noncryptic auxiliary records | **Excluded** from this adoption path |

This is a **positive-unlabeled (PU) learning** setup. The training objective must be
chosen to handle this — not standard BCE with implicit false negatives. The exact
objective (PU loss, masked BCE, ranking/Top-K loss, or other) is a separate downstream
decision for Phase 3 implementation and is not locked here.

### What Is Not Approved by This Decision

- The specific training loss function (that is a Phase 3 model decision)
- Any claim that unlabeled residues are confirmed true negatives
- Dense binary classification framing (positive/negative for all residues) without
  a documented background-negative justification
- Ligand contact labels (not proposed here; separate audit required)

### What Happens Under Each Choice

**YES — Approve the proposed supervision contract:**
- Blocker 5 is cleared
- Label generation script can be written to implement this contract
- Residue mapping failures can be processed under the policy in Decision 4 (blocker 4,
  handled separately)
- Phase 3 training harness can be built around a PU-learning or masked-loss objective

**NO — Reject this supervision contract:**
- Specify what alternative label source or contract you want
- All label generation, graph building, and training remain blocked

**DEFER — Need more information:**
- Specify what you need (e.g., want to see the exact ligand contact semantics first,
  or want to review the PU-learning literature before approving)

### Supporting Reports

- Full label policy draft: `reports/phase2/proposed_label_policy.md`
- Label semantics audit: `reports/phase2/cryptobench_label_semantics.md`
- Label supervision risks: `reports/phase2/label_supervision_risks.md`
- Governance rule: `docs/scientific_governance/06_LABELING_RULES.md`

### Decision 3 Sign-Off

```
[ ] YES — Approve the proposed supervision contract (positive-unlabeled framing)
[ ] NO  — Reject (specify alternative below)
[ ] DEFER — Need more information (specify below)

Notes / conditions:
_______________________________________________________________
_______________________________________________________________

Reviewer initials: _______   Date: _______________
```

---

## Summary Checklist

| # | Decision | Status |
|---|---|---|
| 1 | CryptoBench adoption (cryptic-only with exclusions) | ☐ Pending |
| 2 | PCNA isolation policy | ☐ Pending |
| 3 | Label supervision contract (positive-unlabeled) | ☐ Pending |

**After all three are decided:** Return this document to Reshwant.
Reshwant will update `.memory/PROJECT_STATE.md` and `wiki/log.md` to record the
decisions and unblock the appropriate downstream work.

**If you have questions** about any technical finding cited here, the full audit
scripts are at `scripts/cryptobench_deep_audit.py` and
`scripts/phase2_remediation_packet.py` and can be rerun to verify any number.

---

## Provenance

- Prepared from: `reports/phase2/cryptobench_adoption_decision.md`,
  `reports/phase2/pcna_isolation_policy.md`, `reports/phase2/proposed_label_policy.md`,
  `reports/phase2/pcna_contamination_screen.md`,
  `reports/phase2/cryptobench_leakage_remediation.md`
- Governance paths: `docs/scientific_governance/04_DATASET_CONSTRAINTS.md`,
  `05_SPLIT_PROTOCOL.md`, `06_LABELING_RULES.md`, `12_PCNA_SPECIFIC_CHECKS.md`,
  `14_CLAIM_POLICY.md`, `26_HUMAN_REVIEW_GATES.md`
- All factual claims in this document are derived directly from automated audit
  scripts run on local files. No claims are inferred or hallucinated.
- Evidence status: verified for structure counts, hit IDs, and failure counts;
  inferred for remediation pathway recommendations.
