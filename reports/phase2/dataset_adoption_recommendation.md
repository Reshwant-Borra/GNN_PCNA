# Dataset Adoption Recommendation
_Generated: 2026-05-27T18:53:33Z_

> **Status: NOT_READY_FOR_SPLIT_FREEZE**
> None of the datasets below are cleared for training. Human review required for each.

## Tier 1 — HIGH priority, likely usable (pending schema audit)

| Dataset | Role | Blocker before adoption |
|---------|------|------------------------|
| CryptoBench | PRIMARY benchmark | Verify residue-level labels, splits, license |
| RCSB PDB (8GLA, 1W60, PCNA set) | Canonical structures | None — use as-is for structure reference |
| PocketMiner | Baseline method | Verify input/output schema, run locally |
| fpocket | Mandatory baseline | Install and test on 8GLA |
| P2Rank | Mandatory baseline | Install and test on 8GLA |

## Tier 2 — AUXILIARY (useful but not ground truth)

| Dataset | Role | Caveat |
|---------|------|--------|
| BioLiP | Auxiliary binding-residue supervision | NOT cryptic-pocket truth — ligand-contact only |
| scPDB | Druggable pocket context | Proxy labels only — druggable ≠ cryptic |
| AlphaFold (PCNA) | Predicted structure context | Predicted — pLDDT check required |
| BioGRID / STRING | PCNA interaction priors | Context only — not pocket labels |

## Tier 3 — DO NOT USE AS PRIMARY LABELS

| Dataset | Reason |
|---------|--------|
| ASD | License unknown; allosteric ≠ cryptic without schema validation |
| PDBbind | Registration required; affinity labels ≠ pocket labels |
| PDBbind full dataset | Potential leakage — use LP-PDBBind split methodology |

## Recommended canonical dataset for Phase 2

**CryptoBench** is the recommended primary benchmark IF:
1. Schema audit confirms residue-level cryptic-pocket labels
2. Apo/holo pairs are confirmed
3. Train/val/test splits are provided or derivable without leakage
4. PCNA or PCNA homologs are NOT in training set (held-out for final inference)
5. License is confirmed for academic use

**Until the above are confirmed**: status remains `NOT_READY_FOR_SPLIT_FREEZE`.

## Next required actions (human review)

- [ ] Open CryptoBench OSF node and read the README/dataset card
- [ ] Inspect CryptoBench label schema: what does a positive label mean exactly?
- [ ] Check whether PCNA appears in any split
- [ ] Verify BioLiP ligand-contact column definitions
- [ ] Install fpocket and run on 8GLA to verify output schema
- [ ] Install P2Rank and run on 8GLA to verify residue-level scores
- [ ] Hash-verify all downloaded files against official checksums if available
- [ ] Review all licenses with project PI before training adoption