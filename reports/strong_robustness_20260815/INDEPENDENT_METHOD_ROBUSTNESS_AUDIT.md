# Independent Method Robustness Audit

POST-PASS STRONGER INTERNAL ROBUSTNESS REQUIREMENT: the earlier 0.6792 result remains a valid exploratory PASS under the previous gate. The >=0.75 mean-Jaccard target is a new voluntary internal release standard imposed after seeing that result; it is not represented as a universal literature threshold.

Best full-grid policy: `mcc_rank_count_eps7_ms3_min3_mean_score_sqrt_size` robust score 0.6433.
Current policy grid ID: `mcc_rank_fraction_eps6_ms3_min3_mean_score_sqrt_size`.
Materially better policy found by LOPO rule: `False`.
LOPO score improvement over current: 0.0413.
Current policy full-grid robust score: 0.6239; mean F1 0.3081; valid cluster rate 0.9333.
Best LOPO policy valid-cluster floor: 0.6667; top-1 count 0; top-2 count 1.
No new policy was frozen because the apparent LOPO improvement was small, validation-set dependent, and did not satisfy the material-improvement rule.

Full grid CSV: `artifacts/strong_robustness_20260815/independent_method_full_grid_summary.csv`.
LOPO CSV: `artifacts/strong_robustness_20260815/leave_one_protein_out_summary.csv`.
Selection file-read log confirms `pcna_inputs_read_during_selection: []`.
