# PCNA Data Crawl Report
Generated: 2026-05-15T03:48:51.595796Z

## Summary
- PDB structures found (verified): 193
- External dataset links found: 0

## Top PDB Structures
| PDB ID | Score | Title | Resolution |
|--------|-------|-------|------------|
| [1AXC](https://www.rcsb.org/structure/1AXC) | 1.00 | HUMAN PCNA | 2.6 Å |
| [1W60](https://www.rcsb.org/structure/1W60) | 1.00 | NATIVE HUMAN PCNA | 3.15 Å |
| [1W61](https://www.rcsb.org/structure/1W61) | 1.00 | proline racemase in complex with 2 molecules of py | 2.1 Å |
| [1AXC](https://www.rcsb.org/structure/1AXC) | 1.00 |  | None Å |
| [1W60](https://www.rcsb.org/structure/1W60) | 1.00 |  | None Å |
| [8GLA](https://www.rcsb.org/structure/8GLA) | 1.00 |  | None Å |
| [8GLA](https://www.rcsb.org/structure/8GLA) | 0.90 | Co-crystal structure of caPCNA bound to the AOH199 | 3.77 Å |
| [1U7B](https://www.rcsb.org/structure/1U7B) | 0.60 | Crystal structure of hPCNA bound to residues 331-3 | 1.88 Å |
| [1VYM](https://www.rcsb.org/structure/1VYM) | 0.60 | NATIVE HUMAN PCNA | 2.3 Å |
| [2ZVL](https://www.rcsb.org/structure/2ZVL) | 0.60 | Crystal structure of PCNA in complex with DNA poly | 2.5 Å |
| [2ZVM](https://www.rcsb.org/structure/2ZVM) | 0.60 | Crystal structure of PCNA in complex with DNA poly | 2.3 Å |
| [3VKX](https://www.rcsb.org/structure/3VKX) | 0.60 | Structure of PCNA | 2.1 Å |
| [4RJF](https://www.rcsb.org/structure/4RJF) | 0.60 | Crystal structure of the human sliding clamp at 2. | 2.0072 Å |
| [4ZTD](https://www.rcsb.org/structure/4ZTD) | 0.60 | Crystal Structure of Human PCNA in complex with a  | 2.199 Å |
| [5E0U](https://www.rcsb.org/structure/5E0U) | 0.60 | Human PCNA variant (S228I) complexed with p21 at 1 | 1.93 Å |
| [5E0V](https://www.rcsb.org/structure/5E0V) | 0.60 | Human PCNA variant (S228I) complexed with FEN1 at  | 2.074 Å |
| [5MLO](https://www.rcsb.org/structure/5MLO) | 0.60 | Crystal structure of human PCNA in complex with ZR | 1.96 Å |
| [5MLW](https://www.rcsb.org/structure/5MLW) | 0.60 | Crystal structure of human PCNA in complex with ZR | 2.45 Å |
| [5MOM](https://www.rcsb.org/structure/5MOM) | 0.60 | Crystal Structure of PCNA encoding the hypomorphic | 2.27 Å |
| [5YCO](https://www.rcsb.org/structure/5YCO) | 0.60 | Complex structure of PCNA with UHRF2 | 2.199 Å |
| [5YD8](https://www.rcsb.org/structure/5YD8) | 0.60 | Crystal structure of human PCNA in complex with AP | 2.3 Å |
| [6HVO](https://www.rcsb.org/structure/6HVO) | 0.60 | Crystal structure of human PCNA in complex with th | 2.1 Å |
| [6K3A](https://www.rcsb.org/structure/6K3A) | 0.60 | Crystal structure of human PCNA in complex with DN | 2.3 Å |
| [7KQ0](https://www.rcsb.org/structure/7KQ0) | 0.60 | PCNA bound to peptide mimetic | 2.4 Å |
| [8F5Q](https://www.rcsb.org/structure/8F5Q) | 0.60 | Crystal structure of human PCNA in complex with th | 1.9 Å |
| [9N3L](https://www.rcsb.org/structure/9N3L) | 0.60 | Co-crystal structure of PCNA bound to HSP90alpha i | 1.9 Å |
| [1U76](https://www.rcsb.org/structure/1U76) | 0.50 | Crystal structure of hPCNA bound to residues 452-4 | 2.6 Å |
| [1UL1](https://www.rcsb.org/structure/1UL1) | 0.50 | Crystal structure of the human FEN1-PCNA complex | 2.9 Å |
| [1VYJ](https://www.rcsb.org/structure/1VYJ) | 0.50 | Structural and biochemical studies of human PCNA c | 2.8 Å |
| [2ZVK](https://www.rcsb.org/structure/2ZVK) | 0.50 | Crystal structure of PCNA in complex with DNA poly | 2.7 Å |

## External Dataset Links

## Next Steps
1. Run `python agents/pcna_crawler.py --download` to fetch top PDB files
2. Check `data/catalog/download_queue.txt` for full download list
3. Manually verify CryptoSite/PocketMiner links and download dataset
4. Run `src/data_processing/parse_pdb.py` on downloaded structures