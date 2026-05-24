from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from agents.base import AgentRole
from agents.manager.pipeline_helpers.manager_helpers import build_turn_start_context_bundle


def test_build_turn_start_context_bundle_uses_real_repository_files() -> None:
    manager = SimpleNamespace(
        _active_roles={
            AgentRole.CAPTAIN,
            AgentRole.FIRST_MATE,
            AgentRole.ENGINEER,
            AgentRole.RADIO_OPERATOR,
        }
    )

    context_report = {
        "team_view": {},
        "round_type": "normal",
        "source": "api",
    }

    bundle = build_turn_start_context_bundle(manager, context_report)

    common_root = Path("/home/david/documents/mestrado/AASMA/src/agents")
    common_dir = common_root / "common"

    assert bundle["play_context"] == (common_dir / "play_context.md").read_text(encoding="utf-8")
    assert bundle["master_memory"] == (common_dir / "master_memory.md").read_text(encoding="utf-8")

    for role in (AgentRole.CAPTAIN, AgentRole.FIRST_MATE, AgentRole.ENGINEER, AgentRole.RADIO_OPERATOR):
        role_dir = common_root / role.name.lower()
        role_files = bundle["roles"][role.value]
        assert role_files["context"] == (role_dir / "context.md").read_text(encoding="utf-8")
        strategy_path = role_dir / "strategy.md"
        memory_path = role_dir / "memory.md"
        assert role_files["strategy"] == (strategy_path.read_text(encoding="utf-8") if strategy_path.exists() else "")
        assert role_files["memory"] == (memory_path.read_text(encoding="utf-8") if memory_path.exists() else "")
        prompt_path = role_dir / "prompt.md"
        if prompt_path.exists():
            assert role_files["prompt"] == prompt_path.read_text(encoding="utf-8")
        else:
            assert role_files["prompt"] == ""
