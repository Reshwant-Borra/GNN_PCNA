# Next Prompt: CryptoBench Deep Schema And Biological Audit

Proceed to the full CryptoBench schema and biological audit phase.

Do not train.
Do not generate graphs yet.
Do not run MD.
Do not freeze labels or splits yet.

Goal:
Understand exactly what CryptoBench contains scientifically and structurally.

Tasks:

1. Parse and inspect:
- dataset.json
- folds.json
- train/test fold files
- noncryptic-pockets JSON
- CIF inventory metadata

2. Determine:
- exact schema fields
- label meanings
- whether labels are residue-level, pocket-level, or structure-level
- how positives/negatives are defined
- whether apo/holo pairing exists explicitly
- whether folds are leakage-aware
- whether proteins repeat across folds
- whether homolog leakage risk exists
- whether PCNA or PCNA homologs appear

3. Build reports:
- reports/phase2/cryptobench_schema_deep_audit.md
- reports/phase2/cryptobench_split_risk_audit.md
- reports/phase2/cryptobench_label_semantics.md
- reports/phase2/cryptobench_structure_inventory.md
- reports/phase2/pcna_contamination_screen.md

4. Build machine-readable summaries:
- data/registries/cryptobench_schema_summary.json
- data/registries/cryptobench_fold_summary.json
- data/registries/cryptobench_structure_index.json

5. Verify:
- residue numbering consistency
- chain consistency
- CIF readability
- fold integrity
- missing structures
- duplicate identifiers
- malformed entries

6. Investigate graph feasibility:
Without building final graphs yet, determine:
- whether residue-level graph construction is feasible
- what node granularity makes sense
- whether chains/residues align cleanly
- whether edge construction from CIFs appears practical
- whether ESM/protein-sequence alignment is feasible

7. Biological audit:
- determine whether labels appear biologically meaningful
- determine whether negatives are true negatives or unlabeled
- determine whether cryptic/noncryptic definitions appear proxy-based
- identify likely benchmark biases

Important:
Do not assume benchmark correctness.
Do not trust folds automatically.
Do not trust labels automatically.
Do not silently infer biology.

Final output should answer:
- what CryptoBench REALLY is
- whether it is scientifically usable
- what the biggest benchmark risks are
- whether split freeze is feasible
- whether graph-building is feasible
- whether Phase 2 can proceed safely

