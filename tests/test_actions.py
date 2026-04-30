from captain_sonar.actions import Action, ActionType, validate_action


def test_move_requires_direction():
    action = Action(actor="BLUE", type=ActionType.MOVE, payload={})
    errors = validate_action(action)
    assert errors


def test_torpedo_requires_target():
    action = Action(actor="BLUE", type=ActionType.TORPEDO, payload={})
    errors = validate_action(action)
    assert errors


def test_silence_requires_steps():
    action = Action(actor="BLUE", type=ActionType.SILENCE, payload={"direction": "N"})
    errors = validate_action(action)
    assert errors


def test_drone_requires_sector():
    action = Action(actor="BLUE", type=ActionType.DRONE, payload={})
    errors = validate_action(action)
    assert errors
