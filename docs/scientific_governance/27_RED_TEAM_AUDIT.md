# Red Team Audit

## Purpose

Actively try to disprove the project before training, before claims, and before publication. The goal is to find explanations that make the GNN result less impressive or scientifically invalid.

## Hard Rules

- Red-team audit is required before first training and before preliminary claims.
- The red team must argue against the project, not defend it.
- A red-team finding cannot be dismissed without evidence.
- Any unresolved high-severity red-team issue blocks claims.

## Required Checks

- What if the model is learning graph size?
- What if labels correlate with ligand count, ligand size, or ligand chemistry?
- What if cryptic labels correlate with protein family or publication bias?
- What if PCNA predictions are just solvent accessibility?
- What if PCNA predictions are just conservation, B-factor, residue type, or geometric cavity score?
- What if AOH1996/8GLA biases architecture, thresholds, or expectations?
- What if chain ID or residue index explains PCNA performance?
- What if benchmark labels are noisy or inconsistent?
- What if MD behavior reflects force-field, protonation, ligand-parameter, or setup artifacts?
- What if the best scientific result is that the GNN adds no value over simple heuristics?

## Forbidden Actions

- Running red-team audit only after conclusions are written.
- Treating red-team questions as rhetorical.
- Omitting red-team failures from reports.
- Explaining away failed baselines or negative MD without evidence.

## Audit Template

| Attack | Evidence tested | Result | Severity | Required remediation |
|---|---|---|---|---|
| Graph-size shortcut |  |  |  |  |
| Ligand-count bias |  |  |  |  |
| Accessibility-only explanation |  |  |  |  |
| Benchmark noise |  |  |  |  |
| MD artifact |  |  |  |  |

## Examples Of Failure

- GNN beats random but not solvent-accessibility-only baseline.
- AOH1996 positive control passes only because chain ID is encoded.
- Test performance comes from a few related protein families.

## Prevention

Run red-team audit before expensive training and again before claims.

## Compliance Artifact

`reports/phase2/red_team_audit.md`.

## If The Rule Fails

Block training or claims depending on stage. Add remediation or downgrade the scientific claim.
