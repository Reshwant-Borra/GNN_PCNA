# Seed Stability

Release gate: run/freeze seeds 42/43/44, score 1W60 without tuning on 1W60, then evaluate Jaccard, residue frequency, cluster size/chain consistency, and runner-up margin.

Current status: completed for the frozen `independent_mcc_rank_fraction_size_weighted_cluster` handoff. Mean literal Jaccard is `0.6792`, interpreted as `MODERATE / EXPLORATORY PASS`, with 11 core 3/3 residues, 5 supported 2/3 residues, and 4 uncertain 1/3 fringe residues. This is not Gate-6 approval and does not authorize production MD.
