# Models

## Primary Architecture: CrypticGNN

### Overview
Message-passing GNN that operates on residue-level protein graphs to output per-residue cryptic pocket scores.

### Architecture

```
Input Graph
  ↓
Node Embedding MLP (raw features → 128-dim)
  ↓
GNN Layers × 4  (GATv2Conv or GINEConv)
  - Hidden dim: 256
  - Attention heads: 4 (if GAT)
  - Edge features: concatenated at each message pass
  - Residual connections between layers
  ↓
Global + Local Readout
  - Node-level: 256-dim per residue
  ↓
Pocket Scoring Head
  - MLP: 256 → 64 → 1
  - Sigmoid activation
  - Output: P(cryptic pocket) per residue
```

### Loss Function
- Focal Loss (γ=2, α=0.25) — handles severe class imbalance
- Alternative: weighted BCE with pos_weight ~ 10–20×

### Key Design Choices
- **GATv2Conv** preferred over GCNConv: dynamic attention captures long-range interactions
- **Edge features**: distance + sequence separation encode both spatial and sequential context
- **No global pooling** at the scoring stage — per-residue output is needed
- Symmetric aggregation exploits PCNA homotrimer (all 3 chains share weights)

## Baseline Models

| Model | Type | Notes |
|---|---|---|
| fpocket | Geometric | Rule-based Voronoi tessellation; no dynamics awareness |
| SiteMap (Schrödinger) | Geometric + scoring | Commercial; good baseline if available |
| PocketMiner | GNN (similar architecture) | Pre-trained on CryptoSite; primary comparison |
| DeepAllo | Attention GNN | Targets allosteric sites; relevant for PCNA interface |

## Pre-training Strategy
1. Pre-train on sc-PDB / CryptoSite (binary pocket/not-pocket)
2. Fine-tune on PCNA-specific data (few-shot: 8GLA as positive)
3. Evaluate: AUROC on held-out CryptoSite proteins + recovery of 8GLA site

## Hyperparameter Defaults

| Param | Value |
|---|---|
| Learning rate | 1e-3 (AdamW) |
| Weight decay | 1e-4 |
| Batch size | 16 graphs |
| Epochs | 100 (early stopping on val loss, patience=10) |
| Dropout | 0.2 |
| Distance cutoff | 8 Å |
