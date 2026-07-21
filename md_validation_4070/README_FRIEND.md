# PCNA cryptic-pocket MD validation — RTX 4070 run package (v2)

Hey — thanks for running this. It's a molecular-dynamics check for a GNN that predicts a
cryptic drug pocket on the PCNA protein (cancer target). You don't need to know the biology;
just run the commands below. The whole point of this version is that it **can't come back as a
fake negative** like the first attempt did — it runs a built-in positive control and checks
itself — and v2 also fixes a structural bug where the apo and control weren't the same shape.

## 0. One-time setup (~10 min)
```bash
conda env create -f environment.yml
conda activate pcna-md-4070
python -c "import openmm; print(openmm.Platform.getPlatformByName('CUDA').getName())"   # should print: CUDA
```

## 1. Easiest path — one command, runs detached in tmux
```bash
./run_in_tmux.sh          # runs the control, then the apo, then the analysis — all unattended
```
This starts everything in a **tmux** session so it keeps running after you close your SSH window
or log out, and you can look in on it whenever:
```bash
tmux attach -t pcna-md               # watch live   (leave it running: press Ctrl-b, then d)
tail -f run_*.log                    # or just tail the log file from anywhere
```
**If the machine reboots or you Ctrl-C:** just run `./run_in_tmux.sh` again — it resumes each
replicate from its last checkpoint, never from zero.

## 1b. Or run the steps by hand
Run the **positive control first** (8GLA), then the apo (1W60). Each is 3 replicates × 100 ns.
On a 4070 with HMR + 4 fs expect roughly **1.5–2.5 days per structure** (it prints a live ETA).
```bash
python run_md.py --pocket aoh1996 --run control --replicates 3 --ns 100   # 8GLA (pocket starts open)
python run_md.py --pocket aoh1996 --run apo     --replicates 3 --ns 100   # 1W60 (does the pocket open?)
python analyze_md.py --pocket aoh1996
```
Same resume behaviour: re-run the exact same command after any crash. Shorter on time? Use
`--ns 50`. Don't go below 3 replicates or ~50 ns — that's what made the first result uninterpretable.

## 2. Read the result
Analysis writes `outputs/analysis/REPORT.md`. **Look at the "Positive-control gate" line:**
- `Interpretable: True`  → the method can tell the open pocket (8GLA) from the closed one
  (1W60), so whatever the apo result is, it's real.
- `Interpretable: False` → control and apo look the same to the metric → **the run is
  inconclusive, not a negative.** Extend sampling (`--ns 200`) or we switch to enhanced
  sampling. Do NOT report this as "no pocket."

## 3. Send results back
Send the whole `outputs/` folder back (trajectories + saved topology + analysis). Easiest:
```bash
pip install magic-wormhole
wormhole send outputs            # paste me the code it prints
```
Each trajectory has its `system_solvated.pdb` saved right next to it, so the analysis is never
blocked on a missing topology.

## What v2 fixed (on top of the v1 anti-false-negative design)
| Problem | v2 fix |
|---|---|
| **apo and control were different shapes.** v1 downloaded the *deposited* file, so apo (1W60) came out as 2 loose chains whose "interface" was a crystal-packing accident, while the control (8GLA) was a different chain count. The pocket only exists at a *real* subunit interface, so the comparison was apples-to-oranges. | Both structures are now rebuilt into the **biological homotrimer** (gemmi applies the crystal symmetry), so apo and control are matched 3-chain rings with a genuine interface. Verified: both give 3 chains with all 28 pocket residues present. |
| Chain count was never checked | The run **hard-fails** unless it gets exactly 3 PCNA chains — no silently simulating the wrong assembly |
| "peptides stripped" but a peptide made of normal amino acids (like p21) slipped through | Only real PCNA chains (≥200 residues) are kept; peptides are dropped by length |
| Pocket residue list was hand-typed and missing 4 real contact residues | Residues now come from `pockets/aoh1996.json` (the reproducible, derived list) |

## What v1 already fixed (vs the very first attempt)
| First attempt | This package |
|---|---|
| "apo" was 1AXC (p21-bound) / 5E0V (a disease mutant + FEN1) | **True apo 1W60** + **true holo 8GLA** |
| No positive control → a negative meant nothing | **8GLA open-pocket positive control + auto gate** |
| n=1 (replicates died, never resumed) | **Resumable** 3 replicates; killed runs continue |
| Topology not saved → analysis blocked | **`system_solvated.pdb` saved next to every DCD** |
| 2 fs, ~20 ns usable | **HMR + 4 fs**, default 3 × 100 ns |
| PBC artifact → 25 Å RMSD garbage | Analysis **images PBC before** superposition + a jump-based artifact check |

No ligand force-field parameterization is needed — both systems are simulated as protein-only
(the ligand is stripped), and 8GLA's already-open conformation is the control.

Questions → ping Advay. Thank you! 🙏
