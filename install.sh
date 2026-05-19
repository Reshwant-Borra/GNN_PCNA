#!/usr/bin/env bash
# GNN-PCNA dependency installer.
# Usage:
#   bash install.sh          # CPU-only (default)
#   bash install.sh cu118    # NVIDIA GPU, CUDA 11.8
#   bash install.sh cu121    # NVIDIA GPU, CUDA 12.1
#
# Reason this script exists: torch-scatter and torch-sparse must be installed
# from the PyG wheel server with a tag that matches your torch+CUDA build.
# A plain 'pip install -r requirements.txt' will fail or install wrong binaries.

set -e

CUDA=${1:-cpu}

echo "=== Step 1: PyTorch (${CUDA}) ==="
pip install torch==2.1.2 --index-url "https://download.pytorch.org/whl/${CUDA}"

echo "=== Step 2: PyG sparse ops (${CUDA}) ==="
pip install torch-scatter torch-sparse \
  -f "https://data.pyg.org/whl/torch-2.1.0+${CUDA}.html"

echo "=== Step 3: PyTorch Geometric ==="
pip install torch-geometric==2.5.3

echo "=== Step 4: All other dependencies ==="
pip install biopython==1.83 scipy==1.13.1 numpy==1.26.4 \
            scikit-learn==1.5.2 tqdm==4.66.5 \
            requests==2.32.3 beautifulsoup4==4.12.3 \
            streamlit==1.38.0 matplotlib==3.9.2 pandas==2.2.3

echo ""
echo "=== Verify ==="
python -c "import torch; import torch_geometric; import torch_scatter; print('OK — torch', torch.__version__, '| pyg', torch_geometric.__version__)"
