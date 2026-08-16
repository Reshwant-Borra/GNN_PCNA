# Current 0.6792 Geometric Diagnosis

POST-PASS STRONGER INTERNAL ROBUSTNESS REQUIREMENT: the earlier 0.6792 result remains a valid exploratory PASS under the previous gate. The >=0.75 mean-Jaccard target is a new voluntary internal release standard imposed after seeing that result; it is not represented as a universal literature threshold.

Interpretation: **same physical pocket core with nontrivial boundary/fringe extension disagreement**.
The clusters are not three unrelated/displaced pocket solutions. They share a central residue core, but the boundary and an adjacent 231-252 extension differ enough that the stricter release target is not met.
3/3 core residues: 11; >=2/3 residues: 16; union: 20.

Centroid distances (A):
- 42-43: 4.454
- 42-44: 1.394
- 43-44: 5.091

Near-neighborhood overlap:
- 42-43 within 6 A: 0.906
- 42-44 within 6 A: 1.000
- 43-44 within 6 A: 0.889

Seed fractions:
- seed 42: 0.688 in 3/3 core; 0.938 in >=2/3 consensus
- seed 43: 0.846 in 3/3 core; 1.000 in >=2/3 consensus
- seed 44: 0.611 in 3/3 core; 0.833 in >=2/3 consensus

Residue table: `artifacts/strong_robustness_20260815/current_06792_residue_membership.csv`.
Visualization aid: `artifacts/strong_robustness_20260815/current_06792_membership_colored_ca.pdb` uses B-factors 75/50/25 for 3/2/1 seed selection.
