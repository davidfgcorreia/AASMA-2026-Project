from __future__ import annotations

import json

from captain_sonar.event_log import EventLogger


def test_turn_start_logging_writes_one_jsonl_record(tmp_path):
    log_path = tmp_path / "game_log.jsonl"
    logger = EventLogger(str(log_path), turn_start_log=True)

    logger.log_turn_start(3, "BLUE", "move")

    lines = log_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    assert json.loads(lines[0]) == {
        "type": "turn_start",
        "turn": 3,
        "team": "BLUE",
        "phase": "move",
    }


def test_possible_actions_logging_writes_to_separate_file(tmp_path):
    log_path = tmp_path / "game_log.jsonl"
    possible_path = tmp_path / "game_possible.jsonl"
    logger = EventLogger(str(log_path), possible_actions_path=str(possible_path))

    logger.log_possible_actions(1, "RED", "move", "captain", ["MOVE", "SURFACE"])

    lines = possible_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    assert json.loads(lines[0]) == {
        "type": "possible_actions",
        "turn": 1,
        "team": "RED",
        "phase": "move",
        "role": "captain",
        "possible_actions": ["MOVE", "SURFACE"],
    }


def test_team_view_logging_writes_to_state_log(tmp_path):
    state_path = tmp_path / "game_state_snapshots.jsonl"
    logger = EventLogger(str(tmp_path / "game_log.jsonl"), state_path=str(state_path))

    logger.log_team_view(2, "RED", {"team": "RED", "turn": 2, "own_mines": []})

    lines = state_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    assert json.loads(lines[0]) == {
        "type": "team_view",
        "turn": 2,
        "team": "RED",
        "own_mines": [],
    }