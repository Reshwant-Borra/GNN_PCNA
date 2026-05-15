"""PyTorch dataset wrapper for pre-built .pt graph files."""
from __future__ import annotations
from pathlib import Path
from torch.utils.data import Dataset
from torch_geometric.data import Data
import torch


class PocketDataset(Dataset):
    """Load pre-built PyG graphs from a directory of .pt files."""

    def __init__(self, root: str):
        self.files = sorted(Path(root).glob('*.pt'))

    def __len__(self) -> int:
        return len(self.files)

    def __getitem__(self, idx: int) -> Data:
        return torch.load(self.files[idx], weights_only=False)
