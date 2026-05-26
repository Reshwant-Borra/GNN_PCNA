"""Tests for InfrastructureHealer — self-healing scaffolds."""
from __future__ import annotations

from pathlib import Path

import pytest

from research_os.autonomous.healer import HealReport, InfrastructureHealer, MissingItem


def test_detect_missing_compute_intent_modules(tmp_path: Path):
    (tmp_path / "agents").mkdir()
    (tmp_path / "agents" / "orchestrator.py").write_text(
        '"""fake."""\nimport agents.pcna_crawler\n', encoding="utf-8",
    )
    healer = InfrastructureHealer(tmp_path)
    report = healer.detect()
    paths = {i.path for i in report.detected}
    assert "agents/pcna_crawler.py" in paths


def test_detect_missing_memory_files(tmp_path: Path):
    healer = InfrastructureHealer(tmp_path)
    report = healer.detect()
    # Memory dir doesn't exist; should flag all canonical files.
    mem_items = [i for i in report.detected if i.kind == "memory"]
    assert len(mem_items) >= 1


def test_heal_memory_defers_to_bootstrap(tmp_path: Path):
    healer = InfrastructureHealer(tmp_path)
    item = MissingItem(path="research_os_memory/PROJECT_CANONICAL_STATUS.md",
                        kind="memory", severity="high")
    result = healer.heal_one(item)
    assert result.repaired is False
    assert result.pending_human is True
    assert "bootstrap" in result.error.lower()


def test_heal_module_scaffolds_under_safe_dir(tmp_path: Path):
    # Drop a fake compute orchestrator so detection fires.
    (tmp_path / "agents").mkdir()
    (tmp_path / "agents" / "orchestrator.py").write_text(
        "import agents.pcna_crawler\n", encoding="utf-8",
    )
    healer = InfrastructureHealer(tmp_path)
    detect = healer.detect()
    heal = healer.heal_all(detect, dry_run=False)
    # The pcna_crawler scaffold should be written.
    scaffolded = tmp_path / "agents" / "pcna_crawler.py"
    assert scaffolded.exists()
    assert "Placeholder scaffolded" in scaffolded.read_text(encoding="utf-8")
    # And a corresponding test should exist.
    smoke = tmp_path / "tests" / "test_placeholder_pcna_crawler.py"
    assert smoke.exists()


def test_heal_dry_run_does_not_write(tmp_path: Path):
    (tmp_path / "agents").mkdir()
    (tmp_path / "agents" / "orchestrator.py").write_text(
        "import agents.pcna_crawler\n", encoding="utf-8",
    )
    healer = InfrastructureHealer(tmp_path)
    healer.heal_all(dry_run=True)
    assert not (tmp_path / "agents" / "pcna_crawler.py").exists()


def test_heal_existing_target_is_no_op(tmp_path: Path):
    (tmp_path / "agents").mkdir()
    (tmp_path / "agents" / "orchestrator.py").write_text(
        "import agents.pcna_crawler\n", encoding="utf-8",
    )
    target = tmp_path / "agents" / "pcna_crawler.py"
    target.write_text("# real content\n", encoding="utf-8")
    healer = InfrastructureHealer(tmp_path)
    item = MissingItem(path="agents/pcna_crawler.py", kind="module")
    result = healer.heal_one(item)
    assert result.repaired is False
    assert "already exists" in result.error
    assert target.read_text(encoding="utf-8") == "# real content\n"
