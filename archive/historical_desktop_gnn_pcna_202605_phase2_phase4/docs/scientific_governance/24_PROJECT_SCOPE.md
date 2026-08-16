# Project Scope

## Purpose

Define the scientific boundary of GNN-PCNA Phase 2 so the project does not drift into drug discovery, cancer therapy, clinical prediction, or therapeutic validation.

## Hard Rules

- Phase 2 is a computational structural biology project.
- The core task is residue-level prediction and auditing of PCNA candidate cryptic, allosteric, or pocket-like regions.
- The project may generate hypotheses for follow-up study.
- The project may not claim therapeutic validation, clinical actionability, treatment benefit, drug discovery success, or confirmed mechanism.
- PCNA cancer relevance is motivation only, not proof of druggability or clinical utility.
- AOH1996/8GLA and ATX-101 are context and controls, not proof that new predicted sites are valid targets.

## In Scope

- Dataset, split, label, graph, and provenance governance.
- Residue-level GNN and baseline comparison.
- PCNA structural mapping and known-interface comparison.
- Candidate-pocket ranking.
- Biological plausibility review.
- Exploratory MD interpretation under strict pre-registration.
- Honest negative or inconclusive result reporting.

## Out Of Scope

- Claiming a discovered therapeutic target.
- Claiming validated binding or mechanism without experiment.
- Clinical prediction or patient stratification.
- Cancer treatment claims.
- Wet-lab efficacy claims.
- Medicinal chemistry optimization claims.
- Docking-first drug discovery campaigns unless separately governed.

## Forbidden Actions

- Using survival, expression, or cancer relevance to imply clinical value of a predicted pocket.
- Describing GNN predictions as drug targets.
- Treating ligand docking, MD, or AOH1996 recovery as therapeutic validation.
- Expanding scope because a generated result looks exciting.

## Required Checks

- Scope check before implementation.
- Scope check before every claim audit.
- Scope check before external-facing figures, abstracts, README updates, or presentations.

## Examples Of Failure

- "This model discovered a new PCNA cancer therapy target."
- "The predicted site is clinically actionable because PCNA is overexpressed in tumors."
- "MD confirmed this site is druggable."

## Prevention

Use [14_CLAIM_POLICY.md](14_CLAIM_POLICY.md), [35_SCIENTIFIC_UNCERTAINTY_REGISTER.md](35_SCIENTIFIC_UNCERTAINTY_REGISTER.md), and this scope file together before writing claims.

## Compliance Artifact

`reports/phase2/project_scope_audit.md`.

## If The Rule Fails

Freeze the claim or artifact. Rewrite it within computational structural biology scope or remove it.
