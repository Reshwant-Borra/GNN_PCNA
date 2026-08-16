# Label Chain Bug Impact Report

Status: mixed. The composite-chain masking bug is confirmed in the historical 25-dim archive, but the recovered 520-dim XL graph lineage that reproduces `d9efd97400f24cb1cd9ab55cf112c174f2a610e405714758f688cd4944cad193` does not use that target-chain comparison path.

## Confirmed Historical Archive Bug

The archived Phase-3 label outputs contain composite-chain examples with all positives masked, including `7ep1` (`A-B`, positive_count 0, masked_count 26), `3w3g` (`A-B`, positive_count 0, masked_count 36), and `5dy9` (`H-I`, positive_count 0, masked_count 8). This is historical 25-dim material unless later evidence links it to a 520-dim run.

## Recovered 520-Dim XL Lineage

The recovered XL graph lineage contains 55 structures, 43 train / 6 validation / 6 test, 36,211 residues, and 1,630 positive graph labels. Labels are embedded in recovered graph tensors and summarized by `data/results/split_integrity_520.json` on branch `pcna-xl-esm-full-final-framing` at `d7cf76d674bced192b3c9d2b4f7f4fbf7ac3a228`.

The 520-dim graph-generation path labels residues from ligand-distance coordinates and does not compare atom-level chain identifiers with a composite target-chain string. For the specific composite-chain bug: affected structures 0; affected train 0; affected validation 0; affected test 0; positive residues lost 0; structures made zero-positive by this bug 0.

The 520 graph tensors do contain two zero-positive structures, `2BKM` in train and `2NMO` in test, but current evidence does not attribute those to the composite-chain bug.

## Decision

Impact classification is A for the recovered `d9efd...` 520-dim graph lineage. The later August three-seed handoff remains unresolved until its exact training/label lineage is recovered.
