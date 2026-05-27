# CryptoBench Schema-First Audit

## Conservative Status

- Final status: `CRYPTOBENCH_READY_FOR_SCHEMA_AUDIT`
- Adoption status: `not_adopted`
- Quarantine status: `raw_unverified`
- Training, graph generation, split freeze, label freeze, evaluation, MD, and claims remain blocked.

## Scope

This audit inspects the top-level structure of acquired CryptoBench JSON files and the inventory of `cif-files.zip` only. It does not extract the archive into canonical data folders and does not validate labels, splits, leakage, PCNA contamination, or biological meaning.

## JSON Schema First Pass

### `data\raw_intake\cryptobench\metadata_files\66c328c87352852f68dbeac4_dataset.json`

- Size bytes: 8386019
- Top-level type: `dict`
- Top-level length: `1107`
- Top-level keys: `1a4u`, `1a8d`, `1ad1`, `1ak1`, `1arl`, `1ayl`, `1b0i`, `1bfn`, `1bhs`, `1bk2`, `1byi`, `1bzj`, `1c3k`, `1cuz`, `1cwq`, `1d7k`, `1dc6`, `1dkl`, `1dpj`, `1dq2`, `1dqz`, `1dte`, `1e3g`, `1e5l`, `1e6k`, `1ecc`, `1efh`, `1esw`, `1evy`, `1ezl`
- Sample nested structure:
  - `1a4u`: list len=13 first_item_keys=`uniprot_id`, `holo_pdb_id`, `holo_chain`, `apo_chain`, `ligand`, `ligand_index`, `ligand_chain`, `apo_pocket_selection`, `holo_pocket_selection`, `apo_pymol_selection`, `holo_pymol_selection`, `pRMSD`, `is_main_holo_structure`
  - `1a8d`: list len=1 first_item_keys=`uniprot_id`, `holo_pdb_id`, `holo_chain`, `apo_chain`, `ligand`, `ligand_index`, `ligand_chain`, `apo_pocket_selection`, `holo_pocket_selection`, `apo_pymol_selection`, `holo_pymol_selection`, `pRMSD`, `is_main_holo_structure`
  - `1ad1`: list len=2 first_item_keys=`uniprot_id`, `holo_pdb_id`, `holo_chain`, `apo_chain`, `ligand`, `ligand_index`, `ligand_chain`, `apo_pocket_selection`, `holo_pocket_selection`, `apo_pymol_selection`, `holo_pymol_selection`, `pRMSD`, `is_main_holo_structure`
  - `1ak1`: list len=1 first_item_keys=`uniprot_id`, `holo_pdb_id`, `holo_chain`, `apo_chain`, `ligand`, `ligand_index`, `ligand_chain`, `apo_pocket_selection`, `holo_pocket_selection`, `apo_pymol_selection`, `holo_pymol_selection`, `pRMSD`, `is_main_holo_structure`
  - `1arl`: list len=4 first_item_keys=`uniprot_id`, `holo_pdb_id`, `holo_chain`, `apo_chain`, `ligand`, `ligand_index`, `ligand_chain`, `apo_pocket_selection`, `holo_pocket_selection`, `apo_pymol_selection`, `holo_pymol_selection`, `pRMSD`, `is_main_holo_structure`

### `data\raw_intake\cryptobench\metadata_files\66c328d97352852f68dbead5_folds.json`

- Size bytes: 17826
- Top-level type: `dict`
- Top-level length: `5`
- Top-level keys: `test`, `train-0`, `train-1`, `train-2`, `train-3`
- Sample nested structure:
  - `test`: list len=222
  - `train-0`: list len=219
  - `train-1`: list len=222
  - `train-2`: list len=222
  - `train-3`: list len=222

### `data\raw_intake\cryptobench\labels_or_splits\66c328e138497880962d3054_test.json`

- Size bytes: 1705224
- Top-level type: `dict`
- Top-level length: `222`
- Top-level keys: `7qoq`, `4x19`, `8i84`, `5igh`, `7w19`, `5uxa`, `3h8a`, `6isu`, `5yhb`, `3rwv`, `2i3a`, `4oqo`, `3gdg`, `1kx9`, `1kxr`, `1ute`, `7f4y`, `7nlx`, `1se8`, `7xgf`, `5yj2`, `7e5q`, `5e0v`, `6jq9`, `7o1i`, `1fd4`, `3ly8`, `1bzj`, `7c63`, `7x0i`
- Sample nested structure:
  - `7qoq`: list len=1 first_item_keys=`uniprot_id`, `holo_pdb_id`, `holo_chain`, `apo_chain`, `ligand`, `ligand_index`, `ligand_chain`, `apo_pocket_selection`, `holo_pocket_selection`, `apo_pymol_selection`, `holo_pymol_selection`, `pRMSD`, `is_main_holo_structure`
  - `4x19`: list len=1 first_item_keys=`uniprot_id`, `holo_pdb_id`, `holo_chain`, `apo_chain`, `ligand`, `ligand_index`, `ligand_chain`, `apo_pocket_selection`, `holo_pocket_selection`, `apo_pymol_selection`, `holo_pymol_selection`, `pRMSD`, `is_main_holo_structure`
  - `8i84`: list len=3 first_item_keys=`uniprot_id`, `holo_pdb_id`, `holo_chain`, `apo_chain`, `ligand`, `ligand_index`, `ligand_chain`, `apo_pocket_selection`, `holo_pocket_selection`, `apo_pymol_selection`, `holo_pymol_selection`, `pRMSD`, `is_main_holo_structure`
  - `5igh`: list len=1 first_item_keys=`uniprot_id`, `holo_pdb_id`, `holo_chain`, `apo_chain`, `ligand`, `ligand_index`, `ligand_chain`, `apo_pocket_selection`, `holo_pocket_selection`, `apo_pymol_selection`, `holo_pymol_selection`, `pRMSD`, `is_main_holo_structure`
  - `7w19`: list len=1 first_item_keys=`uniprot_id`, `holo_pdb_id`, `holo_chain`, `apo_chain`, `ligand`, `ligand_index`, `ligand_chain`, `apo_pocket_selection`, `holo_pocket_selection`, `apo_pymol_selection`, `holo_pymol_selection`, `pRMSD`, `is_main_holo_structure`

### `data\raw_intake\cryptobench\labels_or_splits\66c328eba3530855975d9d19_train-fold-0.json`

- Size bytes: 1721723
- Top-level type: `dict`
- Top-level length: `219`
- Top-level keys: `1jpm`, `2yx7`, `2e1c`, `1qht`, `7jpi`, `6cjf`, `2w6r`, `5x6z`, `1nko`, `5cae`, `7dl7`, `1mac`, `4dmz`, `4gvr`, `6kx4`, `7p2t`, `4ok2`, `4ljp`, `5v49`, `7l8q`, `1g1o`, `4m23`, `7se6`, `4yt8`, `6j10`, `4brr`, `1vju`, `1nwh`, `5uzv`, `4fl8`
- Sample nested structure:
  - `1jpm`: list len=6 first_item_keys=`uniprot_id`, `holo_pdb_id`, `holo_chain`, `apo_chain`, `ligand`, `ligand_index`, `ligand_chain`, `apo_pocket_selection`, `holo_pocket_selection`, `apo_pymol_selection`, `holo_pymol_selection`, `pRMSD`, `is_main_holo_structure`
  - `2yx7`: list len=3 first_item_keys=`uniprot_id`, `holo_pdb_id`, `holo_chain`, `apo_chain`, `ligand`, `ligand_index`, `ligand_chain`, `apo_pocket_selection`, `holo_pocket_selection`, `apo_pymol_selection`, `holo_pymol_selection`, `pRMSD`, `is_main_holo_structure`
  - `2e1c`: list len=2 first_item_keys=`uniprot_id`, `holo_pdb_id`, `holo_chain`, `apo_chain`, `ligand`, `ligand_index`, `ligand_chain`, `apo_pocket_selection`, `holo_pocket_selection`, `apo_pymol_selection`, `holo_pymol_selection`, `pRMSD`, `is_main_holo_structure`
  - `1qht`: list len=2 first_item_keys=`uniprot_id`, `holo_pdb_id`, `holo_chain`, `apo_chain`, `ligand`, `ligand_index`, `ligand_chain`, `apo_pocket_selection`, `holo_pocket_selection`, `apo_pymol_selection`, `holo_pymol_selection`, `pRMSD`, `is_main_holo_structure`
  - `7jpi`: list len=4 first_item_keys=`uniprot_id`, `holo_pdb_id`, `holo_chain`, `apo_chain`, `ligand`, `ligand_index`, `ligand_chain`, `apo_pocket_selection`, `holo_pocket_selection`, `apo_pymol_selection`, `holo_pymol_selection`, `pRMSD`, `is_main_holo_structure`

### `data\raw_intake\cryptobench\labels_or_splits\66c328f5cb9874ed0d2d33b3_train-fold-1.json`

- Size bytes: 2130591
- Top-level type: `dict`
- Top-level length: `222`
- Top-level keys: `5iwi`, `8j1k`, `1k1x`, `3iun`, `7yx7`, `5hsi`, `4faf`, `6f4m`, `6pnt`, `1fwk`, `1p74`, `3bif`, `8h0n`, `1pfz`, `3pgs`, `1d7k`, `4ei8`, `7jrb`, `6up2`, `1xqz`, `3f0f`, `4omg`, `1g24`, `6czp`, `6aqe`, `6j35`, `8s32`, `5lqj`, `5ojx`, `1nxm`
- Sample nested structure:
  - `5iwi`: list len=1 first_item_keys=`uniprot_id`, `holo_pdb_id`, `holo_chain`, `apo_chain`, `ligand`, `ligand_index`, `ligand_chain`, `apo_pocket_selection`, `holo_pocket_selection`, `apo_pymol_selection`, `holo_pymol_selection`, `pRMSD`, `is_main_holo_structure`
  - `8j1k`: list len=1 first_item_keys=`uniprot_id`, `holo_pdb_id`, `holo_chain`, `apo_chain`, `ligand`, `ligand_index`, `ligand_chain`, `apo_pocket_selection`, `holo_pocket_selection`, `apo_pymol_selection`, `holo_pymol_selection`, `pRMSD`, `is_main_holo_structure`
  - `1k1x`: list len=2 first_item_keys=`uniprot_id`, `holo_pdb_id`, `holo_chain`, `apo_chain`, `ligand`, `ligand_index`, `ligand_chain`, `apo_pocket_selection`, `holo_pocket_selection`, `apo_pymol_selection`, `holo_pymol_selection`, `pRMSD`, `is_main_holo_structure`
  - `3iun`: list len=1 first_item_keys=`uniprot_id`, `holo_pdb_id`, `holo_chain`, `apo_chain`, `ligand`, `ligand_index`, `ligand_chain`, `apo_pocket_selection`, `holo_pocket_selection`, `apo_pymol_selection`, `holo_pymol_selection`, `pRMSD`, `is_main_holo_structure`
  - `7yx7`: list len=2 first_item_keys=`uniprot_id`, `holo_pdb_id`, `holo_chain`, `apo_chain`, `ligand`, `ligand_index`, `ligand_chain`, `apo_pocket_selection`, `holo_pocket_selection`, `apo_pymol_selection`, `holo_pymol_selection`, `pRMSD`, `is_main_holo_structure`

### `data\raw_intake\cryptobench\labels_or_splits\66c328fe653be15e240b528b_train-fold-2.json`

- Size bytes: 1738396
- Top-level type: `dict`
- Top-level length: `222`
- Top-level keys: `7ery`, `6llg`, `5v2k`, `7mbk`, `7rx7`, `8r43`, `6ezr`, `3ffe`, `1ayl`, `2hf0`, `5hke`, `2qsu`, `4yb7`, `7nte`, `5xvv`, `5ggs`, `1of3`, `4a6p`, `4zky`, `7poq`, `1a4u`, `3ssx`, `6tn3`, `4yaj`, `7ejw`, `7k4w`, `6tbt`, `4l6w`, `4twi`, `2ffy`
- Sample nested structure:
  - `7ery`: list len=5 first_item_keys=`uniprot_id`, `holo_pdb_id`, `holo_chain`, `apo_chain`, `ligand`, `ligand_index`, `ligand_chain`, `apo_pocket_selection`, `holo_pocket_selection`, `apo_pymol_selection`, `holo_pymol_selection`, `pRMSD`, `is_main_holo_structure`
  - `6llg`: list len=1 first_item_keys=`uniprot_id`, `holo_pdb_id`, `holo_chain`, `apo_chain`, `ligand`, `ligand_index`, `ligand_chain`, `apo_pocket_selection`, `holo_pocket_selection`, `apo_pymol_selection`, `holo_pymol_selection`, `pRMSD`, `is_main_holo_structure`
  - `5v2k`: list len=1 first_item_keys=`uniprot_id`, `holo_pdb_id`, `holo_chain`, `apo_chain`, `ligand`, `ligand_index`, `ligand_chain`, `apo_pocket_selection`, `holo_pocket_selection`, `apo_pymol_selection`, `holo_pymol_selection`, `pRMSD`, `is_main_holo_structure`
  - `7mbk`: list len=6 first_item_keys=`uniprot_id`, `holo_pdb_id`, `holo_chain`, `apo_chain`, `ligand`, `ligand_index`, `ligand_chain`, `apo_pocket_selection`, `holo_pocket_selection`, `apo_pymol_selection`, `holo_pymol_selection`, `pRMSD`, `is_main_holo_structure`
  - `7rx7`: list len=16 first_item_keys=`uniprot_id`, `holo_pdb_id`, `holo_chain`, `apo_chain`, `ligand`, `ligand_index`, `ligand_chain`, `apo_pocket_selection`, `holo_pocket_selection`, `apo_pymol_selection`, `holo_pymol_selection`, `pRMSD`, `is_main_holo_structure`

### `data\raw_intake\cryptobench\labels_or_splits\66c329087352852f68dbeaf4_train-fold-3.json`

- Size bytes: 1090093
- Top-level type: `dict`
- Top-level length: `222`
- Top-level keys: `6qpe`, `2dh4`, `5k3a`, `6l1i`, `7oap`, `2pry`, `2gzr`, `4i36`, `6pqz`, `1ak1`, `2x36`, `5gw7`, `7wmy`, `5hsm`, `4xmq`, `2y7a`, `5tqv`, `1tqd`, `4hc4`, `7piz`, `1gqn`, `2wvh`, `3ih2`, `8duf`, `3px7`, `8abu`, `8i7x`, `6pvg`, `4zxg`, `6rwd`
- Sample nested structure:
  - `6qpe`: list len=2 first_item_keys=`uniprot_id`, `holo_pdb_id`, `holo_chain`, `apo_chain`, `ligand`, `ligand_index`, `ligand_chain`, `apo_pocket_selection`, `holo_pocket_selection`, `apo_pymol_selection`, `holo_pymol_selection`, `pRMSD`, `is_main_holo_structure`
  - `2dh4`: list len=4 first_item_keys=`uniprot_id`, `holo_pdb_id`, `holo_chain`, `apo_chain`, `ligand`, `ligand_index`, `ligand_chain`, `apo_pocket_selection`, `holo_pocket_selection`, `apo_pymol_selection`, `holo_pymol_selection`, `pRMSD`, `is_main_holo_structure`
  - `5k3a`: list len=2 first_item_keys=`uniprot_id`, `holo_pdb_id`, `holo_chain`, `apo_chain`, `ligand`, `ligand_index`, `ligand_chain`, `apo_pocket_selection`, `holo_pocket_selection`, `apo_pymol_selection`, `holo_pymol_selection`, `pRMSD`, `is_main_holo_structure`
  - `6l1i`: list len=1 first_item_keys=`uniprot_id`, `holo_pdb_id`, `holo_chain`, `apo_chain`, `ligand`, `ligand_index`, `ligand_chain`, `apo_pocket_selection`, `holo_pocket_selection`, `apo_pymol_selection`, `holo_pymol_selection`, `pRMSD`, `is_main_holo_structure`
  - `7oap`: list len=2 first_item_keys=`uniprot_id`, `holo_pdb_id`, `holo_chain`, `apo_chain`, `ligand`, `ligand_index`, `ligand_chain`, `apo_pocket_selection`, `holo_pocket_selection`, `apo_pymol_selection`, `holo_pymol_selection`, `pRMSD`, `is_main_holo_structure`

### `data\raw_intake\cryptobench\labels_or_splits\66c32918467db4bc475da14e_noncryptic-pockets.json`

- Size bytes: 18879987
- Top-level type: `dict`
- Top-level length: `665`
- Top-level keys: `1a4u`, `1a8d`, `1ad1`, `1ak1`, `1arl`, `1b0i`, `1bhs`, `1byi`, `1bzj`, `1c3k`, `1cuz`, `1d7k`, `1dc6`, `1dkl`, `1dqz`, `1dte`, `1e3g`, `1ecc`, `1evy`, `1ezl`, `1f47`, `1f8a`, `1fd9`, `1fwk`, `1g0s`, `1g1m`, `1g1o`, `1g24`, `1g59`, `1gqn`
- Sample nested structure:
  - `1a4u`: list len=1 first_item_keys=`uniprot_id`, `holo_pdb_id`, `holo_chain`, `apo_chain`, `ligand`, `ligand_index`, `ligand_chain`, `apo_pocket_selection`, `holo_pocket_selection`, `apo_pymol_selection`, `holo_pymol_selection`
  - `1a8d`: list len=12 first_item_keys=`uniprot_id`, `holo_pdb_id`, `holo_chain`, `apo_chain`, `ligand`, `ligand_index`, `ligand_chain`, `apo_pocket_selection`, `holo_pocket_selection`, `apo_pymol_selection`, `holo_pymol_selection`
  - `1ad1`: list len=1 first_item_keys=`uniprot_id`, `holo_pdb_id`, `holo_chain`, `apo_chain`, `ligand`, `ligand_index`, `ligand_chain`, `apo_pocket_selection`, `holo_pocket_selection`, `apo_pymol_selection`, `holo_pymol_selection`
  - `1ak1`: list len=4 first_item_keys=`uniprot_id`, `holo_pdb_id`, `holo_chain`, `apo_chain`, `ligand`, `ligand_index`, `ligand_chain`, `apo_pocket_selection`, `holo_pocket_selection`, `apo_pymol_selection`, `holo_pymol_selection`
  - `1arl`: list len=23 first_item_keys=`uniprot_id`, `holo_pdb_id`, `holo_chain`, `apo_chain`, `ligand`, `ligand_index`, `ligand_chain`, `apo_pocket_selection`, `holo_pocket_selection`, `apo_pymol_selection`, `holo_pymol_selection`

## ZIP Inventory Only

- Path: `data\raw_intake\cryptobench\files\672a0171eae0bff252ba9ea3_cif-files.zip`
- Size bytes: 1145203712
- Can open safely with Python zipfile: `True`
- File count: 5005
- Directory count: 1
- Total uncompressed bytes: 4537113269
- Suffix counts: `.cif`=5005
- Top directories: `cif-files`=5006

### First ZIP Entries

- `cif-files/`
- `cif-files/1a4u.cif`
- `cif-files/1b14.cif`
- `cif-files/1b15.cif`
- `cif-files/1b16.cif`
- `cif-files/1b2l.cif`
- `cif-files/1sby.cif`
- `cif-files/3rj5.cif`
- `cif-files/3rj9.cif`
- `cif-files/1a8d.cif`
- `cif-files/1diw.cif`
- `cif-files/1ad1.cif`
- `cif-files/6clv.cif`
- `cif-files/1ak1.cif`
- `cif-files/2q2o.cif`
- `cif-files/1arl.cif`
- `cif-files/1bav.cif`
- `cif-files/2ctc.cif`
- `cif-files/3cpa.cif`
- `cif-files/3i1u.cif`
- `cif-files/1ayl.cif`
- `cif-files/6at3.cif`
- `cif-files/1b0i.cif`
- `cif-files/1g9h.cif`
- `cif-files/1bfn.cif`
- `cif-files/1byb.cif`
- `cif-files/1byc.cif`
- `cif-files/1byd.cif`
- `cif-files/1q6c.cif`
- `cif-files/1q6d.cif`
- `cif-files/1q6e.cif`
- `cif-files/1q6f.cif`
- `cif-files/1q6g.cif`
- `cif-files/1v3h.cif`
- `cif-files/1v3i.cif`
- `cif-files/1wdq.cif`
- `cif-files/1wdr.cif`
- `cif-files/1wds.cif`
- `cif-files/1bhs.cif`
- `cif-files/1a27.cif`

## Interpretation Limits

- JSON schema visibility is partial until a formal schema audit maps records to structures, labels, residues, chains, apo/holo pairs, and splits.
- ZIP inventory visibility confirms the archive can be listed, not that its structures are scientifically usable.
- PCNA/homolog contamination screening has not been completed.
- Leakage audits and human dataset/label/split review are still required.

## Provenance

- Date: 2026-05-27T17:55:19-04:00
- Script/command used: `python scripts/cryptobench_schema_first_audit.py`
- Source paths inspected: `data/raw_intake/cryptobench/metadata_files/`, `data/raw_intake/cryptobench/labels_or_splits/`, `data/raw_intake/cryptobench/files/672a0171eae0bff252ba9ea3_cif-files.zip`
- Confidence level: high for local file inventory and JSON/ZIP readability; uncertain for scientific usability.
- Evidence status: verified for local file structure; inferred for schema meaning; uncertain for labels/leakage/biological use.
- Unresolved questions: label semantics, residue mapping, chain mapping, apo/holo grouping, PCNA/homolog contamination, leakage, and human review.
