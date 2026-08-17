"""Central configuration for paper_engine.

Resolves the two data roots (the ResearchOS orchestration repo and the nested
``Desktop/GNN_PCNA`` experimental-science root), output locations, and the local
Ollama model + CPU-thread settings. Everything is overridable via environment
variables so the engine can be tuned without code edits.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable, List, Optional

# --- Roots -------------------------------------------------------------------
# paper_engine/ lives at the orchestration repo root next to research_os/.
REPO_ROOT: Path = Path(__file__).resolve().parents[1]

# The real experimental data (Phase-3 training, labels, splits, baselines, wiki)
# lives in a nested directory. Large artifacts (the MD trajectory) live under the
# orchestration repo's own data/ dir. We search both, science-root first.
SCIENCE_ROOT: Path = REPO_ROOT / "Desktop" / "GNN_PCNA"
# The repository consolidation moved the Phase-2/Phase-3 experimental tree
# (reports/phase3, data/labels, data/registries) under archive/. It is still the
# authoritative source for those artifacts, so it is searched last: if the data
# is ever restored to SCIENCE_ROOT or REPO_ROOT, those take precedence.
ARCHIVE_ROOT: Path = REPO_ROOT / "archive" / "historical_desktop_gnn_pcna_202605_phase2_phase4"
DATA_SEARCH_ROOTS: List[Path] = [SCIENCE_ROOT, REPO_ROOT, ARCHIVE_ROOT]

# --- Output locations --------------------------------------------------------
PAPER_DIR: Path = REPO_ROOT / "paper"
FIGURES_DIR: Path = PAPER_DIR / "figures"
CACHE_DIR: Path = PAPER_DIR / ".cache"
DRAFT_DIR: Path = PAPER_DIR / "drafts"
CORPUS_DIR: Path = REPO_ROOT / "data" / "literature"
CORPUS_PDF_DIR: Path = CORPUS_DIR / "pdfs"
CORPUS_INDEX_DIR: Path = CORPUS_DIR / "index"

# --- Local models (Ollama, CPU-first) ----------------------------------------
# Default to the model that is already installed (gemma3:4b) so the engine runs
# out of the box. For higher-quality prose set PAPER_ENGINE_MODEL to a stronger
# CPU-capable model once pulled, e.g.:
#     ollama pull qwen2.5:14b-instruct        (better prose, slower on CPU)
#     ollama pull gpt-oss:20b
WRITER_MODEL: str = os.environ.get("PAPER_ENGINE_MODEL", "gemma3:4b")
AUDIT_MODEL: str = os.environ.get("PAPER_ENGINE_AUDIT_MODEL", "gemma3:4b")
EMBED_MODEL: str = os.environ.get("PAPER_ENGINE_EMBED_MODEL", "nomic-embed-text")
OLLAMA_HOST: str = os.environ.get("OLLAMA_HOST", "http://localhost:11434")

# --- CPU usage ---------------------------------------------------------------
N_CORES: int = os.cpu_count() or 4
# Embedding/PDF-extraction work IS embarrassingly parallel — fan it out across
# all cores (this is where "use the whole CPU" pays off).
WORKER_PROCESSES: int = int(os.environ.get("PAPER_ENGINE_WORKERS", N_CORES))
# LLM inference is NOT: forcing all logical cores oversubscribes hybrid CPUs and
# collapses throughput (~1.6 tok/s observed at num_thread=22). Leave this unset
# so Ollama auto-selects the optimal thread count; override only if you have
# measured a better value.
_ollama_threads_env = os.environ.get("PAPER_ENGINE_OLLAMA_THREADS")
OLLAMA_NUM_THREAD = int(_ollama_threads_env) if _ollama_threads_env else None

# --- Known real-data artifact locations (relative to a search root) ----------
# Each entry is a tuple of candidate relative paths; find_data_file returns the
# first that exists across DATA_SEARCH_ROOTS.
PHASE3_REPORTS = ("Desktop/GNN_PCNA/reports/phase3", "reports/phase3")
MD_TRAJECTORY = ("data/md/1W60_production.dcd",)
LABEL_MANIFEST = ("data/labels/label_manifest.json",)
SPLIT_MANIFEST = ("data/registries/split_manifest_frozen.json",)


def find_data_file(
    *relative_candidates: str, roots: Optional[Iterable[Path]] = None
) -> Optional[Path]:
    """Return the first existing path for any candidate across the data roots."""
    search_roots = list(roots) if roots is not None else DATA_SEARCH_ROOTS
    for root in search_roots:
        for rel in relative_candidates:
            candidate = root / rel
            if candidate.exists():
                return candidate
    return None


def require_data_file(*relative_candidates: str, roots: Optional[Iterable[Path]] = None) -> Path:
    """Like find_data_file but raises a clear error instead of fabricating.

    Integrity rule: the engine fails loudly when real data is absent rather than
    inventing numbers.
    """
    found = find_data_file(*relative_candidates, roots=roots)
    if found is None:
        searched = [str(r) for r in (roots or DATA_SEARCH_ROOTS)]
        raise FileNotFoundError(
            "Required real-data file not found. Candidates="
            + repr(list(relative_candidates))
            + " searched roots="
            + repr(searched)
        )
    return found


def phase3_reports_dir() -> Path:
    """Absolute path to the phase-3 reports directory holding run manifests."""
    return require_data_file(*PHASE3_REPORTS)


def ensure_output_dirs() -> None:
    for directory in (PAPER_DIR, FIGURES_DIR, CACHE_DIR, DRAFT_DIR):
        directory.mkdir(parents=True, exist_ok=True)


def describe() -> dict:
    """Human-readable snapshot of the resolved configuration (for diagnostics)."""
    return {
        "repo_root": str(REPO_ROOT),
        "science_root": str(SCIENCE_ROOT),
        "science_root_exists": SCIENCE_ROOT.exists(),
        "archive_root": str(ARCHIVE_ROOT),
        "archive_root_exists": ARCHIVE_ROOT.exists(),
        "paper_dir": str(PAPER_DIR),
        "writer_model": WRITER_MODEL,
        "embed_model": EMBED_MODEL,
        "n_cores": N_CORES,
        "worker_processes": WORKER_PROCESSES,
        "phase3_reports": str(find_data_file(*PHASE3_REPORTS)),
        "md_trajectory": str(find_data_file(*MD_TRAJECTORY)),
    }


if __name__ == "__main__":  # pragma: no cover - diagnostic helper
    import json

    print(json.dumps(describe(), indent=2))
