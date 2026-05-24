from __future__ import annotations

import json
from pathlib import Path

from agents.manager.pipeline_helpers import manager_helpers


def test_run_turn_start_call_writes_role_outputs(tmp_path, monkeypatch) -> None:
    repo_root = tmp_path / "repo"
    src_root = repo_root / "src" / "agents"

    for path in [
        src_root / "captain" / "prompts",
        src_root / "first_mate" / "prompts",
        src_root / "engineer" / "prompts",
        src_root / "captain",
        src_root / "first_mate",
        src_root / "engineer",
        src_root / "common",
        src_root / "manager" / "contexts",
        src_root / "manager" / "outputs",
    ]:
        path.mkdir(parents=True, exist_ok=True)

    (src_root / "captain" / "prompts" / "1_analysis.md").write_text("captain prompt", encoding="utf-8")
    (src_root / "first_mate" / "prompts" / "1_strategy_lock.md").write_text("first mate prompt", encoding="utf-8")
    (src_root / "engineer" / "prompts" / "1_board_analysis.md").write_text("engineer prompt", encoding="utf-8")

    (src_root / "manager" / "contexts" / "captain_blue.md").write_text("captain context", encoding="utf-8")
    (src_root / "manager" / "contexts" / "first_mate_blue.md").write_text("first mate context", encoding="utf-8")
    (src_root / "manager" / "contexts" / "engineer_blue.md").write_text("engineer context", encoding="utf-8")

    (src_root / "captain" / "memory.md").write_text("captain memory", encoding="utf-8")
    (src_root / "first_mate" / "memory.md").write_text("first mate memory", encoding="utf-8")
    (src_root / "engineer" / "memory.md").write_text("engineer memory", encoding="utf-8")
    (src_root / "common" / "master_memory.md").write_text("master memory", encoding="utf-8")

    original_captain_memory = (src_root / "captain" / "memory.md").read_text(encoding="utf-8")
    original_first_mate_memory = (src_root / "first_mate" / "memory.md").read_text(encoding="utf-8")
    original_engineer_memory = (src_root / "engineer" / "memory.md").read_text(encoding="utf-8")
    original_master_memory = (src_root / "common" / "master_memory.md").read_text(encoding="utf-8")

    fake_file = src_root / "manager" / "pipeline_helpers" / "manager_helpers.py"
    fake_file.parent.mkdir(parents=True, exist_ok=True)
    fake_file.write_text("", encoding="utf-8")
    monkeypatch.setattr(manager_helpers, "__file__", str(fake_file))

    calls: list[dict[str, str]] = []

    def fake_call_agent_activity_with_context(**kwargs):
        calls.append({
            "role": str(kwargs["role"]),
            "prompt": str(kwargs["prompt"]),
            "context": str(kwargs["context"]),
        })
        output_text = (
            "## Memory Update\n"
            f"{kwargs['role']} memory update\n\n"
            "## Master Memory Update\n"
            f"{kwargs['role']} master update\n"
        )
        return type("Response", (), {"text": output_text})()

    def fake_read_role_memory(role) -> str:
        return (src_root / role.name.lower() / "memory.md").read_text(encoding="utf-8")

    def fake_update_master_memory(section: str, content: str) -> str:
        master_path = src_root / "common" / "master_memory.md"
        current = master_path.read_text(encoding="utf-8")
        new_text = f"{current}\n## {section}\n\n{content}".strip()
        master_path.write_text(new_text, encoding="utf-8")
        return new_text

    monkeypatch.setattr(manager_helpers, "call_agent_activity_with_context", fake_call_agent_activity_with_context)
    monkeypatch.setattr(manager_helpers, "read_role_memory", fake_read_role_memory)
    monkeypatch.setattr(manager_helpers, "update_master_memory", fake_update_master_memory)

    bundle = {
        "team": "BLUE",
        "turn": 12,
        "roles": {
            "CAPTAIN": {},
            "FIRST_MATE": {},
            "ENGINEER": {},
        },
    }

    results = manager_helpers.run_turn_start_call(bundle)
    manager_helpers.update_memory(manager=None, context_report={})

    assert set(results) == {"CAPTAIN", "FIRST_MATE", "ENGINEER"}
    assert len(calls) == 3

    outputs_dir = src_root / "manager" / "outputs"
    assert list(outputs_dir.iterdir()) == []

    assert (src_root / "captain" / "memory.md").read_text(encoding="utf-8") != original_captain_memory
    assert (src_root / "first_mate" / "memory.md").read_text(encoding="utf-8") != original_first_mate_memory
    assert (src_root / "engineer" / "memory.md").read_text(encoding="utf-8") != original_engineer_memory
    assert (src_root / "common" / "master_memory.md").read_text(encoding="utf-8") != original_master_memory

    assert {entry["role"] for entry in calls} == {"CAPTAIN", "FIRST_MATE", "ENGINEER"}
    assert any("captain context" in entry["context"] for entry in calls)
    assert any("first mate context" in entry["context"] for entry in calls)
    assert any("engineer context" in entry["context"] for entry in calls)