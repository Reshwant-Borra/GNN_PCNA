"""PyTorch Geometric dataset wrapper for pre-built .pt graph files."""
from __future__ import annotations
from pathlib import Path
from torch_geometric.data import Dataset, Data
import torch


class PocketDataset(Dataset):
    """Load pre-built PyG graphs from a directory of .pt files."""

    def __init__(self, root: str):
        self.files = sorted(Path(root).glob('*.pt'))
        super().__init__()

    def len(self) -> int:
        return len(self.files)

    def get(self, idx: int) -> Data:
        return torch.load(self.files[idx])
