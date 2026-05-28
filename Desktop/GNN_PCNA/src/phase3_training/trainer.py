"""Governed Phase 3 training loop for GraphSAGE-3L.

Implements 4-fold CV with early stopping on validation macro-AUPRC (patience=10).
pos_weight is computed from training-fold nodes only — never from val/test.

The dry-run guard in gates.py is checked at the start of train() and will
raise TrainingGateError until a human signs the GATE 2 first-training record.
Do NOT remove or weaken this gate until the human sign-off is recorded.

Governance:
  docs/scientific_governance/08_MODEL_ARCHITECTURE_CONSTRAINTS.md
  docs/scientific_governance/09_EVALUATION_PROTOCOL.md
  docs/scientific_governance/19_STOP_CONDITIONS.md
Approval:
  reports/phase3/model_training_decision_20260528.md
  (decision_id: phase3_model_training_plan_20260528)
"""

from __future__ import annotations

import copy
import dataclasses
import math
from pathlib import Path
from typing import Any

import torch
import torch.nn as nn
from torch_geometric.loader import DataLoader

from phase3_training.gates import training_gate_status


@dataclasses.dataclass
class TrainerConfig:
    hidden_dim: int = 128
    dropout: float = 0.1
    lr: float = 1e-3
    weight_decay: float = 1e-5
    max_epochs: int = 200
    patience: int = 10
    batch_size: int = 4
    device: str = "cpu"
    seed: int = 0


@dataclasses.dataclass
class EpochResult:
    epoch: int
    train_loss: float
    val_macro_auprc: float


@dataclasses.dataclass
class TrainingResult:
    best_val_macro_auprc: float
    best_epoch: int
    epochs_run: int
    history: list[EpochResult]
    model_state_dict: dict[str, Any]
    config: TrainerConfig
    governance: list[str] = dataclasses.field(default_factory=lambda: [
        "docs/scientific_governance/08_MODEL_ARCHITECTURE_CONSTRAINTS.md",
        "docs/scientific_governance/09_EVALUATION_PROTOCOL.md",
        "docs/scientific_governance/19_STOP_CONDITIONS.md",
    ])


def _train_epoch(
    model: nn.Module,
    loader: DataLoader,
    optimizer: torch.optim.Optimizer,
    criterion: nn.BCEWithLogitsLoss,
    device: torch.device,
) -> float:
    """Run one training epoch. Returns mean loss over loss_mask=True nodes."""
    model.train()
    total_loss = 0.0
    total_nodes = 0
    for batch in loader:
        batch = batch.to(device)
        optimizer.zero_grad()
        logits = model(batch)                   # (N_all,) raw logits
        mask = batch.loss_mask                  # (N_all,) bool
        targets = batch.y[mask].float()         # (N_masked,) float
        loss = criterion(logits[mask], targets)
        loss.backward()
        optimizer.step()
        n = int(mask.sum())
        total_loss += loss.item() * n
        total_nodes += n
    return total_loss / max(total_nodes, 1)


def _collect_protein_scores(
    model: nn.Module,
    loader: DataLoader,
    device: torch.device,
) -> list[tuple[list[float], list[int]]]:
    """Run inference and return per-protein (scores, labels) pairs.

    Only loss_mask=True nodes are included. Scores are raw logits (not sigmoid).
    """
    model.eval()
    protein_scores: list[tuple[list[float], list[int]]] = []
    with torch.no_grad():
        for batch in loader:
            batch = batch.to(device)
            logits = model(batch)  # (N_all,)
            for i in range(batch.num_graphs):
                node_mask = batch.batch == i
                loss_mask = batch.loss_mask[node_mask]
                logits_i = logits[node_mask][loss_mask].cpu().tolist()
                labels_i = batch.y[node_mask][loss_mask].cpu().tolist()
                protein_scores.append((logits_i, labels_i))
    return protein_scores


def train(
    model: nn.Module,
    train_loader: DataLoader,
    val_loader: DataLoader,
    pos_weight: torch.Tensor,
    config: TrainerConfig,
    first_training_signoff: Path | None = None,
) -> TrainingResult:
    """Run the governed training loop.

    This function is gated: it will raise TrainingGateError until a human
    records GATE 2 first-training sign-off in gates.py.

    Args:
        model: GraphSAGE3L instance.
        train_loader: DataLoader over training-fold graphs.
        val_loader: DataLoader over validation-fold graphs.
        pos_weight: n_bg_train / n_pos_train (training fold only).
        config: TrainerConfig with hyperparameters.
        first_training_signoff: Path to the GATE 2 human sign-off record.
            Must exist as a file before training is allowed.

    Returns:
        TrainingResult with best model state dict and full history.

    Raises:
        TrainingGateError: always, until GATE 2 is signed and gates.py updated.
    """
    # Gate check — this raises until GATE 2 human sign-off is recorded.
    # Do NOT remove this call. Do NOT wrap in try/except to suppress.
    training_gate_status(
        real_training=True,
        human_pipeline_signoff=first_training_signoff,
    )

    # --- Code below is correct but unreachable until gate passes ---

    from phase3_evaluation.metrics import compute_metrics_from_lists

    torch.manual_seed(config.seed)
    device = torch.device(config.device)
    model = model.to(device)
    pw = pos_weight.to(device)

    criterion = nn.BCEWithLogitsLoss(pos_weight=pw)
    optimizer = torch.optim.Adam(
        model.parameters(),
        lr=config.lr,
        weight_decay=config.weight_decay,
    )

    best_val_auprc = -1.0
    best_epoch = 0
    best_state: dict[str, Any] = copy.deepcopy(model.state_dict())
    no_improve = 0
    history: list[EpochResult] = []

    for epoch in range(1, config.max_epochs + 1):
        train_loss = _train_epoch(model, train_loader, optimizer, criterion, device)

        val_scores = _collect_protein_scores(model, val_loader, device)
        val_metrics = compute_metrics_from_lists(val_scores)
        val_auprc = val_metrics["macro_auprc"]

        history.append(EpochResult(epoch=epoch, train_loss=train_loss, val_macro_auprc=val_auprc))

        if not math.isnan(val_auprc) and val_auprc > best_val_auprc:
            best_val_auprc = val_auprc
            best_epoch = epoch
            best_state = copy.deepcopy(model.state_dict())
            no_improve = 0
        else:
            no_improve += 1

        if no_improve >= config.patience:
            break

    return TrainingResult(
        best_val_macro_auprc=best_val_auprc,
        best_epoch=best_epoch,
        epochs_run=len(history),
        history=history,
        model_state_dict=best_state,
        config=config,
    )
