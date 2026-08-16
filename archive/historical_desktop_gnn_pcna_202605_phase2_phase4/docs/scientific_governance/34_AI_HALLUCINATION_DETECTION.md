# AI Hallucination Detection

## Purpose

Prevent AI-generated scientific confidence from becoming project truth.

## Hard Rules

- Any AI-generated scientific explanation, biological rationale, metric interpretation, MD interpretation, literature claim, or claim wording must include a source reference or uncertainty marker.
- AI may summarize sources but may not create biological facts.
- Unsupported AI text must be treated as unverified.
- If no source is available, the statement must be marked as inference or uncertainty.

## Required Checks

- Source reference present for literature claims.
- Artifact reference present for metric, dataset, split, label, graph, MD, or figure claims.
- Uncertainty marker present when evidence is weak, missing, conflicting, or inferred.
- Claim-policy scan for forbidden language.
- Human review for claim-ready AI text.

## Forbidden Actions

- Copying AI biological rationale into docs without source review.
- Treating AI confidence as evidence.
- Letting a coding agent invent pocket definitions, PCNA mechanisms, or MD interpretations.
- Removing uncertainty markers to make the story cleaner.

## Examples Of Failure

- AI writes "PCNA site X is allosteric" without source or model evidence.
- AI explains an MD trajectory as ligand stabilization without contact analysis.
- AI says CryptoBench labels are experimental without checking benchmark documentation.

## Prevention

Make reports include a `source_or_uncertainty` field for AI-generated scientific statements.

## Compliance Artifact

`reports/phase2/ai_hallucination_audit.md`.

## If The Rule Fails

Mark the generated text `UNVERIFIED_AI_TEXT`, remove it from claims, and replace it with sourced or uncertainty-marked language.
