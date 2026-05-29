# Claim Schema

## Claim Entry

```json
{
  "claim_id": "CLAIM-0001",
  "created_at": "",
  "updated_at": "",
  "created_by": "",
  "status": "hypothesis_generating",
  "claim_text": "",
  "plain_language_summary": "",
  "claim_strength": "proven_experimentally|strongly_supported_computationally|moderately_supported|suggestive|hypothesis_generating|unsupported|contradicted",
  "evidence_for": [],
  "evidence_against": [],
  "limitations": [],
  "required_evidence_to_strengthen": [],
  "allowed_wording": [],
  "disallowed_wording": [],
  "required_citations": [],
  "associated_artifacts": [],
  "associated_experiments": [],
  "associated_figures": [],
  "associated_paper_sections": [],
  "gate_status": {},
  "human_approval": {
    "required": false,
    "decision_id": "",
    "approval_status": "not_required|pending|approved|rejected|revised"
  },
  "notes": ""
}
```

## Claim Strength Rules

- `proven_experimentally`: direct experimental validation.
- `strongly_supported_computationally`: clean splits, strong baselines, independent metrics, validation, biological plausibility.
- `moderately_supported`: useful evidence with limitations.
- `suggestive`: promising but incomplete.
- `hypothesis_generating`: candidate only.
- `unsupported`: missing evidence.
- `contradicted`: evidence conflicts with claim.

## Example Safe Claim

```json
{
  "claim_id": "CLAIM-0001",
  "claim_text": "The GNN predicts a candidate pocket-associated residue region near AOH1996-associated residues.",
  "claim_strength": "hypothesis_generating",
  "evidence_for": ["known residue recovery", "structural proximity"],
  "evidence_against": ["MD under tested apo conditions did not show strong pocket opening"],
  "allowed_wording": ["candidate pocket-associated residue region", "computational candidate"],
  "disallowed_wording": ["validated cryptic pocket", "confirmed novel binding residues"]
}
```
