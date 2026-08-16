# Source Registry

|ID|type|source|url|used_for|
|---|---|---|---|---|
|SRC-PDB-1W60|SOURCE_FACT|RCSB PDB entry 1W60|https://www.rcsb.org/structure/1W60|1W60 native/apo human PCNA reference; use biological assembly, not ASU, for comparable homotrimer MD.|
|SRC-PDB-8GLA|SOURCE_FACT|RCSB PDB entry 8GLA|https://www.rcsb.org/structure/8GLA|8GLA is caPCNA bound to AOH1996 derivative ligand ZQZ; used as positive-control holo/open structure.|
|SRC-AOH-2023|SOURCE_FACT|Gu et al. Cell Chemical Biology 2023 / PMC10592352|https://pmc.ncbi.nlm.nih.gov/articles/PMC10592352/|AOH1996 targets PCNA/transcription-replication conflict; 8GLA associated with AOH1996/ZQZ structural evidence.|
|SRC-PDB-BIOASM|SOURCE_FACT|RCSB PDB101 biological assembly guide|https://pdb101.rcsb.org/learn/guide-to-understanding-pdb-data/biological-assemblies|Biological assembly can differ from asymmetric unit; MD should simulate biological assembly when that is the biologically relevant oligomer.|
|SRC-POCKETMINER|SOURCE_FACT|Meller et al. Nat Commun 2023|https://www.nature.com/articles/s41467-023-36699-3|PocketMiner predicts cryptic pocket locations from single structures with GVP-GNN; reported ROC-AUC 0.87 on curated cryptic-pocket data.|
|SRC-CRYPTOBENCH|SOURCE_FACT|CryptoBench Bioinformatics 2025|https://academic.oup.com/bioinformatics/article/41/1/btae745/7927823|CryptoBench provides 1107 cryptic binding-site structures with predefined splits and benchmark framing.|
|SRC-ESM2|SOURCE_FACT|facebookresearch ESM repository / ESM-2 model card|https://github.com/facebookresearch/ESM|ESM-2 provides pretrained protein language-model embeddings; model variant used here is documented as esm2_t12_35M_UR50D in repo scripts/docs.|
|SRC-OPENMM-HMR|SOURCE_FACT|OpenMM User Guide heavy hydrogens|https://docs.openmm.org/latest/userguide/application/02_running_sims.html#heavy-hydrogens|OpenMM supports hydrogen mass repartitioning via hydrogenMass to slow fast hydrogen motions.|
|SRC-MDTRAJ-SASA|SOURCE_FACT|MDTraj Shrake-Rupley API|https://mdtraj.org/1.9.4/api/generated/mdtraj.shrake_rupley.html|MDTraj SASA uses Shrake-Rupley style solvent-accessible surface estimation.|
|SRC-UNIPROT-PCNA|SOURCE_FACT|UniProt P12004|https://www.uniprot.org/uniprotkb/P12004/entry|Human PCNA sequence/function reference.|
