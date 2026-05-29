# MD Pre-Registration — 5E0V (PCNA reference)

> Pre-registered per `docs/scientific_governance/13_MD_VALIDATION_RULES.md` **before** any
> simulation. Written 2026-05-28 by Advay (parallel track 3b). Hypothesis registration, not
> a result and not a claim. Setup values are PROPOSED defaults to confirm and must match the
> 8GLA / candidate systems (doc 13).
>
> **Required statement (doc 13):** MD can support, weaken, redirect, or falsify the working
> hypothesis. All outcomes are evidence.

## ⚠ Critical structure caveat (read before using 5E0V as "apo reference")

The task brief calls 5E0V "apo PCNA." **It is not.** RCSB / primary literature show 5E0V is
the **PCNA S228I disease variant in complex with a FEN1 peptide** (chains C/D, FEN1 ~res
335-350); resolution 2.07 Å (Duffy CM, Hilbert BJ, Kelch BA. *J Mol Biol* 2016;428:1023-1040,
PMID 26688547). The S228I mutation itself **disrupts the front-face binding site**. Therefore:

- 5E0V as-deposited is **mutant + peptide-bound**, not wild-type apo.
- Using it as a clean apo WT reference is **not valid without modification**, and even after
  stripping the peptide it carries the S228I substitution at the binding site.
- **Recommendation:** confirm a true-apo wild-type PCNA reference before production. Options
  to evaluate: WT PCNA chains from a complex with partner removed (e.g., 1AXC PCNA A/C/E
  minus p21), or another apo WT entry. This decision is flagged to Reshwant and logged as an
  open question.

This pre-registration is written for the **intended apo WT reference role**; the chosen
coordinates must satisfy the caveat above.

## System
- Structure: nominal **5E0V** (see caveat) — intended role: apo WT PCNA reference.
- Chains: PCNA homotrimer; **strip** FEN1 peptide (C/D), ions, waters for an apo run.
- Mutation: S228I present in 5E0V — must be reverted to WT (S228) or a WT structure used.
- Ligand/docked molecule: none (apo reference).
- Force field: PROPOSED AMBER ff19SB — confirm; identical to 8GLA system.
- Water/ions: PROPOSED TIP3P, 150 mM NaCl — confirm.
- Protonation policy: PROPOSED pH 7.4 standard states; identical across systems.
- Duration and replicates: PROPOSED ≥3 × 100 ns replicates.
- Random seeds: record per replicate in MANIFEST.md.

## Hypothesis
Characterize **baseline conformational dynamics** of wild-type apo PCNA, specifically the
flexibility of the **IDCL (residues 117-135)** and the **trimer interface** (74-83, 108-117,
143-185; see `pcna_interface_map.json`). Establishes the apo reference behavior against which
the 8GLA (AOH1996) and candidate systems are compared.

## Expected observations
Elevated RMSF in the IDCL and C-terminus relative to the β-barrel core (consistent with
solution NMR, De Biasio 2012, PMID 23110233); a stable closed trimer ring.

## Alternative outcomes
Unexpectedly rigid IDCL; trimer interface loosening; transient front-face pocket opening in
the absence of any ligand (would itself be a notable, reportable baseline observation).

## Interpretation if pocket does not open
Expected for an apo reference; provides the baseline "closed/low-accessibility" state. No
claim beyond "baseline apo dynamics characterized under the tested setup."

## Interpretation if pocket opens
A transient front-face opening in apo WT is reportable as "computational evidence of
intrinsic front-face accessibility under the tested setup" — context for cryptic-pocket
behavior, **not** a druggability or novel-site claim (doc 12/14).

## Interpretation if simulation is unstable
Archive as exploratory only; used for no claims; re-examine setup (doc 13).

## Claim allowed if positive
"Baseline apo PCNA dynamics (IDCL/C-terminus flexibility, trimer-interface stability)
characterized under the tested setup; reference for comparison; requires careful comparison
to holo systems with identical setup."

## Claim allowed if negative
"Under the tested setup, apo PCNA showed [observed] dynamics; no pocket opening observed."
All outcomes valid.

## Metrics
- RMSD: backbone per chain vs. start.
- RMSF: per residue; IDCL (117-135), C-terminus, trimer interface.
- Pocket volume: front-face PIP/IDCL region time series (baseline).
- DCCM: inter-domain and inter-subunit correlations.
- Interface distances: trimer-interface contact distances; IDCL gating distances.
- Ligand stability/contact persistence: N/A (apo).

## Provenance
- Structure: `data/registries/friend_crawl_registry.json` (5E0V). Identity correction:
  RCSB 5E0V / PMID 26688547. Interface residues: `data/registries/pcna_interface_map.json`.
- Status: PRE-REGISTRATION ONLY. No simulation run. No claims.
