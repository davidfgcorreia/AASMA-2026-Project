from __future__ import annotations

from agents.base import AgentRole
from agents.common.functions import read_role_memory


def test_read_role_memory_prefers_prompt_markdown(tmp_path) -> None:
    root = tmp_path / "agents"
    captain_dir = root / "captain"
    captain_dir.mkdir(parents=True)
    (captain_dir / "prompt.md").write_text("# Captain Prompt\n", encoding="utf-8")
    (captain_dir / "memory.md").write_text("# Captain Memory\n", encoding="utf-8")

    assert read_role_memory(AgentRole.CAPTAIN, root) == "# Captain Prompt\n"