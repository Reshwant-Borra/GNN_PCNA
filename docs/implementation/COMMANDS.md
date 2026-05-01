# COMMANDS.md — CLI Commands

→ Links: [[ENVIRONMENT]] | [[PIPELINE]] | [[FILE_GUIDE]]

> Commands marked `Needs verification` have not been tested yet.

---

## Data Acquisition

```bash
# Download PDB structures
mkdir -p data/raw
wget https://files.rcsb.org/download/1W60.pdb -O data/raw/1W60.pdb
wget https://files.rcsb.org/download/8GLA.pdb -O data/raw/8GLA.pdb

# Verify download
grep "^ATOM" data/raw/1W60.pdb | wc -l
grep "HETATM" data/raw/8GLA.pdb | head -20
```

---

## Data Processing

```bash
# Needs verification — scripts not yet implemented

# Parse and clean PDB (placeholder)
python -c "
from pathlib import Path
from src.data_processing.parse_pdb import parse_pdb
residues = parse_pdb(Path('data/raw/1W60.pdb'))
print(f'Residues: {len(residues)}')
"

# Build graph (placeholder)
python -c "
import torch
from src.data_processing.graph_construction import build_graph
# import parse_pdb output here
"
```

---

## Training

```bash
# Needs verification — train.py not yet implemented

# Run training (placeholder signature)
python src/training/train.py \
    --train-graphs data/graphs/train/ \
    --val-graphs data/graphs/val/ \
    --epochs 100 \
    --lr 1e-3 \
    --patience 10 \
    --checkpoint-dir checkpoints/

# Resume from checkpoint
python src/training/train.py \
    --resume checkpoints/best_model.pt
```

---

## Evaluation

```bash
# Needs verification — score_pockets.py not yet implemented

# Score pockets on a structure
python src/evaluation/score_pockets.py \
    --pdb data/processed/8GLA_clean.pdb \
    --graph data/graphs/8GLA.pt \
    --model checkpoints/best_model.pt \
    --output results/pockets/8GLA_pockets.json

# Run baseline fpocket (geometric)
fpocket -f data/processed/1W60_clean.pdb
```

---

## MD Analysis

```bash
# Needs verification — parse_trajectory.py not yet implemented

# Compute RMSF from trajectory
python src/md/parse_trajectory.py \
    --topology data/trajectories/1W60_apo.gro \
    --trajectory data/trajectories/1W60_apo_100ns.xtc \
    --output results/md/rmsf.npy

# Run MDpocket for volume tracking
mdpocket \
    --trajectory_file data/trajectories/1W60_apo_100ns.xtc \
    --trajectory_format xtc \
    -f data/processed/1W60_clean.pdb \
    --output_prefix results/md/volume/
```

---

## Model Inspection

```bash
# Quick smoke test of CrypticGNN (no data needed)
python -c "
import torch
from src.models.cryptic_gnn import CrypticGNN

model = CrypticGNN()
N, E = 267, 2000
x = torch.randn(N, 26)
edge_index = torch.randint(0, N, (2, E))
edge_attr = torch.randn(E, 2)
scores = model(x, edge_index, edge_attr)
print(f'Output shape: {scores.shape}')  # expect (267,)
print(f'Score range: [{scores.min():.3f}, {scores.max():.3f}]')  # expect [0, 1]
"
```

---

## Visualization

```bash
# Open interactive system map (Windows)
start docs\visuals\system_map.html

# Render Mermaid to PNG (requires Node.js + mmdc)
npx @mermaid-js/mermaid-cli -i docs/visuals/pipeline_map.mmd -o pipeline_map.png
```

---

## Git

```bash
# Do NOT commit large data files
git status
# Add gitignore rules for data/ if not already present

# Normal workflow
git add CLAUDE.md REPO_MAP.md AGENTS.md docs/
git commit -m "update: [description]"
```
