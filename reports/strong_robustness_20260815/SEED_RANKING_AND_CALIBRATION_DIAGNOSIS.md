# Seed Ranking and Calibration Diagnosis

POST-PASS STRONGER INTERNAL ROBUSTNESS REQUIREMENT: the earlier 0.6792 result remains a valid exploratory PASS under the previous gate. The >=0.75 mean-Jaccard target is a new voluntary internal release standard imposed after seeing that result; it is not represented as a universal literature threshold.

Global Spearman correlations:
- 42-43: 0.8497
- 42-44: 0.8069
- 43-44: 0.8787

Local 8 A Spearman correlations around the selected pocket:
- 42-43: 0.8631 across 55 residues
- 42-44: 0.9250 across 55 residues
- 43-44: 0.8982 across 55 residues

Top-k residue-overlap Jaccards:
- 42-43 top-10: 0.2500
- 42-44 top-10: 0.3333
- 43-44 top-10: 0.3333
- 42-43 top-20: 0.4815
- 42-44 top-20: 0.5385
- 43-44 top-20: 0.4286
- 42-43 top-50: 0.6129
- 42-44 top-50: 0.6667
- 43-44 top-50: 0.6129

Score distributions are recorded in `seed_ranking_and_calibration_diagnosis.json`.

Diagnosis: rankings are similar; absolute score distributions differ materially. The current disagreement is mostly boundary/extraction/calibration, not an obviously different learned pocket.
