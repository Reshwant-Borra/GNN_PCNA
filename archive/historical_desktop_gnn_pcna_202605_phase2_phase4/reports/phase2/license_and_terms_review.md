# License And Terms Review

## Conservative Status

- Final status: `RAW_ASSETS_ACQUIRED_NOT_VERIFIED`
- Adoption status: `not_adopted`
- Quarantine status: `raw_unverified`
- Training, graph generation, split freeze, label freeze, evaluation, MD, and claims remain blocked.

## License And Terms

- `alphafold`: license status `LICENSE_UNRESOLVED`, terms URL `https://alphafold.ebi.ac.uk/entry/P12004`
- `asd`: license status `LICENSE_UNRESOLVED`, terms URL `https://mdl.shsmu.edu.cn/ASD/`
- `baseline_tools`: license status `LICENSE_UNRESOLVED`, terms URL `https://github.com/rdk/p2rank`
- `biogrid`: license status `LICENSE_UNRESOLVED`, terms URL `https://thebiogrid.org/`
- `biolip`: license status `LICENSE_UNRESOLVED`, terms URL `https://zhanggroup.org/BioLiP/qbiolip/`
- `cryptobench`: license status `LICENSE_KNOWN`, terms URL `https://osf.io/pz4a9/files/osfstorage/66c39eaa7f76e94ea65d9a85`
- `pcna_structures`: license status `LICENSE_KNOWN`, terms URL `https://www.rcsb.org/structure/1W60`
- `pocketminer`: license status `LICENSE_UNRESOLVED`, terms URL `https://github.com/Mickdub/gvp`
- `scpdb`: license status `LICENSE_UNRESOLVED`, terms URL `http://bioinfo-pharma.u-strasbg.fr/scPDB/`
- `string`: license status `LICENSE_UNRESOLVED`, terms URL `https://string-db.org/`

## Provenance

- Date: 2026-05-27T19:03:36-04:00
- Script/command used: `scripts/dataset_intake.py acquire --source alphafold --target P12004`
- Source paths inspected: `data/registries/download_manifest.jsonl`, `data/raw_intake/`, source adapter official URLs
- Confidence level: high for local manifest/report generation; uncertain for external source completeness until official audits finish
- Evidence status: verified for local files and manifest rows; inferred/uncertain for external source content not downloaded
- Python: `3.11.7`
- Unresolved questions: licenses, schemas, leakage, PCNA/homolog screening, label definitions, and human approvals remain unresolved

## Update Note

- Updated at: 2026-05-27T19:03:36-04:00
- Prior useful content was superseded by manifest-derived regenerated sections.
- Reason: governed dataset intake run/report regeneration.

