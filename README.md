# Captain Sonar Prototype

## Setup

1. Create and activate the virtual environment.
2. Install dependencies:

```
python -m pip install -r requirements.txt
```

## Run

```
python run_game.py
```

## Replay

```
python run_replay.py --log logs/game_log.jsonl
```

## Controls

- WASD: queue a MOVE action
- F: set SILENCE action (4 steps), then press WASD
- T: set TORPEDO action (uses cursor tile)
- O: set SONAR action (uses cursor tile)
- V: set DRONE action (uses cursor sector)
- M: set MINE action (uses cursor tile)
- G: trigger a MINE at cursor
- C: queue SURFACE
- R: queue REPAIR action
- Space / Left click: queue active action
- Enter: confirm queued actions
- Backspace: undo last queued action
- Esc: clear active action
- 1-6: choose system gauge to charge on next MOVE/SILENCE
