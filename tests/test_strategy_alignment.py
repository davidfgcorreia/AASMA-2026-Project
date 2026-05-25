from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from agents.manager.pipeline_helpers import manager_helpers


def test_run_strategy_alignment_updates_all_roles_with_one_call(monkeypatch) -> None:
    calls = {"count": 0}

    captain_path = Path("/home/david/documents/mestrado/AASMA/src/agents/captain/strategy.md")
    first_mate_path = Path("/home/david/documents/mestrado/AASMA/src/agents/first_mate/strategy.md")
    engineer_path = Path("/home/david/documents/mestrado/AASMA/src/agents/engineer/strategy.md")

    original_captain = captain_path.read_text(encoding="utf-8")
    original_first_mate = first_mate_path.read_text(encoding="utf-8")
    original_engineer = engineer_path.read_text(encoding="utf-8")

    def fake_call_agent_activity_with_context(**kwargs):
        calls["count"] += 1
        payload = {
            "CAPTAIN": "- Move safely while preserving tactical flexibility.",
            "FIRST_MATE": "- Charge Sonar first, then keep Silence ready.",
            "ENGINEER": "- Prefer green and yellow buttons; repair if red or radioactive remain.",
        }
        return SimpleNamespace(text=json.dumps(payload))

    monkeypatch.setattr(manager_helpers, "call_agent_activity_with_context", fake_call_agent_activity_with_context)

    try:
        result = manager_helpers.run_strategy_alignment(
            {
                "team": "BLUE",
                "turn": 3,
                "roles": {
                    "CAPTAIN": {},
                    "FIRST_MATE": {},
                    "ENGINEER": {},
                },
            }
        )

        assert calls["count"] == 1
        assert result["updated"] is True
        assert set(result["roles"].keys()) == {"CAPTAIN", "FIRST_MATE", "ENGINEER"}

        assert captain_path.read_text(encoding="utf-8").count("## Strategy to follow:") == 1
        assert first_mate_path.read_text(encoding="utf-8").count("## Strategy to follow:") == 1
        assert engineer_path.read_text(encoding="utf-8").count("## Strategy to follow:") == 1

        output_path = Path(result["output_path"])
        assert output_path.exists()
        assert json.loads(output_path.read_text(encoding="utf-8")) == {
            "CAPTAIN": "- Move safely while preserving tactical flexibility.",
            "ENGINEER": "- Prefer green and yellow buttons; repair if red or radioactive remain.",
            "FIRST_MATE": "- Charge Sonar first, then keep Silence ready.",
        }
    finally:
        captain_path.write_text(original_captain, encoding="utf-8")
        first_mate_path.write_text(original_first_mate, encoding="utf-8")
        engineer_path.write_text(original_engineer, encoding="utf-8")
        result_path = Path("/home/david/documents/mestrado/AASMA/src/agents/manager/outputs/strategy_alignment_blue_turn_3.json")
        if result_path.exists():
            result_path.unlink()