from __future__ import annotations

from agents.base import AgentRole
from agents.common.functions import read_common_context, read_role_memory


def test_common_context_exists() -> None:
    context = read_common_context()
    assert "Captain Sonar Shared Game Rules Context" in context


def test_role_context_preferred_over_prompt(tmp_path) -> None:
    root = tmp_path / "agents"
    captain_dir = root / "captain"
    captain_dir.mkdir(parents=True)
    (captain_dir / "context.md").write_text("# Captain Context\n", encoding="utf-8")
    (captain_dir / "prompt.md").write_text("# Captain Prompt\n", encoding="utf-8")

    assert read_role_memory(AgentRole.CAPTAIN, root) == "# Captain Context\n"