from __future__ import annotations

from pathlib import Path
from typing import Any

from ..base import AgentRole
from ..common.functions import write_turn_actions
import json


def write_iteration_ledger(*, base_path: Path, turn_id: int, record: dict[str, Any]) -> None:
    """Persist the iteration record as JSON and a small markdown summary."""
    base_path.mkdir(parents=True, exist_ok=True)
    json_path = base_path / f"turn_{turn_id}_iterations.json"
    md_path = base_path / f"turn_{turn_id}_iterations.md"

    # write JSON
    with json_path.open("w", encoding="utf-8") as fh:
        json.dump(record, fh, indent=2, ensure_ascii=False)

    # write a compact markdown summary
    lines = [
        "# Turn Iterations",
        "",
        f"- turn_id: {turn_id}",
        f"- iterations: {len(record.get('iterations', []))}",
        "",
        "## Iteration Summaries",
        "",
    ]

    for it in record.get("iterations", []):
        proposals = it.get("proposals", {})
        lines.append(f"- iteration {it.get('iteration')}: proposals={{{', '.join(proposals.keys())}}}")

    lines.append("")
    lines.append("## Accepted Decisions")
    lines.append("")
    for item in record.get("accepted", []):
        lines.append(f"- {item}")

    md_content = "\n".join(lines).rstrip() + "\n"
    md_path.write_text(md_content, encoding="utf-8")


def write_turn_actions_ledger(
    *,
    base_path: Path,
    turn_id: int,
    status: str,
    active_roles: set[AgentRole],
    activation_deadline_ms: int | None,
    action_window_open: bool,
    turn_action_proposals: dict[AgentRole, dict[str, Any]],
    accepted: list[dict[str, Any]] | None = None,
    omitted: list[dict[str, Any]] | None = None,
) -> None:
    roles = [role.value for role in sorted(active_roles, key=lambda value: value.value)]
    lines = [
        "# Turn Actions",
        "",
        "This file stores the current turn activation window, action proposals, and the final consensus result.",
        "",
        "## Current Turn",
        "",
        f"- turn_id: {turn_id}",
        f"- status: {status}",
        f"- active_roles: {roles}",
        f"- activation_deadline_ms: {activation_deadline_ms}",
        f"- action_window: {'open' if action_window_open else 'closed'}",
        "",
        "## Proposals",
        "",
    ]

    if turn_action_proposals:
        for role, proposal in turn_action_proposals.items():
            lines.append(f"- {role.value}: {proposal}")
    else:
        lines.append("- none")

    lines.extend([
        "",
        "## Final Decisions",
        "",
    ])

    if accepted:
        for item in accepted:
            lines.append(f"- accepted: {item}")
    else:
        lines.append("- none")

    if omitted:
        lines.append("")
        lines.append("## Omitted")
        lines.append("")
        for item in omitted:
            lines.append(f"- omitted: {item}")

    write_turn_actions("\n".join(lines).rstrip() + "\n", base_path=base_path)
