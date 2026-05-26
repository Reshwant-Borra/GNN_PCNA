"""Stub source bank for smoke runs.

When ``run_phase2_pcna(mode="smoke")`` is invoked, this module supplies a
small but coverage-balanced set of mock sources so the campaign can
produce all its deliverables without network access.

Each entry conforms to the ``SourceEntry`` schema in
``research_os.schemas.registries`` (key fields: ``source_id``,
``source``, ``topic``, ``key_methods``, ``required_controls``,
``relevance_to_project``). The synthesis writer reads with ``.get()`` so
either shape (this strict one or the looser ``agents/ingest.py`` one)
works.
"""
from __future__ import annotations

from typing import Any, Dict, List


def _entry(source_id: str, source: str, topic: str, title: str,
           topics: List[str], relevance: float, summary: str) -> Dict[str, Any]:
    """Build one stub entry. Carries the strict-schema fields *and* the
    loose-schema fields the synthesis writer also reads."""
    return {
        # SourceEntry-required fields
        "source_id": source_id,
        "source": source,
        "topic": topic,
        # Optional SourceEntry fields
        "relevance_to_project": summary,
        "notes": title,
        # Loose-schema fields (silently dropped by RegistryStore validation
        # but kept here so other readers see them).
        "id": source_id,
        "title": title,
        "source_type": source,
        "topics": topics,
        "relevance_score": relevance,
        "abstract_summary": summary,
    }


def stub_sources() -> List[Dict[str, Any]]:
    return [
        # ---- PCNA biology / AOH1996 (8) ----
        _entry("SRC-9001", "review", "pcna",
                "PCNA: a master regulator of DNA replication",
                ["pcna", "dna replication"], 0.95,
                "Review of PCNA's role in DNA replication and repair."),
        _entry("SRC-9002", "article", "pcna",
                "AOH1996 selectively binds a transient PCNA pocket",
                ["pcna", "aoh1996", "cryptic pocket"], 0.97,
                "AOH1996 mechanism characterization."),
        _entry("SRC-9003", "article", "pcna",
                "ATX-101 disrupts PCNA-protein interactions",
                ["pcna", "atx-101", "protein-protein"], 0.88,
                "ATX-101 PCNA inhibitor."),
        _entry("SRC-9004", "article", "pcna",
                "PCNA conformational dynamics from NMR",
                ["pcna", "dynamics", "nmr"], 0.78,
                "PCNA flexibility from NMR ensemble."),
        _entry("SRC-9005", "review", "pcna",
                "The PCNA interactome: 200+ partners",
                ["pcna", "interactome"], 0.82,
                "Comprehensive PCNA partner review."),
        _entry("SRC-9006", "article", "pcna",
                "Crystallographic study of PCNA with AOH1996",
                ["pcna", "aoh1996", "crystal structure"], 0.92,
                "X-ray structure of PCNA-AOH1996 complex (8GLA)."),
        _entry("SRC-9007", "article", "pcna",
                "PCNA loading and unloading by RFC",
                ["pcna", "rfc", "clamp loader"], 0.7,
                "Mechanism of PCNA loading by RFC."),
        _entry("SRC-9008", "review", "pcna",
                "PCNA post-translational modifications",
                ["pcna", "ptm", "ubiquitination"], 0.7,
                "PCNA PTMs and DNA damage response."),

        # ---- Cryptic pockets (6) ----
        _entry("SRC-9101", "review", "cryptic pocket",
                "Cryptic binding sites in proteins: a review",
                ["cryptic pocket", "allosteric"], 0.94,
                "Review of cryptic pocket discovery methods."),
        _entry("SRC-9102", "article", "cryptic pocket",
                "MD reveals cryptic pockets in undruggable targets",
                ["cryptic pocket", "molecular dynamics"], 0.9,
                "MD-based cryptic pocket detection."),
        _entry("SRC-9103", "article", "cryptic pocket",
                "PocketMiner: ML detection of cryptic sites",
                ["cryptic site", "pocket detection", "machine learning"], 0.92,
                "PocketMiner cryptic site predictor."),
        _entry("SRC-9104", "review", "allosteric",
                "Allosteric pockets in cancer targets",
                ["allosteric", "cancer", "drug discovery"], 0.78,
                "Allosteric pocket discovery for cancer."),
        _entry("SRC-9105", "article", "cryptic pocket",
                "Transient pocket opening in solvated proteins",
                ["transient pocket", "solvation"], 0.75,
                "Transient pocket dynamics from explicit-solvent MD."),
        _entry("SRC-9106", "article", "cryptic pocket",
                "Hidden pockets validated by experimental fragment screening",
                ["hidden pocket", "fragment screening"], 0.83,
                "Fragment screen validation of cryptic sites."),

        # ---- Protein GNNs (6) ----
        _entry("SRC-9201", "review", "graph neural network",
                "Graph neural networks for protein structure",
                ["gnn", "graph neural", "protein structure"], 0.93,
                "GNN methods for protein graphs."),
        _entry("SRC-9202", "article", "graph neural network",
                "EGNN: E(n) equivariant graph neural networks",
                ["equivariant", "egnn", "graph neural"], 0.9,
                "E(n)-equivariant GNN architecture."),
        _entry("SRC-9203", "article", "graph neural network",
                "GAT: Graph Attention Networks",
                ["graph attention", "gnn"], 0.85,
                "Graph attention network introduction."),
        _entry("SRC-9204", "article", "graph neural network",
                "SchNet: continuous-filter convolutional networks for molecules",
                ["schnet", "graph neural", "molecules"], 0.82,
                "SchNet molecular GNN."),
        _entry("SRC-9205", "article", "protein language model",
                "ESM2: large language model for proteins",
                ["esm2", "protein language model"], 0.88,
                "ESM2 protein language model."),
        _entry("SRC-9206", "article", "graph neural network",
                "GVP: Geometric vector perceptrons",
                ["gvp", "geometric", "gnn"], 0.78,
                "Geometric vector perceptron architecture."),

        # ---- Pocket prediction (5) ----
        _entry("SRC-9301", "article", "pocket detection",
                "fpocket: open-source protein pocket detector",
                ["fpocket", "pocket detection"], 0.85,
                "fpocket algorithm and benchmark."),
        _entry("SRC-9302", "article", "pocket detection",
                "P2Rank: ML-based binding site prediction",
                ["p2rank", "binding site prediction"], 0.82,
                "P2Rank random-forest binding site predictor."),
        _entry("SRC-9303", "article", "pocket detection",
                "DeepSite: 3D-CNN for binding site detection",
                ["deepsite", "pocket detection", "cnn"], 0.8,
                "DeepSite 3D-CNN approach."),
        _entry("SRC-9304", "preprint", "pocket detection",
                "PocketGNNXL: graph + ESM2 fusion for cryptic pockets",
                ["pocketgnn", "pcna", "esm2", "cryptic pocket"], 0.96,
                "PocketGNNXL architecture combining GNN + ESM2 embeddings."),
        _entry("SRC-9305", "review", "benchmark",
                "Benchmark for protein-ligand binding site prediction",
                ["benchmark", "binding site prediction"], 0.75,
                "CASF and related binding site benchmarks."),

        # ---- MD validation (5) ----
        _entry("SRC-9401", "article", "molecular dynamics",
                "OpenMM toolkit for molecular dynamics",
                ["openmm", "molecular dynamics"], 0.84,
                "OpenMM MD engine paper."),
        _entry("SRC-9402", "review", "molecular dynamics",
                "RMSF analysis for protein flexibility",
                ["rmsf", "molecular dynamics", "flexibility"], 0.8,
                "RMSF analysis best practices."),
        _entry("SRC-9403", "article", "molecular dynamics",
                "DCCM analysis of allosteric coupling",
                ["dccm", "molecular dynamics", "allosteric"], 0.78,
                "Dynamic cross-correlation matrix interpretation."),
        _entry("SRC-9404", "article", "molecular dynamics",
                "Enhanced sampling for cryptic-pocket opening",
                ["metadynamics", "enhanced sampling", "cryptic pocket"], 0.82,
                "Metadynamics for slow conformational changes."),
        _entry("SRC-9405", "review", "molecular dynamics",
                "100ns MD limits for protein flexibility",
                ["molecular dynamics", "rmsd", "timescale"], 0.74,
                "Timescale limitations of MD."),

        # ---- Leakage / splits (3) ----
        _entry("SRC-9501", "article", "leakage",
                "Data leakage in protein ML benchmarks",
                ["leakage", "data leakage", "ml"], 0.92,
                "Leakage pitfalls in protein ML."),
        _entry("SRC-9502", "article", "leakage",
                "Homology-blocked splits for protein function prediction",
                ["homolog", "homology split", "train/test split"], 0.88,
                "Homology-aware train/test splitting."),
        _entry("SRC-9503", "article", "leakage",
                "Apo/holo bias in pocket prediction benchmarks",
                ["apo/holo", "leakage", "pocket detection"], 0.86,
                "Apo/holo bias and its mitigation."),

        # ---- Baselines (3) ----
        _entry("SRC-9601", "article", "baseline",
                "Sequence-only baselines for binding site prediction",
                ["baseline", "sequence-only", "binding site"], 0.78,
                "Sequence-only baselines."),
        _entry("SRC-9602", "article", "baseline",
                "Random forest baselines for pocket detection",
                ["baseline", "random forest", "pocket"], 0.75,
                "RF baseline comparison."),
        _entry("SRC-9603", "article", "baseline",
                "Logistic regression for protein residue classification",
                ["baseline", "logistic regression"], 0.7,
                "LR baseline study."),

        # ---- Reproducibility (2) ----
        _entry("SRC-9701", "review", "reproducibility",
                "Reproducibility crisis in protein ML",
                ["reproducibility", "ml", "protein"], 0.85,
                "Reproducibility issues in protein ML."),
        _entry("SRC-9702", "article", "reproducibility",
                "Deterministic training: seeds, env pinning, and CI",
                ["reproducibility", "deterministic", "seed"], 0.78,
                "Best practices for deterministic ML."),
    ]


def seed_source_registry(registry_store, sources: list = None,
                          *, replace_existing: bool = False) -> int:
    """Seed the registry with the stub sources. Returns the number written.

    Uses ``RegistryStore.append`` so the strict-schema validation runs.
    Entries whose ``source_id`` already exists are skipped.
    """
    sources = sources or stub_sources()
    try:
        existing = {e.get("source_id") for e in registry_store.all_entries("source_registry")
                    if isinstance(e, dict)}
    except Exception:
        existing = set()
    written = 0
    for s in sources:
        if s.get("source_id") in existing and not replace_existing:
            continue
        try:
            registry_store.append("source_registry", s)
            written += 1
        except Exception:
            # Best-effort — corrupt seeds are skipped silently.
            pass
    return written


__all__ = ["stub_sources", "seed_source_registry"]
