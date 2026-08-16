# PCNA Specific Checks

## Purpose

Apply PCNA biology constraints to every Phase 2 prediction, validation, and claim.

## Hard Rules

- PCNA must be treated as a trimeric sliding clamp, not a generic monomer.
- Chain identity and residue mapping must be verified.
- Trimer interfaces must be respected.
- Known PIP-box and APIM interaction regions must be mapped.
- Known PCNA-targeting agents must be handled carefully.
- AOH1996/8GLA is a positive control, not proof of novel-site validity.
- ATX-101 must be framed according to evidence as an APIM-derived PCNA-targeting agent, not proof that every APIM/PIP-adjacent site is druggable.
- PCNA cancer relevance must not become a therapeutic overclaim.
- Predicted regions must be compared to known PCNA surfaces and interactions.

## Required Structural Mapping Checklist

- [ ] PDB ID, biological assembly, and asymmetric unit documented.
- [ ] PCNA chains identified and mapped to UniProt P12004 or declared species variant.
- [ ] Non-PCNA chains, DNA/RNA, ligands, ions, and waters identified.
- [ ] Residue numbering mapped to canonical PCNA numbering.
- [ ] Missing residues and insertion codes documented.
- [ ] PIP-box/APIM/IDCL region mapped.
- [ ] AOH1996/8GLA ZQZ contact region mapped if used.
- [ ] Trimer interface residues mapped.
- [ ] Predicted site overlap with known interfaces quantified.

## Known-Interface Comparison Table Template

| Prediction ID | Structure | Chain(s) | Residues | Overlap with PIP-box/APIM/IDCL | Overlap with AOH1996/8GLA region | Trimer-interface risk | Accessibility | Interpretation |
|---|---|---|---|---|---|---|---|---|
| PRED-001 |  |  |  |  |  |  |  |  |

## Allowed PCNA Claim Language

- "candidate PCNA cryptic pocket region"
- "computationally predicted PCNA surface region"
- "overlaps a known PCNA interaction interface"
- "positive-control recovery of the AOH1996/8GLA region"
- "hypothesis-generating site for follow-up"

## Forbidden PCNA Claim Language

- "validated PCNA drug target"
- "new therapeutic site"
- "confirmed resistance-proof pocket"
- "AOH1996 mechanism proven by the model"
- "ATX-101 proves this site is druggable"
- "PCNA cancer relevance proves clinical actionability"

## Forbidden Actions

- Ignoring biological assembly when interpreting trimer biology.
- Treating any PCNA chain as canonical without mapping.
- Calling overlap with PIP-box/APIM/IDCL a novel site without qualification.
- Using PCNA cancer relevance to imply treatment relevance.

## Required Checks

- PCNA trimer mapping audit.
- Known-interface overlap audit.
- AOH1996 positive-control status audit.
- ATX-101 evidence-framing audit.
- Claim-language audit.

## Examples Of Failure

- A predicted site is called novel but overlaps the known IDCL/PIP-box hydrophobic pocket.
- AOH1996 recovery is used to validate a novel site although 8GLA influenced training.
- Chain D in 8GLA is interpreted as equivalent to canonical chain C without mapping.

## Prevention

Run this file after [11_BIOLOGICAL_REALISM_RULES.md](11_BIOLOGICAL_REALISM_RULES.md) and before [13_MD_VALIDATION_RULES.md](13_MD_VALIDATION_RULES.md).

## Compliance Artifact

`reports/phase2/pcna_specific_audit.md`.

## If The Rule Fails

Do not claim PCNA novelty. Reclassify the site as known-interface overlap, mapping unresolved, or biologically implausible.
