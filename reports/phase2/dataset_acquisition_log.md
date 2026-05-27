# Phase 2 Dataset Acquisition Log
_Generated: 2026-05-27T18:53:33Z_  |  _Status: RAW_ASSETS_ACQUIRED_NOT_VERIFIED_

## Summary
| Metric | Count |
|--------|-------|
| Files acquired (downloaded) | 94 |
| Sources linked only | 0 |
| Inaccessible | 1 |
| Total inventory entries | 95 |

## Acquired files

### CryptoBench OSF search page
- **URL**: https://osf.io/search/?q=CryptoBench
- **File**: `data\raw_intake\cryptobench\osf_search_page.html`
- **Size**: 4.2 KB
- **SHA-256**: `b822066d7d70e4af25ab91701580983fd38ae77401008bf5dd770eb50145332f`
- **Type**: HTML
- **Trust**: LINKED_ONLY
- **Role**: CryptoBench discovery
- **License**: UNKNOWN

### CryptoBench GitHub search results
- **URL**: https://api.github.com/search/repositories?q=CryptoBench+cryptic+pocket
- **File**: `data\raw_intake\cryptobench\github_search_cryptobench.json`
- **Size**: 72 B
- **SHA-256**: `53895997f5e07566d90a3f34b7fbb880fb1acf32d885aa31fbb268a6d7769d2a`
- **Type**: JSON
- **Trust**: OFFICIAL_API
- **Role**: CryptoBench repo discovery
- **License**: UNKNOWN

### RCSB PCNA full-text search results
- **URL**: https://search.rcsb.org/rcsbsearch/v2/query
- **File**: `data\raw_intake\rcsb_pdb\rcsb_pcna_search_results.json`
- **Size**: 4.1 KB
- **SHA-256**: `95ed9ca58c4a8cd2ce6ddf15ea132a38e9fe5e1ac087fb3fb3579df1358ba9c1`
- **Type**: JSON
- **Trust**: OFFICIAL_API
- **Role**: PCNA structure discovery
- **License**: Public Domain (PDB data policy)

### RCSB PDB 8GLA metadata
- **URL**: https://www.rcsb.org/structure/8GLA
- **File**: `data\raw_intake\pcna_structures\8GLA_metadata.json`
- **Size**: 19.7 KB
- **SHA-256**: `f5281ca8fad1055dfeaf32b9de3070dd87a9131577790a28250ef173f3f4dead`
- **Type**: JSON (RCSB REST API)
- **Trust**: OFFICIAL_API
- **Role**: positive-control (cryptic pocket ligand)
- **License**: Public Domain (wwPDB open access)

### RCSB PDB 8GLA mmCIF
- **URL**: https://files.rcsb.org/download/8GLA.cif
- **File**: `data\raw_intake\pcna_structures\8GLA.cif`
- **Size**: 826.0 KB
- **SHA-256**: `8c88e5ef1fe2df0403bcd2e56e5e626711949600bbcee6d51b749ffabb630bec`
- **Type**: mmCIF
- **Trust**: OFFICIAL_DOWNLOAD
- **Role**: PCNA positive-control structure
- **License**: Public Domain (wwPDB open access)

### RCSB PDB 1W60 metadata
- **URL**: https://www.rcsb.org/structure/1W60
- **File**: `data\raw_intake\pcna_structures\1W60_metadata.json`
- **Size**: 14.8 KB
- **SHA-256**: `58b5ebde62c0412880214d60ae499c225c331b75bf75bdb1dddcc4db1ae39924`
- **Type**: JSON (RCSB REST API)
- **Trust**: OFFICIAL_API
- **Role**: PCNA reference structure
- **License**: Public Domain (wwPDB open access)

### RCSB PDB 1W60 mmCIF
- **URL**: https://files.rcsb.org/download/1W60.cif
- **File**: `data\raw_intake\pcna_structures\1W60.cif`
- **Size**: 434.5 KB
- **SHA-256**: `bceb8eaede5fb7a356ef8b293aae75ef3f8cd3564b81c60c4f16827afcddf9a8`
- **Type**: mmCIF
- **Trust**: OFFICIAL_DOWNLOAD
- **Role**: PCNA reference structure
- **License**: Public Domain (wwPDB open access)

### RCSB PDB 1AXC metadata
- **URL**: https://www.rcsb.org/structure/1AXC
- **File**: `data\raw_intake\pcna_structures\1AXC_metadata.json`
- **Size**: 15.8 KB
- **SHA-256**: `40181cdc665d9d7ddab317e0d8ac96539b837d985f80626deb6b071626f3493f`
- **Type**: JSON (RCSB REST API)
- **Trust**: OFFICIAL_API
- **Role**: PCNA structure inventory
- **License**: Public Domain (wwPDB open access)

### RCSB PDB 1AXC mmCIF
- **URL**: https://files.rcsb.org/download/1AXC.cif
- **File**: `data\raw_intake\pcna_structures\1AXC.cif`
- **Size**: 853.7 KB
- **SHA-256**: `f9472769dcbceec05533fa1a85e617dd50e2dde66f2c9f6554d52a2ecc1ec135`
- **Type**: mmCIF
- **Trust**: OFFICIAL_DOWNLOAD
- **Role**: PCNA reference structure
- **License**: Public Domain (wwPDB open access)

### RCSB PDB 1W63 metadata
- **URL**: https://www.rcsb.org/structure/1W63
- **File**: `data\raw_intake\pcna_structures\1W63_metadata.json`
- **Size**: 18.8 KB
- **SHA-256**: `53ee4a1ddfa938e31766bf9bb994fba7d3cd91c10a53d1ef567974e67287719a`
- **Type**: JSON (RCSB REST API)
- **Trust**: OFFICIAL_API
- **Role**: PCNA structure inventory
- **License**: Public Domain (wwPDB open access)

### RCSB PDB 1W63 mmCIF
- **URL**: https://files.rcsb.org/download/1W63.cif
- **File**: `data\raw_intake\pcna_structures\1W63.cif`
- **Size**: 7.98 MB
- **SHA-256**: `589a2a1e36ae13268d6551ea9b475aeb3a18cceab77a47238fe2ff8e7089a09b`
- **Type**: mmCIF
- **Trust**: OFFICIAL_DOWNLOAD
- **Role**: PCNA reference structure
- **License**: Public Domain (wwPDB open access)

### RCSB PDB 3JAB metadata
- **URL**: https://www.rcsb.org/structure/3JAB
- **File**: `data\raw_intake\pcna_structures\3JAB_metadata.json`
- **Size**: 17.8 KB
- **SHA-256**: `6681eada583adfc1699a1ea60463342811aa0eb36a0c29e2ab90a8b30e7aa508`
- **Type**: JSON (RCSB REST API)
- **Trust**: OFFICIAL_API
- **Role**: PCNA structure inventory
- **License**: Public Domain (wwPDB open access)

### RCSB PDB 3JAB mmCIF
- **URL**: https://files.rcsb.org/download/3JAB.cif
- **File**: `data\raw_intake\pcna_structures\3JAB.cif`
- **Size**: 1.80 MB
- **SHA-256**: `ff031a497ddc10992f40a658ab9e78ba5b5c243d5ccd9b7627876bbd65a6b9d5`
- **Type**: mmCIF
- **Trust**: OFFICIAL_DOWNLOAD
- **Role**: PCNA reference structure
- **License**: Public Domain (wwPDB open access)

### RCSB PDB 6GIS metadata
- **URL**: https://www.rcsb.org/structure/6GIS
- **File**: `data\raw_intake\pcna_structures\6GIS_metadata.json`
- **Size**: 30.4 KB
- **SHA-256**: `07759ecbce59147a1b2483b71d3e3d36669e7dd104bc53347c485c344e9e7db5`
- **Type**: JSON (RCSB REST API)
- **Trust**: OFFICIAL_API
- **Role**: PCNA structure inventory
- **License**: Public Domain (wwPDB open access)

### RCSB PDB 6GIS mmCIF
- **URL**: https://files.rcsb.org/download/6GIS.cif
- **File**: `data\raw_intake\pcna_structures\6GIS.cif`
- **Size**: 1.20 MB
- **SHA-256**: `11abcc8d33f474a8eb01574d2480e3b1aebc2a93ddff78632f89d6b8ee7ebe35`
- **Type**: mmCIF
- **Trust**: OFFICIAL_DOWNLOAD
- **Role**: PCNA reference structure
- **License**: Public Domain (wwPDB open access)

### RCSB PDB 1VYJ metadata
- **URL**: https://www.rcsb.org/structure/1VYJ
- **File**: `data\raw_intake\pcna_structures\1VYJ_metadata.json`
- **Size**: 17.7 KB
- **SHA-256**: `324496643c428ec5fda3e9a04a628bde80b737607fa0120e98e362883543576f`
- **Type**: JSON (RCSB REST API)
- **Trust**: OFFICIAL_API
- **Role**: PCNA structure inventory
- **License**: Public Domain (wwPDB open access)

### RCSB PDB 1VYJ mmCIF
- **URL**: https://files.rcsb.org/download/1VYJ.cif
- **File**: `data\raw_intake\pcna_structures\1VYJ.cif`
- **Size**: 1.35 MB
- **SHA-256**: `77c759a0a0998e31b1456b9315e4d6cf04949d556bebb4584b9cf42d50878555`
- **Type**: mmCIF
- **Trust**: OFFICIAL_DOWNLOAD
- **Role**: PCNA reference structure
- **License**: Public Domain (wwPDB open access)

### RCSB PDB 1UL1 metadata
- **URL**: https://www.rcsb.org/structure/1UL1
- **File**: `data\raw_intake\pcna_structures\1UL1_metadata.json`
- **Size**: 19.7 KB
- **SHA-256**: `56806b028947bce8dab039cfeaf9ec3f038c9b4250e8381d494ef3d467871fbe`
- **Type**: JSON (RCSB REST API)
- **Trust**: OFFICIAL_API
- **Role**: PCNA structure inventory
- **License**: Public Domain (wwPDB open access)

### RCSB PDB 1UL1 mmCIF
- **URL**: https://files.rcsb.org/download/1UL1.cif
- **File**: `data\raw_intake\pcna_structures\1UL1.cif`
- **Size**: 1.40 MB
- **SHA-256**: `7f11d6c7d5b8135108d143ab07c2412075914e45bcc75427cbda68d7c695a3a9`
- **Type**: mmCIF
- **Trust**: OFFICIAL_DOWNLOAD
- **Role**: PCNA reference structure
- **License**: Public Domain (wwPDB open access)

### RCSB PDB 2ZVK metadata
- **URL**: https://www.rcsb.org/structure/2ZVK
- **File**: `data\raw_intake\pcna_structures\2ZVK_metadata.json`
- **Size**: 21.2 KB
- **SHA-256**: `625873bf1df0a438a50138d982df311d78d30433ab4854286a81c04bf6a311ae`
- **Type**: JSON (RCSB REST API)
- **Trust**: OFFICIAL_API
- **Role**: PCNA structure inventory
- **License**: Public Domain (wwPDB open access)

### RCSB PDB 2ZVK mmCIF
- **URL**: https://files.rcsb.org/download/2ZVK.cif
- **File**: `data\raw_intake\pcna_structures\2ZVK.cif`
- **Size**: 636.9 KB
- **SHA-256**: `a071a7609090c7227c60cae39b90c197aaa8dbe07b9c54dc454ca54f8fdb9e76`
- **Type**: mmCIF
- **Trust**: OFFICIAL_DOWNLOAD
- **Role**: PCNA reference structure
- **License**: Public Domain (wwPDB open access)

### RCSB PDB 4D2G metadata
- **URL**: https://www.rcsb.org/structure/4D2G
- **File**: `data\raw_intake\pcna_structures\4D2G_metadata.json`
- **Size**: 16.6 KB
- **SHA-256**: `a194808a7c12469260ef2fb3d1294e2c7869d19e571718cce16c7ce0920bd032`
- **Type**: JSON (RCSB REST API)
- **Trust**: OFFICIAL_API
- **Role**: PCNA structure inventory
- **License**: Public Domain (wwPDB open access)

### RCSB PDB 4D2G mmCIF
- **URL**: https://files.rcsb.org/download/4D2G.cif
- **File**: `data\raw_intake\pcna_structures\4D2G.cif`
- **Size**: 1.26 MB
- **SHA-256**: `0405ce41ced9ab78d964bd8d5e716eda901d19430e8cbff2042174ac61488c20`
- **Type**: mmCIF
- **Trust**: OFFICIAL_DOWNLOAD
- **Role**: PCNA reference structure
- **License**: Public Domain (wwPDB open access)

### RCSB PDB 2HIK metadata
- **URL**: https://www.rcsb.org/structure/2HIK
- **File**: `data\raw_intake\rcsb_pdb\2HIK_metadata.json`
- **Size**: 22.9 KB
- **SHA-256**: `2214c30b751b70a94fb17e4442a3428babb4a292c39dfacabb441ccbc05f495d`
- **Type**: JSON (RCSB REST API)
- **Trust**: OFFICIAL_API
- **Role**: PCNA structure inventory
- **License**: Public Domain (wwPDB open access)

### RCSB PDB 2HIK mmCIF
- **URL**: https://files.rcsb.org/download/2HIK.cif
- **File**: `data\raw_intake\rcsb_pdb\2HIK.cif`
- **Size**: 1.78 MB
- **SHA-256**: `2190e9f9e0940575619273e9f345c97d64394eedba00de4f6962be288df6c667`
- **Type**: mmCIF
- **Trust**: OFFICIAL_DOWNLOAD
- **Role**: PCNA reference structure
- **License**: Public Domain (wwPDB open access)

### RCSB PDB 2HII metadata
- **URL**: https://www.rcsb.org/structure/2HII
- **File**: `data\raw_intake\rcsb_pdb\2HII_metadata.json`
- **Size**: 23.4 KB
- **SHA-256**: `c3f86d3b65e60ef51fdd6632b146d627c94ccb1e798aff4f7a5223d5185af65d`
- **Type**: JSON (RCSB REST API)
- **Trust**: OFFICIAL_API
- **Role**: PCNA structure inventory
- **License**: Public Domain (wwPDB open access)

### RCSB PDB 2HII mmCIF
- **URL**: https://files.rcsb.org/download/2HII.cif
- **File**: `data\raw_intake\rcsb_pdb\2HII.cif`
- **Size**: 1.21 MB
- **SHA-256**: `52e93986c92a0a2a16982d66a79b80c994423fc6681f6c95b9523bb97bcd805a`
- **Type**: mmCIF
- **Trust**: OFFICIAL_DOWNLOAD
- **Role**: PCNA reference structure
- **License**: Public Domain (wwPDB open access)

### RCSB PDB 2NTI metadata
- **URL**: https://www.rcsb.org/structure/2NTI
- **File**: `data\raw_intake\rcsb_pdb\2NTI_metadata.json`
- **Size**: 19.9 KB
- **SHA-256**: `1c69e8eb8861673c188942af135f41f6537350cc20eb17cbb40866e92f191e08`
- **Type**: JSON (RCSB REST API)
- **Trust**: OFFICIAL_API
- **Role**: PCNA structure inventory
- **License**: Public Domain (wwPDB open access)

### RCSB PDB 2NTI mmCIF
- **URL**: https://files.rcsb.org/download/2NTI.cif
- **File**: `data\raw_intake\rcsb_pdb\2NTI.cif`
- **Size**: 1.96 MB
- **SHA-256**: `dc21b9ed81dd97a18621bd532f650c8e3ea492cfd98d2e83387db76d4babf930`
- **Type**: mmCIF
- **Trust**: OFFICIAL_DOWNLOAD
- **Role**: PCNA reference structure
- **License**: Public Domain (wwPDB open access)

### RCSB PDB 3IFV metadata
- **URL**: https://www.rcsb.org/structure/3IFV
- **File**: `data\raw_intake\rcsb_pdb\3IFV_metadata.json`
- **Size**: 23.5 KB
- **SHA-256**: `5bc17143765a15199e02f6410f70f9ecedd31088b11bad2626d8ab9e204de01d`
- **Type**: JSON (RCSB REST API)
- **Trust**: OFFICIAL_API
- **Role**: PCNA structure inventory
- **License**: Public Domain (wwPDB open access)

### RCSB PDB 3IFV mmCIF
- **URL**: https://files.rcsb.org/download/3IFV.cif
- **File**: `data\raw_intake\rcsb_pdb\3IFV.cif`
- **Size**: 617.3 KB
- **SHA-256**: `fbc10313be1b8f7e49b73d737995fd52e7b5c9f72cb78de171708b9a036cf79d`
- **Type**: mmCIF
- **Trust**: OFFICIAL_DOWNLOAD
- **Role**: PCNA reference structure
- **License**: Public Domain (wwPDB open access)

### RCSB PDB 3HI8 metadata
- **URL**: https://www.rcsb.org/structure/3HI8
- **File**: `data\raw_intake\rcsb_pdb\3HI8_metadata.json`
- **Size**: 17.8 KB
- **SHA-256**: `b7b5cf723a679c0246778247d821813dabf5e613436ec2fa6e2316714fb379a6`
- **Type**: JSON (RCSB REST API)
- **Trust**: OFFICIAL_API
- **Role**: PCNA structure inventory
- **License**: Public Domain (wwPDB open access)

### RCSB PDB 3HI8 mmCIF
- **URL**: https://files.rcsb.org/download/3HI8.cif
- **File**: `data\raw_intake\rcsb_pdb\3HI8.cif`
- **Size**: 1.15 MB
- **SHA-256**: `1786225b5854205208427bbc8bc55f373c057faf3e22ad3b543fed82856dbf0c`
- **Type**: mmCIF
- **Trust**: OFFICIAL_DOWNLOAD
- **Role**: PCNA reference structure
- **License**: Public Domain (wwPDB open access)

### RCSB PDB 2IX2 metadata
- **URL**: https://www.rcsb.org/structure/2IX2
- **File**: `data\raw_intake\rcsb_pdb\2IX2_metadata.json`
- **Size**: 20.9 KB
- **SHA-256**: `6de68641b3f26a47a0c044f81a43ecdc808acb8f8e8f1b56c2c5de741a0f68c1`
- **Type**: JSON (RCSB REST API)
- **Trust**: OFFICIAL_API
- **Role**: PCNA structure inventory
- **License**: Public Domain (wwPDB open access)

### RCSB PDB 2IX2 mmCIF
- **URL**: https://files.rcsb.org/download/2IX2.cif
- **File**: `data\raw_intake\rcsb_pdb\2IX2.cif`
- **Size**: 618.2 KB
- **SHA-256**: `369f3310ac09d25e19560c477cc6ab65ba446baf6d23fe8b5a62d26c4a257779`
- **Type**: mmCIF
- **Trust**: OFFICIAL_DOWNLOAD
- **Role**: PCNA reference structure
- **License**: Public Domain (wwPDB open access)

### RCSB PDB 5AUJ metadata
- **URL**: https://www.rcsb.org/structure/5AUJ
- **File**: `data\raw_intake\rcsb_pdb\5AUJ_metadata.json`
- **Size**: 15.0 KB
- **SHA-256**: `5d120ebe50fd5b497838e4bf2b051aab347b65638fe74e4c14e757e525a3dd4e`
- **Type**: JSON (RCSB REST API)
- **Trust**: OFFICIAL_API
- **Role**: PCNA structure inventory
- **License**: Public Domain (wwPDB open access)

### RCSB PDB 5AUJ mmCIF
- **URL**: https://files.rcsb.org/download/5AUJ.cif
- **File**: `data\raw_intake\rcsb_pdb\5AUJ.cif`
- **Size**: 243.4 KB
- **SHA-256**: `2be984c311029198e8a537b7f2028f072872c1656e82e0f72e56787700e47dfb`
- **Type**: mmCIF
- **Trust**: OFFICIAL_DOWNLOAD
- **Role**: PCNA reference structure
- **License**: Public Domain (wwPDB open access)

### RCSB PDB 5A6D metadata
- **URL**: https://www.rcsb.org/structure/5A6D
- **File**: `data\raw_intake\rcsb_pdb\5A6D_metadata.json`
- **Size**: 16.7 KB
- **SHA-256**: `5e6d1a3b61ed9a1311a36366f64f30ce3b95c2f2a117cb8e1a07a4cf5157f013`
- **Type**: JSON (RCSB REST API)
- **Trust**: OFFICIAL_API
- **Role**: PCNA structure inventory
- **License**: Public Domain (wwPDB open access)

### RCSB PDB 5A6D mmCIF
- **URL**: https://files.rcsb.org/download/5A6D.cif
- **File**: `data\raw_intake\rcsb_pdb\5A6D.cif`
- **Size**: 411.6 KB
- **SHA-256**: `868cc56e80c5ff0ecd71e22df221e2dcb049d5b336270fb5b8bb14423b349de0`
- **Type**: mmCIF
- **Trust**: OFFICIAL_DOWNLOAD
- **Role**: PCNA reference structure
- **License**: Public Domain (wwPDB open access)

### RCSB PDB 1RWZ metadata
- **URL**: https://www.rcsb.org/structure/1RWZ
- **File**: `data\raw_intake\rcsb_pdb\1RWZ_metadata.json`
- **Size**: 15.9 KB
- **SHA-256**: `845e0f6620951fec323412599510e421972f6ea13c5f559627a9914c7254df64`
- **Type**: JSON (RCSB REST API)
- **Trust**: OFFICIAL_API
- **Role**: PCNA structure inventory
- **License**: Public Domain (wwPDB open access)

### RCSB PDB 1RWZ mmCIF
- **URL**: https://files.rcsb.org/download/1RWZ.cif
- **File**: `data\raw_intake\rcsb_pdb\1RWZ.cif`
- **Size**: 271.5 KB
- **SHA-256**: `4bbe7970efd7ed105dfa88c3f27d5e1425343506bbbfe95fd685bdde56fe6e76`
- **Type**: mmCIF
- **Trust**: OFFICIAL_DOWNLOAD
- **Role**: PCNA reference structure
- **License**: Public Domain (wwPDB open access)

### RCSB PDB 1IZ5 metadata
- **URL**: https://www.rcsb.org/structure/1IZ5
- **File**: `data\raw_intake\rcsb_pdb\1IZ5_metadata.json`
- **Size**: 16.6 KB
- **SHA-256**: `7568e1352246e2daa73625f4d4f687a1d9e85da3c676aa05cd8133821169bf6a`
- **Type**: JSON (RCSB REST API)
- **Trust**: OFFICIAL_API
- **Role**: PCNA structure inventory
- **License**: Public Domain (wwPDB open access)

### RCSB PDB 1IZ5 mmCIF
- **URL**: https://files.rcsb.org/download/1IZ5.cif
- **File**: `data\raw_intake\rcsb_pdb\1IZ5.cif`
- **Size**: 421.9 KB
- **SHA-256**: `8a26f060f9eed206108cd585fa5c8bd760ec2fa0ce8caa8dfb174cf9b64be0cc`
- **Type**: mmCIF
- **Trust**: OFFICIAL_DOWNLOAD
- **Role**: PCNA reference structure
- **License**: Public Domain (wwPDB open access)

### RCSB PDB 1GE8 metadata
- **URL**: https://www.rcsb.org/structure/1GE8
- **File**: `data\raw_intake\rcsb_pdb\1GE8_metadata.json`
- **Size**: 17.0 KB
- **SHA-256**: `77982a1999494041afc16e20c6e08dcdad8aa44c30f10360025fe57ef02f23c9`
- **Type**: JSON (RCSB REST API)
- **Trust**: OFFICIAL_API
- **Role**: PCNA structure inventory
- **License**: Public Domain (wwPDB open access)

### RCSB PDB 1GE8 mmCIF
- **URL**: https://files.rcsb.org/download/1GE8.cif
- **File**: `data\raw_intake\rcsb_pdb\1GE8.cif`
- **Size**: 231.4 KB
- **SHA-256**: `57c6fb10840e4ee18ab4460248383a8dfb52f6be4b248603ea828b8eb6f9abc0`
- **Type**: mmCIF
- **Trust**: OFFICIAL_DOWNLOAD
- **Role**: PCNA reference structure
- **License**: Public Domain (wwPDB open access)

### RCSB PDB 1UD9 metadata
- **URL**: https://www.rcsb.org/structure/1UD9
- **File**: `data\raw_intake\rcsb_pdb\1UD9_metadata.json`
- **Size**: 21.6 KB
- **SHA-256**: `41b99eba25b04e98e33f410ad46aec51c8c23896c54c65536a8c5a44ed8d478d`
- **Type**: JSON (RCSB REST API)
- **Trust**: OFFICIAL_API
- **Role**: PCNA structure inventory
- **License**: Public Domain (wwPDB open access)

### RCSB PDB 1UD9 mmCIF
- **URL**: https://files.rcsb.org/download/1UD9.cif
- **File**: `data\raw_intake\rcsb_pdb\1UD9.cif`
- **Size**: 885.2 KB
- **SHA-256**: `d15434fab6317218f808bf24fccb45db3cd9f2227352e043f3d3244799fdc506`
- **Type**: mmCIF
- **Trust**: OFFICIAL_DOWNLOAD
- **Role**: PCNA reference structure
- **License**: Public Domain (wwPDB open access)

### RCSB PDB 5DA7 metadata
- **URL**: https://www.rcsb.org/structure/5DA7
- **File**: `data\raw_intake\rcsb_pdb\5DA7_metadata.json`
- **Size**: 16.1 KB
- **SHA-256**: `23d50f3ceb2fbbf3eb053b6a6cad0aace391177057e2b66e47b13deec98d38e2`
- **Type**: JSON (RCSB REST API)
- **Trust**: OFFICIAL_API
- **Role**: PCNA structure inventory
- **License**: Public Domain (wwPDB open access)

### RCSB PDB 5DA7 mmCIF
- **URL**: https://files.rcsb.org/download/5DA7.cif
- **File**: `data\raw_intake\rcsb_pdb\5DA7.cif`
- **Size**: 511.7 KB
- **SHA-256**: `1e6b9021bc82d9826f5b0a7c586c6bf0f1302e8136c851ef75f7b7b7f719b9fd`
- **Type**: mmCIF
- **Trust**: OFFICIAL_DOWNLOAD
- **Role**: PCNA reference structure
- **License**: Public Domain (wwPDB open access)

### RCSB PDB 5HAC metadata
- **URL**: https://www.rcsb.org/structure/5HAC
- **File**: `data\raw_intake\rcsb_pdb\5HAC_metadata.json`
- **Size**: 21.6 KB
- **SHA-256**: `54fd4eaa3910cba63e1acd2051fa81ffe355ea8fff9a88e3fbad1fe7bd65673e`
- **Type**: JSON (RCSB REST API)
- **Trust**: OFFICIAL_API
- **Role**: PCNA structure inventory
- **License**: Public Domain (wwPDB open access)

### RCSB PDB 5HAC mmCIF
- **URL**: https://files.rcsb.org/download/5HAC.cif
- **File**: `data\raw_intake\rcsb_pdb\5HAC.cif`
- **Size**: 1.27 MB
- **SHA-256**: `41b7148134a6ec6b82cae2a7b622e05d2f535957391bac1e7ae0c421547f3dd4`
- **Type**: mmCIF
- **Trust**: OFFICIAL_DOWNLOAD
- **Role**: PCNA reference structure
- **License**: Public Domain (wwPDB open access)

### RCSB PDB 1IZ4 metadata
- **URL**: https://www.rcsb.org/structure/1IZ4
- **File**: `data\raw_intake\rcsb_pdb\1IZ4_metadata.json`
- **Size**: 17.3 KB
- **SHA-256**: `549bfe1a26b859ec01314b83264d8b4cfb0a6fc3c87e0b243f8f83d5af54f368`
- **Type**: JSON (RCSB REST API)
- **Trust**: OFFICIAL_API
- **Role**: PCNA structure inventory
- **License**: Public Domain (wwPDB open access)

### RCSB PDB 1IZ4 mmCIF
- **URL**: https://files.rcsb.org/download/1IZ4.cif
- **File**: `data\raw_intake\rcsb_pdb\1IZ4.cif`
- **Size**: 231.4 KB
- **SHA-256**: `e14dd1763bed723e60ad42866e9235ea3b5939bcbec21d65c3b5badb460e5c6c`
- **Type**: mmCIF
- **Trust**: OFFICIAL_DOWNLOAD
- **Role**: PCNA reference structure
- **License**: Public Domain (wwPDB open access)

### RCSB PDB 2IO4 metadata
- **URL**: https://www.rcsb.org/structure/2IO4
- **File**: `data\raw_intake\rcsb_pdb\2IO4_metadata.json`
- **Size**: 25.7 KB
- **SHA-256**: `51b9da410fd5973ab8ab7513ad9a360dad73cd176d3ff7800e18c484bb486369`
- **Type**: JSON (RCSB REST API)
- **Trust**: OFFICIAL_API
- **Role**: PCNA structure inventory
- **License**: Public Domain (wwPDB open access)

### RCSB PDB 2IO4 mmCIF
- **URL**: https://files.rcsb.org/download/2IO4.cif
- **File**: `data\raw_intake\rcsb_pdb\2IO4.cif`
- **Size**: 843.8 KB
- **SHA-256**: `3c36e22368115985e74ff36c5d7b12b19ca2c31d803eee98548786772eab120e`
- **Type**: mmCIF
- **Trust**: OFFICIAL_DOWNLOAD
- **Role**: PCNA reference structure
- **License**: Public Domain (wwPDB open access)

### RCSB PDB 1RXM metadata
- **URL**: https://www.rcsb.org/structure/1RXM
- **File**: `data\raw_intake\rcsb_pdb\1RXM_metadata.json`
- **Size**: 15.6 KB
- **SHA-256**: `4ac7c572669af7ce6c3db750309ad677cae86c1e9f3f8e9851227ee4647147ff`
- **Type**: JSON (RCSB REST API)
- **Trust**: OFFICIAL_API
- **Role**: PCNA structure inventory
- **License**: Public Domain (wwPDB open access)

### RCSB PDB 1RXM mmCIF
- **URL**: https://files.rcsb.org/download/1RXM.cif
- **File**: `data\raw_intake\rcsb_pdb\1RXM.cif`
- **Size**: 245.6 KB
- **SHA-256**: `247763eab40e1882f4a335339fbc49955ad481b8364f072e83752600ff14cb0d`
- **Type**: mmCIF
- **Trust**: OFFICIAL_DOWNLOAD
- **Role**: PCNA reference structure
- **License**: Public Domain (wwPDB open access)

### RCSB PDB 2IJX metadata
- **URL**: https://www.rcsb.org/structure/2IJX
- **File**: `data\raw_intake\rcsb_pdb\2IJX_metadata.json`
- **Size**: 22.5 KB
- **SHA-256**: `a961a6aae6c772e8cdd9a6f1e5d363e91abc111f9ad0c5afbd4cad933481c107`
- **Type**: JSON (RCSB REST API)
- **Trust**: OFFICIAL_API
- **Role**: PCNA structure inventory
- **License**: Public Domain (wwPDB open access)

### RCSB PDB 2IJX mmCIF
- **URL**: https://files.rcsb.org/download/2IJX.cif
- **File**: `data\raw_intake\rcsb_pdb\2IJX.cif`
- **Size**: 907.2 KB
- **SHA-256**: `df8819dd9a833954188ac77d056593d0b8cf11098a082baccd67a6286a04ccef`
- **Type**: mmCIF
- **Trust**: OFFICIAL_DOWNLOAD
- **Role**: PCNA reference structure
- **License**: Public Domain (wwPDB open access)

### RCSB PDB 5H0T metadata
- **URL**: https://www.rcsb.org/structure/5H0T
- **File**: `data\raw_intake\rcsb_pdb\5H0T_metadata.json`
- **Size**: 23.9 KB
- **SHA-256**: `7dbfaedae11fa4180c76519b4748c00c080565ab6e933916dfdb25c264399d96`
- **Type**: JSON (RCSB REST API)
- **Trust**: OFFICIAL_API
- **Role**: PCNA structure inventory
- **License**: Public Domain (wwPDB open access)

### RCSB PDB 5H0T mmCIF
- **URL**: https://files.rcsb.org/download/5H0T.cif
- **File**: `data\raw_intake\rcsb_pdb\5H0T.cif`
- **Size**: 1.24 MB
- **SHA-256**: `aae817e46f28f88edc0c19ab7f7edbcfe3772322c69b0c4106ff1053457dc1ed`
- **Type**: mmCIF
- **Trust**: OFFICIAL_DOWNLOAD
- **Role**: PCNA reference structure
- **License**: Public Domain (wwPDB open access)

### RCSB PDB 5CFK metadata
- **URL**: https://www.rcsb.org/structure/5CFK
- **File**: `data\raw_intake\rcsb_pdb\5CFK_metadata.json`
- **Size**: 18.9 KB
- **SHA-256**: `9c6fb394ad16fce1c380ad4baf82f05be8990274a9fdeb3c902f49710f3a9928`
- **Type**: JSON (RCSB REST API)
- **Trust**: OFFICIAL_API
- **Role**: PCNA structure inventory
- **License**: Public Domain (wwPDB open access)

### RCSB PDB 5CFK mmCIF
- **URL**: https://files.rcsb.org/download/5CFK.cif
- **File**: `data\raw_intake\rcsb_pdb\5CFK.cif`
- **Size**: 1.22 MB
- **SHA-256**: `f7040771feda29e5a157e051727b3b565cefc807a33ac21bae3f623bac9390e1`
- **Type**: mmCIF
- **Trust**: OFFICIAL_DOWNLOAD
- **Role**: PCNA reference structure
- **License**: Public Domain (wwPDB open access)

### BioLiP page: biolip_home.html
- **URL**: https://zhanggroup.org/BioLiP/
- **File**: `data\raw_intake\biolip\biolip_home.html`
- **Size**: 30.1 KB
- **SHA-256**: `9e78a4aa2def69cfbb94153adf00d7c52909eac7635bf04a4e3af69021b1e5ca`
- **Type**: HTML
- **Trust**: OFFICIAL_PAGE
- **Role**: BioLiP ligand-binding residue annotation discovery
- **License**: Free for academic use (Zhang Lab)

### scPDB page: scpdb_home.html
- **URL**: http://bioinfo-pharma.u-strasbg.fr/scPDB/
- **File**: `data\raw_intake\scpdb\scpdb_home.html`
- **Size**: 6.0 KB
- **SHA-256**: `efbb541cb736cb159efe0628db25235478e71355d0c933d57233fe12cfccd1bc`
- **Type**: HTML
- **Trust**: OFFICIAL_PAGE
- **Role**: scPDB druggable binding site annotation discovery
- **License**: Free for academic use (Strasbourg)

### ASD page: asd_home.html
- **URL**: http://mdl.shsmu.edu.cn/ASD/
- **File**: `data\raw_intake\asd\asd_home.html`
- **Size**: 20.9 KB
- **SHA-256**: `612d007d54e967c9038a240bae069aab04933377fcdfbab57b35ef2f98562c7c`
- **Type**: HTML
- **Trust**: OFFICIAL_PAGE
- **Role**: Allosteric site/modulator context for PCNA
- **License**: UNKNOWN — check asd.bidd2.com/about

### ASD page: asd_download.html
- **URL**: http://mdl.shsmu.edu.cn/ASD/module/download/download.jsp
- **File**: `data\raw_intake\asd\asd_download.html`
- **Size**: 8.4 KB
- **SHA-256**: `1269f05e48e7dcc4de7ec1e5ab233ef98cdc5e4a105bf06775e4d8855a2bc3f1`
- **Type**: HTML
- **Trust**: OFFICIAL_PAGE
- **Role**: Allosteric site/modulator context for PCNA
- **License**: UNKNOWN — check asd.bidd2.com/about

### PocketMiner PubMed abstract
- **URL**: https://pubmed.ncbi.nlm.nih.gov
- **File**: `data\raw_intake\pocketminer\pocketminer_pubmed_abstract.txt`
- **Size**: 9.3 KB
- **SHA-256**: `527a7382c80d88d83b7133412367e0253c557b438a7ab4613c45e66709598394`
- **Type**: Text
- **Trust**: OFFICIAL_API
- **Role**: PocketMiner paper metadata for citation
- **License**: UNKNOWN

### fpocket GitHub releases
- **URL**: https://github.com/Discngine/fpocket
- **File**: `data\raw_intake\baseline_tools\fpocket\releases.json`
- **Size**: 7.4 KB
- **SHA-256**: `81c3123074688125567c732fa5e848578dc2203f53d716bb33c4e985fc7c3b5a`
- **Type**: JSON
- **Trust**: OFFICIAL_REPO
- **Role**: Voronoi-based open-cavity pocket detector; mandatory baseline
- **License**: MIT/Apache — check per repo

### fpocket README
- **URL**: https://raw.githubusercontent.com/Discngine/fpocket/main/README.md
- **File**: `data\raw_intake\baseline_tools\fpocket\README.md`
- **Size**: 7.5 KB
- **SHA-256**: `68a5fcf00fe341d7b6c71c3a2d430c7fbc287777db5c111a2a70669226020ca0`
- **Type**: Markdown
- **Trust**: OFFICIAL_REPO
- **Role**: Voronoi-based open-cavity pocket detector; mandatory baseline
- **License**: CHECK_REPO

### P2Rank GitHub releases
- **URL**: https://github.com/rdk/p2rank
- **File**: `data\raw_intake\baseline_tools\p2rank\releases.json`
- **Size**: 17.8 KB
- **SHA-256**: `7d202ef36b7ab60aa0b57d5aaad82eb90c72d9bd9b83b2a4b47145b65c08773d`
- **Type**: JSON
- **Trust**: OFFICIAL_REPO
- **Role**: ML-based binding site prediction; second mandatory baseline
- **License**: MIT/Apache — check per repo

### P2Rank README
- **URL**: https://raw.githubusercontent.com/rdk/p2rank/main/README.md
- **File**: `data\raw_intake\baseline_tools\p2rank\README.md`
- **Size**: 14.8 KB
- **SHA-256**: `f56aecb63bec5895b9c2308f74df0ab567563c424b4604cb5b42d07d2aa05fab`
- **Type**: Markdown
- **Trust**: OFFICIAL_REPO
- **Role**: ML-based binding site prediction; second mandatory baseline
- **License**: CHECK_REPO

### PDBbind: pdbbind_home.html
- **URL**: http://www.pdbbind.org.cn
- **File**: `data\raw_intake\pdbbind\pdbbind_home.html`
- **Size**: 218.1 KB
- **SHA-256**: `dd9bd52f44033557ab14569552bba11dfb187172171e30684adc3da81e247eb4`
- **Type**: HTML
- **Trust**: OFFICIAL_PAGE
- **Role**: Protein-ligand affinity context only. NOT cryptic-pocket ground truth.
- **License**: RESTRICTED — registration required for download

### LP-PDBBind GitHub search
- **URL**: https://github.com/search?q=LP-PDBBind
- **File**: `data\raw_intake\pdbbind\lp_pdbbind_github_search.json`
- **Size**: 72 B
- **SHA-256**: `53895997f5e07566d90a3f34b7fbb880fb1acf32d885aa31fbb268a6d7769d2a`
- **Type**: JSON
- **Trust**: OFFICIAL_API
- **Role**: LP-PDBBind leakage-aware split reference for data hygiene
- **License**: UNKNOWN

### AlphaFold P15531 (PCNA_HUMAN) CIF
- **URL**: https://alphafold.ebi.ac.uk/entry/P15531
- **File**: `data\raw_intake\alphafold\AF_P15531_PCNA_HUMAN.cif`
- **Size**: 152.7 KB
- **SHA-256**: `4eab0679af9b60a442d47c869c5f1c42b6fce228803f2378ca342129f894b91c`
- **Type**: mmCIF (predicted)
- **Trust**: OFFICIAL_DOWNLOAD
- **Role**: PCNA predicted structure for structural context only
- **License**: CC BY 4.0

### AlphaFold P15531 (PCNA_HUMAN) API metadata
- **URL**: https://alphafold.ebi.ac.uk/api/prediction/P15531
- **File**: `data\raw_intake\alphafold\AF_P15531_PCNA_HUMAN_api.json`
- **Size**: 4.5 KB
- **SHA-256**: `6cfd164a07258c7d163d176da245228ac14e8eaa322add30630ad324844264a3`
- **Type**: JSON
- **Trust**: OFFICIAL_API
- **Role**: AlphaFold PCNA metadata
- **License**: CC BY 4.0

### AlphaFold P12004 (PCNA_MOUSE) CIF
- **URL**: https://alphafold.ebi.ac.uk/entry/P12004
- **File**: `data\raw_intake\alphafold\AF_P12004_PCNA_MOUSE.cif`
- **Size**: 244.9 KB
- **SHA-256**: `cd62288975867475d1e6c10279b3eac025794bb8e5ddc89cbf4610b3a4de6f01`
- **Type**: mmCIF (predicted)
- **Trust**: OFFICIAL_DOWNLOAD
- **Role**: PCNA predicted structure for structural context only
- **License**: CC BY 4.0

### AlphaFold P12004 (PCNA_MOUSE) API metadata
- **URL**: https://alphafold.ebi.ac.uk/api/prediction/P12004
- **File**: `data\raw_intake\alphafold\AF_P12004_PCNA_MOUSE_api.json`
- **Size**: 2.6 KB
- **SHA-256**: `b7281207729e246f8c5f614a46fcc9c99a05061a5c16d7cf0496797438ac8a88`
- **Type**: JSON
- **Trust**: OFFICIAL_API
- **Role**: AlphaFold PCNA metadata
- **License**: CC BY 4.0

### AlphaFold P04448 (PCNA_YEAST) CIF
- **URL**: https://alphafold.ebi.ac.uk/entry/P04448
- **File**: `data\raw_intake\alphafold\AF_P04448_PCNA_YEAST.cif`
- **Size**: 173.1 KB
- **SHA-256**: `4dd217da965f14922a96bdb45f1a480245d052e8b2c4f7e8e08ae1b02806e56e`
- **Type**: mmCIF (predicted)
- **Trust**: OFFICIAL_DOWNLOAD
- **Role**: PCNA predicted structure for structural context only
- **License**: CC BY 4.0

### AlphaFold P04448 (PCNA_YEAST) API metadata
- **URL**: https://alphafold.ebi.ac.uk/api/prediction/P04448
- **File**: `data\raw_intake\alphafold\AF_P04448_PCNA_YEAST_api.json`
- **Size**: 2.2 KB
- **SHA-256**: `1be5f50698dd78000019e3c2622235c1c8355409b8e6126d9ad34ef7d8b379fe`
- **Type**: JSON
- **Trust**: OFFICIAL_API
- **Role**: AlphaFold PCNA metadata
- **License**: CC BY 4.0

### STRING PCNA network
- **URL**: https://string-db.org
- **File**: `data\raw_intake\string\pcna_string_network.json`
- **Size**: 362.3 KB
- **SHA-256**: `d186acbecc223811aa5d5b02b9bf766ebfb229507545ce33df6bd21e90ea7155`
- **Type**: JSON
- **Trust**: OFFICIAL_API
- **Role**: PCNA functional/physical interaction context
- **License**: CC BY 4.0

### STRING PCNA enrichment
- **URL**: https://string-db.org
- **File**: `data\raw_intake\string\pcna_string_enrichment.json`
- **Size**: 1.02 MB
- **SHA-256**: `cef1fa9b55fc07a774acfdeb1b0e5647450e2bbf334abdcac204f5ae437331a5`
- **Type**: JSON
- **Trust**: OFFICIAL_API
- **Role**: PCNA functional/physical interaction context
- **License**: CC BY 4.0

### STRING PCNA partners
- **URL**: https://string-db.org
- **File**: `data\raw_intake\string\pcna_string_partners.json`
- **Size**: 33.9 KB
- **SHA-256**: `8130c19088bd0d4d36199080940cc676498a7df064b2b359f3d00cc90d4bf875`
- **Type**: JSON
- **Trust**: OFFICIAL_API
- **Role**: PCNA functional/physical interaction context
- **License**: CC BY 4.0

### PubMed abstracts: aoh1996
- **URL**: https://pubmed.ncbi.nlm.nih.gov/?term=AOH1996%20PCNA%20inhibitor
- **File**: `data\raw_intake\literature_metadata\pm_aoh1996.txt`
- **Size**: 36.6 KB
- **SHA-256**: `b05a221f8ccbf334894b09c4b8cae752bac56dc882164e8519d9a9ad0f8c7511`
- **Type**: Text
- **Trust**: OFFICIAL_API
- **Role**: Literature metadata for topic: aoh1996
- **License**: NLM open access — abstracts only

### PubMed abstracts: pocketminer
- **URL**: https://pubmed.ncbi.nlm.nih.gov/?term=PocketMiner%20pocket%20prediction
- **File**: `data\raw_intake\literature_metadata\pm_pocketminer.txt`
- **Size**: 6.9 KB
- **SHA-256**: `8b50bd8aff876af046dcdb8eeb02f96c32e69aae46c5d94387564e96cfc94a2b`
- **Type**: Text
- **Trust**: OFFICIAL_API
- **Role**: Literature metadata for topic: pocketminer
- **License**: NLM open access — abstracts only

### PubMed abstracts: biolip
- **URL**: https://pubmed.ncbi.nlm.nih.gov/?term=BioLiP%20ligand%20binding%20residue%20database
- **File**: `data\raw_intake\literature_metadata\pm_biolip.txt`
- **Size**: 10.4 KB
- **SHA-256**: `c3bcc19a0af2c6a0b07991ef26cf9aac338530b421275591f98659ec0b1e34f4`
- **Type**: Text
- **Trust**: OFFICIAL_API
- **Role**: Literature metadata for topic: biolip
- **License**: NLM open access — abstracts only

### PubMed abstracts: fpocket
- **URL**: https://pubmed.ncbi.nlm.nih.gov/?term=fpocket%20Voronoi%20pocket%20detection
- **File**: `data\raw_intake\literature_metadata\pm_fpocket.txt`
- **Size**: 2.3 KB
- **SHA-256**: `9786cf3af3c14212084af0d7901779eaa21b19813cf5d39a7d9c52a35ba63d57`
- **Type**: Text
- **Trust**: OFFICIAL_API
- **Role**: Literature metadata for topic: fpocket
- **License**: NLM open access — abstracts only

### PubMed abstracts: lp_pdbbind
- **URL**: https://pubmed.ncbi.nlm.nih.gov/?term=LP-PDBBind%20leakage%20protein-ligand%20split
- **File**: `data\raw_intake\literature_metadata\pm_lp_pdbbind.txt`
- **Size**: 4.0 KB
- **SHA-256**: `0227c54b48204c375aae5dee27e2e5108489412ff2d0543d96a51cc6717026f9`
- **Type**: Text
- **Trust**: OFFICIAL_API
- **Role**: Literature metadata for topic: lp_pdbbind
- **License**: NLM open access — abstracts only

### PubMed abstracts: deeppocket
- **URL**: https://pubmed.ncbi.nlm.nih.gov/?term=DeepPocket%20deep%20learning%20pocket
- **File**: `data\raw_intake\literature_metadata\pm_deeppocket.txt`
- **Size**: 4.3 KB
- **SHA-256**: `b17db3aa67d6ed868e161380fc60c1fb465df4a6ecf3a1e577cc1ed4e72b032b`
- **Type**: Text
- **Trust**: OFFICIAL_API
- **Role**: Literature metadata for topic: deeppocket
- **License**: NLM open access — abstracts only

### PubMed abstracts: equipocket
- **URL**: https://pubmed.ncbi.nlm.nih.gov/?term=EquiPocket%20equivariant%20pocket%20prediction
- **File**: `data\raw_intake\literature_metadata\pm_equipocket.txt`
- **Size**: 43.0 KB
- **SHA-256**: `c7a221086443e2e56d749675a24f97e11360d57c65f98e515bedb39f925fa813`
- **Type**: Text
- **Trust**: OFFICIAL_API
- **Role**: Literature metadata for topic: equipocket
- **License**: NLM open access — abstracts only

### PubMed abstracts: leakage
- **URL**: https://pubmed.ncbi.nlm.nih.gov/?term=dataset%20leakage%20protein%20structure%20benchmark
- **File**: `data\raw_intake\literature_metadata\pm_leakage.txt`
- **Size**: 15.7 KB
- **SHA-256**: `4cd4da6ea4643d48d1dc15f3621027ccf96fbe4f463a18ed2115fb5a4333a2b5`
- **Type**: Text
- **Trust**: OFFICIAL_API
- **Role**: Literature metadata for topic: leakage
- **License**: NLM open access — abstracts only

### PubMed abstracts: allosteric_review
- **URL**: https://pubmed.ncbi.nlm.nih.gov/?term=allosteric%20site%20detection%20review
- **File**: `data\raw_intake\literature_metadata\pm_allosteric_review.txt`
- **Size**: 52.9 KB
- **SHA-256**: `3465cad045934d4f42c145aca3bfc3ded56dab2d506ad49f277029b9ad70f667`
- **Type**: Text
- **Trust**: OFFICIAL_API
- **Role**: Literature metadata for topic: allosteric_review
- **License**: NLM open access — abstracts only

### PubMed abstracts: pcna_review
- **URL**: https://pubmed.ncbi.nlm.nih.gov/?term=PCNA%20ring%20sliding%20clamp%20DNA%20replication%20review
- **File**: `data\raw_intake\literature_metadata\pm_pcna_review.txt`
- **Size**: 24.2 KB
- **SHA-256**: `e65c581b378b32982e3715f57d48fbc05595666bd1ff783e1ba4ae504229376a`
- **Type**: Text
- **Trust**: OFFICIAL_API
- **Role**: Literature metadata for topic: pcna_review
- **License**: NLM open access — abstracts only

### Seed context relevant papers (from round_00_seed.json)
- **URL**: local:context/round_00_seed.json
- **File**: `data\raw_intake\literature_metadata\seed_relevant_papers.json`
- **Size**: 437.0 KB
- **SHA-256**: `29c792c1faaa1047eee2bba72339ff036568e7e80310cb12b314c148e13d7e27`
- **Type**: JSON
- **Trust**: CRAWL_LEAD
- **Role**: Literature leads for manual review
- **License**: various

## Linked-only sources (not downloaded)


## Inaccessible sources

- CryptoBench (OSF API search): https://api.osf.io/v2/nodes/?filter[title]=CryptoBench  —  OSF API returned no result