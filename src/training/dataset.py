"""PyTorch dataset wrapper for pre-built .pt graph files."""
from __future__ import annotations
import json
from pathlib import Path
from torch.utils.data import Dataset
from torch_geometric.data import Data
import torch


class PocketDataset(Dataset):
    """Load pre-built PyG graphs from a directory of .pt files or a split manifest."""

    def __init__(self, root: str):
        root = Path(root)
        if root.suffix == ".json":
            # manifest not supported via __init__ — use from_manifest()
            raise ValueError(
                f"{root} looks like a JSON manifest. Use:\n"
                f"  PocketDataset.from_manifest('{root}', split='train', graph_dir='data/graphs')"
            )
        self.files = sorted(root.glob("*.pt"))

    @classmethod
    def from_manifest(
        cls,
        manifest_path: str | Path,
        split: str,
        graph_dir: str | Path = "data/graphs",
    ) -> "PocketDataset":
        """Load a named split (train/val/test) from cryptosite_split.json."""
        manifest = json.loads(Path(manifest_path).read_text())
        graph_dir = Path(graph_dir)
        stems = manifest["splits"][split]
        obj = cls.__new__(cls)
        obj.files = [graph_dir / f"{stem}.pt" for stem in stems]
        missing = [f for f in obj.files if not f.exists()]
        if missing:
            raise FileNotFoundError(
                f"{len(missing)} graph file(s) missing from {graph_dir}. "
                f"First missing: {missing[0].name}"
            )
        return obj

    def __len__(self) -> int:
        return len(self.files)

    def __getitem__(self, idx: int) -> Data:
        return torch.load(self.files[idx], weights_only=False)
