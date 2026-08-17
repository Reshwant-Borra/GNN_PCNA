"""Register generated figures and the paper draft as ResearchOS artifacts.

Writing provenance entries into ``research_os_registries/artifact_registry.json``
is what lets the existing VisualEvidence/FIGURE gate recognise the figures and
the PaperClaim/CLAIM gate recognise the draft. Each entry records the command
that produced it, its inputs (the real data sources), and the reviewer question
/ claim it supports. Idempotent: a path already registered is skipped.
"""
from __future__ import annotations

import json
import platform
from pathlib import Path
from typing import List

from paper_engine import config


def _store():
    from research_os.registries.store import RegistryStore, ensure_registries_initialized

    store = RegistryStore(config.REPO_ROOT / "research_os_registries")
    ensure_registries_initialized(store)
    return store


def _git_state():
    """Current commit + dirty flag, for artifact provenance (empty if no git)."""
    try:
        from research_os.tools.git import capture_git_state

        gs = capture_git_state(config.REPO_ROOT)
        return (gs.commit, gs.dirty) if gs.inside_repo else ("", False)
    except Exception:
        return ("", False)


def _backfill_provenance(store, rel_path: str, commit: str, dirty: bool) -> None:
    """Add git provenance to an already-registered artifact that lacks it."""
    if not commit:
        return
    for ent in store.find("artifact_registry", lambda e: e.get("path") == rel_path):
        if not ent.get("git_commit"):
            try:
                store.update("artifact_registry", ent["artifact_id"],
                             {"git_commit": commit, "git_dirty": dirty})
            except Exception:
                pass


def _rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(config.REPO_ROOT).as_posix()
    except ValueError:
        return str(path)


def _already(store, rel_path: str) -> bool:
    return bool(store.find("artifact_registry", lambda e: e.get("path") == rel_path))


def register_figures() -> List[str]:
    """Register every figure in the figures manifest. Returns new artifact IDs."""
    manifest_path = config.FIGURES_DIR / "figures_manifest.json"
    if not manifest_path.exists():
        return []
    figures = json.loads(manifest_path.read_text(encoding="utf-8")).get("figures", [])
    store = _store()
    commit, dirty = _git_state()
    new_ids: List[str] = []
    for fig in figures:
        path = Path(fig["path"])
        if not path.exists():
            continue
        rel = _rel(path)
        if _already(store, rel):
            _backfill_provenance(store, rel, commit, dirty)
            continue
        note = (f"{fig.get('title','')} | answers: {fig.get('reviewer_question','')} "
                f"| {fig.get('caption','')}")[:1000]
        entry = {
            "path": rel,
            "artifact_type": "figure",
            "status": "draft",
            "created_by_agent": "paper_engine.figures",
            "machine": platform.node(),
            "git_commit": commit,
            "git_dirty": dirty,
            "command": fig.get("command", ""),
            "inputs": [Path(s).name for s in fig.get("data_sources", [])],
            "notes": note,
        }
        try:
            new_ids.append(store.append("artifact_registry", entry))
        except Exception as exc:  # never abort the whole batch on one bad entry
            print(f"[register] skipped {rel}: {exc}")
    return new_ids


def register_md_results() -> str:
    """Register the Phase-5 MD results doc as an md_analysis artifact (research bank)."""
    doc = config.find_data_file("outputs/phase5_md/PHASE5_MD_RESULTS.md")
    if doc is None:
        return ""
    store = _store()
    commit, dirty = _git_state()
    rel = _rel(doc)
    if _already(store, rel):
        _backfill_provenance(store, rel, commit, dirty)
        existing = store.find("artifact_registry", lambda e: e.get("path") == rel)
        return existing[0].get("artifact_id", "")
    entry = {
        "path": rel,
        "artifact_type": "md_analysis",
        "status": "current",
        "created_by_agent": "phase5_md",
        "machine": platform.node(),
        "git_commit": commit,
        "git_dirty": dirty,
        "command": "MD triage: 1AXC PCNA apo-from-p21, 25 ns, OpenMM/AMBER14/TIP3P",
        "notes": "25 ns exploratory MD (1AXC). Stable trimer; GNN candidate windows "
                 "remained rigid (RMSF 0.59-0.65x reference); no sustained pocket opening. "
                 "Valid negative/inconclusive result; no validated-site claims supported.",
    }
    try:
        return store.append("artifact_registry", entry)
    except Exception as exc:
        print(f"[register] md results skipped: {exc}")
        return ""


def register_paper_draft(docx_path: Path, md_path: Path) -> str:
    """Register the manuscript draft (markdown twin) as a paper_draft artifact."""
    store = _store()
    commit, dirty = _git_state()
    rel = _rel(Path(md_path))
    if _already(store, rel):
        _backfill_provenance(store, rel, commit, dirty)
        existing = store.find("artifact_registry", lambda e: e.get("path") == rel)
        return existing[0].get("artifact_id", "")
    entry = {
        "path": rel,
        "artifact_type": "paper_draft",
        "status": "draft",
        "created_by_agent": "paper_engine.manuscript",
        "machine": platform.node(),
        "git_commit": commit,
        "git_dirty": dirty,
        "command": "python -m research_os paper",
        "notes": (f"Auto-generated competition draft (DOCX: {_rel(Path(docx_path))}). "
                  "Validation-only; test set not evaluated; requires human review."),
    }
    try:
        return store.append("artifact_registry", entry)
    except Exception as exc:
        print(f"[register] paper draft skipped: {exc}")
        return ""
