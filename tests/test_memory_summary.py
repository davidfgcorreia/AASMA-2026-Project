from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from typing import cast

from captain_sonar.game_state import GameState

from agents.manager.pipeline_helpers import manager_api, manager_helpers


def test_summarize_memory_updates_all_files_from_one_llm_call(tmp_path, monkeypatch) -> None:
    repo_root = tmp_path / "repo"
    agents_root = repo_root / "src" / "agents"
    common_dir = agents_root / "common"
    manager_dir = agents_root / "manager" / "pipeline_helpers"

    for role_name in ["captain", "first_mate", "engineer"]:
        role_dir = agents_root / role_name
        role_dir.mkdir(parents=True, exist_ok=True)
        role_dir.joinpath("memory.md").write_text((f"{role_name} line\n" * 120), encoding="utf-8")

    common_dir.mkdir(parents=True, exist_ok=True)
    common_memory_path = common_dir / "master_memory.md"
    common_memory_path.write_text(("shared line\n" * 120), encoding="utf-8")

    fake_helpers_path = manager_dir / "manager_helpers.py"
    fake_helpers_path.parent.mkdir(parents=True, exist_ok=True)
    fake_helpers_path.write_text("", encoding="utf-8")
    monkeypatch.setattr(manager_helpers, "__file__", str(fake_helpers_path))

    calls = {"count": 0}

    def fake_call_agent_activity_with_context(**kwargs):
        calls["count"] += 1
        context_text = kwargs.get("context", "")
        if "# Memory Type: MASTER_MEMORY" in context_text:
            return SimpleNamespace(text="shared summary")
        if "# Memory Type: CAPTAIN_MEMORY" in context_text:
            return SimpleNamespace(text="captain summary")
        if "# Memory Type: FIRST_MATE_MEMORY" in context_text:
            return SimpleNamespace(text="first mate summary")
        return SimpleNamespace(text="engineer summary")

    monkeypatch.setattr(manager_helpers, "call_agent_activity_with_context", fake_call_agent_activity_with_context)
    monkeypatch.setattr(manager_helpers, "_load_memory_summary_prompt", lambda: "# Memory Summary\n")

    manager = SimpleNamespace(team="BLUE", _turn_id=12)
    result = manager_helpers.summarize_memory(manager, None)

    assert calls["count"] == 4
    assert result["summarized"] is True
    assert common_memory_path.read_text(encoding="utf-8").strip() == "shared summary"
    assert (agents_root / "captain" / "memory.md").read_text(encoding="utf-8").strip() == "captain summary"
    assert (agents_root / "first_mate" / "memory.md").read_text(encoding="utf-8").strip() == "first mate summary"
    assert (agents_root / "engineer" / "memory.md").read_text(encoding="utf-8").strip() == "engineer summary"

    assert json.loads(json.dumps(result["sections"])) == {
        "MASTER_MEMORY": str(common_memory_path),
        "CAPTAIN_MEMORY": str(agents_root / "captain" / "memory.md"),
        "FIRST_MATE_MEMORY": str(agents_root / "first_mate" / "memory.md"),
        "ENGINEER_MEMORY": str(agents_root / "engineer" / "memory.md"),
    }

    outputs_dir = agents_root / "manager" / "outputs"
    assert sorted(path.name for path in outputs_dir.iterdir()) == [
        "memory_summary_captain_memory_blue_turn_12.md",
        "memory_summary_engineer_memory_blue_turn_12.md",
        "memory_summary_first_mate_memory_blue_turn_12.md",
        "memory_summary_master_memory_blue_turn_12.md",
    ]


def test_collect_actions_calls_summarize_memory(monkeypatch) -> None:
    manager = SimpleNamespace(team="BLUE")
    state = cast(GameState, SimpleNamespace(turn=12))
    calls = {"summarize": 0}

    monkeypatch.setattr(manager_api, "run_turn_start_phase", lambda *_args, **_kwargs: {})
    monkeypatch.setattr(manager_api, "run_discussion_phase", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(manager_api, "run_finalization_phase", lambda *_args, **_kwargs: [])
    monkeypatch.setattr(manager_api, "run_send_phase", lambda *_args, **_kwargs: [])

    def fake_summarize_memory(*_args, **_kwargs):
        calls["summarize"] += 1
        return {"summarized": False, "reason": "below_threshold"}

    monkeypatch.setattr(manager_api, "summarize_memory", fake_summarize_memory)

    actions = manager_api.collect_actions(manager, state, "move")

    assert actions == []
    assert calls["summarize"] == 1