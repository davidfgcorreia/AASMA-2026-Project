from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple

from .config import PANEL_WIDTH

ENGINEER_BOARD_WIDTH = PANEL_WIDTH
ENGINEER_BOARD_HEIGHT = 474
ENGINEER_IMAGE_WIDTH = 205
ENGINEER_IMAGE_HEIGHT = 474
ENGINEER_LEFT_COLUMN_WIDTH = ENGINEER_BOARD_WIDTH - ENGINEER_IMAGE_WIDTH -50
ENGINEER_BUTTON_RADIUS = 15
ENGINEER_LABEL_WIDTH = 34
ENGINEER_LABEL_HEIGHT = 28

ENGINEER_ROW_OFFSETS: Dict[str, int] = {
    "W": 96,
    "N": 190,
    "S": 284,
    "E": 378,
}

ENGINEER_CIRCUIT_PARTS = ("top", "central", "down", "not")
ENGINEER_FUNCTION_TYPES = ("radioactive", "red", "yellow", "green")


@dataclass(frozen=True)
class EngineerButtonSpec:
    button_id: str
    direction: str
    slot_index: int
    circuit_part: str
    function_type: str


def _build_engineer_button_specs(direction: str) -> list[EngineerButtonSpec]:
    specs_by_direction = {
        "W": [
            EngineerButtonSpec(f"{direction}-not-green-0", direction, 0, "not", "green"),
            EngineerButtonSpec(f"{direction}-not-radioactive-1", direction, 1, "not", "radioactive"),
            EngineerButtonSpec(f"{direction}-not-radioactive-2", direction, 2, "not", "radioactive"),
            EngineerButtonSpec(f"{direction}-top-red-3", direction, 3, "top", "red"),
            EngineerButtonSpec(f"{direction}-top-green-4", direction, 4, "top", "green"),
            EngineerButtonSpec(f"{direction}-top-yellow-5", direction, 5, "top", "yellow"),
        ],
        "N": [
            EngineerButtonSpec(f"{direction}-not-green-0", direction, 0, "not", "green"),
            EngineerButtonSpec(f"{direction}-not-red-1", direction, 1, "not", "red"),
            EngineerButtonSpec(f"{direction}-not-radioactive-2", direction, 2, "not", "radioactive"),
            EngineerButtonSpec(f"{direction}-central-red-3", direction, 3, "central", "red"),
            EngineerButtonSpec(f"{direction}-central-yellow-4", direction, 4, "central", "yellow"),
            EngineerButtonSpec(f"{direction}-central-red-5", direction, 5, "central", "red"),
        ],
        "S": [
            EngineerButtonSpec(f"{direction}-not-red-0", direction, 0, "not", "red"),
            EngineerButtonSpec(f"{direction}-not-radioactive-1", direction, 1, "not", "radioactive"),
            EngineerButtonSpec(f"{direction}-not-yellow-2", direction, 2, "not", "yellow"),
            EngineerButtonSpec(f"{direction}-down-yellow-3", direction, 3, "down", "yellow"),
            EngineerButtonSpec(f"{direction}-down-green-4", direction, 4, "down", "green"),
            EngineerButtonSpec(f"{direction}-down-red-5", direction, 5, "down", "red"),
        ],
        "E": [
            EngineerButtonSpec(f"{direction}-not-radioactive-0", direction, 0, "not", "radioactive"),
            EngineerButtonSpec(f"{direction}-not-green-1", direction, 1, "not", "green"),
            EngineerButtonSpec(f"{direction}-not-radioactive-2", direction, 2, "not", "radioactive"),
            EngineerButtonSpec(f"{direction}-down-yellow-3", direction, 3, "down", "yellow"),
            EngineerButtonSpec(f"{direction}-central-green-4", direction, 4, "central", "green"),
            EngineerButtonSpec(f"{direction}-top-red-5", direction, 5, "top", "red"),
        ],
    }
    return specs_by_direction.get(direction, [])


ENGINEER_BUTTON_SPECS: Dict[str, list[EngineerButtonSpec]] = {
    direction: _build_engineer_button_specs(direction)
    for direction in ("W", "N", "S", "E")
}

ENGINEER_BUTTON_SPECS_BY_ID: Dict[str, EngineerButtonSpec] = {
    spec.button_id: spec
    for specs in ENGINEER_BUTTON_SPECS.values()
    for spec in specs
}

# Individual button positions per direction (adjust these for visual fine-tuning)
ENGINEER_BUTTON_POSITIONS: Dict[str, list[Tuple[int, int]]] = {
    "W": [
        (100, 45),   # Button 0
        (100, 75),   # Button 1
        (100, 105),   # Button 2
        (218, 45),   # Button 3
        (160, 105),  # Button 4
        (218, 105),  # Button 5
    ],
    "N": [
        (100, 155),  # Button 0
        (100, 185),  # Button 1
        (100, 215),  # Button 2
        (160, 155),  # Button 3
        (218, 155),  # Button 4
        (160, 215),  # Button 5
    ],
    "S": [
        (100, 265),  # Button 0
        (100, 295),  # Button 1
        (100, 325),  # Button 2
        (160, 265),  # Button 3
        (218, 265),  # Button 4
        (160, 325),  # Button 5
    ],
    "E": [
        (100, 375),  # Button 0
        (100, 405),  # Button 1
        (100, 435),  # Button 2
        (160, 375),  # Button 3
        (218, 375),  # Button 4
        (160, 435),  # Button 5
    ],
}


def engineer_board_geometry(origin_x: int, origin_y: int) -> dict[str, object]:
    board_rect = (origin_x, origin_y, ENGINEER_BOARD_WIDTH, ENGINEER_BOARD_HEIGHT)
    image_rect = (origin_x + ENGINEER_LEFT_COLUMN_WIDTH, origin_y, ENGINEER_IMAGE_WIDTH, ENGINEER_IMAGE_HEIGHT)
    rows: dict[str, dict[str, object]] = {}

    for direction in ("W", "N", "S", "E"):
        row_y = origin_y + ENGINEER_ROW_OFFSETS[direction]
        label_rect = (origin_x + 10, row_y - ENGINEER_LABEL_HEIGHT // 2, ENGINEER_LABEL_WIDTH, ENGINEER_LABEL_HEIGHT)
        # Use explicit button positions from constants
        base_positions = ENGINEER_BUTTON_POSITIONS.get(direction, [])
        buttons = [(origin_x + bx, origin_y + by) for bx, by in base_positions]
        rows[direction] = {
            "row_y": row_y,
            "label_rect": label_rect,
            "buttons": buttons,
            "button_specs": ENGINEER_BUTTON_SPECS[direction],
        }

    return {
        "board_rect": board_rect,
        "image_rect": image_rect,
        "rows": rows,
    }
def engineer_button_spec(direction: str, slot_index: int) -> EngineerButtonSpec | None:
    specs = ENGINEER_BUTTON_SPECS.get(direction, [])
    if slot_index < 0 or slot_index >= len(specs):
        return None
    return specs[slot_index]


def engineer_button_spec_by_id(button_id: str) -> EngineerButtonSpec | None:
    return ENGINEER_BUTTON_SPECS_BY_ID.get(button_id)


def point_in_rect(point: Tuple[int, int], rect: Tuple[int, int, int, int]) -> bool:
    px, py = point
    rx, ry, rw, rh = rect
    return rx <= px <= rx + rw and ry <= py <= ry + rh