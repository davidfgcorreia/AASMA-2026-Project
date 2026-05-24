from __future__ import annotations

from pathlib import Path

from agents.base import AgentRole
from agents.manager.pipeline_helpers import manager_helpers


def test_update_memory_applies_output_files_and_clears_outputs(tmp_path, monkeypatch) -> None:
    repo_root = tmp_path / "repo"
    agents_root = repo_root / "src" / "agents"
    outputs_dir = agents_root / "manager" / "outputs"

    for role_name in ["captain", "first_mate", "engineer"]:
        role_dir = agents_root / role_name
        role_dir.mkdir(parents=True, exist_ok=True)
        (role_dir / "memory.md").write_text(f"{role_name} existing memory", encoding="utf-8")

    common_dir = agents_root / "common"
    common_dir.mkdir(parents=True, exist_ok=True)
    master_memory_path = common_dir / "master_memory.md"
    master_memory_path.write_text("shared existing memory", encoding="utf-8")

    original_captain_memory = (agents_root / "captain" / "memory.md").read_text(encoding="utf-8")
    original_first_mate_memory = (agents_root / "first_mate" / "memory.md").read_text(encoding="utf-8")
    original_engineer_memory = (agents_root / "engineer" / "memory.md").read_text(encoding="utf-8")
    original_master_memory = master_memory_path.read_text(encoding="utf-8")

    outputs_dir.mkdir(parents=True, exist_ok=True)
    (outputs_dir / "captain_blue_turn_12.md").write_text(
        """## Memory Update
Captain note for turn 12.

## Master Memory Update
Shared captain note for turn 12.
""",
        encoding="utf-8",
    )
    (outputs_dir / "first_mate_blue_turn_12.md").write_text(
        """## Memory Update
First mate note for turn 12.

## Master Memory Update
Shared first mate note for turn 12.
""",
        encoding="utf-8",
    )
    (outputs_dir / "engineer_blue_turn_12.md").write_text(
        """## Memory Update
Engineer note for turn 12.

## Master Memory Update
Shared engineer note for turn 12.
""",
        encoding="utf-8",
    )

    fake_helpers_path = agents_root / "manager" / "pipeline_helpers" / "manager_helpers.py"
    fake_helpers_path.parent.mkdir(parents=True, exist_ok=True)
    fake_helpers_path.write_text("", encoding="utf-8")
    monkeypatch.setattr(manager_helpers, "__file__", str(fake_helpers_path))

    def fake_read_role_memory(role: AgentRole) -> str:
        return (agents_root / role.name.lower() / "memory.md").read_text(encoding="utf-8")

    def fake_update_master_memory(section: str, content: str) -> str:
        current = master_memory_path.read_text(encoding="utf-8")
        new_text = f"{current}\n## {section}\n\n{content}".strip()
        master_memory_path.write_text(new_text, encoding="utf-8")
        return new_text

    monkeypatch.setattr(manager_helpers, "read_role_memory", fake_read_role_memory)
    monkeypatch.setattr(manager_helpers, "update_master_memory", fake_update_master_memory)

    manager_helpers.update_memory(manager=None, context_report={})

    assert (agents_root / "captain" / "memory.md").read_text(encoding="utf-8") != original_captain_memory
    assert (agents_root / "first_mate" / "memory.md").read_text(encoding="utf-8") != original_first_mate_memory
    assert (agents_root / "engineer" / "memory.md").read_text(encoding="utf-8") != original_engineer_memory
    master_memory_text = master_memory_path.read_text(encoding="utf-8")
    assert master_memory_text != original_master_memory
    assert list(outputs_dir.iterdir()) == []