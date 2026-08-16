"""GNN baseline trainer with GATE 3 authorization check.

Trains any GNN model that produces (N,) logits from a PyG Data object.
Supports edge-type filtering for ablation studies.

All GNN baselines use:
  - frozen split (hash validated by caller via load_split)
  - pos_weight from training fold only (governance requirement)
  - validation-fold evaluation only (test set never touched)
  - early stopping on val macro-AUPRC (patience=10)

Governance: docs/scientific_governance/10_BASELINE_REQUIREMENTS.md
Gate: reports/phase3/baseline_gate3_authorization_20260529.md
"""

from __future__ import annotations

import copy
import math
import time
from pathlib import Path
from typing import Any

import torch
import torch.nn as nn
from torch_geometric.data import Data
from torch_geometric.loader import DataLoader

_GATE3_RECORD = Path(__file__).resolve().parents[2] / "reports/phase3/baseline_gate3_authorization_20260529.md"

EDGE_TYPE_SPATIAL: int = 0
EDGE_TYPE_SEQUENTIAL: int = 1


class BaselineGateError(RuntimeError):
    """Raised if GATE 3 authorization record is missing."""


def _check_gate3(gate3_record: Path = _GATE3_RECORD) -> None:
    if not gate3_record.is_file():
        raise BaselineGateError(
            f"Baseline GATE 3 authorization record not found: {gate3_record}. "
            "Human authorization (Reshwant) must be recorded before GNN baselines run."
        )


def filter_edges(data: Data, keep_type: int | None) -> Data:
    """Return a new Data with only edges of the specified type.

    Args:
        data: PyG Data object with edge_type field.
        keep_type: EDGE_TYPE_SPATIAL (0), EDGE_TYPE_SEQUENTIAL (1), or None (keep all).

    Returns:
        New Data object; non-edge attributes are unchanged.
    """
    if keep_type is None:
        return data
    mask = (data.edge_type == keep_type)
    kwargs: dict[str, Any] = {}
    for key, val in data.items():
        if key == "edge_index":
            kwargs[key] = val[:, mask]
        elif key in ("edge_type", "edge_attr"):
            kwargs[key] = val[mask]
        else:
            kwargs[key] = val
    return Data(**kwargs)


def _collect_val_scores(
    model: nn.Module,
    val_loader: DataLoader,
    device: torch.device,
) -> list[tuple[list[float], list[int]]]:
    model.eval()
    protein_scores: list[tuple[list[float], list[int]]] = []
    with torch.no_grad():
        for batch in val_loader:
            batch = batch.to(device)
            logits = model(batch)
            for i in range(batch.num_graphs):
                nm = batch.batch == i
                lm = batch.loss_mask[nm]
                protein_scores.append((
                    logits[nm][lm].cpu().tolist(),
                    [int(v) for v in batch.y[nm][lm].cpu().tolist()],
                ))
    return protein_scores


def train_baseline_gnn(
    model: nn.Module,
    train_data: list[Data],
    val_data: list[Data],
    pos_weight: torch.Tensor,
    seed: int = 0,
    lr: float = 1e-3,
    weight_decay: float = 1e-5,
    max_epochs: int = 100,
    patience: int = 10,
    batch_size: int = 4,
    edge_type_filter: int | None = None,
    gate3_record: Path = _GATE3_RECORD,
    verbose: bool = False,
) -> dict[str, Any]:
    """Train a GNN baseline model.

    Args:
        model: Any nn.Module producing (N,) logits from a PyG Data.
        train_data: Training-fold Data objects.
        val_data: Validation-fold Data objects.
        pos_weight: BCEWithLogitsLoss pos_weight (train-only, computed by caller).
        seed: Random seed.
        lr: Adam learning rate.
        weight_decay: Adam L2 penalty.
        max_epochs: Maximum training epochs.
        patience: Early-stopping patience on val macro-AUPRC.
        batch_size: Training batch size (proteins per batch).
        edge_type_filter: None=all edges, 0=spatial only, 1=sequential only.
        gate3_record: Path to GATE 3 authorization record.
        verbose: Print epoch-level progress.

    Returns:
        Dict with best metrics, history, and provenance.

    Raises:
        BaselineGateError: if GATE 3 record is absent.
    """
    from phase3_evaluation.metrics import compute_metrics_from_lists

    _check_gate3(gate3_record)

    t_start = time.time()
    torch.manual_seed(seed)
    device = torch.device("cpu")
    model = model.to(device)

    if edge_type_filter is not None:
        train_filtered = [filter_edges(d, edge_type_filter) for d in train_data]
        val_filtered = [filter_edges(d, edge_type_filter) for d in val_data]
    else:
        train_filtered = train_data
        val_filtered = val_data

    train_loader = DataLoader(train_filtered, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_filtered, batch_size=32, shuffle=False)

    criterion = nn.BCEWithLogitsLoss(pos_weight=pos_weight.to(device))
    optimizer = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=weight_decay)

    best_auprc = -1.0
    best_epoch = 0
    best_state: dict[str, Any] = copy.deepcopy(model.state_dict())
    no_improve = 0
    history: list[dict[str, Any]] = []

    for epoch in range(1, max_epochs + 1):
        model.train()
        total_loss, total_n = 0.0, 0
        for batch in train_loader:
            batch = batch.to(device)
            optimizer.zero_grad()
            logits = model(batch)
            mask = batch.loss_mask
            loss = criterion(logits[mask], batch.y[mask].float())
            loss.backward()
            optimizer.step()
            n = int(mask.sum())
            total_loss += loss.item() * n
            total_n += n

        train_loss = total_loss / max(total_n, 1)
        val_scores = _collect_val_scores(model, val_loader, device)
        vm = compute_metrics_from_lists(val_scores)
        val_auprc = vm["macro_auprc"]

        history.append({
            "epoch": epoch,
            "train_loss": round(train_loss, 6),
            "val_macro_auprc": round(val_auprc, 6) if not math.isnan(val_auprc) else None,
        })

        improved = not math.isnan(val_auprc) and val_auprc > best_auprc
        if improved:
            best_auprc = val_auprc
            best_epoch = epoch
            best_state = copy.deepcopy(model.state_dict())
            no_improve = 0
        else:
            no_improve += 1

        if verbose and (epoch % 5 == 0 or epoch == 1 or improved):
            flag = " *" if improved else ""
            print(f"  ep {epoch:3d}  loss={train_loss:.4f}  val_macro_auprc={val_auprc:.4f}{flag}")

        if no_improve >= patience:
            if verbose:
                print(f"  Early stop ep {epoch}")
            break

    model.load_state_dict(best_state)
    final_scores = _collect_val_scores(
        model,
        DataLoader(val_filtered, batch_size=32, shuffle=False),
        device,
    )
    from phase3_evaluation.metrics import bootstrap_ci, compute_metrics_from_lists
    final_metrics = compute_metrics_from_lists(final_scores)
    final_ci = bootstrap_ci(final_scores)

    return {
        "seed": seed,
        "edge_type_filter": edge_type_filter,
        "best_epoch": best_epoch,
        "epochs_run": len(history),
        "best_val_macro_auprc": round(best_auprc, 6),
        "elapsed_seconds": round(time.time() - t_start, 1),
        "final_metrics": final_metrics,
        "final_ci": final_ci,
        "history": history,
        "gate": str(gate3_record),
        "no_test_set_evaluation": True,
        "no_scientific_claims": True,
    }
