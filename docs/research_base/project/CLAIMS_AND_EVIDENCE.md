# Claims and Evidence

|ID|statement|type|source|where used|
|---|---|---|---|---|
|FACT-REPO-001|Current starting branch was main at HEAD 5b2ce676c790c4aac0caa10dc4226b5a924791c0.|REPO_MEASUREMENT|reports/final_consolidation/STARTING_STATE.md|release audit|
|FACT-REPO-002|Active shell has Python 3.12.10 but lacks pytest, numpy, torch, torch_geometric, OpenMM, MDTraj, MDAnalysis, BioPython.|REPO_MEASUREMENT|reports/final_consolidation/STARTING_STATE.md|test/training feasibility|
|FACT-REPO-003|`gnn_pcna_pre_md_v3.zip` was not found under the searched parent workspace.|REPO_MEASUREMENT|find .. -maxdepth 3|package consolidation|
|FACT-REPO-004|`Desktop/GNN_PCNA/` contained 1567 tracked files before archiving.|REPO_MEASUREMENT|reports/final_consolidation/file_inventory.csv|cleanup|
|FACT-PCNA-001|Human PCNA is represented as UniProt P12004 in this project.|SOURCE_FACT|SRC-UNIPROT-PCNA|biology|
|FACT-PCNA-002|1W60 is the project apo/native PCNA reference structure.|SOURCE_FACT|SRC-PDB-1W60|MD apo|
|FACT-PCNA-003|8GLA is a PCNA/AOH1996 derivative ZQZ co-crystal used as the positive control.|SOURCE_FACT|SRC-PDB-8GLA; SRC-AOH-2023|MD control|
|FACT-PCNA-004|Biological assembly and asymmetric unit may differ for X-ray structures.|SOURCE_FACT|SRC-PDB-BIOASM|MD assembly|
|FACT-ML-001|PocketMiner is a GNN-based cryptic-pocket predictor reported on a curated 39-protein cryptic-pocket dataset.|SOURCE_FACT|SRC-POCKETMINER|benchmark framing|
|FACT-ML-002|CryptoBench provides a larger cryptic binding-site benchmark with 1107 structures.|SOURCE_FACT|SRC-CRYPTOBENCH|future benchmark|
|FACT-ML-003|The consolidated GNN model code uses dual spatial/sequential GATv2 branches and optional ESM2 concatenation.|REPO_MEASUREMENT|src/models/cryptic_gnn.py|model|
|FACT-ML-004|`scripts/run_v3_inference.py` has a stale-checkpoint guard keyed to the virtual-node fix date.|REPO_MEASUREMENT|scripts/run_v3_inference.py|prior fix 2|
|FACT-ML-005|`scripts/finetune_v3_fixed.py` exposes `--seed` and seeds random, numpy, and torch near the top of main.|REPO_MEASUREMENT|scripts/finetune_v3_fixed.py|prior fix 3|
|FACT-MD-001|`md_validation_4070/analyze_md.py` contains atom-level pocket parity logic.|REPO_MEASUREMENT|md_validation_4070/analyze_md.py|prior fix 4|
|FACT-MD-002|`md_validation_4070/run_md.py` contains impossible-bond assertion wiring.|REPO_MEASUREMENT|md_validation_4070/run_md.py|prior fix 5|
|FACT-MD-003|OpenMM supports hydrogen-mass repartitioning configuration.|SOURCE_FACT|SRC-OPENMM-HMR|MD protocol|
|FACT-MD-004|MDTraj provides Shrake-Rupley SASA calculation.|SOURCE_FACT|SRC-MDTRAJ-SASA|analysis|
|RESULT-SELECT-001|An independent non-PCNA benchmark selected `independent_mcc_rank_fraction_size_weighted_cluster` as the frozen extraction policy.|OBSERVATION/RESULT|artifacts/pre_md_independent_extraction_20260815/independent_extraction_selection_results.json|pre-MD extraction gate|
|RESULT-PCNA-001|Applying the frozen policy once to frozen 1W60 seed outputs 42/43/44 produced PRE-MD STABILITY PASS with literal mean Jaccard 0.6792 and 16 consensus residues.|OBSERVATION/RESULT|artifacts/pre_md_independent_extraction_20260815/final_1w60_three_seed_stability_report.json|MD handoff eligibility|
|RESULT-ROBUST-001|The post-pass stronger internal robustness audit did not identify a materially better independent extraction policy and did not run a second 1W60 evaluation.|OBSERVATION/RESULT|artifacts/strong_robustness_20260815/strong_robustness_summary.json; reports/strong_robustness_20260815/INDEPENDENT_METHOD_ROBUSTNESS_AUDIT.md|release-readiness decision|
|RESULT-ROBUST-002|The prior 0.6792 1W60 result shares a physical pocket core but falls short of the new internal >=0.75 mean-Jaccard target and has minimum pairwise Jaccard 0.6316.|OBSERVATION/RESULT|reports/strong_robustness_20260815/CURRENT_06792_GEOMETRIC_DIAGNOSIS.md; reports/pre_md_independent_extraction_20260815/FINAL_1W60_THREE_SEED_STABILITY_REPORT.md|strong robustness verdict|
|CLAIM-PCNA-001|The frozen GNN/extraction workflow prioritizes a seed-stable candidate residue region on 1W60 under the predeclared pre-MD gate.|HYPOTHESIS_GENERATING / COMPUTATIONAL_RESULT|RESULT-PCNA-001; DECISION-SELECT-003|handoff wording only|
|CLAIM-PCNA-002|The current frozen workflow has not achieved the post-pass stronger internal release target for production-MD readiness.|HYPOTHESIS_GENERATING / COMPUTATIONAL_RESULT|RESULT-ROBUST-001; RESULT-ROBUST-002; DECISION-ROBUST-001|current project status|
