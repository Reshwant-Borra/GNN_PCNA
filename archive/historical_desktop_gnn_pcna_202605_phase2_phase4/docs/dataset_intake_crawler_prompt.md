# Dataset Intake Crawler Prompt

Before implementing the dataset intake crawler, tighten the crawler requirements with these additional safety rules:

1. No large bulk downloads without approval
Do not download any single file or archive over 500 MB, or any dataset totaling over 2 GB, without first recording:
- source name
- URL
- estimated size
- license/terms
- reason needed
- recommended action

Then stop and mark: HUMAN_APPROVAL_REQUIRED_FOR_BULK_DOWNLOAD.

2. Add required download manifest
Create:

data/registries/download_manifest.jsonl

Every attempted URL must create one JSONL row with:
- timestamp
- source_name
- target
- url
- local_path if downloaded
- action: downloaded | skipped | linked_only | failed
- HTTP status if available
- error if failed
- reason_skipped if skipped
- file_size_bytes if known
- sha256 if downloaded
- license_status
- schema_status
- trust_level
- notes

3. Quarantine all raw assets
All downloaded files must be treated as:

raw_unverified / quarantined

until license, schema, hash, and provenance checks pass.

Store raw assets under:

data/raw_intake/<source_name>/

Do not move them into canonical training/data folders.

4. License stop condition
If license or terms are missing, unclear, restrictive, or forbid redistribution:

- download metadata only if allowed
- do not download restricted bulk files
- mark asset as LICENSE_UNRESOLVED or RESTRICTED
- record official URL and terms page
- require human approval before further use

5. Official-source fallback policy
Use official sources first.

If official download fails:
- record the failure in download_manifest.jsonl
- record the official page URL
- do not use mirrors automatically

If a third-party mirror is discovered:
- mark it unverified_third_party
- link only unless human approval is given
- do not adopt it as canonical

6. PCNA contamination screening is first-pass only
During acquisition, only record whether screening is possible now.

For each dataset, mark:
- pcna_screening_status: not_started | simple_text_screen_possible | requires_schema_parse | requires_sequence_parse | requires_structure_parse
- homolog_screening_status: not_started | requires_sequence_parse | requires_structure_parse

Do not claim full contamination clearance during acquisition.

7. Reports must be provenance-aware
Every generated report must include:
- date
- script/command used
- source paths inspected
- confidence level
- evidence status: verified | inferred | uncertain | speculative
- unresolved questions

8. Do not mutate prior reports silently
If updating an existing report:
- preserve useful prior content
- add an update note with timestamp
- describe what changed and why

9. Schema status must be explicit
Use:
- SCHEMA_KNOWN
- SCHEMA_PARTIAL
- SCHEMA_UNKNOWN
- SCHEMA_UNREADABLE

Do not infer schema from filenames alone.

10. Final status must remain conservative
Expected final status after crawler acquisition is still:

RAW_ASSETS_ACQUIRED_NOT_VERIFIED

Do not mark:
- READY_FOR_TRAINING
- READY_FOR_SPLIT_FREEZE
- READY_FOR_LABEL_FREEZE

until later audits pass.

After adding these rules, implement the crawler/intake scripts and reports. is this prompt better now and if this prompt is better copy this exact prompt text and add it to a markdown file so you can read and do whatever it says later. Do not actually do what the prompt says now. Next tell me if building an agent like this is possible. Do not plan do not actually think of doing anything just tell me if it is possible to build and agent to do whatever the prompt asks. Finally also check this repo and see if we still have the context from the 400 sources we crawled previously and if that didnt get lost or accidently deleted.

## Approved Implementation Override

- Date: 2026-05-27
- Source path: user approval in Codex thread after the original prompt was saved
- Confidence level: high
- Evidence status: verified
- Decision: total dataset cap is 20 GB instead of the original 2 GB. The 500 MB single-file/archive approval gate remains in force. Unclear/restricted licenses still block download/adoption. Third-party mirrors remain linked-only unless approved. All files remain quarantined/raw_unverified. Intake must not mark anything ready for training, split freeze, or label freeze.
