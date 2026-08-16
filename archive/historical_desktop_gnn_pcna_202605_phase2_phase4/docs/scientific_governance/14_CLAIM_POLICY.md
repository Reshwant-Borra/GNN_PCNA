# Claim Policy

## Purpose

Control wording so Phase 2 claims match evidence.

## Hard Rules

- No claim may appear in a report, figure, abstract, README, or presentation unless it passes claim audit.
- Claims must be scoped to the weakest required evidence gate.
- Computational evidence must stay computational unless experimental validation exists.

## Allowed Wording

- candidate cryptic pocket
- computationally predicted site
- hypothesis-generating result
- supportive MD evidence
- preliminary computational evidence
- requires experimental validation
- positive-control recovery
- same-split computational comparison

## Forbidden Wording Unless Experimentally Proven

- discovered therapeutic target
- validated binding site
- proven mechanism
- clinically actionable
- confirmed drug target
- cure claim
- treatment claim
- resistance-proof target
- druggable site, unless backed by appropriate ligandability evidence and framed cautiously

## Every Claim Must Include

- evidence source
- confidence level
- limitations
- verification status
- allowed figure/table support
- governing assumption IDs
- artifact hashes

## Claim Audit Checklist

- [ ] Does the claim cite evidence, not just model output?
- [ ] Is the dataset/split/label source clear?
- [ ] Was test used once?
- [ ] Are baselines present for performance claims?
- [ ] Is MD described as supportive only?
- [ ] Is PCNA trimer biology respected?
- [ ] Is AOH1996/8GLA framed as positive control when appropriate?
- [ ] Does the claim avoid clinical or therapeutic overreach?

## Overclaim Examples

| Overclaim | Corrected claim |
|---|---|
| "We discovered a new PCNA drug target." | "We identified a candidate PCNA pocket region for follow-up computational and experimental study." |
| "MD validated ligand binding." | "MD provided supportive evidence for local stability/accessibility under the tested setup." |
| "AOH1996 recovery proves the model finds novel PCNA pockets." | "AOH1996/8GLA recovery is a positive-control sanity check and does not validate novel-site predictions." |
| "PCNA expression in cancer makes this clinically actionable." | "PCNA cancer relevance motivates the target but does not establish clinical actionability." |

## Examples Of Failure

- A figure caption says "validated binding site" based only on GNN score and MD RMSF.
- A README says "drug target" because the site is near AOH1996.
- A report hides baseline failure but keeps superiority wording.

## Prevention

Run a claim audit before any external-facing text is finalized and downgrade language to allowed wording when evidence is preliminary.

## Forbidden Actions

- Writing claim-ready language before audits.
- Omitting limitations from figure captions.
- Treating high AUROC as mechanistic proof.
- Treating baseline defeat or failed MD as something to hide.

## Required Checks

- Claim-to-evidence trace.
- Claim-to-artifact trace.
- Forbidden-word scan.
- Human or critic-agent review.

## Compliance Artifact

`reports/phase2/claim_audit.md`.

## If The Rule Fails

Rewrite the claim or remove it. If a figure depends on the claim, downgrade the caption and conclusion.
