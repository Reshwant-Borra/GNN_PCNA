# Prompt to send to Claude for Life Sciences

> Paste everything below the line into Claude for Life Sciences (operon / Claude Science).
> Attach the file **`GNN_PCNA_Failure_Assessment_2026-07.md`** alongside it if the tool supports
> attachments; the prompt also inlines the key facts so it works without the attachment.

---

**Role.** Act as a senior computational structural biologist / early-stage drug-discovery advisor.
I need rigorous, literature-grounded, *honest* guidance — not encouragement. If my approach has a flaw
or my hypothesis is probably wrong, say so plainly. Every outcome (the pocket opens / is static / needs
enhanced sampling) is an acceptable answer; do **not** assume the pocket opens, and flag anything in my
setup that looks like confirmation bias.

**Project.** A student research project trained a graph neural network (GNN) to predict a *cryptic*
(transient, ligand-inducible) druggable pocket on human **PCNA** (Proliferating Cell Nuclear Antigen,
UniProt P12004) — the DNA-replication sliding clamp, a homotrimer, overexpressed in many cancers and
historically "undruggable." The known druggable precedent is **AOH1996** (ligand code **ZQZ**,
co-crystal **PDB 8GLA**, PMID 37531956), which binds a two-subunit interface pocket. Apo reference is
**PDB 1W60**.

**Where it stands (verified facts — see attached assessment for full detail):**
- The GNN *localizes* the AOH1996 pocket well (held-out generalization AUROC 0.8081 / AUPRC 0.3441 over
  13 proteins; recovers the AOH site cleanly), **but it carries no dynamics signal**: at matched pocket
  residues it scores the site ~0.87 in holo (8GLA) and ~0.91 in apo (1W60) — a holo−apo difference of
  ≈ −0.04, essentially zero. So the "cryptic/dynamic" claim can only come from MD, not the network.
- The one MD run to date (1AXC, 25 ns, n=1, no positive control, wrong apo state, corrupt analysis)
  showed the predicted windows as the *most rigid* regions — but that test was methodologically invalid
  and is best classed as *inconclusive*, not negative. It has been rebuilt.
- The corrected validation package now simulates **true apo 1W60** and a **holo-stripped 8GLA positive
  control** (biological homotrimer, matched setup), 3 × 100 ns each, with an automatic gate that reports
  **"inconclusive" instead of a false negative** when the openness metric can't separate the known-open
  control from the closed apo. This corrected run has not been executed yet.
- A coarse normal-mode (ANM) estimate is *suggestive* that the AOH site is more flexible in the
  ligand-associated state (fold-change 0.857 apo → 1.157 holo, Δ +0.300), but ANM is not sampling.

**What I need from you — please address each numbered item:**

1. **Is the AOH1996/ZQZ site actually cryptic?** From the literature and the 8GLA vs 1W60 structures,
   is this pocket described as *opening* from a closed apo state, or is it a largely pre-formed interface
   cavity? This determines whether I should even expect unbiased MD to show opening. Cite sources.

2. **Openness metric / positive-control review.** My gate compares an "openness" signal (pocket SASA +
   pocket-Cα radius of gyration) between the open control (8GLA, ligand stripped) and closed apo (1W60).
   Is that a sound positive control, and is there a better pocket-volume/opening observable
   (MDpocket, POVME, fpocket time-series, a specific collective variable)? Any confounder from stripping
   ZQZ and relaxing, and how to control for it?

3. **Enhanced-sampling plan.** If 3 × 100 ns unbiased MD fails the gate (can't distinguish open from
   closed — the likely outcome for a genuinely cryptic site), give a concrete, prioritized protocol to
   test cryptic opening on a system like PCNA — e.g. metadynamics/OPES (which collective variables?),
   cosolvent / mixed-solvent MD (which probe molecules?), SWISH, Gaussian-accelerated MD, or weighted
   ensemble. Include practical settings feasible on a single RTX 4070 / modest cloud GPU.

4. **Orthogonal in-silico validation.** How should I triangulate so the claim doesn't rest on one GNN?
   Please advise on PocketMiner (Meller et al. 2023), CryptoSite, and FTMap/fragment-hotspot mapping for
   PCNA, and how to reconcile "our GNN localizes the site but shows no opening signal."

5. **Novelty check.** Beyond the AOH site, the GNN flagged windows 239–243, 28–32, 206–210, which
   overlap or abut known PCNA interfaces (the PIP-box front face and the interdomain connecting loop).
   Given PCNA's known interaction surfaces, are any of these plausibly *novel* druggable sites versus
   known interface real estate — and what is the honest, defensible way to test and word a novelty claim?

6. **Wet-lab confirmation path.** If the computational evidence firms up, what experiments would confirm
   a cryptic pocket, ranked by signal-to-cost for a student-scale budget? (e.g. DSF/thermal-shift with a
   fragment, HDX-MS for conformational exchange, crystallographic/cryo-EM soaking, SPR/ITC, site-directed
   mutagenesis of pocket residues + a PCNA functional assay.)

7. **Reviewer red-team.** Given (a) the model that produced the headline numbers currently exists only as
   compiled bytecode with no committed checkpoint (a reproducibility gap I am closing), and (b) the
   localizes-but-no-dynamics-signal nuance above — what would a tough reviewer or competition judge attack
   first, and what is the *minimum defensible* set of claims + evidence I should hold to?

Where useful, pull primary literature (PCNA druggability, the AOH1996 mechanism, cryptic-pocket MD
methodology, PocketMiner/CryptoSite benchmarks) and cite it. Give me a prioritized, actionable plan, and
tell me explicitly which of my current claims are safe to make today and which are not yet supported.
