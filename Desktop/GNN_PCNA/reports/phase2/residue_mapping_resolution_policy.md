---
type: policy-draft
status: partially_approved
created: 2026-05-27
approved: 2026-05-27
blocker_addressed: 4
decision_4a: APPROVED — remap via label_seq_id fallback
decision_4b: APPROVED — mask absent residues as unlabeled
decision_4c: DEFERRED — threshold pending per-structure impact analysis (see reports/phase2/residue_mapping_4c_impact_analysis.md)
decision_4d: APPROVED — exclude 4 wrong-chain records
source_registry: data/registries/residue_mapping_failures.json
---

# Residue Mapping Resolution Policy — Draft

**Status:** `draft_not_frozen` — requires human approval before implementation.
**Blocker:** #4 in `.memory/PROJECT_STATE.md`
**Prepared from:** `data/registries/residue_mapping_failures.json` (generated
2026-05-27 by `scripts/phase2_remediation_packet.py`).

---

## Summary of Failures

Out of 409,944 pocket selection tokens checked against present CIF atom-site records:

| Failure class | Count | % of failures | Record type breakdown |
|---|---|---|---|
| `matches_label_seq_id_not_auth_seq_id` | 420 | 58.3% | mixed cryptic/noncryptic |
| `residue_token_absent_from_atom_site` | 297 | 41.2% | mixed cryptic/noncryptic |
| `residue_token_exists_on_other_chain` | 4 | 0.6% | mixed |
| **Total** | **721** | **100%** | **cryptic: 183 · noncryptic: 538** |

Overall failure rate: 721 / 409,944 = **0.18%** of checked tokens.

**Important scope note:** Since Phase 2 is pursuing cryptic-only adoption, the
noncryptic failures (538) are lower priority. The 183 cryptic failures are the
critical set. However, this policy covers all 721 because the noncryptic records
may be revisited later and the failure classes are the same.

---

## Class 1 — `matches_label_seq_id_not_auth_seq_id` (420 failures)

### What This Means

The pocket selection token in `dataset.json` uses a residue number that matches
the PDB **label_seq_id** (internal sequential numbering assigned by PDB, always
1-based and gapless) but does NOT match the **auth_seq_id** (author-assigned
numbering, which may have gaps, insertions, negative numbers, or non-sequential
values). The audit code searched by auth_seq_id and failed to find the residue.

The residue and its 3D coordinates **exist** in the CIF file — they are simply
referenced by the wrong numbering convention.

### Example (from registry)

```
apo_pdb_id: 1d7k  chain: A  residue_token: 69
selection_token: A_69  reason: matches_label_seq_id_not_auth_seq_id
```

Residue 69 exists in 1d7k under its label_seq_id but has a different auth_seq_id.

### Proposed Resolution: REMAP

Attempt a fallback lookup using label_seq_id when auth_seq_id lookup fails.
If label_seq_id lookup succeeds and returns a unique residue with atom-site
coordinates, accept the mapping and label the residue normally.

**Implementation:** In the label generation script, when auth_seq_id lookup fails
for a selection token, perform a secondary lookup by label_seq_id. If successful,
log the remap event (original token, found auth_seq_id, chain, pdb_id) to a
dedicated `data/registries/residue_remap_log.json` file for audit purposes.

**Risk assessment:** Low. This is a metadata convention mismatch, not missing data.
The coordinates exist. The remap is deterministic and reproducible.

**Requires new assumption in `data/registries/assumption_registry.json`:**
"When auth_seq_id lookup fails for a pocket selection token but label_seq_id
lookup succeeds with a unique residue, the label_seq_id match is treated as
authoritative. Rationale: CryptoBench pocket selections were generated against
label_seq_id numbering based on observed mismatches in audit."

**Human approval needed for:** The assumption above and the remap log format.

---

## Class 2 — `residue_token_absent_from_atom_site` (297 failures)

### What This Means

The residue is referenced in the pocket selection but has **no atom-site coordinates
in the CIF file at all** — it is absent from the resolved structure. This occurs when:

- The residue is in a disordered / flexible region that could not be resolved by
  crystallography (missing electron density)
- The residue was truncated from the deposited model
- The residue exists in the SEQRES record (sequence) but not in the ATOM/HETATM
  records (coordinates)

The residue cannot be represented as a graph node because there are no coordinates
to build its feature vector.

### Proposed Resolution: MASK AS UNLABELED

These residues must be excluded from the graph entirely. They cannot be labeled
positive (no structural evidence) and must not be labeled negative (the absence of
coordinates is not evidence of absence of pocket character). They should be recorded
as **masked** in the label vector — excluded from the training loss.

**Implementation:**
- During graph construction, skip any residue that has no atom-site record.
- In the label vector, use a third state (e.g., label = -1 or a separate mask array)
  to flag these residues as excluded from loss computation.
- Log skipped residues to `data/registries/masked_residue_log.json` per structure.
- This is consistent with the proposed label supervision contract in
  `reports/phase2/proposed_label_policy.md` (ambiguous residues → masked).

**Risk assessment:** Medium for cryptic failures (183 tokens across cryptic records).
Each masked positive is a lost label signal. The impact depends on how many unique
apo structures are affected and how many residues per structure are lost.

**Further analysis needed before implementation:**
How many unique apo PDB IDs have at least one Class 2 cryptic failure? If a small
number of structures account for most failures, those structures may warrant
exclusion rather than masking. This analysis requires grouping
`data/registries/residue_mapping_failures.json` by `apo_pdb_id` for cryptic records
with `reason = residue_token_absent_from_atom_site`.

**Human approval needed for:** The mask-as-unlabeled treatment and the decision of
whether structures with a high proportion of masked positives should be excluded
entirely (threshold TBD, e.g. >50% of pocket residues masked → exclude structure).

---

## Class 3 — `residue_token_exists_on_other_chain` (4 failures)

### What This Means

4 residue tokens were found in the CIF but on a **different chain** than the chain
specified in the selection token. For example, the selection says chain A, residue 42,
but that residue appears on chain B in the CIF.

This is likely caused by chain reassignment between the author's PDB submission and
the CryptoBench pocket selection script.

### Proposed Resolution: EXCLUDE THE 4 RECORDS

With only 4 affected tokens across the entire dataset, the cost of building and
validating cross-chain remapping logic is not justified. Exclude the 4 apo/holo
records that contain these failures from the candidate set. Log their PDB IDs to
`data/registries/excluded_records.json` with reason `chain_mismatch`.

**Risk assessment:** Negligible. 4 records out of 1,107 apo structures (<0.4%).

**Human approval needed for:** Confirmation that exclusion is preferred over
attempting cross-chain lookup.

---

## Implementation Order (if all classes are approved)

1. Fix Class 1 first — remap logic is a pure gain (recovers 420 tokens that exist)
2. Fix Class 3 — exclude 4 records, log them, move on
3. Fix Class 2 — implement masking logic; run the per-structure impact analysis
   (how many apo structures are affected and how severely) before setting an
   exclusion threshold for high-mask structures

All fixes should be implemented in a dedicated label generation script, not ad-hoc
in the training loop. The script must output a deterministic, hash-verified label
file per `docs/scientific_governance/06_LABELING_RULES.md`.

---

## Decisions Required from Human Reviewer

| # | Decision | Options |
|---|---|---|
| 4a | Class 1 remap policy | Approve remap via label_seq_id fallback / Reject / Defer |
| 4b | Class 2 mask policy | Approve mask-as-unlabeled / Require exclude-only / Defer |
| 4c | Class 2 exclusion threshold | Set a % threshold above which a structure is excluded entirely (e.g. >50% masked pocket residues) / Leave to further analysis / Defer |
| 4d | Class 3 exclusion policy | Approve exclude-4-records / Attempt cross-chain remap / Defer |

```
Decision 4a (Class 1 remap):
[ ] Approve  [ ] Reject  [ ] Defer
Notes: _______________________________________________________________

Decision 4b (Class 2 mask):
[ ] Approve mask-as-unlabeled  [ ] Require hard exclude  [ ] Defer
Notes: _______________________________________________________________

Decision 4c (Class 2 exclusion threshold):
[ ] Set threshold at _____%  [ ] Leave to further analysis  [ ] Defer
Notes: _______________________________________________________________

Decision 4d (Class 3 exclude 4 records):
[ ] Approve exclusion  [ ] Attempt cross-chain remap  [ ] Defer
Notes: _______________________________________________________________

Reviewer initials: _______   Date: _______________
```

---

## Provenance

- Source: `data/registries/residue_mapping_failures.json` (generated
  2026-05-27T19:09:22 by `scripts/phase2_remediation_packet.py`)
- Governance paths: `docs/scientific_governance/06_LABELING_RULES.md`,
  `docs/scientific_governance/05_SPLIT_PROTOCOL.md`,
  `docs/scientific_governance/07_PREPROCESSING_AND_GRAPH_RULES.md`,
  `docs/scientific_governance/15_PROVENANCE_AND_REPRODUCIBILITY.md`
- All counts are taken directly from the machine-generated registry.
  No counts are inferred or estimated.
- Evidence status: verified for failure counts and reasons; inferred for
  proposed remediation approaches; uncertain for impact of Class 2 masking
  until per-structure analysis is run.
