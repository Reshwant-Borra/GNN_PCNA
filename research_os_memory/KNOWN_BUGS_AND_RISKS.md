# KNOWN_BUGS_AND_RISKS.md

Last updated: 2026-05-24T00:00:00Z
Updated by: human (initial bootstrap)
Status: current

Full machine-readable record: `../research_os_registries/issue_registry.json`

---

## Critical Bugs

### BUG-001 / ISSUE-0001: 9B8T chain assignment wrong

- **Status**: open
- **Affected**: all existing 9B8T outputs — inference results, any figures referencing 9B8T scores
- **Description**: Chain A in 9B8T = DNA pol epsilon. PCNA is chains B/C/D. All existing 9B8T scores are biologically meaningless.
- **Stale artifacts**: any 9B8T score files, any figure panel with 9B8T data
- **Fix**: regenerate inference with chains B/C/D

---

## Open Bugs

### BUG-002 / ISSUE-0002: Stale ANM outputs may carry wrong numbers

- **Status**: open (watch for cached reports)
- **Affected**: any ANM output before 2026-05-19
- **Description**: Old: holo=1.104, delta=+0.247, holo DCCM=0.078. Correct: holo=1.157, delta=+0.300, DCCM 0.0995→0.2093
- **Stale artifacts**: old reports, any paper draft section using old numbers
- **Fix applied**: `scripts/run_nma.py` and `data/results/nma_apo_holo_comparison.json` are correct

### BUG-004 / ISSUE-0004: T6 sanity test fails

- **Status**: open (accepted limitation)
- **Affected**: `tests/test_model_sanity.py`, test T6
- **Description**: Chain_id one-hot in node features breaks strict permutation equivariance
- **Impact on metrics**: None — held-out AUROC 0.8081 stands. Document as limitation.

---

## Resolved Bugs

### BUG-003: LIMITATIONS.md line 26 wrong (now fixed)

- **Status**: fixed 2026-05-19
- **Was**: "8GLA absent from all training data"
- **Correct**: 8GLA IS in PCNA fine-tuning; absent from held-out CryptoSite eval only
- **Fix applied**: `docs/LIMITATIONS.md` corrected in main repo

---

## Scientific Risks

| Risk | Severity | Mitigation |
|---|---|---|
| 100 ns MD may be too short for cryptic pocket opening | moderate | If no opening: use metadynamics / enhanced sampling |
| Single MD trajectory — limited conformational sampling | low | Acknowledge in paper limitations |
| Homology leakage between PCNA structures in split | low | 1W60 not in any split; 8GLA in fine-tuning only |
| Crystal contacts in 1W60 may mask accessible surface | low | Flag pocket candidates near crystal contacts |

---

## Artifacts Requiring Regeneration

| Artifact | Reason | Priority |
|---|---|---|
| All 9B8T inference outputs | Wrong chain assignment | High |
| Any report with ANM holo=1.104 | Stale ANM numbers | Medium (paper is already correct) |
