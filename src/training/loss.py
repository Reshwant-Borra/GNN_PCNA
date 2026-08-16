"""Focal loss for imbalanced pocket/non-pocket classification."""
import torch
import torch.nn.functional as F


def focal_loss(
    scores: torch.Tensor,   # (N,) predicted probabilities
    targets: torch.Tensor,  # (N,) binary labels
    gamma: float = 2.0,
    alpha: float = 0.25,
    reduction: str = 'mean',
) -> torch.Tensor:
    bce = F.binary_cross_entropy(scores, targets, reduction='none')
    p_t = scores * targets + (1 - scores) * (1 - targets)
    alpha_t = alpha * targets + (1 - alpha) * (1 - targets)
    loss = alpha_t * (1 - p_t) ** gamma * bce
    if reduction == 'mean':
        return loss.mean()
    return loss.sum()
