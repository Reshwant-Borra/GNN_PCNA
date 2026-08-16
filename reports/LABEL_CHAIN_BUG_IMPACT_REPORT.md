# Label Chain Bug Impact Report

## Verdict

Label integrity: **FAIL for historical 520-dim proof**, **PASS for the archived Phase-3 parser inspected here**.

The specific reported bug pattern, comparing an atom-level chain such as `A` or `B` against the literal composite string `A-B`, was not found in the archived Phase-3 label alignment implementation. The archived parser converts both `A-B` and `A,B` to `("A", "B")` before residue inclusion.

## Counts From Authoritative 520-Dim Lineage

The repository still lacks the exact 520-dim label manifest and label-generation provenance, so the required impact counts for the actual frozen training lineage cannot be computed honestly.

| Quantity | Count |
|---|---:|
| total structures | 55 from recovered split / 55 in `split_integrity_520.json` |
| structures with composite target chains | MISSING_LABEL_MANIFEST |
| affected structures before fix | MISSING_LABEL_MANIFEST |
| affected train structures | MISSING_LABEL_MANIFEST |
| affected validation structures | MISSING_LABEL_MANIFEST |
| affected test structures | MISSING_LABEL_MANIFEST |
| positive residues lost | MISSING_LABEL_MANIFEST |
| structures with zero positives caused by bug | MISSING_LABEL_MANIFEST |
| cluster identities | MISSING_LABEL_MANIFEST |
| affected structures crossing folds | MISSING_LABEL_MANIFEST |

## Decision

Decision category: **UNRESOLVED**.

The available evidence is insufficient to choose A/B/C for the frozen 520-dim model because the exact label manifest is missing. The repository must not claim the frozen model was unaffected until the 520-dim label manifest is recovered and hashed.
