from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import cast

from captain_sonar.game_state import GameState
from agents.manager.pipeline_helpers import iteration_orchestrator


def test_run_iteration_cycle_runs_strategy_alignment_every_3_turns(monkeypatch) -> None:
    manager = SimpleNamespace()
    state = cast(GameState, SimpleNamespace(turn=3))
    context_report = {"team_view": {"turn": 3}}

    calls = {
        "build": 0,
        "align": 0,
        "discussion": 0,
    }

    def fake_build_turn_start_context_bundle(_manager, _context_report):
        calls["build"] += 1
        return {"team": "BLUE", "turn": 3, "roles": {"CAPTAIN": {}, "FIRST_MATE": {}, "ENGINEER": {}}}

    def fake_run_strategy_alignment(_bundle):
        calls["align"] += 1
        return {"updated": True}

    def fake_run_discussion_call(_bundle):
        calls["discussion"] += 1
        return {}

    monkeypatch.setattr(iteration_orchestrator, "build_turn_start_context_bundle", fake_build_turn_start_context_bundle)
    monkeypatch.setattr(iteration_orchestrator, "run_strategy_alignment", fake_run_strategy_alignment)
    monkeypatch.setattr(iteration_orchestrator, "run_discussion_call", fake_run_discussion_call)

    iteration_orchestrator.run_iteration_cycle(manager, state, max_iterations=2, context_report=context_report)

    assert calls["align"] == 1
    assert calls["discussion"] == 2
    # One bundle build for strategy alignment + one per iteration.
    assert calls["build"] == 3
    assert context_report.get("strategy_alignment") == {"updated": True}


def test_run_iteration_cycle_skips_strategy_alignment_other_turns(monkeypatch) -> None:
    manager = SimpleNamespace()
    state = cast(GameState, SimpleNamespace(turn=4))
    context_report = {"team_view": {"turn": 4}}

    calls = {
        "build": 0,
        "align": 0,
        "discussion": 0,
    }

    def fake_build_turn_start_context_bundle(_manager, _context_report):
        calls["build"] += 1
        return {"team": "BLUE", "turn": 4, "roles": {"CAPTAIN": {}, "FIRST_MATE": {}, "ENGINEER": {}}}

    def fake_run_strategy_alignment(_bundle):
        calls["align"] += 1
        return {"updated": True}

    def fake_run_discussion_call(_bundle):
        calls["discussion"] += 1
        return {}

    monkeypatch.setattr(iteration_orchestrator, "build_turn_start_context_bundle", fake_build_turn_start_context_bundle)
    monkeypatch.setattr(iteration_orchestrator, "run_strategy_alignment", fake_run_strategy_alignment)
    monkeypatch.setattr(iteration_orchestrator, "run_discussion_call", fake_run_discussion_call)

    iteration_orchestrator.run_iteration_cycle(manager, state, max_iterations=2, context_report=context_report)

    assert calls["align"] == 0
    assert calls["discussion"] == 2
    assert calls["build"] == 2
    assert "strategy_alignment" not in context_report


def test_run_iteration_cycle_stops_early_when_all_support_stop_yes(monkeypatch, tmp_path) -> None:
    manager = SimpleNamespace()
    state = cast(GameState, SimpleNamespace(turn=1))
    context_report = {"team_view": {"turn": 1}}

    calls = {
        "build": 0,
        "discussion": 0,
    }

    def fake_build_turn_start_context_bundle(_manager, _context_report):
        calls["build"] += 1
        return {"team": "BLUE", "turn": 1, "roles": {"CAPTAIN": {}, "FIRST_MATE": {}, "ENGINEER": {}}}

    def fake_run_discussion_call(bundle):
        calls["discussion"] += 1
        results = {}
        for role_name in bundle["roles"]:
            output_path = tmp_path / f"{role_name.lower()}_blue_turn_1.md"
            output_path.write_text(
                "\n".join([
                    "## Memory Update",
                    "Done.",
                    "",
                    "## Master Memory Update",
                    "Done.",
                    "",
                    "## suport stop",
                    "yes",
                ]),
                encoding="utf-8",
            )
            results[role_name] = {"output_path": str(output_path), "output": output_path.read_text(encoding="utf-8")}
        return results

    monkeypatch.setattr(iteration_orchestrator, "build_turn_start_context_bundle", fake_build_turn_start_context_bundle)
    monkeypatch.setattr(iteration_orchestrator, "run_discussion_call", fake_run_discussion_call)
    monkeypatch.setattr(iteration_orchestrator, "update_memory", lambda *_args, **_kwargs: None)

    iteration_orchestrator.run_iteration_cycle(manager, state, max_iterations=3, context_report=context_report)

    assert calls["discussion"] == 1
    assert calls["build"] == 1
    assert context_report.get("early_stop") is True
