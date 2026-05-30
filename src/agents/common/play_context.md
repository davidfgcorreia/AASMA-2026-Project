# Play Context

## Trajectory Map
```
map: 15x15
.-O............
.-#...#.....##.
..#.....#...#..
........#......
...............
...............
.#.#..#.#......
.#.#..#........
...#...#...###.
...............
...#...........
..#....#...#...
#...........#..
..#...#.#....#.
...#...........
```

## Belief Map
```
0.01 0.01 0.01 0.01 0.01 0.01 0.01 0.01 0.01 0.01 0.01 0.01 0.01 0.01 0.01
0.01 0.01 0.00 0.01 0.01 0.01 0.00 0.01 0.01 0.01 0.01 0.01 0.00 0.00 0.01
0.01 0.01 0.00 0.01 0.01 0.01 0.01 0.01 0.00 0.01 0.01 0.01 0.00 0.01 0.01
0.01 0.01 0.01 0.01 0.01 0.01 0.01 0.01 0.00 0.01 0.01 0.01 0.01 0.01 0.01
0.01 0.01 0.01 0.01 0.01 0.01 0.01 0.01 0.01 0.01 0.01 0.01 0.01 0.01 0.01
0.01 0.01 0.01 0.01 0.01 0.01 0.01 0.01 0.01 0.01 0.01 0.01 0.01 0.01 0.01
0.01 0.00 0.01 0.00 0.01 0.01 0.00 0.01 0.00 0.01 0.01 0.01 0.01 0.01 0.01
0.01 0.00 0.01 0.00 0.01 0.01 0.00 0.01 0.01 0.01 0.01 0.01 0.01 0.01 0.01
0.01 0.01 0.01 0.00 0.01 0.01 0.01 0.00 0.01 0.01 0.01 0.00 0.00 0.00 0.01
0.01 0.01 0.01 0.01 0.01 0.01 0.01 0.01 0.01 0.01 0.01 0.01 0.01 0.01 0.01
0.01 0.01 0.01 0.00 0.01 0.01 0.01 0.01 0.01 0.01 0.01 0.01 0.01 0.01 0.01
0.01 0.01 0.00 0.01 0.01 0.01 0.01 0.00 0.01 0.01 0.01 0.00 0.01 0.01 0.01
0.00 0.01 0.01 0.01 0.01 0.01 0.01 0.01 0.01 0.01 0.01 0.01 0.00 0.01 0.01
0.01 0.01 0.00 0.01 0.01 0.01 0.00 0.01 0.00 0.01 0.01 0.01 0.01 0.00 0.01
0.01 0.01 0.01 0.00 0.01 0.01 0.01 0.01 0.01 0.01 0.01 0.01 0.01 0.01 0.01
```

## Engineer Board (Crossed)
- W: (none)
- N: N-not-green-0
- S: (none)
- E: E-not-green-1

- team: BLUE
- turn: 2
- round_type: normal
- source: api
- enemy_last_play: None

```json
{
  "enemy_last_play": null,
  "engineer_board": {
    "buttons_by_direction": {
      "E": [
        {
          "button_id": "E-not-radioactive-0",
          "circuit_part": "not",
          "crossed": false,
          "direction": "E",
          "function_type": "radioactive",
          "slot_index": 0
        },
        {
          "button_id": "E-not-green-1",
          "circuit_part": "not",
          "crossed": true,
          "direction": "E",
          "function_type": "green",
          "slot_index": 1
        },
        {
          "button_id": "E-not-radioactive-2",
          "circuit_part": "not",
          "crossed": false,
          "direction": "E",
          "function_type": "radioactive",
          "slot_index": 2
        },
        {
          "button_id": "E-down-yellow-3",
          "circuit_part": "down",
          "crossed": false,
          "direction": "E",
          "function_type": "yellow",
          "slot_index": 3
        },
        {
          "button_id": "E-central-green-4",
          "circuit_part": "central",
          "crossed": false,
          "direction": "E",
          "function_type": "green",
          "slot_index": 4
        },
        {
          "button_id": "E-top-red-5",
          "circuit_part": "top",
          "crossed": false,
          "direction": "E",
          "function_type": "red",
          "slot_index": 5
        }
      ],
      "N": [
        {
          "button_id": "N-not-green-0",
          "circuit_part": "not",
          "crossed": true,
          "direction": "N",
          "function_type": "green",
          "slot_index": 0
        },
        {
          "button_id": "N-not-red-1",
          "circuit_part": "not",
          "crossed": false,
          "direction": "N",
          "function_type": "red",
          "slot_index": 1
        },
        {
          "button_id": "N-not-radioactive-2",
          "circuit_part": "not",
          "crossed": false,
          "direction": "N",
          "function_type": "radioactive",
          "slot_index": 2
        },
        {
          "button_id": "N-central-red-3",
          "circuit_part": "central",
          "crossed": false,
          "direction": "N",
          "function_type": "red",
          "slot_index": 3
        },
        {
          "button_id": "N-central-yellow-4",
          "circuit_part": "central",
          "crossed": false,
          "direction": "N",
          "function_type": "yellow",
          "slot_index": 4
        },
        {
          "button_id": "N-central-red-5",
          "circuit_part": "central",
          "crossed": false,
          "direction": "N",
          "function_type": "red",
          "slot_index": 5
        }
      ],
      "S": [
        {
          "button_id": "S-not-red-0",
          "circuit_part": "not",
          "crossed": false,
          "direction": "S",
          "function_type": "red",
          "slot_index": 0
        },
        {
          "button_id": "S-not-radioactive-1",
          "circuit_part": "not",
          "crossed": false,
          "direction": "S",
          "function_type": "radioactive",
          "slot_index": 1
        },
        {
          "button_id": "S-not-yellow-2",
          "circuit_part": "not",
          "crossed": false,
          "direction": "S",
          "function_type": "yellow",
          "slot_index": 2
        },
        {
          "button_id": "S-down-yellow-3",
          "circuit_part": "down",
          "crossed": false,
          "direction": "S",
          "function_type": "yellow",
          "slot_index": 3
        },
        {
          "button_id": "S-down-green-4",
          "circuit_part": "down",
          "crossed": false,
          "direction": "S",
          "function_type": "green",
          "slot_index": 4
        },
        {
          "button_id": "S-down-red-5",
          "circuit_part": "down",
          "crossed": false,
          "direction": "S",
          "function_type": "red",
          "slot_index": 5
        }
      ],
      "W": [
        {
          "button_id": "W-not-green-0",
          "circuit_part": "not",
          "crossed": false,
          "direction": "W",
          "function_type": "green",
          "slot_index": 0
        },
        {
          "button_id": "W-not-radioactive-1",
          "circuit_part": "not",
          "crossed": false,
          "direction": "W",
          "function_type": "radioactive",
          "slot_index": 1
        },
        {
          "button_id": "W-not-radioactive-2",
          "circuit_part": "not",
          "crossed": false,
          "direction": "W",
          "function_type": "radioactive",
          "slot_index": 2
        },
        {
          "button_id": "W-top-red-3",
          "circuit_part": "top",
          "crossed": false,
          "direction": "W",
          "function_type": "red",
          "slot_index": 3
        },
        {
          "button_id": "W-top-green-4",
          "circuit_part": "top",
          "crossed": false,
          "direction": "W",
          "function_type": "green",
          "slot_index": 4
        },
        {
          "button_id": "W-top-yellow-5",
          "circuit_part": "top",
          "crossed": false,
          "direction": "W",
          "function_type": "yellow",
          "slot_index": 5
        }
      ]
    },
    "circuits_status": {},
    "crossed_by_direction": {
      "E": [
        "E-not-green-1"
      ],
      "N": [
        "N-not-green-0"
      ],
      "S": [],
      "W": []
    },
    "team": "BLUE"
  },
  "own_gauges": {
    "drone": 0,
    "mine": 0,
    "scenario": 0,
    "silence": 0,
    "sonar": 2,
    "torpedo": 0
  },
  "own_submarine": {
    "damage": 0,
    "x": 2,
    "y": 0
  },
  "radio_operator": {
    "heard_moves": [],
    "most_likely_sector": 1
  },
  "round_type": "normal",
  "source": "api",
  "team": "BLUE",
  "turn": 2
}
```
