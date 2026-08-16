# MD Pre-Registration — 8GLA (AOH1996 positive control)

> Pre-registered per `docs/scientific_governance/13_MD_VALIDATION_RULES.md` **before** any
> simulation. Written 2026-05-28 by Advay (parallel track 3a). This is a hypothesis
> registration, not a result and not a claim. MD setup/execution is Reshwant's domain;
> force-field/solvent values below are **PROPOSED defaults to be confirmed**, and must be
> identical across the 8GLA / 5E0V / candidate systems (doc 13).
>
> **Required statement (doc 13):** We do not build expecting one MD result and then panic
> when MD gives unexpected results. MD can support, weaken, redirect, or falsify the working
> hypothesis. All outcomes are evidence.

## System
- Structure: PDB **8GLA** — cancer-associated PCNA + AOH1996 derivative (AOH1996-1LE, ligand
  code **ZQZ**). Gu L et al., *Cell Chem Biol* 2023;30:1235, PMID 37531956. Resolution
  **3.77 Å** (low — flagged; failed the Track-2 ≤3.5 Å quality filter and is force-included
  as positive control only).
- Chains: PCNA chains A/B/C/D as deposited; biological assembly = homotrimer. Chain/assembly
  mapping must be resolved per doc 12 before production.
- Ligand/docked molecule: ZQZ (AOH1996-1LE), present in the crystal. Two systems to compare:
  **(i) holo** (ZQZ retained), **(ii) apo-from-holo** (ZQZ removed, same coordinates).
- Force field: PROPOSED AMBER ff19SB (protein) + GAFF2/ligand parameters for ZQZ — confirm.
- Water/ions: PROPOSED TIP3P, 150 mM NaCl, neutralizing counter-ions — confirm.
- Protonation policy: PROPOSED pH 7.4 standard states; identical across all systems.
- Duration and replicates: PROPOSED ≥3 × 100 ns replicates per system (a single 100 ns run
  is exploratory only, doc 13). Enhanced sampling considered if the pocket is cryptic.
- Random seeds: record per replicate in MANIFEST.md.

## Hypothesis
The GNN should score the AOH1996/ZQZ contact region (residues 23-47, 121-131, 231-234,
250-253; see `pcna_interface_map.json`) as a high-score region. The MD question: when ZQZ is
removed (apo-from-holo), does this front-face pocket **remain open/accessible**, or does it
collapse? This tests whether the AOH1996 site is a stable surface feature vs. ligand-induced.

## Expected observations
If the site is a genuine, ligand-stabilized-but-pre-existing pocket, apo-from-holo MD should
show partial retention of pocket volume around the IDCL (117-135) and the 40-47 hydrophobic
patch, with elevated IDCL flexibility.

## Alternative outcomes
Pocket collapses quickly (induced-fit, ligand-dependent); pocket stays fully open (stable
surface site); or pocket fluctuates between states (cryptic/transient).

## Interpretation if pocket does not open
A valid, reportable result. Indicates the AOH1996 site is ligand-induced under this setup.
Allowed claim: "under the tested setup the AOH1996/8GLA front-face pocket did not remain open
in apo simulation." NOT "the site is not druggable."

## Interpretation if pocket opens
Allowed claim: "supportive computational evidence that the AOH1996/8GLA front-face region can
remain accessible in the absence of ligand under the tested setup." This is **positive-control
context only** and does NOT validate any novel-site prediction (doc 12).

## Interpretation if simulation is unstable
Given the 3.77 Å starting model, instability is plausible. If equilibration/stability audits
fail, the trajectory is archived as exploratory only and used for no claims (doc 13).

## Claim allowed if positive
"Positive-control recovery / supportive MD evidence for accessibility of the known
AOH1996/8GLA interface under the tested setup; hypothesis-generating; requires experimental
validation." (doc 12/14 allowed wording.)

## Claim allowed if negative
"Under the tested setup, MD did not support persistent apo accessibility of the AOH1996/8GLA
pocket." Negative results are valid and reported honestly (doc 13).

## Metrics
- RMSD: backbone, per chain, vs. starting structure.
- RMSF: per residue, focus on IDCL (117-135) and C-terminus.
- Pocket volume: at the AOH1996/ZQZ contact region (fpocket/MDpocket time series).
- DCCM: dynamic cross-correlation across domains/subunits.
- Interface distances: key 40-47 / IDCL / 250-253 pairwise distances framing the pocket.
- Ligand stability/contact persistence: ZQZ heavy-atom contact persistence (holo system).

## Provenance
- Structure source: `data/registries/friend_crawl_registry.json` (8GLA, file in local crawl
  zip). Interface residues: `data/registries/pcna_interface_map.json`.
- Status: PRE-REGISTRATION ONLY. No simulation run. No claims.
