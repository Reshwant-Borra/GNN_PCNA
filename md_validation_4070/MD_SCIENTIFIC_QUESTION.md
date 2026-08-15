# MD Scientific Question

## Primary Question

The GNN identifies where on PCNA to investigate. MD tests whether that frozen predicted region reproducibly exhibits predefined accessibility, geometry, flexibility, correlated-motion, or cavity-like dynamics under the simulated conditions.

## What The MD Experiment Tests

The GNN result is a hypothesis about where to investigate PCNA dynamics. The MD experiment tests whether the frozen 3/3 core and >=2/3 supported region show reproducible, predefined changes in accessibility, geometry, flexibility, correlated motion, and open-like CA convex-hull/SASA behavior under the chosen apo/control simulation protocol.

## What The MD Experiment Does Not Test

It does not establish ligand binding, druggability, therapeutic relevance, biological efficacy, or that a true cryptic pocket exists. A negative or inconclusive result from this protocol remains scientifically valid if preparation, control behavior, and analysis sensitivity pass prospectively.

## Secondary Questions

- Does local solvent accessibility increase in the 3/3 core and supported >=2/3 region?
- Does local flexibility change after alignment and PBC correction?
- Does candidate-region geometry expand by predefined CA geometry metrics?
- Are opening-like events reproducible across independent trajectories?
- Are motions correlated with nearby structural elements by DCCM, interpreted qualitatively unless replicate-stable?
- Can the 8GLA reference/control distinguish the relevant open/reference state from 1W60 under frozen analysis?
- Is the 3/3 core more stable and interpretable than the uncertain 1-of-3 fringe?

## Frozen GNN Context

Policy: `independent_mcc_rank_fraction_size_weighted_cluster`. Literal mean pairwise Jaccard: `0.6792`. Interpretation remains `MODERATE / EXPLORATORY PASS`, not strong residue-level reproducibility.
