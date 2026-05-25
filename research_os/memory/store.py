"""Markdown memory store.

Canonical markdown files live in `research_os_memory/`. Each file starts with
a standard header:

    # <Title>

    Last updated: <ISO timestamp>
    Updated by: <agent or human>
    Status: current|needs_review|stale

The store provides:

- `read(name)` / `read_all()` — load files into memory
- `propose_update(...)` — emit a structured `MemoryUpdateProposal`
- `apply_memory_update(...)` — actually write to disk after validation

Agents never write canonical files directly; they always go through this layer
so the Orchestrator and Contradiction Agent can intercept changes.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from research_os.schemas.vocab import UPDATE_TYPES, require_value


CANONICAL_FILES = (
    "PROJECT_CANONICAL_STATUS.md",
    "CURRENT_CLAIMS.md",
    "KNOWN_BUGS_AND_RISKS.md",
    "HUMAN_DECISIONS.md",
    "VALIDATION_STATUS.md",
    "DATASET_REGISTRY.md",
    "MODEL_REGISTRY.md",
    "COMPUTE_REGISTRY.md",
    "REVIEWER_RISK_REGISTER.md",
)

_DEFAULT_TITLE = {
    "PROJECT_CANONICAL_STATUS.md": "Project Canonical Status",
    "CURRENT_CLAIMS.md": "Current Claims",
    "KNOWN_BUGS_AND_RISKS.md": "Known Bugs and Risks",
    "HUMAN_DECISIONS.md": "Human Decisions",
    "VALIDATION_STATUS.md": "Validation Status",
    "DATASET_REGISTRY.md": "Dataset Registry",
    "MODEL_REGISTRY.md": "Model Registry",
    "COMPUTE_REGISTRY.md": "Compute Registry",
    "REVIEWER_RISK_REGISTER.md": "Reviewer Risk Register",
}

_HEADER_RE = re.compile(
    r"^Last updated:\s*(?P<updated>.+)$\s*"
    r"^Updated by:\s*(?P<by>.+)$\s*"
    r"^Status:\s*(?P<status>current|needs_review|stale)$",
    re.MULTILINE,
)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass
class MemoryFile:
    name: str
    title: str
    last_updated: str
    updated_by: str
    status: str  # current | needs_review | stale
    body: str = ""
    path: Optional[Path] = None

    def to_markdown(self) -> str:
        return (
            f"# {self.title}\n\n"
            f"Last updated: {self.last_updated}\n"
            f"Updated by: {self.updated_by}\n"
            f"Status: {self.status}\n\n"
            f"{self.body.rstrip()}\n"
        )


@dataclass
class MemoryUpdateProposal:
    """Structured proposal an agent emits when it wants to change canonical memory."""

    target_file: str
    update_type: str  # one of UPDATE_TYPES
    summary: str
    proposed_by: str = ""
    new_body: Optional[str] = None
    append_section: Optional[str] = None  # markdown to append
    section_heading: Optional[str] = None  # heading the new content should live under
    evidence: List[str] = field(default_factory=list)
    affected_claim_ids: List[str] = field(default_factory=list)
    affected_artifact_ids: List[str] = field(default_factory=list)
    requires_human_approval: bool = False
    reason_human_approval_required: str = ""

    def validate(self) -> None:
        require_value("MemoryUpdateProposal.update_type", self.update_type, UPDATE_TYPES)
        if self.target_file not in CANONICAL_FILES:
            raise ValueError(
                f"target_file {self.target_file!r} is not a canonical memory file"
            )
        if self.requires_human_approval and not self.reason_human_approval_required:
            raise ValueError(
                "requires_human_approval is True but reason_human_approval_required is empty"
            )
        if self.new_body is None and self.append_section is None:
            raise ValueError(
                "MemoryUpdateProposal needs either new_body or append_section"
            )

    def to_dict(self) -> Dict[str, object]:
        return asdict(self)


class MemoryStore:
    def __init__(self, base_dir: Path | str):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def path_for(self, name: str) -> Path:
        if name not in CANONICAL_FILES:
            raise ValueError(
                f"{name!r} is not a canonical memory file. "
                f"Allowed: {CANONICAL_FILES}"
            )
        return self.base_dir / name

    def exists(self, name: str) -> bool:
        return self.path_for(name).exists()

    def read(self, name: str) -> MemoryFile:
        path = self.path_for(name)
        if not path.exists():
            raise FileNotFoundError(path)
        text = path.read_text(encoding="utf-8")
        title_match = re.match(r"^#\s*(.+)$", text, re.MULTILINE)
        title = title_match.group(1).strip() if title_match else _DEFAULT_TITLE[name]
        header_match = _HEADER_RE.search(text)
        if header_match:
            last_updated = header_match.group("updated").strip()
            updated_by = header_match.group("by").strip()
            status = header_match.group("status").strip()
            body_start = header_match.end()
            body = text[body_start:].lstrip("\n")
        else:
            last_updated = ""
            updated_by = "unknown"
            status = "needs_review"
            body = text
        return MemoryFile(
            name=name,
            title=title,
            last_updated=last_updated,
            updated_by=updated_by,
            status=status,
            body=body,
            path=path,
        )

    def read_all(self) -> Dict[str, MemoryFile]:
        out: Dict[str, MemoryFile] = {}
        for name in CANONICAL_FILES:
            if self.exists(name):
                out[name] = self.read(name)
        return out

    def write(self, mem: MemoryFile, updated_by: str) -> None:
        mem.last_updated = _utc_now_iso()
        mem.updated_by = updated_by
        target = self.path_for(mem.name)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(mem.to_markdown(), encoding="utf-8")


_STARTER_CONTENT: Dict[str, str] = {
    "PROJECT_CANONICAL_STATUS.md": (
        "## Project goal\n\n"
        "GNN-PCNA + molecular-dynamics validation: identify candidate pocket-associated\n"
        "residues on PCNA, assess them with computational baselines and MD, and produce a\n"
        "manuscript whose claims are proportional to the evidence.\n\n"
        "## Current research question\n\n"
        "Can a leakage-clean GNN identify candidate AOH1996-associated pocket residues\n"
        "on PCNA that hold up under structural realism and MD analysis?\n\n"
        "## Current hypothesis\n\n"
        "There exists a pocket-associated residue region near known AOH1996 contacts\n"
        "that a GNN can flag with above-baseline performance under leakage-clean splits.\n\n"
        "## Current status summary\n\n"
        "Dataset status: see DATASET_REGISTRY.md (treat as needs_review).\n"
        "Model status: see MODEL_REGISTRY.md (treat as needs_review).\n"
        "Validation status: see VALIDATION_STATUS.md (treat as inconclusive by default).\n"
        "Paper status: drafting; claim wording governed by CURRENT_CLAIMS.md.\n\n"
        "## Current blockers\n\n"
        "- ResearchOS agents have not yet completed a clean full-audit pass.\n"
        "- All headline metrics, claims, and figures are pending independent verification.\n\n"
        "## Next steps\n\n"
        "1. Run `python -m research_os audit --repo .`.\n"
        "2. Triage findings.\n"
        "3. Re-run with corrected splits / regenerated artifacts as needed.\n"
    ),
    "CURRENT_CLAIMS.md": (
        "## Accepted claims\n\n"
        "(none yet — all candidate claims require ResearchOS sign-off)\n\n"
        "## Partially supported claims\n\n"
        "(none yet)\n\n"
        "## Hypothesis-generating claims\n\n"
        "- CLAIM-template: \"The GNN predicts a candidate pocket-associated residue\n"
        "  region near known AOH1996-associated residues on PCNA.\"\n\n"
        "## Unsupported claims\n\n"
        "(none yet)\n\n"
        "## Contradicted claims\n\n"
        "(none yet)\n\n"
        "## Allowed wording\n\n"
        "- \"candidate pocket-associated residue region\"\n"
        "- \"computationally predicted region\"\n"
        "- \"partially supported by structural proximity\"\n"
        "- \"requires further validation\"\n"
        "- \"MD under the tested conditions did not strongly support pocket opening\"\n\n"
        "## Disallowed wording\n\n"
        "- \"validated cryptic pocket\"\n"
        "- \"confirmed novel residues\"\n"
        "- \"MD proves opening\"\n"
        "- \"discovered binding site\"\n"
        "- \"generalizes broadly\"\n"
        "- \"experimentally validated\"\n"
        "- \"causal mechanism\"\n\n"
        "## Claims requiring human approval\n\n"
        "- Any upgrade above `moderately_supported`.\n"
        "- Any wording change that touches paper or abstract direction.\n"
    ),
    "KNOWN_BUGS_AND_RISKS.md": (
        "## Critical bugs\n\n"
        "(none recorded yet)\n\n"
        "## Open bugs\n\n"
        "(none recorded yet)\n\n"
        "## Resolved bugs\n\n"
        "(none recorded yet)\n\n"
        "## Scientific risks\n\n"
        "- Residue-level samples may be treated as protein-level samples — inflated n.\n"
        "- Small independent test set: AUROC fragile to single-protein swings.\n"
        "- Apo/holo leakage if ligand-bound structures appear in training.\n"
        "- Homology leakage if family-blocked split is missing.\n"
        "- MD stability may be misread as cryptic pocket opening.\n\n"
        "## Stale artifacts caused by bugs\n\n"
        "(none recorded yet)\n\n"
        "## Artifacts requiring regeneration\n\n"
        "(none recorded yet)\n"
    ),
    "HUMAN_DECISIONS.md": (
        "Append-only decision log. Decisions added via the Orchestrator only.\n\n"
        "## DEC-template\n\n"
        "- Date: <iso>\n"
        "- Decision maker: <name>\n"
        "- Request: <one-line request>\n"
        "- Options: <list>\n"
        "- Decision: <choice>\n"
        "- Rationale: <reasoning>\n"
        "- Evidence: <artifact/claim IDs>\n"
        "- Affected: <claim/artifact IDs>\n"
        "- Follow-up: <next steps>\n"
    ),
    "VALIDATION_STATUS.md": (
        "## Validation question\n\n"
        "Do candidate pocket-associated residues predicted by the GNN show:\n"
        "(a) structural proximity to known AOH1996 contacts,\n"
        "(b) physical plausibility (accessibility, clustering),\n"
        "(c) MD support for flexibility / pocket opening under tested conditions?\n\n"
        "## Structural evidence\n\n"
        "Pending Biological Realism Agent pass.\n\n"
        "## MD evidence\n\n"
        "Pending Validation Agent pass. Default classification: `inconclusive`.\n\n"
        "## Metrics used\n\n"
        "Pending Metrics Agent verification.\n\n"
        "## Evidence classification\n\n"
        "`inconclusive` until validation classifier runs.\n\n"
        "## Contradictions\n\n"
        "(none recorded yet)\n\n"
        "## Safe interpretation\n\n"
        "The GNN highlights a candidate region. MD has not been shown to validate cryptic\n"
        "pocket opening under the tested conditions.\n\n"
        "## Disallowed interpretation\n\n"
        "- \"MD validated the cryptic pocket\"\n"
        "- \"MD proves opening\"\n\n"
        "## Required follow-up\n\n"
        "- Run validation workflow.\n"
        "- Classify MD evidence explicitly.\n"
    ),
    "DATASET_REGISTRY.md": (
        "## Datasets in use\n\n"
        "Pending Dataset Integrity Agent intake.\n\n"
        "## Label definition\n\n"
        "Pending explicit documentation.\n\n"
        "## Missing-data policy\n\n"
        "Pending documentation.\n\n"
        "## Residue/chain mapping rules\n\n"
        "Pending documentation.\n\n"
        "## Split protocol\n\n"
        "Pending Leakage Agent approval.\n"
    ),
    "MODEL_REGISTRY.md": (
        "## Current canonical checkpoint\n\n"
        "(none accepted yet — Provenance + Leakage + Metrics gates must pass.)\n\n"
        "## Architecture\n\n"
        "Pending Model Training Agent registration.\n\n"
        "## Baselines\n\n"
        "Required: random, sequence-only, geometry-only, distance-to-known-pocket,\n"
        "logistic regression / random forest, conservation if available, fpocket if relevant.\n\n"
        "## Training history\n\n"
        "(none recorded yet)\n"
    ),
    "COMPUTE_REGISTRY.md": (
        "## Compute budget\n\n"
        "Pending Compute Planning Agent intake.\n\n"
        "## Approved expensive runs\n\n"
        "(none recorded yet — all MD / cloud runs require human approval.)\n\n"
        "## Failed / cancelled runs\n\n"
        "(none recorded yet)\n"
    ),
    "REVIEWER_RISK_REGISTER.md": (
        "## Open reviewer risks\n\n"
        "- How was homology leakage prevented?\n"
        "- How many independent test proteins exist?\n"
        "- Where is AUPRC?\n"
        "- Were baselines compared under the same split?\n"
        "- Does MD actually validate the exact claim?\n"
        "- Are novel residues experimentally supported?\n"
        "- Were old checkpoints regenerated after bug fixes?\n"
        "- Can the repo run from scratch?\n"
        "- Are skipped tests hiding failures?\n"
        "- Are claims proportional to evidence?\n\n"
        "## Mitigated reviewer risks\n\n"
        "(none recorded yet)\n"
    ),
}


def _starter_for(name: str) -> str:
    return _STARTER_CONTENT.get(name, "(pending agent intake)\n")


def ensure_memory_initialized(store: MemoryStore) -> None:
    """Create the 9 canonical files if missing."""
    for name in CANONICAL_FILES:
        if not store.exists(name):
            mem = MemoryFile(
                name=name,
                title=_DEFAULT_TITLE[name],
                last_updated=_utc_now_iso(),
                updated_by="research_os.bootstrap",
                status="needs_review",
                body=_starter_for(name),
            )
            store.path_for(name).write_text(mem.to_markdown(), encoding="utf-8")


def apply_memory_update(
    store: MemoryStore,
    proposal: MemoryUpdateProposal,
    applied_by: str,
) -> MemoryFile:
    """Apply an approved memory update. Raises if validation fails or human
    approval is required but missing."""
    proposal.validate()
    if proposal.requires_human_approval:
        raise PermissionError(
            f"Memory update for {proposal.target_file} requires human approval: "
            f"{proposal.reason_human_approval_required}"
        )
    mem = (
        store.read(proposal.target_file)
        if store.exists(proposal.target_file)
        else MemoryFile(
            name=proposal.target_file,
            title=_DEFAULT_TITLE[proposal.target_file],
            last_updated="",
            updated_by="",
            status="needs_review",
            body="",
        )
    )
    if proposal.new_body is not None:
        mem.body = proposal.new_body
    elif proposal.append_section is not None:
        if proposal.section_heading:
            mem.body = _replace_or_append_section(
                mem.body, proposal.section_heading, proposal.append_section.strip()
            )
        else:
            mem.body = f"{mem.body.rstrip()}\n\n{proposal.append_section.strip()}\n"
    mem.status = "current"
    store.write(mem, updated_by=applied_by)
    return mem


def _replace_or_append_section(body: str, heading: str, new_content: str) -> str:
    """If ``## heading`` exists in ``body``, replace its content with ``new_content``.
    Otherwise append a new section with that heading at the end."""
    pattern = re.compile(
        rf"(^##\s+{re.escape(heading)}\s*$)(?P<body>.*?)(?=^##\s|\Z)",
        re.IGNORECASE | re.MULTILINE | re.DOTALL,
    )
    if pattern.search(body):
        return pattern.sub(
            lambda m: f"{m.group(1)}\n\n{new_content}\n\n",
            body,
            count=1,
        )
    return f"{body.rstrip()}\n\n## {heading}\n\n{new_content}\n"


__all__ = [
    "CANONICAL_FILES",
    "MemoryFile",
    "MemoryStore",
    "MemoryUpdateProposal",
    "apply_memory_update",
    "ensure_memory_initialized",
]
