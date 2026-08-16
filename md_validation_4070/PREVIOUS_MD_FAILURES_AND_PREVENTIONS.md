# Previous MD Failures And Preventions

Generated: 2026-08-15T18:58:43.139697+00:00

| Problem | Cause | Fix | Automated check | Current status |
| --- | --- | --- | --- | --- |
| Impossible peptide connections across unresolved gaps | SEQRES/gap loss let OpenMM bond across missing loops | run_md.py transfers full sequence and asserts no >2.5 A covalent bonds | assert_no_impossible_bonds plus prep_audit | Protected in preflight; exact smoke still pending |
| Wrong apo/control structures | Prior 1AXC/5E0V variants were not true apo/control | Frozen 1W60 apo and 8GLA reference | pocket JSON and readiness gate check | Protected |
| Wrong biological assembly | ASU-only preparation made incomparable systems | gemmi assembly 1 homotrimer for both | prep_audit expected 3 chains | Protected in preflight |
| Chain mapping errors | Bare residue numbers are ambiguous in homotrimer | pcna_chain_residue_mapping.json | md_readiness_gate checks mapping file | Protected for current chain A hypothesis |
| SASA atom-parity mismatch | Apo/control atom sets differed | atom-key parity required in frozen protocol; prepared static parity is 100 percent | static_reference_analysis.json | Protected for static refs; trajectory parity checked by analyze_md.py |
| PBC/imaging artifacts | Old RMSD/RMSF used un-imaged trajectories | analyze_md.py images before alignment and detects jumps | analysis script checks | Needs smoke trajectory validation |
| Stale/generated input reuse | Existing DONE/topology could be reused silently | Readiness gate checks hashes; preflight kept outside production outputs | md_readiness_gate | Protected for production if gate used |
| Topology/trajectory pairing mismatch | Old trajectory lacked saved topology | run_md.py writes system_solvated.pdb next to DCD | DONE.json topology field and file hash | Protected |
| Pseudoreplication | Chains/frames treated as independent replicates | replicate plan defines trajectory as independent unit | FROZEN_MD_ANALYSIS_PROTOCOL.json | Protected prospectively |
