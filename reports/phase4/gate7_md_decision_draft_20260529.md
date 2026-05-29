# GATE 7 MD Validation Decision Package — Phase 5

**Status:** DRAFT — requires separate human decision before any MD simulation runs.
**Date drafted:** 2026-05-29
**Drafted by:** claude-sonnet-4-6 (Phase 4 finalization task)
**Governance:** `docs/scientific_governance/13_MD_VALIDATION_RULES.md`,
`docs/scientific_governance/14_CLAIM_POLICY.md`,
`docs/scientific_governance/12_PCNA_SPECIFIC_CHECKS.md`
**Depends on:** `reports/phase4/gate6_authorization_20260529.md` (GATE 6 cleared),
`reports/phase4/phase4_candidate_prioritization_20260529.md` (reclassified),
`data/registries/pcna_interface_map.json`

---

## Required Statement (doc 13, mandatory reproduction)

We do not build expecting one MD result and then panic when MD gives unexpected results.
MD can support, weaken, redirect, or falsify the working hypothesis. All outcomes are
evidence. Negative MD results are valid and will be reported honestly. We do not treat
the absence of pocket opening as a failed run, nor ligand stability in one trajectory
as binding-site proof.

---

## Decision Required

GATE 7 is the human authorization gate for Phase 5 MD validation. No MD simulation may
begin until this package is reviewed and approved by Reshwant-Borra. Approval of this
document must be recorded in `reports/phase4/gate7_authorization_YYYYMMDD.md` before
any simulation setup, trajectory generation, or analysis begins.

This document covers **MD Wave 1** targets only. Tier 1B (trimer-interface) candidates
are deferred to MD Wave 2 and require a separate human decision.

---

## MD Wave 1 — Recommended Targets

| Candidate Group    | Residues | Tier   | Max Score | Mean Score | Rationale                          |
|--------------------|----------|--------|-----------|------------|------------------------------------|
| Positive control   | 118-122  | 3      | 0.9300    | 0.8199     | AOH1996/IDCL sanity check          |
| Novel candidate A  | 239-243  | 1A     | 0.8472    | 0.7117     | Highest Tier 1A; no interface      |
| Novel candidate B  | 28-32    | 1A     | 0.8157    | 0.7430     | Second Tier 1A; no interface       |
| Novel candidate C  | 206-210  | 1A     | 0.8087    | 0.6137     | Third Tier 1A; no interface        |
| Interface-adjacent | 134-138  | 2      | 0.7699    | 0.5868     | IDCL-adjacent positive control     |

All Wave 1 candidates use the same simulation protocol (apo PCNA trimer, AMBER ff19SB,
TIP3P, ≥3 × 100 ns replicates) — setup policy must be identical per doc 13.

## MD Wave 2 — Deferred Targets (Tier 1B, requires separate decision)

| Candidate         | Residues | Max Score | Mean Score | Why Deferred                              |
|-------------------|----------|-----------|------------|-------------------------------------------|
| Trimer candidate A | 170-174 | 0.9233    | 0.8681     | Trimer interface; needs enhanced sampling |
| Trimer candidate B | 175-179 | 0.8892    | 0.8459     | Trimer interface; needs enhanced sampling |
| Trimer candidate C | 152-156 | 0.8761    | 0.8057     | Trimer interface; needs enhanced sampling |

---

## Tier 1B Justification — Explicit Include/Exclude Decision

### Why Tier 1B Cannot Be Silently Omitted

Regions 170-174 (max 0.9233), 175-179 (max 0.8892), and 152-156 (max 0.8761) are the
highest-scoring non-positive-control regions in the entire Phase 4 inference. Omitting
them without justification would be scientifically dishonest and would misrepresent the
model's output. They are documented here with explicit reasoning for their deferred status.

### Structural Context

Residues 173, 174, 175, 176, 177, 178, 179, 180, 181, 182, 183, 185 and 153, 154 are
canonical trimer-interface positions, derived from inter-subunit heavy-atom contacts
≤4.5 Å across chains A/C/E in PDB 1AXC (Gulbis JM et al., Cell 1996;87:297, PMID 8861913;
reproduced via `scripts/derive_pcna_interface_contacts.py`). These residues are buried at
the head-to-tail subunit-subunit contact in the assembled homotrimer. They are on the
back face of the ring, mechanistically distinct from the front-face PIP/APIM/AOH1996 sites.

### Why Standard Wave 1 MD Cannot Characterize Tier 1B

1. **Buried in assembled state.** Trimer interface residues are not solvent-accessible in
   the closed clamp. A standard apo MD trajectory of the assembled trimer will not expose
   these residues as a cryptic pocket — they will remain buried throughout any 100 ns run
   without extraordinary conformational events.

2. **Ring opening is a large-scale event.** The PCNA ring opens for loading (RFC loads
   the clamp by separating subunits) — a process that requires RFC engagement, ATP hydrolysis,
   and large interdomain motion. Standard, unbiased 100 ns MD cannot sample this event at
   any reasonable timescale.

3. **Monomer simulation is not biologically relevant.** Running PCNA as a monomer would
   artificially expose the trimer interface but does not reflect the biologically relevant
   assembled state. Interpretations from monomer MD cannot be extrapolated to trimer behavior.

4. **Protocol incompatibility.** Wave 1 uses a single protocol (apo trimer, unbiased MD)
   that is appropriate for front-face and surface candidates. Applying this protocol to Tier 1B
   would yield uninformative results (stable buried contacts) and waste simulation time.

### Why Tier 1B Should Not Be Permanently Excluded

1. **Scores are highest of all.** The signal is robust, reproducible across 229 structures,
   and systematic. A GNN trained on general cryptic pocket data producing its strongest
   signal at the trimer interface is scientifically interesting even if the interpretation
   is unclear.

2. **Mechanistically distinct hypothesis.** Disrupting PCNA ring assembly is a separate
   anti-PCNA strategy from PIP-box competition. The trimer interface is a legitimate
   candidate for an allosteric or ring-opening mechanism. This merits proper investigation,
   not dismissal.

3. **Precedent for ring-opening biology.** RFC (Replication Factor C) opens the PCNA ring
   for clamp loading. Agents that stabilize or modulate a partially open state could have
   functional consequences. This is a hypothesis-generating result that warrants enhanced
   sampling.

4. **Precedent for enhanced sampling in cryptic pocket studies.** Governance doc 13
   explicitly notes that "enhanced sampling may be needed for cryptic pockets." Tier 1B
   is precisely this case.

### Decision: Defer to MD Wave 2 (Not Excluded, Not Approved for Wave 1)

Tier 1B candidates are **deferred to MD Wave 2** with the following requirements before
any simulation may begin:

1. A specialized enhanced-sampling pre-registration (metadynamics or umbrella sampling
   on a ring-breathing coordinate), submitted as a separate document.
2. Explicit definition of the collective variable (e.g., distance across the subunit
   interface, radius of gyration of the trimer ring).
3. A human decision on whether to simulate (a) full trimer with enhanced sampling, or
   (b) monomer with caveats on biological relevance documented upfront.
4. A separate GATE 7B authorization record (not covered by this Wave 1 document).

Tier 1B scores and rationale are preserved in this record. The deferred status is not
a scientific dismissal; it reflects that a proper protocol does not yet exist for these
candidates.

---

## MD Target-Selection Rationale

### Positive Control (118-122) — REQUIRED

Region 118-122 spans the IDCL core (residues 117-135 per pcna_interface_map.json) and
the AOH1996 contact region (residues 23, 25-27, 38-47, 121, 123-131, 231-234, 250-253).
This is the highest-scoring region overall (max 0.9300) and the governance-required
positive-control sanity check. MD must include this system to confirm that simulation
setup is capable of detecting known front-face dynamics before novel candidates are
interpreted. Failure of the positive control (e.g., simulation instability, no detectable
IDCL flexibility) invalidates Wave 1 results for all other candidates.

Positive-control MD tests the hypothesis that the AOH1996/IDCL pocket retains some
accessibility in apo PCNA after ZQZ removal. This is distinct from novel-site prediction.
Recovery of this region by MD supports the simulation setup but does NOT validate any
Tier 1A prediction (governance doc 12).

### Tier 1A Top-3 (239-243, 28-32, 206-210) — SELECTED

These three candidates have no overlap with any known interface (pip_box_binding_site,
apim_site, idcl, trimer_interface, aoh1996_contact_region per pcna_interface_map.json)
and score above 0.80 by max score. They represent the strongest computationally predicted
novel PCNA surface regions from this model.

Selection was limited to top-3 for Wave 1 to balance scientific completeness against
the cost of ≥3 replicates × 100 ns per candidate per doc 13. Wave 1 results will inform
whether to expand to additional Tier 1A candidates (157-161, 49-53, etc.) in Wave 1.5
or Wave 2.

### Interface-Adjacent Control (134-138) — SELECTED

Region 134-138 overlaps the IDCL tail (IDCL spans 117-135; residues 134, 135 overlap)
and pip_box_binding_site (residues 134, 135 in the PIP-box list). This region is
distinct from the AOH1996/118-122 core: it is the distal end of the IDCL, adjacent to
but not coincident with the AOH1996 contact zone. Including it tests whether the model's
signal at IDCL-proximal positions reflects genuine IDCL dynamics or merely proximity
to the known pocket. It serves as a useful reference between Tier 3 (positive control)
and Tier 1A (novel surface) interpretations.

### Excluded from Wave 1

- Tier 1B (170-174, 175-179, 152-156): Deferred — see above.
- Tier 1A ranks 4-15 (157-161 through 211-215): Not excluded. Reserved for Wave 1.5 or
  Wave 2 depending on Wave 1 results. Higher-priority Wave 1 candidates must be run first.
- Tier 3 ranks 2-6 (23-27, 123-127, etc.): Additional AOH1996 region recovery candidates;
  not required for Wave 1 since 118-122 already covers the core positive control.

---

## Candidate-to-PDB Mapping Table

| Candidate  | Residues | Recommended Primary PDB | Assembly    | Preparation Notes                                    | Secondary PDB     |
|------------|----------|-------------------------|-------------|------------------------------------------------------|-------------------|
| PC-118     | 118-122  | 8GLA (holo, ZQZ)        | Trimer      | Holo system: retain ZQZ. Apo system: remove ZQZ,     | 1AXC (apo ref)    |
|            |          |                         |             | energy-minimize. Run both for pocket comparison.     |                   |
|            |          |                         |             | Resolution 3.77 Å — flag; force-included positive    |                   |
|            |          |                         |             | control only. Stability audit required (doc 13).     | 8GL9 (alt apo)   |
| T1A-239    | 239-243  | 1AXC (remove p21)       | Trimer      | Remove p21 chains (D and any partner chains);        | apo Part-1 struct |
|            |          |                         |             | energy-minimize; confirm IDCL not distorted by       | (from candidate   |
|            |          |                         |             | peptide removal before equilibration.                | manifest ≤3.5 Å)  |
| T1A-28     | 28-32    | 1AXC (remove p21)       | Trimer      | Same preparation as T1A-239.                         | Same as above     |
| T1A-206    | 206-210  | 1AXC (remove p21)       | Trimer      | Same preparation as T1A-239.                         | Same as above     |
| T1B-170    | 170-174  | 1AXC (biological asm)   | Trimer      | DEFERRED. Requires enhanced-sampling protocol.        | N/A (Wave 2)      |
|            |          |                         |             | Full trimer required; interface must remain intact.  |                   |
| T1B-175    | 175-179  | 1AXC (biological asm)   | Trimer      | DEFERRED. Same as T1B-170.                           | N/A (Wave 2)      |
| T1B-152    | 152-156  | 1AXC (biological asm)   | Trimer      | DEFERRED. Same as T1B-170.                           | N/A (Wave 2)      |
| T2-134     | 134-138  | 1AXC (remove p21)       | Trimer      | Same preparation as T1A-239. IDCL must be fully      | apo Part-1 struct  |
|            |          |                         |             | ordered in chosen starting structure; verify IDCL    | with visible IDCL  |
|            |          |                         |             | completeness before equilibration.                   |                   |

**Notes on 1AXC:**
- PDB 1AXC: Gulbis JM et al., Cell 1996;87:297, PMID 8861913. Human PCNA trimer with
  three bound p21 PIP-box peptides. Resolution ~1.35 Å. Top-ranked structure in
  `data/registries/phase4_candidate_manifest.json` (quality filter passed).
- For apo simulations: remove all non-PCNA chains (p21 peptides), energy-minimize the
  exposed surface, then equilibrate before production.
- Biological assembly = homotrimer (chains A/C/E as PCNA; chains B/D/F as p21 peptides
  — remove B/D/F for apo; actual chain letters must be verified from the deposited CIF).
- Alternative apo structures: the 7 apo/no-ligand Part 1 structures from
  `data/registries/phase4_candidate_manifest.json` that passed the ≤3.5 Å quality filter.

**Notes on 8GLA:**
- Resolution 3.77 Å — below project quality threshold (≤3.5 Å). Force-included as
  positive control only (GATE 6 authorization). Not used for novel-site simulations.
- Any trajectory from 8GLA must include an equilibration and stability audit per doc 13.
  If the trajectory is unstable, it is archived as exploratory only (doc 13).

---

## Per-Candidate Pre-Registrations

All pre-registrations below are pre-registered before any simulation. They are
hypothesis documents, not results and not claims. Setup parameters marked PROPOSED
must be confirmed by Reshwant-Borra before execution. All systems must use identical
force field, water model, protonation policy, and ion concentration per doc 13.

**Shared simulation policy (proposed, applies to all Wave 1 candidates):**
- Force field: AMBER ff19SB (protein)
- Water model: TIP3P, 150 mM NaCl, neutralizing counter-ions
- Protonation: pH 7.4 standard states (uniform across all systems)
- Duration: ≥3 × 100 ns replicates per system (a single 100 ns run is exploratory only)
- Random seeds: record per replicate in `reports/phase4/md/MANIFEST.md`

---

### PC-118: Positive Control — Residues 118-122 (AOH1996 / IDCL Recovery)

**Candidate ID:** PC-118
**Residues:** 118-122 (canonical UniProt P12004 numbering)
**Tier:** 3 (Positive control)
**Max score:** 0.9300 | **Mean score:** 0.8199 | **N structures:** 229
**Interface overlap:** aoh1996_contact_region, idcl, pip_box_binding_site

#### Interface classification
Region 118-122 covers the core of the IDCL (117-135) and the AOH1996 contact zone
(includes residues 121, 123-129, 131 per pcna_interface_map.json). This is the established
front-face hydrophobic pocket that accommodates PIP-box, APIM, and the AOH1996 compound
(ZQZ) in 8GLA. Recovery of this region is expected and is a sanity check, not a novel
prediction. All interpretation of this candidate must be framed as positive-control
context only (governance doc 12).

#### Scientific rationale for inclusion
This is the governance-required positive control. The model's highest score (0.93) is
at this region, consistent with training-set signal at front-face cryptic pockets. MD
must be run on this candidate to validate that (1) the simulation setup can detect IDCL
dynamics and (2) the apo-from-holo system can be meaningfully compared to novel candidates.
If positive control MD fails to show any IDCL flexibility or pocket dynamics, all Wave 1
results for novel candidates must be treated with heightened skepticism.

#### System

```
Structure:         8GLA — human PCNA + AOH1996 derivative ZQZ (Gu L et al.,
                   Cell Chem Biol 2023;30:1235, PMID 37531956). Resolution 3.77 Å.
                   POSITIVE CONTROL ONLY. Flag: below ≤3.5 Å quality threshold.
Chains (PCNA):     Biological assembly chains — verify mapping in deposited CIF.
                   Standard 8GLA has 4 chains (A/B/C/D or similar); resolve to
                   biological assembly (PCNA homotrimer) before setup.
Ligand:            ZQZ (AOH1996-1LE). Holo system: retain. Apo-from-holo: remove ZQZ,
                   energy-minimize, re-equilibrate.
Force field:       PROPOSED AMBER ff19SB + GAFF2/AM1-BCC for ZQZ (holo system only)
Water/ions:        PROPOSED TIP3P, 150 mM NaCl, neutralizing counter-ions
Protonation:       PROPOSED pH 7.4 standard states; identical across all systems
Duration:          PROPOSED ≥3 × 100 ns per system (holo and apo-from-holo)
Seeds:             Record per replicate in MANIFEST.md
```

#### Hypothesis
When ZQZ is removed from the 8GLA crystal structure (apo-from-holo system), will the
IDCL (117-135) and adjacent hydrophobic patch (40-47) retain the pocket geometry seen
in the crystal, or will the pocket collapse? If the AOH1996/IDCL site is a stable
surface feature (pre-existing pocket), apo-from-holo MD should show partial retention.
If it is ligand-induced, it will collapse quickly.

#### Expected observations
Elevated RMSF at IDCL (117-135); partial pocket volume retention at the front-face
hydrophobic cleft in the first 50 ns of apo-from-holo trajectories; ZQZ contact
persistence >50% in holo trajectories.

#### Alternative outcomes
Pocket collapses within 10 ns (induced-fit, ligand-dependent geometry); pocket remains
fully open with minimal RMSF increase (stable surface site); oscillation between open
and closed states (cryptic/transient).

#### Interpretation if pocket does not open (apo-from-holo)
Valid result. AOH1996/8GLA site is ligand-induced under this setup. Allowed claim:
"under the tested apo-from-holo setup, the AOH1996/8GLA front-face pocket did not
retain accessibility." Does not indicate the site is not druggable — only that this
setup did not show pocket persistence.

#### Interpretation if pocket opens
Allowed claim: "supportive MD evidence that the AOH1996/8GLA front-face region can
remain partially accessible in the absence of ligand under the tested setup." This is
positive-control context only. Does NOT validate any Tier 1A prediction.

#### Interpretation if simulation is unstable
Given 3.77 Å starting model, instability is plausible. If equilibration/stability audit
fails (doc 13 required check), trajectory is archived as exploratory only and used for
no claims. The low-resolution start must be flagged in any report.

#### Claim allowed if positive
"Positive-control recovery: supportive MD evidence for accessibility of the known
AOH1996/8GLA front-face IDCL pocket under the tested setup. Hypothesis-generating;
requires experimental validation. Does not validate novel-site predictions."

#### Claim allowed if negative
"Under the tested setup, MD did not support persistent apo accessibility of the
AOH1996/8GLA pocket. Negative result reported as evidence."

#### Success criteria
- IDCL (117-135) RMSF > backbone average in ≥2 of 3 replicates
- Pocket volume at AOH1996 contact zone detectable (>50 Å³) in ≥50% of frames
  in ≥2 of 3 replicates (apo-from-holo)
- ZQZ contact persistence >50% in holo replicates

#### Failure criteria
- Simulation instability (RMSD > 5 Å backbone at equilibration)
- IDCL collapses and becomes rigid (RMSF below mean) across all replicates
- No detectable pocket volume at any timepoint across all replicates

#### Interpretation limitations
- Single model, single checkpoint — results reflect this specific model's scoring
- 3.77 Å start introduces coordinate uncertainty; results should be replicated
  from an independent, higher-resolution starting structure if possible
- Positive result in positive-control MD does not validate Tier 1A candidate MD
- AOH1996 recovery is never framed as novel site prediction (governance doc 12)

#### Metrics
```
RMSD:                 Backbone, per chain, vs. starting structure
RMSF:                 Per residue; focus on IDCL (117-135) and 40-47 patch
Pocket volume:        fpocket/MDpocket time series at AOH1996 contact zone
DCCM:                 Dynamic cross-correlation across PCNA domains/subunits
Interface distances:  Key 40-47 / IDCL / 250-253 pairwise distances
Ligand stability:     ZQZ heavy-atom contact persistence (holo only)
```

---

### T1A-239: Tier 1A Novel Candidate — Residues 239-243

**Candidate ID:** T1A-239
**Residues:** 239-243 (canonical UniProt P12004 numbering)
**Tier:** 1A (Novel surface candidate — no interface overlap)
**Max score:** 0.8472 | **Mean score:** 0.7117 | **N structures:** 229
**Interface overlap:** none

#### Interface classification
Region 239-243 has no overlap with any defined PCNA interface:
pip_box_binding_site (residues 40-44, 117-135, 230-235, 251-253), apim_site (40, 47,
126-129, 233-234), idcl (117-135), trimer_interface (74-185 subset), or
aoh1996_contact_region (23, 25-47, 121-134, 231-234, 250-253). Residues 239-243 lie
between the end of the C-terminal pip_box_binding_site stretch (230-235) and the
C-terminal continuation (251-253) — not a documented PCNA interaction surface.

This is a computationally predicted PCNA surface region. It is NOT a validated site.

#### Scientific rationale for inclusion
Highest-scoring Tier 1A candidate (max 0.8472), robust across 229 human PCNA
structures. The absence of any known interface overlap makes this the strongest
candidate for genuine novel surface prediction from this model. If MD shows transient
pocket formation at this location, it supports further follow-up. If MD shows no
accessible pocket, that is equally informative.

#### System

```
Structure:         1AXC (Gulbis JM et al., Cell 1996;87:297, PMID 8861913).
                   Human PCNA trimer; p21 PIP-box peptide removed. Resolution ~1.35 Å.
                   Alternative: apo Part 1 structure from phase4_candidate_manifest.json
                   (≤3.5 Å quality filter passed, no VARIANT/POSITIVE_CONTROL flag).
Chains:            PCNA homotrimer only; all non-PCNA chains removed before setup.
Ligand:            None (apo simulation only for Tier 1A candidates).
Force field:       PROPOSED AMBER ff19SB
Water/ions:        PROPOSED TIP3P, 150 mM NaCl, neutralizing counter-ions
Protonation:       PROPOSED pH 7.4 standard states
Duration:          PROPOSED ≥3 × 100 ns replicates
Seeds:             Record per replicate in MANIFEST.md
```

#### Hypothesis
Residues 239-243 constitute a computationally predicted PCNA surface region with no
known functional annotation. The hypothesis is that this region can adopt a transiently
accessible conformation (cryptic pocket state) in apo PCNA simulation. If a stable or
semi-stable accessible volume forms at this location in multiple replicates, this
supports designation as a candidate cryptic pocket region for experimental follow-up.

#### Expected observations
If the hypothesis holds: transient increase in solvent-accessible surface area at
239-243 in ≥2 of 3 replicates; detectable pocket volume (fpocket/MDpocket) in >20%
of trajectory frames; local RMSF elevated relative to the domain mean.

#### Alternative outcomes
No detectable pocket at 239-243 (region is stably packed); pocket forms only
transiently (<5% of frames); pocket forms in only 1 of 3 replicates (insufficient
signal); or unexpectedly, the region shows high flexibility but no accessible volume
(disordered rather than pocket-forming).

#### Interpretation if pocket does not open
Valid result. This region, under this simulation setup, does not show evidence of a
cryptic pocket. Allowed claim: "MD did not provide supportive evidence for pocket
formation at residues 239-243 under the tested apo PCNA setup." This result does not
rule out the region as a binding site but reduces its priority.

#### Interpretation if pocket opens
Allowed claim: "Preliminary computational evidence for transient pocket accessibility
at PCNA residues 239-243. Hypothesis-generating result; requires experimental
validation." Does not constitute a validated binding site or therapeutic target claim.

#### Interpretation if simulation is unstable
Trajectory archived as exploratory only per doc 13. Results used for no claims.
Setup reviewed for protonation and chain preparation errors.

#### Claim allowed if positive
"Computationally predicted PCNA surface region 239-243 showed preliminary pocket
accessibility in apo MD under the tested setup. Hypothesis-generating; requires
experimental validation. No therapeutic or druggability claims."

#### Claim allowed if negative
"MD did not support transient pocket formation at 239-243. Negative result is reported
as evidence. Region remains a computationally predicted candidate; experimental
characterization could still reveal accessibility not sampled in these trajectories."

#### Success criteria
- Pocket volume >100 Å³ at residues 239-243 in >10% of frames in ≥2 of 3 replicates
- Local RMSF at 239-243 above the domain-2 backbone mean in ≥2 of 3 replicates
- RMSD stable (<3 Å backbone) confirming structural integrity during pocket sampling

#### Failure criteria
- No detectable pocket volume at 239-243 in any replicate across any timepoint
- Region shows below-average RMSF (rigidly packed) in all replicates
- Simulation instability (RMSD > 5 Å backbone at equilibration)

#### Interpretation limitations
- Single model (GraphSAGE-3L spatial-only), single checkpoint — model-specific result
- Apo MD may not capture binding-induced conformational changes
- 100 ns may be insufficient for rare cryptic pocket events — enhanced sampling not used
- Positive MD result does not validate the site; experimental characterization is required
- No comparison to state-of-the-art tools (fpocket/P2Rank/PocketMiner) yet available

#### Metrics
```
RMSD:                 Backbone, per chain, vs. starting structure
RMSF:                 Per residue; focus on 239-243 and flanking 230-248 window
Pocket volume:        fpocket/MDpocket time series at 239-243 region center
DCCM:                 Dynamic cross-correlation; note any correlated motion with
                      front-face (IDCL) or trimer interface regions
Interface distances:  Backbone and Cβ distances framing the predicted pocket
Ligand stability:     N/A (apo only)
```

---

### T1A-28: Tier 1A Novel Candidate — Residues 28-32

**Candidate ID:** T1A-28
**Residues:** 28-32 (canonical UniProt P12004 numbering)
**Tier:** 1A (Novel surface candidate — no interface overlap)
**Max score:** 0.8157 | **Mean score:** 0.7430 | **N structures:** 229
**Interface overlap:** none

#### Interface classification
Region 28-32 has no overlap with any defined PCNA interface. Residue 27 is the closest
interface-adjacent position (aoh1996_contact_region includes residues 23, 25, 26, 27);
residues 28-32 are NOT included in the AOH1996 contact region and are not part of
pip_box_binding_site, apim_site, idcl, or trimer_interface. They lie on the N-terminal
face of domain 1, immediately distal to the AOH1996 contact zone but not overlapping it.

This is a computationally predicted PCNA surface region. It is NOT a validated site.

#### Scientific rationale for inclusion
Second-highest Tier 1A candidate (max 0.8157) with the highest mean score among Tier 1A
(0.7430), indicating the signal is strong and consistent rather than driven by outlier
structures. Adjacent proximity to the AOH1996 region (but verified non-overlapping)
makes this an interesting test case — if MD shows pocket formation here, it tests whether
the model detects a secondary surface feature near the front face.

#### System

```
Structure:         1AXC (p21 removed, apo). Same as T1A-239 system.
                   Alternative: apo Part 1 structure from phase4_candidate_manifest.json.
Chains:            PCNA homotrimer only.
Ligand:            None.
Force field:       PROPOSED AMBER ff19SB
Water/ions:        PROPOSED TIP3P, 150 mM NaCl, neutralizing counter-ions
Protonation:       PROPOSED pH 7.4 standard states
Duration:          PROPOSED ≥3 × 100 ns replicates
Seeds:             Record per replicate in MANIFEST.md
```

#### Hypothesis
Residues 28-32 constitute a computationally predicted PCNA surface region adjacent to
but distinct from the AOH1996 contact zone. The hypothesis is that this surface can
adopt a transiently accessible conformation in apo MD, potentially reflecting a secondary
binding surface on the front face of the PCNA ring.

#### Expected observations
If hypothesis holds: local RMSF elevated at 28-32 relative to the β-strand average;
transient accessible volume detectable by fpocket/MDpocket; no correlated motion with
the IDCL (would suggest independent dynamics, not front-face coupled).

#### Alternative outcomes
Region is rigidly packed (part of a β-strand); region is flexible but pocket-negative
(disordered, not pocket-forming); or pocket forms but is correlated with IDCL opening
(suggesting the signal reflects proximity to the AOH1996 zone rather than an independent
surface feature).

#### Interpretation if pocket does not open
Valid result. Region not supported by MD as a cryptic pocket under this setup. Allowed
claim: same structure as T1A-239 negative interpretation.

#### Interpretation if pocket opens
Same allowed claim structure as T1A-239 positive interpretation, with the additional
caveat: if the pocket correlates with IDCL motion, this must be reported and the
independence from the AOH1996 site must be explicitly discussed.

#### Interpretation if simulation is unstable
Archived as exploratory, used for no claims.

#### Claim allowed if positive
Same structure as T1A-239, replacing residue range.

#### Claim allowed if negative
Same structure as T1A-239, replacing residue range.

#### Success criteria
- Pocket volume >100 Å³ at 28-32 in >10% of frames in ≥2 of 3 replicates
- Local RMSF at 28-32 above domain-1 backbone mean in ≥2 of 3 replicates
- RMSD stable (<3 Å backbone)
- If correlated with IDCL: must be flagged, not interpreted as independent site

#### Failure criteria
- No detectable pocket at 28-32 in any replicate
- Region below-average RMSF in all replicates
- Simulation instability

#### Interpretation limitations
- Same as T1A-239
- Additional caveat: proximity to AOH1996 contact zone (residue 27) means any positive
  result must verify non-overlap with the aoh1996_contact_region before reporting

#### Metrics
```
RMSD:                 Same as T1A-239
RMSF:                 Focus on 28-32 and flanking 23-37 window
Pocket volume:        At 28-32 region center
DCCM:                 Note correlation with IDCL (117-135); independence from
                      AOH1996 zone must be verified
Interface distances:  Backbone distances framing 28-32
Ligand stability:     N/A
```

---

### T1A-206: Tier 1A Novel Candidate — Residues 206-210

**Candidate ID:** T1A-206
**Residues:** 206-210 (canonical UniProt P12004 numbering)
**Tier:** 1A (Novel surface candidate — no interface overlap)
**Max score:** 0.8087 | **Mean score:** 0.6137 | **N structures:** 229
**Interface overlap:** none

#### Interface classification
Region 206-210 has no overlap with any defined PCNA interface (verified against all
five regions in pcna_interface_map.json). Residues 206-210 are in domain 2 of PCNA,
in an internal region not documented as a functional interaction surface. The lower
mean score (0.6137) relative to max (0.8087) indicates more structural variability
across the 229 scored structures than the top two Tier 1A candidates.

This is a computationally predicted PCNA surface region. It is NOT a validated site.

#### Scientific rationale for inclusion
Third Tier 1A candidate; no interface overlap; max score >0.80. The score variability
(max-mean gap = 0.195, larger than 239-243 and 28-32) suggests this region scores highly
in a structural subset of PCNA conformations. MD can test whether this reflects a
conditionally accessible surface feature.

#### System

```
Structure:         1AXC (p21 removed, apo). Same as T1A-239 system.
                   Alternative: apo Part 1 structure from phase4_candidate_manifest.json.
Chains:            PCNA homotrimer only.
Ligand:            None.
Force field:       PROPOSED AMBER ff19SB
Water/ions:        PROPOSED TIP3P, 150 mM NaCl, neutralizing counter-ions
Protonation:       PROPOSED pH 7.4 standard states
Duration:          PROPOSED ≥3 × 100 ns replicates
Seeds:             Record per replicate in MANIFEST.md
```

#### Hypothesis
Residues 206-210 constitute a computationally predicted PCNA surface region in domain 2.
The hypothesis is that this region shows transient pocket accessibility in apo MD,
reflecting a novel surface feature not captured by any known PCNA interface annotation.

#### Expected observations
If hypothesis holds: elevated RMSF at 206-210; transient pocket volume at this location;
results potentially dependent on which structural subpopulation is sampled.

#### Alternative outcomes
No pocket detected; region is rigidly packed; score variability may reflect structural
diversity across PCNA complexes rather than a cryptic pocket.

#### Interpretation if pocket does not open
Valid result. The score variability may reflect model uncertainty or structural context
rather than a consistent cryptic pocket signal.

#### Interpretation if pocket opens
Same claim structure as T1A-239; requires experimental validation.

#### Interpretation if simulation is unstable
Archived as exploratory.

#### Claim allowed if positive / if negative
Same structure as T1A-239, replacing residue range.

#### Success criteria
Same threshold as T1A-239.

#### Failure criteria
Same as T1A-239. Additionally: if only the high-resolution starting structure (1AXC)
shows no pocket but a high-score alternative structure does, this must be investigated.

#### Interpretation limitations
- Same as T1A-239
- Higher max-mean gap warrants explicit discussion of structural variability in the
  MD report; a single starting structure may not represent the full scoring ensemble

#### Metrics
```
RMSD:                 Backbone, per chain
RMSF:                 Focus on 206-210 and flanking 200-215 window
Pocket volume:        At 206-210 region center
DCCM:                 Note any long-range correlated motion with IDCL or C-terminus
Interface distances:  Backbone distances framing 206-210
Ligand stability:     N/A
```

---

### T1B-170 (DEFERRED): Tier 1B Trimer-Interface Candidate — Residues 170-174

**Candidate ID:** T1B-170
**Residues:** 170-174 (canonical UniProt P12004 numbering)
**Tier:** 1B (Trimer-interface — DEFERRED to MD Wave 2)
**Max score:** 0.9233 | **Mean score:** 0.8681 | **N structures:** 229
**Interface overlap:** trimer_interface (residues 173, 174 in canonical trimer-interface set)

#### Deferral status
T1B-170 is the highest-scoring non-positive-control candidate in all of Phase 4 inference.
It is NOT excluded. It is deferred because the standard Wave 1 protocol (100 ns apo
unbiased MD of assembled trimer) cannot address the relevant hypothesis for a trimer-
interface candidate. See the Tier 1B Justification section of this document for the
full reasoning.

#### Required before any simulation may begin
1. A separate enhanced-sampling pre-registration document specific to Tier 1B.
2. Definition of the ring-breathing collective variable (e.g., inter-subunit Cα distance
   across the 170-185 contact zone, or radius of gyration of the full trimer ring).
3. Human decision on simulation mode: (a) full trimer + metadynamics/umbrella sampling,
   or (b) monomer with explicit biological-relevance caveats.
4. A separate GATE 7B authorization record.

#### Structural context (for Wave 2 planning)
Residues 170-174: 173 and 174 are in the canonical trimer_interface (buried inter-subunit
contacts ≤4.5 Å in 1AXC). The broader region 170-172 may be partially surface-exposed
at the outer edge of the interface. In Wave 2, the hypothesis to pre-register will be:
"Does MD sampling of ring-breathing dynamics reveal a transiently accessible pocket at
or near residues 170-174 that could be modulated by a small molecule?"

#### Recommended Wave 2 PDB
1AXC (full biological assembly, all three PCNA subunits). Enhanced sampling must be
applied on a ring-breathing coordinate rather than running standard unbiased trajectories.

#### Metrics (Wave 2 placeholder)
Ring-opening coordinate (inter-subunit distance), pocket volume at 170-174, DCCM
across subunit interfaces, RMSF of 170-185 region.

---

### T1B-175 (DEFERRED): Tier 1B Trimer-Interface Candidate — Residues 175-179

**Candidate ID:** T1B-175
**Residues:** 175-179 (canonical UniProt P12004 numbering)
**Tier:** 1B (Trimer-interface — DEFERRED to MD Wave 2)
**Max score:** 0.8892 | **Mean score:** 0.8459 | **N structures:** 229
**Interface overlap:** trimer_interface (residues 175, 176, 177, 178, 179 all in canonical
trimer-interface set per pcna_interface_map.json)

#### Deferral status
All five residues (175-179) are canonical trimer-interface positions. This is the most
completely buried of the Tier 1B candidates in this window. The standard MD protocol
cannot meaningfully address accessibility here. Deferred per the Tier 1B justification.
All Wave 2 requirements identical to T1B-170.

#### Note
Residues 175-179 are the most deeply buried at the head-to-tail interface in 1AXC. Any
Wave 2 enhanced-sampling study must explicitly address whether a ring-breathing event is
capable of exposing this region or whether the geometry forecloses any accessible pocket.

---

### T1B-152 (DEFERRED): Tier 1B Trimer-Interface Candidate — Residues 152-156

**Candidate ID:** T1B-152
**Residues:** 152-156 (canonical UniProt P12004 numbering)
**Tier:** 1B (Trimer-interface — DEFERRED to MD Wave 2)
**Max score:** 0.8761 | **Mean score:** 0.8057 | **N structures:** 229
**Interface overlap:** trimer_interface (residues 153, 154 in canonical trimer-interface set)

#### Deferral status
Residues 153 and 154 are canonical trimer-interface contacts; 152, 155, 156 may be
partially surface-exposed at the interface edge. Third highest-scoring non-positive-control
candidate. Deferred per the Tier 1B justification. All Wave 2 requirements identical to
T1B-170.

---

### T2-134: Interface-Adjacent Control — Residues 134-138

**Candidate ID:** T2-134
**Residues:** 134-138 (canonical UniProt P12004 numbering)
**Tier:** 2 (Interface-adjacent — IDCL / PIP-box overlap)
**Max score:** 0.7699 | **Mean score:** 0.5868 | **N structures:** 229
**Interface overlap:** idcl (117-135), pip_box_binding_site (residues 134, 135)

#### Interface classification
Region 134-138 overlaps the distal end of the IDCL (117-135) and residues 134, 135 of
the pip_box_binding_site. Residues 136-138 are not in the canonical IDCL or PIP-box lists.
This is NOT a novel site — it overlaps known PCNA interaction surfaces. It is included as
an interface-adjacent control to test whether MD shows IDCL dynamics extending beyond
the core 118-122 region captured by the positive control.

#### Scientific rationale for inclusion
Including T2-134 alongside the 118-122 positive control allows a direct comparison:
does MD support IDCL dynamics at the distal end (134-138) consistent with the proximal
end (118-122)? If yes, this supports IDCL as a coherent dynamic unit. If not, it suggests
the front-face signal is localized. This information is useful for interpreting Tier 1A
candidate MD results in the context of known front-face dynamics.

#### System

```
Structure:         1AXC (p21 removed, apo). IDCL must be fully ordered in the chosen
                   starting structure; verify completeness before equilibration.
                   Alternative: apo Part 1 structure with resolved IDCL.
Chains:            PCNA homotrimer only.
Ligand:            None.
Force field:       PROPOSED AMBER ff19SB
Water/ions:        PROPOSED TIP3P, 150 mM NaCl, neutralizing counter-ions
Protonation:       PROPOSED pH 7.4 standard states
Duration:          PROPOSED ≥3 × 100 ns replicates
Seeds:             Record per replicate in MANIFEST.md
```

#### Hypothesis
The IDCL distal end (134-138) shows correlated dynamics with the IDCL core (117-133)
and the front-face pocket in apo MD. If so, the model's detection of this region
reflects IDCL-wide flexibility rather than a novel independent pocket.

#### Expected observations
Elevated RMSF at 134-138 correlated with IDCL core (DCCM); accessible volume here
correlated with front-face pocket dynamics; lower scores than positive-control 118-122
in pocket detection tools.

#### Alternative outcomes
134-138 dynamics are uncorrelated with IDCL core (suggests an independent surface
feature); or 134-138 is rigid despite IDCL core flexibility (localized loop dynamics).

#### Interpretation if pocket does not open
Valid result. The IDCL distal end is rigidly packed despite known IDCL flexibility
at the core. Interpretation: model signal at 134-138 likely reflects IDCL proximity
rather than an independent cryptic pocket.

#### Interpretation if pocket opens (correlated with IDCL)
The model correctly detects IDCL dynamics. The T2-134 signal is not an independent
novel pocket but a continuation of the known front-face dynamics. This interpretation
must be stated explicitly and not framed as a novel site.

#### Interpretation if pocket opens (uncorrelated with IDCL)
More interesting. A separate accessible volume at the distal IDCL edge could represent
a secondary binding surface. Must be reported with explicit limitations and flagged for
further investigation.

#### Interpretation if simulation is unstable
Archived as exploratory.

#### Claim allowed if positive (correlated)
"MD supports IDCL-coupled dynamics at residues 134-138, consistent with known IDCL
flexibility. This region overlaps known PCNA interaction surfaces and does not constitute
a novel-site prediction."

#### Claim allowed if positive (uncorrelated)
"Preliminary MD evidence for a secondary accessible surface feature at residues 134-138,
distinct from the IDCL core. This overlaps a known PCNA interaction surface; experimental
characterization is required before any site novelty claim."

#### Claim allowed if negative
"MD did not support independent pocket formation at residues 134-138 beyond correlated
IDCL dynamics."

#### Success criteria
- RMSF at 134-138 elevated relative to β-strand mean in ≥2 of 3 replicates
- DCCM correlation between 134-138 and 117-133 quantified (not assumed)
- Pocket volume assessment at 134-138 separately from 118-122

#### Failure criteria
- 134-138 rigid in all replicates
- Simulation instability

#### Interpretation limitations
- This region overlaps known PCNA interfaces — any positive result must be framed
  as interface-associated, not novel
- IDCL is known to be flexible; elevated RMSF at 134-138 is expected, not surprising
- Positive result does NOT validate a novel binding site at this position

#### Metrics
```
RMSD:                 Backbone, per chain
RMSF:                 Focus on 117-138 full IDCL + distal region
Pocket volume:        At 134-138 separately from 118-122 (compare)
DCCM:                 IDCL core (117-133) vs. distal IDCL (134-138) correlation;
                      IDCL vs. Tier 1A candidate regions (is IDCL dynamics coupled
                      to any novel candidate motion?)
Interface distances:  IDCL distal-end distances
Ligand stability:     N/A
```

---

## Governance Compliance Checklist

Pre-simulation compliance. All items must be verified by the human reviewer before
GATE 7 authorization is granted.

### Doc 13 (MD Validation Rules) — Required

- [ ] All candidates pre-registered before any simulation begins (this document)
- [ ] Required statement reproduced: "MD can support, weaken, redirect, or falsify..."
- [ ] Each candidate has: hypothesis, expected observations, alternative outcomes,
      interpretation if positive, interpretation if negative, interpretation if unstable
- [ ] Replicates ≥3 per system (not a single 100 ns run)
- [ ] Enhanced sampling flagged as needed for Tier 1B (deferred, doc 13 explicitly allows)
- [ ] Negative results explicitly recognized as valid evidence
- [ ] Positive-control (118-122) included before novel candidates are interpreted
- [ ] Apo and holo (positive control) systems to be compared with identical setup
- [ ] Same protonation, force field, water model across all systems
- [ ] Forbidden actions confirmed absent:
  - [ ] "validation" not claimed without this pre-registration
  - [ ] No pocket opening ≠ failed MD (explicitly stated per candidate)
  - [ ] Ligand stability ≠ binding-site proof (not claimed)
  - [ ] Therapeutic relevance NOT claimed from MD alone
  - [ ] Apo/ligand comparisons use identical setup policies

### Doc 14 (Claim Policy) — Required

- [ ] No forbidden wording: "validated binding site", "proven mechanism",
      "clinically actionable", "confirmed drug target", "druggable site",
      "therapeutic target" — all absent from this document
- [ ] All positive outcome claims use: "computationally predicted", "hypothesis-
      generating", "requires experimental validation", "supportive MD evidence",
      "preliminary computational evidence"
- [ ] Positive-control (118-122) framed as sanity check, not novel-site validation
- [ ] No therapeutic/clinical overclaim linking PCNA cancer relevance to actionability
- [ ] Every claim includes: evidence source, confidence level, limitations,
      verification status

### Doc 12 (PCNA-Specific Checks) — Required

- [ ] PCNA treated as trimeric sliding clamp (trimer biology respected)
- [ ] All chain identities verified against biological assembly before setup
- [ ] Trimer interface residues mapped per pcna_interface_map.json (done — 1AXC)
- [ ] PIP-box / APIM / IDCL regions mapped (done — pcna_interface_map.json)
- [ ] AOH1996/8GLA framed as positive control in all sections (done)
- [ ] Tier 1B trimer-interface candidates NOT called novel surface sites (done)
- [ ] ATX-101 not cited as druggability proof for any candidate
- [ ] PCNA cancer relevance not used to imply clinical actionability

### GATE 7 Prerequisites

- [ ] GATE 6 cleared: `reports/phase4/gate6_authorization_20260529.md` (YES)
- [ ] Phase 4 prioritization report reclassified:
      `reports/phase4/phase4_candidate_prioritization_20260529.md` (YES)
- [ ] Tier 1B justification documented explicitly (YES — see above)
- [ ] Positive control included in Wave 1 (YES — 118-122)
- [ ] Candidate-to-PDB mapping documented (YES — mapping table above)
- [ ] MD target-selection rationale documented (YES — selection rationale above)
- [ ] Separate GATE 7B required for Tier 1B Wave 2 candidates (PENDING)

### Provenance

| Artifact | Path | Status |
|----------|------|--------|
| GATE 6 authorization | `reports/phase4/gate6_authorization_20260529.md` | CLEARED |
| Prioritization report (reclassified) | `reports/phase4/phase4_candidate_prioritization_20260529.md` | UPDATED |
| Candidate report (raw scores) | `reports/phase4/phase4_candidate_report_20260529.md` | UNCHANGED |
| Interface overlap analysis | `reports/phase4/phase4_interface_overlap_20260529.md` | UNCHANGED |
| PCNA audit | `reports/phase4/phase4_pcna_audit_20260529.md` | UNCHANGED |
| Interface map | `data/registries/pcna_interface_map.json` | UNCHANGED |
| Positive control pre-reg | `reports/phase4/md/8gla/pre_registration.md` | REFERENCE |
| Frozen checkpoint | `checkpoints/phase3/spatial_only_fold1_seed1_best.pt` | FROZEN |
| Test evaluation (one-shot) | `reports/phase3/test_evaluation_20260529.md` | LOCKED |

---

## What Must NOT Happen Before GATE 7 Authorization

- No MD simulation setup, parameterization, or execution
- No trajectory generation of any kind
- No fpocket/MDpocket analysis of PCNA structures outside of post-GATE-7 scope
- No druggability or therapeutic claims of any kind
- No scientific publication, presentation, or external communication of any result
  labeling these candidates as validated sites

---

*Drafted: 2026-05-29 | Authorization status: PENDING HUMAN DECISION*
*This document is a draft pre-registration package, not an authorization record.*
*Authorization record path (when approved): `reports/phase4/gate7_authorization_YYYYMMDD.md`*
