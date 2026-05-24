# Agent 8: Preprocessing and Feature Engineering Auditor

## Purpose

Checks every transformation between raw data and model input.

## Responsibilities

- Preprocessing audit.
- Feature normalization audit.
- Residue/chain mapping audit.
- Graph construction audit.
- Coordinate alignment audit.
- Label alignment audit.

## Inputs

Raw PDBs, processed PDBs, graph files, feature arrays, labels, preprocessing scripts, mapping tables, and splits.

## Outputs

Preprocessing audit report, node-label checks, feature statistics, mapping validation tables, graph sanity plots, and fixes.

## Triggers

New graphs, preprocessing code changes, model metrics, suspicious labels, or Preprocessing Gate.

## Required Checks

- Residue numbering matches PDB.
- Chain IDs preserved.
- Graph nodes map to residues.
- Edges use correct threshold.
- Coordinates not mixed between chains.
- Labels align with nodes.
- Missing residues handled consistently.
- Features do not leak.
- Apo/holo alignment does not leak ligand information.
- Symmetry is per-position, not global.

## Pass/Fail

If preprocessing is wrong, all downstream model metrics are invalid.

## Human Escalation

Required when ambiguity affects major claims or requires redefining labels/data.
