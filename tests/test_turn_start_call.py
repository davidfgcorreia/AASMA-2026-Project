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
        payload = {
            "memory_update": f"{kwargs['role']} memory update",
            "master_memory_update": f"{kwargs['role']} master update",
        }
        return type("Response", (), {"text": json.dumps(payload)})()

    monkeypatch.setattr(manager_helpers, "call_agent_activity_with_context", fake_call_agent_activity_with_context)

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

    assert set(results) == {"CAPTAIN", "FIRST_MATE", "ENGINEER"}
    assert len(calls) == 3

    outputs_dir = src_root / "manager" / "outputs"
    expected_files = {
        "captain_blue_turn_12.md": "captain prompt",
        "first_mate_blue_turn_12.md": "first mate prompt",
        "engineer_blue_turn_12.md": "engineer prompt",
    }

    for file_name, prompt_text in expected_files.items():
        output_path = outputs_dir / file_name
        assert output_path.exists()
        saved_output = output_path.read_text(encoding="utf-8")
        assert saved_output.startswith('{"memory_update":')
        assert prompt_text in {entry["prompt"] for entry in calls}

    assert {entry["role"] for entry in calls} == {"CAPTAIN", "FIRST_MATE", "ENGINEER"}
    assert any("captain context" in entry["context"] for entry in calls)
    assert any("first mate context" in entry["context"] for entry in calls)
    assert any("engineer context" in entry["context"] for entry in calls)