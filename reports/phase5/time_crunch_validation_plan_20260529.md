# Time-Crunch Validation Plan Review

**Date:** 2026-05-29  
**Prepared by:** Codex planning review  
**Commit reviewed:** `076e4c0`  
**Status:** PLANNING REVIEW ONLY - not an MD authorization record  
**Requested output:** Evaluate a reduced 1AXC-only MD plan under a 24-hour time limit with at least 6 hours reserved for paper preparation.

---

## Budget-Constrained Execution Amendment

**Updated execution recommendation:** For RunPod execution under the later $30 hard
budget, the `3 x 100 ns` scope in this planning review is superseded by
`reports/phase5/runpod_execution_package_20260529.md`.

The RunPod-ready plan is `3 x 25 ns` on the same 1AXC apo-from-p21 system, using the
same candidate windows (`239-243`, `28-32`, `206-210`, `134-138`) plus optional
read-only `118-122` reference analysis. The scientific framing is unchanged:
exploratory short-timescale MD only, not official GATE 7 Wave 1 completion and not a
validated-site claim.

---

## Executive Summary

**Recommendation: APPROVE WITH LIMITATIONS.**

The proposed reduced plan is scientifically defensible only as a time-crunch, exploratory 1AXC apo triage run. It is not a full substitute for the official GATE 7 Wave 1 plan and should not be described as completing GATE 7 MD validation.

The plan's strongest point is efficiency: one set of 3 x 100 ns apo PCNA trajectories can be analyzed for all proposed 1AXC windows: 239-243, 28-32, 206-210, and 134-138. This avoids wasteful duplicate simulations for windows on the same prepared structure.

The main weakness is omission of the official 8GLA AOH1996 positive-control systems. Governance and the GATE 7 package require positive-control framing before novel candidate interpretation. Without 8GLA holo and apo-from-holo, any result can support only a limited statement such as: "under a 1AXC apo-from-p21 setup, these candidate windows showed/failed to show local dynamic pocket-like behavior." It cannot validate novel-site predictions, druggability, mechanism, or general PCNA pocket behavior.

Given the 24-hour remaining window and the explicit need to preserve at least 6 hours for paper writing, this reduced plan is preferable to starting the full Wave 1 campaign and failing to finish or interpret it. The recommended operational constraint is a hard compute-and-analysis stop no later than 18 hours after start. If complete analysis is not ready by then, the paper should report MD as deferred rather than forcing an under-audited interpretation.

---

## Rationale

The official Phase 4 state shows that GATE 6 is cleared and GATE 7 remains blocked pending human authorization. The relevant current artifacts are:

- `.memory/PROJECT_STATE.md`: Phase 4 complete; GATE 7 blocked.
- `reports/phase4/gate7_md_decision_draft_20260529.md`: official Wave 1 draft package.
- `reports/phase4/phase4_candidate_prioritization_20260529.md`: corrected Tier 1A / Tier 1B / Tier 2 / Tier 3 classification.
- `reports/phase4/phase4_candidate_report_20260529.md`: raw ranked candidate regions.
- `reports/phase4/phase4_interface_overlap_20260529.md`: known-interface overlap analysis.
- `reports/phase4/phase4_pcna_audit_20260529.md`: PCNA inference audit.
- `data/registries/pcna_interface_map.json`: PCNA interface, IDCL, PIP/APIM, trimer-interface, and AOH1996 contact mapping.

The governing rules are:

- `docs/scientific_governance/13_MD_VALIDATION_RULES.md`: MD is supportive evidence only; single 100 ns trajectories are exploratory; negative results are valid; replicates are preferred; interpretation must be pre-registered.
- `docs/scientific_governance/33_PRE_MD_REALITY_CHECK.md`: MD must test specific, falsifiable hypotheses and cannot be "let's see what happens" evidence.
- `docs/scientific_governance/12_PCNA_SPECIFIC_CHECKS.md`: PCNA must be treated as a trimer; known interfaces and AOH1996/8GLA positive-control status must be respected.
- `docs/scientific_governance/14_CLAIM_POLICY.md` and `24_PROJECT_SCOPE.md`: no therapeutic, clinical, validated-site, or druggability claims from model output or MD alone.
- `docs/scientific_governance/26_HUMAN_REVIEW_GATES.md`: first MD interpretation requires human review.
- `docs/scientific_governance/15_PROVENANCE_AND_REPRODUCIBILITY.md`: any executed MD artifact must preserve setup, command, seed, environment, and input/output provenance.

The time-crunch plan is a practical compromise. It preserves the highest-priority no-interface-overlap Tier 1A windows and one IDCL/PIP-adjacent control while avoiding 8GLA ligand parameterization and low-resolution 8GLA stability risk.

---

## Scope

### In Scope

- Prepare a planning recommendation for a reduced 1AXC-only MD campaign.
- Evaluate governance consistency, risks, feasibility, and relationship to official GATE 7.
- Estimate runtime and storage at planning level for H200 and B200-class hardware.
- Define expected outputs if the plan is later authorized.

### Out of Scope

- No MD setup.
- No MD execution.
- No trajectory analysis.
- No training, inference, or evaluation reruns.
- No edits to official GATE 7 documents.
- No scientific claims that candidates are validated, druggable, therapeutic, or mechanistically confirmed.

---

## Systems to Run

### Proposed Reduced System

| System ID | Starting structure | State | Candidate windows analyzed | Replicates | Production length |
|---|---|---|---|---:|---:|
| TC-1AXC-APO | 1AXC PCNA trimer, p21 peptides removed | apo-from-p21 | 239-243, 28-32, 206-210, 134-138 | 3 | 100 ns each |

Preparation assumptions:

- Use biological PCNA trimer from 1AXC.
- Remove p21 peptide chains before production.
- Preserve PCNA trimer assembly.
- Use the same force field, water model, ion concentration, protonation policy, equilibration protocol, and trajectory save policy across all replicates.
- Record random seeds separately for each replicate.
- Analyze all four windows from the same three trajectories.

### Candidate Interpretation

| Window | Tier | Official context | Reduced-plan interpretation |
|---|---|---|---|
| 239-243 | Tier 1A | Highest no-interface-overlap candidate | Main no-interface candidate; can be tested for local transient pocket-like behavior in 1AXC apo only. |
| 28-32 | Tier 1A | Second no-interface-overlap candidate | Useful but close to AOH1996 contact residue 27; any IDCL/front-face coupling must be flagged. |
| 206-210 | Tier 1A | Third no-interface-overlap candidate | Useful but lower mean score and larger max-mean gap; negative result may indicate structure-context dependence. |
| 134-138 | Tier 2 control | IDCL/PIP-box adjacent control | Not novel; use as known-interface-adjacent comparator for IDCL dynamics. |

Recommended no-cost amendment if the plan is executed: also compute read-only metrics for 118-122 from the same 1AXC trajectories as an internal IDCL/front-face reference. This does not replace 8GLA, but it helps interpret 134-138 and 28-32 without additional simulation time.

---

## Deferred Systems

| Deferred item | Official role | Consequence of deferral |
|---|---|---|
| 8GLA holo with ZQZ retained | AOH1996 positive-control system | No ligand-contact persistence or known AOH1996 recovery test in the time-crunch run. |
| 8GLA apo-from-holo with ZQZ removed | AOH1996 pocket persistence test | Cannot test whether the AOH1996 pocket persists after ligand removal under matched setup. |
| 118-122 official positive-control candidate | Tier 3 positive control | Official positive-control evidence is absent unless 8GLA is later run. 1AXC-only 118-122 analysis would be an internal reference only. |
| Tier 1B trimer-interface candidates 170-174, 175-179, 152-156 | Highest non-positive-control scores, but trimer-interface class | Deferral remains scientifically appropriate; standard 100 ns apo trimer MD is not expected to sample ring opening. |
| Expanded Tier 1A campaign | Broader follow-up | Time-crunch run cannot evaluate candidate robustness across structures or starting conformations. |

---

## Runtime Estimates

No committed project-specific H200/B200 MD benchmark was found in `reports/`, `wiki/`, or `docs/`. The estimates below are planning-grade and should be replaced by a short benchmark if MD is later authorized.

Hardware reference points:

- NVIDIA lists H200 as 141 GB HBM3e with 4.8 TB/s memory bandwidth.
- NVIDIA lists DGX B200 as 8 Blackwell GPUs with 1,440 GB total GPU memory and 64 TB/s total HBM3e bandwidth, i.e. approximately 180 GB and 8 TB/s per GPU.
- NVIDIA's GROMACS application table reports multi-GPU B200 and H100 benchmark performance on standard datasets, but not this exact PCNA system.

Assumed system size:

- 1AXC graph audit: 750 PCNA residue nodes for the selected chains.
- Expected solvated production system: roughly 100,000-200,000 atoms, depending on box padding and ions.
- Production workload: 3 trajectories x 100 ns = 300 ns total simulation.

Estimated wall time:

| Hardware / scheduling | Conservative throughput assumption | 3 x 100 ns serial wall time | If 3 replicates run concurrently | Feasibility under 18-hour compute-analysis window |
|---|---:|---:|---:|---|
| 1 x H200 | 200-500 ns/day per active trajectory | 14-36 hours | 5-12 hours if GPU sharing or 3 GPUs available | Risky on one GPU; feasible with parallel GPUs and fast setup. |
| 1 x B200 | 300-800 ns/day per active trajectory | 9-24 hours | 3-8 hours if GPU sharing or 3 GPUs available | Feasible if the software stack is Blackwell-ready and setup is smooth. |
| 3 x H200 | 200-500 ns/day per replicate | 5-12 hours elapsed | 5-12 hours | Feasible, leaving analysis and paper time. |
| 3 x B200 | 300-800 ns/day per replicate | 3-8 hours elapsed | 3-8 hours | Best option if available and stable. |

Operational timing recommendation:

- Reserve 0.5-2 hours for structure preparation, minimization, equilibration checks, and launch overhead.
- Reserve 2-4 hours for trajectory quality audit and primary window metrics.
- Stop compute/analysis no later than 18 hours after start to preserve at least 6 hours for paper writing.
- If the 3 replicate trajectories or the core metrics are incomplete at the 18-hour mark, report the MD campaign as deferred or incomplete; do not force a claim.

---

## Storage Estimates

Storage depends mainly on atom count and coordinate save frequency.

Planning assumptions:

- Solvated 1AXC apo trimer: approximately 100,000-200,000 atoms.
- Production length: 3 x 100 ns.
- Recommended for time-crunch analysis: save compressed coordinates every 50-100 ps for pocket/RMSF/DCCM screening, plus a less frequent full-precision checkpoint/restart policy.

Estimated output footprint:

| Save policy | Per 100 ns trajectory | 3 replicate total | Notes |
|---|---:|---:|---|
| Lean compressed trajectory, 100 ps frames | ~0.5-2 GB | ~1.5-6 GB | Usually enough for first-pass RMSD/RMSF/pocket time series. |
| Denser compressed trajectory, 10 ps frames | ~5-20 GB | ~15-60 GB | Better temporal resolution, higher I/O and analysis cost. |
| Full package with logs, energies, checkpoints, processed metrics, plots | add ~1-5 GB | add ~3-15 GB | Depends on restart frequency and retained intermediate files. |

Recommended planning reservation: **100 GB free local storage minimum** for the reduced plan. Use **200 GB** if dense frame output or multiple restart checkpoints are retained. The full official Wave 1 package would require substantially more storage because it adds 8GLA holo and apo-from-holo trajectories, and possibly duplicate system setups if interpreted per candidate rather than per structure.

---

## Risks and Limitations

1. **Not equivalent to official GATE 7 Wave 1.** The official draft includes 8GLA positive-control systems and explicitly frames 118-122 as required positive-control context. The reduced plan omits that system.

2. **Positive-control weakness.** Without 8GLA holo and apo-from-holo, the run cannot test ZQZ contact persistence or AOH1996 pocket retention. This limits any interpretation of novel Tier 1A windows.

3. **1AXC is not a clean apo structure.** 1AXC is a PCNA-p21 PIP-box complex; the proposed apo state is apo-from-p21 after peptide removal. Results may reflect relaxation from a peptide-bound conformation.

4. **Single starting structure.** All conclusions are conditional on 1AXC. The run cannot distinguish robust PCNA dynamics from artifacts of the 1AXC starting conformation.

5. **100 ns is still short.** Governance doc 13 states that a single 100 ns trajectory is exploratory. Three replicates improve confidence but do not make rare cryptic-pocket events exhaustive.

6. **Shared-trajectory analysis reduces independence.** Analyzing four windows from the same trajectories is efficient and scientifically valid for a common system, but the windows are not independent MD experiments.

7. **Tier 1B remains unresolved.** The highest non-positive-control scores are the trimer-interface Tier 1B candidates. Their deferral is justified, but any paper must acknowledge that the strongest scoring non-positive-control class was not tested here.

8. **Paper-time risk.** If the run overruns, analysis will consume the 6 hours needed for writing. This is a practical stop condition: incomplete MD should be reported as deferred, not rushed.

9. **Claim limitations.** Allowed wording is limited to preliminary, computational, hypothesis-generating, and under-tested-setup statements. No "validated site", "druggable site", "therapeutic target", or mechanism claim is allowed.

---

## Expected Outputs

If later authorized and executed, the reduced plan should produce:

- `reports/phase5/md/time_crunch_1axc/MANIFEST.md` with structure source, commit, command, environment, force field, water model, ion policy, protonation policy, seeds, and hashes.
- Prepared 1AXC apo-from-p21 topology and coordinates with non-PCNA chains removed.
- Three minimized/equilibrated systems with stability audit.
- Three 100 ns production trajectories.
- Per-replicate RMSD and per-chain stability plots.
- Per-window RMSF for 239-243, 28-32, 206-210, and 134-138.
- Per-window pocket-volume or pocket-detection time series.
- DCCM or correlation metrics, especially checking coupling between Tier 1A windows and IDCL/front-face dynamics.
- Distance distributions for window-specific pocket-framing residues.
- A concise interpretation table: supports, partially supports, inconclusive, weakens, or contradicts the pre-registered hypothesis.
- Claim audit text before any paper use.

Minimum paper-safe output if time is short:

- State that full GATE 7 MD was deferred.
- Optionally report that a time-crunch 1AXC-only exploratory plan was prepared, not executed or not fully interpreted.
- Do not include MD conclusions unless all three trajectories pass stability and the planned metrics are complete.

---

## Relationship to the Official GATE 7 Plan

The official GATE 7 Wave 1 plan includes:

- Positive control: 118-122, mapped to AOH1996/IDCL context.
- Tier 1A top-3: 239-243, 28-32, 206-210.
- Interface-adjacent control: 134-138.
- 8GLA holo and apo-from-holo systems for AOH1996 positive-control comparison.
- 1AXC apo-from-p21 simulations for the Tier 1A and Tier 2 windows.
- Tier 1B trimer-interface candidates deferred to Wave 2 with enhanced-sampling requirements.

The time-crunch plan preserves:

- The three Tier 1A windows.
- The 134-138 IDCL/PIP-adjacent control.
- Three 100 ns replicates.
- The principle of analyzing PCNA as a trimer.
- The deferral of Tier 1B trimer-interface candidates.

The time-crunch plan removes or defers:

- 8GLA holo.
- 8GLA apo-from-holo.
- Official AOH1996 positive-control validation.
- Cross-system comparison between AOH1996/ZQZ and 1AXC apo-from-p21.
- Any expanded MD campaign.

Therefore, this plan should be described as **GATE 7A time-crunch exploratory triage**, not as the official Wave 1 completion. It can inform the paper only if its limited scope is made explicit and if human review approves the interpretation.

---

## Final Recommendation

**APPROVE WITH LIMITATIONS.**

Approve the reduced plan only under these constraints:

1. It is explicitly named a time-crunch exploratory 1AXC apo triage plan.
2. It is not presented as completing the official GATE 7 Wave 1 plan.
3. It does not replace the deferred 8GLA positive-control systems.
4. It uses 3 x 100 ns replicates, not a single trajectory.
5. It analyzes all four proposed windows from the same trajectories.
6. It preserves at least 6 hours for paper preparation by enforcing an 18-hour compute-analysis cutoff.
7. It reports negative or inconclusive outcomes honestly.
8. It uses only cautious, governance-compliant claim language.
9. It requires separate human authorization before any MD setup or execution.

If the goal is to make a strong MD-supported claim for the paper, **reject** this as insufficient. If the goal is to obtain the best defensible exploratory evidence within the remaining time while preserving writing time, **approve** it as the least risky reduced plan.

---

## Source and Evidence Status

| Source | Role | Evidence status | Confidence |
|---|---|---|---|
| `.memory/PROJECT_STATE.md` | Current phase and GATE 7 status | verified local project state | high |
| `reports/phase4/gate7_md_decision_draft_20260529.md` | Official Wave 1 draft and candidate rationale | verified local artifact | high |
| `reports/phase4/phase4_candidate_prioritization_20260529.md` | Tier classifications | verified local artifact | high |
| `reports/phase4/phase4_candidate_report_20260529.md` | Candidate scores | verified local artifact | high |
| `reports/phase4/phase4_interface_overlap_20260529.md` | Interface overlap | verified local artifact | high |
| `reports/phase4/phase4_pcna_audit_20260529.md` | Structure counts and PCNA audit | verified local artifact | high |
| `data/registries/pcna_interface_map.json` | PCNA interface mapping | verified local artifact | high |
| `docs/scientific_governance/13_MD_VALIDATION_RULES.md` | MD rules | binding governance | high |
| `docs/scientific_governance/33_PRE_MD_REALITY_CHECK.md` | Pre-MD hypothesis rules | binding governance | high |
| `docs/scientific_governance/12_PCNA_SPECIFIC_CHECKS.md` | PCNA-specific rules | binding governance | high |
| `docs/scientific_governance/14_CLAIM_POLICY.md` | Claim policy | binding governance | high |
| `docs/scientific_governance/24_PROJECT_SCOPE.md` | Scope limits | binding governance | high |
| `docs/scientific_governance/15_PROVENANCE_AND_REPRODUCIBILITY.md` | Provenance rules | binding governance | high |
| NVIDIA H200 product page: https://www.nvidia.com/en-gb/data-center/h200/ | H200 memory/bandwidth reference | official hardware source | high |
| NVIDIA DGX B200 product page: https://www.nvidia.com/en-us/data-center/dgx-b200/ | B200 aggregate memory/bandwidth reference | official hardware source | high |
| NVIDIA HPC application performance page: https://developer.nvidia.com/hpc-application-performance | GROMACS benchmark context | official benchmark context, not PCNA-specific | medium |
