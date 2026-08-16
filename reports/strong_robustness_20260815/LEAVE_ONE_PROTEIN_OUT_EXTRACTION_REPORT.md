# Leave-One-Protein-Out Extraction Report

POST-PASS STRONGER INTERNAL ROBUSTNESS REQUIREMENT: the earlier 0.6792 result remains a valid exploratory PASS under the previous gate. The >=0.75 mean-Jaccard target is a new voluntary internal release standard imposed after seeing that result; it is not represented as a universal literature threshold.

Best LOPO policy: `fixed_rank_fraction_0p06_eps6_ms3_min3_mean_score_sqrt_size`.
Current policy LOPO mean score: 0.6184.
Best policy LOPO mean score: 0.6597.
Current worst LOPO score: 0.4597; best-policy worst LOPO score: 0.4932.
Best-policy min valid-cluster rate: 0.6667.
The LOPO result does not justify replacing the frozen policy because the leading methods are close and no candidate is consistently dominant across proteins.
Detailed cases: `artifacts/strong_robustness_20260815/leave_one_protein_out_cases.csv`.
