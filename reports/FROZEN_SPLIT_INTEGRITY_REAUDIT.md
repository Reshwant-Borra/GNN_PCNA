# Frozen Split Integrity Reaudit

## Inputs

- Recovered split manifest: `data/splits/cryptosite_homology30_split.json`
- Split SHA-256: `828fd6d4e694cc6e258a2de8e63c4130876a9c7897dd14ccc2db15a3e6c1f06a`
- Homology audit: `data/results/homology30_audit.json`
- Homology audit SHA-256: `bb6a368274bc153405d232855cc63d8764e037ac09afef70966b219419b1ddf2`

## Findings

| Quantity | Count |
|---|---:|
| structures | 55 |
| train structures | 43 |
| validation structures | 6 |
| test structures | 6 |
| sequence clusters/components | 49 |
| clusters spanning train/validation | 0 |
| clusters spanning train/test | 0 |
| clusters spanning val/test | 0 |
| train-to-val/test overlap count | 0 |

Verdict from recovered audit: **PASS**, leakage_detected = `false`.

## Caveat

The split is recovered from Git history and matches the available homology audit, but the recorded training metadata contains a different `split_hash` (`a88bd6...`) than the raw recovered file SHA-256. The exact historical hash procedure or canonicalized split bytes remain unresolved.
